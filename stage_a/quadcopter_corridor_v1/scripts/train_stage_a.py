"""
Train Tier 2 Stage A: vision-PPO over the 1-obstacle corridor.

Bypasses Isaac Lab's stock skrl/train.py because the stock script uses
model_instantiator (yaml-only, MLP-only) and can't express the CNN+MLP
fusion that Stage A needs.

Usage (inside isaaclab container):
  /workspace/isaacsim/python.sh \
    /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_corridor_v1/scripts/train_stage_a.py \
    [--num_envs 16 --iters 1 --headless]    # smoke
    [--num_envs 512 --iters 1000 --headless] # full Stage A
"""

from __future__ import annotations

import argparse

# Isaac Lab requires AppLauncher to be the first thing constructed
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num_envs", type=int, default=512)
parser.add_argument("--iters", type=int, default=1000, help="PPO updates")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--checkpoint", type=str, default=None, help="resume from .pt")
parser.add_argument("--video", action="store_true", help="record video during training")
parser.add_argument("--experiment_name", type=str, default="stage_a_corridor_v1")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True   # depth camera needs the renderer alive

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# -------------------------------------------------------------------- imports
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

# Ours
import isaaclab_tasks.direct.quadcopter_corridor_v1  # noqa: F401  — gym.register
from isaaclab_tasks.direct.quadcopter_corridor_v1.networks_vision import VisionPolicy, VisionValue


def main():
    set_seed(args.seed)

    env_cfg = parse_env_cfg(
        "Isaac-Quadcopter-Corridor-V1-v0",
        device=args.device,
        num_envs=args.num_envs,
    )
    env = gym.make("Isaac-Quadcopter-Corridor-V1-v0", cfg=env_cfg, render_mode=None)
    env = SkrlVecEnvWrapper(env)

    # ----------------------------------------------------------------- models
    device = env.device
    policy = VisionPolicy(env.observation_space, env.action_space, device)
    value = VisionValue(env.observation_space, env.action_space, device)
    models = {"policy": policy, "value": value}

    print(f"[stage_a] policy params: {sum(p.numel() for p in policy.parameters()):,}")
    print(f"[stage_a] value  params: {sum(p.numel() for p in value.parameters()):,}")

    # ---------------------------------------------------------------- memory
    memory = RandomMemory(memory_size=24, num_envs=env.num_envs, device=device)

    # ------------------------------------------------------------------ PPO
    # Hyperparams cloned from Phase 6a's skrl_ppo_cfg.yaml; only memory_size
    # changed (rollouts=24) and tuned for the smaller num_envs.
    cfg = PPO_DEFAULT_CONFIG.copy()
    cfg.update({
        "rollouts": 24,
        "learning_epochs": 5,
        "mini_batches": 4,
        "discount_factor": 0.99,
        "lambda": 0.95,
        "learning_rate": 5.0e-4,
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
        "rewards_shaper": lambda r, *_: r * 0.01,
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
        print(f"[stage_a] loaded checkpoint {args.checkpoint}")

    # ---------------------------------------------------------------- trainer
    # skrl's trainer 'timesteps' is sim-steps (one step = all envs step in parallel),
    # NOT env-steps. Total sim-steps = iters * rollouts (one rollout per iter).
    total_sim_steps = args.iters * cfg["rollouts"]
    trainer = SequentialTrainer(
        cfg={"timesteps": total_sim_steps, "headless": True, "environment_info": "log"},
        env=env,
        agents=agent,
    )

    total_env_steps = total_sim_steps * env.num_envs
    print(f"[stage_a] num_envs={env.num_envs} iters={args.iters} "
          f"rollouts={cfg['rollouts']} sim_steps={total_sim_steps:,} "
          f"env_steps={total_env_steps:,}")

    trainer.train()

    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
