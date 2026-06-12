#!/usr/bin/env python3
"""
render_drone_demo.py — Phase 1 smoke test of the drone visual-eval pipeline.

What this does, end-to-end:
  1. Bakes a USDA file with:
       - a ground floor plane (visual context)
       - a "drone" prim (small cube placeholder for Phase 1; swap for Crazyflie in Phase 2)
       - time-sampled translate from Point A -> Point B
       - a fixed perspective camera
       - a key light
  2. Base64-encodes the USDA and POSTs to the OVRTX rendering API (port 8001)
       request body matches apps/ovrtx_rendering_api/client/client.py
  3. Decodes the per-frame PNGs from the response
  4. ffmpeg-encodes the PNGs into an MP4

Validates the entire bake -> OVRTX -> MP4 chain BEFORE we waste GPU hours
on PPO training (per Avinash's "static render first, training after" rule).

Usage (on the EC2 host, where ovrtx-rendering-api is on localhost:8001):
  python3 render_drone_demo.py \\
    --out /home/ubuntu/drone_demo.mp4 \\
    --frames 30 --width 640 --height 360 \\
    --point-a -3 1 0 --point-b 3 2 0

The output MP4 can be scp'd off the box, or further converted with
usd_to_glb.py for Quest 3 WebXR viewing.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests


# ---------- USD baking ----------

# Minimal USDA — ONLY the animated Drone Xform. Used for GLB export → Quest VR.
# No floor, no markers, no camera, no lights — those come from the Unity/VR scene.
MINIMAL_USDA_TEMPLATE = """#usda 1.0
(
    defaultPrim = "Drone"
    upAxis = "Y"
    metersPerUnit = 1.0
    startTimeCode = 0
    endTimeCode = {end_frame}
    timeCodesPerSecond = {fps}
    framesPerSecond = {fps}
)

def Xform "Drone" (
    {drone_references}
)
{{
    double3 xformOp:translate.timeSamples = {{
{translate_samples}
    }}
    quatd xformOp:orient.timeSamples = {{
{orient_samples}
    }}
    double3 xformOp:scale = ({drone_scale}, {drone_scale}, {drone_scale})
    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
    {drone_children}
}}
"""

USDA_TEMPLATE = """#usda 1.0
(
    defaultPrim = "World"
    upAxis = "Y"
    metersPerUnit = 1.0
    startTimeCode = 0
    endTimeCode = {end_frame}
    timeCodesPerSecond = {fps}
    framesPerSecond = {fps}
)

def Xform "World"
{{
    def Cube "Floor"
    {{
        double size = 1.0
        color3f[] primvars:displayColor = [(0.25, 0.27, 0.3)]
        double3 xformOp:translate = (0, -0.05, 0)
        double3 xformOp:scale = (12, 0.1, 8)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }}

    def Xform "PointA_Marker"
    {{
        def Cube "Marker"
        {{
            double size = 1.0
            color3f[] primvars:displayColor = [(0.1, 0.8, 0.1)]
            double3 xformOp:scale = (0.3, 0.02, 0.3)
            uniform token[] xformOpOrder = ["xformOp:scale"]
        }}
        double3 xformOp:translate = ({pa_x}, 0, {pa_z})
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}

    def Xform "PointB_Marker"
    {{
        def Cube "Marker"
        {{
            double size = 1.0
            color3f[] primvars:displayColor = [(0.8, 0.1, 0.1)]
            double3 xformOp:scale = (0.3, 0.02, 0.3)
            uniform token[] xformOpOrder = ["xformOp:scale"]
        }}
        double3 xformOp:translate = ({pb_x}, 0, {pb_z})
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}

    def Xform "Drone" (
        {drone_references}
    )
    {{
        double3 xformOp:translate.timeSamples = {{
{translate_samples}
        }}
        quatd xformOp:orient.timeSamples = {{
{orient_samples}
        }}
        double3 xformOp:scale = ({drone_scale}, {drone_scale}, {drone_scale})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
        {drone_children}
    }}

{city_buildings}

    def Camera "Camera"
    {{
        float focalLength = 28
        float horizontalAperture = 36
        float verticalAperture = 24
        float2 clippingRange = (0.1, 1000)
        double3 xformOp:translate = ({cam_x}, {cam_y}, {cam_z})
        double3 xformOp:rotateXYZ = ({cam_rx}, {cam_ry}, 0)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}

    def DistantLight "KeyLight"
    {{
        float inputs:intensity = 4500
        double3 xformOp:rotateXYZ = (-45, 30, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}

    def DistantLight "FillLight"
    {{
        float inputs:intensity = 1500
        double3 xformOp:rotateXYZ = (-25, -120, 0)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }}
}}
"""


def _smoothstep(t: float) -> float:
    """Smooth A->B easing so the drone doesn't look like it teleports linearly."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def load_trajectory_json(path: Path) -> tuple[list[tuple[float, float, float]],
                                              list[tuple[float, float, float, float]],
                                              int]:
    """Load a trajectory JSON produced by export_drone_trajectory.py.

    Isaac Sim's world is **Z-up, right-handed**. Our USDA template is **Y-up**.
    We remap each (x_i, y_i, z_i) -> (x_i, z_i, -y_i) which preserves handedness
    and keeps the drone's "up" direction visually correct (USD Y) and the
    horizontal flight plane (Isaac X-Y) becomes the USD X-Z plane (camera floor).

    For the quaternion: swapping basis vectors changes the rotation too. With
    (q_w, q_x, q_y, q_z)_isaac, the same axis remap produces
    (q_w, q_x, q_z, -q_y)_usd. Phase 2 v1 keeps it simple — the drone is small
    and the camera is far enough away that tiny pitch/roll inaccuracies are
    invisible; we'll tighten in a follow-up.

    Returns (positions, quaternions_usd, fps). Quaternions are (qw, qx, qy, qz).
    """
    data = json.loads(path.read_text())
    fps = int(data.get("fps", 24))
    positions: list[tuple[float, float, float]] = []
    quats: list[tuple[float, float, float, float]] = []
    for f in data["frames"]:
        t = f["t"]
        q = f.get("q", [1.0, 0.0, 0.0, 0.0])
        # Z-up (Isaac) -> Y-up (USD), right-handed:
        positions.append((float(t[0]), float(t[2]), -float(t[1])))
        # quaternion basis swap matching the position remap:
        qw, qx, qy, qz = float(q[0]), float(q[1]), float(q[2]), float(q[3])
        quats.append((qw, qx, qz, -qy))
    return positions, quats, fps


def bake_drone_usda(
    out_path: Path,
    point_a: tuple[float, float, float] | None,
    point_b: tuple[float, float, float] | None,
    frames: int, fps: int,
    drone_asset: str | None = None, drone_scale: float = 5.0,
    trajectory_path: Path | None = None,
    minimal: bool = False,
    identity_rotation: bool = False,
    city_usd: str | None = None,
    camera_override: tuple[float, float, float, float, float] | None = None,
) -> tuple[int, int]:
    """Write a USDA file with a drone moving over `frames` time codes.

    Two modes:
      * `trajectory_path` is given -> read per-frame (t, q) from JSON
      * else hardcoded smoothstep A->B (q is identity rotation)

    Returns (n_frames, fps_used) so the caller can match the OVRTX request.
    """
    translate_lines: list[str] = []
    orient_lines: list[str] = []

    if trajectory_path is not None:
        positions, quats, traj_fps = load_trajectory_json(trajectory_path)
        n = len(positions)
        if n == 0:
            raise SystemExit(f"trajectory at {trajectory_path} has no frames")
        # caller's fps takes precedence if explicitly set, else use trajectory's
        if fps <= 0:
            fps = traj_fps
        # Diagnostic: replace every per-frame quaternion with identity. Isolates
        # whether a WebXR orientation bug originates from the rotation track
        # (drone visibly upright with identity) vs the position remap or the
        # cf2x asset's local frame (drone still tilted with identity).
        if identity_rotation:
            quats = [(1.0, 0.0, 0.0, 0.0)] * n
        # End time code = n - 1 (frames are 0..n-1)
        end_frame = n - 1
        for i, (p, q) in enumerate(zip(positions, quats)):
            translate_lines.append(
                f"            {i}: ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}),"
            )
            orient_lines.append(
                f"            {i}: ({q[0]:.6f}, {q[1]:.6f}, {q[2]:.6f}, {q[3]:.6f}),"
            )
        # Optional: rebase point markers to the trajectory's start/end so they
        # visually correspond to A and B. Useful when caller didn't pass them.
        if point_a is None: point_a = positions[0]
        if point_b is None: point_b = positions[-1]
    else:
        if point_a is None or point_b is None:
            raise SystemExit("must pass either --trajectory or --point-a/--point-b")
        end_frame = frames
        for i in range(frames + 1):
            t = _smoothstep(i / frames) if frames > 0 else 0.0
            x = point_a[0] + (point_b[0] - point_a[0]) * t
            y = point_a[1] + (point_b[1] - point_a[1]) * t
            y_bob = 0.15 * (1 - abs(2 * t - 1))
            z = point_a[2] + (point_b[2] - point_a[2]) * t
            translate_lines.append(f"            {i}: ({x:.4f}, {y + y_bob:.4f}, {z:.4f}),")
            orient_lines.append(f"            {i}: (1.0, 0.0, 0.0, 0.0),")  # identity

    if drone_asset:
        drone_references = f'references = @{drone_asset}@'
        drone_children = ""  # the asset provides geometry
    else:
        drone_references = ""
        # fall back to a colored cube child so we still see something
        drone_children = (
            'def Cube "DroneFallback"\n'
            '        {\n'
            '            double size = 1.0\n'
            '            color3f[] primvars:displayColor = [(0.95, 0.85, 0.1)]\n'
            '            double3 xformOp:scale = (0.25, 0.08, 0.25)\n'
            '            uniform token[] xformOpOrder = ["xformOp:scale"]\n'
            '        }'
        )
        # when no asset, scale should be 1.0 (the cube's own scale handles size)
        drone_scale = 1.0

    if minimal:
        body = MINIMAL_USDA_TEMPLATE.format(
            end_frame=end_frame, fps=fps,
            translate_samples="\n".join(translate_lines),
            orient_samples="\n".join(orient_lines),
            drone_references=drone_references,
            drone_scale=drone_scale,
            drone_children=drone_children,
        )
    else:
        # camera placement: auto-frame based on trajectory bounds so we never
        # render a drone that flew out of the static viewport (the 500-iter
        # trained policy went to X=-1.4 with a fixed (0,3.5,7) camera and the
        # VLM scored a blank scene 8/10 because nothing was visible).
        if camera_override is not None:
            # Caller supplied explicit (cam_x, cam_y, cam_z, cam_rx, cam_ry) —
            # bypass auto-frame entirely. Use this for cinematic wide shots
            # where you want the drone visible *within* the city context.
            cam_x, cam_y, cam_z, cam_rx, cam_ry = camera_override
        elif trajectory_path is not None and translate_lines:
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]   # already remapped to Y-up (Isaac Z)
            zs = [p[2] for p in positions]   # USD Z (depth, -Isaac Y)
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            cz = (min(zs) + max(zs)) / 2
            span = max(max(xs) - min(xs), max(zs) - min(zs), 1.0)
            # camera sits behind +Z, lifted, tilted down 20deg
            cam_z = cz + max(span * 1.4, 6.0)
            cam_y = cy + max(span * 0.7, 3.0)
            cam_x = cx
            cam_rx, cam_ry = -20.0, 0.0
        else:
            cam_x, cam_y, cam_z = 0.0, 3.5, 7.0
            cam_rx, cam_ry = -20.0, 0.0

        # Optional city backdrop. When --city-usd is set we inject a Xform
        # reference into the {city_buildings} placeholder so OVRTX renders
        # the trajectory *inside* the actual scene. Without it the drone
        # renders against a black void (which is why every prior MP4 has
        # been city-less even though the drone trains in Rivermark).
        if city_usd:
            city_block = (
                f'\n    def Xform "City" (\n'
                f'        references = @{city_usd}@\n'
                f'    )\n'
                f'    {{\n'
                f'    }}\n'
            )
        else:
            city_block = ""

        body = USDA_TEMPLATE.format(
            end_frame=end_frame, fps=fps,
            pa_x=point_a[0], pa_z=point_a[2],
            pb_x=point_b[0], pb_z=point_b[2],
            translate_samples="\n".join(translate_lines),
            orient_samples="\n".join(orient_lines),
            drone_references=drone_references,
            drone_scale=drone_scale,
            drone_children=drone_children,
            city_buildings=city_block,
            cam_x=cam_x, cam_y=cam_y, cam_z=cam_z,
            cam_rx=cam_rx, cam_ry=cam_ry,
        )
    out_path.write_text(body)
    return (end_frame + 1, fps)


# ---------- OVRTX call ----------

def render_usda_via_ovrtx(
    usda_path: Path, base_url: str, frames: int, width: int, height: int,
    timeout: float = 600.0,
) -> dict:
    """POST the data-URI'd USDA to /render and return the response body."""
    data_uri = "data:application/octet-stream;base64," + base64.b64encode(
        usda_path.read_bytes()
    ).decode("ascii")
    payload = {
        "url": data_uri,
        "force_render": True,
        "render_settings": {
            "camera_paths": ["/World/Camera"],
            "frame_range": {"start": 0, "end": frames},
            "camera_parameters": {"width": width, "height": height},
            "sensors": None,
            "apply_background_mask": False,
        },
    }
    print(f"POST /render usda={usda_path.stat().st_size} bytes "
          f"frames=0..{frames} size={width}x{height}")
    r = requests.post(
        f"{base_url.rstrip('/')}/render",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") != "success":
        raise SystemExit(f"OVRTX render failed: status={body.get('status')} "
                         f"error={body.get('error')}")
    return body


def decode_frames_to_pngs(body: dict, frames: int, out_dir: Path) -> list[Path]:
    """Walk body['images'][frame][camera][sensor] -> base64 -> write PNG files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    images = body.get("images", {})
    for i in range(frames + 1):
        # OVRTX returns frame keys as strings
        frame_key = str(i)
        if frame_key not in images:
            print(f"  warn: frame {i} missing from response")
            continue
        cam_entries = images[frame_key]
        # take the first (and only) camera result
        cam_path, sensor_map = next(iter(cam_entries.items()))
        # sensor_map looks like {"rgb": "<b64>"} or {"images": "<b64>"} -
        # take whatever's there (single sensor in our request)
        b64 = next(iter(sensor_map.values()))
        png_path = out_dir / f"frame_{i:04d}.png"
        png_path.write_bytes(base64.b64decode(b64))
        written.append(png_path)
    return written


# ---------- ffmpeg encode ----------

def encode_mp4(png_dir: Path, mp4_path: Path, fps: int) -> None:
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
    print(f"encode: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="/home/ubuntu/drone_demo.mp4")
    ap.add_argument("--frames", type=int, default=30,
                    help="frame count (0..N); ignored when --trajectory is set")
    ap.add_argument("--fps", type=int, default=24,
                    help="fps; with --trajectory, pass 0 to inherit from JSON")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=360)
    ap.add_argument("--point-a", type=float, nargs=3, default=[-3.0, 1.0, 0.0],
                    metavar=("X", "Y", "Z"),
                    help="ignored when --trajectory is set")
    ap.add_argument("--point-b", type=float, nargs=3, default=[3.0, 2.0, 0.0],
                    metavar=("X", "Y", "Z"),
                    help="ignored when --trajectory is set")
    ap.add_argument("--trajectory", default=None,
                    help="JSON trajectory from export_drone_trajectory.py "
                         "(per-frame world-space position + quaternion). "
                         "When set, --frames/--point-a/--point-b are ignored.")
    ap.add_argument("--skip-render", action="store_true",
                    help="bake the USDA only; skip OVRTX call + ffmpeg encode "
                         "(useful when the next step is usd_to_glb.py instead)")
    ap.add_argument("--minimal-usda", action="store_true",
                    help="emit a minimal USDA with ONLY the animated Drone Xform "
                         "(no floor / camera / lights / markers). Use this for the GLB "
                         "export path; the Unity / Quest scene already provides lighting "
                         "+ environment.")
    ap.add_argument("--identity-rotation", action="store_true",
                    help="diagnostic: force xformOp:orient = (1,0,0,0) every frame. "
                         "Trajectory positions still apply. Use to isolate whether a "
                         "WebXR orientation issue is in the rotation track or elsewhere.")
    ap.add_argument("--city-usd", default=None,
                    help="USD path (resolvable inside the OVRTX container, so under "
                         "/host_tmp/...) referenced as /World/City to give the drone "
                         "an actual environment to fly through. Without this the render "
                         "is drone-against-black-void.")
    ap.add_argument("--camera-pos", type=float, nargs=5, default=None,
                    metavar=("X", "Y", "Z", "RX", "RY"),
                    help="Override auto-frame with an explicit camera transform "
                         "(translate XYZ + rotateX/Y in degrees). Use this for "
                         "cinematic wide shots that include the city.")
    ap.add_argument("--evaluate", action="store_true",
                    help="after rendering, call evaluate_drone_trajectory.py to have "
                         "the LiteLLM-proxied gpt-4o-mini grade the flight and write "
                         "<out>.evaluation.json next to the MP4. Only meaningful with "
                         "a real render (not with --skip-render).")
    ap.add_argument("--evaluator-script", default=None,
                    help="path to evaluate_drone_trajectory.py "
                         "(defaults to sibling of this script)")
    ap.add_argument("--base-url", default="http://localhost:8001")
    ap.add_argument("--drone-asset", default=None,
                    help="USD path the Drone Xform references "
                         "(e.g. /host_tmp/cf2x.usd inside the OVRTX container). "
                         "If unset, a yellow placeholder cube is used.")
    ap.add_argument("--drone-scale", type=float, default=5.0,
                    help="uniform scale applied to drone asset (default 5x to make "
                         "the 10cm Crazyflie visible at the chosen camera distance)")
    ap.add_argument("--keep-usda", action="store_true",
                    help="keep the baked USDA next to the MP4 for inspection")
    args = ap.parse_args()

    out_mp4 = Path(args.out).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        usda_path = tmp_dir / "drone_demo.usda"
        png_dir = tmp_dir / "frames"

        print(f"[1/4] baking USDA -> {usda_path}")
        traj_path = Path(args.trajectory) if args.trajectory else None
        n_frames, fps_used = bake_drone_usda(
            usda_path,
            tuple(args.point_a) if args.point_a else None,
            tuple(args.point_b) if args.point_b else None,
            args.frames, args.fps,
            drone_asset=args.drone_asset,
            drone_scale=args.drone_scale,
            trajectory_path=traj_path,
            minimal=args.minimal_usda,
            identity_rotation=args.identity_rotation,
            city_usd=args.city_usd,
            camera_override=tuple(args.camera_pos) if args.camera_pos else None,
        )
        print(f"      {usda_path.stat().st_size} bytes, {n_frames} frames @ {fps_used} fps")

        if args.keep_usda or args.skip_render:
            shutil.copy(usda_path, out_mp4.with_suffix(".usda"))
            print(f"      kept USDA at {out_mp4.with_suffix('.usda')}")

        if args.skip_render:
            print("[done] --skip-render set; USDA only")
            return

        print(f"[2/4] rendering via OVRTX at {args.base_url}")
        body = render_usda_via_ovrtx(
            usda_path, args.base_url,
            n_frames - 1, args.width, args.height,
        )

        print(f"[3/4] decoding {n_frames} frame PNGs -> {png_dir}")
        pngs = decode_frames_to_pngs(body, n_frames - 1, png_dir)
        print(f"      {len(pngs)} PNGs written")
        if not pngs:
            raise SystemExit("no frames decoded; aborting")

        print(f"[4/4] ffmpeg -> {out_mp4}")
        encode_mp4(png_dir, out_mp4, fps_used)

        if args.evaluate:
            evaluator = Path(args.evaluator_script) if args.evaluator_script else (
                Path(__file__).resolve().parent / "evaluate_drone_trajectory.py"
            )
            if not evaluator.exists():
                print(f"[evaluate] script not found at {evaluator}; skipping eval")
            else:
                eval_out = out_mp4.with_suffix(".evaluation.json")
                grid_out = out_mp4.with_suffix(".evaluation_grid.jpg")
                print(f"[evaluate] {evaluator.name} -> {eval_out.name}")
                cmd = [
                    sys.executable, str(evaluator),
                    "--mp4", str(out_mp4),
                    "--out", str(eval_out),
                    "--save-grid", str(grid_out),
                ]
                # don't abort the whole render if eval fails — the MP4 is still useful
                subprocess.run(cmd, check=False)

    print(f"✓ done: {out_mp4} ({out_mp4.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
