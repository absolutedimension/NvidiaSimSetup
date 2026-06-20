#!/usr/bin/env python3
"""
Compose Course 1 / Module 1 video (Mode A): per-scene transparent text cards over the
audio-reactive circuit_mind shader, timed to the FROZEN per-scene audio in mod01_build/.
Scene-by-scene render -> concat (no giant filtergraph). Faceless, no presenter.

Usage (on EC2):
  python3 compose_mod01.py --scene 1     # prototype just scene 1
  python3 compose_mod01.py               # full build (all 12) -> module01_FINAL.mp4
"""
import os, sys, subprocess, argparse
sys.path.append('/home/ubuntu/video-creator-backend')
from services.slide_service import render_slide
from services.shader_service import render_shader_video

BUILD = "/home/ubuntu/youtube_series/mod01_build"      # frozen audio sNN.mp3 live here
OUT   = "/home/ubuntu/youtube_series/mod01_out"
SHADER = "circuit_mind"
MUSIC = "/home/ubuntu/welcome_voice/bg_ambient.mp3"    # ambient_low bed
W, H, FPS = 1920, 1080, 30
os.makedirs(OUT, exist_ok=True)

# scene_id -> render_slide kwargs (on_screen from the script)
SCENES = [
    dict(layout="center",  accent_color="blue",  title="Your First VR Scene",
         subtitle="Module 1", body="Running on YOUR Quest headset"),
    dict(layout="bullets", accent_color="blue",  title="The Project  —  ZenSpace",
         bullet_points=["A VR + MR meditation room",
                        "Beginner-simple, teaches every core idea",
                        "Mirrors my real shipped app, EnergyField"]),
    dict(layout="bullets", accent_color="purple", title="You Won't Type Code by Hand",
         bullet_points=["Describe what you want — in plain English",
                        "The AI agent writes the C#",
                        "You test in VR, then iterate"]),
    dict(layout="bullets", accent_color="blue",  title="The 11-Module Journey",
         bullet_points=["1 · Tools + first room",
                        "2 · Your AI coding partner",
                        "3–8 · Hands, UI, audio, movement, multiplayer",
                        "9 · Mixed Reality",
                        "10 · Polish",
                        "11 · Ship to Meta's Store"]),
    dict(layout="center",  accent_color="purple", title="The VR Development Loop",
         body="Unity  →  APK  →  Quest  →  test  →  repeat"),
    dict(layout="bullets", accent_color="blue",  title="What a VR Scene Really Is",
         bullet_points=["Camera rig — that's YOU, tracked in space",
                        "Geometry — the floor and walls",
                        "Materials — how surfaces look",
                        "Lights — warmth, not emptiness"]),
    dict(layout="bullets", accent_color="amber", title="Today You Install Three Things",
         bullet_points=["Unity 6  +  Android Build Support",
                        "Meta XR All-in-One SDK  (free)",
                        "Switch the build target to Meta Quest"]),
    dict(layout="bullets", accent_color="amber", title="Build the Room",
         bullet_points=["Warm wood floor",
                        "Soft cream walls",
                        "Sunlight + a warm overhead glow",
                        "One meditation stone"]),
    dict(layout="center",  accent_color="green", title="Put On the Headset",
         subtitle="You made this",
         body="You're not watching a VR scene — you're standing in one"),
    dict(layout="bullets", accent_color="green", title="Every Bug, Every Fix",
         bullet_points=["I built EnergyField — live in Meta alpha",
                        "I've hit every one of these errors",
                        "You get the fixes, not just the happy path"]),
    dict(layout="bullets", accent_color="blue",  title="How to Use This Module",
         bullet_points=["This video = the MAP  (what + why)",
                        "The Lab Guide = the TERRAIN  (every click)",
                        "Watch once, then build along with the guide"]),
    dict(layout="center",  accent_color="green", title="Next — Your AI Coding Partner",
         subtitle="Module 2", body="Open the Lab Guide and let's start"),
]

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                        "-of","csv=p=0",p], capture_output=True, text=True)
    return float(r.stdout.strip())

def build_scene(i):
    n = i + 1
    audio = f"{BUILD}/s{n:02d}.mp3"
    d = dur(audio)
    slide = f"{OUT}/slide{n:02d}.png"
    bg    = f"{OUT}/bg{n:02d}.mp4"
    clip  = f"{OUT}/scene{n:02d}.mp4"
    # 1) transparent text card
    render_slide(transparent=True, output_path=slide, **SCENES[i])
    # 2) circuit_mind shader bg, reactive to this scene's voice, exact length
    render_shader_video(shader_name=SHADER, audio_path=audio, output_path=bg,
                        duration=d, fps=FPS, width=W, height=H)
    # 3) composite: card fades in/out over shader, scene audio
    fo = max(d - 0.4, 0.1)
    fc = (f"[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1,"
          f"fade=out:st={fo:.2f}:d=0.4:alpha=1[s];"
          f"[0:v][s]overlay=0:0,format=yuv420p[v]")
    subprocess.run(["ffmpeg","-y","-i",bg,"-loop","1","-i",slide,"-i",audio,
                    "-filter_complex",fc,"-map","[v]","-map","2:a","-t",f"{d:.3f}",
                    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k",clip], check=True,
                   capture_output=True)
    print(f"  scene{n:02d}: {d:5.1f}s  -> {clip}", flush=True)
    return clip, d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, default=0, help="1-based; 0 = full build")
    ap.add_argument("--scenes", type=str, default="", help="comma list of 1-based scenes to (re)render")
    ap.add_argument("--finalize", action="store_true", help="concat existing scene clips + music only")
    a = ap.parse_args()

    if a.scenes:
        for n in [int(x) for x in a.scenes.split(",") if x.strip()]:
            build_scene(n - 1)
        print(">> scenes done", flush=True)
        return

    if a.scene:
        build_scene(a.scene - 1)
        print(">> single scene done", flush=True)
        return

    clips, total = [], 0.0
    for i in range(len(SCENES)):
        if a.finalize:
            c = f"{OUT}/scene{i+1:02d}.mp4"; d = dur(c)
        else:
            c, d = build_scene(i)
        clips.append(c); total += d
    # concat (re-encode, not -c copy)
    lst = f"{OUT}/concat.txt"
    with open(lst,"w") as f:
        for c in clips: f.write(f"file '{c}'\n")
    nomusic = f"{OUT}/module01_nomusic.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k",nomusic], check=True, capture_output=True)
    # ambient music bed, looped to fill, ducked low
    final = f"{OUT}/module01_FINAL.mp4"
    if os.path.exists(MUSIC):
        fo = max(total - 3, 1)
        mf = (f"[1:a]volume=0.06,afade=in:st=0:d=3,afade=out:st={fo:.2f}:d=3[m];"
              f"[0:a][m]amix=inputs=2:duration=first[a]")
        subprocess.run(["ffmpeg","-y","-i",nomusic,"-stream_loop","-1","-i",MUSIC,
                        "-filter_complex",mf,"-map","0:v","-map","[a]",
                        "-c:v","copy","-c:a","aac","-b:a","192k",final],
                       check=True, capture_output=True)
    else:
        os.replace(nomusic, final)
    print(f">> FINAL {total:.1f}s -> {final}", flush=True)

if __name__ == "__main__":
    main()
