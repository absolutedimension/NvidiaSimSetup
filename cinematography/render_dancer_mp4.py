#!/usr/bin/env python3
"""
render_dancer_mp4.py — Phase A2: render baked dancer USDA to MP4 via OVRTX.

End-to-end pipeline:
  1. Loads a mocap session and bakes a dancer + orbital camera USDA
  2. Base64-encodes the USDA and POSTs to OVRTX rendering API
  3. Decodes per-frame PNGs from the response
  4. ffmpeg-encodes PNGs to MP4

Reuses the proven OVRTX rendering patterns from render_drone_demo.py.

Usage (on EC2, where OVRTX is on localhost:8001):
    python3 render_dancer_mp4.py \
        --session /path/to/mocap_handoff/Mocap/dance_20260519_213931 \
        --out /home/ubuntu/dancer_orbital.mp4 \
        --duration 25 --target-fps 30 \
        --width 800 --height 450

    # USDA-only mode (no OVRTX, no ffmpeg — for local testing):
    python3 render_dancer_mp4.py \
        --session /path/to/session \
        --out /tmp/test.mp4 \
        --usda-only
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from parse_pose_bin import load_session
from bake_dancer_usda import bake_usda


def render_usda_via_ovrtx(
    usda_path: Path,
    base_url: str,
    frames: int,
    width: int,
    height: int,
    timeout: float = 600.0,
    batch_size: int = 50,
) -> dict:
    """POST the data-URI'd USDA to /render in batches and merge responses.

    OVRTX times out on large frame ranges (>120 frames). We split into
    batches of `batch_size` frames, POST each separately, and merge the
    images dict into a single response body.
    """
    import requests

    data_uri = "data:application/octet-stream;base64," + base64.b64encode(
        usda_path.read_bytes()
    ).decode("ascii")
    usda_kb = usda_path.stat().st_size / 1024
    b64_kb = len(data_uri) / 1024

    merged_images = {}
    total_batches = (frames + batch_size) // batch_size

    for batch_i in range(total_batches):
        start = batch_i * batch_size
        end = min(start + batch_size - 1, frames)
        if start > frames:
            break

        print(f"  batch {batch_i+1}/{total_batches}: frames {start}..{end} "
              f"({end - start + 1} frames)")

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
            f"{base_url.rstrip('/')}/render",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        r.raise_for_status()
        body = r.json()
        if body.get("status") != "success":
            raise SystemExit(f"OVRTX render failed on batch {batch_i}: "
                             f"status={body.get('status')} error={body.get('error')}")
        batch_images = body.get("images", {})
        merged_images.update(batch_images)
        print(f"    got {len(batch_images)} frames")

    print(f"POST /render complete: {len(merged_images)} frames total, "
          f"usda={usda_kb:.0f}KB size={width}x{height}")
    return {"status": "success", "images": merged_images}


def decode_frames_to_pngs(body: dict, frames: int, out_dir: Path) -> list[Path]:
    """Walk body['images'][frame][camera][sensor] → base64 → PNG files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    images = body.get("images", {})
    missing = 0
    for i in range(frames + 1):
        frame_key = str(i)
        if frame_key not in images:
            missing += 1
            continue
        cam_entries = images[frame_key]
        cam_path, sensor_map = next(iter(cam_entries.items()))
        b64 = next(iter(sensor_map.values()))
        png_path = out_dir / f"frame_{i:04d}.png"
        png_path.write_bytes(base64.b64decode(b64))
        written.append(png_path)
    if missing:
        print(f"  warn: {missing} frames missing from OVRTX response")
    return written


def encode_mp4(png_dir: Path, mp4_path: Path, fps: int) -> None:
    """ffmpeg-encode a directory of frame_NNNN.png → MP4."""
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH; install with `sudo apt install ffmpeg`")
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-framerate", str(fps),
        "-i", str(png_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        str(mp4_path),
    ]
    print(f"ffmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True, type=Path,
                    help="Mocap session directory")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output .mp4 path (or .usda path with --usda-only)")
    ap.add_argument("--duration", type=float, default=25.0,
                    help="Clip duration in seconds (default: 25)")
    ap.add_argument("--target-fps", type=int, default=30,
                    help="Output frame rate (default: 30)")
    ap.add_argument("--orbit-radius", type=float, default=2.0,
                    help="Camera orbit radius in meters (default: 2.0)")
    ap.add_argument("--orbit-height", type=float, default=0.3,
                    help="Camera height above pelvis (default: 0.3)")
    ap.add_argument("--width", type=int, default=800,
                    help="Render width (default: 800)")
    ap.add_argument("--height", type=int, default=450,
                    help="Render height (default: 450)")
    ap.add_argument("--ovrtx-url", default="http://localhost:8001",
                    help="OVRTX rendering API base URL")
    ap.add_argument("--usda-only", action="store_true",
                    help="Only write the USDA, skip OVRTX and ffmpeg")
    ap.add_argument("--keep-usda", action="store_true",
                    help="Keep the intermediate USDA file (written next to the MP4)")
    ap.add_argument("--no-bones", action="store_true",
                    help="Omit bone cylinders (spheres only, smaller USDA)")
    args = ap.parse_args()

    # Step 1: Load session + bake USDA
    print(f"[1/4] Loading session: {args.session.name}")
    session = load_session(args.session)
    print(f"       {session.num_frames} frames @ {session.fps} Hz = "
          f"{session.duration_s:.1f}s (schema {session.schema})")

    if args.usda_only:
        usda_path = args.out.with_suffix(".usda") if args.out.suffix == ".mp4" else args.out
    else:
        usda_path = args.out.with_suffix(".usda")

    print(f"[2/4] Baking USDA: {usda_path}")
    num_frames, fps = bake_usda(
        session, usda_path,
        duration=args.duration,
        target_fps=args.target_fps,
        orbit_radius=args.orbit_radius,
        orbit_height_offset=args.orbit_height,
        with_bones=not args.no_bones,
    )
    end_frame = num_frames - 1

    if args.usda_only:
        print(f"\n--usda-only: done. USDA at {usda_path}")
        return

    # Step 3: Render via OVRTX
    print(f"[3/4] Rendering {num_frames} frames via OVRTX at {args.ovrtx_url}")
    body = render_usda_via_ovrtx(
        usda_path, args.ovrtx_url,
        frames=end_frame,
        width=args.width,
        height=args.height,
    )

    # Decode PNGs to temp dir
    with tempfile.TemporaryDirectory(prefix="dancer_frames_") as tmpdir:
        png_dir = Path(tmpdir)
        pngs = decode_frames_to_pngs(body, end_frame, png_dir)
        print(f"       decoded {len(pngs)} frames to {png_dir}")

        # Step 4: ffmpeg encode
        print(f"[4/4] Encoding MP4: {args.out}")
        encode_mp4(png_dir, args.out, fps)

    if not args.keep_usda and usda_path.exists():
        usda_path.unlink()

    mp4_size = args.out.stat().st_size / 1024
    print(f"\nDone: {args.out} ({mp4_size:.0f} KB)")
    print(f"  {num_frames} frames @ {fps} fps = {num_frames/fps:.1f}s")


if __name__ == "__main__":
    main()
