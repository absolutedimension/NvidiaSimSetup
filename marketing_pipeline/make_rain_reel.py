#!/usr/bin/env python3
"""
Rain garden reel generator — recreates the animated rain/nature cinemagraph style.
Generates scene via Azure gpt-image-1.5, adds rain + tree sway via PIL, encodes with ffmpeg.
"""
import os, sys, json, random, math, subprocess, base64, requests, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
HERE      = Path(__file__).parent
OUT_DIR   = HERE / "rain_reel"
MUSIC     = Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/music_pipeline/bg_tracks/peaceful_garden_30s_cut.mp3")
OUT_MP4   = HERE / "rain_garden_reel.mp4"
FRAMES    = OUT_DIR / "frames"
W, H      = 576, 1024
FPS       = 30
DURATION  = 30   # seconds
N_FRAMES  = FPS * DURATION

# ── Azure image gen ────────────────────────────────────────────────────────
AZURE_ENDPOINT = "https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
AZURE_KEY      = "3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
AZURE_VERSION  = "2025-04-01-preview"

PROMPT = (
    "A breathtaking AI-generated painterly garden scene, vertical portrait 9:16, "
    "lush winding stone path curving into the distance, a large white cherry blossom tree "
    "dominating the right side, vibrant pink and yellow flowers lining the path edges, "
    "green bamboo and trees in soft-focus background, dramatic overcast sky with soft light, "
    "wet stone path reflecting surroundings, ultra-detailed digital painting style, "
    "dreamy saturated greens and pinks, cinematic depth of field, no text, no people"
)

def generate_base_image(out_path: Path):
    print("Generating base scene via Azure gpt-image-1.5...")
    url = f"{AZURE_ENDPOINT}/openai/deployments/gpt-image-1.5/images/generations?api-version={AZURE_VERSION}"
    r = requests.post(url, headers={"api-key": AZURE_KEY, "Content-Type": "application/json"},
                      json={"prompt": PROMPT, "n": 1, "size": "1024x1536",
                            "quality": "high", "output_format": "png"},
                      timeout=120)
    r.raise_for_status()
    data = r.json()
    b64 = data["data"][0].get("b64_json") or data["data"][0].get("url")
    if b64 and not b64.startswith("http"):
        img_bytes = base64.b64decode(b64)
    else:
        img_bytes = requests.get(b64, timeout=60).content
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    print(f"  Base image saved → {out_path}")

# ── Rain system ────────────────────────────────────────────────────────────
class RainDrop:
    def __init__(self, w, h):
        self.reset(w, h, random.random())
    def reset(self, w, h, progress=0):
        self.x = random.randint(-50, w + 50)
        self.y = random.randint(-h, int(h * progress))
        self.length = random.randint(8, 28)
        self.speed  = random.uniform(14, 32)
        self.angle  = random.uniform(-0.18, -0.08)   # slight diagonal
        self.alpha  = random.randint(60, 160)
        self.width  = 1
    def update(self, w, h):
        self.y += self.speed
        self.x += self.speed * self.angle
        if self.y > h + 40:
            self.reset(w, h)

def draw_rain(base: Image.Image, drops, intensity=1.0) -> Image.Image:
    rain = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(rain)
    for drop in drops:
        a = int(drop.alpha * intensity)
        dx = int(drop.length * drop.angle)
        d.line([(drop.x, drop.y), (drop.x + dx, drop.y + drop.length)],
               fill=(220, 235, 255, a), width=drop.width)
    return Image.alpha_composite(base.convert("RGBA"), rain)

def add_sway(img: Image.Image, t: float, strength=2.0) -> Image.Image:
    """Subtle horizontal warp to simulate tree sway."""
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]
    # Sine-based horizontal displacement, stronger at top (trees)
    for y in range(h):
        weight = max(0, 1 - y / (h * 0.65))   # stronger at top
        shift = int(math.sin(t * 0.9 + y * 0.012) * strength * weight)
        if shift > 0:
            arr[y, shift:] = arr[y, :-shift] if shift < w else arr[y]
        elif shift < 0:
            arr[y, :shift] = arr[y, -shift:]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def add_wetness_shimmer(img: Image.Image, t: float) -> Image.Image:
    """Subtle brightness pulse on the wet path."""
    enhancer = ImageEnhance.Brightness(img)
    factor = 1.0 + 0.012 * math.sin(t * 2.3)
    return enhancer.enhance(factor)

def color_grade(img: Image.Image) -> Image.Image:
    """Push greens, cool highlights — matches the original palette."""
    arr = np.array(img, dtype=np.float32)
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.06, 0, 255)   # +green
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.04, 0, 255)   # +blue (cool)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.96, 0, 255)   # -red
    return Image.fromarray(arr.astype(np.uint8))

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    OUT_DIR.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)

    base_path = OUT_DIR / "base_scene.png"
    if not base_path.exists():
        generate_base_image(base_path)
    else:
        print(f"Base image already exists, skipping generation.")

    base = Image.open(base_path).convert("RGB")
    base = base.resize((W, H), Image.LANCZOS)
    base = color_grade(base)

    # Init rain layers — 3 depths
    n_drops_fg = 120
    n_drops_mg = 80
    n_drops_bg = 50
    drops_fg = [RainDrop(W, H) for _ in range(n_drops_fg)]
    drops_mg = [RainDrop(W, H) for _ in range(n_drops_mg)]
    drops_bg = [RainDrop(W, H) for _ in range(n_drops_bg)]

    print(f"Rendering {N_FRAMES} frames ({DURATION}s @ {FPS}fps)...")
    for i in range(N_FRAMES):
        t = i / FPS
        # Update drops
        for d in drops_fg: d.update(W, H)
        for d in drops_mg: d.update(W, H)
        for d in drops_bg: d.update(W, H)

        # Build frame
        frame = add_sway(base, t, strength=1.8)
        frame = add_wetness_shimmer(frame, t)

        # Rain layers: bg (faint) → mg → fg (bright)
        frame = draw_rain(frame, drops_bg, intensity=0.35)
        frame = draw_rain(frame, drops_mg, intensity=0.60)
        frame = draw_rain(frame, drops_fg, intensity=1.00)

        frame = frame.convert("RGB")
        frame.save(FRAMES / f"frame_{i:05d}.jpg", quality=92)

        if i % (FPS * 5) == 0:
            print(f"  {i}/{N_FRAMES} frames ({t:.0f}s)")

    print("Encoding video with ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "frame_%05d.jpg"),
        "-i", str(MUSIC),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=576:1024",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(OUT_MP4)
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    print(f"\n✅ Done → {OUT_MP4}  ({OUT_MP4.stat().st_size//1024//1024} MB)")
    print("Cleaning up frames...")
    shutil.rmtree(FRAMES)

if __name__ == "__main__":
    main()
