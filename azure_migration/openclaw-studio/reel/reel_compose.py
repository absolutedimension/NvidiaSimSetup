#!/usr/bin/env python3
"""Vertical 9:16 reel composer: PIL kinetic text beats over an audio-reactive shader bg + F5 voiceover.
Run from inside video-creator-backend/ (for the services import).
Usage: python reel_compose.py <build_dir> <out.mp4> [shader]
  build_dir/voice/  must contain full_voiceover.wav + manifest.json (from generate_voice_f5.py)
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from services.shader_service import render_shader_video
from PIL import Image, ImageDraw, ImageFont

BUILD  = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/reel_build")
OUT    = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/reel_agentic.mp4")
SHADER = sys.argv[3] if len(sys.argv) > 3 else "circuit_mind"
VOICE  = os.path.join(BUILD, "voice")
WORK   = os.path.join(BUILD, "work"); os.makedirs(WORK, exist_ok=True)
W, H, FPS = 1080, 1920, 30
HOME = os.path.expanduser("~")
FONT_DIR = os.path.join(HOME, ".local/share/fonts")
F_TITLE = os.path.join(FONT_DIR, "Poppins-ExtraBold.ttf")
F_SUB   = os.path.join(FONT_DIR, "Poppins-Bold.ttf")

# on-screen beats, aligned 1:1 with the F5 segments (no special glyphs — Poppins-safe)
BEATS = [
    {"title": "An agent\nACTS",          "subtitle": "a chatbot just answers"},
    {"title": "Reason. Act.\nCheck. Repeat.", "subtitle": "until the job is done"},
    {"title": "From TALK\nto ACTION",     "subtitle": "that's the shift"},
    {"title": "It takes the\nNEXT STEP",  "subtitle": "not just the next word"},
    {"title": "A tireless\nDIGITAL WORKER", "subtitle": "TrigunAI"},
]

def make_beat(title, subtitle, out):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # soft dark scrim band behind the text for readability over the shader
    band_h = 760; y0 = (H - band_h) // 2
    scrim = Image.new("RGBA", (W, band_h), (8, 10, 18, 150))
    img.alpha_composite(scrim, (0, y0))
    ft = ImageFont.truetype(F_TITLE, 110)
    fs = ImageFont.truetype(F_SUB, 56)
    lines = title.split("\n")
    # total title block height
    line_h = 128
    block_h = line_h * len(lines)
    ty = (H - block_h) // 2 - 40
    for ln in lines:
        w = d.textbbox((0, 0), ln, font=ft)[2]
        # subtle shadow + white text
        d.text(((W - w) // 2 + 3, ty + 3), ln, font=ft, fill=(0, 0, 0, 180))
        d.text(((W - w) // 2, ty), ln, font=ft, fill=(255, 255, 255, 255))
        ty += line_h
    # subtitle (accent)
    sw = d.textbbox((0, 0), subtitle, font=fs)[2]
    d.text(((W - sw) // 2, ty + 24), subtitle, font=fs, fill=(124, 156, 255, 255))
    img.save(out)

def ffprobe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", p], capture_output=True, text=True)
    return float(r.stdout.strip())

AUDIO = os.path.join(VOICE, "full_voiceover.wav")
AUDIO_DUR = ffprobe_dur(AUDIO)
man = json.load(open(os.path.join(VOICE, "manifest.json")))
seg_durs = [s["duration"] for s in man["segments"]]
tot = sum(seg_durs)
durations, t = [], 0.0
for i, sd in enumerate(seg_durs):
    dd = AUDIO_DUR * sd / tot
    if i == len(seg_durs) - 1:
        dd = AUDIO_DUR - t
    durations.append((t, t + dd)); t += dd

# 1. text beats
slide_paths = []
for i, b in enumerate(BEATS):
    p = os.path.join(WORK, f"beat_{i:02d}.png")
    make_beat(b["title"], b["subtitle"], p)
    slide_paths.append(p)
print(f"beats rendered: {len(slide_paths)}  audio={AUDIO_DUR:.1f}s")

# 2. vertical audio-reactive shader bg
shader_bg = os.path.join(WORK, "shader_bg.mp4")
render_shader_video(shader_name=SHADER, audio_path=AUDIO, output_path=shader_bg,
                    duration=AUDIO_DUR, fps=FPS, width=W, height=H)
print("shader bg rendered")

# 3. composite: shader bg + timed full-canvas beat overlays + voiceover
inputs = ["-i", shader_bg]
for p in slide_paths:
    inputs += ["-loop", "1", "-t", f"{AUDIO_DUR:.2f}", "-i", p]
inputs += ["-i", AUDIO]
audio_idx = 1 + len(slide_paths)
fc, base = [], "0:v"
for i, (s, e) in enumerate(durations):
    fade = 0.35; label = f"v{i}"
    fc.append(
        f"[{i+1}:v]format=rgba,fade=t=in:st={s:.2f}:d={fade}:alpha=1,"
        f"fade=t=out:st={max(e-fade, s):.2f}:d={fade}:alpha=1[s{i}];"
        f"[{base}][s{i}]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[{label}]"
    )
    base = label
fc.append(f"[{base}]format=yuv420p[v]")
cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", ";".join(fc),
    "-map", "[v]", "-map", f"{audio_idx}:a",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest", OUT,
]
subprocess.run(cmd, check=True)
print("REEL_DONE", OUT)
