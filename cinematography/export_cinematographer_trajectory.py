#!/usr/bin/env python3
"""Export a trained cinematographer policy rollout to JSON.

Loads the trained checkpoint, runs one episode in the env at num_envs=1,
and saves per-frame drone position + quaternion + dancer position.

Run inside the isaaclab container:
    cd /workspace/isaaclab && ./isaaclab.sh -p /workspace/isaaclab/cinematography/export_cinematographer_trajectory.py \
        --checkpoint /workspace/isaaclab/logs/rl_games/cinematographer_direct/2026-05-24_09-37-23/nn/cinematographer_direct.pth \
        --steps 1250 --fps 50 \
        --out /workspace/isaaclab/cinematography/cinematographer_trajectory.json
"""
from __future__ import annotations

import argparse
import json

import torch
import gymnasium as gym

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--steps", type=int, default=1250)
parser.add_argument("--fps", type=float, default=50.0)
parser.add_argument("--out", required=True)
parser.add_argument("--task", default="Isaac-Cinematographer-Direct-v4",
                    help="Gym env ID (v0=single-mode, v4=6-mode)")
parser.add_argument("--mode-schedule", default=None,
                    help="Comma-separated step:MODE pairs, e.g. "
                         "'0:BEAUTY,400:HERO,750:INTIMATE'. "
                         "If omitted, mode stays at default (HERO).")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)

import isaaclab_tasks  # noqa: F401 — triggers gym.register
import warp as wp
from rl_games.torch_runner import Runner
from rl_games.common import env_configurations
from isaaclab_rl.rl_games import RlGamesGpuEnv, RlGamesVecEnvWrapper
from isaaclab.envs import DirectRLEnv


def _to_list(x):
    if hasattr(x, "numpy"):
        return x.numpy().tolist()
    if hasattr(x, "cpu"):
        return x.cpu().numpy().tolist()
    return list(x)


MODE_NAMES = ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"]


def parse_mode_schedule(schedule_str):
    """Parse '0:BEAUTY,400:HERO,...' into sorted list of (step, mode_index) tuples."""
    if not schedule_str:
        return []
    entries = []
    for part in schedule_str.split(","):
        step_s, mode_name = part.strip().split(":")
        step = int(step_s)
        mode_idx = MODE_NAMES.index(mode_name.upper())
        entries.append((step, mode_idx))
    return sorted(entries, key=lambda x: x[0])


def main():
    env_cfg_cls = gym.spec(args.task).kwargs["env_cfg_entry_point"]
    if isinstance(env_cfg_cls, str):
        mod, cls = env_cfg_cls.rsplit(":", 1)
        import importlib
        m = importlib.import_module(mod)
        env_cfg_cls = getattr(m, cls)

    cfg = env_cfg_cls()
    cfg.scene.num_envs = 1

    env = gym.make(args.task, cfg=cfg)
    unwrapped = env.unwrapped

    rl_cfg_path = gym.spec(args.task).kwargs["rl_games_cfg_entry_point"]
    import os, yaml
    from importlib import resources
    mod_name, file_name = rl_cfg_path.rsplit(":", 1)
    mod = __import__(mod_name, fromlist=[""])
    cfg_path = os.path.join(os.path.dirname(mod.__file__), file_name)
    with open(cfg_path) as f:
        rl_cfg = yaml.safe_load(f)

    rl_cfg["params"]["config"]["num_actors"] = 1
    rl_cfg["params"]["load_checkpoint"] = True
    rl_cfg["params"]["load_path"] = args.checkpoint

    def create_env(**kwargs):
        return RlGamesVecEnvWrapper(env, rl_device="cuda:0", clip_obs=10.0, clip_actions=1.0)

    env_configurations.register("rlgpu", {"vecenv_type": "RLGPU", "env_creator": create_env})

    runner = Runner()
    runner.load(rl_cfg)
    agent = runner.create_player()
    agent.restore(args.checkpoint)
    agent.reset()

    mode_schedule = parse_mode_schedule(args.mode_schedule)
    current_mode_idx = 0
    schedule_ptr = 0
    if mode_schedule:
        current_mode_idx = mode_schedule[0][1]
        print(f"Mode schedule: {len(mode_schedule)} switches")
        for step, mi in mode_schedule:
            print(f"  step {step}: {MODE_NAMES[mi]}")

    frames = []
    obs = env.reset()[0]

    for step_i in range(args.steps):
        if mode_schedule and schedule_ptr < len(mode_schedule):
            if step_i >= mode_schedule[schedule_ptr][0]:
                current_mode_idx = mode_schedule[schedule_ptr][1]
                if hasattr(unwrapped, '_current_mode'):
                    unwrapped._current_mode[:] = current_mode_idx
                schedule_ptr += 1
                if schedule_ptr < len(mode_schedule):
                    pass

        with torch.no_grad():
            action = agent.get_action(obs["policy"], is_deterministic=True)
        if action.dim() == 1:
            action = action.unsqueeze(0)
        obs, reward, terminated, truncated, info = env.step(action)

        drone_pos = wp.to_torch(unwrapped._robot.data.root_pos_w)
        drone_quat = wp.to_torch(unwrapped._robot.data.root_quat_w)
        dancer_pos = unwrapped._dancer_pos_w

        origin = unwrapped._terrain.env_origins[0]
        dp = (drone_pos[0] - origin).cpu().tolist()
        dq = drone_quat[0].cpu().tolist()
        dancer = (dancer_pos[0] - origin).cpu().tolist()

        frames.append({
            "t": step_i / args.fps,
            "drone_pos": dp,
            "drone_quat": dq,
            "dancer_pos": dancer,
            "mode": MODE_NAMES[current_mode_idx],
        })

        if terminated.any() or truncated.any():
            obs = env.reset()[0]

    traj = {
        "fps": args.fps,
        "num_frames": len(frames),
        "coordinate_system": "isaac_sim_z_up",
        "mode_schedule": args.mode_schedule or "",
        "frames": frames,
    }

    with open(args.out, "w") as f:
        json.dump(traj, f, indent=1)
    print(f"Exported {len(frames)} frames to {args.out}")

    env.close()
    app_launcher.app.close()


if __name__ == "__main__":
    main()
