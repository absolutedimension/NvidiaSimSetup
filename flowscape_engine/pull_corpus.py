#!/usr/bin/env python3
"""
Part 0 — GATHER (analysis-only corpus).

yt-dlp a channel/playlist/video-list into corpus/ so the VLM can read the STYLE.
Mirror of dj_engine/fs_pull*.py + the yt-dlp corpus step in DJ_ENGINE.md.

COPYRIGHT STANCE (non-negotiable, same as dj_engine):
  These videos are TEACHERS, never source. They are read ONCE by the VLM grammar
  extractor to learn the recipe, then can be deleted. They are NEVER copied into
  seeds_clean/ and NEVER fed to train_lora.py. Nothing from a downloaded frame
  ends up in an output video.

Usage:
  python3 pull_corpus.py --channel https://www.youtube.com/@CleverSpacesGirl --max 12
  python3 pull_corpus.py --urls url1 url2 ...

Note: YouTube bot-blocks datacenter IPs ("confirm you're not a bot"). Same fix as
dj_engine: pass --cookies cookies.txt (exported from a logged-in browser) or run
from a residential IP, then rsync the corpus to EC2.
"""
import argparse, os, subprocess, sys
import config as C


def run(cmd):
    print("+", " ".join(cmd)); subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", help="channel/playlist URL")
    ap.add_argument("--urls", nargs="*", default=[], help="explicit video URLs")
    ap.add_argument("--max", type=int, default=10, help="max videos from a channel")
    ap.add_argument("--cookies", help="cookies.txt to beat the bot-block")
    ap.add_argument("--height", type=int, default=720, help="cap resolution (analysis only)")
    args = ap.parse_args()

    if not args.channel and not args.urls:
        sys.exit("give --channel or --urls")

    base = [
        "yt-dlp",
        "-f", f"bv*[height<={args.height}]+ba/b[height<={args.height}]",
        "-o", os.path.join(C.CORPUS, "%(id)s.%(ext)s"),
        "--merge-output-format", "mp4",
        "--no-playlist-reverse",
    ]
    if args.cookies:
        base += ["--cookies", args.cookies]

    if args.channel:
        run(base + ["--playlist-end", str(args.max), args.channel])
    for u in args.urls:
        run(base + ["--no-playlist", u])

    got = [f for f in os.listdir(C.CORPUS) if f.endswith(".mp4")]
    print(f"\ncorpus: {len(got)} videos in {C.CORPUS}")
    print("NEXT: python3 extract_keyframes.py")


if __name__ == "__main__":
    main()
