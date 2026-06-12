"""Isaac Lab environment v4: Mode-conditioned cinematographer drone.

6 shooting modes (HERO, INTIMATE, EPIC, ENERGY, SOLITUDE, BEAUTY) each with
different reward weight profiles. The policy receives a one-hot mode vector as
part of its observation and learns mode-specific behavior.

10 new reward terms beyond v3:
  r_thirds       — rule-of-thirds composition (replaces center-bias r_framing)
  r_beat_sync    — camera movement aligned to music beats
  r_tracking     — match dancer velocity when they're moving
  r_hero_shot    — low angle, camera below dancer waist, looking up
  r_topdown      — brief bird's-eye moments (pitch near -90)
  r_headroom     — proper space above dancer head in frame
  r_lead_room    — more space in dancer's movement direction
  r_neg_space    — subject small in frame for isolation feel
  r_eye_level    — camera at dancer head height
  r_orbit_quality — consistent radius + angular velocity during orbits

v3 rewards preserved: r_framing (as gate), r_look_at, r_front_arc,
  r_hold_beauty, r_zoom, r_pacing, r_smoothness, r_safety, r_distance,
  r_variety, r_height, r_shot_type
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

from .cinematographer_env_cfg_v4 import CinematographerEnvCfgV4  # noqa: F401


# ── Mode definitions ──────────────────────────────────────────────────────
NUM_MODES = 6
MODE_HERO     = 0
MODE_INTIMATE = 1
MODE_EPIC     = 2
MODE_ENERGY   = 3
MODE_SOLITUDE = 4
MODE_BEAUTY   = 5

MODE_NAMES = ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"]

# Per-mode reward weight profiles  (keys must match self._reward_keys)
# Each row sums to ~1.0 (the artistic terms; safety/gate are separate)
MODE_WEIGHTS = {
    MODE_HERO: {
        "r_thirds": 0.12, "r_look_at": 0.10, "r_front_arc": 0.08,
        "r_hero_shot": 0.22, "r_hold_beauty": 0.08, "r_smoothness": 0.08,
        "r_distance": 0.04, "r_safety": 0.08, "r_tracking": 0.05,
        "r_beat_sync": 0.05, "r_headroom": 0.03, "r_orbit_quality": 0.04,
        "r_zoom": 0.03,
        # Zero out incompatible
        "r_topdown": 0.0, "r_neg_space": 0.0, "r_eye_level": 0.0,
        "r_lead_room": 0.0, "r_pacing": 0.0, "r_variety": 0.0,
        "r_height": 0.0, "r_shot_type": 0.0,
    },
    MODE_INTIMATE: {
        "r_thirds": 0.12, "r_look_at": 0.12, "r_front_arc": 0.08,
        "r_hold_beauty": 0.20, "r_headroom": 0.10, "r_eye_level": 0.10,
        "r_smoothness": 0.10, "r_safety": 0.05, "r_distance": 0.05,
        "r_beat_sync": 0.03, "r_lead_room": 0.05,
        # Zero out incompatible
        "r_hero_shot": 0.0, "r_topdown": 0.0, "r_neg_space": 0.0,
        "r_tracking": 0.0, "r_zoom": 0.0, "r_pacing": 0.0,
        "r_orbit_quality": 0.0, "r_variety": 0.0, "r_height": 0.0,
        "r_shot_type": 0.0,
    },
    MODE_EPIC: {
        "r_thirds": 0.08, "r_look_at": 0.08, "r_topdown": 0.15,
        "r_neg_space": 0.12, "r_smoothness": 0.12, "r_orbit_quality": 0.12,
        "r_height": 0.08, "r_safety": 0.05, "r_distance": 0.05,
        "r_variety": 0.05, "r_hold_beauty": 0.05, "r_beat_sync": 0.05,
        # Zero out incompatible
        "r_hero_shot": 0.0, "r_eye_level": 0.0, "r_headroom": 0.0,
        "r_front_arc": 0.0, "r_tracking": 0.0, "r_zoom": 0.0,
        "r_pacing": 0.0, "r_lead_room": 0.0, "r_shot_type": 0.0,
    },
    MODE_ENERGY: {
        "r_thirds": 0.08, "r_look_at": 0.10, "r_front_arc": 0.08,
        "r_beat_sync": 0.20, "r_tracking": 0.15, "r_zoom": 0.08,
        "r_pacing": 0.05, "r_variety": 0.06, "r_safety": 0.08,
        "r_smoothness": 0.04, "r_distance": 0.04, "r_lead_room": 0.04,
        # Zero out incompatible
        "r_hero_shot": 0.0, "r_topdown": 0.0, "r_neg_space": 0.0,
        "r_eye_level": 0.0, "r_headroom": 0.0, "r_hold_beauty": 0.0,
        "r_orbit_quality": 0.0, "r_height": 0.0, "r_shot_type": 0.0,
    },
    MODE_SOLITUDE: {
        "r_thirds": 0.08, "r_look_at": 0.08, "r_neg_space": 0.22,
        "r_smoothness": 0.12, "r_hold_beauty": 0.10, "r_height": 0.08,
        "r_safety": 0.05, "r_distance": 0.05, "r_variety": 0.05,
        "r_topdown": 0.07, "r_orbit_quality": 0.05, "r_beat_sync": 0.05,
        # Zero out incompatible
        "r_hero_shot": 0.0, "r_eye_level": 0.0, "r_headroom": 0.0,
        "r_front_arc": 0.0, "r_tracking": 0.0, "r_zoom": 0.0,
        "r_pacing": 0.0, "r_lead_room": 0.0, "r_shot_type": 0.0,
    },
    MODE_BEAUTY: {
        "r_thirds": 0.18, "r_look_at": 0.10, "r_front_arc": 0.08,
        "r_hold_beauty": 0.15, "r_orbit_quality": 0.12, "r_headroom": 0.08,
        "r_lead_room": 0.07, "r_smoothness": 0.08, "r_safety": 0.05,
        "r_distance": 0.04, "r_beat_sync": 0.05,
        # Zero out incompatible
        "r_hero_shot": 0.0, "r_topdown": 0.0, "r_neg_space": 0.0,
        "r_eye_level": 0.0, "r_tracking": 0.0, "r_zoom": 0.0,
        "r_pacing": 0.0, "r_variety": 0.0, "r_height": 0.0,
        "r_shot_type": 0.0,
    },
}

# Flatten into a (NUM_MODES, NUM_REWARDS) tensor at init time
_REWARD_KEYS = sorted(MODE_WEIGHTS[0].keys())


class CinematographerEnvV4(DirectRLEnv):
    cfg: CinematographerEnvCfgV4

    def __init__(self, cfg: CinematographerEnvCfgV4, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self._actions = torch.zeros(self.num_envs, gym.spaces.flatdim(self.single_action_space), device=self.device)
        self._thrust = torch.zeros(self.num_envs, 1, 3, device=self.device)
        self._moment = torch.zeros(self.num_envs, 1, 3, device=self.device)

        # ── Dancer trajectory ──
        data = np.load(self.cfg.mocap_npz_path)
        self._dancer_traj = torch.tensor(data["positions"], dtype=torch.float32, device=self.device)
        self._dancer_fps = float(data["fps"])
        self._dancer_T = self._dancer_traj.shape[0]
        self._dancer_time_idx = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_dancer_pos_w = torch.zeros(self.num_envs, 3, device=self.device)

        # ── Music features (optional) ──
        self._has_music = False
        self._num_music_features = 9
        if hasattr(self.cfg, "music_npz_path") and self.cfg.music_npz_path:
            try:
                mdata = np.load(self.cfg.music_npz_path)
                self._music_features = torch.tensor(
                    mdata["features"], dtype=torch.float32, device=self.device
                )  # (T_music, 9)
                self._music_fps = float(mdata.get("fps", self._dancer_fps))
                self._has_music = True
                print(f"[v4] Loaded music features: {self._music_features.shape}")
            except Exception as e:
                print(f"[v4] No music features loaded: {e}")
        if not self._has_music:
            self._music_features = torch.zeros(1, self._num_music_features, device=self.device)
            self._music_fps = self._dancer_fps

        # ── Mode state ──
        self._mode = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._mode_onehot = torch.zeros(self.num_envs, NUM_MODES, device=self.device)

        # Build reward weight tensor: (NUM_MODES, NUM_REWARDS)
        self._reward_keys = _REWARD_KEYS
        self._num_reward_terms = len(self._reward_keys)
        weight_matrix = torch.zeros(NUM_MODES, self._num_reward_terms, device=self.device)
        for m in range(NUM_MODES):
            for i, key in enumerate(self._reward_keys):
                weight_matrix[m, i] = MODE_WEIGHTS[m].get(key, 0.0)
        self._mode_weight_matrix = weight_matrix  # (6, N_rewards)

        # ── Physics state ──
        self._prev_accel = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_vel = torch.zeros(self.num_envs, 3, device=self.device)

        # ── History buffers ──
        self._history_len = 150
        self._azimuth_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._elevation_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._distance_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._velocity_history = torch.zeros(self.num_envs, self._history_len, device=self.device)
        self._history_ptr = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)

        self._prev_azimuth = torch.zeros(self.num_envs, device=self.device)
        self._prev_elevation = torch.zeros(self.num_envs, device=self.device)

        # Performer facing direction
        self._performer_facing = torch.zeros(self.num_envs, 3, device=self.device)
        self._performer_facing[:, 0] = 1.0

        # ── Robot physics ──
        self._body_id = self._robot.find_bodies("body")[0]
        self._robot_mass = wp.to_torch(self._robot.root_view.get_masses())[0].sum()
        self._gravity_magnitude = torch.tensor(self.sim.cfg.gravity, device=self.device).norm()
        self._robot_weight = (self._robot_mass * self._gravity_magnitude).item()

        # ── Constants ──
        self._safety_radius = 1.5
        self._dist_ideal = 3.0
        self._dist_margin = 2.0
        self._jerk_scale = 10.0
        self._dancer_height = 1.7  # assumed height for headroom/hero calculations

        # ── Logging ──
        log_keys = ["total"] + self._reward_keys + ["mode"]
        self._episode_sums = {
            key: torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
            for key in log_keys
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
        self._actions = actions.clone().clamp(-1.0, 1.0)
        self._thrust[:, 0, 2] = self.cfg.thrust_to_weight * self._robot_weight * (self._actions[:, 0] + 1.0) / 2.0
        self._moment[:, 0, :] = self.cfg.moment_scale * self._actions[:, 1:]

    def _apply_action(self):
        self._robot.permanent_wrench_composer.set_forces_and_torques_index(
            body_ids=self._body_id, forces=self._thrust, torques=self._moment,
        )

    # ── Post-physics: advance dancer, update histories ───────────────────

    def _post_physics_step(self):
        sim_dt = self.cfg.sim.dt * self.cfg.decimation
        steps_per_mocap_frame = max(1, round(1.0 / (self._dancer_fps * sim_dt)))
        advance = (self.episode_length_buf % steps_per_mocap_frame == 0).long()
        self._dancer_time_idx = (self._dancer_time_idx + advance) % self._dancer_T

        self._prev_dancer_pos_w[:] = self._dancer_pos_w
        base_pos = self._dancer_traj[self._dancer_time_idx]
        self._dancer_pos_w = base_pos + self._terrain.env_origins

        # History
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        rel = drone_pos - self._dancer_pos_w
        dist = rel.norm(dim=-1)
        azimuth = torch.atan2(rel[:, 0], rel[:, 1])
        horiz = (rel[:, 0]**2 + rel[:, 1]**2).sqrt()
        elevation = torch.atan2(rel[:, 2], horiz)

        ptr = self._history_ptr % self._history_len
        env_ids = torch.arange(self.num_envs, device=self.device)
        self._azimuth_history[env_ids, ptr] = azimuth
        self._elevation_history[env_ids, ptr] = elevation
        self._distance_history[env_ids, ptr] = dist

        drone_speed = wp.to_torch(self._robot.data.root_lin_vel_w).norm(dim=-1)
        self._velocity_history[env_ids, ptr] = drone_speed

        # Performer facing from velocity
        dancer_vel = (self._dancer_pos_w - self._prev_dancer_pos_w) / sim_dt
        dancer_speed = dancer_vel.norm(dim=-1, keepdim=True)
        moving_mask = (dancer_speed > 0.1).float()
        new_facing = dancer_vel / (dancer_speed + 1e-8)
        self._performer_facing = moving_mask * new_facing + (1.0 - moving_mask) * self._performer_facing

        self._history_ptr += 1
        self._prev_azimuth = azimuth
        self._prev_elevation = elevation

        return super()._post_physics_step()

    # ── Observations: 20 (state) + 6 (mode) + 9 (music) = 35 ────────────

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

        # Music features for this timestep
        if self._has_music:
            # Map dancer time to music time
            music_idx = (self._dancer_time_idx.float() * self._music_fps / self._dancer_fps).long()
            music_idx = music_idx.clamp(0, self._music_features.shape[0] - 1)
            music_obs = self._music_features[music_idx]  # (N, 9)
        else:
            music_obs = torch.zeros(self.num_envs, self._num_music_features, device=self.device)

        obs = torch.cat([
            wp.to_torch(self._robot.data.root_lin_vel_b),      # 3
            wp.to_torch(self._robot.data.root_ang_vel_b),      # 3
            wp.to_torch(self._robot.data.projected_gravity_b), # 3
            rel_dancer_b,                                       # 3
            rel_vel_b,                                          # 3
            dist,                                               # 1
            azimuth,                                            # 1
            elevation,                                          # 1
            self._mode_onehot,                                  # 6 (mode)
            music_obs,                                          # 9 (music)
        ], dim=-1)  # total = 33

        return {"policy": obs}

    # ── Rewards ──────────────────────────────────────────────────────────

    def _get_rewards(self) -> torch.Tensor:
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        drone_quat = wp.to_torch(self._robot.data.root_quat_w)
        sim_dt = self.cfg.sim.dt * self.cfg.decimation

        # ── Drone forward vector ──
        qw, qx, qy, qz = drone_quat[:, 0], drone_quat[:, 1], drone_quat[:, 2], drone_quat[:, 3]
        fwd_x = 1 - 2*(qy*qy + qz*qz)
        fwd_y = 2*(qx*qy + qw*qz)
        fwd_z = 2*(qx*qz - qw*qy)
        drone_forward = torch.stack([fwd_x, fwd_y, fwd_z], dim=-1)

        # ── Velocity, acceleration, jerk ──
        vel = wp.to_torch(self._robot.data.root_lin_vel_w)
        accel = (vel - self._prev_vel) / sim_dt
        jerk = (accel - self._prev_accel) / sim_dt
        self._prev_vel = vel.clone()
        self._prev_accel = accel.clone()

        # ── Basic geometry ──
        rel = self._dancer_pos_w - drone_pos
        dist = rel.norm(dim=-1)
        to_dancer = rel / (dist.unsqueeze(-1) + 1e-8)
        fwd_norm = drone_forward / (drone_forward.norm(dim=-1, keepdim=True) + 1e-8)
        cos_angle = (to_dancer * fwd_norm).sum(dim=-1).clamp(-1, 1)
        frame_angle = cos_angle.acos()

        # Dancer velocity for tracking
        dancer_vel_w = (self._dancer_pos_w - self._prev_dancer_pos_w) / sim_dt
        dancer_speed = dancer_vel_w.norm(dim=-1)

        # ── Music features for beat sync ──
        if self._has_music:
            music_idx = (self._dancer_time_idx.float() * self._music_fps / self._dancer_fps).long()
            music_idx = music_idx.clamp(0, self._music_features.shape[0] - 1)
            music_feat = self._music_features[music_idx]
            # features: [bpm, beat_phase, onset, rms, spec_centroid, spec_rolloff, bass, mid, treble]
            beat_onset = music_feat[:, 2]   # 1.0 on beat frames
            audio_rms = music_feat[:, 3]    # energy
        else:
            beat_onset = torch.zeros(self.num_envs, device=self.device)
            audio_rms = torch.ones(self.num_envs, device=self.device) * 0.5

        # ══════════════════════════════════════════════════════════════════
        # COMPUTE ALL REWARD TERMS (each returns a per-env scalar)
        # ══════════════════════════════════════════════════════════════════

        all_rewards = {}

        # ── r_beat_sync: velocity changes land on music beats ──
        # Reward high acceleration magnitude on beat onset frames
        accel_mag = accel.norm(dim=-1)
        # On beat frames: reward having accel > threshold. Off beats: no penalty.
        beat_accel_score = (accel_mag / 2.0).tanh()  # 0-1
        r_beat_sync = beat_onset * beat_accel_score  # only matters on beats
        all_rewards["r_beat_sync"] = r_beat_sync

        # ── r_distance ──
        dist_err = dist - self._dist_ideal
        r_distance = 1.0 - (dist_err.abs() / self._dist_margin).tanh()
        all_rewards["r_distance"] = r_distance

        # ── r_eye_level: camera at dancer head height ──
        dancer_head_height = self._dancer_pos_w[:, 2] + self._dancer_height
        height_diff = (drone_pos[:, 2] - dancer_head_height).abs()
        r_eye_level = 1.0 - (height_diff / 0.5).tanh()
        all_rewards["r_eye_level"] = r_eye_level

        # ── r_front_arc: stay in front 180 arc ──
        to_drone_horiz = -rel.clone()
        to_drone_horiz[:, 2] = 0
        to_drone_horiz = to_drone_horiz / (to_drone_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        facing_horiz = self._performer_facing.clone()
        facing_horiz[:, 2] = 0
        facing_horiz = facing_horiz / (facing_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        front_cos = (to_drone_horiz * facing_horiz).sum(dim=-1)
        is_behind = (front_cos < 0).float()
        r_front_arc = is_behind * (-5.0)
        all_rewards["r_front_arc"] = r_front_arc

        # ── r_headroom: proper space above head in virtual frame ──
        # Project dancer head to camera's vertical frame axis
        # Approximate: elevation angle from drone to dancer head
        to_head = self._dancer_pos_w.clone()
        to_head[:, 2] += self._dancer_height
        to_head = to_head - drone_pos
        to_head_norm = to_head / (to_head.norm(dim=-1, keepdim=True) + 1e-8)
        # Dot with drone forward → vertical offset in frame
        head_in_fwd = (to_head_norm * fwd_norm).sum(dim=-1)
        # Head should be in upper portion of FOV but not at edge
        # Ideal: head_in_fwd between 0.85 and 0.95 of forward cone
        head_offset = (head_in_fwd - 0.9).abs()
        r_headroom = 1.0 - (head_offset / 0.15).tanh()
        all_rewards["r_headroom"] = r_headroom

        # ── r_height: elevation range variety ──
        el_hist = self._elevation_history
        el_range = el_hist.max(dim=-1).values - el_hist.min(dim=-1).values
        r_height = (el_range / math.radians(50)).clamp(0, 1)
        all_rewards["r_height"] = r_height

        # ── r_hero_shot: low angle, camera below waist, looking up ──
        dancer_waist_height = self._dancer_pos_w[:, 2] + self._dancer_height * 0.5
        is_below_waist = (drone_pos[:, 2] < dancer_waist_height).float()
        # Check that camera is tilted upward (forward vector has positive Z component toward dancer)
        looking_up = (to_dancer[:, 2] > 0).float()  # dancer is above drone
        r_hero_shot = is_below_waist * looking_up * r_distance  # only reward if also at good distance
        all_rewards["r_hero_shot"] = r_hero_shot

        # ── r_hold_beauty: pause on good frames ──
        frame_quality = (1.0 - (frame_angle / math.radians(15)).tanh()) * \
                        (1.0 - (frame_angle / math.radians(10)).tanh())
        is_good_frame = (frame_quality / 0.5).clamp(0.0, 1.0)
        drone_speed = vel.norm(dim=-1)
        stillness = 1.0 - (drone_speed / 2.0).tanh()
        r_hold_beauty = is_good_frame * stillness
        all_rewards["r_hold_beauty"] = r_hold_beauty

        # ── r_lead_room: more frame space in dancer's movement direction ──
        # Project dancer velocity onto the camera's lateral axis
        # Drone right axis: cross(forward, up) ≈ cross(fwd_norm, [0,0,1])
        up = torch.zeros_like(fwd_norm)
        up[:, 2] = 1.0
        right = torch.cross(fwd_norm, up, dim=-1)
        right = right / (right.norm(dim=-1, keepdim=True) + 1e-8)
        # Dancer velocity projected onto camera right axis
        dancer_vel_lateral = (dancer_vel_w * right).sum(dim=-1)
        # Dancer position in camera lateral frame
        dancer_lateral = (rel * right).sum(dim=-1)
        # Lead room: dancer moving right → dancer should be on left of frame (negative lateral)
        # So sign(velocity) should be opposite to sign(position)
        has_lead_room = (dancer_vel_lateral.sign() * (-dancer_lateral.sign())).clamp(0, 1)
        # Only matters when dancer is actually moving laterally
        lateral_moving = (dancer_vel_lateral.abs() > 0.2).float()
        r_lead_room = has_lead_room * lateral_moving
        all_rewards["r_lead_room"] = r_lead_room

        # ── r_look_at: horizontal aim at dancer ──
        to_dancer_horiz_look = rel.clone()
        to_dancer_horiz_look[:, 2] = 0
        to_dancer_horiz_look = to_dancer_horiz_look / (to_dancer_horiz_look.norm(dim=-1, keepdim=True) + 1e-8)
        fwd_horiz = drone_forward.clone()
        fwd_horiz[:, 2] = 0
        fwd_horiz = fwd_horiz / (fwd_horiz.norm(dim=-1, keepdim=True) + 1e-8)
        cos_look = (to_dancer_horiz_look * fwd_horiz).sum(dim=-1).clamp(-1, 1)
        look_angle = cos_look.acos()
        r_look_at = 1.0 - (look_angle / math.radians(10)).tanh()
        all_rewards["r_look_at"] = r_look_at

        # ── r_neg_space: subject small in frame (for SOLITUDE/EPIC) ──
        # Reward when dancer occupies < 20% of frame (far away, high up)
        half_vfov = math.atan(24.0 / (2 * 35.0))
        frame_coverage = self._dancer_height / (2.0 * dist * math.tan(half_vfov) + 1e-8)
        r_neg_space = (1.0 - frame_coverage / 0.3).clamp(0, 1)  # reward when coverage < 30%
        all_rewards["r_neg_space"] = r_neg_space

        # ── r_orbit_quality: consistent radius + angular velocity ──
        filled = self._history_ptr.clamp(max=self._history_len).long()
        if filled.min() >= 20:
            az_recent = self._azimuth_history[:, -20:]
            d_recent = self._distance_history[:, -20:]
            # Radius consistency (low variance = good orbit)
            d_std = d_recent.std(dim=-1)
            radius_score = 1.0 - (d_std / 0.5).tanh()
            # Angular velocity consistency
            az_diff = az_recent[:, 1:] - az_recent[:, :-1]
            # Handle wraparound
            az_diff = torch.atan2(az_diff.sin(), az_diff.cos())
            az_vel_std = az_diff.std(dim=-1)
            az_vel_mean = az_diff.abs().mean(dim=-1)
            # Good orbit = moving (mean > 0) with consistent speed (low std)
            angular_score = az_vel_mean.clamp(0, 0.1) / 0.1 * (1.0 - (az_vel_std / 0.05).tanh())
            r_orbit_quality = radius_score * angular_score
        else:
            r_orbit_quality = torch.zeros(self.num_envs, device=self.device)
        all_rewards["r_orbit_quality"] = r_orbit_quality

        # ── r_pacing: alternate movement and stillness ──
        v_hist = self._velocity_history
        is_moving = (v_hist > 0.3).float()
        move_ratio = is_moving.mean(dim=-1)
        pace_transitions = (is_moving[:, 1:] - is_moving[:, :-1]).abs().sum(dim=-1)
        pace_trans_score = (pace_transitions / 6.0).clamp(0.0, 1.0)
        pace_ratio_score = (1.0 - (move_ratio - 0.5).abs() * 2).clamp(0.0, 1.0)
        r_pacing = 0.6 * pace_ratio_score + 0.4 * pace_trans_score
        all_rewards["r_pacing"] = r_pacing

        # ── r_safety ──
        violation = (dist < self._safety_radius).float()
        r_safety = violation * (-10.0)
        all_rewards["r_safety"] = r_safety

        # ── r_shot_type: mix of shot sizes ──
        d_hist = self._distance_history
        coverage_hist = 2.0 * d_hist * math.tan(half_vfov)
        shot_type = (coverage_hist >= 0.8).float() + (coverage_hist >= 1.5).float()
        has_close = (shot_type == 0).any(dim=-1).float()
        has_half = (shot_type == 1).any(dim=-1).float()
        has_full = (shot_type == 2).any(dim=-1).float()
        num_types = has_close + has_half + has_full
        transitions = (shot_type[:, 1:] - shot_type[:, :-1]).abs().gt(0).sum(dim=-1).float()
        r_shot_type = 0.6 * (num_types / 3.0) + 0.4 * (transitions / 5.0).clamp(0, 1)
        all_rewards["r_shot_type"] = r_shot_type

        # ── r_smoothness ──
        jerk_mag = jerk.norm(dim=-1)
        r_smoothness = 1.0 - (jerk_mag / self._jerk_scale).tanh()
        all_rewards["r_smoothness"] = r_smoothness

        # ── r_thirds: rule-of-thirds composition ──
        # Project dancer position onto camera image plane
        # Use dot products with camera right and up axes
        cam_up = torch.zeros_like(fwd_norm)
        cam_up[:, 2] = 1.0  # world up as approximation
        cam_right = torch.cross(fwd_norm, cam_up, dim=-1)
        cam_right = cam_right / (cam_right.norm(dim=-1, keepdim=True) + 1e-8)
        cam_up_actual = torch.cross(cam_right, fwd_norm, dim=-1)

        # Dancer offset in screen space (normalized -1 to 1)
        screen_x = (to_dancer * cam_right).sum(dim=-1)  # lateral
        screen_y = (to_dancer * cam_up_actual).sum(dim=-1)  # vertical
        # Normalize by FOV
        screen_x_norm = (screen_x / math.tan(half_vfov)).clamp(-1, 1)
        screen_y_norm = (screen_y / math.tan(half_vfov)).clamp(-1, 1)
        # Map to 0-1 range
        sx = (screen_x_norm + 1) / 2  # 0=left, 1=right
        sy = (screen_y_norm + 1) / 2  # 0=bottom, 1=top

        # Distance to nearest thirds intersection point
        thirds_x = torch.tensor([1/3, 2/3, 1/3, 2/3], device=self.device)
        thirds_y = torch.tensor([1/3, 1/3, 2/3, 2/3], device=self.device)
        dx = sx.unsqueeze(-1) - thirds_x.unsqueeze(0)  # (N, 4)
        dy = sy.unsqueeze(-1) - thirds_y.unsqueeze(0)
        thirds_dist = (dx**2 + dy**2).sqrt().min(dim=-1).values  # (N,)
        # Max distance from any thirds point is ~0.47 (center to corner)
        r_thirds = 1.0 - (thirds_dist / 0.15).tanh()  # reward peaks when < 0.1 from intersection
        all_rewards["r_thirds"] = r_thirds

        # ── r_topdown: brief bird's-eye moments ──
        # Camera pointing nearly straight down + high altitude
        elevation_angle = torch.atan2(
            rel[:, 2], (rel[:, 0]**2 + rel[:, 1]**2).sqrt() + 1e-8
        )
        # Negative elevation = drone above dancer. Want < -70 degrees
        is_overhead = (elevation_angle < math.radians(-70)).float()
        high_enough = (drone_pos[:, 2] > self._dancer_pos_w[:, 2] + 3.0).float()
        r_topdown = is_overhead * high_enough
        all_rewards["r_topdown"] = r_topdown

        # ── r_tracking: match dancer velocity when dancer is moving ──
        vel_diff = (vel[:, :2] - dancer_vel_w[:, :2]).norm(dim=-1)  # horizontal only
        tracking_score = 1.0 - (vel_diff / 1.5).tanh()
        is_dancer_moving = (dancer_speed > 0.3).float()
        r_tracking = tracking_score * is_dancer_moving * r_distance  # only when dancer moves + good dist
        all_rewards["r_tracking"] = r_tracking

        # ── r_variety: azimuth variety ──
        filled_f = self._history_ptr.clamp(max=self._history_len).float()
        az_hist = self._azimuth_history
        sin_mean = az_hist.sin().sum(dim=-1) / filled_f.clamp(min=1)
        cos_mean = az_hist.cos().sum(dim=-1) / filled_f.clamp(min=1)
        R = (sin_mean**2 + cos_mean**2).sqrt()
        circ_std = (-2.0 * R.clamp(1e-8, 1.0).log()).sqrt()
        r_variety = (circ_std / math.radians(30)).clamp(0, 1)
        all_rewards["r_variety"] = r_variety

        # ── r_zoom: push-in / pull-out dynamics ──
        d_hist_zoom = self._distance_history
        kernel_size = 10
        if d_hist_zoom.shape[-1] >= kernel_size:
            smoothed = d_hist_zoom.unfold(-1, kernel_size, 1).mean(dim=-1)
            diff_d = smoothed[:, 1:] - smoothed[:, :-1]
            if diff_d.shape[-1] > 1:
                sign_ch = (diff_d[:, 1:].sign() - diff_d[:, :-1].sign()).abs().gt(0).sum(dim=-1).float()
                r_zoom = 1.0 - (sign_ch - 4.0).abs() / 5.0
                r_zoom = r_zoom.clamp(0.0, 1.0)
            else:
                r_zoom = torch.zeros(self.num_envs, device=self.device)
        else:
            r_zoom = torch.zeros(self.num_envs, device=self.device)
        all_rewards["r_zoom"] = r_zoom

        # ══════════════════════════════════════════════════════════════════
        # MODE-CONDITIONED WEIGHTED SUM
        # ══════════════════════════════════════════════════════════════════

        # Framing gate (applied to all modes)
        in_frame = (frame_angle < math.radians(60)).float()
        framing_gate = 0.3 + 0.7 * in_frame

        # Stack all rewards in canonical order: (N, num_rewards)
        reward_stack = torch.stack([all_rewards[k] for k in self._reward_keys], dim=-1)

        # Gather mode weights for each env: (N, num_rewards)
        env_weights = self._mode_weight_matrix[self._mode]  # index by mode per env

        # Weighted sum per env
        total = (reward_stack * env_weights).sum(dim=-1) * framing_gate * self.cfg.reward_scale * self.step_dt

        # ── Logging ──
        self._episode_sums["total"] += total
        self._episode_sums["mode"] += self._mode.float() * self.step_dt
        for key in self._reward_keys:
            self._episode_sums[key] += all_rewards[key] * self.step_dt

        return total

    # ── Dones ────────────────────────────────────────────────────────────

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        drone_pos = wp.to_torch(self._robot.data.root_pos_w)
        died = torch.logical_or(drone_pos[:, 2] < 0.1, drone_pos[:, 2] > 15.0)  # wider range for EPIC mode
        dist = (drone_pos - self._dancer_pos_w).norm(dim=-1)
        died = torch.logical_or(died, dist > 20.0)  # wider for SOLITUDE/EPIC
        return died, time_out

    # ── Reset ────────────────────────────────────────────────────────────

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

        # ── Randomize mode per episode ──
        self._mode[env_ids] = torch.randint(0, NUM_MODES, (len(env_ids),), device=self.device)
        self._mode_onehot[env_ids] = 0.0
        self._mode_onehot[env_ids, self._mode[env_ids].long()] = 1.0

        # ── Randomize dancer start time ──
        self._dancer_time_idx[env_ids] = torch.randint(0, self._dancer_T, (len(env_ids),), device=self.device)
        base_pos = self._dancer_traj[self._dancer_time_idx[env_ids]]
        self._dancer_pos_w[env_ids] = base_pos + self._terrain.env_origins[env_ids]
        self._prev_dancer_pos_w[env_ids] = self._dancer_pos_w[env_ids]

        # ── Spawn drone — mode-dependent distance range ──
        default_root_pose = wp.to_torch(self._robot.data.default_root_pose)[env_ids].clone()
        default_root_pose[:, :3] += self._terrain.env_origins[env_ids]

        # Mode-specific spawn ranges
        mode_ids = self._mode[env_ids]
        spawn_dist_min = torch.where(
            (mode_ids == MODE_EPIC) | (mode_ids == MODE_SOLITUDE),
            torch.tensor(5.0, device=self.device),
            torch.tensor(2.0, device=self.device),
        )
        spawn_dist_max = torch.where(
            (mode_ids == MODE_EPIC) | (mode_ids == MODE_SOLITUDE),
            torch.tensor(10.0, device=self.device),
            torch.where(
                mode_ids == MODE_INTIMATE,
                torch.tensor(3.0, device=self.device),
                torch.tensor(5.0, device=self.device),
            ),
        )
        spawn_height_min = torch.where(
            mode_ids == MODE_HERO,
            torch.tensor(0.3, device=self.device),
            torch.where(
                mode_ids == MODE_EPIC,
                torch.tensor(3.0, device=self.device),
                torch.tensor(0.5, device=self.device),
            ),
        )
        spawn_height_max = torch.where(
            mode_ids == MODE_HERO,
            torch.tensor(0.8, device=self.device),
            torch.where(
                mode_ids == MODE_EPIC,
                torch.tensor(8.0, device=self.device),
                torch.tensor(2.5, device=self.device),
            ),
        )

        spawn_dist = torch.empty(len(env_ids), device=self.device).uniform_(0, 1)
        spawn_dist = spawn_dist_min + spawn_dist * (spawn_dist_max - spawn_dist_min)
        spawn_angle = torch.empty(len(env_ids), device=self.device).uniform_(0, 2 * math.pi)
        spawn_height = torch.empty(len(env_ids), device=self.device).uniform_(0, 1)
        spawn_height = spawn_height_min + spawn_height * (spawn_height_max - spawn_height_min)

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
        self._velocity_history[env_ids] = 0.0
        self._history_ptr[env_ids] = 0
        self._prev_accel[env_ids] = 0.0
        self._prev_vel[env_ids] = 0.0
