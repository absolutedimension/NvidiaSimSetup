"""Cinematographer drone — RL-trained autonomous camera for filming a dancer.

v3: 12 reward terms, 20-dim obs, single behavior
v4: 22 reward terms, 33-dim obs, 6 shooting modes (HERO/INTIMATE/EPIC/ENERGY/SOLITUDE/BEAUTY)
"""

import gymnasium as gym

from . import agents

# v3 (preserved for comparison / rollback)
gym.register(
    id="Isaac-Cinematographer-Direct-v0",
    entry_point=f"{__name__}.cinematographer_env:CinematographerEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg:CinematographerEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
    },
)

# v4 — mode-conditioned
gym.register(
    id="Isaac-Cinematographer-Direct-v4",
    entry_point=f"{__name__}.cinematographer_env_v4:CinematographerEnvV4",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg_v4:CinematographerEnvCfgV4",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_v4_cfg.yaml",
    },
)

# v5 — STEADY (single-purpose: hold still, face dancer, relocate smoothly)
gym.register(
    id="Isaac-Cinematographer-Steady-v5",
    entry_point=f"{__name__}.cinematographer_env_v5_steady:CinematographerEnvV5Steady",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.cinematographer_env_cfg_v5_steady:CinematographerEnvCfgV5Steady",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_v5_steady_cfg.yaml",
    },
)
