#!/usr/bin/env python3
"""Render the trained cinematographer trajectory as MP4 via OVRTX.

Bakes a USDA with:
  - Drone (Starling 2) animated along the trained trajectory
  - Dancer stick figure from mocap
  - Camera that follows the drone's perspective (slightly behind)
  - Floor plane

Then renders each frame via OVRTX and encodes to MP4 with ffmpeg.

Run on EC2 host (NOT in container — needs OVRTX on :8001):
    python3 render_cinematographer_mp4.py \
        --trajectory /tmp/cinematographer_trajectory.json \
        --dancer-npz /tmp/dancer_trajectory.npz \
        --out /home/ubuntu/cinematographer_trained.mp4 \
        --width 800 --height 450 --fps 30
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import requests


def isaac_to_usd_pos(pos):
    """Isaac Sim (Z-up) → USD (Y-up): (x, y, z) → (x, z, -y)."""
    return (pos[0], pos[2], -pos[1])


def isaac_to_usd_quat(q):
    """Isaac quat (w,x,y,z) Z-up → USD Y-up: (w, x, z, -y)."""
    w, x, y, z = q
    return (w, x, z, -y)


def build_usda(traj, dancer_data, drone_asset_path, fps_render, drone_scale=5.0):
    """Build a USDA string with drone + dancer + camera."""
    frames = traj["frames"]
    src_fps = traj["fps"]

    dancer_pos_all = dancer_data["positions"]
    dancer_fps = float(dancer_data["fps"])

    num_render_frames = int(len(frames) * fps_render / src_fps)
    end_frame = num_render_frames - 1

    lines = []
    lines.append('#usda 1.0')
    lines.append(f'(startTimeCode = 0; endTimeCode = {end_frame}; '
                 f'timeCodesPerSecond = {fps_render}; framesPerSecond = {fps_render})')
    lines.append('')
    lines.append('def Xform "World" {')

    # Floor
    lines.append('  def Mesh "Floor" {')
    lines.append('    float3[] points = [(-10,-0.01,-10),(10,-0.01,-10),(10,-0.01,10),(-10,-0.01,10)]')
    lines.append('    int[] faceVertexCounts = [4]')
    lines.append('    int[] faceVertexIndices = [0,1,2,3]')
    lines.append('    color3f[] primvars:displayColor = [(0.3,0.3,0.35)]')
    lines.append('  }')

    # Dancer stick figure (keyframed positions)
    lines.append('  def Xform "Dancer" {')
    lines.append('    def Sphere "Body" {')
    lines.append('      float radius = 0.15')
    lines.append('      color3f[] primvars:displayColor = [(0.9, 0.3, 0.1)]')

    # Keyframe dancer position
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["dancer_pos"]
        usd_pos = isaac_to_usd_pos(dp)
        lines.append(f'      double3 xformOp:translate.timeSamples = {{')
        break

    # Write all dancer keyframes at once
    lines_dancer = []
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["dancer_pos"]
        usd_pos = isaac_to_usd_pos(dp)
        lines_dancer.append(f'        {rf}: ({usd_pos[0]:.4f}, {usd_pos[1]:.4f}, {usd_pos[2]:.4f}),')

    # Remove the premature line and redo
    lines.pop()  # remove the broken start
    lines.append(f'      double3 xformOp:translate.timeSamples = {{')
    lines.extend(lines_dancer)
    lines.append('      }')
    lines.append('      uniform token[] xformOpOrder = ["xformOp:translate"]')
    lines.append('    }')

    # Head marker
    lines.append('    def Sphere "Head" {')
    lines.append('      float radius = 0.1')
    lines.append('      color3f[] primvars:displayColor = [(1.0, 0.8, 0.6)]')
    lines.append(f'      double3 xformOp:translate.timeSamples = {{')
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["dancer_pos"]
        head_pos = (dp[0], dp[1], dp[2] + 0.4)
        usd_pos = isaac_to_usd_pos(head_pos)
        lines.append(f'        {rf}: ({usd_pos[0]:.4f}, {usd_pos[1]:.4f}, {usd_pos[2]:.4f}),')
    lines.append('      }')
    lines.append('      uniform token[] xformOpOrder = ["xformOp:translate"]')
    lines.append('    }')
    lines.append('  }')

    # Drone Xform with reference to Starling 2 USD
    lines.append(f'  def Xform "Drone" {{')
    lines.append(f'    def Xform "Model" (')
    lines.append(f'      references = @{drone_asset_path}@')
    lines.append(f'    ) {{')
    lines.append(f'      double3 xformOp:scale = ({drone_scale}, {drone_scale}, {drone_scale})')
    lines.append(f'      uniform token[] xformOpOrder = ["xformOp:scale"]')
    lines.append(f'    }}')

    # Drone position keyframes
    lines.append(f'    double3 xformOp:translate.timeSamples = {{')
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["drone_pos"]
        usd_pos = isaac_to_usd_pos(dp)
        lines.append(f'      {rf}: ({usd_pos[0]:.4f}, {usd_pos[1]:.4f}, {usd_pos[2]:.4f}),')
    lines.append('    }')

    # Drone orientation keyframes
    lines.append(f'    quatf xformOp:orient.timeSamples = {{')
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dq = frames[src_idx]["drone_quat"]
        usd_q = isaac_to_usd_quat(dq)
        lines.append(f'      {rf}: ({usd_q[0]:.6f}, {usd_q[1]:.6f}, {usd_q[2]:.6f}, {usd_q[3]:.6f}),')
    lines.append('    }')
    lines.append('    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient"]')
    lines.append('  }')

    # Camera — slightly behind and above the drone, looking at the dancer
    lines.append('  def Camera "Camera" {')
    lines.append('    float focalLength = 35')
    lines.append('    float horizontalAperture = 36')
    lines.append('    float verticalAperture = 24')
    lines.append('    float2 clippingRange = (0.1, 100)')
    lines.append(f'    double3 xformOp:translate.timeSamples = {{')
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["drone_pos"]
        dancer = frames[src_idx]["dancer_pos"]

        # Camera position: behind drone (relative to drone-dancer direction), slightly above
        drone_usd = isaac_to_usd_pos(dp)
        dancer_usd = isaac_to_usd_pos(dancer)

        dx = drone_usd[0] - dancer_usd[0]
        dy_h = drone_usd[2] - dancer_usd[2]  # horizontal in USD Z
        dist_h = math.sqrt(dx**2 + dy_h**2) + 1e-8

        # Camera offset: 2m behind drone (away from dancer), 1m above drone
        cam_x = drone_usd[0] + 2.0 * dx / dist_h
        cam_y = drone_usd[1] + 1.0
        cam_z = drone_usd[2] + 2.0 * dy_h / dist_h

        lines.append(f'      {rf}: ({cam_x:.4f}, {cam_y:.4f}, {cam_z:.4f}),')
    lines.append('    }')

    # Camera rotation — look at midpoint between drone and dancer
    lines.append(f'    float3 xformOp:rotateXYZ.timeSamples = {{')
    for rf in range(num_render_frames):
        t_sec = rf / fps_render
        src_idx = min(int(t_sec * src_fps), len(frames) - 1)
        dp = frames[src_idx]["drone_pos"]
        dancer = frames[src_idx]["dancer_pos"]

        drone_usd = isaac_to_usd_pos(dp)
        dancer_usd = isaac_to_usd_pos(dancer)

        # Look at midpoint
        look_x = (drone_usd[0] + dancer_usd[0]) / 2
        look_y = (drone_usd[1] + dancer_usd[1]) / 2
        look_z = (drone_usd[2] + dancer_usd[2]) / 2

        # Camera is behind drone
        dx = drone_usd[0] - dancer_usd[0]
        dy_h = drone_usd[2] - dancer_usd[2]
        dist_h = math.sqrt(dx**2 + dy_h**2) + 1e-8
        cam_x = drone_usd[0] + 2.0 * dx / dist_h
        cam_y = drone_usd[1] + 1.0
        cam_z = drone_usd[2] + 2.0 * dy_h / dist_h

        # Direction from camera to look target
        to_x = look_x - cam_x
        to_y = look_y - cam_y
        to_z = look_z - cam_z

        ry = math.atan2(-to_x, -to_z) * 180 / math.pi
        horiz = math.sqrt(to_x**2 + to_z**2)
        rx = math.atan2(-to_y, horiz) * 180 / math.pi

        lines.append(f'      {rf}: ({rx:.2f}, {ry:.2f}, 0),')
    lines.append('    }')
    lines.append('    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]')
    lines.append('  }')

    # Lights
    lines.append('  def DomeLight "DomeLight" {')
    lines.append('    float intensity = 1000')
    lines.append('    color3f color = (1, 1, 1)')
    lines.append('  }')
    lines.append('  def DistantLight "KeyLight" {')
    lines.append('    float intensity = 3000')
    lines.append('    float3 xformOp:rotateXYZ = (-45, 30, 0)')
    lines.append('    uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]')
    lines.append('  }')

    lines.append('}')  # close World

    return '\n'.join(lines), num_render_frames


def render_usda_via_ovrtx(usda_text, camera_path, start_frame, end_frame,
                          width, height, ovrtx_url, batch_size=10):
    """POST USDA to OVRTX and return list of PNG bytes."""
    encoded = base64.b64encode(usda_text.encode()).decode()
    data_uri = f"data:application/octet-stream;base64,{encoded}"

    all_pngs = []
    for batch_start in range(start_frame, end_frame + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_frame)

        payload = {
            "url": data_uri,
            "force_render": True,
            "render_settings": {
                "camera_paths": [camera_path],
                "frame_range": {"start": batch_start, "end": batch_end},
                "camera_parameters": {"width": width, "height": height},
                "sensors": None,
                "apply_background_mask": False,
            },
        }

        print(f"  Rendering frames {batch_start}-{batch_end}...", end=" ", flush=True)
        resp = requests.post(
            f"{ovrtx_url}/render",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") != "success":
            raise RuntimeError(f"OVRTX error: {body.get('error')}")

        batch_images = body.get("images", {})
        for f in range(batch_start, batch_end + 1):
            frame_key = str(f)
            if frame_key not in batch_images:
                print(f"\n  WARN: frame {f} missing from response")
                continue
            cam_entries = batch_images[frame_key]
            cam_key, sensor_map = next(iter(cam_entries.items()))
            b64 = next(iter(sensor_map.values()))
            all_pngs.append(base64.b64decode(b64))
        print(f"got {len(batch_images)} frames")

    return all_pngs


def pngs_to_mp4(pngs, out_path, fps, width, height):
    """ffmpeg-encode PNGs to MP4."""
    with tempfile.TemporaryDirectory() as tmp:
        for i, png in enumerate(pngs):
            with open(os.path.join(tmp, f"frame_{i:05d}.png"), "wb") as f:
                f.write(png)

        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(tmp, "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", f"scale={width}:{height}",
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    print(f"Saved: {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajectory", required=True)
    ap.add_argument("--dancer-npz", default=None)
    ap.add_argument("--drone-asset", default="/host_tmp/cf2x.usd")
    ap.add_argument("--drone-scale", type=float, default=5.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--height", type=int, default=450)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--ovrtx-url", default="http://localhost:8001")
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--keep-usda", action="store_true")
    args = ap.parse_args()

    with open(args.trajectory) as f:
        traj = json.load(f)
    print(f"Trajectory: {traj['num_frames']} frames @ {traj['fps']} fps")

    dancer_data = None
    if args.dancer_npz and os.path.exists(args.dancer_npz):
        dancer_data = dict(np.load(args.dancer_npz))
    else:
        dancer_data = {"positions": np.zeros((1, 3)), "fps": traj["fps"]}

    usda_text, num_frames = build_usda(
        traj, dancer_data, args.drone_asset, args.fps, args.drone_scale
    )
    print(f"USDA: {num_frames} frames, {len(usda_text)} chars")

    if args.keep_usda:
        usda_path = args.out.rsplit(".", 1)[0] + ".usda"
        with open(usda_path, "w") as f:
            f.write(usda_text)
        print(f"Saved USDA: {usda_path}")

    pngs = render_usda_via_ovrtx(
        usda_text,
        camera_path="/World/Camera",
        start_frame=0,
        end_frame=num_frames - 1,
        width=args.width,
        height=args.height,
        ovrtx_url=args.ovrtx_url,
        batch_size=args.batch_size,
    )

    pngs_to_mp4(pngs, args.out, args.fps, args.width, args.height)


if __name__ == "__main__":
    main()
