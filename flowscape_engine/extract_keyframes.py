#!/usr/bin/env python3
"""
Part A.0 — sample keyframes from each corpus video for the VLM.

ffmpeg pulls N evenly-spaced stills per video (default 1 every 20 s). These are
transient analysis crops, not training data. Mirror of the ffmpeg keyframe-grid
step in the drone VLM critic (CLAUDE.md §17.9).

Usage: python3 extract_keyframes.py --every 20
"""
import argparse, glob, os, subprocess
import config as C


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", path],
        capture_output=True, text=True).stdout.strip()
    try:    return float(out)
    except: return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=20, help="seconds between stills")
    ap.add_argument("--max-per-video", type=int, default=40)
    args = ap.parse_args()

    vids = sorted(glob.glob(os.path.join(C.CORPUS, "*.mp4")))
    if not vids:
        print("no videos in corpus/. run pull_corpus.py first."); return

    total = 0
    for v in vids:
        vid = os.path.splitext(os.path.basename(v))[0]
        outdir = os.path.join(C.KEYFRAMES, vid); os.makedirs(outdir, exist_ok=True)
        dur = duration(v)
        n = min(args.max_per_video, max(1, int(dur // args.every))) if dur else args.max_per_video
        # fps filter: one frame every `every` seconds
        subprocess.run([
            "ffmpeg", "-y", "-i", v,
            "-vf", f"fps=1/{args.every},scale=768:-1",
            "-frames:v", str(n),
            os.path.join(outdir, "kf_%03d.jpg"),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        got = len(glob.glob(os.path.join(outdir, "*.jpg")))
        total += got
        print(f"{vid}: {got} keyframes")

    print(f"\ntotal {total} keyframes in {C.KEYFRAMES}")
    print("NEXT: python3 visual_grammar_extract.py")


if __name__ == "__main__":
    main()
