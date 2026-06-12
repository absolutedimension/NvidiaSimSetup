#!/usr/bin/env python3
"""
bake_dancer_usda.py — Phase A1+A2: bake a dancer stick figure + orbital camera to USDA.

Reads a Gurulok mocap session (pose.bin), extracts 15 body positions,
renders them as animated sphere prims (stick figure), adds a smooth 2m
orbital camera, floor, and lighting. Output is a self-contained USDA
ready for OVRTX rendering.

Usage (on EC2 or locally for USDA-only):
    python3 bake_dancer_usda.py \
        --session /path/to/mocap_handoff/Mocap/dance_20260519_213931 \
        --out /tmp/dancer_orbital.usda \
        --duration 25 --target-fps 30 --orbit-radius 2.0
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from parse_pose_bin import (
    BODY_NAMES, BONES, MocapSession, load_session, unity_to_usd_pos,
)

BODY_COLORS = {
    "pelvis":          "(0.9, 0.3, 0.2)",
    "torso":           "(0.9, 0.5, 0.2)",
    "head":            "(0.95, 0.85, 0.7)",
    "left_upper_arm":  "(0.3, 0.6, 0.9)",
    "left_lower_arm":  "(0.3, 0.6, 0.9)",
    "left_hand":       "(0.4, 0.7, 1.0)",
    "right_upper_arm": "(0.2, 0.8, 0.4)",
    "right_lower_arm": "(0.2, 0.8, 0.4)",
    "right_hand":      "(0.3, 0.9, 0.5)",
    "left_thigh":      "(0.3, 0.6, 0.9)",
    "left_shin":       "(0.3, 0.6, 0.9)",
    "left_foot":       "(0.4, 0.7, 1.0)",
    "right_thigh":     "(0.2, 0.8, 0.4)",
    "right_shin":      "(0.2, 0.8, 0.4)",
    "right_foot":      "(0.3, 0.9, 0.5)",
}

BODY_RADII = {
    "head": 0.10,
    "pelvis": 0.08,
    "torso": 0.07,
    "left_hand": 0.04, "right_hand": 0.04,
    "left_foot": 0.05, "right_foot": 0.05,
}
DEFAULT_RADIUS = 0.05


def _fmt_vec3(v):
    return f"({v[0]:.5f}, {v[1]:.5f}, {v[2]:.5f})"


def _subsample(session: MocapSession, target_fps: int, max_duration: float):
    """Subsample body positions from session fps to target fps, capped at max_duration."""
    T = session.num_frames
    src_fps = session.fps
    max_frames_src = int(max_duration * src_fps)
    T = min(T, max_frames_src)

    step = max(1, round(src_fps / target_fps))
    indices = np.arange(0, T, step)
    return session.body_positions[indices]  # (N, 15, 3) in Unity coords


def _build_body_spheres(positions_usd: np.ndarray, fps: int) -> str:
    """Build USDA text for 15 animated sphere prims."""
    N = positions_usd.shape[0]
    parts = []
    for i, name in enumerate(BODY_NAMES):
        radius = BODY_RADII.get(name, DEFAULT_RADIUS)
        color = BODY_COLORS[name]
        samples = []
        for f in range(N):
            p = positions_usd[f, i]
            samples.append(f"        {f}: {_fmt_vec3(p)},")

        part = f"""
    def Sphere "{name}"
    {{
        double radius = {radius}
        color3f[] primvars:displayColor = [{color}]
        double3 xformOp:translate.timeSamples = {{
{chr(10).join(samples)}
        }}
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}"""
        parts.append(part)
    return "\n".join(parts)


def _build_bone_cylinders(positions_usd: np.ndarray, fps: int) -> str:
    """Build USDA text for bone-connecting cylinder prims.

    Each cylinder is placed at the midpoint between parent/child joints,
    oriented and scaled to span the gap. Uses per-frame timeSamples for
    translate and scale (height = distance), with a fixed small radius.
    Orientation is baked as rotateXYZ pointing from parent to child.
    """
    N = positions_usd.shape[0]
    parts = []
    for bi, (parent, child) in enumerate(BONES):
        pi = BODY_NAMES.index(parent)
        ci = BODY_NAMES.index(child)

        translate_samples = []
        scale_samples = []
        rotate_samples = []

        for f in range(N):
            p0 = positions_usd[f, pi]
            p1 = positions_usd[f, ci]
            mid = (p0 + p1) * 0.5
            diff = p1 - p0
            length = float(np.linalg.norm(diff))
            if length < 1e-6:
                length = 0.01
                diff = np.array([0.0, 1.0, 0.0])

            d = diff / length
            # USD Cylinder is Y-aligned by default, height=1, radius=1
            # We scale Y to the bone length, X/Z to the radius
            # Rotation: align Y-axis to the bone direction
            # Using rotateXYZ: first compute the angles
            # Y-axis = (0,1,0). We need rotation to align (0,1,0) → d
            ry = math.atan2(d[0], d[2]) * 180 / math.pi if abs(d[0]) + abs(d[2]) > 1e-6 else 0
            horiz = math.sqrt(d[0]**2 + d[2]**2)
            rx = -math.atan2(horiz, d[1]) * 180 / math.pi if abs(d[1]) > 1e-6 or horiz > 1e-6 else 0

            radius = 0.02
            translate_samples.append(f"        {f}: {_fmt_vec3(mid)},")
            scale_samples.append(f"        {f}: ({radius:.4f}, {length/2:.5f}, {radius:.4f}),")
            rotate_samples.append(f"        {f}: ({rx:.2f}, {ry:.2f}, 0),")

        part = f"""
    def Cylinder "bone_{bi}_{parent}_to_{child}"
    {{
        double height = 2.0
        double radius = 1.0
        color3f[] primvars:displayColor = [(0.85, 0.85, 0.85)]
        double3 xformOp:translate.timeSamples = {{
{chr(10).join(translate_samples)}
        }}
        double3 xformOp:scale.timeSamples = {{
{chr(10).join(scale_samples)}
        }}
        double3 xformOp:rotateXYZ.timeSamples = {{
{chr(10).join(rotate_samples)}
        }}
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
    }}"""
        parts.append(part)
    return "\n".join(parts)


def _build_orbital_camera(
    pelvis_positions: np.ndarray,
    torso_positions: np.ndarray,
    num_frames: int,
    fps: int,
    radius: float = 2.0,
    height_offset: float = 0.3,
) -> str:
    """Build USDA text for an orbital camera that tracks the dancer per-frame.

    Camera orbits around the dancer's per-frame chest midpoint (average of
    pelvis + torso), always looking at the dancer. This keeps the dancer
    centered regardless of how they move across the floor.
    """
    translate_samples = []
    rotate_samples = []
    for f in range(num_frames):
        # Track point = midpoint between pelvis and torso (chest height)
        target = (pelvis_positions[f] + torso_positions[f]) * 0.5
        tx, ty, tz = float(target[0]), float(target[1]), float(target[2])

        angle = 2 * math.pi * f / num_frames
        cam_x = tx + radius * math.sin(angle)
        cam_y = ty + height_offset
        cam_z = tz + radius * math.cos(angle)

        # Look-at rotation: camera faces toward the target
        dx = tx - cam_x
        dy = ty - cam_y
        dz = tz - cam_z
        ry = math.atan2(-dx, -dz) * 180 / math.pi
        horiz = math.sqrt(dx**2 + dz**2)
        rx = math.atan2(-dy, horiz) * 180 / math.pi

        translate_samples.append(f"        {f}: ({cam_x:.5f}, {cam_y:.5f}, {cam_z:.5f}),")
        rotate_samples.append(f"        {f}: ({rx:.2f}, {ry:.2f}, 0),")

    return f"""
    def Camera "Camera"
    {{
        float focalLength = 35
        float horizontalAperture = 36
        float verticalAperture = 24
        float2 clippingRange = (0.1, 100)
        double3 xformOp:translate.timeSamples = {{
{chr(10).join(translate_samples)}
        }}
        double3 xformOp:rotateXYZ.timeSamples = {{
{chr(10).join(rotate_samples)}
        }}
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}"""


def bake_usda(
    session: MocapSession,
    out_path: Path,
    duration: float = 25.0,
    target_fps: int = 30,
    orbit_radius: float = 2.0,
    orbit_height_offset: float = 0.3,
    with_bones: bool = True,
) -> tuple[int, int]:
    """Bake the dancer + orbital camera USDA. Returns (num_frames, fps)."""
    # Subsample to target fps
    positions_unity = _subsample(session, target_fps, duration)
    positions_usd = unity_to_usd_pos(positions_unity)
    num_frames = positions_usd.shape[0]
    end_frame = num_frames - 1

    # Per-frame pelvis and torso positions for camera tracking
    pelvis_idx = BODY_NAMES.index("pelvis")
    torso_idx = BODY_NAMES.index("torso")
    pelvis_usd = positions_usd[:, pelvis_idx]
    torso_usd = positions_usd[:, torso_idx]

    # Floor at Y=0
    floor_size = max(orbit_radius * 3, 6.0)

    body_spheres = _build_body_spheres(positions_usd, target_fps)
    bone_cylinders = _build_bone_cylinders(positions_usd, target_fps) if with_bones else ""
    camera = _build_orbital_camera(
        pelvis_usd, torso_usd, num_frames, target_fps,
        orbit_radius, orbit_height_offset,
    )

    usda = f"""#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
    metersPerUnit = 1.0
    startTimeCode = 0
    endTimeCode = {end_frame}
    timeCodesPerSecond = {target_fps}
    framesPerSecond = {target_fps}
)

def Xform "World"
{{
    def Cube "Floor"
    {{
        double size = 1.0
        color3f[] primvars:displayColor = [(0.18, 0.20, 0.22)]
        double3 xformOp:translate = (0, -0.02, 0)
        double3 xformOp:scale = ({floor_size}, 0.04, {floor_size})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }}

    def Xform "Dancer"
    {{
{body_spheres}
{bone_cylinders}
    }}

{camera}

    def DistantLight "KeyLight"
    {{
        float inputs:intensity = 5000
        double3 xformOp:rotateXYZ = (-45, 30, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def DistantLight "FillLight"
    {{
        float inputs:intensity = 2000
        double3 xformOp:rotateXYZ = (-25, -120, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def DomeLight "AmbientDome"
    {{
        float inputs:intensity = 500
    }}
}}
"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(usda)
    size_kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path} ({size_kb:.0f} KB)")
    print(f"  {num_frames} frames @ {target_fps} fps = {num_frames/target_fps:.1f}s")
    print(f"  Camera: tracking dancer per-frame, orbit radius={orbit_radius}m, "
          f"height offset={orbit_height_offset}m")
    return num_frames, target_fps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", required=True, type=Path,
                    help="Mocap session directory (contains meta.json + pose.bin)")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output .usda path")
    ap.add_argument("--duration", type=float, default=25.0,
                    help="Max clip duration in seconds (default: 25)")
    ap.add_argument("--target-fps", type=int, default=30,
                    help="Output frame rate (default: 30)")
    ap.add_argument("--orbit-radius", type=float, default=2.0,
                    help="Camera orbit radius in meters (default: 2.0)")
    ap.add_argument("--orbit-height", type=float, default=0.3,
                    help="Camera height offset above pelvis (default: 0.3)")
    ap.add_argument("--no-bones", action="store_true",
                    help="Omit bone cylinders (spheres only)")
    args = ap.parse_args()

    print(f"Loading session: {args.session}")
    session = load_session(args.session)
    print(f"  {session.num_frames} frames @ {session.fps} Hz = {session.duration_s:.1f}s "
          f"(schema {session.schema})")

    bake_usda(
        session, args.out,
        duration=args.duration,
        target_fps=args.target_fps,
        orbit_radius=args.orbit_radius,
        orbit_height_offset=args.orbit_height,
        with_bones=not args.no_bones,
    )


if __name__ == "__main__":
    main()
