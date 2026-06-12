"""
Train Stage A vision-PPO: Isaac-Quadcopter-OSM-City-Vision-v0.

Manhattan OSM city (866 buildings, convex-hull collision) + 84×84 depth
camera. Same VisionPolicy/VisionValue trunk as corridor_v1 — both take
obs_dim=7068 flat vectors (12 state + 84*84 depth). Network architecture
is obs-shape-agnostic so weights transfer between the two tasks.

Usage (inside isaaclab container):
  # Smoke check (15 s):
  /workspace/isaacsim/python.sh \\
    /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/\\
    quadcopter_osm_city_vision/scripts/train_osm_city_vision.py \\
    --num_envs 16 --iters 3 --headless

  # Full Stage A (128 envs × 1000 iters ≈ 40–50 min on A10G):
  /workspace/isaacsim/python.sh \\
    /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/\\
    quadcopter_osm_city_vision/scripts/train_osm_city_vision.py \\
    --num_envs 128 --iters 1000 --headless

  # Resume from checkpoint:
    ... --checkpoint /workspace/isaaclab/stage_a_runs/osm_city_vision/<ts>/checkpoints/best_agent.pt

After training:
  - Checkpoints: /workspace/isaaclab/stage_a_runs/osm_city_vision/<timestamp>/
  - Export trajectory with export_drone_trajectory.py, bake GLB with usd_to_glb.py
"""

from __future__ import annotations

import argparse

# AppLauncher must be constructed before any Isaac / torch imports
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--num_envs", type=int, default=128,
                    help="Parallel environments (default 128; smoke at 16)")
parser.add_argument("--iters", type=int, default=1000, help="PPO update iterations")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--checkpoint", type=str, default=None,
                    help="Resume from a .pt checkpoint path")
parser.add_argument("--experiment_name", type=str, default="osm_city_vision")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True  # depth camera requires renderer to be alive
args.headless = True        # always headless in training (OVRTX pipeline for viz)

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ------------------------------------------------------------------ imports
# Everything that touches torch / isaaclab must happen *after* AppLauncher.

import gymnasium as gym
import torch

from isaaclab_tasks.utils import parse_env_cfg
from isaaclab_rl.skrl import SkrlVecEnvWrapper

from skrl.agents.torch.ppo import PPO, PPO_DEFAULT_CONFIG
from skrl.memories.torch import RandomMemory
from skrl.resources.preprocessors.torch import RunningStandardScaler
from skrl.resources.schedulers.torch import KLAdaptiveLR
from skrl.trainers.torch import SequentialTrainer
from skrl.utils import set_seed

# Trigger gym.register for both envs (auto-discovery may already do this, but
# explicit imports guard against partial module scan ordering).
import isaaclab_tasks.direct.quadcopter_corridor_v1        # noqa: F401 — VisionPolicy lives here
import isaaclab_tasks.direct.quadcopter_osm_city_vision    # noqa: F401 — our task

from isaaclab_tasks.direct.quadcopter_corridor_v1.networks_vision import (
    VisionPolicy,
    VisionValue,
)

TASK = "Isaac-Quadcopter-OSM-City-Vision-v0"


def main():
    set_seed(args.seed)

    env_cfg = parse_env_cfg(TASK, device=args.device, num_envs=args.num_envs)
    env = gym.make(TASK, cfg=env_cfg, render_mode=None)
    env = SkrlVecEnvWrapper(env)

    # -------------------------------------------------------------- models
    device = env.device
    policy = VisionPolicy(env.observation_space, env.action_space, device)
    value  = VisionValue(env.observation_space, env.action_space, device)
    models = {"policy": policy, "value": value}

    policy_params = sum(p.numel() for p in policy.parameters())
    value_params  = sum(p.numel() for p in value.parameters())
    print(f"[osm_city_vision] obs_dim={env.observation_space.shape[0]}  "
          f"policy={policy_params:,} params  value={value_params:,} params")

    # ------------------------------------------------------------- memory
    # 24-step rollout horizon (same as corridor_v1 for fair comparison)
    memory = RandomMemory(memory_size=24, num_envs=env.num_envs, device=device)

    # ---------------------------------------------------------------- PPO
    # Hyperparams from Phase 6a / corridor_v1 — proven stable for drone A→B.
    # Only departure: slightly lower LR (3e-4 vs 5e-4) to be conservative with
    # the larger obs space (7068-d inputs slow convergence per step).
    cfg = PPO_DEFAULT_CONFIG.copy()
    cfg.update({
        "rollouts": 24,
        "learning_epochs": 5,
        "mini_batches": 4,
        "discount_factor": 0.99,
        "lambda": 0.95,
        "learning_rate": 3.0e-4,             # slightly more conservative than corridor_v1
        "learning_rate_scheduler": KLAdaptiveLR,
        "learning_rate_scheduler_kwargs": {"kl_threshold": 0.016},
        "state_preprocessor": RunningStandardScaler,
        "state_preprocessor_kwargs": {"size": env.observation_space, "device": device},
        "value_preprocessor": RunningStandardScaler,
        "value_preprocessor_kwargs": {"size": 1, "device": device},
        "random_timesteps": 0,
        "learning_starts": 0,
        "grad_norm_clip": 1.0,
        "ratio_clip": 0.2,
        "value_clip": 0.2,
        "clip_predicted_values": True,
        "entropy_loss_scale": 0.0,
        "value_loss_scale": 1.0,
        "rewards_shaper": lambda r, *_: r * 0.01,  # scale rewards for PPO stability
        "time_limit_bootstrap": True,
        "experiment": {
            "directory": "stage_a_runs",
            "experiment_name": args.experiment_name,
            "write_interval": "auto",
            "checkpoint_interval": "auto",
        },
    })

    agent = PPO(
        models=models,
        memory=memory,
        cfg=cfg,
        observation_space=env.observation_space,
        action_space=env.action_space,
        device=device,
    )

    if args.checkpoint:
        agent.load(args.checkpoint)
        print(f"[osm_city_vision] resumed from {args.checkpoint}")

    # ------------------------------------------------------------- trainer
    # skrl 'timesteps' = sim steps (not env steps); each sim step is 1 step
    # for all envs in parallel. Total env-steps = iters * rollouts * num_envs.
    total_sim_steps = args.iters * cfg["rollouts"]
    total_env_steps = total_sim_steps * env.num_envs

    trainer = SequentialTrainer(
        cfg={"timesteps": total_sim_steps, "headless": True, "environment_info": "log"},
        env=env,
        agents=agent,
    )

    print(f"[osm_city_vision] num_envs={env.num_envs}  iters={args.iters}  "
          f"sim_steps={total_sim_steps:,}  env_steps={total_env_steps:,}")

    trainer.train()

    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
