#!/usr/bin/env python3
"""
Rain garden reel v2 — fully animated zones, memory-efficient.
Uses integer row/col shifts + brightness modulation per zone.
"""
import math, random, shutil, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE  = Path(__file__).parent
BASE  = HERE / "rain_reel" / "base_scene.png"
MUSIC = Path(__file__).parent.parent / "music_pipeline/bg_tracks/peaceful_garden_30s_cut.mp3"
FRAMES = HERE / "rain_reel" / "frames_v2"
OUT   = HERE / "rain_garden_reel_v2.mp4"
W, H  = 576, 1024
FPS   = 30
DUR   = 30
NF    = FPS * DUR

assert BASE.exists(), f"Need base image: {BASE}"

# ── Zone rows ──────────────────────────────────────────────────────────────
SKY_Y0,  SKY_Y1   = 0,           int(H * 0.18)
CAN_Y0,  CAN_Y1   = int(H*0.15), int(H * 0.53)
MID_Y0,  MID_Y1   = int(H*0.50), int(H * 0.71)
FLW_Y0,  FLW_Y1   = int(H*0.68), int(H * 0.89)
PTH_Y0,  PTH_Y1   = int(H*0.85), H

# Feather weight arrays for smooth blending
def feather(h, y0, y1, f=30):
    w = np.zeros(h, np.float32)
    w[y0:y1] = 1.0
    for i in range(min(f, y1-y0)):
        if y0+i < h: w[y0+i] = min(w[y0+i], i/f)
        if y1-1-i >= 0: w[y1-1-i] = min(w[y1-1-i], i/f)
    return w

SKY_W = feather(H, SKY_Y0, SKY_Y1, 30)
CAN_W = feather(H, CAN_Y0, CAN_Y1, 50)
MID_W = feather(H, MID_Y0, MID_Y1, 40)
FLW_W = feather(H, FLW_Y0, FLW_Y1, 35)
PTH_W = feather(H, PTH_Y0, PTH_Y1, 25)


def row_shift(arr, weights, shifts):
    """Shift each row by shifts[row] pixels, blend with original by weight[row]."""
    out = arr.copy()
    for y in range(H):
        s = int(shifts[y])
        w = weights[y]
        if w < 0.01 or s == 0:
            continue
        row = arr[y]
        shifted = np.roll(row, s, axis=0)
        out[y] = (row * (1 - w) + shifted * w).astype(np.uint8)
    return out


def col_shift(arr, weights, shifts_y, shifts_x):
    """Per-row vertical+horizontal blend for flowers."""
    out = arr.copy()
    for y in range(FLW_Y0, FLW_Y1):
        w = float(weights[y])
        if w < 0.01:
            continue
        sy = int(shifts_y[y])
        sx = int(shifts_x[y])
        src_y = max(0, min(H-1, y + sy))
        row = np.roll(arr[src_y], sx, axis=0)
        out[y] = (arr[y] * (1-w) + row * w).astype(np.uint8)
    return out


def animate_frame(base, t):
    arr = base.copy()

    # ── Sky / cloud drift ─────────────────────────────────────────────────
    cloud_shift = int((t * 0.5) % W)
    for y in range(SKY_Y0, SKY_Y1):
        w = SKY_W[y]
        if w < 0.01: continue
        shifted = np.roll(arr[y], cloud_shift, axis=0)
        # gentle vertical shimmer
        vy = int(math.sin(t * 0.4 + y * 0.03) * 1.5)
        src_y = max(0, min(H-1, y + vy))
        blended = (arr[src_y] * (1-w) + shifted * w).astype(np.uint8)
        arr[y] = blended

    # ── Canopy sway ───────────────────────────────────────────────────────
    can_shifts = np.array([
        math.sin(t * 1.1 + y * 0.018) * 5.0 +
        math.sin(t * 0.7 + y * 0.030) * 2.5 +
        math.sin(t * 1.8 + y * 0.010) * 1.2
        for y in range(H)
    ], dtype=np.float32)
    arr = row_shift(arr, CAN_W, can_shifts)

    # ── Bamboo / mid sway ────────────────────────────────────────────────
    mid_shifts = np.array([
        math.sin(t * 1.5 + y * 0.022 + 1.5) * 3.5 +
        math.sin(t * 2.2 + y * 0.015 + 0.8) * 1.8
        for y in range(H)
    ], dtype=np.float32)
    arr = row_shift(arr, MID_W, mid_shifts)

    # ── Flower bob ───────────────────────────────────────────────────────
    flw_dy = np.array([
        math.sin(t * 1.9 + y * 0.04) * 2.5 +
        math.sin(t * 2.6 + y * 0.07 + 1.0) * 1.2
        for y in range(H)
    ], dtype=np.float32)
    flw_dx = np.array([
        math.sin(t * 1.4 + y * 0.05 + 0.5) * 2.0
        for y in range(H)
    ], dtype=np.float32)
    arr = col_shift(arr, FLW_W, flw_dy, flw_dx)

    # ── Path shimmer (brightness only — water surface) ───────────────────
    for y in range(PTH_Y0, PTH_Y1):
        w = PTH_W[y]
        if w < 0.01: continue
        b = 1.0 + 0.06 * math.sin(t * 3.5 + y * 0.10) * w
        arr[y] = np.clip(arr[y].astype(np.float32) * b, 0, 255).astype(np.uint8)

    return arr


# ── Rain ──────────────────────────────────────────────────────────────────
class Drop:
    __slots__ = ('x','y','length','speed','angle','alpha','scale')
    def __init__(self, scale=1.0):
        self.scale = scale
        self._rand()
    def _rand(self):
        self.x      = random.uniform(-60, W + 60)
        self.y      = random.uniform(-H, H * 0.25)
        self.length = random.uniform(6, 28) * self.scale
        self.speed  = random.uniform(10, 38) * self.scale
        self.angle  = random.uniform(-0.20, -0.05)
        self.alpha  = int(random.uniform(45, 190) * self.scale)
    def step(self):
        self.y += self.speed
        self.x += self.speed * self.angle
        if self.y > H + 50: self._rand()

class Splash:
    def __init__(self):
        self.x = self.y = self.r = self.max_r = self.life = self.spd = 0.0
        self.reset()
    def reset(self):
        self.x     = random.uniform(W * 0.15, W * 0.85)
        self.y     = random.uniform(H * 0.87, H * 0.98)
        self.r     = 0.0
        self.max_r = random.uniform(3, 12)
        self.life  = 0.0
        self.spd   = random.uniform(0.06, 0.18)
    def step(self):
        self.life += self.spd
        self.r = self.max_r * min(self.life, 1.0)
        if self.life > 1.0: self.reset()

def render_rain_layer(drops, img):
    d = ImageDraw.Draw(img)
    for dr in drops:
        dx = int(dr.length * dr.angle)
        d.line([(dr.x, dr.y), (dr.x + dx, dr.y + int(dr.length))],
               fill=(215, 235, 255, int(dr.alpha)), width=1)

def render_splashes(spl_list, img):
    d = ImageDraw.Draw(img)
    for sp in spl_list:
        a = int(130 * (1 - sp.life))
        r = max(1, int(sp.r))
        d.ellipse([sp.x-r, sp.y-r, sp.x+r, sp.y+r],
                  outline=(200, 225, 255, a), width=1)

def composite(base_arr, rgba_arr):
    a = rgba_arr[:, :, 3:4].astype(np.float32) / 255.0
    rgb = rgba_arr[:, :, :3].astype(np.float32)
    return np.clip(base_arr.astype(np.float32) * (1 - a) + rgb * a, 0, 255).astype(np.uint8)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    FRAMES.mkdir(parents=True, exist_ok=True)

    img = Image.open(BASE).convert("RGB").resize((W, H), Image.LANCZOS)
    base = np.array(img, dtype=np.uint8)
    # colour grade once
    base = base.astype(np.float32)
    base[:,:,0] *= 0.93; base[:,:,1] *= 1.07; base[:,:,2] *= 1.05
    base = np.clip(base, 0, 255).astype(np.uint8)

    # Rain: 3 depth layers
    bg_drops = [Drop(0.45) for _ in range(200)]
    mg_drops = [Drop(0.72) for _ in range(160)]
    fg_drops = [Drop(1.00) for _ in range(130)]
    spl_list = [Splash()   for _ in range(50)]
    for sp in spl_list: sp.life = random.random()

    # Vignette mask (compute once)
    Y, X = np.ogrid[:H, :W]
    cy, cx = H/2, W/2
    dist = np.sqrt(((X-cx)/(W*0.58))**2 + ((Y-cy)/(H*0.52))**2)
    vig  = np.clip(1 - dist * 0.32, 0.62, 1.0).astype(np.float32)[:,:,None]

    print(f"Rendering {NF} frames — clouds / canopy / bamboo / flowers / path / rain / splashes")
    for i in range(NF):
        t = i / FPS

        # 1) Animate background zones
        arr = animate_frame(base, t)

        # 2) Rain layers
        rain_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for d in bg_drops: d.step()
        for d in mg_drops: d.step()
        for d in fg_drops: d.step()
        render_rain_layer(bg_drops, rain_img)
        render_rain_layer(mg_drops, rain_img)
        render_rain_layer(fg_drops, rain_img)
        render_splashes(spl_list, rain_img)
        for sp in spl_list: sp.step()

        arr = composite(arr, np.array(rain_img))

        # 3) Vignette
        arr = np.clip(arr.astype(np.float32) * vig, 0, 255).astype(np.uint8)

        Image.fromarray(arr).save(FRAMES / f"f{i:05d}.jpg", quality=90)
        if i % (FPS * 5) == 0:
            print(f"  {i}/{NF}  t={t:.0f}s")

    print("Encoding...")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f%05d.jpg"),
        "-i", str(MUSIC),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=576:1024",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(OUT)
    ], check=True, stderr=subprocess.DEVNULL)

    sz = OUT.stat().st_size // 1024 // 1024
    print(f"\n✅  {OUT}  ({sz} MB)")
    shutil.rmtree(FRAMES)

if __name__ == "__main__":
    main()
