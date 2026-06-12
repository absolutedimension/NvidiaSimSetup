"""
export_drone_trajectory.py — Run a trained Isaac Lab drone policy and dump its
world-space (position, orientation) per simulation step to a JSON file.

The JSON is the input to render_drone_demo.py --trajectory <path>, which bakes
it into an animated USDA → MP4 / GLB.

Runs INSIDE the isaaclab Docker container:

    docker exec isaaclab bash -lc "cd /workspace/isaaclab && \\
        ./isaaclab.sh -p /workspace/isaaclab/export_drone_trajectory.py \\
        --task Isaac-Quadcopter-Direct-v0 \\
        --checkpoint <path-to-pth> \\
        --steps 240 \\
        --out /host_tmp/drone_trajectory.json"

Output JSON shape:
{
  "task": "Isaac-Quadcopter-Direct-v0",
  "fps": 30,                       # caller can override; default matches sim dt
  "frames": [
      {"i": 0, "t": [x, y, z], "q": [qw, qx, qy, qz]},
      ...
  ],
  "goal": [gx, gy, gz]             # the target position the policy was flying toward, if available
}

Coordinate convention is Isaac Sim default (Y-up world). render_drone_demo.py
preserves this exactly when baking the USDA so the OVRTX render orients correctly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher

# --- arg parse must happen BEFORE AppLauncher import-time effects ---
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--task", default="Isaac-Quadcopter-Direct-v0")
parser.add_argument("--checkpoint", required=True,
                    help=".pth file from a prior train.py run")
parser.add_argument("--steps", type=int, default=240,
                    help="number of simulation steps to record (default 240 = ~10s at sim dt 1/24)")
parser.add_argument("--out", required=True, help="output JSON path")
parser.add_argument("--fps", type=int, default=30,
                    help="fps tag stored in JSON; downstream uses it for the USDA timecodes")
parser.add_argument("--deterministic", action="store_true", default=True,
                    help="use deterministic action (mean of policy distribution) instead of sampled")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Force single-env, no viewport, no video — pure physics + policy
args_cli.num_envs = 1
args_cli.viz = "none"
args_cli.enable_cameras = False
args_cli.video = False

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---- imports that need the app to be alive ----
import gymnasium as gym
import torch
import isaaclab_tasks  # noqa: F401  registers the gym envs
from isaaclab_tasks.utils import parse_env_cfg
from isaaclab_rl.rl_games import RlGamesVecEnvWrapper
from rl_games.common import env_configurations, vecenv
from rl_games.torch_runner import Runner
from isaaclab_tasks.utils.parse_cfg import load_cfg_from_registry


def main() -> None:
    out_path = Path(args_cli.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[export] task={args_cli.task} steps={args_cli.steps} -> {out_path}")
    print(f"[export] checkpoint={args_cli.checkpoint}")

    # 1. build env (single env)
    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)

    # 2. configure rl_games to consume that env
    agent_cfg = load_cfg_from_registry(args_cli.task, "rl_games_cfg_entry_point")
    agent_cfg["params"]["config"]["num_actors"] = 1
    obs_groups = agent_cfg["params"]["env"].get("obs_groups")
    concate = agent_cfg["params"]["env"].get("concate_obs_groups", True)
    clip_obs = float(agent_cfg["params"]["config"].get("clip_observations", 100.0))
    clip_act = float(agent_cfg["params"]["config"].get("clip_actions", 100.0))

    wrapped = RlGamesVecEnvWrapper(env, args_cli.device, clip_obs, clip_act, obs_groups, concate)
    vecenv.register("IsaacRlgWrapper", lambda *a, **k: wrapped)
    env_configurations.register(
        "rlgpu",
        {"vecenv_type": "IsaacRlgWrapper", "env_creator": lambda **k: wrapped},
    )

    # 3. load policy
    runner = Runner()
    runner.load(agent_cfg)
    agent = runner.create_player()
    agent.restore(args_cli.checkpoint)
    agent.has_batch_dimension = True
    agent.is_rnn = False

    # 4. roll out
    obs = wrapped.reset()
    obs_in = obs["obs"] if isinstance(obs, dict) else obs

    frames = []
    goal_xyz = None

    for step in range(args_cli.steps):
        with torch.no_grad():
            action = agent.get_action(obs_in, is_deterministic=args_cli.deterministic)
        obs, _, terminated, _ = wrapped.step(action)
        obs_in = obs["obs"] if isinstance(obs, dict) else obs

        # read the drone state directly from the scene articulation.
        # Isaac Lab 3.0 returns warp arrays; convert via .numpy() then index.
        scene = env.unwrapped.scene
        robot = scene["robot"]                       # Articulation; key "robot" is canonical in this env

        def _to_list(arr):
            """Convert (wp.array | torch.Tensor | np.ndarray) row 0 to a Python list."""
            if hasattr(arr, "numpy"):
                return arr.numpy()[0].tolist()
            if hasattr(arr, "cpu"):
                return arr.cpu()[0].tolist()
            return list(arr[0])

        pos_w = _to_list(robot.data.root_pos_w)       # (3,) -> [x, y, z]
        quat_w = _to_list(robot.data.root_quat_w)     # (4,) -> [qw, qx, qy, qz]

        # capture goal once (it's randomized at reset; same across the episode)
        if goal_xyz is None and hasattr(env.unwrapped, "_desired_pos_w"):
            try:
                goal_xyz = _to_list(env.unwrapped._desired_pos_w)
            except Exception:
                goal_xyz = None

        frames.append({"i": step, "t": pos_w, "q": quat_w})

        if step % 30 == 0:
            print(f"  step {step}/{args_cli.steps}  pos={[round(p, 3) for p in pos_w]}")

        if bool(terminated[0]) if hasattr(terminated, "__getitem__") else bool(terminated):
            # the drone reset (out of bounds / timeout) — keep recording so we capture
            # a continuous animation; trained policies usually fly until step budget
            pass

    payload = {
        "task": args_cli.task,
        "checkpoint": args_cli.checkpoint,
        "fps": args_cli.fps,
        "goal": goal_xyz,
        "frames": frames,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"[export] wrote {len(frames)} frames -> {out_path} "
          f"({out_path.stat().st_size / 1024:.1f} KB)")

    simulation_app.close()


if __name__ == "__main__":
    main()
