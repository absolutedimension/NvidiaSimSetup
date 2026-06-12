#!/usr/bin/env python3
"""Driver: render Episode 2 via the Manim engine (all motion-graphics over reactive shader)."""
import os, sys, glob, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

HOME="/home/ubuntu"; BUILD=f"{HOME}/youtube_series/ep02_build"
WORK=f"{HOME}/youtube_series/ep02_manim_build"; os.makedirs(WORK, exist_ok=True)
OUT=f"{HOME}/youtube_series/ep02_learning_manim.mp4"
W,H,FPS=1920,1080,30

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

arg=sys.argv[1] if len(sys.argv)>1 else "all"
todo=list(range(1,14)) if arg=="all" else [int(x) for x in arg.split(",")]

for i in todo:
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio)
    print(f">> {sc}: {D:.1f}s — manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,"ep02_manim.py",sc], cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/ep02_manim/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov {sc}\n{r.stderr[-1500:]}", flush=True); continue
    mov=movs[0]; bg=os.path.join(WORK,f"{sc}_bg.mp4"); clip=os.path.join(WORK,f"{sc}.mp4")
    render_shader_video(shader_name="circuit_mind",audio_path=audio,output_path=bg,duration=D,fps=FPS,width=W,height=H)
    cp=subprocess.run(["ffmpeg","-y","-i",bg,"-i",mov,"-i",audio,
        "-filter_complex","[1:v]scale=1920:1080[mg];[0:v][mg]overlay=0:0:format=auto[v]",
        "-map","[v]","-map","2:a","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-shortest",clip], capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1200:]}", flush=True); continue
    print(f"   {sc} clip done", flush=True)

clips=sorted(glob.glob(f"{WORK}/S??.mp4"))
if len(clips)==13:
    lst=os.path.join(WORK,"concat.txt"); open(lst,"w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
    print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)", flush=True)
else:
    print(f"\n(have {len(clips)}/13 clips)", flush=True)
