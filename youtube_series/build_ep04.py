#!/usr/bin/env python3
"""Full EN Episode 3: Mode-C scenes (boomerang bg) -> kinetic captions -> concat -> focus bed."""
import subprocess, os
HOME="/home/ubuntu"; B=f"{HOME}/youtube_series/ep04_manim_build"; BUILD=f"{HOME}/youtube_series/ep04_build"
OUT=f"{HOME}/youtube_series/ep04_FINAL.mp4"; N=12

print("== STEP 1: render scenes (boomerang bg) ==",flush=True)
subprocess.run(["python3","render_ep04_manim.py"],cwd=HOME)

print("== STEP 2: kinetic captions per scene ==",flush=True)
caps=[]
for i in range(1,N+1):
    s=f"{i:02d}"; out=f"{B}/cap_S{s}.mp4"
    r=subprocess.run(["python3","make_caps_fx.py",f"{BUILD}/s{s}.mp3",f"{B}/S{s}.mp4",out],cwd=HOME,capture_output=True,text=True)
    if not os.path.exists(out):
        print(f"  !! caption fail s{s}: {r.stdout[-200:]} {r.stderr[-300:]}",flush=True); out=f"{B}/S{s}.mp4"
    print(f"  scene {s} done",flush=True); caps.append(out)

print("== STEP 3: concat (re-encode) ==",flush=True)
inp=[]; fc=""
for i,c in enumerate(caps): inp+=["-i",c]; fc+=f"[{i}:v][{i}:a]"
fc+=f"concat=n={N}:v=1:a=1[v][a]"
subprocess.run(["ffmpeg","-y",*inp,"-filter_complex",fc,"-map","[v]","-map","[a]",
    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k",OUT],capture_output=True)
d=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",OUT],capture_output=True,text=True).stdout.strip()
print(f"  concat -> {OUT} ({d}s)",flush=True)

print("== STEP 4: focus bed ==",flush=True)
subprocess.run(["python3","focus_audio.py","--dur",str(int(float(d))),"--beat","12","--out","/tmp/bed_ep04_en.wav"],cwd=HOME)
FOC=f"{HOME}/youtube_series/ep04_FINAL_focus.mp4"
subprocess.run(["python3","focus_mix.py",OUT,"/tmp/bed_ep04_en.wav",FOC],cwd=HOME)
print(f"\n✅ EP03_EN_DONE: {FOC}",flush=True)
