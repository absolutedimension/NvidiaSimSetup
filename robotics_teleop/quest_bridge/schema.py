"""Frame schema for the Quest → PC teleop stream.

See ../docs/PROTOCOL.md for the wire format. This module decodes one JSON
message into a typed dataclass + applies the Unity LH Y-up → Isaac RH Z-up
coordinate transform used throughout the rest of the pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


PROTOCOL_VERSION = 1
BODY_JOINT_COUNT = 84
HAND_JOINT_COUNT = 52   # 26 left + 26 right
DEFAULT_PORT = 9000


@dataclass
class GazeEye:
    pos: np.ndarray         # (3,) world position of eye-pose origin
    dir: np.ndarray         # (3,) unit-length gaze direction
    conf: float


@dataclass
class FrameIsaac:
    """A teleop frame in Isaac RH Z-up coordinates (post-conversion)."""
    t_quest_ns: int
    t_pc_recv_ns: int       # filled in by receiver on recv()
    frame: int
    tracking_quality: int   # 0/1/2/3 — see protocol

    # Body — (84, 3) positions, (84, 4) quaternions (x,y,z,w), (84,) valid mask
    body_pos: np.ndarray
    body_quat: np.ndarray
    body_valid: np.ndarray

    # Hands — (52, 3), (52, 4) — NaN where not tracked
    hand_pos: np.ndarray
    hand_quat: np.ndarray
    left_hand_tracked: bool
    right_hand_tracked: bool

    # Gaze (optional)
    left_eye: Optional[GazeEye] = None
    right_eye: Optional[GazeEye] = None

    @property
    def latency_ms(self) -> float:
        """End-to-end latency (Quest sensor read → PC bridge recv)."""
        return (self.t_pc_recv_ns - self.t_quest_ns) / 1e6


def _unity_pos_to_isaac(p: np.ndarray) -> np.ndarray:
    """(x, y, z)_unity_LH_Yup → (x, z, y)_isaac_RH_Zup.
    Same as `pose_bin_to_amp_motion_v2._unity_to_isaac_pos`.
    """
    return np.stack([p[..., 0], p[..., 2], p[..., 1]], axis=-1)


def _unity_quat_to_isaac(q: np.ndarray) -> np.ndarray:
    """(qx, qy, qz, qw)_unity → (qx, qz, qy, qw)_isaac.
    Component swap to match the position-axis swap.
    """
    return np.stack([q[..., 0], q[..., 2], q[..., 1], q[..., 3]], axis=-1)


def decode_frame(msg: dict, t_pc_recv_ns: int) -> FrameIsaac:
    """Parse one WebSocket JSON message into a FrameIsaac.

    Raises ValueError if schema version is wrong or shapes are off.
    """
    v = msg.get("v")
    if v != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version: {v} (expected {PROTOCOL_VERSION})")

    body = msg["body"]
    joints = np.asarray(body["joints"], dtype=np.float32)  # (84, 7)
    if joints.shape != (BODY_JOINT_COUNT, 7):
        raise ValueError(f"body.joints shape {joints.shape}, expected ({BODY_JOINT_COUNT}, 7)")
    body_pos_unity = joints[:, :3]
    body_quat_unity = joints[:, 3:7]
    body_valid = np.asarray(body["valid"], dtype=bool)
    if body_valid.shape != (BODY_JOINT_COUNT,):
        raise ValueError(f"body.valid shape {body_valid.shape}")

    hands = msg["hands"]
    hjoints = np.asarray(hands["joints"], dtype=np.float32)  # (52, 7)
    if hjoints.shape != (HAND_JOINT_COUNT, 7):
        raise ValueError(f"hands.joints shape {hjoints.shape}")
    hand_pos_unity = hjoints[:, :3]
    hand_quat_unity = hjoints[:, 3:7]

    # Coordinate conversion (only done here, never repeated downstream)
    body_pos = _unity_pos_to_isaac(body_pos_unity)
    body_quat = _unity_quat_to_isaac(body_quat_unity)
    hand_pos = _unity_pos_to_isaac(hand_pos_unity)
    hand_quat = _unity_quat_to_isaac(hand_quat_unity)

    # Gaze (optional)
    left_eye = right_eye = None
    g = msg.get("gaze", {})
    if g and "left" in g:
        le = g["left"]
        left_eye = GazeEye(
            pos=_unity_pos_to_isaac(np.asarray(le["pos"], dtype=np.float32)),
            dir=_unity_pos_to_isaac(np.asarray(le["dir"], dtype=np.float32)),
            conf=float(le.get("conf", 0.0)),
        )
    if g and "right" in g:
        re = g["right"]
        right_eye = GazeEye(
            pos=_unity_pos_to_isaac(np.asarray(re["pos"], dtype=np.float32)),
            dir=_unity_pos_to_isaac(np.asarray(re["dir"], dtype=np.float32)),
            conf=float(re.get("conf", 0.0)),
        )

    return FrameIsaac(
        t_quest_ns=int(msg["t_quest_ns"]),
        t_pc_recv_ns=t_pc_recv_ns,
        frame=int(msg["frame"]),
        tracking_quality=int(msg.get("tracking_quality", 0)),
        body_pos=body_pos,
        body_quat=body_quat,
        body_valid=body_valid,
        hand_pos=hand_pos,
        hand_quat=hand_quat,
        left_hand_tracked=bool(hands.get("left_tracked", False)),
        right_hand_tracked=bool(hands.get("right_tracked", False)),
        left_eye=left_eye,
        right_eye=right_eye,
    )
