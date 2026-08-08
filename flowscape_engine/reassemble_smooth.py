#!/usr/bin/env python3
"""
Smooth assembler — fixes the two smoothness bugs in the first render:
  1. loop-snap ("boomerang"): DON'T stream-loop a 1s clip to fill a 20s hold.
     Instead do a slow, continuous Ken-Burns zoom/pan on the still (perfectly
     smooth, fills any duration).
  2. hard cuts between scenes: xfade crossfade dissolves, not concat cuts.

Reuses the already-rendered shots (extracts a still from each) so no GPU re-run.

Usage:
  python3 reassemble_smooth.py --shots output/flowscape_3min \
      --hold 20 --crossfade 2 --audio /home/ubuntu/cosmic-hypnotic.mp3 \
      --out output/flowscape_3min_smooth.mp4
"""
import argparse, glob, os, subprocess, sys
import config as C

W, H, FPS = C.UPSCALE_TO, int(C.UPSCALE_TO * 9 / 16), 30  # 1920x1080@30


def still_from(clip, out_png):
    subprocess.run(["ffmpeg", "-y", "-i", clip, "-frames:v", "1", out_png],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ken_burns(still, hold, out_mp4, direction):
    """slow continuous zoom (in or out) — motion-smooth, no loop, no snap."""
    d = int(hold * FPS)
    if direction == "in":
        z = "min(zoom+0.00035,1.25)"
    else:  # start zoomed, ease out
        z = "if(eq(on,0),1.25,max(zoom-0.00035,1.0))"
    # scale up first so zoompan has pixels to work with (no jitter), then pan center
    vf = (f"scale=3840:-1,zoompan=z='{z}':d={d}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", still, "-t", str(hold),
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def xfade_chain(clips, hold, xf, out_mp4):
    """dissolve-crossfade all equal-length clips into one smooth stream."""
    n = len(clips)
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    if n == 1:
        subprocess.run(["ffmpeg", "-y"] + inputs + ["-c", "copy", out_mp4], check=True)
        return
    fc, last = [], "0:v"
    for i in range(1, n):
        off = i * (hold - xf)
        lbl = f"v{i}"
        src = f"[{last}]" if i == 1 else f"[{last}]"
        fc.append(f"{src}[{i}:v]xfade=transition=fade:duration={xf}:offset={off}[{lbl}]")
        last = lbl
    filt = ";".join(fc)
    subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", filt, "-map", f"[{last}]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True, help="dir with shot_*_raw.mp4 (or *.png stills)")
    ap.add_argument("--hold", type=float, default=20)
    ap.add_argument("--crossfade", type=float, default=2)
    ap.add_argument("--audio")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raws = sorted(glob.glob(os.path.join(args.shots, "shot_*_raw.mp4")))
    if not raws:
        sys.exit(f"no shot_*_raw.mp4 in {args.shots}")
    work = os.path.join(args.shots, "_smooth"); os.makedirs(work, exist_ok=True)

    held = []
    for i, raw in enumerate(raws):
        still = os.path.join(work, f"still_{i:03d}.png")
        still_from(raw, still)
        seg = os.path.join(work, f"kb_{i:03d}.mp4")
        ken_burns(still, args.hold, seg, "in" if i % 2 == 0 else "out")
        held.append(seg)
        print(f"  ken-burns shot {i+1}/{len(raws)}")

    silent = os.path.join(work, "silent.mp4")
    xfade_chain(held, args.hold, args.crossfade, silent)
    print("  crossfaded")

    cmd = ["ffmpeg", "-y", "-i", silent]
    if args.audio:
        cmd += ["-stream_loop", "-1", "-i", args.audio, "-shortest",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c", "copy"]
    cmd += [args.out]
    subprocess.run(cmd, check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", args.out], capture_output=True, text=True).stdout.strip()
    print(f"\nSMOOTH -> {args.out}  ({dur}s)")


if __name__ == "__main__":
    main()
