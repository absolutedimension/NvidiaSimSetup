"""Isaac Lab environment: Cinematographer drone filming a dancer.

The drone (Starling 2) is the RL agent. The dancer is a kinematic target
driven by pre-recorded mocap. The reward teaches cinematic camera work:
framing, distance, smoothness, shot variety, height variation, safety.
"""
from __future__ import annotations

import math
import gymnasium as gym
import torch
import warp as wp
import numpy as np

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.utils.math import subtract_frame_transforms

from .cinematographer_env_cfg import CinematographerEnvCfg  # noqa: F401


class CinematographerEnv(DirectRLEnv):
    cfg: CinematographerEnvCfg

    def __init__(self, cfg: CinematographerEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self._actions = torch.zeros(self.num_envs, gym.spaces.flatdim(self.single_action_space), device=self.device)
        self._thrust = torch.zeros(self.num_envs, 1, 3, device=self.device)
        self._moment = torch.zeros(self.num_envs, 1, 3, device=self.device)

        # Load dancer trajectory
        data = np.load(self.cfg.mocap_npz_path)
        self._dancer_traj = torch.tensor(data["positions"], dtype=torch.float32, device=self.device)  # (T, 3)
        self._dancer_fps = float(data["fps"])
        self._dancer_T = self._dancer_traj.shape[0]

        # Per-env time index into the dancer trajectory
        self._dancer_time_idx = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)

        # Current dancer position per env (updated each step)
        self._dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)

        # Previous dancer position for velocity estimation
        self._prev_dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)

        # Previous acceleration for jerk (smoothness reward)
        self._prev_accel = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_vel = torch.zeros(self.num_envs, 3, device=self.device)

        # History buffers for variety rewards
        self._history_len = 150
        self._azimuth_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._elevation_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._distance_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._history_ptr = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)

        # Previous azimuth/elevation for observations
        self._prev_azimuth = torch.zeros(self.num_envs, device=self.device)
        self._prev_elevation = torch.zeros(self.num_envs, device=self.device)

        # v3: velocity history for pacing reward
        self._velocity_history = torch.zeros(self.num_envs, self._history_len, device=self.device)

        # v3: performer facing direction (computed from consecutive positions)
        # Default facing = +X axis (stage front). Updated each step from dancer velocity.
        self._performer_facing = torch.zeros(self.num_envs, 3, device=self.device)
        self._performer_facing[:, 0] = 1.0  # default: face +X

        # Robot physics
        self._body_id = self._robot.find_bodies("body")[0]
        self._robot_mass = wp.to_torch(self._robot.root_view.get_masses())[0].sum()
        self._gravity_magnitude = torch.tensor(self.sim.cfg.gravity, device=self.device).norm()
        self._robot_weight = (self._robot_mass * self._gravity_magnitude).item()

        # Reward config constants
        self._safety_radius = 1.5
        self._dist_ideal = 3.0
        self._dist_margin = 2.0
        self._jerk_scale = 10.0

        # Logging
        self._episode_sums = {
            key: torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
            for key in ["total", "framing", "distance", "smoothness", "variety",
                        "safety", "height", "look_at", "shot_type",
                        "front_arc", "hold_beauty", "zoom", "pacing"]
        }

    def _setup_scene(self):
        self._robot = Articulation(self.cfg.robot)
        self.scene.articulations["robot"] = self._robot

        self.cfg.terrain.num_envs = self.scene.cfg.num_envs
        self.cfg.terrain.env_spacing = self.scene.cfg.env_spacing
        self._terrain = self.cfg.terrain.class_type(self.cfg.terrain)
        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[self.cfg.terrain.prim_path])
        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

    def _pre_physics_step(self, actions: torch.Tensor):
        self._actions = actions.clone().clamp(-1.0, 1.0)
        self._thrust[:, 0, 2] = self.cfg.thrust_to_weight * self._robot_weight * (self._actions[:, 0] + 1.0) / 2.0
        self._moment[:, 0, :] = self.cfg.moment_scale * self._actions[:, 1:]

    def _apply_action(self):
        self._robot.permanent_wrench_composer.set_forces_and_torques_index(
            body_ids=self._body_id, forces=self._thrust, torques=self._moment,
        )

    def _post_physics_step(self):
        # Advance dancer timeline
        sim_dt = self.cfg.sim.dt * self.cfg.decimation
        steps_per_mocap_frame = max(1, round(1.0 / (self._dancer_fps * sim_dt)))
        advance = (self.episode_length_buf % steps_per_mocap_frame == 0).long()
        self._dancer_time_idx = (self._dancer_time_idx + advance) % self._dancer_T

        # Update dancer position (offset to env origin)
        self._prev_dancer_pos_w[:] = self._dancer_pos_w
        base_pos = self._dancer_traj[self._dancer_time_idx]  # (N, 3)
        self._dancer_pos_w = base_pos + self._terrain.env_origins

        # Update history buffers
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        rel = drone_pos - self._dancer_pos_w
        dist = rel.norm(dim=-1)
        azimuth = torch.atan2(rel[:, 0], rel[:, 1])  # Isaac: Z-up, so XY is horizontal
        horiz = (rel[:, 0]**2 + rel[:, 1]**2).sqrt()
        elevation = torch.atan2(rel[:, 2], horiz)

        ptr = self._history_ptr % self._history_len
        env_ids = torch.arange(self.num_envs, device=self.device)
        self._azimuth_history[env_ids, ptr] = azimuth
        self._elevation_history[env_ids, ptr] = elevation
        self._distance_history[env_ids, ptr] = dist

        # v3: track drone speed for pacing reward
        drone_speed = wp.to_torch(self._robot.data.root_lin_vel_w).norm(dim=-1)
        self._velocity_history[env_ids, ptr] = drone_speed

        # v3: update performer facing from velocity (direction of movement)
        dancer_vel = (self._dancer_pos_w - self._prev_dancer_pos_w) / sim_dt
        dancer_speed = dancer_vel.norm(dim=-1, keepdim=True)
        # Only update facing when dancer is moving (> 0.1 m/s); keep previous when still
        moving_mask = (dancer_speed > 0.1).float()
        new_facing = dancer_vel / (dancer_speed + 1e-8)
        self._performer_facing = moving_mask * new_facing + (1.0 - moving_mask) * self._performer_facing

        self._history_ptr += 1

        self._prev_azimuth = azimuth
        self._prev_elevation = elevation

        return super()._post_physics_step()

    def _get_observations(self) -> dict:
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        drone_quat = wp.to_torch(self._robot.data.root_quat_w)

        # Relative dancer position in body frame
        rel_dancer_b, _ = subtract_frame_transforms(drone_pos, drone_quat, self._dancer_pos_w)

        # Dancer velocity in world frame (finite diff)
        sim_dt = self.cfg.sim.dt * self.cfg.decimation
        dancer_vel_w = (self._dancer_pos_w - self._prev_dancer_pos_w) / sim_dt

        # Transform dancer velocity to body frame (approximate: just rotate)
        # For simplicity, use world-frame velocity magnitude direction in body frame
        rel_vel_b, _ = subtract_frame_transforms(
            torch.zeros_like(drone_pos), drone_quat, dancer_vel_w
        )

        # Scalar features
        dist = rel_dancer_b.norm(dim=-1, keepdim=True)
        azimuth = self._prev_azimuth.unsqueeze(-1)
        elevation = self._prev_elevation.unsqueeze(-1)

        # Previous angular features (for the policy to track angular velocity)
        idx = ((self._history_ptr - 2) % self._history_len).long()
        prev_az = self._azimuth_history[torch.arange(self.num_envs, device=self.device), idx].unsqueeze(-1)
        prev_el = self._elevation_history[torch.arange(self.num_envs, device=self.device), idx].unsqueeze(-1)

        obs = torch.cat([
            wp.to_torch(self._robot.data.root_lin_vel_b),    # 3
            wp.to_torch(self._robot.data.root_ang_vel_b),    # 3
            wp.to_torch(self._robot.data.projected_gravity_b),  # 3
            rel_dancer_b,                                      # 3
            rel_vel_b,                                         # 3
            dist,                                              # 1
            azimuth,                                           # 1
            elevation,                                         # 1
            prev_az,                                           # 1
            prev_el,                                           # 1
        ], dim=-1)  # total = 20

        return {"policy": obs}

    def _get_rewards(self) -> torch.Tensor:
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        drone_quat = wp.to_torch(self._robot.data.root_quat_w)
        sim_dt = self.cfg.sim.dt * self.cfg.decimation

        # --- Compute drone forward vector in world frame ---
        # Quaternion to forward: rotate (0,0,1) by quat (Isaac Z-up, forward is usually -Y or +X)
        # For a quadcopter, "camera forward" = body -Y axis (or we define it as the facing dir)
        # Use body X-axis as forward (typical for quads)
        qw, qx, qy, qz = drone_quat[:, 0], drone_quat[:, 1], drone_quat[:, 2], drone_quat[:, 3]
        # Rotate unit X by quaternion: R * (1,0,0)
        fwd_x = 1 - 2*(qy*qy + qz*qz)
        fwd_y = 2*(qx*qy + qw*qz)
        fwd_z = 2*(qx*qz - qw*qy)
        drone_forward = torch.stack([fwd_x, fwd_y, fwd_z], dim=-1)

        # --- Velocity + acceleration ---
        vel = wp.to_torch(self._robot.data.root_lin_vel_w)
        accel = (vel - self._prev_vel) / sim_dt
        jerk = (accel - self._prev_accel) / sim_dt
        self._prev_vel = vel.clone()
        self._prev_accel = accel.clone()

        # --- Individual reward terms ---
        rel = self._dancer_pos_w - drone_pos
        dist = rel.norm(dim=-1)

        # 1. Framing: angle between forward and direction to dancer
        to_dancer = rel / (dist.unsqueeze(-1) + 1e-8)
        fwd_norm = drone_forward / (drone_forward.norm(dim=-1, keepdim=True) + 1e-8)
        cos_angle = (to_dancer * fwd_norm).sum(dim=-1).clamp(-1, 1)
        frame_angle = cos_angle.acos()
        r_framing = 1.0 - (frame_angle / math.radians(15)).tanh()

        # 2. Distance
        dist_err = dist - self._dist_ideal
        r_distance = 1.0 - (dist_err.abs() / self._dist_margin).tanh()

        # 3. Smoothness (jerk penalty)
        jerk_mag = jerk.norm(dim=-1)
        r_smoothness = 1.0 - (jerk_mag / self._jerk_scale).tanh()

        # 4. Azimuth variety (circular std over history window)
        filled = self._history_ptr.clamp(max=self._history_len).float()
        az_hist = self._azimuth_history
        sin_mean = az_hist.sin().sum(dim=-1) / filled.clamp(min=1)
        cos_mean = az_hist.cos().sum(dim=-1) / filled.clamp(min=1)
        R = (sin_mean**2 + cos_mean**2).sqrt()
        circ_std = (-2.0 * R.clamp(1e-8, 1.0).log()).sqrt()
        r_variety = (circ_std / math.radians(30)).clamp(0, 1)

        # 5. Safety
        violation = (dist < self._safety_radius).float()
        r_safety = violation * (-10.0)

        # 6. Height variety (elevation range over history)
        el_hist = self._elevation_history
        el_range = el_hist.max(dim=-1).values - el_hist.min(dim=-1).values
        r_height = (el_range / math.radians(50)).clamp(0, 1)

        # 7. Look-at (horizontal aim)
        to_dancer_horiz = rel.clone()
        to_dancer_horiz[:, 2] = 0  # zero out Z (up axis)
        to_dancer_horiz = to_dancer_horiz / (to_dancer_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        fwd_horiz = drone_forward.clone()
        fwd_horiz[:, 2] = 0
        fwd_horiz = fwd_horiz / (fwd_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        cos_look = (to_dancer_horiz * fwd_horiz).sum(dim=-1).clamp(-1, 1)
        look_angle = cos_look.acos()
        r_look_at = 1.0 - (look_angle / math.radians(10)).tanh()

        # 8. Shot type diversity
        d_hist = self._distance_history
        half_vfov = math.atan(24.0 / (2 * 35.0))  # 35mm lens, 24mm sensor
        coverage = 2.0 * d_hist * math.tan(half_vfov)
        shot_type = (coverage >= 0.8).float() + (coverage >= 1.5).float()  # 0/1/2
        has_close = (shot_type == 0).any(dim=-1).float()
        has_half = (shot_type == 1).any(dim=-1).float()
        has_full = (shot_type == 2).any(dim=-1).float()
        num_types = has_close + has_half + has_full
        transitions = (shot_type[:, 1:] - shot_type[:, :-1]).abs().gt(0).sum(dim=-1).float()
        r_shot_type = 0.6 * (num_types / 3.0) + 0.4 * (transitions / 5.0).clamp(0, 1)

        # --- v3: Front arc (no going behind performer) ---
        # Drone-to-performer vector dotted with performer facing
        to_drone_horiz = -rel.clone()  # dancer→drone direction
        to_drone_horiz[:, 2] = 0
        to_drone_horiz = to_drone_horiz / (to_drone_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        facing_horiz = self._performer_facing.clone()
        facing_horiz[:, 2] = 0
        facing_horiz = facing_horiz / (facing_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        front_cos = (to_drone_horiz * facing_horiz).sum(dim=-1)
        # Positive = drone in front, negative = behind
        is_behind = (front_cos < 0).float()
        r_front_arc = is_behind * (-5.0)  # hard penalty when behind

        # --- v3: Hold-when-good (pause on beautiful frames) ---
        frame_quality = r_framing * r_look_at  # both 0-1
        is_good_frame = (frame_quality / 0.7).clamp(0.0, 1.0)
        drone_speed = vel.norm(dim=-1)
        stillness = 1.0 - (drone_speed / 2.0).tanh()
        r_hold_beauty = is_good_frame * stillness

        # --- v3: Zoom dynamics (push-in / pull-out) ---
        d_hist_zoom = self._distance_history
        kernel_size = 10
        if d_hist_zoom.shape[-1] >= kernel_size:
            smoothed = d_hist_zoom.unfold(-1, kernel_size, 1).mean(dim=-1)
            diff_d = smoothed[:, 1:] - smoothed[:, :-1]
            if diff_d.shape[-1] > 1:
                sign_ch = (diff_d[:, 1:].sign() - diff_d[:, :-1].sign()).abs().gt(0).sum(dim=-1).float()
                r_zoom = 1.0 - (sign_ch - 4.0).abs() / 5.0  # want ~2 push-in/pull-out cycles
                r_zoom = r_zoom.clamp(0.0, 1.0)
            else:
                r_zoom = torch.zeros(self.num_envs, device=self.device)
        else:
            r_zoom = torch.zeros(self.num_envs, device=self.device)

        # --- v3: Pacing (alternate movement and stillness) ---
        v_hist = self._velocity_history
        is_moving = (v_hist > 0.3).float()
        move_ratio = is_moving.mean(dim=-1)
        pace_transitions = (is_moving[:, 1:] - is_moving[:, :-1]).abs().sum(dim=-1)
        pace_trans_score = (pace_transitions / 6.0).clamp(0.0, 1.0)
        pace_ratio_score = (1.0 - (move_ratio - 0.5).abs() * 2).clamp(0.0, 1.0)
        r_pacing = 0.6 * pace_ratio_score + 0.4 * pace_trans_score

        # --- Framing gate: if dancer not in camera view, zero all other rewards ---
        in_frame = (frame_angle < math.radians(60)).float()
        framing_gate = 0.3 + 0.7 * in_frame

        # --- Weighted total (v3: cinematographer brain) ---
        # "Always see the dancer" (framing + look_at + front_arc) = 50%
        # "Film like an artist" (hold + zoom + pacing + variety) = 30%
        # "Stay safe and smooth" (safety + distance + smoothness) = 20%
        total = (
            0.25 * r_framing          # always keep dancer in view
            + 0.15 * r_look_at        # camera points at dancer
            + 0.10 * r_front_arc      # stay in front 180° arc (can go negative!)
            + 0.10 * r_hold_beauty    # hold still on good frames
            + 0.08 * r_zoom           # push-in / pull-out dynamics
            + 0.07 * r_pacing         # alternate move and hold
            + 0.03 * r_variety        # some angle variety
            + 0.02 * r_height         # some height variety
            + 0.05 * r_shot_type      # mix full/half body
            + 0.05 * r_safety         # don't crash into dancer
            + 0.05 * r_distance       # stay in filmable range
            + 0.05 * r_smoothness     # smooth motion
        ) * framing_gate * self.cfg.reward_scale * self.step_dt

        # Logging
        rewards = {
            "total": total,
            "framing": r_framing * self.step_dt,
            "distance": r_distance * self.step_dt,
            "smoothness": r_smoothness * self.step_dt,
            "variety": r_variety * self.step_dt,
            "safety": r_safety * self.step_dt,
            "height": r_height * self.step_dt,
            "look_at": r_look_at * self.step_dt,
            "shot_type": r_shot_type * self.step_dt,
            "front_arc": r_front_arc * self.step_dt,
            "hold_beauty": r_hold_beauty * self.step_dt,
            "zoom": r_zoom * self.step_dt,
            "pacing": r_pacing * self.step_dt,
        }
        for key, value in rewards.items():
            self._episode_sums[key] += value

        return total

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        # Die if crashed into ground or flew too high
        died = torch.logical_or(drone_pos[:, 2] < 0.1, drone_pos[:, 2] > 10.0)
        # Die if too far from dancer (>15m — lost tracking)
        dist = (drone_pos - self._dancer_pos_w).norm(dim=-1)
        died = torch.logical_or(died, dist > 15.0)
        return died, time_out

    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = wp.to_torch(self._robot._ALL_INDICES)

        # Logging
        extras = dict()
        for key in self._episode_sums.keys():
            episodic_avg = torch.mean(self._episode_sums[key][env_ids])
            extras["Episode_Reward/" + key] = episodic_avg / self.max_episode_length_s
            self._episode_sums[key][env_ids] = 0.0
        self.extras["log"] = dict()
        self.extras["log"].update(extras)

        self._robot.reset(env_ids)
        super()._reset_idx(env_ids)

        if len(env_ids) == self.num_envs:
            self.episode_length_buf = torch.randint_like(self.episode_length_buf, high=int(self.max_episode_length))

        self._actions[env_ids] = 0.0

        # Randomize dancer start time so each env sees different parts of the dance
        self._dancer_time_idx[env_ids] = torch.randint(0, self._dancer_T, (len(env_ids),), device=self.device)

        # Update dancer pos for reset envs
        base_pos = self._dancer_traj[self._dancer_time_idx[env_ids]]
        self._dancer_pos_w[env_ids] = base_pos + self._terrain.env_origins[env_ids]
        self._prev_dancer_pos_w[env_ids] = self._dancer_pos_w[env_ids]

        # Spawn drone at random position around the dancer
        default_root_pose = wp.to_torch(self._robot.data.default_root_pose)[env_ids].clone()
        default_root_pose[:, :3] += self._terrain.env_origins[env_ids]

        # Randomize: spawn 2-4m from dancer, random azimuth, 0.5-2m above dancer
        spawn_dist = torch.empty(len(env_ids), device=self.device).uniform_(2.0, 4.0)
        spawn_angle = torch.empty(len(env_ids), device=self.device).uniform_(0, 2 * math.pi)
        spawn_height = torch.empty(len(env_ids), device=self.device).uniform_(0.5, 2.0)

        default_root_pose[:, 0] = self._dancer_pos_w[env_ids, 0] + spawn_dist * spawn_angle.cos()
        default_root_pose[:, 1] = self._dancer_pos_w[env_ids, 1] + spawn_dist * spawn_angle.sin()
        default_root_pose[:, 2] = self._dancer_pos_w[env_ids, 2] + spawn_height

        default_root_vel = wp.to_torch(self._robot.data.default_root_vel)[env_ids]
        self._robot.write_root_pose_to_sim_index(root_pose=default_root_pose, env_ids=env_ids)
        self._robot.write_root_velocity_to_sim_index(root_velocity=default_root_vel, env_ids=env_ids)

        joint_pos = wp.to_torch(self._robot.data.default_joint_pos)[env_ids]
        joint_vel = wp.to_torch(self._robot.data.default_joint_vel)[env_ids]
        self._robot.write_joint_position_to_sim_index(position=joint_pos, env_ids=env_ids)
        self._robot.write_joint_velocity_to_sim_index(velocity=joint_vel, env_ids=env_ids)

        # Reset histories
        self._azimuth_history[env_ids] = 0.0
        self._elevation_history[env_ids] = 0.0
        self._distance_history[env_ids] = self._dist_ideal
        self._history_ptr[env_ids] = 0
        self._prev_accel[env_ids] = 0.0
        self._prev_vel[env_ids] = 0.0
