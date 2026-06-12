"""
Slide Renderer Service.
Generates animated slide PNGs with particles, gradients, and text.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os
import random

W, H = 1920, 1080

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

COLORS = {
    "blue": (59, 130, 246),
    "green": (74, 222, 128),
    "red": (248, 113, 113),
    "amber": (251, 191, 36),
    "purple": (168, 85, 247),
    "white": (255, 255, 255),
}

BG_DARK = (10, 10, 26)
BG_NAVY = (18, 22, 48)


def _font(name, size):
    try:
        return ImageFont.truetype(name, max(1, int(size)))
    except:
        return ImageFont.load_default()


def _gradient_bg(img, c1=BG_DARK, c2=BG_NAVY):
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return draw


def _draw_particles(draw, count=80, seed=42):
    rng = random.Random(seed)
    for _ in range(count):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        brightness = rng.randint(20, 80)
        size = rng.uniform(1, 2.5)
        draw.ellipse([x-size, y-size, x+size, y+size],
                     fill=(brightness, brightness, int(brightness * 0.9)))


def _draw_glow(img, cx, cy, radius, color, alpha=25):
    draw = ImageDraw.Draw(img)
    for r in range(radius, 0, -4):
        intensity = int(alpha * (r / radius))
        c = (
            min(255, color[0] * intensity // 255),
            min(255, color[1] * intensity // 255),
            min(255, color[2] * intensity // 255),
        )
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)


def render_slide(title, body="", accent_color="blue", layout="center",
                 output_path="/tmp/slide.png", screenshot_path=None,
                 subtitle="", bullet_points=None, transparent=False):
    """
    Render a single slide PNG.

    Args:
        title: Main heading
        body: Optional body text
        accent_color: "blue", "green", "red", "amber", "purple"
        layout: "center", "left", "split", "bullets", "screenshot"
        output_path: Where to save
        screenshot_path: Optional screenshot image to embed
        subtitle: Optional subtitle under title
        bullet_points: List of strings for bullet layout
    """
    if transparent:
        # Transparent canvas so a shader background shows through. A soft dark
        # scrim keeps text readable over a bright/animated shader.
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        scrim = Image.new("RGBA", (W, H), (6, 8, 20, 115))
        img = Image.alpha_composite(img, scrim)
        draw = ImageDraw.Draw(img)
    else:
        img = Image.new("RGB", (W, H), BG_DARK)
        draw = _gradient_bg(img)
        _draw_particles(draw, count=100, seed=hash(title) % 10000)

    color = COLORS.get(accent_color, COLORS["blue"])

    if layout == "center":
        if not transparent:
            _draw_glow(img, W//2, H//2 - 50, 300, color, alpha=20)
        draw = ImageDraw.Draw(img)

        draw.text((W//2, H//2 - 60), title, fill=(255, 255, 255),
                  font=_font(FONT_BOLD, 64), anchor="mm")
        if subtitle:
            draw.text((W//2, H//2 + 20), subtitle, fill=color,
                      font=_font(FONT_REG, 32), anchor="mm")
        if body:
            draw.text((W//2, H//2 + 80), body, fill=(160, 160, 170),
                      font=_font(FONT_REG, 26), anchor="mm")

    elif layout == "left":
        draw.text((120, 100), title, fill=(255, 255, 255),
                  font=_font(FONT_BOLD, 52))
        if subtitle:
            draw.text((120, 170), subtitle, fill=color,
                      font=_font(FONT_REG, 28))
        y = 250
        if body:
            for line in body.split("\n"):
                draw.text((120, y), line, fill=(180, 180, 190),
                          font=_font(FONT_REG, 24))
                y += 38

    elif layout == "bullets":
        draw.text((W//2, 80), title, fill=(255, 255, 255),
                  font=_font(FONT_BOLD, 48), anchor="mm")
        if subtitle:
            draw.text((W//2, 130), subtitle, fill=color,
                      font=_font(FONT_REG, 26), anchor="mm")

        points = bullet_points or body.split("\n") if body else []
        y = 220
        for i, point in enumerate(points):
            if not point.strip():
                continue
            # Bullet dot
            draw.ellipse([180, y+10, 200, y+30], fill=color)
            draw.text((220, y+5), point.strip(), fill=(220, 220, 230),
                      font=_font(FONT_REG, 28))
            # Separator
            if i < len(points) - 1:
                draw.line([(220, y+60), (W-200, y+60)], fill=(30, 30, 50), width=1)
            y += 80

    elif layout == "split":
        # Left side: text, Right side: screenshot or colored box
        draw.text((100, 100), title, fill=(255, 255, 255),
                  font=_font(FONT_BOLD, 48))
        if subtitle:
            draw.text((100, 165), subtitle, fill=color,
                      font=_font(FONT_REG, 26))

        y = 240
        if body:
            for line in body.split("\n"):
                draw.text((100, y), line, fill=(180, 180, 190),
                          font=_font(FONT_REG, 22))
                y += 34

        # Right side
        rx, ry, rw, rh = 1000, 100, 820, 500
        if screenshot_path and os.path.exists(screenshot_path):
            ss = Image.open(screenshot_path).convert("RGB")
            ratio = min(rw / ss.width, rh / ss.height)
            ss = ss.resize((int(ss.width * ratio), int(ss.height * ratio)), Image.LANCZOS)
            px = rx + (rw - ss.width) // 2
            py = ry + (rh - ss.height) // 2
            # Border
            draw.rounded_rectangle([px-3, py-3, px+ss.width+3, py+ss.height+3],
                                   radius=8, outline=color, width=2)
            img.paste(ss, (px, py))
        else:
            draw.rounded_rectangle([rx, ry, rx+rw, ry+rh], radius=16,
                                   fill=(20, 22, 40), outline=(40, 40, 60), width=2)

    elif layout == "screenshot":
        draw.text((W//2, 50), title, fill=(255, 255, 255),
                  font=_font(FONT_BOLD, 40), anchor="mm")
        if subtitle:
            draw.text((W//2, 95), subtitle, fill=color,
                      font=_font(FONT_REG, 22), anchor="mm")

        if screenshot_path and os.path.exists(screenshot_path):
            ss = Image.open(screenshot_path).convert("RGB")
            max_w, max_h = W - 200, H - 200
            ratio = min(max_w / ss.width, max_h / ss.height)
            ss = ss.resize((int(ss.width * ratio), int(ss.height * ratio)), Image.LANCZOS)
            px = (W - ss.width) // 2
            py = 140
            draw.rounded_rectangle([px-4, py-4, px+ss.width+4, py+ss.height+4],
                                   radius=10, outline=color, width=3)
            img.paste(ss, (px, py))

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    return {"path": output_path}
