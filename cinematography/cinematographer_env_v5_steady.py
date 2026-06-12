"""Isaac Lab environment v5d: STEADY cinematographer drone.

v5d: DAMPING + STRIPPED REWARD + EMA actions
  - Rigid body linear_damping=2.0, angular_damping=3.0 (simulates air drag)
  - moment_scale halved to 0.01 (less rotational authority)
  - Action EMA filter alpha=0.15 (prevents jitter)
  - Only 3 active reward terms: stillness(0.65), look_at(0.20), distance(0.10) + safety(0.05)
  - Gaussian stillness: exp(-speed² * 50) — peaks sharply at zero velocity
  - No composition, no variety, no hold bonus — just be still and face the dancer

The damping is the critical change: with linear_damping=2.0, the drone naturally
decelerates. The policy only needs to learn the exact hover thrust and hold it.
Previous versions had zero damping, making hover fundamentally unstable.
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

from .cinematographer_env_cfg_v5_steady import CinematographerEnvCfgV5Steady  # noqa: F401


class CinematographerEnvV5Steady(DirectRLEnv):
    cfg: CinematographerEnvCfgV5Steady

    def __init__(self, cfg: CinematographerEnvCfgV5Steady, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self._actions = torch.zeros(self.num_envs, gym.spaces.flatdim(self.single_action_space), device=self.device)
        self._prev_actions = torch.zeros_like(self._actions)
        self._smoothed_actions = torch.zeros_like(self._actions)
        self._thrust = torch.zeros(self.num_envs, 1, 3, device=self.device)
        self._moment = torch.zeros(self.num_envs, 1, 3, device=self.device)

        # Action EMA filter
        self._action_ema_alpha = 0.15

        # ── Dancer trajectory ──
        data = np.load(self.cfg.mocap_npz_path)
        self._dancer_traj = torch.tensor(data["positions"], dtype=torch.float32, device=self.device)
        self._dancer_fps = float(data["fps"])
        self._dancer_T = self._dancer_traj.shape[0]
        self._dancer_time_idx = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)

        # ── Physics state ──
        self._prev_vel = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_accel = torch.zeros(self.num_envs, 3, device=self.device)

        # ── Stillness tracking ──
        self._stillness_time = torch.zeros(self.num_envs, device=self.device)
        self._hold_quality = torch.zeros(self.num_envs, device=self.device)

        # ── History buffers (kept for obs compatibility) ──
        self._history_len = 300
        self._azimuth_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._elevation_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._history_ptr = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._prev_azimuth = torch.zeros(self.num_envs, device=self.device)
        self._prev_elevation = torch.zeros(self.num_envs, device=self.device)

        # ── Robot physics ──
        self._body_id = self._robot.find_bodies("body")[0]
        self._robot_mass = wp.to_torch(self._robot.root_view.get_masses())[0].sum()
        self._gravity_magnitude = torch.tensor(self.sim.cfg.gravity, device=self.device).norm()
        self._robot_weight = (self._robot_mass * self._gravity_magnitude).item()

        # ── Constants ──
        self._safety_radius = 1.5
        self._dist_ideal = 3.0
        self._dist_margin = 2.0
        self._stillness_threshold = 0.25
        self._ang_stillness_threshold = 0.3

        # ── Logging ──
        self._reward_keys = [
            "r_stillness", "r_look_at", "r_composition", "r_action_smooth",
            "r_distance", "r_safety", "r_angle_variety", "r_hold_bonus",
        ]
        self._episode_sums = {
            key: torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
            for key in ["total"] + self._reward_keys
        }

    # ── Scene setup ──────────────────────────────────────────────────────

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

    # ── Action ───────────────────────────────────────────────────────────

    def _pre_physics_step(self, actions: torch.Tensor):
        self._prev_actions = self._actions.clone()
        self._actions = actions.clone().clamp(-1.0, 1.0)

        # EMA filter: smooth actions to prevent jitter
        alpha = self._action_ema_alpha
        self._smoothed_actions = alpha * self._actions + (1.0 - alpha) * self._smoothed_actions

        self._thrust[:, 0, 2] = self.cfg.thrust_to_weight * self._robot_weight * (self._smoothed_actions[:, 0] + 1.0) / 2.0
        self._moment[:, 0, :] = self.cfg.moment_scale * self._smoothed_actions[:, 1:]

    def _apply_action(self):
        self._robot.permanent_wrench_composer.set_forces_and_torques_index(
            body_ids=self._body_id, forces=self._thrust, torques=self._moment,
        )

    # ── Post-physics ─────────────────────────────────────────────────────

    def _post_physics_step(self):
        sim_dt = self.cfg.sim.dt * self.cfg.decimation
        steps_per_mocap_frame = max(1, round(1.0 / (self._dancer_fps * sim_dt)))
        advance = (self.episode_length_buf % steps_per_mocap_frame == 0).long()
        self._dancer_time_idx = (self._dancer_time_idx + advance) % self._dancer_T

        self._prev_dancer_pos_w[:] = self._dancer_pos_w
        base_pos = self._dancer_traj[self._dancer_time_idx]
        self._dancer_pos_w = base_pos + self._terrain.env_origins

        # Track stillness
        drone_speed = wp.to_torch(self._robot.data.root_lin_vel_w).norm(dim=-1)
        ang_speed = wp.to_torch(self._robot.data.root_ang_vel_w).norm(dim=-1)
        is_still = ((drone_speed < self._stillness_threshold) &
                     (ang_speed < self._ang_stillness_threshold)).float()
        self._stillness_time = self._stillness_time * is_still + sim_dt * is_still

        # History
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        rel = drone_pos - self._dancer_pos_w
        azimuth = torch.atan2(rel[:, 0], rel[:, 1])
        horiz = (rel[:, 0]**2 + rel[:, 1]**2).sqrt()
        elevation = torch.atan2(rel[:, 2], horiz)
        ptr = self._history_ptr % self._history_len
        env_ids = torch.arange(self.num_envs, device=self.device)
        self._azimuth_history[env_ids, ptr] = azimuth
        self._elevation_history[env_ids, ptr] = elevation
        self._history_ptr += 1
        self._prev_azimuth = azimuth
        self._prev_elevation = elevation

        return super()._post_physics_step()

    # ── Observations: 20-dim ─────────────────────────────────────────────

    def _get_observations(self) -> dict:
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        drone_quat = wp.to_torch(self._robot.data.root_quat_w)
        sim_dt = self.cfg.sim.dt * self.cfg.decimation

        rel_dancer_b, _ = subtract_frame_transforms(drone_pos, drone_quat, self._dancer_pos_w)
        dancer_vel_w = (self._dancer_pos_w - self._prev_dancer_pos_w) / sim_dt
        rel_vel_b, _ = subtract_frame_transforms(
            torch.zeros_like(drone_pos), drone_quat, dancer_vel_w
        )

        dist = rel_dancer_b.norm(dim=-1, keepdim=True)
        azimuth = self._prev_azimuth.unsqueeze(-1)
        elevation = self._prev_elevation.unsqueeze(-1)

        obs = torch.cat([
            wp.to_torch(self._robot.data.root_lin_vel_b),      # 3
            wp.to_torch(self._robot.data.root_ang_vel_b),      # 3
            wp.to_torch(self._robot.data.projected_gravity_b), # 3
            rel_dancer_b,                                       # 3
            rel_vel_b,                                          # 3
            dist,                                               # 1
            azimuth,                                            # 1
            elevation,                                          # 1
            self._stillness_time.unsqueeze(-1) / 5.0,          # 1
            self._hold_quality.unsqueeze(-1),                   # 1
        ], dim=-1)  # total = 20

        return {"policy": obs}

    # ── Rewards: STRIPPED — 3 terms + safety ─────────────────────────────

    def _get_rewards(self) -> torch.Tensor:
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        drone_quat = wp.to_torch(self._robot.data.root_quat_w)
        sim_dt = self.cfg.sim.dt * self.cfg.decimation

        # Drone forward vector
        qw, qx, qy, qz = drone_quat[:, 0], drone_quat[:, 1], drone_quat[:, 2], drone_quat[:, 3]
        fwd_x = 1 - 2*(qy*qy + qz*qz)
        fwd_y = 2*(qx*qy + qw*qz)
        fwd_z = 2*(qx*qz - qw*qy)
        drone_forward = torch.stack([fwd_x, fwd_y, fwd_z], dim=-1)
        fwd_norm = drone_forward / (drone_forward.norm(dim=-1, keepdim=True) + 1e-8)

        # Velocity
        vel = wp.to_torch(self._robot.data.root_lin_vel_w)
        ang_vel = wp.to_torch(self._robot.data.root_ang_vel_w)
        accel = (vel - self._prev_vel) / sim_dt
        self._prev_vel = vel.clone()
        self._prev_accel = accel.clone()

        # Geometry
        rel = self._dancer_pos_w - drone_pos
        dist = rel.norm(dim=-1)
        to_dancer = rel / (dist.unsqueeze(-1) + 1e-8)

        # ══════════════════════════════════════════════════════════
        # v5d: ONLY 3 ACTIVE REWARDS + SAFETY
        # With damping, the drone naturally decelerates.
        # Policy just needs: hover thrust, face dancer, right distance.
        # ══════════════════════════════════════════════════════════

        drone_speed = vel.norm(dim=-1)
        ang_speed = ang_vel.norm(dim=-1)

        # ── r_stillness: GAUSSIAN peaked at zero velocity ──
        # speed=0 → 1.0, speed=0.1 → 0.61, speed=0.2 → 0.14, speed=0.5 → ~0
        r_stillness = torch.exp(-drone_speed.pow(2) * 50.0) * torch.exp(-ang_speed.pow(2) * 20.0)

        # ── r_look_at: camera aims at dancer ──
        cos_angle = (to_dancer * fwd_norm).sum(dim=-1).clamp(-1, 1)
        look_angle = cos_angle.acos()
        r_look_at = 1.0 - (look_angle / math.radians(15)).tanh()

        # ── r_distance: maintain ideal filming distance ──
        dist_err = dist - self._dist_ideal
        r_distance = 1.0 - (dist_err.abs() / self._dist_margin).tanh()

        # ── r_safety: don't crash into dancer ──
        violation = (dist < self._safety_radius).float()
        r_safety = violation * (-5.0)

        # Update hold_quality for obs
        self._hold_quality = r_look_at.detach() * (1.0 - drone_speed.detach().clamp(0, 1))

        # Placeholders for logging (unused in reward sum)
        r_composition = r_look_at
        r_action_smooth = torch.exp(-(self._actions - self._prev_actions).norm(dim=-1) * 3.0)
        r_angle_variety = torch.zeros_like(r_stillness)
        r_hold_bonus = (self._stillness_time > 0.5).float() * (self._stillness_time / 3.0).clamp(0, 1)

        # ── Weighted sum ──
        total = (
            0.65 * r_stillness +
            0.20 * r_look_at +
            0.10 * r_distance +
            0.05 * r_safety
        ) * self.cfg.reward_scale * self.step_dt

        # Logging
        all_rewards = {
            "r_stillness": r_stillness, "r_look_at": r_look_at,
            "r_composition": r_composition, "r_action_smooth": r_action_smooth,
            "r_distance": r_distance, "r_safety": r_safety,
            "r_angle_variety": r_angle_variety, "r_hold_bonus": r_hold_bonus,
        }
        self._episode_sums["total"] += total
        for key in self._reward_keys:
            self._episode_sums[key] += all_rewards[key] * self.step_dt

        return total

    # ── Dones ────────────────────────────────────────────────────────────

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        died = torch.logical_or(drone_pos[:, 2] < 0.1, drone_pos[:, 2] > 10.0)
        dist = (drone_pos - self._dancer_pos_w).norm(dim=-1)
        died = torch.logical_or(died, dist > 12.0)
        return died, time_out

    # ── Reset ────────────────────────────────────────────────────────────

    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = wp.to_torch(self._robot._ALL_INDICES)

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
        self._prev_actions[env_ids] = 0.0
        self._smoothed_actions[env_ids] = 0.0

        # Randomize dancer start time
        self._dancer_time_idx[env_ids] = torch.randint(0, self._dancer_T, (len(env_ids),), device=self.device)
        base_pos = self._dancer_traj[self._dancer_time_idx[env_ids]]
        self._dancer_pos_w[env_ids] = base_pos + self._terrain.env_origins[env_ids]
        self._prev_dancer_pos_w[env_ids] = self._dancer_pos_w[env_ids]

        # Spawn drone at random angle, 2-5m from dancer, 0.5-2.5m height
        default_root_pose = wp.to_torch(self._robot.data.default_root_pose)[env_ids].clone()
        default_root_pose[:, :3] += self._terrain.env_origins[env_ids]

        spawn_dist = torch.empty(len(env_ids), device=self.device).uniform_(2.0, 5.0)
        spawn_angle = torch.empty(len(env_ids), device=self.device).uniform_(0, 2 * math.pi)
        spawn_height = torch.empty(len(env_ids), device=self.device).uniform_(0.5, 2.5)

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

        self._azimuth_history[env_ids] = 0.0
        self._elevation_history[env_ids] = 0.0
        self._history_ptr[env_ids] = 0
        self._prev_accel[env_ids] = 0.0
        self._prev_vel[env_ids] = 0.0
        self._stillness_time[env_ids] = 0.0
        self._hold_quality[env_ids] = 0.0
