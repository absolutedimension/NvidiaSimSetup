"""
Quadcopter-Corridor-V1 — Tier 2 Stage A: vision-PPO over a procedural
1-obstacle corridor with depth camera and real collision physics.

Fork of Quadcopter-City-A2B-v0 (Phase 6a):
  - drops Rivermark, spawns one kinematic box obstacle per env at random x,y
  - adds forward-facing 84x84 depth camera attached to drone body
  - adds contact-sensor-based collision termination + penalty
  - adds proximity penalty from depth-min
"""

import gymnasium as gym

from . import agents

gym.register(
    id="Isaac-Quadcopter-Corridor-V1-v0",
    entry_point=f"{__name__}.quadcopter_corridor_v1_env:QuadcopterCorridorV1Env",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.quadcopter_corridor_v1_env_cfg:QuadcopterCorridorV1EnvCfg",
        # No rl_games / rsl_rl entry points — Stage A is skrl-only.
        # The train script in scripts/train_stage_a.py wires the custom vision Models directly.
    },
)
