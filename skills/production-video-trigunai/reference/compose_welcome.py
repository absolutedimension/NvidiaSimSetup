"""
Compose the complete Welcome / Module-1 intro video.

  full narration (kept 100% intact)
+ full-length Vocal Melt shader background (voice-reactive)
+ 12 timed transparent section slides (durations ~ spoken length)
= welcome_complete.mp4

Runs on EC2 (needs GPU for the shader + ffmpeg). Reuses the Video Creator
backend services already deployed at /home/ubuntu/video-creator-backend.
"""
import os, sys, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.slide_service import render_slide
from services.shader_service import render_shader_video

AUDIO = "/home/ubuntu/full_voiceover.mp3"
SHADER = "vocal_melt"
W, H, FPS = 1920, 1080, 30
WORK = "/home/ubuntu/welcome_build"
OUT = "/home/ubuntu/welcome_complete.mp4"
os.makedirs(WORK, exist_ok=True)


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


# (spoken_text_for_weighting, slide kwargs)
SEGMENTS = [
    ("By the end of today, your first VR scene will be running on your Quest headset. Not a tutorial. Not a demo someone else built. YOUR scene, running on YOUR headset.",
     dict(title="Your First VR Scene", subtitle="Today", body="Running on YOUR Quest headset")),
    ("And by the end of this full course, eleven modules later, you'll have built a complete VR and Mixed Reality app, and submitted it to Meta's Store.",
     dict(title="Build a Complete VR + MR App", subtitle="11 modules", body="Submitted to Meta's Store")),
    ("And here's what makes this different from every other VR course out there: You won't be typing code by hand.",
     dict(title="You Won't Type Code by Hand", subtitle="What makes this different")),
    ("We're going to use AI coding agents, Claude Code specifically, to write our C# scripts. You describe what you want in plain English. The AI writes the code. You test it in VR. You iterate. That's how professional developers actually work in 2026.",
     dict(title="AI Coding Agents", subtitle="Claude Code", body="Describe in English  -  AI writes it  -  test in VR  -  iterate")),
    ("So even if you've never written a line of code, you can build this.",
     dict(title="No Experience Needed", subtitle="Even if you've never written a line of code")),
    ("Here's the journey. Module 1, that's today, we set up Unity, configure it for Quest, and build our first VR room.",
     dict(title="Module 1  -  Today", subtitle="The Journey begins", body="Set up Unity, configure for Quest, build your first VR room")),
    ("Module 2, we set up our AI coding partner.",
     dict(title="Module 2", subtitle="Your AI Coding Partner")),
    ("Modules 3 through 8, we add hands, UI, audio, movement, saving, and multiplayer.",
     dict(title="Modules 3 - 8", body="Hands  -  UI  -  Audio  -  Movement  -  Saving  -  Multiplayer")),
    ("Module 9, this is the one that makes your resume different, Mixed Reality. Your app objects placed in your real room through Quest 3 passthrough.",
     dict(title="Module 9  -  Mixed Reality", subtitle="The one that makes your resume different", body="Your objects in your real room, via Quest 3 passthrough")),
    ("Module 10, we polish for performance.",
     dict(title="Module 10", subtitle="Polish for Performance")),
    ("And Module 11, we submit to Meta's Store. Nobody else teaches that last step.",
     dict(title="Module 11  -  Submit to Meta's Store", subtitle="Nobody else teaches this last step")),
    ("My name is Deepak, and I'm not just teaching this. I built a VR app called EnergyField that's currently in Meta's alpha program. I'm going to show you exactly how I did it. Every step, every bug, every fix. Let's start.",
     dict(title="Meet Deepak", subtitle="Creator of EnergyField  -  live in Meta's alpha", body="Every step. Every bug. Every fix.  Let's start.")),
]

AUDIO_DUR = dur(AUDIO)
total_chars = sum(len(t) for t, _ in SEGMENTS)
print(f"audio = {AUDIO_DUR:.1f}s across {len(SEGMENTS)} slides")

# durations proportional to spoken length
durations, t = [], 0.0
for i, (text, _) in enumerate(SEGMENTS):
    d = AUDIO_DUR * len(text) / total_chars
    if i == len(SEGMENTS) - 1:
        d = AUDIO_DUR - t  # absorb rounding into last
    durations.append((t, t + d))
    t += d

# 1. transparent slides
slide_paths = []
for i, (_, kw) in enumerate(SEGMENTS):
    p = os.path.join(WORK, f"slide_{i:02d}.png")
    render_slide(layout="center", transparent=True, output_path=p, **kw)
    slide_paths.append(p)
print("slides rendered")

# 2. full-length shader background reactive to the narration
shader_bg = os.path.join(WORK, "shader_bg.mp4")
print("rendering shader background (full length)...")
render_shader_video(shader_name=SHADER, audio_path=AUDIO, output_path=shader_bg,
                    duration=AUDIO_DUR, fps=FPS, width=W, height=H)

# 3. composite: shader bg + timed slide overlays + intact narration
inputs = ["-i", shader_bg]
for p in slide_paths:
    inputs += ["-loop", "1", "-t", f"{AUDIO_DUR:.2f}", "-i", p]
inputs += ["-i", AUDIO]
audio_idx = 1 + len(slide_paths)

fc, base = [], "0:v"
for i, (s, e) in enumerate(durations):
    fade = 0.4
    label = f"v{i}"
    fc.append(
        f"[{i+1}:v]scale={W}:{H},format=rgba,"
        f"fade=t=in:st={s:.2f}:d={fade}:alpha=1,fade=t=out:st={e-fade:.2f}:d={fade}:alpha=1[s{i}];"
        f"[{base}][s{i}]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[{label}]"
    )
    base = label
fc.append(f"[{base}]format=yuv420p[v]")

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", ";".join(fc),
    "-map", "[v]", "-map", f"{audio_idx}:a",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", OUT,
]
print("compositing final video...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERROR:\n", r.stderr[-1500:])
    sys.exit(1)
print(f"DONE -> {OUT}  ({dur(OUT):.1f}s, {os.path.getsize(OUT)//1024//1024} MB)")
