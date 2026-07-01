#!/usr/bin/env python3
"""EN Ep8 driver: ep08_manim.py over a clean dark background (no LTX clips needed) + logo finish.
Usage: python3 render_ep08_manim.py [all|3,5]"""
import os, sys, glob, subprocess
HOME="/home/ubuntu"
BUILD=f"{HOME}/youtube_series/ep08_build"
WORK=f"{HOME}/youtube_series/ep08_manim_build"; os.makedirs(WORK, exist_ok=True)
ASSETS=f"{HOME}/youtube_series/assets"
SPIN=f"{ASSETS}/trigun_spin_1080.mp4"
SCRIM=f"{ASSETS}/scrim.png"
BG=f"{ASSETS}/dark_bg_ep08.png"
W,H,FPS=1920,1080,30
N=14; LOGO_SCENE=14
ENGINE="ep08_manim.py"; MEDIA="ep08_manim"

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

# --- ensure a clean dark background still exists (deep blue-black radial vignette) ---
if not os.path.exists(BG):
    from PIL import Image
    import math
    img=Image.new("RGB",(W,H))
    px=img.load()
    cx,cy=W/2,H*0.42; maxd=math.hypot(cx,cy)
    for y in range(H):
        for x in range(W):
            d=math.hypot(x-cx,y-cy)/maxd
            t=min(1.0,d)
            r=int(10+ 6*(1-t)); g=int(12+10*(1-t)); b=int(20+22*(1-t))
            px[x,y]=(max(4,r),max(6,g),max(10,b))
    img.save(BG)
    print(f">> generated {BG}", flush=True)

arg=sys.argv[1] if len(sys.argv)>1 else "all"
todo=list(range(1,N+1)) if arg=="all" else [int(x) for x in arg.split(",")]

for i in todo:
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio)
    print(f">> {sc}: {D:.1f}s — manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,ENGINE,sc], cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/{MEDIA}/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov {sc}\n{r.stderr[-1800:]}", flush=True); continue
    mov=movs[0]; clip=os.path.join(WORK,f"{sc}.mp4")
    if i==LOGO_SCENE and os.path.exists(SPIN):
        fc=(f"[0:v][4:v]overlay=0:0[bgs];"
            f"[3:v]scale=560:560,fps={FPS}[logo];[bgs][logo]overlay=(W-w)/2:560[bl];"
            f"[1:v]scale=1920:1080[mg];[bl][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-loop","1","-t",f"{D}","-i",BG,"-i",mov,"-i",audio,
             "-stream_loop","-1","-t",f"{D}","-i",SPIN,"-i",SCRIM,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]; tag="split-logo"
    else:
        fc=(f"[0:v][3:v]overlay=0:0[bgs];"
            f"[1:v]scale=1920:1080[mg];[bgs][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-loop","1","-t",f"{D}","-i",BG,"-i",mov,"-i",audio,"-i",SCRIM,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]; tag="dark-bg"
    cp=subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1400:]}", flush=True); continue
    print(f"   {sc} done ({tag})", flush=True)

clips=sorted(glob.glob(f"{WORK}/S??.mp4"))
print(f"\n(have {len(clips)}/{N} scene clips)", flush=True)
