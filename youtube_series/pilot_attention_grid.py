#!/usr/bin/env python3
"""
PILOT — animated attention grid (scene 6 of Episode 1).
Renders the signature teaching visual: words score every other word, then the row
for "it" lights up — "animal" bright (high attention), "street" dim (ignored).
Composited over the circuit_mind shader bg + the real scene-6 narration.
Output: /home/ubuntu/youtube_series/pilot_attention_grid.mp4
"""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

W, H, FPS = 1920, 1080, 30
AUDIO = "/home/ubuntu/youtube_series/ep01_build/s06.mp3"
WORK = "/home/ubuntu/youtube_series/pilot_grid"
FRAMES = os.path.join(WORK, "frames")
OUT = "/home/ubuntu/youtube_series/pilot_attention_grid.mp4"
os.makedirs(FRAMES, exist_ok=True)

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                       capture_output=True, text=True); return float(r.stdout.strip())
DUR = dur(AUDIO)
NF = int(DUR * FPS)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font_lbl   = ImageFont.truetype(FB, 30)
font_title = ImageFont.truetype(FB, 46)
font_cap   = ImageFont.truetype(FB, 40)

WORDS = ["animal", "crossed", "the", "street", "because", "it", "tired"]
n = len(WORDS)
IT, ANIMAL, STREET = WORDS.index("it"), WORDS.index("animal"), WORDS.index("street")

# full-grid pseudo weights (every word scores every word) — seeded, deterministic
rng = np.random.default_rng(7)
FULL = rng.uniform(0.08, 0.75, (n, n))
np.fill_diagonal(FULL, 0.25)
# the explicit "it" row (the story): animal high, street low
IT_ROW = np.full(n, 0.12)
IT_ROW[ANIMAL] = 0.97; IT_ROW[STREET] = 0.12; IT_ROW[WORDS.index("tired")] = 0.55
IT_ROW[WORDS.index("because")] = 0.30

# grid geometry
CELL, GAP = 86, 8
GRID = n * CELL + (n - 1) * GAP
GX = (W - GRID) // 2 + 70          # shift right to leave room for row labels
GY = (H - GRID) // 2 + 30

def lerp(a, b, t): return a + (b - a) * t
def smooth(t): return t * t * (3 - 2 * t)
def clamp01(x): return max(0.0, min(1.0, x))

def cell_color(w):
    # dim blue -> gold by weight
    lo, hi = (44, 64, 104), (255, 196, 70)
    return tuple(int(lerp(lo[i], hi[i], clamp01(w))) for i in range(3))

def draw_text_c(d, cx, cy, txt, font, fill):
    b = d.textbbox((0, 0), txt, font=font)
    d.text((cx - (b[2]-b[0])/2, cy - (b[3]-b[1])/2 - b[1]), txt, font=font, fill=fill)

for f in range(NF):
    t = f / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft scrim so text/grid read over the shader
    scrim = Image.new("RGBA", (W, H), (6, 8, 20, 120))
    img = Image.alpha_composite(img, scrim)
    d = ImageDraw.Draw(img)

    # phase envelopes
    a_in   = smooth(clamp01(t / 2.5))                 # grid fade-in
    shimmer = clamp01((t - 5) / 2)                    # full-grid scoring on
    isolate = smooth(clamp01((t - 17) / 3))           # dim to the "it" row
    reveal  = smooth(clamp01((t - 20) / 7))           # it-row weights reveal
    lock    = clamp01((t - 30) / 2)                   # lock-on pulse

    # title
    d.text((GX - 0, GY - 95), "Every word scores every other word",
           font=font_title, fill=(235, 238, 250, int(230 * a_in)))

    # column + row labels
    for j, wd in enumerate(WORDS):
        cx = GX + j * (CELL + GAP) + CELL / 2
        is_it_col = False
        draw_text_c(d, cx, GY - 34, wd, font_lbl, (170, 185, 220, int(220 * a_in)))
    for i, wd in enumerate(WORDS):
        cy = GY + i * (CELL + GAP) + CELL / 2
        hot = (i == IT) and isolate > 0
        col = (255, 210, 90) if hot else (170, 185, 220)
        b = d.textbbox((0,0), wd, font=font_lbl)
        d.text((GX - 22 - (b[2]-b[0]), cy - (b[3]-b[1])/2 - b[1]), wd, font=font_lbl,
               fill=col + (int(235 * a_in),))

    # cells
    for i in range(n):
        for j in range(n):
            x0 = GX + j * (CELL + GAP); y0 = GY + i * (CELL + GAP)
            # weight per phase
            w_full = FULL[i, j] * shimmer
            if i == IT:
                w = lerp(w_full, IT_ROW[j], reveal)
            else:
                w = w_full * (1 - isolate * 0.92)      # dim non-it rows when isolating
            # gentle shimmer flicker before isolate
            if isolate < 0.5:
                w *= 0.82 + 0.18 * math.sin(t * 3 + (i * 7 + j))
            w = clamp01(w)
            base_a = int(40 + 200 * w) * a_in / 255 * 255
            col = cell_color(w)
            # lock-on highlight for it->animal
            if i == IT and j == ANIMAL and lock > 0:
                pulse = 0.5 + 0.5 * math.sin(t * 6)
                col = (255, 215, 90); base_a = 255
                d.rounded_rectangle([x0-5, y0-5, x0+CELL+5, y0+CELL+5], radius=16,
                                    outline=(255, 235, 150, int(255*lock)), width=int(3+3*pulse))
            d.rounded_rectangle([x0, y0, x0 + CELL, y0 + CELL], radius=12,
                                fill=col + (int(clamp01(base_a/255) * 255),))

    # caption on lock-on
    if lock > 0:
        cap = '"it"  →  "animal"'
        d.text((GX, GY + GRID + 34), cap, font=font_cap, fill=(255, 215, 110, int(255*lock)))
        d.text((GX + 360, GY + GRID + 38), "  not \"street\"", font=font_lbl,
               fill=(150, 165, 200, int(220*lock)))

    img.convert("RGB").save  # noop guard
    img.save(os.path.join(FRAMES, f"f{f:04d}.png"))
    if f % 120 == 0:
        print(f"frame {f}/{NF}", flush=True)

print(">> frames done; rendering shader bg…", flush=True)
bg = os.path.join(WORK, "bg.mp4")
render_shader_video(shader_name="circuit_mind", audio_path=AUDIO, output_path=bg,
                    duration=DUR, fps=FPS, width=W, height=H)

print(">> compositing grid over shader + audio…", flush=True)
cmd = ["ffmpeg", "-y",
       "-i", bg,
       "-framerate", str(FPS), "-i", os.path.join(FRAMES, "f%04d.png"),
       "-i", AUDIO,
       "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto[v]",
       "-map", "[v]", "-map", "2:a",
       "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERR:\n", r.stderr[-2500:]); sys.exit(1)
print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)", flush=True)
