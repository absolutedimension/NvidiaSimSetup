#!/usr/bin/env python3
"""Outro: the spinning TrigunAI logo (1080x1080) presented 16:9 via a blurred-self fill.
Clean, no washout, no black bars — the logo on its own polished dark look."""
import os, subprocess

SPIN="/home/ubuntu/youtube_series/assets/trigun_spin_1080.mp4"
OUT="/home/ubuntu/youtube_series/clips/outro.mp4"
DUR="5"
os.makedirs(os.path.dirname(OUT),exist_ok=True)

fc=("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "boxblur=26:4,eq=brightness=-0.16:saturation=0.85[bg];"
    "[0:v]scale=-1:1080[fg];"
    "[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]")
cmd=["ffmpeg","-y","-i",SPIN,"-f","lavfi","-t",DUR,"-i","anullsrc=r=44100:cl=stereo",
     "-filter_complex",fc,"-map","[v]","-map","1:a","-t",DUR,
     "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",OUT]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode!=0: print("FFMPEG ERR:\n",r.stderr[-1500:]); raise SystemExit(1)
print(f"✅ outro: {OUT}")
