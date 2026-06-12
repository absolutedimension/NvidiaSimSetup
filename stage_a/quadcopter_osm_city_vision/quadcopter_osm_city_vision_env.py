# Stage A — Crazyflie vision-PPO in the Manhattan OSM city.
#
# Inherits from QuadcopterEnv (the base Crazyflie env, not city_a2b or corridor_v1)
# so we can set up the full scene from scratch — the only safe way to ensure:
#   1. OSM city USD is referenced BEFORE clone_environments (so 866 convex-hull
#      collidables appear in every /World/envs/env_N/City slot)
#   2. Camera and ContactSensor are also registered BEFORE clone (so each env
#      slot gets its own camera prim and contact listener)
#
# Key differences vs quadcopter_corridor_v1_env:
#   - No procedural RigidObject obstacle — buildings are the obstacles
#   - No _reset_idx obstacle randomization
#   - City USD collision APIs are deliberately PRESERVED (not stripped)
#   - episode_length_s=30 (longer traverse horizon)
#   - altitude ceiling bumped to 200 m (city is ~366 m tall at tallest point)
#
# All depth observation, reward, done logic is identical to corridor_v1 so the
# trained policy can be directly compared and the same VisionPolicy/VisionValue
# weights can be fine-tuned across tasks.

from __future__ import annotations

import torch
import warp as wp

import omni.usd
from pxr import UsdGeom

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs.ui import BaseEnvWindow
from isaaclab.sensors import Camera, ContactSensor
from isaaclab.utils.math import subtract_frame_transforms

from isaaclab_tasks.direct.quadcopter.quadcopter_env import QuadcopterEnv

from .quadcopter_osm_city_vision_env_cfg import (
    QuadcopterOsmCityVisionEnvCfg,
    DEPTH_H,
    DEPTH_W,
)


class QuadcopterOsmCityVisionEnvWindow(BaseEnvWindow):
    def __init__(self, env, window_name: str = "IsaacLab"):
        super().__init__(env, window_name)


class QuadcopterOsmCityVisionEnv(QuadcopterEnv):
    cfg: QuadcopterOsmCityVisionEnvCfg

    # ================================================================ scene setup
    def _setup_scene(self):
        # ---- 1. Reference OSM city USD BEFORE clone ----
        # The reference is added at /World/City. When clone_environments() runs,
        # it replicates /World/envs/env_.* but the city USD at /World/City is a
        # SHARED backdrop — same physical mesh for all envs. This is correct:
        # the city is static (no RigidBodyAPI), so all 128 envs share the same
        # collision geometry without needing per-env copies. Only the drone,
        # camera, and contact sensor need per-env replication.
        #
        # We deliberately do NOT strip collision APIs: OSM city was pre-baked
        # by city_add_colliders.py with convex-hull approximations. ~866 hulls
        # is well within PhysX's safe range. Real collisions are the point.
        stage = omni.usd.get_context().get_stage()
        city_xform = UsdGeom.Xform.Define(stage, "/World/City")
        city_xform.GetPrim().GetReferences().AddReference(self.cfg.city_usd_path)
        print(
            f"[QuadcopterOsmCityVisionEnv] referenced city USD: {self.cfg.city_usd_path}"
            "  — collision APIs PRESERVED (866 convex-hull buildings)"
        )

        # ---- 2. Register per-env sensors BEFORE clone ----
        # Isaac Lab's clone_environments() replicates everything registered under
        # /World/envs/env_0/* into /World/envs/env_1/*, ..., /World/envs/env_N/*.
        # The Camera and ContactSensor prim paths use the glob pattern env_.* so
        # they must exist under env_0 before clone runs.
        self._robot = Articulation(self.cfg.robot)
        self._camera = Camera(self.cfg.camera)
        self._contact = ContactSensor(self.cfg.contact)

        self.scene.articulations["robot"] = self._robot
        self.scene.sensors["camera"] = self._camera
        self.scene.sensors["contact"] = self._contact

        # ---- 3. Terrain (handles env grid layout) ----
        self.cfg.terrain.num_envs = self.scene.cfg.num_envs
        self.cfg.terrain.env_spacing = self.scene.cfg.env_spacing
        self._terrain = self.cfg.terrain.class_type(self.cfg.terrain)

        # ---- 4. Clone all registered prims into per-env slots ----
        self.scene.clone_environments(copy_from_source=False)

        # ---- 5. Collision filter (CPU-only; GPU uses TGS broad-phase) ----
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[self.cfg.terrain.prim_path])

        # ---- 6. Global dome light (same as corridor_v1) ----
        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

        # ---- 7. Per-env rolling state for reward computation ----
        self._prev_distance = torch.zeros(self.num_envs, device=self.device)
        self._max_depth = float(self.cfg.camera.spawn.clipping_range[1])

    # ================================================================ helpers
    @staticmethod
    def _as_torch(x: object) -> torch.Tensor:
        """Normalize warp.array or torch.Tensor to torch.Tensor."""
        return x if isinstance(x, torch.Tensor) else wp.to_torch(x)

    def _collision_mask(self) -> torch.Tensor:
        """True per env if the drone body has any non-trivial contact force this step."""
        forces = self._as_torch(self._contact.data.net_forces_w)  # (N, ..., 3)
        norm = forces.norm(dim=-1)
        if norm.ndim > 1:
            norm = norm.reshape(self.num_envs, -1).max(dim=1).values
        return norm > 0.1   # 0.1 N threshold matches corridor_v1

    def _clean_depth(self) -> torch.Tensor:
        """Camera depth map with NaN/inf replaced by max clip distance, clamped."""
        d = self._as_torch(self._camera.data.output["distance_to_image_plane"])
        if d.ndim == 4:
            d = d.squeeze(-1)   # (N, H, W, 1) → (N, H, W)
        d = torch.nan_to_num(
            d, nan=self._max_depth, posinf=self._max_depth, neginf=self._max_depth
        )
        return d.clamp(0.0, self._max_depth)

    # ============================================================== observations
    def _get_observations(self) -> dict:
        # Goal vector in body frame
        desired_pos_b, _ = subtract_frame_transforms(
            self._as_torch(self._robot.data.root_pos_w),
            self._as_torch(self._robot.data.root_quat_w),
            self._desired_pos_w,
        )
        # 12-dimensional state vector
        state = torch.cat(
            [
                self._as_torch(self._robot.data.root_lin_vel_b),    # (N, 3)
                self._as_torch(self._robot.data.root_ang_vel_b),    # (N, 3)
                self._as_torch(self._robot.data.projected_gravity_b),  # (N, 3)
                desired_pos_b,                                       # (N, 3)
            ],
            dim=-1,
        )  # (N, 12)

        # Flatten depth: (N, H, W) → (N, H*W)
        depth_flat = self._clean_depth().flatten(start_dim=1)   # (N, 7056)

        # Concatenate into single flat vector expected by VisionPolicy trunk
        obs = torch.cat([state, depth_flat], dim=-1)            # (N, 7068)
        return {"policy": obs}

    # ================================================================= rewards
    def _get_rewards(self) -> torch.Tensor:
        lin_vel = torch.sum(
            torch.square(self._as_torch(self._robot.data.root_lin_vel_b)), dim=1
        )
        ang_vel = torch.sum(
            torch.square(self._as_torch(self._robot.data.root_ang_vel_b)), dim=1
        )
        pos = self._as_torch(self._robot.data.root_pos_w)
        distance_to_goal = torch.linalg.norm(self._desired_pos_w - pos, dim=1)

        # Phase 6a a2b shaping — proven for 100 m traverse at city scale
        distance_mapped = 1.0 - torch.tanh(distance_to_goal / 100.0)
        progress = self._prev_distance - distance_to_goal      # positive = moved closer
        self._prev_distance = distance_to_goal.detach()
        arrived = (distance_to_goal < 2.0).float() * 50.0

        # Stage A collision penalty (one-shot spike when building contact detected)
        collided = self._collision_mask()
        collision_pen = collided.float() * self.cfg.collision_penalty  # ← -50 per collision

        # Stage A proximity penalty (soft, continuous — encourage >0.5 m clearance)
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

        # Lazy-init episode sums for all reward keys (mirrors corridor_v1 pattern)
        for key, value in rewards.items():
            if key not in self._episode_sums:
                self._episode_sums[key] = torch.zeros_like(value)
            self._episode_sums[key] += value

        return reward

    # =================================================================== dones
    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        pos = self._as_torch(self._robot.data.root_pos_w)
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # Altitude bounds: floor at 0.5 m, ceiling at 200 m
        # (city tallest building is ~366 m real-world but that's at full scale;
        # training at city scale, 200 m cap keeps episodes bounded)
        altitude_died = torch.logical_or(pos[:, 2] < 0.5, pos[:, 2] > 200.0)

        died = altitude_died
        if self.cfg.terminate_on_collision:
            died = died | self._collision_mask()

        return died, time_out

    # =================================================================== reset
    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)

        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = self._as_torch(self._robot._ALL_INDICES)
        n = len(env_ids)

        # ---- Goal at fixed B (env-local + env_origin offset) ----
        b = torch.tensor(self.cfg.goal_pos, device=self.device, dtype=torch.float32)
        self._desired_pos_w[env_ids] = b.unsqueeze(0).expand(n, 3).clone()
        self._desired_pos_w[env_ids, :2] += self._terrain.env_origins[env_ids, :2]

        # ---- Spawn drone at A ----
        default_root_pose = self._as_torch(
            self._robot.data.default_root_pose
        )[env_ids].clone()
        a = self.cfg.spawn_pos
        default_root_pose[:, 0] = float(a[0]) + self._terrain.env_origins[env_ids, 0]
        default_root_pose[:, 1] = float(a[1]) + self._terrain.env_origins[env_ids, 1]
        default_root_pose[:, 2] = float(a[2])
        default_root_pose[:, 3] = 1.0   # qw = 1 (identity quaternion)
        default_root_pose[:, 4:] = 0.0
        self._robot.write_root_pose_to_sim_index(
            root_pose=default_root_pose, env_ids=env_ids
        )

        default_root_vel = self._as_torch(
            self._robot.data.default_root_vel
        )[env_ids].clone()
        default_root_vel[:] = 0.0
        self._robot.write_root_velocity_to_sim_index(
            root_velocity=default_root_vel, env_ids=env_ids
        )

        # ---- Re-init progress tracking ----
        new_pos = self._as_torch(self._robot.data.root_pos_w)[env_ids]
        self._prev_distance[env_ids] = torch.linalg.norm(
            self._desired_pos_w[env_ids] - new_pos, dim=1
        )
