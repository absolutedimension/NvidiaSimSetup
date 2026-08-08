#!/usr/bin/env python3
"""Generate on-brand Google Ads image assets for the Acharya Patna campaigns.

Google Ads "image assets" (extensions) want a 1.91:1 landscape (1200x628) and a
1:1 square (1200x1200), PNG/JPG, <5 MB. Search ads don't REQUIRE images, but these
strengthen the ad and are reusable for Display/PMax later.

Output → creative/  (student_square.png, student_landscape.png, teacher_*.png)
Brand palette matches the live Acharya templates (cream + dark-gold).
"""
import os
from PIL import Image, ImageDraw, ImageFont

FONTS = "/System/Library/Fonts/Supplemental/"
SYS = "/System/Library/Fonts/"
GEORGIA_B = FONTS + "Georgia Bold.ttf"
ARIAL_B   = FONTS + "Arial Bold.ttf"
ARIAL     = FONTS + "Arial.ttf"
DEVA      = SYS + "Supplemental/Devanagari Sangam MN.ttc"

# brand palette (from lms/app/templates/*.html :root)
CREAM_TOP = (253, 246, 236)
CREAM_BOT = (247, 224, 200)
INK       = (42, 32, 24)
GOLD      = (194, 89, 31)
GOLD2     = (168, 72, 26)
GOLD_LT   = (232, 147, 74)
MUTED     = (122, 106, 87)
WHITE     = (255, 255, 255)


def f(path, size):
    return ImageFont.truetype(path, size)


def vgrad(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return base


def rrect(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..",
                          "brand_logo", "logo_chrome.png")
_LOGO = None


def mark(size):
    """Real brand mark — the gold triskelion — as a rounded app-icon tile."""
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(_LOGO_PATH).convert("RGB")
    tile = _LOGO.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(tile, (0, 0), mask)
    return out


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build(path, W, H, headline, sub, cta, accent_words=()):
    im = vgrad(W, H, CREAM_TOP, CREAM_BOT)
    d = ImageDraw.Draw(im)
    pad = int(W * 0.07)

    # brand lockup (mark + wordmark) top-left
    ms = int(H * 0.11)
    mk = mark(ms)
    im.paste(mk, (pad, pad), mk)
    d.text((pad + ms + int(ms * 0.34), pad + int(ms * 0.06)),
           "Acharya", font=f(GEORGIA_B, int(ms * 0.62)), fill=INK)
    d.text((pad + ms + int(ms * 0.34), pad + int(ms * 0.60)),
           "by TrigunAI", font=f(ARIAL, int(ms * 0.30)), fill=MUTED)

    # headline (serif, wrapped)
    hsize = int(H * 0.088) if W >= H else int(H * 0.062)
    hf = f(GEORGIA_B, hsize)
    max_w = W - 2 * pad
    lines = wrap(d, headline, hf, max_w)
    y = pad + ms + int(H * 0.06)
    for ln in lines:
        x = pad
        # word-level gold accenting
        for i, word in enumerate(ln.split()):
            token = word + (" " if i < len(ln.split()) - 1 else "")
            col = GOLD if word.strip(".,").lower() in accent_words else INK
            d.text((x, y), token, font=hf, fill=col)
            x += d.textlength(token, font=hf)
        y += int(hsize * 1.16)

    # subline
    if sub:
        sf = f(ARIAL, int(H * 0.036))
        y += int(H * 0.02)
        for ln in wrap(d, sub, sf, max_w):
            d.text((pad, y), ln, font=sf, fill=MUTED)
            y += int(H * 0.046)

    # CTA pill (bottom-left) + domain (bottom-right)
    cf = f(ARIAL_B, int(H * 0.040))
    cw = d.textlength(cta, font=cf)
    ch = int(H * 0.092)
    cx0, cy0 = pad, H - pad - ch
    rrect(d, [cx0, cy0, cx0 + cw + int(H * 0.09), cy0 + ch], int(ch / 2), GOLD)
    d.text((cx0 + int(H * 0.045), cy0 + (ch - int(H * 0.040) * 1.3) / 2),
           cta, font=cf, fill=WHITE)
    dom = "acharya.trigunai.com"
    df = f(ARIAL_B, int(H * 0.030))
    d.text((W - pad - d.textlength(dom, font=df), H - pad - int(H * 0.05)),
           dom, font=df, fill=GOLD2)

    im.save(path, "PNG")
    print("wrote", path, im.size)


import os
OUT = os.path.join(os.path.dirname(__file__), "creative")
os.makedirs(OUT, exist_ok=True)

# ---- STUDENT ----
S_HEAD = "Find your weak topics before the exam does"
S_SUB  = "Free adaptive JEE, NEET & board tests. See exactly what to revise next."
build(os.path.join(OUT, "student_landscape.png"), 1200, 628, S_HEAD, S_SUB,
      "Start free →", accent_words={"weak", "topics"})
build(os.path.join(OUT, "student_square.png"), 1200, 1200, S_HEAD, S_SUB,
      "Start free →", accent_words={"weak", "topics"})

# ---- TEACHER ----
T_HEAD = "You teach. Acharya tests & tracks."
T_SUB  = "Create a JEE/NEET test in seconds. Share one link. See who's weak in which topic."
build(os.path.join(OUT, "teacher_landscape.png"), 1200, 628, T_HEAD, T_SUB,
      "Set up free →", accent_words={"tests", "tracks."})
build(os.path.join(OUT, "teacher_square.png"), 1200, 1200, T_HEAD, T_SUB,
      "Set up free →", accent_words={"tests", "tracks."})
