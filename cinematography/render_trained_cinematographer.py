#!/usr/bin/env python3
"""Render the trained cinematographer trajectory as MP4 via OVRTX.

Uses the PROVEN USDA format from bake_dancer_usda.py (defaultPrim, upAxis,
metersPerUnit, double3 rotations, inputs:intensity lights) combined with the
trained drone trajectory JSON.

Scene: dancer stick-figure (orange sphere) + drone marker (blue sphere) +
orbital camera that tracks the dancer from behind the drone's perspective.

Run on EC2 host (NOT in container — needs OVRTX on :8001):
    python3 render_trained_cinematographer.py \
        --trajectory /tmp/cinematographer_trajectory.json \
        --out /home/ubuntu/cinematographer_trained.mp4 \
        --width 800 --height 450
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def isaac_to_usd(pos):
    """Isaac Sim Z-up → USD Y-up: (x, y, z) → (x, z, -y)."""
    return (pos[0], pos[2], -pos[1])


def build_usda(traj, target_fps=30, mode="drone_pov", hdri_path=None, lighting_mode=None):
    """Build a self-contained USDA with dancer + drone + camera + lights.

    Modes:
      - "drone_pov": camera rides on the drone, always looking at the dancer (A4 deliverable)
      - "overhead": static overhead camera showing both drone and dancer (debug view)

    hdri_path: if set, replaces hardcoded lights with a DomeLight using the HDRI texture.
    lighting_mode: if set, uses mode-specific USDA light blocks from lighting/presets.py.
    """
    frames = traj["frames"]
    src_fps = traj["fps"]

    num_render_frames = int(len(frames) * target_fps / src_fps)
    end_frame = num_render_frames - 1

    def src_idx(rf):
        t_sec = rf / target_fps
        return min(int(t_sec * src_fps), len(frames) - 1)

    # Precompute all positions in USD coords
    drone_usd = []
    dancer_usd = []
    for rf in range(num_render_frames):
        si = src_idx(rf)
        drone_usd.append(isaac_to_usd(frames[si]["drone_pos"]))
        dancer_usd.append(isaac_to_usd(frames[si]["dancer_pos"]))

    # Scene bounding box
    all_x = [d[0] for d in drone_usd] + [d[0] for d in dancer_usd]
    all_y = [d[1] for d in drone_usd] + [d[1] for d in dancer_usd]
    all_z = [d[2] for d in drone_usd] + [d[2] for d in dancer_usd]
    cx = (min(all_x) + max(all_x)) / 2
    cy = (min(all_y) + max(all_y)) / 2
    cz = (min(all_z) + max(all_z)) / 2

    d0 = dancer_usd[0]
    floor_size = 20.0

    lines = []
    lines.append('#usda 1.0')
    lines.append('(')
    lines.append('    defaultPrim = "World"')
    lines.append('    upAxis = "Y"')
    lines.append('    metersPerUnit = 1.0')
    lines.append(f'    startTimeCode = 0')
    lines.append(f'    endTimeCode = {end_frame}')
    lines.append(f'    timeCodesPerSecond = {target_fps}')
    lines.append(f'    framesPerSecond = {target_fps}')
    lines.append(')')
    lines.append('')
    lines.append('def Xform "World"')
    lines.append('{')

    # Floor
    lines.append('    def Cube "Floor"')
    lines.append('    {')
    lines.append('        double size = 1.0')
    lines.append('        color3f[] primvars:displayColor = [(0.18, 0.20, 0.22)]')
    lines.append(f'        double3 xformOp:translate = ({d0[0]:.4f}, -0.02, {d0[2]:.4f})')
    lines.append(f'        double3 xformOp:scale = ({floor_size:.1f}, 0.04, {floor_size:.1f})')
    lines.append('        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]')
    lines.append('    }')

    # Dancer body sphere (orange)
    lines.append('    def Sphere "DancerBody"')
    lines.append('    {')
    lines.append('        double radius = 0.15')
    lines.append('        color3f[] primvars:displayColor = [(0.9, 0.3, 0.1)]')
    lines.append('        double3 xformOp:translate.timeSamples = {')
    for rf in range(num_render_frames):
        d = dancer_usd[rf]
        lines.append(f'            {rf}: ({d[0]:.5f}, {d[1]:.5f}, {d[2]:.5f}),')
    lines.append('        }')
    lines.append('        uniform token[] xformOpOrder = ["xformOp:translate"]')
    lines.append('    }')

    # Dancer head sphere (skin tone)
    lines.append('    def Sphere "DancerHead"')
    lines.append('    {')
    lines.append('        double radius = 0.10')
    lines.append('        color3f[] primvars:displayColor = [(0.95, 0.85, 0.7)]')
    lines.append('        double3 xformOp:translate.timeSamples = {')
    for rf in range(num_render_frames):
        si = src_idx(rf)
        dp = frames[si]["dancer_pos"]
        head = (dp[0], dp[1], dp[2] + 0.4)
        h = isaac_to_usd(head)
        lines.append(f'            {rf}: ({h[0]:.5f}, {h[1]:.5f}, {h[2]:.5f}),')
    lines.append('        }')
    lines.append('        uniform token[] xformOpOrder = ["xformOp:translate"]')
    lines.append('    }')

    # Camera
    if mode == "drone_pov":
        # Camera ON the drone, always looking at the dancer
        lines.append('    def Camera "Camera"')
        lines.append('    {')
        lines.append('        float focalLength = 35')
        lines.append('        float horizontalAperture = 36')
        lines.append('        float verticalAperture = 24')
        lines.append('        float2 clippingRange = (0.1, 100)')
        lines.append('        double3 xformOp:translate.timeSamples = {')
        for rf in range(num_render_frames):
            d = drone_usd[rf]
            lines.append(f'            {rf}: ({d[0]:.5f}, {d[1]:.5f}, {d[2]:.5f}),')
        lines.append('        }')
        lines.append('        double3 xformOp:rotateXYZ.timeSamples = {')
        for rf in range(num_render_frames):
            dr = drone_usd[rf]
            da = dancer_usd[rf]
            dx = da[0] - dr[0]
            dy = da[1] - dr[1]
            dz = da[2] - dr[2]
            ry = math.atan2(-dx, -dz) * 180 / math.pi
            horiz = math.sqrt(dx**2 + dz**2)
            # CRITICAL: atan2(dy, horiz) not atan2(-dy, horiz)
            # Positive dy (target above) → positive rx → look up
            # Negative dy (target below) → negative rx → look down
            rx = math.atan2(dy, horiz) * 180 / math.pi
            lines.append(f'            {rf}: ({rx:.2f}, {ry:.2f}, 0),')
        lines.append('        }')
        lines.append('        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]')
        lines.append('    }')
    else:
        # Static overhead camera
        cam_x = cx
        cam_y = cy + 4.0
        cam_z = cz + 5.0
        dx = cx - cam_x
        dy = cy - cam_y
        dz = cz - cam_z
        ry = math.atan2(-dx, -dz) * 180 / math.pi
        horiz = math.sqrt(dx**2 + dz**2)
        rx = math.atan2(dy, horiz) * 180 / math.pi
        lines.append('    def Camera "Camera"')
        lines.append('    {')
        lines.append('        float focalLength = 24')
        lines.append('        float horizontalAperture = 36')
        lines.append('        float verticalAperture = 24')
        lines.append('        float2 clippingRange = (0.1, 100)')
        lines.append(f'        double3 xformOp:translate = ({cam_x:.5f}, {cam_y:.5f}, {cam_z:.5f})')
        lines.append(f'        double3 xformOp:rotateXYZ = ({rx:.2f}, {ry:.2f}, 0)')
        lines.append('        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]')
        lines.append('    }')

    # Lights
    if hdri_path:
        lines.append('    def DomeLight "Environment"')
        lines.append('    {')
        lines.append(f'        asset inputs:texture:file = @{hdri_path}@')
        lines.append('        float inputs:intensity = 1.0')
        lines.append('        token inputs:textureFormat = "latlong"')
        lines.append('    }')
    elif lighting_mode:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).parent.parent))
        from lighting.presets import preset_to_usda
        lines.append(preset_to_usda(lighting_mode))
    else:
        lines.append('    def DistantLight "KeyLight"')
        lines.append('    {')
        lines.append('        float inputs:intensity = 5000')
        lines.append('        double3 xformOp:rotateXYZ = (-45, 30, 0)')
        lines.append('        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]')
        lines.append('    }')
        lines.append('    def DistantLight "FillLight"')
        lines.append('    {')
        lines.append('        float inputs:intensity = 2000')
        lines.append('        double3 xformOp:rotateXYZ = (-25, -120, 0)')
        lines.append('        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]')
        lines.append('    }')
        lines.append('    def DomeLight "AmbientDome"')
        lines.append('    {')
        lines.append('        float inputs:intensity = 500')
        lines.append('    }')

    lines.append('}')
    return '\n'.join(lines), num_render_frames


def render_usda_via_ovrtx(usda_text, ovrtx_url, num_frames, width, height, batch_size=50):
    """POST USDA to OVRTX in batches, return merged images dict."""
    import requests

    data_uri = "data:application/octet-stream;base64," + base64.b64encode(
        usda_text.encode()
    ).decode("ascii")

    end_frame = num_frames - 1
    merged_images = {}
    total_batches = (num_frames + batch_size - 1) // batch_size

    for batch_i in range(total_batches):
        start = batch_i * batch_size
        end = min(start + batch_size - 1, end_frame)
        if start > end_frame:
            break

        print(f"  batch {batch_i+1}/{total_batches}: frames {start}..{end}", flush=True)

        payload = {
            "url": data_uri,
            "force_render": True,
            "render_settings": {
                "camera_paths": ["/World/Camera"],
                "frame_range": {"start": start, "end": end},
                "camera_parameters": {"width": width, "height": height},
                "sensors": None,
                "apply_background_mask": False,
            },
        }
        r = requests.post(
            f"{ovrtx_url.rstrip('/')}/render",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        r.raise_for_status()
        body = r.json()
        if body.get("status") != "success":
            raise RuntimeError(f"OVRTX error batch {batch_i}: {body.get('error')}")
        batch_images = body.get("images", {})
        merged_images.update(batch_images)
        print(f"    got {len(batch_images)} frames")

    return merged_images


def images_to_mp4(images, num_frames, out_path, fps, width, height):
    """Decode base64 PNGs → temp dir → ffmpeg MP4."""
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")

    with tempfile.TemporaryDirectory(prefix="cine_frames_") as tmpdir:
        written = 0
        for i in range(num_frames):
            fkey = str(i)
            if fkey not in images:
                continue
            cam_entries = images[fkey]
            cam_path, sensor_map = next(iter(cam_entries.items()))
            b64 = next(iter(sensor_map.values()))
            png_path = Path(tmpdir) / f"frame_{i:04d}.png"
            png_path.write_bytes(base64.b64decode(b64))
            written += 1

        print(f"Decoded {written}/{num_frames} frames")

        cmd = [
            "ffmpeg", "-y", "-loglevel", "warning",
            "-framerate", str(fps),
            "-i", str(Path(tmpdir) / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)

    size_kb = out_path.stat().st_size / 1024
    print(f"Saved: {out_path} ({size_kb:.0f} KB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trajectory", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--height", type=int, default=450)
    ap.add_argument("--ovrtx-url", default="http://localhost:8001")
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--keep-usda", action="store_true")
    ap.add_argument("--usda-only", action="store_true",
                    help="Only write the USDA, skip rendering")
    ap.add_argument("--hdri", default=None,
                    help="Path to HDRI file for DomeLight (replaces default lights)")
    ap.add_argument("--lighting-preset", default=None,
                    help="Lighting preset name: HERO, INTIMATE, EPIC, ENERGY, SOLITUDE, BEAUTY")
    args = ap.parse_args()

    print(f"[1/3] Loading trajectory: {args.trajectory}")
    with open(args.trajectory) as f:
        traj = json.load(f)
    print(f"  {traj['num_frames']} frames @ {traj['fps']} fps "
          f"= {traj['num_frames']/traj['fps']:.1f}s")

    print(f"[2/3] Building USDA (target {args.fps} fps)")
    usda_text, num_frames = build_usda(
        traj, target_fps=args.fps,
        hdri_path=args.hdri, lighting_mode=args.lighting_preset,
    )
    print(f"  {num_frames} render frames, {len(usda_text)} chars")

    if args.keep_usda or args.usda_only:
        usda_path = args.out.with_suffix(".usda")
        usda_path.write_text(usda_text)
        print(f"  Saved USDA: {usda_path}")

    if args.usda_only:
        return

    print(f"[3/3] Rendering via OVRTX at {args.ovrtx_url}")
    images = render_usda_via_ovrtx(
        usda_text, args.ovrtx_url, num_frames,
        args.width, args.height, args.batch_size,
    )

    images_to_mp4(images, num_frames, args.out, args.fps, args.width, args.height)
    print(f"\nDone: {num_frames} frames @ {args.fps} fps = {num_frames/args.fps:.1f}s")


if __name__ == "__main__":
    main()
