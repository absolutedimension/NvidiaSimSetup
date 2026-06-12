"""Lower Body Physics — Isaac Lab AMP task registration.

Registers Isaac-Humanoid-AMP-LowerBody-Direct-v0 for use with:
    ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
        --task Isaac-Humanoid-AMP-LowerBody-Direct-v0 --algorithm AMP \
        --num_envs 256 --max_iterations 500 --headless

Deployment: copy the entire humanoid_amp_lower_body/ directory to
    /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp_lower_body/
and add 'from .humanoid_amp_lower_body import *' to
    isaaclab_tasks/direct/__init__.py
"""
import os

import gymnasium as gym

_AGENTS_DIR = os.path.join(os.path.dirname(__file__), "agents")

gym.register(
    id="Isaac-Humanoid-AMP-LowerBody-Direct-v0",
    entry_point=f"{__name__}.humanoid_amp_lower_body_env:HumanoidAmpLowerBodyEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.humanoid_amp_lower_body_env_cfg:HumanoidAmpLowerBodyEnvCfg",
        "skrl_amp_cfg_entry_point": os.path.join(_AGENTS_DIR, "skrl_amp_cfg.yaml"),
    },
)
