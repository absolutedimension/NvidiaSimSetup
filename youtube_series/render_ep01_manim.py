#!/usr/bin/env python3
"""
Driver: Episode 1 via Manim engine + per-scene contextual-abstract background CLIPS.
Every scene = its background clip (stretched to fill) with the Manim text/diagram on top.
Hero scenes (3,4,9) use the LTX hero clips (party/spotlight/brain); the rest use the
contextual-abstract bg clips (bg_sNN.mp4). The FINAL scene (10) also gets the spinning
TrigunAI logo screen-blended in — no separate outro.
Usage: python3 render_ep01_manim.py            # all 10, concat
       python3 render_ep01_manim.py 6,7         # re-render those, re-concat all 10
"""
import os, sys, glob, subprocess
HOME="/home/ubuntu"
BUILD=f"{HOME}/youtube_series/ep01_build"
CLIPDIR=f"{HOME}/youtube_series/clips"
WORK=f"{HOME}/youtube_series/ep01_manim_build"; os.makedirs(WORK, exist_ok=True)
OUT=f"{HOME}/youtube_series/ep01_manim_v3.mp4"
SPIN=f"{HOME}/youtube_series/assets/trigun_spin_1080.mp4"
W,H,FPS=1920,1080,30
ALLBG={1:"bg_s01_boom.mp4",2:"bg_s02_boom.mp4",3:"party_boom.mp4",4:"spotlight_boom.mp4",5:"bg_s05_boom.mp4",
       6:"bg_s06_boom.mp4",7:"bg_s07_boom.mp4",8:"bg_s08_boom.mp4",9:"brain_boom.mp4",10:"bg_s10.mp4"}
LOGO_SCENE=10

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                     capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

arg=sys.argv[1] if len(sys.argv)>1 else "all"
todo=list(range(1,11)) if arg=="all" else [int(x) for x in arg.split(",")]
COVER="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"

for i in todo:
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio)
    print(f">> {sc}: {D:.1f}s — manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,"ep01_manim.py",sc], cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/ep01_manim/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov {sc}\n{r.stderr[-1500:]}", flush=True); continue
    mov=movs[0]; clip=os.path.join(WORK,f"{sc}.mp4")
    SCRIM=f"{HOME}/youtube_series/assets/scrim.png"
    bgsrc=f"{CLIPDIR}/{ALLBG[i]}"
    if i==LOGO_SCENE and os.path.exists(SPIN):
        # FINAL scene SPLIT: text in top half (manim), spin logo in bottom half, on a dark bg
        fc=(f"[3:v]scale=620:620,fps={FPS}[logo];"
            f"[0:v][logo]overlay=(W-w)/2:500[bl];"
            f"[1:v]scale=1920:1080[mg];[bl][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-f","lavfi","-t",f"{D}","-i","color=c=0x06080f:s=1920x1080:r=30",
             "-i",mov,"-i",audio,"-stream_loop","-1","-t",f"{D}","-i",SPIN,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]
        tag="split: dark bg, text top / logo bottom"
    else:
        # loop bg at NATIVE speed (smooth, no stutter) + text-safe scrim + manim text
        fc=(f"[0:v]{COVER}[bg];[bg][3:v]overlay=0:0[bgs];"
            f"[1:v]scale=1920:1080[mg];[bgs][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-stream_loop","-1","-t",f"{D}","-i",bgsrc,"-i",mov,"-i",audio,"-i",SCRIM,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]
        tag="loop+scrim"
    cp=subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1200:]}", flush=True); continue
    print(f"   {sc} done (bg={ALLBG[i]} · {tag})", flush=True)

clips=sorted(glob.glob(f"{WORK}/S??.mp4"))
if len(clips)==10:
    lst=os.path.join(WORK,"concat.txt"); open(lst,"w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
    print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)", flush=True)
else:
    print(f"\n(have {len(clips)}/10 clips)", flush=True)
