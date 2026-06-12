#!/usr/bin/env python3
"""Roll out a trained LB (Lower Body) AMP policy and export full-body timeline.

Usage (inside isaaclab container):
    cd /workspace/isaaclab
    ./isaaclab.sh -p source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp_lower_body/rollout_lb_policy.py \
        --headless \
        --checkpoint /workspace/isaaclab/lb5_best_agent.pt \
        --steps 600 \
        --out /tmp/lb5_rollout.npz

Output arrays in NPZ:
    body_positions: (T, num_bodies, 3) float32
    body_rotations: (T, num_bodies, 4) float32 (wxyz)
    joint_positions: (T, num_dofs) float32
    body_names, joint_names, fps=60, coordinate_system="isaac_lab_z_up"
"""

import argparse
import os

# ── Argparse BEFORE AppLauncher ──────────────────────────────────────────
parser = argparse.ArgumentParser(description="Roll out trained LB policy")
parser.add_argument("--checkpoint", required=True, help="Path to .pt checkpoint")
parser.add_argument("--steps", type=int, default=600, help="Number of timesteps (600 = 10s at 60Hz)")
parser.add_argument("--out", required=True, help="Output .npz path")
parser.add_argument("--num_envs", type=int, default=4, help="Number of environments for rollout")

# AppLauncher adds --headless, --device, etc.
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# ── Launch simulation app ────────────────────────────────────────────────
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ── Now safe to import Isaac Lab + gymnasium ─────────────────────────────
import numpy as np
import torch
import gymnasium as gym

import isaaclab_tasks  # noqa: registers all tasks including our LB env
from isaaclab_tasks.direct.humanoid_amp_lower_body.humanoid_amp_lower_body_env_cfg import HumanoidAmpLowerBodyEnvCfg


def load_skrl_policy(checkpoint_path: str, obs_space, act_space, device: str):
    """Load a trained skrl AMP policy from a .pt checkpoint."""
    from skrl.models.torch import Model, GaussianMixin, DeterministicMixin
    import torch.nn as nn

    obs_dim = obs_space.shape[-1]  # 81
    act_dim = act_space.shape[-1]  # 14

    class GaussianModel(GaussianMixin, Model):
        def __init__(self, observation_space, action_space, device, clip_actions=False,
                     clip_log_std=True, min_log_std=-20.0, max_log_std=2.0, reduction="sum"):
            Model.__init__(self, observation_space, action_space, device)
            GaussianMixin.__init__(self, clip_actions, clip_log_std, min_log_std, max_log_std, reduction)
            self.net_container = nn.Sequential(
                nn.Linear(obs_dim, 1024), nn.ReLU(),
                nn.Linear(1024, 512), nn.ReLU(),
                nn.Linear(512, act_dim),
            )
            # Fixed log_std as used in training config (initial_log_std=-2.9, fixed_log_std=True)
            self.log_std_parameter = nn.Parameter(torch.full((act_dim,), -2.9))

        def compute(self, inputs, role=""):
            mean = self.net_container(inputs["states"])
            return mean, self.log_std_parameter, {}

    # Create policy on CPU first, load weights, then move to device
    policy = GaussianModel(obs_space, act_space, "cpu")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    if "policy" in checkpoint:
        policy.load_state_dict(checkpoint["policy"])
    elif "models" in checkpoint:
        policy.load_state_dict(checkpoint["models"]["policy"])

    policy = policy.to(device)

    policy.eval()
    return policy


def rollout(env, policy, num_steps: int, device: str):
    """Run the policy for num_steps and capture full-body state."""
    import warp as wp

    all_body_pos = []
    all_body_rot = []
    all_joint_pos = []

    obs, _ = env.reset()
    policy_obs = obs["policy"] if isinstance(obs, dict) else obs

    with torch.no_grad():
        for step in range(num_steps):
            act_result = policy.act({"states": policy_obs}, role="policy")
            action = act_result[0] if isinstance(act_result, tuple) else act_result

            obs, reward, terminated, truncated, info = env.step(action)
            policy_obs = obs["policy"] if isinstance(obs, dict) else obs

            # Capture full body state (env 0 only)
            body_pos = wp.to_torch(env.unwrapped.robot.data.body_pos_w)[0]
            body_quat = wp.to_torch(env.unwrapped.robot.data.body_quat_w)[0]
            joint_pos = wp.to_torch(env.unwrapped.robot.data.joint_pos)[0]

            # Subtract env origin for world-relative coordinates
            origins = env.unwrapped.scene.env_origins
            if hasattr(origins, 'is_cpu'):
                env_origin = origins[0]  # already torch tensor
            else:
                env_origin = wp.to_torch(origins)[0]
            body_pos = body_pos - env_origin.unsqueeze(0)

            all_body_pos.append(body_pos.cpu().numpy())
            all_body_rot.append(body_quat.cpu().numpy())
            all_joint_pos.append(joint_pos.cpu().numpy())

            if step % 60 == 0:
                root_z = body_pos[0, 2].item()
                print(f"  Step {step:4d}/{num_steps}: root_z={root_z:.3f}m, reward={reward[0].item():.3f}")

            if terminated[0] or truncated[0]:
                print(f"  Episode ended at step {step} -- resetting")
                obs, _ = env.reset()
                policy_obs = obs["policy"] if isinstance(obs, dict) else obs

    return (
        np.stack(all_body_pos, axis=0),
        np.stack(all_body_rot, axis=0),
        np.stack(all_joint_pos, axis=0),
    )


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[rollout] Device: {device}")
    print(f"[rollout] Checkpoint: {args_cli.checkpoint}")
    print(f"[rollout] Steps: {args_cli.steps}")

    cfg = HumanoidAmpLowerBodyEnvCfg()
    cfg.scene.num_envs = args_cli.num_envs

    env = gym.make("Isaac-Humanoid-AMP-LowerBody-Direct-v0", cfg=cfg, render_mode=None)

    obs_space = env.observation_space
    act_space = env.action_space
    print(f"[rollout] Obs space: {obs_space.shape}, Act space: {act_space.shape}")

    policy = load_skrl_policy(args_cli.checkpoint, obs_space, act_space, device)

    print(f"\n[rollout] Starting {args_cli.steps}-step rollout...")
    body_pos, body_rot, joint_pos = rollout(env, policy, args_cli.steps, device)

    body_names = list(env.unwrapped.robot.data.body_names)
    joint_names = list(env.unwrapped.robot.data.joint_names)

    np.savez(
        args_cli.out,
        body_positions=body_pos.astype(np.float32),
        body_rotations=body_rot.astype(np.float32),
        joint_positions=joint_pos.astype(np.float32),
        body_names=np.array(body_names),
        joint_names=np.array(joint_names),
        fps=60,
        coordinate_system="isaac_lab_z_up",
        checkpoint=os.path.basename(args_cli.checkpoint),
        num_steps=args_cli.steps,
    )

    duration = args_cli.steps / 60.0
    print(f"\n[rollout] Saved {args_cli.out}")
    print(f"  body_positions: {body_pos.shape}")
    print(f"  body_rotations: {body_rot.shape}")
    print(f"  joint_positions: {joint_pos.shape}")
    print(f"  Duration: {duration:.1f}s at 60 fps")
    print(f"  Body names: {body_names}")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
