"""Cinematographer drone v5e — STEADY mode with improved stability + smooth transitions."""

import gymnasium as gym

from . import agents

# v5e STEADY — improved reward balance, stable training
gym.register(
    id="Isaac-Cinematographer-Steady-v5e",
    entry_point=f"{__name__}.cinematographer_env_v5e_steady:CinematographerEnvV5eSteady",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg_v5e_steady:CinematographerEnvCfgV5eSteady",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_v5e_steady_cfg.yaml",
    },
)

# Keep v5d registration for comparison
gym.register(
    id="Isaac-Cinematographer-Steady-v5",
    entry_point=f"{__name__}.cinematographer_env_v5_steady:CinematographerEnvV5Steady",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg_v5_steady:CinematographerEnvCfgV5Steady",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_v5_steady_cfg.yaml",
    },
)
