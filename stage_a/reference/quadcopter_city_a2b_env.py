# Quadcopter A->B in Rivermark - env class (fork of QuadcopterEnv)
#
# Surgical overrides on top of the proven hover-near-goal env:
#   1) _setup_scene: load Rivermark city as /World/City visual-only
#      (physics APIs stripped to avoid PhysX choke on building props)
#   2) _reset_idx: lock goal to fixed B; respawn drone at A altitude (z=30)
#   3) _get_dones: do NOT kill the drone for being at high altitude
#      (parent's z>2.0 termination would kill us on step 1 since A is at z=30)
#   4) _get_rewards: replace the saturating tanh(d/0.8) reward with a
#      reward that has signal across the full A->B span (100m), plus a
#      progress term (delta-distance per step) so PPO has a gradient.

from __future__ import annotations

import torch
import warp as wp

import omni.usd
from pxr import UsdGeom, UsdPhysics

from isaaclab.envs.ui import BaseEnvWindow
from isaaclab_tasks.direct.quadcopter.quadcopter_env import QuadcopterEnv

from .quadcopter_city_a2b_env_cfg import QuadcopterCityA2BEnvCfg


class QuadcopterCityA2BEnvWindow(BaseEnvWindow):
    def __init__(self, env, window_name: str = "IsaacLab"):
        super().__init__(env, window_name)


class QuadcopterCityA2BEnv(QuadcopterEnv):
    cfg: QuadcopterCityA2BEnvCfg

    def _setup_scene(self):
        # 1. City as visual-only static prim
        stage = omni.usd.get_context().get_stage()
        city_xform = UsdGeom.Xform.Define(stage, "/World/City")
        city_xform.GetPrim().GetReferences().AddReference(self.cfg.city_usd_path)
        print(f"[QuadcopterCityA2BEnv] referenced city USD: {self.cfg.city_usd_path}")

        # 2. Strip physics APIs from city props - PhysX silently dies at scale
        #    with replicate_physics=True if /World/City has thousands of rigid bodies
        stripped = 0
        for prim in stage.Traverse():
            if not str(prim.GetPath()).startswith("/World/City"):
                continue
            for api_type in (UsdPhysics.RigidBodyAPI, UsdPhysics.CollisionAPI,
                             UsdPhysics.MassAPI, UsdPhysics.MeshCollisionAPI):
                if prim.HasAPI(api_type):
                    prim.RemoveAPI(api_type)
                    stripped += 1
        print(f"[QuadcopterCityA2BEnv] stripped {stripped} physics APIs from /World/City")

        # 3. Parent setup (Articulation + flat-plane ground + light)
        super()._setup_scene()

        # 4. Track previous distance per env for the progress reward signal
        self._prev_distance = torch.zeros(self.num_envs, device=self.device)

    def _reset_idx(self, env_ids):
        super()._reset_idx(env_ids)

        if env_ids is None or len(env_ids) == self.num_envs:
            env_ids = wp.to_torch(self._robot._ALL_INDICES)

        # Goal at fixed Point B (env-local + env_origin offset)
        b = torch.tensor(self.cfg.goal_pos, device=self.device, dtype=torch.float32)
        self._desired_pos_w[env_ids] = b.unsqueeze(0).expand(len(env_ids), 3).clone()
        self._desired_pos_w[env_ids, :2] += self._terrain.env_origins[env_ids, :2]

        # Drone spawn at fixed Point A
        default_root_pose = wp.to_torch(self._robot.data.default_root_pose)[env_ids].clone()
        a = self.cfg.spawn_pos
        default_root_pose[:, 0] = float(a[0]) + self._terrain.env_origins[env_ids, 0]
        default_root_pose[:, 1] = float(a[1]) + self._terrain.env_origins[env_ids, 1]
        default_root_pose[:, 2] = float(a[2])
        default_root_pose[:, 3] = 1.0
        default_root_pose[:, 4:] = 0.0
        self._robot.write_root_pose_to_sim_index(root_pose=default_root_pose, env_ids=env_ids)

        # Zero velocity
        default_root_vel = wp.to_torch(self._robot.data.default_root_vel)[env_ids].clone()
        default_root_vel[:] = 0.0
        self._robot.write_root_velocity_to_sim_index(root_velocity=default_root_vel, env_ids=env_ids)

        # Initialize prev_distance for the progress reward
        pos = wp.to_torch(self._robot.data.root_pos_w)[env_ids]
        self._prev_distance[env_ids] = torch.linalg.norm(self._desired_pos_w[env_ids] - pos, dim=1)

    def _get_rewards(self) -> torch.Tensor:
        # Drone state
        lin_vel = torch.sum(torch.square(wp.to_torch(self._robot.data.root_lin_vel_b)), dim=1)
        ang_vel = torch.sum(torch.square(wp.to_torch(self._robot.data.root_ang_vel_b)), dim=1)
        pos = wp.to_torch(self._robot.data.root_pos_w)
        distance_to_goal = torch.linalg.norm(self._desired_pos_w - pos, dim=1)

        # Distance reward — scaled for 100m horizon (was tanh(d/0.8) which saturates
        # past d~2m). Now uses d/100 so the policy sees signal across the full A->B.
        distance_mapped = 1.0 - torch.tanh(distance_to_goal / 100.0)

        # Progress reward — delta in distance this step. Always non-zero (positive
        # if moving toward goal, negative if moving away). This is what gives PPO
        # a clean gradient even when the drone is still very far from B.
        progress = self._prev_distance - distance_to_goal  # positive when closing in
        self._prev_distance = distance_to_goal.detach()

        # Arrival bonus (large spike when within 2m of B)
        arrived = (distance_to_goal < 2.0).float() * 50.0

        rewards = {
            "lin_vel":          lin_vel * self.cfg.lin_vel_reward_scale * self.step_dt,
            "ang_vel":          ang_vel * self.cfg.ang_vel_reward_scale * self.step_dt,
            "distance_to_goal": distance_mapped * self.cfg.distance_to_goal_reward_scale * self.step_dt,
            "progress":         progress * self.cfg.progress_reward_scale,
            "arrived":          arrived * self.step_dt,
        }
        reward = torch.sum(torch.stack(list(rewards.values())), dim=0)
        # Parent only initializes _episode_sums for lin_vel/ang_vel/distance_to_goal.
        # Lazy-init our new keys (progress, arrived) on first access.
        for key, value in rewards.items():
            if key not in self._episode_sums:
                self._episode_sums[key] = torch.zeros_like(value)
            self._episode_sums[key] += value
        return reward

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        # Override parent's z<0.1 or z>2.0 termination. We fly at z=30 by design.
        # Kill the drone only if it goes WAY too high or too low for this task.
        pos = wp.to_torch(self._robot.data.root_pos_w)
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        died = torch.logical_or(
            pos[:, 2] < 0.5,    # crashed into ground
            pos[:, 2] > 100.0,  # flew way too high (above tallest tracked altitude in city)
        )
        return died, time_out
