#!/usr/bin/env python3
"""
Convert a Gurulok mocap session to a dancer trajectory .npz for Isaac Lab training.

Outputs a simple file with:
  - positions: (T, 3) dancer chest position in Isaac Sim coords (Z-up, right-hand)
  - fps: float

Run on EC2 host (has numpy but not Isaac):
    python3 prepare_dancer_trajectory.py \
        --session /home/ubuntu/mocap_session \
        --out /home/ubuntu/dancer_trajectory.npz \
        --duration 25 --target-fps 30
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from parse_pose_bin import BODY_NAMES, load_session


def unity_to_isaac_pos(positions: np.ndarray) -> np.ndarray:
    """Unity (left-hand Y-up) → Isaac Sim (right-hand Z-up).

    (x, y, z) → (x, z, y)
    """
    out = np.empty_like(positions)
    out[..., 0] = positions[..., 0]
    out[..., 1] = positions[..., 2]
    out[..., 2] = positions[..., 1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--duration", type=float, default=25.0)
    ap.add_argument("--target-fps", type=int, default=50,
                    help="Match Isaac Sim step rate (100Hz / decimation=2 = 50Hz)")
    args = ap.parse_args()

    session = load_session(args.session)
    print(f"Loaded: {session.num_frames} frames @ {session.fps}Hz, "
          f"{session.duration_s:.1f}s (schema {session.schema})")

    # Subsample
    max_frames = int(args.duration * session.fps)
    T = min(session.num_frames, max_frames)
    step = max(1, round(session.fps / args.target_fps))
    indices = np.arange(0, T, step)

    # Get pelvis + torso, compute chest midpoint
    pelvis_idx = BODY_NAMES.index("pelvis")
    torso_idx = BODY_NAMES.index("torso")
    pelvis = session.body_positions[indices, pelvis_idx]  # (N, 3) Unity coords
    torso = session.body_positions[indices, torso_idx]
    chest_unity = (pelvis + torso) * 0.5

    # Also save full body for future use (head, hands for framing verification)
    head_idx = BODY_NAMES.index("head")
    lh_idx = BODY_NAMES.index("left_hand")
    rh_idx = BODY_NAMES.index("right_hand")
    lf_idx = BODY_NAMES.index("left_foot")
    rf_idx = BODY_NAMES.index("right_foot")

    head = session.body_positions[indices, head_idx]
    left_hand = session.body_positions[indices, lh_idx]
    right_hand = session.body_positions[indices, rh_idx]
    left_foot = session.body_positions[indices, lf_idx]
    right_foot = session.body_positions[indices, rf_idx]

    # Convert to Isaac Sim coords (Z-up)
    chest_isaac = unity_to_isaac_pos(chest_unity)
    head_isaac = unity_to_isaac_pos(head)
    lh_isaac = unity_to_isaac_pos(left_hand)
    rh_isaac = unity_to_isaac_pos(right_hand)
    lf_isaac = unity_to_isaac_pos(left_foot)
    rf_isaac = unity_to_isaac_pos(right_foot)

    np.savez(
        args.out,
        positions=chest_isaac,          # (N, 3) main tracking target
        head=head_isaac,                # for framing verification
        left_hand=lh_isaac,
        right_hand=rh_isaac,
        left_foot=lf_isaac,
        right_foot=rf_isaac,
        fps=np.float64(args.target_fps),
        duration_s=np.float64(len(indices) / args.target_fps),
        source_session=str(args.session.name),
    )

    print(f"Saved: {args.out}")
    print(f"  {len(indices)} frames @ {args.target_fps}Hz = {len(indices)/args.target_fps:.1f}s")
    print(f"  Chest height range (Isaac Z): {chest_isaac[:, 2].min():.3f} - {chest_isaac[:, 2].max():.3f} m")
    dx = chest_isaac[:, 0].max() - chest_isaac[:, 0].min()
    dy = chest_isaac[:, 1].max() - chest_isaac[:, 1].min()
    print(f"  Chest XY drift: dx={dx:.3f}, dy={dy:.3f} m")


if __name__ == "__main__":
    main()
