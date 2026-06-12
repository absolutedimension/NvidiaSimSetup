#!/usr/bin/env python3
"""Full HINDI Episode 1: Hindi Manim scenes (boomerang bg) -> Hindi captions -> concat."""
import subprocess, os
HOME="/home/ubuntu"; B=f"{HOME}/youtube_series/ep01_manim_hi_build"; BUILD=f"{HOME}/youtube_series/ep01_hi_build"
OUT=f"{HOME}/youtube_series/ep01_hi_FINAL.mp4"

print("== STEP 1: render Hindi scenes (boomerang bg) ==",flush=True)
subprocess.run(["python3","render_ep01_manim_hi.py"],cwd=HOME)

print("== STEP 2: Hindi kinetic captions per scene ==",flush=True)
caps=[]
for i in range(1,11):
    s=f"{i:02d}"; out=f"{B}/cap_S{s}.mp4"
    r=subprocess.run(["python3","make_caps_fx_hi.py",f"{BUILD}/s{s}.mp3",f"{B}/S{s}.mp4",out],cwd=HOME,capture_output=True,text=True)
    if not os.path.exists(out):
        print(f"  !! caption fail s{s}: {r.stdout[-300:]} {r.stderr[-400:]}",flush=True)
        out=f"{B}/S{s}.mp4"
    print(f"  scene {s} done",flush=True); caps.append(out)

print("== STEP 3: concat (re-encode, clean timestamps) ==",flush=True)
inp=[]; fc=""
for i,c in enumerate(caps): inp+=["-i",c]; fc+=f"[{i}:v][{i}:a]"
fc+="concat=n=10:v=1:a=1[v][a]"
subprocess.run(["ffmpeg","-y",*inp,"-filter_complex",fc,"-map","[v]","-map","[a]",
    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k",OUT],capture_output=True)
d=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",OUT],capture_output=True,text=True).stdout.strip()
print(f"\n✅ HI_BUILD_DONE: {OUT} ({d}s)",flush=True)
