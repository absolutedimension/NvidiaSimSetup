#!/usr/bin/env python3
"""Concat the 8 chapter videos into the 1-hour film + print YouTube chapter timestamps."""
import os, subprocess, json
VID=os.path.expanduser("~/dj_engine/series_video")
CH=["ch01","ch02","ch03","ch04","ch05","ch06","ch07","ch08"]
NAMES=["I  ·  Attention","II  ·  Learning","III  ·  Imagination","IV  ·  Meaning",
       "V  ·  Intuition","VI  ·  Will","VII  ·  Getting Better","VIII  ·  Flow  ·  Beyond the Mind"]
import librosa
# concat list
with open(f"{VID}/concat.txt","w") as f:
    for c in CH: f.write(f"file '{VID}/{c}.mp4'\n")
out=f"{VID}/AI_UNIVERSAL_MIND_1HR.mp4"
r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",f"{VID}/concat.txt","-c","copy",out],
                 capture_output=True,text=True)
if r.returncode!=0:  # fallback: re-encode concat
    print("copy-concat failed, re-encoding...")
    inputs=[];
    for c in CH: inputs+=["-i",f"{VID}/{c}.mp4"]
    n=len(CH)
    filt="".join(f"[{i}:v][{i}:a]" for i in range(n))+f"concat=n={n}:v=1:a=1[v][a]"
    r=subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",filt,"-map","[v]","-map","[a]",
        "-c:v","h264_nvenc","-cq","22","-c:a","aac","-b:a","256k",out],capture_output=True,text=True)
    print("reencode rc",r.returncode, r.stderr[-400:] if r.returncode else "")
# timestamps
t=0.0; print("\n=== YOUTUBE CHAPTERS ===")
for c,nm in zip(CH,NAMES):
    m,s=divmod(int(t),60); print(f"{m:02d}:{s:02d} {nm}")
    t+=librosa.get_duration(path=f"{VID}/{c}.mp4")
tot=int(t); print(f"TOTAL {tot//60}:{tot%60:02d}")
print("OUT",out, round(os.path.getsize(out)/1e6,1),"MB")
