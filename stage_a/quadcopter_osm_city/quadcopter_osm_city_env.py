# Quadcopter A->B in OSM-derived city — env class.
# Fork of QuadcopterCityA2BEnv. Overrides:
#   1) _setup_scene — references the OSM city USD; does NOT strip collision APIs
#      (OSM city is ~900 convex hulls, fine at scale; KEEPING collision is the
#      whole point — the drone actually bumps into buildings).
#      Also wires a ContactSensor on the drone body.
#   2) _get_dones — terminates the episode on contact-force > 0.1 N if
#      cfg.terminate_on_collision is True; otherwise just penalises.
#   3) _get_rewards — adds a collision penalty term on top of the inherited
#      a2b reward (distance/progress/arrived).

from __future__ import annotations

import torch
import warp as wp

import omni.usd
from pxr import UsdGeom

from isaaclab.envs.ui import BaseEnvWindow
from isaaclab.sensors import ContactSensor
from isaaclab_tasks.direct.quadcopter_city_a2b.quadcopter_city_a2b_env import (
    QuadcopterCityA2BEnv,
)

from .quadcopter_osm_city_env_cfg import QuadcopterOsmCityEnvCfg


class QuadcopterOsmCityEnvWindow(BaseEnvWindow):
    def __init__(self, env, window_name: str = "IsaacLab"):
        super().__init__(env, window_name)


class QuadcopterOsmCityEnv(QuadcopterCityA2BEnv):
    cfg: QuadcopterOsmCityEnvCfg

    # ------------------------------------------------------------------ scene
    def _setup_scene(self):
        # 1. Reference the OSM city USD.
        #    NOTE: we intentionally do NOT strip collision APIs the way the a2b
        #    parent does for Rivermark. OSM city is small + uses convex-hull
        #    approximations, so PhysX won't choke. Drone collision IS the point.
        stage = omni.usd.get_context().get_stage()
        city_xform = UsdGeom.Xform.Define(stage, "/World/City")
        city_xform.GetPrim().GetReferences().AddReference(self.cfg.city_usd_path)
        print(
            f"[QuadcopterOsmCityEnv] referenced city USD: {self.cfg.city_usd_path}"
            " (collision APIs PRESERVED)"
        )

        # 2. Parent's parent setup (Articulation + ground + light). We skip
        #    QuadcopterCityA2BEnv._setup_scene because its API-stripping loop
        #    would defeat the purpose. Reach past it to the QuadcopterEnv base.
        super(QuadcopterCityA2BEnv, self)._setup_scene()

        # 3. Per-env drone body contact sensor (mirrors corridor-v1).
        self._contact = ContactSensor(self.cfg.contact)
        self.scene.sensors["contact"] = self._contact

        # 4. Track previous distance per env for the progress reward signal
        #    (re-init here because we bypassed the parent class's _setup_scene).
        self._prev_distance = torch.zeros(self.num_envs, device=self.device)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _as_torch(x):
        return x if isinstance(x, torch.Tensor) else wp.to_torch(x)

    def _collision_mask(self) -> torch.Tensor:
        """True per env if drone body has any non-trivial contact this step."""
        forces = self._as_torch(self._contact.data.net_forces_w)  # (N, ..., 3)
        norm = forces.norm(dim=-1)
        if norm.ndim > 1:
            norm = norm.reshape(self.num_envs, -1).max(dim=1).values
        return norm > 0.1

    # ---------------------------------------------------------------- rewards
    def _get_rewards(self) -> torch.Tensor:
        # Inherit the proven a2b distance + progress + arrived shaping…
        reward = super()._get_rewards()
        # …and layer a one-shot collision penalty.
        collided = self._collision_mask()
        collision_pen = collided.float() * self.cfg.collision_penalty
        reward = reward + collision_pen
        if "collision" not in self._episode_sums:
            self._episode_sums["collision"] = torch.zeros_like(collision_pen)
        self._episode_sums["collision"] += collision_pen
        return reward

    # ------------------------------------------------------------------ dones
    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        died, time_out = super()._get_dones()
        if self.cfg.terminate_on_collision:
            died = died | self._collision_mask()
        return died, time_out
