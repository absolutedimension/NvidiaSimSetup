#!/usr/bin/env python3
"""
Parse Gurulok mocap pose.bin files (schema 1.0.0 and 2.0.0).

Returns per-frame joint positions and rotations in the original Unity
coordinate frame (left-hand, Y-up) or optionally converted to USD (Y-up,
right-hand via Z-negate).

Binary layout per frame:
  Header (12 bytes): time_s:f32, frame_idx:u16, tracking_quality:u8, reserved:u8, pad:u32
  Joints (N × 40 bytes each): pos:3×f32, quat:4×f32(xyzw), vel:3×f32

Schema 1.0.0: N=33 joints (basic OVRBody skeleton)
Schema 2.0.0: N=84 joints (full OVRBody + hand sub-joints)

Also parses aux.bin (eye gaze + body confidence, 68 bytes/frame) when present.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


JOINT_REC = np.dtype([
    ("pos",  "<f4", (3,)),
    ("quat", "<f4", (4,)),
    ("vel",  "<f4", (3,)),
])

def _make_frame_dtype(num_joints: int):
    return np.dtype([
        ("t",      "<f4"),
        ("fidx",   "<u2"),
        ("tq",     "u1"),
        ("res",    "u1"),
        ("pad",    "<u4"),
        ("joints", JOINT_REC, (num_joints,)),
    ])

FRAME_V1 = _make_frame_dtype(33)
FRAME_V2 = _make_frame_dtype(84)

AUX_FRAME = np.dtype([
    ("t",       "<f4"),
    ("fidx",    "<u2"),
    ("res",     "<u2"),
    ("gaze_pos",    "<f4", (3,)),
    ("gaze_dir",    "<f4", (3,)),
    ("gaze_conf",   "<f4"),
    ("body_conf",   "<f4"),
    ("pad",         "<f4", (7,)),
])

# --- Joint index → body part mapping ---
# For stick-figure rendering, we extract 15 key body positions.

# Schema 1.0.0 (33 joints): indices follow meta.json joint_order directly
BODY_SOURCES_V1 = {
    "pelvis":          {"pos": [1],     "rot": 1},
    "torso":           {"pos": [3, 4],  "rot": 4},
    "head":            {"pos": [6],     "rot": 6},
    "left_upper_arm":  {"pos": [8],     "rot": 8},
    "left_lower_arm":  {"pos": [9],     "rot": 9},
    "left_hand":       {"pos": [10],    "rot": 10},
    "right_upper_arm": {"pos": [17],    "rot": 17},
    "right_lower_arm": {"pos": [18],    "rot": 18},
    "right_hand":      {"pos": [19],    "rot": 19},
    "left_thigh":      {"pos": [25],    "rot": 25},
    "left_shin":       {"pos": [26],    "rot": 26},
    "left_foot":       {"pos": [27],    "rot": 27},
    "right_thigh":     {"pos": [29],    "rot": 29},
    "right_shin":      {"pos": [30],    "rot": 30},
    "right_foot":      {"pos": [31],    "rot": 31},
}

# Schema 2.0.0 (84 joints): indices follow OVRPlugin.BoneId.FullBody_* enum,
# NOT the meta.json joint_order (which is shuffled). Proven in pose_bin_to_amp_motion_v2.py.
BODY_SOURCES_V2 = {
    "pelvis":          {"pos": [1],        "rot": 1},
    "torso":           {"pos": [3, 4, 5],  "rot": 5},
    "head":            {"pos": [7],        "rot": 7},
    "left_upper_arm":  {"pos": [10],       "rot": 10},
    "left_lower_arm":  {"pos": [11],       "rot": 11},
    "left_hand":       {"pos": [18, 19],   "rot": 19},
    "right_upper_arm": {"pos": [15],       "rot": 15},
    "right_lower_arm": {"pos": [16],       "rot": 16},
    "right_hand":      {"pos": [44, 45],   "rot": 45},
    "left_thigh":      {"pos": [70],       "rot": 70},
    "left_shin":       {"pos": [71],       "rot": 71},
    "left_foot":       {"pos": [73, 76],   "rot": 73},
    "right_thigh":     {"pos": [77],       "rot": 77},
    "right_shin":      {"pos": [78],       "rot": 78},
    "right_foot":      {"pos": [80, 83],   "rot": 80},
}

BODY_NAMES = [
    "pelvis", "torso", "head",
    "left_upper_arm", "left_lower_arm", "left_hand",
    "right_upper_arm", "right_lower_arm", "right_hand",
    "left_thigh", "left_shin", "left_foot",
    "right_thigh", "right_shin", "right_foot",
]

# Skeleton connectivity for stick-figure lines (parent → child)
BONES = [
    ("pelvis", "torso"),
    ("torso", "head"),
    ("torso", "left_upper_arm"),
    ("left_upper_arm", "left_lower_arm"),
    ("left_lower_arm", "left_hand"),
    ("torso", "right_upper_arm"),
    ("right_upper_arm", "right_lower_arm"),
    ("right_lower_arm", "right_hand"),
    ("pelvis", "left_thigh"),
    ("left_thigh", "left_shin"),
    ("left_shin", "left_foot"),
    ("pelvis", "right_thigh"),
    ("right_thigh", "right_shin"),
    ("right_shin", "right_foot"),
]


@dataclass
class MocapSession:
    meta: dict
    num_frames: int
    fps: float
    duration_s: float
    schema: str
    body_positions: np.ndarray     # (T, 15, 3) in Unity coords (LH, Y-up)
    body_rotations: np.ndarray     # (T, 15, 4) quaternion xyzw
    raw_positions: np.ndarray      # (T, N, 3) all joints, Unity coords
    raw_rotations: np.ndarray      # (T, N, 4) all joints
    gaze_positions: Optional[np.ndarray] = None   # (T, 3) eye gaze origin
    gaze_directions: Optional[np.ndarray] = None  # (T, 3) eye gaze direction
    gaze_confidence: Optional[np.ndarray] = None  # (T,) 0..1
    body_confidence: Optional[np.ndarray] = None  # (T,) 0..1


def unity_to_usd_pos(p: np.ndarray) -> np.ndarray:
    """Unity LH Y-up → USD RH Y-up: negate Z."""
    return np.stack([p[..., 0], p[..., 1], -p[..., 2]], axis=-1)


def unity_to_usd_quat(q: np.ndarray) -> np.ndarray:
    """Unity LH → USD RH (both Y-up): negate qz."""
    return np.stack([q[..., 0], q[..., 1], -q[..., 2], q[..., 3]], axis=-1)


def _extract_bodies(raw_pos, raw_quat, sources):
    """Extract 15 body positions/rotations from raw joint arrays."""
    T = raw_pos.shape[0]
    valid = ~np.isnan(raw_pos[..., 0])
    safe_pos = np.where(valid[..., None], raw_pos, 0.0)

    body_pos = np.zeros((T, 15, 3), dtype=np.float32)
    body_rot = np.zeros((T, 15, 4), dtype=np.float32)
    body_rot[..., 3] = 1.0

    for i, name in enumerate(BODY_NAMES):
        src = sources[name]
        accum = np.zeros((T, 3), dtype=np.float32)
        n = np.zeros(T, dtype=np.float32)
        for j in src["pos"]:
            if j >= raw_pos.shape[1]:
                continue
            m = valid[:, j]
            accum += safe_pos[:, j] * m[:, None]
            n += m
        nz = n > 0
        body_pos[nz, i] = accum[nz] / n[nz, None]

        rot_j = src["rot"]
        if rot_j < raw_quat.shape[1]:
            q = raw_quat[:, rot_j]
            q_valid = np.linalg.norm(q, axis=-1) > 0.5
            body_rot[q_valid, i] = q[q_valid]

    return body_pos, body_rot


def ik_fill_standing_legs(body_pos, user_height=1.78):
    """Fill lower-body positions with a standing pose based on pelvis height."""
    pelvis = body_pos[:, 0]
    thigh_len = 0.245 * user_height
    hip_lateral = 0.10 * user_height

    for side_name, sign in [("left", -1.0), ("right", 1.0)]:
        i_th = BODY_NAMES.index(f"{side_name}_thigh")
        i_sh = BODY_NAMES.index(f"{side_name}_shin")
        i_ft = BODY_NAMES.index(f"{side_name}_foot")
        body_pos[:, i_th, 0] = pelvis[:, 0] + sign * hip_lateral
        body_pos[:, i_th, 1] = pelvis[:, 1] - 0.05
        body_pos[:, i_th, 2] = pelvis[:, 2]
        body_pos[:, i_sh, 0] = pelvis[:, 0] + sign * hip_lateral
        body_pos[:, i_sh, 1] = pelvis[:, 1] - thigh_len
        body_pos[:, i_sh, 2] = pelvis[:, 2]
        body_pos[:, i_ft, 0] = pelvis[:, 0] + sign * hip_lateral
        body_pos[:, i_ft, 1] = 0.0
        body_pos[:, i_ft, 2] = pelvis[:, 2] + 0.10 * user_height
    return body_pos


def load_session(session_dir: Path, ik_fill_legs: bool = True) -> MocapSession:
    """Load a mocap session from disk."""
    meta = json.loads((session_dir / "meta.json").read_text())
    schema = meta.get("schema_version", "1.0.0")
    num_joints = len(meta.get("joint_order", []))
    fps = meta["sample_rate_hz"]

    if schema == "2.0.0" and num_joints == 84:
        dtype = FRAME_V2
        sources = BODY_SOURCES_V2
    elif num_joints == 33:
        dtype = FRAME_V1
        sources = BODY_SOURCES_V1
    else:
        dtype = _make_frame_dtype(num_joints)
        sources = BODY_SOURCES_V1 if num_joints <= 33 else BODY_SOURCES_V2

    raw = np.fromfile(session_dir / "pose.bin", dtype=dtype)
    T = raw.shape[0]
    raw_pos = raw["joints"]["pos"].astype(np.float32)
    raw_quat = raw["joints"]["quat"].astype(np.float32)

    body_pos, body_rot = _extract_bodies(raw_pos, raw_quat, sources)

    # IK fill legs if they're all zeros (Quest UpperBody mode)
    lower_idx = [9, 10, 11, 12, 13, 14]
    if ik_fill_legs and np.abs(body_pos[:, lower_idx]).sum() < 1e-6:
        user_h = meta.get("user_height_meters", 1.78)
        body_pos = ik_fill_standing_legs(body_pos, user_h)

    # Parse aux.bin for gaze data
    gaze_pos = gaze_dir = gaze_conf = body_conf = None
    aux_path = session_dir / "aux.bin"
    if aux_path.exists() and aux_path.stat().st_size > 0:
        aux = np.fromfile(aux_path, dtype=AUX_FRAME)
        if len(aux) >= T:
            aux = aux[:T]
        gaze_pos = aux["gaze_pos"].astype(np.float32)
        gaze_dir = aux["gaze_dir"].astype(np.float32)
        gaze_conf = aux["gaze_conf"].astype(np.float32)
        body_conf = aux["body_conf"].astype(np.float32)

    return MocapSession(
        meta=meta,
        num_frames=T,
        fps=fps,
        duration_s=T / fps,
        schema=schema,
        body_positions=body_pos,
        body_rotations=body_rot,
        raw_positions=raw_pos,
        raw_rotations=raw_quat,
        gaze_positions=gaze_pos,
        gaze_directions=gaze_dir,
        gaze_confidence=gaze_conf,
        body_confidence=body_conf,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_pose_bin.py <session_dir>")
        sys.exit(1)
    sess = load_session(Path(sys.argv[1]))
    print(f"Session: {sess.meta['session_id']}")
    print(f"Schema:  {sess.schema}")
    print(f"Frames:  {sess.num_frames} @ {sess.fps} Hz = {sess.duration_s:.1f}s")
    print(f"Body positions shape: {sess.body_positions.shape}")
    print(f"Raw positions shape:  {sess.raw_positions.shape}")
    pelvis = sess.body_positions[:, 0]
    print(f"Pelvis Y (height) — mean: {pelvis[:, 1].mean():.3f}m, "
          f"min: {pelvis[:, 1].min():.3f}m, max: {pelvis[:, 1].max():.3f}m")
    head = sess.body_positions[:, 2]
    print(f"Head Y (height)   — mean: {head[:, 1].mean():.3f}m, "
          f"min: {head[:, 1].min():.3f}m, max: {head[:, 1].max():.3f}m")
    if sess.gaze_positions is not None:
        print(f"Gaze data: {sess.gaze_positions.shape}, "
              f"confidence mean: {sess.gaze_confidence.mean():.3f}")
    else:
        print("Gaze data: not available")

    # Check for NaN bodies
    nan_mask = np.isnan(sess.body_positions)
    if nan_mask.any():
        nan_bodies = [BODY_NAMES[i] for i in range(15) if nan_mask[:, i].any()]
        print(f"WARNING: NaN in body positions: {nan_bodies}")
    else:
        print("No NaN in body positions (clean)")
