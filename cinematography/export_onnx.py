#!/usr/bin/env python3
"""Export trained cinematographer v4 policy to ONNX for real-time Unity Sentis inference.

Extracts the actor network from an rl_games checkpoint, bakes in running-mean/std
input normalization, and exports a standalone ONNX model.

Input:  observation tensor [batch, 33]
  - [0:3]   lin_vel_b       drone body-frame linear velocity
  - [3:6]   ang_vel_b       drone body-frame angular velocity
  - [6:9]   gravity_b       projected gravity in drone body frame
  - [9:12]  rel_dancer_b    relative dancer position in drone body frame
  - [12:15] rel_vel_b       dancer velocity in drone body frame
  - [15]    distance        scalar distance to dancer
  - [16]    azimuth         horizontal angle to dancer (rad)
  - [17]    elevation       vertical angle to dancer (rad)
  - [18:24] mode_onehot     6-dim one-hot: HERO/INTIMATE/EPIC/ENERGY/SOLITUDE/BEAUTY
  - [24:33] music_obs       9 audio features (or zeros)

Output: deterministic action [batch, 4]
  - [0]  vertical thrust   (-1..1 maps to 0..thrust_max)
  - [1]  roll moment       (-1..1 scaled by moment_scale)
  - [2]  pitch moment
  - [3]  yaw moment

Run inside isaaclab container (needs torch):
    python3 export_onnx.py \
        --checkpoint /workspace/isaaclab/logs/rl_games/cinematographer_direct/2026-05-24_17-54-46/nn/last_cinematographer_direct_ep_500_rew_1.5395943.pth \
        --out /workspace/isaaclab/cinematographer_v4.onnx

Or on any machine with torch installed.
"""
import argparse
import os
import torch
import torch.nn as nn


class CinematographerActor(nn.Module):
    """Standalone actor with baked-in rl_games RunningMeanStd normalization."""

    def __init__(self, obs_dim=33, act_dim=4, hidden=(256, 256, 128)):
        super().__init__()
        self.register_buffer("running_mean", torch.zeros(obs_dim))
        self.register_buffer("running_var", torch.ones(obs_dim))

        layers = []
        in_dim = obs_dim
        for h in hidden:
            layers.append(nn.Linear(in_dim, h))
            layers.append(nn.ELU())
            in_dim = h
        self.mlp = nn.Sequential(*layers)
        self.mu = nn.Linear(in_dim, act_dim)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        x = (obs - self.running_mean) / (self.running_var.sqrt() + 1e-5)
        x = x.clamp(-5.0, 5.0)
        x = self.mlp(x)
        return self.mu(x).clamp(-1.0, 1.0)


def detect_hidden_units(state):
    """Auto-detect MLP architecture from checkpoint keys."""
    hidden = []
    idx = 0
    while True:
        key = f"a2c_network.actor_mlp.{idx}.weight"
        if key in state:
            hidden.append(state[key].shape[0])
            idx += 2  # skip activation layer
        else:
            break
    return tuple(hidden)


def load_from_checkpoint(ckpt_path, obs_dim=33, act_dim=4, hidden=None):
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state = ckpt.get("model", ckpt)

    print("Checkpoint keys:", sorted(k for k in state if not k.startswith("a2c_network.value")
                                     and not k.startswith("value_mean_std")))

    if hidden is None:
        hidden = detect_hidden_units(state)
    print(f"Detected architecture: obs({obs_dim}) -> {list(hidden)} -> act({act_dim})")

    actor = CinematographerActor(obs_dim, act_dim, hidden)

    with torch.no_grad():
        if "running_mean_std.running_mean" in state:
            actor.running_mean.copy_(state["running_mean_std.running_mean"])
            actor.running_var.copy_(state["running_mean_std.running_var"])
            count = state.get("running_mean_std.count", "?")
            print(f"Loaded running_mean_std (count={count})")
        else:
            print("WARNING: no running_mean_std — using identity normalization")

        idx = 0
        layer_i = 0
        while True:
            w = f"a2c_network.actor_mlp.{idx}.weight"
            b = f"a2c_network.actor_mlp.{idx}.bias"
            if w not in state:
                break
            mlp_idx = layer_i * 2
            actor.mlp[mlp_idx].weight.copy_(state[w])
            actor.mlp[mlp_idx].bias.copy_(state[b])
            print(f"  mlp[{idx}]: {list(state[w].shape)}")
            idx += 2
            layer_i += 1

        if "a2c_network.mu.weight" in state:
            actor.mu.weight.copy_(state["a2c_network.mu.weight"])
            actor.mu.bias.copy_(state["a2c_network.mu.bias"])
            print(f"  mu: {list(state['a2c_network.mu.weight'].shape)}")
        else:
            raise KeyError("a2c_network.mu.weight not found")

    return actor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out", default="cinematographer_v4.onnx")
    parser.add_argument("--obs-dim", type=int, default=33)
    parser.add_argument("--act-dim", type=int, default=4)
    args = parser.parse_args()

    print(f"Loading: {args.checkpoint}")
    actor = load_from_checkpoint(args.checkpoint, args.obs_dim, args.act_dim)
    actor.eval()

    dummy = torch.randn(1, args.obs_dim)
    with torch.no_grad():
        test_out = actor(dummy)
    print(f"\nTest: obs {list(dummy.shape)} -> action {test_out[0].tolist()}")

    # Export with dynamo=False to force legacy tracer (embeds weights inline,
    # no sidecar .onnx.data file). Unity Sentis / AI Inference Engine needs
    # a single self-contained .onnx file.
    torch.onnx.export(
        actor,
        dummy,
        args.out,
        input_names=["observation"],
        output_names=["action"],
        dynamic_axes={"observation": {0: "batch"}, "action": {0: "batch"}},
        opset_version=13,
        dynamo=False,
    )

    size_kb = os.path.getsize(args.out) / 1024
    print(f"\nExported: {args.out} ({size_kb:.1f} KB)")

    # Verify no sidecar was created
    data_path = args.out + ".data"
    if os.path.exists(data_path):
        print(f"WARNING: sidecar {data_path} was created — weights NOT fully embedded")
    else:
        print("✓ Self-contained ONNX (no sidecar .data file)")

    # Also save a metadata JSON for the Unity side
    import json
    meta = {
        "obs_dim": args.obs_dim,
        "act_dim": args.act_dim,
        "obs_layout": [
            {"name": "lin_vel_b", "start": 0, "end": 3, "desc": "drone body-frame linear velocity"},
            {"name": "ang_vel_b", "start": 3, "end": 6, "desc": "drone body-frame angular velocity"},
            {"name": "gravity_b", "start": 6, "end": 9, "desc": "projected gravity in body frame"},
            {"name": "rel_dancer_b", "start": 9, "end": 12, "desc": "relative dancer pos in body frame"},
            {"name": "rel_vel_b", "start": 12, "end": 15, "desc": "dancer velocity in body frame"},
            {"name": "distance", "start": 15, "end": 16, "desc": "scalar distance to dancer"},
            {"name": "azimuth", "start": 16, "end": 17, "desc": "horizontal angle (rad)"},
            {"name": "elevation", "start": 17, "end": 18, "desc": "vertical angle (rad)"},
            {"name": "mode_onehot", "start": 18, "end": 24, "desc": "6-dim one-hot: HERO/INTIMATE/EPIC/ENERGY/SOLITUDE/BEAUTY"},
            {"name": "music_obs", "start": 24, "end": 33, "desc": "9 audio features (zeros if none)"},
        ],
        "act_layout": [
            {"name": "thrust", "idx": 0, "desc": "vertical thrust [-1,1] -> 0..thrust_max"},
            {"name": "roll_moment", "idx": 1, "desc": "roll torque [-1,1] * moment_scale"},
            {"name": "pitch_moment", "idx": 2, "desc": "pitch torque"},
            {"name": "yaw_moment", "idx": 3, "desc": "yaw torque"},
        ],
        "physics": {
            "robot_mass_kg": 0.28,
            "thrust_to_weight": 3.6,
            "moment_scale": 0.02,
            "gravity": 9.81,
            "sim_dt": 0.005,
            "decimation": 4,
            "policy_hz": 50,
        },
        "coord_system": {
            "training": "isaac_sim_z_up_right_hand",
            "unity": "y_up_left_hand",
            "transform_pos": "(x, y, z) -> (x, z, y)",
            "transform_quat": "(qw, qx, qy, qz) -> (qw, qx, qz, qy) then negate qz for handedness",
        },
        "modes": ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"],
        "source_checkpoint": args.checkpoint,
    }
    meta_path = args.out.replace(".onnx", "_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata: {meta_path}")


if __name__ == "__main__":
    main()
