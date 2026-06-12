"""
HumanoidAmpLowerBodyEnv V2 — Curriculum-ready with survival bonus.

Changes from V1:
1. Added survival bonus (per-step reward for staying alive)
2. Rebalanced reward weights: more upright/height, less foot contact
3. Added curriculum support: task/style weights readable from cfg
4. Stricter termination: terminate on head below feet too
"""
from __future__ import annotations

import os
import gymnasium as gym
import numpy as np
import torch
import warp as wp

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import quat_apply

from .humanoid_amp_lower_body_env_cfg import HumanoidAmpLowerBodyEnvCfg

# Import the motion loader from the existing AMP task.
import sys

_AMP_DIR = None
for _candidate in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "humanoid_amp"),
    "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp",
]:
    if os.path.isdir(_candidate):
        _AMP_DIR = _candidate
        break
if _AMP_DIR is None:
    raise ImportError(
        "Cannot find humanoid_amp task directory for MotionLoader. "
        "Ensure this module is deployed alongside the standard AMP task."
    )
sys.path.insert(0, _AMP_DIR)
from motions import MotionLoader


class HumanoidAmpLowerBodyEnv(DirectRLEnv):
    """Pinned-upper-body AMP environment for lower body prediction. V2 with curriculum."""

    cfg: HumanoidAmpLowerBodyEnvCfg

    # Body index splits
    UPPER_BODY_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # pelvis..left_hand
    LOWER_BODY_INDICES = [9, 10, 11, 12, 13, 14]        # thighs..feet

    # DOF index splits
    UPPER_DOF_INDICES = list(range(0, 14))   # abdomen..left_elbow
    LOWER_DOF_INDICES = list(range(14, 28))  # right_hip..left_ankle

    def __init__(self, cfg: HumanoidAmpLowerBodyEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        # DOF limits for action scaling (lower body only)
        soft_limits = wp.to_torch(self.robot.data.soft_joint_pos_limits)
        lower_limits = soft_limits[0, self.LOWER_DOF_INDICES, 0]
        upper_limits = soft_limits[0, self.LOWER_DOF_INDICES, 1]
        self.action_offset = 0.5 * (upper_limits + lower_limits)
        self.action_scale = upper_limits - lower_limits

        # Load reference motion for AMP discriminator
        self._motion_loader = MotionLoader(
            motion_file=self.cfg.amp_motion_file, device=self.device
        )

        # Load Quest trajectory for upper body pinning
        self._load_quest_trajectory()

        # Body and DOF index lookups
        key_body_names = ["right_hand", "left_hand", "right_foot", "left_foot"]
        self.ref_body_index = self.robot.data.body_names.index(self.cfg.reference_body)
        self.key_body_indexes = [self.robot.data.body_names.index(n) for n in key_body_names]
        self.motion_dof_indexes = self._motion_loader.get_dof_index(self.robot.data.joint_names)
        self.motion_ref_body_index = self._motion_loader.get_body_index([self.cfg.reference_body])[0]
        self.motion_key_body_indexes = self._motion_loader.get_body_index(key_body_names)

        # Body indices for termination checks
        self.head_body_index = self.robot.data.body_names.index("head")
        self.rfoot_body_index = self.robot.data.body_names.index("right_foot")
        self.lfoot_body_index = self.robot.data.body_names.index("left_foot")
        self.pelvis_body_index = self.robot.data.body_names.index("pelvis")

        # AMP observation buffer
        self.amp_observation_size = self.cfg.num_amp_observations * self.cfg.amp_observation_space
        self.amp_observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.amp_observation_size,)
        )
        self.amp_observation_buffer = torch.zeros(
            (self.num_envs, self.cfg.num_amp_observations, self.cfg.amp_observation_space),
            device=self.device,
        )

        # Per-env trajectory time index
        self.env_traj_t = torch.zeros(self.num_envs, dtype=torch.float32, device=self.device)
        self._sim_dt = float(self.cfg.sim.dt) * self.cfg.decimation

        # Upper body pinning gains (body-level PD)
        self._pin_kp = self.cfg.upper_body_kp
        self._pin_kd = self.cfg.upper_body_kd
        self._max_torque = self.cfg.max_pinning_torque

        print(f"[LB env v2] Upper body pinning: kp={self._pin_kp}, kd={self._pin_kd}, max_torque={self._max_torque}")
        print(f"[LB env v2] Quest trajectory: {self._quest_T} frames, {self._quest_duration:.1f}s")
        print(f"[LB env v2] AMP reference: {self._motion_loader.num_frames} frames")
        print(f"[LB env v2] Reward weights: upright={self.cfg.reward_upright_weight}, "
              f"height={self.cfg.reward_height_weight}, foot={self.cfg.reward_foot_contact_weight}, "
              f"energy={self.cfg.reward_energy_weight}, survival={self.cfg.reward_survival_weight}")
        print(f"[LB env v2] Termination: height<{self.cfg.termination_height}m, "
              f"head_below_feet={self.cfg.terminate_head_below_feet}")

    def _load_quest_trajectory(self):
        """Load the Quest upper-body trajectory for pinning."""
        traj_path = self.cfg.quest_trajectory_file
        if not os.path.isfile(traj_path):
            raise FileNotFoundError(f"Quest trajectory not found: {traj_path}")

        data = np.load(traj_path, allow_pickle=True)
        self._quest_fps = int(data["fps"])
        self._quest_dt = 1.0 / self._quest_fps

        self._quest_body_pos = torch.tensor(
            data["body_positions"], dtype=torch.float32, device=self.device
        )
        self._quest_body_rot = torch.tensor(
            data["body_rotations"], dtype=torch.float32, device=self.device
        )

        self._quest_T = self._quest_body_pos.shape[0]
        self._quest_duration = self._quest_dt * (self._quest_T - 1)

    def _sample_quest_at(self, times: torch.Tensor):
        """Sample Quest trajectory at given times via linear interpolation."""
        phase = torch.clamp(times / self._quest_duration, 0.0, 1.0)
        idx_f = phase * (self._quest_T - 1)
        idx0 = idx_f.long().clamp(0, self._quest_T - 2)
        idx1 = (idx0 + 1).clamp(max=self._quest_T - 1)
        blend = (idx_f - idx0.float()).unsqueeze(-1).unsqueeze(-1)

        pos = (1 - blend) * self._quest_body_pos[idx0] + blend * self._quest_body_pos[idx1]
        rot = (1 - blend) * self._quest_body_rot[idx0] + blend * self._quest_body_rot[idx1]
        rot = rot / (rot.norm(dim=-1, keepdim=True) + 1e-8)

        return pos, rot

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot)
        spawn_ground_plane(
            prim_path="/World/ground",
            cfg=GroundPlaneCfg(
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.0, dynamic_friction=1.0, restitution=0.0,
                ),
            ),
        )
        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=["/World/ground"])
        self.scene.articulations["robot"] = self.robot

        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

    def _pre_physics_step(self, actions: torch.Tensor):
        self.actions = actions.clone()

        # Advance trajectory time
        self.env_traj_t = (self.env_traj_t + self._sim_dt) % self._quest_duration

        # --- Upper body pinning via external torques ---
        target_pos, target_rot = self._sample_quest_at(self.env_traj_t)

        cur_quat = wp.to_torch(self.robot.data.body_quat_w)
        cur_angvel = wp.to_torch(self.robot.data.body_ang_vel_w)

        cur_rot_xyzw = torch.cat([cur_quat[..., 1:], cur_quat[..., :1]], dim=-1)

        forces = torch.zeros(self.num_envs, len(self.robot.data.body_names), 3, device=self.device)
        torques = torch.zeros_like(forces)

        for ub_idx in self.UPPER_BODY_INDICES:
            q_target = target_rot[:, ub_idx]
            q_current = cur_rot_xyzw[:, ub_idx]

            q_cur_conj = q_current.clone()
            q_cur_conj[:, :3] *= -1

            q_err = _quat_mul_xyzw(q_target, q_cur_conj)
            q_err = torch.where(q_err[:, 3:4] < 0, -q_err, q_err)

            torque = self._pin_kp * 2.0 * q_err[:, :3] - self._pin_kd * cur_angvel[:, ub_idx]
            torque = torch.clamp(torque, -self._max_torque, self._max_torque)
            torques[:, ub_idx] = torque

        self.robot.set_external_force_and_torque(forces=forces, torques=torques)

    def _apply_action(self):
        """Apply policy actions to lower body DOFs only."""
        lower_targets = self.action_offset + self.action_scale * self.actions

        full_targets = wp.to_torch(self.robot.data.joint_pos).clone()
        full_targets[:, self.LOWER_DOF_INDICES] = lower_targets

        self.robot.set_joint_position_target_index(target=full_targets)

    def _get_observations(self) -> dict:
        """Build observation: lower body state + upper body state + root info."""
        joint_pos = wp.to_torch(self.robot.data.joint_pos)
        joint_vel = wp.to_torch(self.robot.data.joint_vel)
        body_pos = wp.to_torch(self.robot.data.body_pos_w)
        body_quat = wp.to_torch(self.robot.data.body_quat_w)
        body_linvel = wp.to_torch(self.robot.data.body_lin_vel_w)
        body_angvel = wp.to_torch(self.robot.data.body_ang_vel_w)

        obs = compute_lb_obs(
            joint_pos[:, self.LOWER_DOF_INDICES],
            joint_vel[:, self.LOWER_DOF_INDICES],
            joint_pos[:, self.UPPER_DOF_INDICES],
            joint_vel[:, self.UPPER_DOF_INDICES],
            body_pos[:, self.ref_body_index],
            body_quat[:, self.ref_body_index],
            body_linvel[:, self.ref_body_index],
            body_angvel[:, self.ref_body_index],
            body_pos[:, self.key_body_indexes],
        )

        amp_obs = compute_amp_obs(
            joint_pos,
            joint_vel,
            body_pos[:, self.ref_body_index],
            body_quat[:, self.ref_body_index],
            body_linvel[:, self.ref_body_index],
            body_angvel[:, self.ref_body_index],
            body_pos[:, self.key_body_indexes],
        )

        for i in reversed(range(self.cfg.num_amp_observations - 1)):
            self.amp_observation_buffer[:, i + 1] = self.amp_observation_buffer[:, i]
        self.amp_observation_buffer[:, 0] = amp_obs.clone()
        self.extras = {"amp_obs": self.amp_observation_buffer.view(-1, self.amp_observation_size)}

        return {"policy": obs}

    def _get_rewards(self) -> torch.Tensor:
        """Compute reward with survival bonus and stronger upright incentive."""
        body_pos = wp.to_torch(self.robot.data.body_pos_w)
        body_quat = wp.to_torch(self.robot.data.body_quat_w)
        joint_vel = wp.to_torch(self.robot.data.joint_vel)

        # Root (pelvis) state — use pelvis body, not torso (index 0)
        root_pos = body_pos[:, self.pelvis_body_index]
        root_quat = body_quat[:, self.pelvis_body_index]

        # Head position for bonus
        head_pos = body_pos[:, self.head_body_index]

        # Foot positions
        right_foot_z = body_pos[:, self.rfoot_body_index, 2]
        left_foot_z = body_pos[:, self.lfoot_body_index, 2]

        # ---- Reward terms ----

        # 1. Upright reward: pelvis up vector · world Z (strong)
        world_up = torch.tensor([0.0, 0.0, 1.0], device=self.device)
        pelvis_up = quat_apply(root_quat, world_up.expand(self.num_envs, -1))
        r_upright = torch.clamp(pelvis_up[:, 2], 0.0, 1.0)

        # 2. Root height reward: pelvis Z should be near target
        z_target = self.cfg.target_root_height
        r_height = torch.exp(-10.0 * (root_pos[:, 2] - z_target) ** 2)

        # 3. Foot contact: at least one foot near ground (Z ≈ 0)
        right_contact = torch.exp(-100.0 * torch.clamp(right_foot_z, min=0.0) ** 2)
        left_contact = torch.exp(-100.0 * torch.clamp(left_foot_z, min=0.0) ** 2)
        r_foot_contact = torch.max(right_contact, left_contact)

        # 4. Energy penalty: penalize excessive lower body joint velocities
        lower_vel = joint_vel[:, self.LOWER_DOF_INDICES]
        r_energy = torch.exp(-0.01 * (lower_vel ** 2).sum(dim=-1))

        # 5. Survival bonus: constant reward for being alive (head above pelvis)
        head_above_pelvis = (head_pos[:, 2] > root_pos[:, 2]).float()
        r_survival = head_above_pelvis  # 1.0 if head above pelvis, 0.0 otherwise

        # 6. Head height bonus: reward head being at natural height (~1.4m)
        r_head_height = torch.exp(-5.0 * (head_pos[:, 2] - 1.4) ** 2)

        # Combine rewards
        reward = (
            self.cfg.reward_upright_weight * r_upright
            + self.cfg.reward_height_weight * r_height
            + self.cfg.reward_foot_contact_weight * r_foot_contact
            + self.cfg.reward_energy_weight * r_energy
            + self.cfg.reward_survival_weight * r_survival
            + self.cfg.reward_head_height_weight * r_head_height
        )

        return reward

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        body_pos = wp.to_torch(self.robot.data.body_pos_w)
        root_z = body_pos[:, self.pelvis_body_index, 2]

        if self.cfg.early_termination:
            # Terminate if pelvis drops below threshold
            died = root_z < self.cfg.termination_height

            # Also terminate if head is below feet (humanoid flipped)
            if self.cfg.terminate_head_below_feet:
                head_z = body_pos[:, self.head_body_index, 2]
                foot_z = torch.min(
                    body_pos[:, self.rfoot_body_index, 2],
                    body_pos[:, self.lfoot_body_index, 2],
                )
                head_below_feet = head_z < foot_z - 0.1  # 10cm tolerance
                died = died | head_below_feet
        else:
            died = torch.zeros_like(time_out)

        return died, time_out

    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = (
                wp.to_torch(self.robot._ALL_INDICES)
                if isinstance(self.robot._ALL_INDICES, wp.array)
                else self.robot._ALL_INDICES
            )
        self.robot.reset(env_ids)
        super()._reset_idx(env_ids)

        num = env_ids.shape[0]
        times = self._motion_loader.sample_times(num)

        (dof_pos, dof_vel, body_pos, body_rot,
         body_linvel, body_angvel) = self._motion_loader.sample(num, times)

        torso_idx = self._motion_loader.get_body_index(["torso"])[0]
        root_state = torch.cat([
            wp.to_torch(self.robot.data.default_root_pose)[env_ids],
            wp.to_torch(self.robot.data.default_root_vel)[env_ids],
        ], dim=-1).clone()
        root_state[:, 0:3] = body_pos[:, torso_idx] + self.scene.env_origins[env_ids]
        root_state[:, 2] += 0.15
        root_state[:, 3:7] = body_rot[:, torso_idx]
        root_state[:, 7:10] = body_linvel[:, torso_idx]
        root_state[:, 10:13] = body_angvel[:, torso_idx]

        dof_p = dof_pos[:, self.motion_dof_indexes]
        dof_v = dof_vel[:, self.motion_dof_indexes]

        self.robot.write_root_link_pose_to_sim_index(root_pose=root_state[:, :7], env_ids=env_ids)
        self.robot.write_root_com_velocity_to_sim_index(root_velocity=root_state[:, 7:], env_ids=env_ids)
        self.robot.write_joint_position_to_sim_index(position=dof_p, env_ids=env_ids)
        self.robot.write_joint_velocity_to_sim_index(velocity=dof_v, env_ids=env_ids)

        self.env_traj_t[env_ids] = torch.tensor(
            times, dtype=torch.float32, device=self.device
        ) % self._quest_duration

        amp_obs = self.collect_reference_motions(num, times)
        self.amp_observation_buffer[env_ids] = amp_obs.view(
            num, self.cfg.num_amp_observations, -1
        )

    def collect_reference_motions(self, num_samples: int,
                                  current_times: np.ndarray | None = None) -> torch.Tensor:
        """Collect AMP reference observations."""
        if current_times is None:
            current_times = self._motion_loader.sample_times(num_samples)
        times = (
            np.expand_dims(current_times, axis=-1)
            - self._motion_loader.dt * np.arange(0, self.cfg.num_amp_observations)
        ).flatten()

        (dof_pos, dof_vel, body_pos, body_rot,
         body_linvel, body_angvel) = self._motion_loader.sample(num_samples, times)

        amp_obs = compute_amp_obs(
            dof_pos[:, self.motion_dof_indexes],
            dof_vel[:, self.motion_dof_indexes],
            body_pos[:, self.motion_ref_body_index],
            body_rot[:, self.motion_ref_body_index],
            body_linvel[:, self.motion_ref_body_index],
            body_angvel[:, self.motion_ref_body_index],
            body_pos[:, self.motion_key_body_indexes],
        )
        return amp_obs.view(-1, self.amp_observation_size)


# ---------- Helper functions ----------

def _quat_mul_xyzw(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Hamilton product for quaternions in (x,y,z,w) format."""
    ax, ay, az, aw = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    bx, by, bz, bw = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    return torch.stack([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], dim=-1)


@torch.jit.script
def quaternion_to_tangent_and_normal(q: torch.Tensor) -> torch.Tensor:
    ref_tangent = torch.zeros_like(q[..., :3])
    ref_normal = torch.zeros_like(q[..., :3])
    ref_tangent[..., 0] = 1
    ref_normal[..., -1] = 1
    tangent = quat_apply(q, ref_tangent)
    normal = quat_apply(q, ref_normal)
    return torch.cat([tangent, normal], dim=len(tangent.shape) - 1)


@torch.jit.script
def compute_amp_obs(
    dof_positions: torch.Tensor,
    dof_velocities: torch.Tensor,
    root_positions: torch.Tensor,
    root_rotations: torch.Tensor,
    root_linear_velocities: torch.Tensor,
    root_angular_velocities: torch.Tensor,
    key_body_positions: torch.Tensor,
) -> torch.Tensor:
    """AMP observation (same as standard AMP env for discriminator compatibility)."""
    return torch.cat(
        (
            dof_positions,
            dof_velocities,
            root_positions[:, 2:3],
            quaternion_to_tangent_and_normal(root_rotations),
            root_linear_velocities,
            root_angular_velocities,
            (key_body_positions - root_positions.unsqueeze(-2)).view(
                key_body_positions.shape[0], -1
            ),
        ),
        dim=-1,
    )


@torch.jit.script
def compute_lb_obs(
    lower_dof_pos: torch.Tensor,
    lower_dof_vel: torch.Tensor,
    upper_dof_pos: torch.Tensor,
    upper_dof_vel: torch.Tensor,
    root_positions: torch.Tensor,
    root_rotations: torch.Tensor,
    root_linear_vel: torch.Tensor,
    root_angular_vel: torch.Tensor,
    key_body_positions: torch.Tensor,
) -> torch.Tensor:
    """Lower body policy observation (81 dims)."""
    return torch.cat(
        (
            lower_dof_pos,
            lower_dof_vel,
            upper_dof_pos,
            upper_dof_vel,
            root_positions[:, 2:3],
            quaternion_to_tangent_and_normal(root_rotations),
            root_linear_vel,
            root_angular_vel,
            (key_body_positions - root_positions.unsqueeze(-2)).view(
                key_body_positions.shape[0], -1
            ),
        ),
        dim=-1,
    )
