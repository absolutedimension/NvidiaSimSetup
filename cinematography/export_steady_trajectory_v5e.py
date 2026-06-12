#!/usr/bin/env python3
"""Export a trained STEADY v5e policy rollout to JSON.

Run inside the isaaclab container:
    cd /workspace/isaaclab && ./isaaclab.sh -p \
        /workspace/isaaclab/cinematography/export_steady_trajectory_v5e.py \
        --checkpoint /workspace/isaaclab/logs/rl_games/cinematographer_v5e_steady/2026-05-26_07-58-42/nn/last_cinematographer_v5e_steady_ep_500_rew_8.288788.pth \
        --steps 750 --fps 30 \
        --out /workspace/isaaclab/exports/steady_v5e_trajectory.json
"""
from __future__ import annotations

import argparse
import json

import torch
import gymnasium as gym

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--steps", type=int, default=750, help="Rollout steps (25s * 30fps = 750)")
parser.add_argument("--fps", type=float, default=50.0, help="Policy step rate")
parser.add_argument("--out", required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)

import isaaclab_tasks  # noqa: F401 — triggers gym.register
import warp as wp
from rl_games.torch_runner import Runner
from rl_games.common import env_configurations
from isaaclab_rl.rl_games import RlGamesGpuEnv, RlGamesVecEnvWrapper


def main():
    task = "Isaac-Cinematographer-Steady-v5e"

    env_cfg_cls = gym.spec(task).kwargs["env_cfg_entry_point"]
    if isinstance(env_cfg_cls, str):
        mod_name, cls_name = env_cfg_cls.rsplit(":", 1) if ":" in env_cfg_cls else env_cfg_cls.rsplit(".", 1)
        import importlib
        m = importlib.import_module(mod_name)
        env_cfg_cls = getattr(m, cls_name)

    cfg = env_cfg_cls()
    cfg.scene.num_envs = 1

    env = gym.make(task, cfg=cfg)
    unwrapped = env.unwrapped

    # -- Load rl_games config --
    rl_cfg_path = gym.spec(task).kwargs["rl_games_cfg_entry_point"]
    import os, yaml
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

    # -- Rollout --
    frames = []
    obs = env.reset()[0]
    print(f"[export_steady_v5e] Rolling out {args.steps} steps with trained STEADY v5e policy...")

    for step_i in range(args.steps):
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
        dq = drone_quat[0].cpu().tolist()  # [qw, qx, qy, qz]
        dancer = (dancer_pos[0] - origin).cpu().tolist()
        stillness = unwrapped._stillness_time[0].item()
        hold_q = unwrapped._hold_quality[0].item()

        frames.append({
            "t": step_i / args.fps,
            "drone_pos": dp,
            "drone_quat": dq,
            "dancer_pos": dancer,
            "mode": "STEADY",
            "stillness": round(stillness, 3),
            "hold_quality": round(hold_q, 3),
        })

        if step_i % 100 == 0:
            speed = wp.to_torch(unwrapped._robot.data.root_lin_vel_w)[0].norm().item()
            print(f"  step {step_i}/{args.steps} — pos ({dp[0]:.2f}, {dp[1]:.2f}, {dp[2]:.2f}), "
                  f"still={stillness:.2f}s, hold_q={hold_q:.3f}, speed={speed:.3f} m/s")

        if terminated.any() or truncated.any():
            obs = env.reset()[0]

    # -- Compute quality metrics --
    speeds = []
    for i in range(1, len(frames)):
        dx = [frames[i]["drone_pos"][j] - frames[i-1]["drone_pos"][j] for j in range(3)]
        dt = frames[i]["t"] - frames[i-1]["t"]
        if dt > 0:
            speed = sum(d**2 for d in dx)**0.5 / dt
            speeds.append(speed)

    below_03 = sum(1 for s in speeds if s < 0.3) / len(speeds) * 100 if speeds else 0
    below_005 = sum(1 for s in speeds if s < 0.05) / len(speeds) * 100 if speeds else 0
    median_speed = sorted(speeds)[len(speeds)//2] if speeds else 0
    mean_hold_q = sum(f["hold_quality"] for f in frames) / len(frames)

    print(f"\n=== v5e STEADY Quality Metrics ===")
    print(f"  Frames below 0.3 m/s:  {below_03:.1f}%")
    print(f"  Frames below 0.05 m/s: {below_005:.1f}%")
    print(f"  Median speed:           {median_speed:.4f} m/s")
    print(f"  Mean hold quality:      {mean_hold_q:.3f}")

    # -- Save --
    traj = {
        "version": "v5e_steady",
        "fps": args.fps,
        "num_frames": len(frames),
        "mode": "STEADY",
        "coordinate_system": "isaac_sim_z_up",
        "quality_metrics": {
            "pct_below_0.3_mps": round(below_03, 1),
            "pct_below_0.05_mps": round(below_005, 1),
            "median_speed_mps": round(median_speed, 4),
            "mean_hold_quality": round(mean_hold_q, 3),
        },
        "frames": frames,
    }

    os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(traj, f, indent=1)
    print(f"[export_steady_v5e] Saved {len(frames)} frames to {args.out}")

    env.close()
    app_launcher.app.close()


if __name__ == "__main__":
    main()
