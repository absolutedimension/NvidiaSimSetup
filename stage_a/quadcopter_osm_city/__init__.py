"""
Quadcopter-OSM-City — drone training in a real-world city pulled from OpenStreetMap.

Fork of Isaac-Quadcopter-City-A2B-v0 (Phase 6a Rivermark). Key differences:
  * City USD is OSM-derived (built by webxr-showcase/scripts/osm_to_usd.py),
    not Rivermark.
  * Collision APIs are KEPT (drone actually bumps into buildings). The OSM
    city is ~150–900 simple convex-hull collidables vs. Rivermark's 12k+
    triangle-mesh prims, so the PhysX-silent-death gotcha doesn't apply.
  * ContactSensor termination + collision penalty (mirrors corridor-v1).

Reuses the existing quadcopter_city_a2b agents (rl_games / skrl / rsl_rl)
unchanged — same PPO config since the reward shape is unchanged.
"""

import gymnasium as gym

gym.register(
    id="Isaac-Quadcopter-OSM-City-Direct-v0",
    entry_point=f"{__name__}.quadcopter_osm_city_env:QuadcopterOsmCityEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.quadcopter_osm_city_env_cfg:QuadcopterOsmCityEnvCfg",
        # Reuse the proven Rivermark a2b PPO configs (same reward shape).
        "rl_games_cfg_entry_point": "isaaclab_tasks.direct.quadcopter_city_a2b.agents:rl_games_ppo_cfg.yaml",
        "skrl_cfg_entry_point": "isaaclab_tasks.direct.quadcopter_city_a2b.agents:skrl_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": "isaaclab_tasks.direct.quadcopter_city_a2b.agents.rsl_rl_ppo_cfg:QuadcopterPPORunnerCfg",
    },
)
