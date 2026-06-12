#!/usr/bin/env python3
"""
Driver: render Episode 1 via the Manim engine.
Per scene: Manim transparent .mov (timed to frozen audio) → composite over reactive
circuit_mind shader bg + audio → clip → concat. Output ep01_manim_v3.mp4.
Usage: python3 render_ep01_manim.py [single_scene_index]   # e.g. 1 to render only S01
"""
import os, sys, glob, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

HOME="/home/ubuntu"
BUILD=f"{HOME}/youtube_series/ep01_build"
WORK=f"{HOME}/youtube_series/ep01_manim_build"; os.makedirs(WORK, exist_ok=True)
OUT=f"{HOME}/youtube_series/ep01_manim_v3.mp4"
W,H,FPS=1920,1080,30

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                     capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

only = int(sys.argv[1]) if len(sys.argv)>1 else None
clips=[]
for i in range(1,11):
    if only and i!=only: continue
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio)
    print(f">> {sc}: {D:.1f}s — rendering manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,"ep01_manim.py",sc],
                     cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/ep01_manim/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov for {sc}\n{r.stderr[-1500:]}", flush=True); continue
    mov=movs[0]
    print(f"   manim ok -> {mov}; shader bg", flush=True)
    bg=os.path.join(WORK,f"{sc}_bg.mp4")
    render_shader_video(shader_name="circuit_mind",audio_path=audio,output_path=bg,duration=D,fps=FPS,width=W,height=H)
    clip=os.path.join(WORK,f"{sc}.mp4")
    cp=subprocess.run(["ffmpeg","-y","-i",bg,"-i",mov,"-i",audio,
        "-filter_complex","[1:v]scale=1920:1080[mg];[0:v][mg]overlay=0:0:format=auto[v]",
        "-map","[v]","-map","2:a","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-shortest",clip], capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1200:]}", flush=True); continue
    clips.append(clip); print(f"   {sc} clip done", flush=True)

if only:
    print(f"\n✅ single scene done: {clips}", flush=True); sys.exit(0)

lst=os.path.join(WORK,"concat.txt")
open(lst,"w").write("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)", flush=True)
