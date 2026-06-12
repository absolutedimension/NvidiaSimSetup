"""
evaluate_drone_trajectory.py — Have a vision-language model (gpt-4o-mini via
LiteLLM proxy) grade a rendered drone-policy MP4 and return a structured JSON
verdict.

This is the post-training critic from Approach A:

    train.py ─► .pth ─► export_drone_trajectory.py ─► render_drone_demo.py ─► .mp4
                                                                              │
                                                                              ▼
                                                            evaluate_drone_trajectory.py
                                                                              │
                                                                              ▼
                                                            JSON  {"overall": 7,
                                                                   "verdict": "ship-it",
                                                                   ...}

Reuses the existing LiteLLM proxy on TrigunAI-Omniverse:
  - endpoint  http://localhost:4000/v1/chat/completions
  - master key sk-trigunai-master-key-2026
  - model     gpt-4o-mini (Azure-backed, vision-capable)

Cost: ~$0.0001 / call. Latency: 3-8 sec. Output: structured JSON.

Usage (on the EC2 host, where the proxy + ffmpeg + python3 are all available):

  python3 evaluate_drone_trajectory.py \\
    --mp4 /home/ubuntu/drone_trained.mp4 \\
    --out /home/ubuntu/drone_evaluation.json

  # Or feed a directory of pre-extracted PNG frames instead of an MP4:
  python3 evaluate_drone_trajectory.py \\
    --frames-dir /tmp/v4_frames \\
    --out /home/ubuntu/drone_evaluation.json

Exit code is 0 on success regardless of verdict; the verdict lives in the JSON
file so callers (e.g. an auto-train loop) can read it and decide.

Wire it into render_drone_demo.py via `--evaluate` to run it automatically
after each render. Or run standalone as above.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

try:
    from PIL import Image
except ImportError:
    print("[vlm] Pillow (PIL) is required: pip install pillow", file=sys.stderr)
    sys.exit(2)


# ---------- keyframe extraction ----------

def extract_keyframes_from_mp4(mp4_path: Path, n_frames: int, out_dir: Path) -> list[Path]:
    """Use ffmpeg to extract n_frames evenly-spaced keyframes from the mp4."""
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH; install with `sudo apt install ffmpeg`")
    out_dir.mkdir(parents=True, exist_ok=True)
    # ffmpeg select expr: pick frames at  0, total/(n-1), 2*total/(n-1), ..., total
    # We don't know total frames a priori. Use the simpler "thumbnail every N seconds" form
    # by querying duration first.
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(mp4_path)],
        capture_output=True, text=True, check=True,
    )
    duration = float(probe.stdout.strip() or "0")
    if duration <= 0:
        raise SystemExit(f"could not read duration of {mp4_path}")
    paths: list[Path] = []
    for i in range(n_frames):
        # spread N points across the clip; first at t=0, last at t=duration-tiny
        t = (duration * i / max(1, n_frames - 1)) if n_frames > 1 else 0.0
        # nudge the last frame back a hair so we don't ask for a frame past EOF
        if i == n_frames - 1:
            t = max(0.0, duration - 0.05)
        out = out_dir / f"keyframe_{i:02d}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-ss", f"{t:.3f}", "-i", str(mp4_path),
             "-frames:v", "1", str(out)],
            check=True,
        )
        paths.append(out)
    return paths


def collect_keyframes_from_dir(frames_dir: Path, n_frames: int) -> list[Path]:
    """Pick n_frames evenly spaced from an existing dir of frame_XXXX.png files."""
    pngs = sorted(frames_dir.glob("*.png"))
    if not pngs:
        raise SystemExit(f"no PNGs in {frames_dir}")
    if len(pngs) <= n_frames:
        return pngs
    idxs = [round((len(pngs) - 1) * i / (n_frames - 1)) for i in range(n_frames)]
    return [pngs[i] for i in idxs]


# ---------- grid composite ----------

def stitch_grid(image_paths: list[Path], cols: int = 3, tile_w: int = 512) -> Image.Image:
    """2x3 (or rows x cols) grid of keyframes, each tile resized to tile_w.

    A single composite image is cheaper than N separate image messages (one
    encode + smaller total bytes) and the VLM reads the time-order better when
    it sees them side-by-side."""
    if not image_paths:
        raise SystemExit("no keyframes to stitch")
    tiles = []
    for p in image_paths:
        im = Image.open(p).convert("RGB")
        w_ratio = tile_w / im.width
        new_h = max(1, int(im.height * w_ratio))
        tiles.append(im.resize((tile_w, new_h)))
    rows = (len(tiles) + cols - 1) // cols
    tile_h = tiles[0].height
    grid = Image.new("RGB", (cols * tile_w, rows * tile_h), color=(0, 0, 0))
    for i, t in enumerate(tiles):
        r = i // cols
        c = i % cols
        grid.paste(t, (c * tile_w, r * tile_h))
    return grid


def grid_to_data_uri(grid: Image.Image, fmt: str = "JPEG", quality: int = 85) -> str:
    """Encode the grid as base64 data URI suitable for an OpenAI vision message."""
    buf = io.BytesIO()
    # JPEG is much smaller than PNG for photographic content; gpt-4o-mini handles both
    grid.save(buf, format=fmt, quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    mime = {"JPEG": "image/jpeg", "PNG": "image/png"}[fmt]
    return f"data:{mime};base64,{b64}"


# ---------- VLM call via LiteLLM proxy ----------

DEFAULT_SYSTEM_PROMPT = """You are an expert reviewer evaluating a simulated NVIDIA \
Crazyflie 2.X quadcopter trained with PPO in Isaac Sim. The drone (small grey \
quadcopter, 4 visible rotors) was trained on the task "Isaac-Quadcopter-Direct-v0": \
hover near a randomized goal position for ~7.5 seconds.

You will see a composite image: 6 keyframes from the same flight in time order \
(top-left, top-mid, top-right, bot-left, bot-mid, bot-right). The drone appears \
small; the green flat marker is Point A (spawn) and the red flat marker is \
Point B (goal). The flight is a 30-fps render of a trained policy's rollout.

**CRITICAL: First, confirm the drone is actually visible in the frames.** If you
cannot see a small grey quadcopter in any of the keyframes — only the floor + the
A/B markers — then the policy flew the drone out of the camera's framing OR
crashed below the floor. In that case set every dimension to 1, list "drone not
visible in any keyframe" as the first issue, and set verdict = "broken". Do NOT
hallucinate a drone you cannot see.

Otherwise, grade the flight on four dimensions, score 1 (worst) to 10 (best):

  reach        - did the drone stay close to / reach Point B?
  smoothness   - did it move smoothly with no jerk / oscillation?
  stability    - did the drone remain upright (no flipping, no extreme tilt)?
  efficiency   - direct motion to/around the goal, not wandering or stalling?

Then give a verdict:
  "ship-it"            - good policy, ready to deliver to the VR app
  "needs-more-training"- mostly working but unrefined; train more iterations
  "broken"             - serious failure (crash, didn't move, wrong direction, or
                         invisible drone — see the rule at the top)

Respond ONLY with a single JSON object, no prose, no markdown fences:
{
  "reach": int 1..10,
  "smoothness": int 1..10,
  "stability": int 1..10,
  "efficiency": int 1..10,
  "overall": int 1..10,
  "issues": ["short bullet 1", "short bullet 2", ...],
  "verdict": "ship-it" | "needs-more-training" | "broken"
}
"""


def call_vlm(
    grid_data_uri: str,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    timeout: float = 60.0,
) -> dict:
    """POST to LiteLLM's OpenAI-compatible /v1/chat/completions with a vision message."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Grade this flight using the schema above. JSON only."},
                    {"type": "image_url", "image_url": {"url": grid_data_uri}},
                ],
            },
        ],
        "temperature": 0.2,         # we want deterministic critique, not creative
        "max_tokens": 400,
        "response_format": {"type": "json_object"},   # LiteLLM passes this through
    }
    r = requests.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=timeout,
    )
    r.raise_for_status()
    body = r.json()
    msg = body["choices"][0]["message"]["content"]

    # gpt-4o-mini sometimes wraps JSON in ```json``` fences despite response_format
    msg = msg.strip()
    fence = re.match(r"^```(?:json)?\s*(.+?)\s*```$", msg, re.DOTALL)
    if fence:
        msg = fence.group(1).strip()

    try:
        verdict = json.loads(msg)
    except json.JSONDecodeError as e:
        raise SystemExit(f"VLM did not return valid JSON:\n{msg}\n\n({e})")
    return verdict


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--mp4", type=Path, help="rendered MP4 to evaluate")
    src.add_argument("--frames-dir", type=Path,
                     help="directory of frame_XXXX.png files (skip ffmpeg extract)")
    ap.add_argument("--out", type=Path, default=Path("/home/ubuntu/drone_evaluation.json"),
                    help="path to write the JSON verdict")
    ap.add_argument("--n-frames", type=int, default=6,
                    help="number of keyframes to extract / use (2x3 grid by default)")
    ap.add_argument("--cols", type=int, default=3,
                    help="grid columns")
    ap.add_argument("--tile-w", type=int, default=512,
                    help="per-tile width in pixels in the composite (height scaled)")
    ap.add_argument("--base-url", default="http://localhost:4000",
                    help="LiteLLM proxy base URL")
    ap.add_argument("--api-key", default=os.environ.get("LITELLM_MASTER_KEY",
                                                       "sk-trigunai-master-key-2026"))
    ap.add_argument("--model", default="gpt-4o-mini",
                    help="model alias as registered in the LiteLLM config")
    ap.add_argument("--save-grid", type=Path, default=None,
                    help="(debug) save the composite grid here as a PNG/JPEG")
    args = ap.parse_args()

    # 1. collect keyframes
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        if args.mp4:
            print(f"[vlm] extracting {args.n_frames} keyframes from {args.mp4.name}")
            frames = extract_keyframes_from_mp4(args.mp4, args.n_frames, tmp_dir)
        else:
            frames = collect_keyframes_from_dir(args.frames_dir, args.n_frames)
            print(f"[vlm] using {len(frames)} frames from {args.frames_dir}")

        # 2. stitch grid
        grid = stitch_grid(frames, cols=args.cols, tile_w=args.tile_w)
        grid_uri = grid_to_data_uri(grid, fmt="JPEG", quality=85)
        size_kb = len(grid_uri) * 3 / 4 / 1024
        print(f"[vlm] composite grid: {grid.size[0]}x{grid.size[1]}, ~{size_kb:.0f} KB encoded")

        if args.save_grid:
            grid.save(args.save_grid)
            print(f"[vlm] saved composite to {args.save_grid}")

        # 3. call VLM
        print(f"[vlm] POST {args.base_url}/v1/chat/completions  model={args.model}")
        verdict = call_vlm(
            grid_uri,
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )

    # 4. write
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2))

    # 5. one-line summary
    def g(k, d="?"):
        return verdict.get(k, d)
    print(
        f"[vlm] reach={g('reach')} smooth={g('smoothness')} "
        f"stab={g('stability')} eff={g('efficiency')} overall={g('overall')} "
        f"verdict={g('verdict')}"
    )
    issues = verdict.get("issues") or []
    if issues:
        print("[vlm] issues:")
        for s in issues:
            print(f"        - {s}")
    print(f"[vlm] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
