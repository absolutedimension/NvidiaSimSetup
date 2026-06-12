"""Verify Isaac-Quadcopter-OSM-City-Direct-v0 loads, resets and steps.

Run inside the isaaclab container:
  cd /workspace/isaaclab
  ./isaaclab.sh -p source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_osm_city/smoke_test.py
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

SENTINEL = Path("/tmp/smoke_sentinel.txt")
SENTINEL.write_text("step:start\n")

def log(msg):
    line = f"[smoke {time.time():.1f}] {msg}"
    print(line, flush=True)
    sys.stderr.write(line + "\n")
    sys.stderr.flush()
    with SENTINEL.open("a") as fh:
        fh.write(line + "\n")

log("imports begin")

from isaaclab.app import AppLauncher

log("AppLauncher imported")

ap = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(ap)
args = ap.parse_args()
args.headless = True
args.enable_cameras = False
app_launcher = AppLauncher(args)
app = app_launcher.app
log("AppLauncher started")

# imports that need the sim app to exist
import gymnasium as gym
import torch

log("about to import isaaclab_tasks")
import isaaclab_tasks  # noqa: F401  triggers gym.register chain
log("isaaclab_tasks imported")
from isaaclab_tasks.utils import parse_env_cfg

TASK = "Isaac-Quadcopter-OSM-City-Direct-v0"

def main():
    log(f"parsing env cfg for {TASK}")
    cfg = parse_env_cfg(TASK, device="cuda", num_envs=4)
    log(f"env cfg parsed; num_envs={cfg.scene.num_envs}")

    log("gym.make")
    env = gym.make(TASK, cfg=cfg)
    log(f"env made; obs={env.observation_space}, act={env.action_space}")

    log("env.reset")
    obs, info = env.reset()
    obs_shape = obs["policy"].shape if isinstance(obs, dict) else obs.shape
    log(f"reset OK, obs shape={obs_shape}")

    action = torch.zeros(
        (cfg.scene.num_envs, env.action_space.shape[0]),
        device="cuda",
    )
    log("stepping 10 frames")
    for i in range(10):
        obs, rew, term, trunc, info = env.step(action)
    log(f"10 steps OK; reward mean={rew.mean().item():.3f}, "
        f"died={term.sum().item()}/{cfg.scene.num_envs}")

    env.close()
    log("=== SMOKE PASSED ===")

try:
    main()
except Exception:
    log("EXCEPTION:")
    log(traceback.format_exc())
    raise
finally:
    log("closing app")
    app.close()
