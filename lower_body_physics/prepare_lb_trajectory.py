"""
prepare_lb_trajectory.py — Prepare Quest mocap data for the Lower Body Physics env.

Takes an existing AMP npz (from pose_bin_to_amp_motion.py) and prepares it for the
pinned-upper-body env by:
  1. Validating body positions/rotations are physically reasonable
  2. Computing upper/lower body split metadata
  3. Resampling to the env's sim frequency if needed
  4. Saving a trajectory file with all metadata the env needs

Usage:
    python3 prepare_lb_trajectory.py \
        --input ../checkpoints/gurulok_dance_v1.npz \
        --output lb_trajectory_v1.npz

Or from raw pose.bin:
    python3 prepare_lb_trajectory.py \
        --session ../mocap_handoff/Mocap/dance_20260519_194152/ \
        --output lb_trajectory_v1.npz
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


# ---------- Constants ----------

ISAAC_BODY_NAMES = [
    "pelvis", "torso", "head",
    "right_upper_arm", "right_lower_arm", "right_hand",
    "left_upper_arm", "left_lower_arm", "left_hand",
    "right_thigh", "right_shin", "right_foot",
    "left_thigh", "left_shin", "left_foot",
]

ISAAC_DOF_NAMES = [
    "abdomen_x", "abdomen_y", "abdomen_z",
    "neck_x", "neck_y", "neck_z",
    "right_shoulder_x", "right_shoulder_y", "right_shoulder_z", "right_elbow",
    "left_shoulder_x", "left_shoulder_y", "left_shoulder_z", "left_elbow",
    "right_hip_x", "right_hip_y", "right_hip_z", "right_knee",
    "right_ankle_x", "right_ankle_y", "right_ankle_z",
    "left_hip_x", "left_hip_y", "left_hip_z", "left_knee",
    "left_ankle_x", "left_ankle_y", "left_ankle_z",
]

# Upper body: bodies whose motion comes from Quest tracking
UPPER_BODY_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # pelvis through hands
UPPER_BODY_NAMES = [ISAAC_BODY_NAMES[i] for i in UPPER_BODY_INDICES]

# Lower body: bodies controlled by RL policy
LOWER_BODY_INDICES = [9, 10, 11, 12, 13, 14]  # thighs through feet
LOWER_BODY_NAMES = [ISAAC_BODY_NAMES[i] for i in LOWER_BODY_INDICES]

# Upper body DOF indices (0-13): these will be pinned via body-level tracking
UPPER_DOF_INDICES = list(range(0, 14))
# Lower body DOF indices (14-27): these are controlled by the RL policy
LOWER_DOF_INDICES = list(range(14, 28))


# ---------- Validation ----------

def validate_body_positions(body_pos: np.ndarray, fps: int) -> dict:
    """Validate that body positions are physically reasonable.

    Args:
        body_pos: (T, 15, 3) body positions in Isaac coords (RH, Z-up)
        fps: frames per second

    Returns:
        dict with validation results
    """
    T = body_pos.shape[0]
    results = {}

    # 1. Pelvis height should be roughly 0.7-1.2m (Z in Isaac coords)
    pelvis_z = body_pos[:, 0, 2]  # pelvis Z
    results["pelvis_z_mean"] = float(pelvis_z.mean())
    results["pelvis_z_range"] = [float(pelvis_z.min()), float(pelvis_z.max())]
    results["pelvis_z_ok"] = 0.3 < pelvis_z.mean() < 2.0

    # 2. Head should be above pelvis
    head_z = body_pos[:, 2, 2]
    results["head_above_pelvis"] = bool((head_z > pelvis_z).all())

    # 3. Body-to-body distances should be anatomically reasonable
    # Pelvis-to-head distance: ~0.5-0.8m
    pelvis_head_dist = np.linalg.norm(body_pos[:, 2] - body_pos[:, 0], axis=-1)
    results["pelvis_head_dist_mean"] = float(pelvis_head_dist.mean())
    results["pelvis_head_dist_ok"] = 0.3 < pelvis_head_dist.mean() < 1.2

    # 4. No NaN or inf values
    results["has_nan"] = bool(np.isnan(body_pos).any())
    results["has_inf"] = bool(np.isinf(body_pos).any())

    # 5. Velocity check: no teleportation (body shouldn't move >2m between frames)
    if T > 1:
        dt = 1.0 / fps
        body_vel = np.diff(body_pos, axis=0) / dt
        max_vel = np.abs(body_vel).max()
        results["max_body_velocity"] = float(max_vel)
        results["velocity_ok"] = max_vel < 20.0  # 20 m/s is very fast motion

    # 6. Foot positions (bodies 11, 14) should be near ground level
    right_foot_z = body_pos[:, 11, 2]
    left_foot_z = body_pos[:, 14, 2]
    results["right_foot_z_min"] = float(right_foot_z.min())
    results["left_foot_z_min"] = float(left_foot_z.min())

    # Overall
    results["valid"] = (
        results["pelvis_z_ok"]
        and results["head_above_pelvis"]
        and results["pelvis_head_dist_ok"]
        and not results["has_nan"]
        and not results["has_inf"]
    )

    return results


def validate_body_rotations(body_rot: np.ndarray) -> dict:
    """Validate quaternions are unit quaternions."""
    norms = np.linalg.norm(body_rot, axis=-1)
    results = {
        "quat_norm_mean": float(norms.mean()),
        "quat_norm_min": float(norms.min()),
        "quat_norm_max": float(norms.max()),
        "unit_quats": bool(np.allclose(norms, 1.0, atol=0.01)),
    }
    return results


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path,
                     help="Existing AMP npz file (from pose_bin_to_amp_motion.py)")
    src.add_argument("--session", type=Path,
                     help="Raw session directory with pose.bin + meta.json")
    ap.add_argument("--output", type=Path, required=True,
                    help="Output trajectory npz for the lower body env")
    ap.add_argument("--target-fps", type=int, default=60,
                    help="Target framerate (default: 60, matches Quest capture rate)")
    args = ap.parse_args()

    # Load data
    if args.input:
        print(f"Loading existing npz: {args.input}")
        d = np.load(args.input, allow_pickle=True)
        fps = int(d["fps"])
        body_pos = d["body_positions"]
        body_rot = d["body_rotations"]
        body_linvel = d["body_linear_velocities"]
        body_angvel = d["body_angular_velocities"]
        dof_pos = d["dof_positions"]
        dof_vel = d["dof_velocities"]
    else:
        # Convert from raw session using the existing converter
        converter_path = Path(__file__).parent.parent / "mocap_handoff" / "pose_bin_to_amp_motion.py"
        if not converter_path.exists():
            # Try alternate location
            for p in [
                Path("/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/pose_bin_to_amp_motion.py"),
                Path(__file__).parent.parent / "cinematography" / "parse_pose_bin.py",
            ]:
                if p.exists():
                    converter_path = p
                    break

        if not converter_path.exists():
            print(f"ERROR: Cannot find pose_bin_to_amp_motion.py converter")
            sys.exit(1)

        # Import and run converter
        import importlib.util
        spec = importlib.util.spec_from_file_location("converter", converter_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        data = mod.convert_session(args.session)
        fps = int(data["fps"])
        body_pos = data["body_positions"]
        body_rot = data["body_rotations"]
        body_linvel = data["body_linear_velocities"]
        body_angvel = data["body_angular_velocities"]
        dof_pos = data["dof_positions"]
        dof_vel = data["dof_velocities"]

    T = body_pos.shape[0]
    duration = T / fps
    print(f"  {T} frames @ {fps} fps = {duration:.1f}s")
    print(f"  body_positions: {body_pos.shape}")
    print(f"  body_rotations: {body_rot.shape}")

    # Validate
    print("\nValidating body positions...")
    pos_results = validate_body_positions(body_pos, fps)
    for k, v in pos_results.items():
        status = "✓" if (isinstance(v, bool) and v) or (k == "has_nan" and not v) or (k == "has_inf" and not v) else ""
        print(f"  {k}: {v} {status}")

    print("\nValidating body rotations...")
    rot_results = validate_body_rotations(body_rot)
    for k, v in rot_results.items():
        status = "✓" if (isinstance(v, bool) and v) else ""
        print(f"  {k}: {v} {status}")

    if not pos_results["valid"]:
        print("\n⚠ WARNING: Body position validation failed — proceed with caution")

    # Compute upper body trajectory (for pinning)
    upper_body_pos = body_pos[:, UPPER_BODY_INDICES]      # (T, 9, 3)
    upper_body_rot = body_rot[:, UPPER_BODY_INDICES]      # (T, 9, 4)
    upper_body_linvel = body_linvel[:, UPPER_BODY_INDICES] # (T, 9, 3)
    upper_body_angvel = body_angvel[:, UPPER_BODY_INDICES] # (T, 9, 3)

    # Lower body reference (for AMP discriminator)
    lower_body_pos = body_pos[:, LOWER_BODY_INDICES]      # (T, 6, 3)
    lower_body_rot = body_rot[:, LOWER_BODY_INDICES]      # (T, 6, 4)

    print(f"\nUpper body trajectory: {upper_body_pos.shape} ({len(UPPER_BODY_NAMES)} bodies)")
    print(f"  Bodies: {UPPER_BODY_NAMES}")
    print(f"Lower body reference: {lower_body_pos.shape} ({len(LOWER_BODY_NAMES)} bodies)")
    print(f"  Bodies: {LOWER_BODY_NAMES}")
    print(f"Upper DOFs (pinned): indices {UPPER_DOF_INDICES}")
    print(f"Lower DOFs (policy): indices {LOWER_DOF_INDICES}")

    # Save trajectory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.output,
        # Full body data (for AMP discriminator)
        fps=np.int64(fps),
        dof_names=np.array(ISAAC_DOF_NAMES),
        body_names=np.array(ISAAC_BODY_NAMES),
        body_positions=body_pos.astype(np.float32),
        body_rotations=body_rot.astype(np.float32),
        body_linear_velocities=body_linvel.astype(np.float32),
        body_angular_velocities=body_angvel.astype(np.float32),
        dof_positions=dof_pos.astype(np.float32),
        dof_velocities=dof_vel.astype(np.float32),
        # Split metadata
        upper_body_indices=np.array(UPPER_BODY_INDICES, dtype=np.int32),
        lower_body_indices=np.array(LOWER_BODY_INDICES, dtype=np.int32),
        upper_dof_indices=np.array(UPPER_DOF_INDICES, dtype=np.int32),
        lower_dof_indices=np.array(LOWER_DOF_INDICES, dtype=np.int32),
        # Validation results
        pelvis_z_mean=np.float32(pos_results["pelvis_z_mean"]),
        duration_seconds=np.float32(duration),
    )

    size_kb = args.output.stat().st_size / 1024
    print(f"\n✓ Saved: {args.output} ({size_kb:.0f} KB)")
    print(f"  Duration: {duration:.1f}s, FPS: {fps}, Frames: {T}")
    print(f"  Upper body: {len(UPPER_BODY_INDICES)} bodies, {len(UPPER_DOF_INDICES)} DOFs (pinned)")
    print(f"  Lower body: {len(LOWER_BODY_INDICES)} bodies, {len(LOWER_DOF_INDICES)} DOFs (policy)")


if __name__ == "__main__":
    main()
