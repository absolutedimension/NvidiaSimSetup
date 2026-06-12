"""
Evaluate a Stage A trained policy against the acceptance criteria:
  - success rate (drone reaches within 2m of B)  target >= 0.80
  - collision rate                                target <= 0.10
  - 100 validation episodes minimum, randomized obstacle positions

The eval is deterministic (no exploration noise on the policy mean).

Usage:
  isaaclab.sh -p .../scripts/evaluate_stage_a.py \
    --checkpoint /workspace/isaaclab/stage_a_runs/.../best_agent.pt \
    [--num_envs 100] [--episodes 100]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", type=str, required=True)
parser.add_argument("--num_envs", type=int, default=100, help="run all 100 eval episodes in one pass")
parser.add_argument("--episodes", type=int, default=100, help="total eval episodes")
parser.add_argument("--seed", type=int, default=12345, help="held-out seed != training seed (42)")
parser.add_argument("--report", type=str, default="stage_a_eval.json")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ----------------------------------------------------------- post-launch imports
import json

import gymnasium as gym
import torch

from isaaclab_tasks.utils import parse_env_cfg
from isaaclab_rl.skrl import SkrlVecEnvWrapper

from skrl.utils import set_seed

import isaaclab_tasks.direct.quadcopter_corridor_v1  # noqa: F401
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

    device = env.device
    policy = VisionPolicy(env.observation_space, env.action_space, device).to(device)
    value = VisionValue(env.observation_space, env.action_space, device).to(device)

    # Load checkpoint (skrl saves a dict containing 'policy', 'value', 'optimizer', etc.)
    state = torch.load(args.checkpoint, map_location=device, weights_only=False)
    policy.load_state_dict(state["policy"])
    value.load_state_dict(state["value"])
    policy.to(device)  # state_dict load can leave params on cpu; reassert
    value.to(device)
    policy.eval()
    value.eval()
    print(f"[eval] loaded {args.checkpoint}")

    # ------------------------------------------------------------- eval loop
    successes = torch.zeros(args.num_envs, dtype=torch.bool, device=device)
    collisions = torch.zeros(args.num_envs, dtype=torch.bool, device=device)
    episode_completed = torch.zeros(args.num_envs, dtype=torch.bool, device=device)
    final_distances = torch.zeros(args.num_envs, device=device)

    obs, _ = env.reset()
    states = obs["policy"] if isinstance(obs, dict) else obs

    # Need internal env handle for state inspection (terrain origins, contact, etc.)
    base_env = env.unwrapped

    max_steps = int(env_cfg.episode_length_s / env_cfg.sim.dt / env_cfg.decimation) + 5
    print(f"[eval] running up to {max_steps} steps per episode across {args.num_envs} envs")

    for step in range(max_steps):
        if episode_completed.all():
            break
        with torch.no_grad():
            mean, _, _ = policy.compute({"states": states}, role="policy")
            actions = mean.clamp(-1.0, 1.0)

        next_obs, _, terminated, truncated, _ = env.step(actions)
        states = next_obs["policy"] if isinstance(next_obs, dict) else next_obs

        # Normalize all per-env masks to a flat (num_envs,) shape — skrl/Isaac Lab
        # wrappers can return (N,) or (N, 1) depending on path
        def _flat(t):
            return t.reshape(-1)[: args.num_envs]

        terminated = _flat(terminated.bool())
        truncated = _flat(truncated.bool())
        done = terminated | truncated
        newly_done = done & (~episode_completed)

        if newly_done.any():
            # Collision = died via the env's collision mask
            collided = _flat(base_env._collision_mask())
            collisions |= newly_done & collided

            # Success = within 2m of goal
            from warp import to_torch as wp_to_torch
            pos = wp_to_torch(base_env._robot.data.root_pos_w)
            d_to_goal = _flat((base_env._desired_pos_w - pos).norm(dim=-1))
            arrived = d_to_goal < 2.0
            successes |= newly_done & arrived

            final_distances = torch.where(newly_done, d_to_goal, final_distances)
            episode_completed |= newly_done

    # ---------------------------------------------------------------- report
    n = args.num_envs
    n_done = int(episode_completed.sum().item())
    n_success = int(successes.sum().item())
    n_collide = int(collisions.sum().item())
    success_rate = n_success / max(n_done, 1)
    collision_rate = n_collide / max(n_done, 1)

    report = {
        "checkpoint": args.checkpoint,
        "num_envs": n,
        "episodes_completed": n_done,
        "successes": n_success,
        "collisions": n_collide,
        "success_rate": success_rate,
        "collision_rate": collision_rate,
        "mean_final_distance_m": float(final_distances[episode_completed].mean().item())
            if n_done > 0 else None,
        "acceptance": {
            "success_target": 0.80,
            "collision_target": 0.10,
            "success_pass": success_rate >= 0.80,
            "collision_pass": collision_rate <= 0.10,
            "overall_pass": (success_rate >= 0.80) and (collision_rate <= 0.10),
        },
    }
    print(json.dumps(report, indent=2))
    Path(args.report).write_text(json.dumps(report, indent=2))
    print(f"[eval] wrote {args.report}")

    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
