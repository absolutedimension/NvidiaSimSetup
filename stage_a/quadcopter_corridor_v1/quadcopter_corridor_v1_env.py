# Stage A — Crazyflie navigating a procedural 1-obstacle corridor with depth vision.
# Fork of QuadcopterEnv adding: forward depth camera (84x84), kinematic box obstacle,
# contact-sensor-based collision detection, proximity + collision rewards.

from __future__ import annotations

import torch
import warp as wp

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs.ui import BaseEnvWindow
from isaaclab.sensors import Camera, ContactSensor
from isaaclab.utils.math import subtract_frame_transforms

from isaaclab_tasks.direct.quadcopter.quadcopter_env import QuadcopterEnv

from .quadcopter_corridor_v1_env_cfg import QuadcopterCorridorV1EnvCfg, DEPTH_H, DEPTH_W


class QuadcopterCorridorV1EnvWindow(BaseEnvWindow):
    def __init__(self, env, window_name: str = "IsaacLab"):
        super().__init__(env, window_name)


class QuadcopterCorridorV1Env(QuadcopterEnv):
    cfg: QuadcopterCorridorV1EnvCfg

    # ------------------------------------------------------------------ scene
    def _setup_scene(self):
        # Replicates parent's _setup_scene + adds obstacle/camera/contact sensors
        # BEFORE clone_environments so they get replicated per env.
        self._robot = Articulation(self.cfg.robot)
        self._obstacle = RigidObject(self.cfg.obstacle)
        self._camera = Camera(self.cfg.camera)
        self._contact = ContactSensor(self.cfg.contact)

        self.scene.articulations["robot"] = self._robot
        self.scene.rigid_objects["obstacle"] = self._obstacle
        self.scene.sensors["camera"] = self._camera
        self.scene.sensors["contact"] = self._contact

        self.cfg.terrain.num_envs = self.scene.cfg.num_envs
        self.cfg.terrain.env_spacing = self.scene.cfg.env_spacing
        self._terrain = self.cfg.terrain.class_type(self.cfg.terrain)

        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[self.cfg.terrain.prim_path])

        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

        self._prev_distance = torch.zeros(self.num_envs, device=self.device)
        self._max_depth = float(self.cfg.camera.spawn.clipping_range[1])

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _as_torch(x):
        # Isaac Lab data accessors return warp arrays; camera output is sometimes
        # already torch. Normalize to torch.Tensor either way.
        return x if isinstance(x, torch.Tensor) else wp.to_torch(x)

    def _collision_mask(self) -> torch.Tensor:
        """True per env if drone body has any non-trivial contact force this step."""
        forces = self._as_torch(self._contact.data.net_forces_w)  # (N, ..., 3)
        norm = forces.norm(dim=-1)
        if norm.ndim > 1:
            norm = norm.reshape(self.num_envs, -1).max(dim=1).values
        return norm > 0.1

    def _clean_depth(self) -> torch.Tensor:
        """Camera depth with NaN/inf replaced by max distance, clamped to [0, max]."""
        d = self._as_torch(self._camera.data.output["distance_to_image_plane"])
        if d.ndim == 4:
            d = d.squeeze(-1)
        d = torch.nan_to_num(d, nan=self._max_depth, posinf=self._max_depth, neginf=self._max_depth)
        return d.clamp(0.0, self._max_depth)

    # -------------------------------------------------------------- observations
    def _get_observations(self) -> dict:
        desired_pos_b, _ = subtract_frame_transforms(
            wp.to_torch(self._robot.data.root_pos_w),
            wp.to_torch(self._robot.data.root_quat_w),
            self._desired_pos_w,
        )
        state = torch.cat(
            [
                wp.to_torch(self._robot.data.root_lin_vel_b),
                wp.to_torch(self._robot.data.root_ang_vel_b),
                wp.to_torch(self._robot.data.projected_gravity_b),
                desired_pos_b,
            ],
            dim=-1,
        )  # (N, 12)

        depth_flat = self._clean_depth().flatten(start_dim=1)  # (N, H*W)
        obs = torch.cat([state, depth_flat], dim=-1)           # (N, 12 + H*W)
        return {"policy": obs}

    # ------------------------------------------------------------------ rewards
    def _get_rewards(self) -> torch.Tensor:
        lin_vel = torch.sum(torch.square(wp.to_torch(self._robot.data.root_lin_vel_b)), dim=1)
        ang_vel = torch.sum(torch.square(wp.to_torch(self._robot.data.root_ang_vel_b)), dim=1)
        pos = wp.to_torch(self._robot.data.root_pos_w)
        distance_to_goal = torch.linalg.norm(self._desired_pos_w - pos, dim=1)

        # Phase 6a a2b shaping (proven for 100m horizon)
        distance_mapped = 1.0 - torch.tanh(distance_to_goal / 100.0)
        progress = self._prev_distance - distance_to_goal
        self._prev_distance = distance_to_goal.detach()
        arrived = (distance_to_goal < 2.0).float() * 50.0

        # Stage A additions
        collided = self._collision_mask()
        collision_pen = collided.float() * self.cfg.collision_penalty

        depth = self._clean_depth()
        min_d = depth.flatten(start_dim=1).min(dim=1).values
        proximity_pen = -1.0 / (min_d.clamp(min=0.5) ** 2) * self.cfg.proximity_penalty_scale

        rewards = {
            "lin_vel":          lin_vel * self.cfg.lin_vel_reward_scale * self.step_dt,
            "ang_vel":          ang_vel * self.cfg.ang_vel_reward_scale * self.step_dt,
            "distance_to_goal": distance_mapped * self.cfg.distance_to_goal_reward_scale * self.step_dt,
            "progress":         progress * self.cfg.progress_reward_scale,
            "arrived":          arrived * self.step_dt,
            "collision":        collision_pen,
            "proximity":        proximity_pen * self.step_dt,
        }
        reward = torch.sum(torch.stack(list(rewards.values())), dim=0)

        # Parent only initializes _episode_sums for lin_vel/ang_vel/distance_to_goal.
        # Lazy-init for the new keys (mirrors the a2b pattern).
        for key, value in rewards.items():
            if key not in self._episode_sums:
                self._episode_sums[key] = torch.zeros_like(value)
            self._episode_sums[key] += value
        return reward

    # -------------------------------------------------------------------- dones
    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        pos = wp.to_torch(self._robot.data.root_pos_w)
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        altitude_died = torch.logical_or(pos[:, 2] < 0.5, pos[:, 2] > 100.0)
        died = altitude_died | self._collision_mask()
        return died, time_out

    # -------------------------------------------------------------------- reset
    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)

        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = wp.to_torch(self._robot._ALL_INDICES)
        n = len(env_ids)

        # Goal at fixed B (env-local + env_origin offset)
        b = torch.tensor(self.cfg.goal_pos, device=self.device, dtype=torch.float32)
        self._desired_pos_w[env_ids] = b.unsqueeze(0).expand(n, 3).clone()
        self._desired_pos_w[env_ids, :2] += self._terrain.env_origins[env_ids, :2]

        # Drone spawn at A
        default_root_pose = wp.to_torch(self._robot.data.default_root_pose)[env_ids].clone()
        a = self.cfg.spawn_pos
        default_root_pose[:, 0] = float(a[0]) + self._terrain.env_origins[env_ids, 0]
        default_root_pose[:, 1] = float(a[1]) + self._terrain.env_origins[env_ids, 1]
        default_root_pose[:, 2] = float(a[2])
        default_root_pose[:, 3] = 1.0
        default_root_pose[:, 4:] = 0.0
        self._robot.write_root_pose_to_sim_index(root_pose=default_root_pose, env_ids=env_ids)

        default_root_vel = wp.to_torch(self._robot.data.default_root_vel)[env_ids].clone()
        default_root_vel[:] = 0.0
        self._robot.write_root_velocity_to_sim_index(root_velocity=default_root_vel, env_ids=env_ids)

        # Randomize obstacle position per env
        rand_xy = torch.rand((n, 2), device=self.device)
        ox = self.cfg.obstacle_x_range
        oy = self.cfg.obstacle_y_range
        obstacle_pose = torch.zeros((n, 7), device=self.device)
        obstacle_pose[:, 0] = ox[0] + rand_xy[:, 0] * (ox[1] - ox[0]) + self._terrain.env_origins[env_ids, 0]
        obstacle_pose[:, 1] = oy[0] + rand_xy[:, 1] * (oy[1] - oy[0]) + self._terrain.env_origins[env_ids, 1]
        obstacle_pose[:, 2] = self.cfg.obstacle_z
        obstacle_pose[:, 3] = 1.0
        self._obstacle.write_root_pose_to_sim_index(root_pose=obstacle_pose, env_ids=env_ids)

        # Re-init prev_distance for progress reward
        new_pos = wp.to_torch(self._robot.data.root_pos_w)[env_ids]
        self._prev_distance[env_ids] = torch.linalg.norm(self._desired_pos_w[env_ids] - new_pos, dim=1)
