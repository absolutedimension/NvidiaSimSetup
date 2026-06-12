"""
Quadcopter A->B-in-Rivermark environment.
Fork of Isaac-Quadcopter-Direct-v0 with:
  - Rivermark NVIDIA DRIVE Sim city loaded as static visual backdrop (/World/City)
  - Drone spawns at A = (0, 0, 30) per env_origin
  - Goal fixed at B = (100, 0, 30) per env_origin  (100m horizontal traverse)
"""
import gymnasium as gym
from . import agents

gym.register(
    id="Isaac-Quadcopter-City-A2B-v0",
    entry_point=f"{__name__}.quadcopter_city_a2b_env:QuadcopterCityA2BEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.quadcopter_city_a2b_env_cfg:QuadcopterCityA2BEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:QuadcopterPPORunnerCfg",
        "skrl_cfg_entry_point": f"{agents.__name__}:skrl_ppo_cfg.yaml",
    },
)
