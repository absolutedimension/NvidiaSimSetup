"""Cinematographer drone — RL-trained autonomous camera for filming a dancer."""

import gymnasium as gym

from . import agents

gym.register(
    id="Isaac-Cinematographer-Direct-v0",
    entry_point=f"{__name__}.cinematographer_env:CinematographerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg:CinematographerEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
    },
)
