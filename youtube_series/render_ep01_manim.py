#!/usr/bin/env python3
"""
Driver: render Episode 1 via the Manim engine.
Per scene: Manim transparent .mov (timed to frozen audio) → composite → clip → concat.
- IMAGE scenes (3,4,9): Ken-Burns hero image as the backdrop, Manim text/glow on top.
- Other scenes: reactive circuit_mind shader backdrop, Manim on top.
Usage: python3 render_ep01_manim.py            # all 10, then concat
       python3 render_ep01_manim.py 3,4,9       # re-render those, then re-concat all 10
"""
import os, sys, glob, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

HOME="/home/ubuntu"
BUILD=f"{HOME}/youtube_series/ep01_build"
ASSETS=f"{HOME}/youtube_series/assets"
WORK=f"{HOME}/youtube_series/ep01_manim_build"; os.makedirs(WORK, exist_ok=True)
OUT=f"{HOME}/youtube_series/ep01_manim_v3.mp4"
W,H,FPS=1920,1080,30
IMG={3:"img_party_crowd.png",4:"img_spotlight_field.png",9:"img_mind_network_head.png"}

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                     capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

arg=sys.argv[1] if len(sys.argv)>1 else "all"
todo=list(range(1,11)) if arg=="all" else [int(x) for x in arg.split(",")]

for i in todo:
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio); NF=int(D*FPS)
    print(f">> {sc}: {D:.1f}s — manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,"ep01_manim.py",sc],
                     cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/ep01_manim/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov {sc}\n{r.stderr[-1500:]}", flush=True); continue
    mov=movs[0]; clip=os.path.join(WORK,f"{sc}.mp4")
    if i in IMG:  # Ken-Burns hero image backdrop
        img=f"{ASSETS}/{IMG[i]}"
        kb=(f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"zoompan=z='min(zoom+0.00035,1.16)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={NF}:s=1920x1080:fps={FPS}[bg];[1:v]scale=1920:1080[mg];[bg][mg]overlay=0:0:format=auto[v]")
        cp=subprocess.run(["ffmpeg","-y","-i",img,"-i",mov,"-i",audio,
            "-filter_complex",kb,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip], capture_output=True, text=True)
        print(f"   image-scene composite", flush=True)
    else:  # reactive shader backdrop
        bg=os.path.join(WORK,f"{sc}_bg.mp4")
        render_shader_video(shader_name="circuit_mind",audio_path=audio,output_path=bg,duration=D,fps=FPS,width=W,height=H)
        cp=subprocess.run(["ffmpeg","-y","-i",bg,"-i",mov,"-i",audio,
            "-filter_complex","[1:v]scale=1920:1080[mg];[0:v][mg]overlay=0:0:format=auto[v]",
            "-map","[v]","-map","2:a","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-shortest",clip], capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1200:]}", flush=True); continue
    print(f"   {sc} clip done", flush=True)

# always re-concat all 10 from whatever is in WORK
clips=sorted(glob.glob(f"{WORK}/S??.mp4"))
if len(clips)==10:
    lst=os.path.join(WORK,"concat.txt")
    open(lst,"w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
    print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)", flush=True)
else:
    print(f"\n(have {len(clips)}/10 clips — not concatenating yet)", flush=True)
