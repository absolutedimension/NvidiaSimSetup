#!/usr/bin/env python3
"""EN Ep3 driver: ep04_manim.py + contextual bg_ep04 clips + logo finish.
Usage: python3 render_ep04_manim.py [all|6,7]"""
import os, sys, glob, subprocess
HOME="/home/ubuntu"
BUILD=f"{HOME}/youtube_series/ep04_build"
CLIPDIR=f"{HOME}/youtube_series/clips"
WORK=f"{HOME}/youtube_series/ep04_manim_build"; os.makedirs(WORK, exist_ok=True)
SPIN=f"{HOME}/youtube_series/assets/trigun_spin_1080.mp4"
W,H,FPS=1920,1080,30
ALLBG={i:f"bg_ep04_s{i:02d}_boom.mp4" for i in range(1,13)}
LOGO_SCENE=12
ENGINE="ep04_manim.py"; MEDIA="ep04_manim"

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

arg=sys.argv[1] if len(sys.argv)>1 else "all"
todo=list(range(1,13)) if arg=="all" else [int(x) for x in arg.split(",")]
COVER="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"

for i in todo:
    sc=f"S{i:02d}"; audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio)
    print(f">> {sc}: {D:.1f}s — manim", flush=True)
    env=dict(os.environ, SCENE_DUR=f"{D}")
    r=subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent",
                      "--disable_caching","-o",sc,ENGINE,sc], cwd=HOME, env=env, capture_output=True, text=True)
    movs=glob.glob(f"{HOME}/media/videos/{MEDIA}/**/{sc}.mov", recursive=True)
    if not movs:
        print(f"   !! no mov {sc}\n{r.stderr[-1500:]}", flush=True); continue
    mov=movs[0]; clip=os.path.join(WORK,f"{sc}.mp4")
    SCRIM=f"{HOME}/youtube_series/assets/scrim.png"; bgsrc=f"{CLIPDIR}/{ALLBG[i]}"
    if i==LOGO_SCENE and os.path.exists(SPIN):
        fc=(f"[3:v]scale=620:620,fps={FPS}[logo];[0:v][logo]overlay=(W-w)/2:500[bl];"
            f"[1:v]scale=1920:1080[mg];[bl][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-f","lavfi","-t",f"{D}","-i","color=c=0x06080f:s=1920x1080:r=30",
             "-i",mov,"-i",audio,"-stream_loop","-1","-t",f"{D}","-i",SPIN,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]; tag="split"
    else:
        fc=(f"[0:v]{COVER}[bg];[bg][3:v]overlay=0:0[bgs];"
            f"[1:v]scale=1920:1080[mg];[bgs][mg]overlay=0:0:format=auto[v]")
        cmd=["ffmpeg","-y","-stream_loop","-1","-t",f"{D}","-i",bgsrc,"-i",mov,"-i",audio,"-i",SCRIM,
             "-filter_complex",fc,"-map","[v]","-map","2:a","-c:v","libx264","-crf","20",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip]; tag="loop+scrim"
    cp=subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode!=0:
        print(f"   !! composite fail {sc}\n{cp.stderr[-1200:]}", flush=True); continue
    print(f"   {sc} done (bg={ALLBG[i]} · {tag})", flush=True)

clips=sorted(glob.glob(f"{WORK}/S??.mp4"))
print(f"\n(have {len(clips)}/12 scene clips)", flush=True)
