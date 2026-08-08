#!/usr/bin/env python3
"""Branded showcase graphics for the Acharya Google Business Profile.
Square 1200x1200 (GBP displays square best). On-brand cream + dark-gold.
Honest product graphics — NOT fake photos of people/premises.
Output → creative/gbp/
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONTS = "/System/Library/Fonts/Supplemental/"
SYS = "/System/Library/Fonts/"
GEORGIA_B = FONTS + "Georgia Bold.ttf"
ARIAL_B = FONTS + "Arial Bold.ttf"
ARIAL = FONTS + "Arial.ttf"
DEVA = SYS + "Supplemental/Devanagari Sangam MN.ttc"

CREAM_TOP = (253, 246, 236); CREAM_BOT = (247, 224, 200)
INK = (42, 32, 24); GOLD = (194, 89, 31); GOLD2 = (168, 72, 26)
GOLD_LT = (232, 147, 74); MUTED = (122, 106, 87); WHITE = (255, 255, 255)


def f(p, s): return ImageFont.truetype(p, s)


def vgrad(w, h, top, bot):
    im = Image.new("RGB", (w, h), top); px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return im


_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..",
                          "brand_logo", "logo_chrome.png")
_LOGO = None


def mark(size):
    """Real brand mark — the gold triskelion — as a rounded app-icon tile."""
    global _LOGO
    if _LOGO is None:
        _LOGO = Image.open(_LOGO_PATH).convert("RGB")
    tile = _LOGO.resize((size, size), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(tile, (0, 0), m)
    return out


def wrap(d, text, font, mw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        tr = (cur + " " + w).strip()
        if d.textlength(tr, font=font) <= mw:
            cur = tr
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


W = 1200
OUT = os.path.join(os.path.dirname(__file__), "creative", "gbp")
os.makedirs(OUT, exist_ok=True)


def card(name, kicker, headline, sub, big=None, accent=()):
    im = vgrad(W, W, CREAM_TOP, CREAM_BOT)
    d = ImageDraw.Draw(im)
    pad = int(W * 0.10)

    # brand lockup centered top
    ms = int(W * 0.13)
    mk = mark(ms)
    im.paste(mk, ((W - ms) // 2, pad), mk)
    nf = f(GEORGIA_B, int(ms * 0.52))
    nb = d.textlength("Acharya", font=nf)
    d.text(((W - nb) / 2, pad + ms + int(W * 0.02)), "Acharya", font=nf, fill=INK)
    kf = f(ARIAL_B, int(W * 0.028))
    kw = d.textlength(kicker.upper(), font=kf)
    d.text(((W - kw) / 2, pad + ms + int(W * 0.10)), kicker.upper(), font=kf, fill=GOLD2)

    y = int(W * 0.42)
    if big:
        bsize = int(W * 0.20)                       # auto-fit: shrink until it fits the card width
        bf = f(GEORGIA_B, bsize)
        while d.textlength(big, font=bf) > W - 2 * pad and bsize > 40:
            bsize -= 6; bf = f(GEORGIA_B, bsize)
        bw = d.textlength(big, font=bf)
        d.text(((W - bw) / 2, y - int(W * 0.02)), big, font=bf, fill=GOLD)
        y += int(W * 0.20)

    hf = f(GEORGIA_B, int(W * 0.066))
    for ln in wrap(d, headline, hf, W - 2 * pad):
        words = ln.split(); tw = sum(d.textlength(w + " ", font=hf) for w in words)
        x = (W - tw) / 2
        for w in words:
            col = GOLD if w.strip(".,").lower() in accent else INK
            d.text((x, y), w + " ", font=hf, fill=col)
            x += d.textlength(w + " ", font=hf)
        y += int(W * 0.078)

    if sub:
        sf = f(ARIAL, int(W * 0.034))
        y += int(W * 0.02)
        for ln in wrap(d, sub, sf, W - 2 * pad):
            lw = d.textlength(ln, font=sf)
            d.text(((W - lw) / 2, y), ln, font=sf, fill=MUTED)
            y += int(W * 0.05)

    # footer domain
    df = f(ARIAL_B, int(W * 0.028))
    dom = "acharya.trigunai.com"
    d.text(((W - d.textlength(dom, font=df)) / 2, W - pad), dom, font=df, fill=GOLD2)

    p = os.path.join(OUT, name)
    im.save(p, "PNG"); print("wrote", p)


card("01_cover.png", "by TrigunAI", "AI exam practice & assessment",
     "JEE · NEET · Class 10 & 12 · Banking", accent={"exam", "practice"})
card("02_questionbank.png", "verified questions", "exam-pattern questions modelled on real papers",
     "JEE · NEET · Boards · Banking (IBPS/SBI/RRB)", big="1,29,000+", accent={"real", "papers"})
card("03_weaktopics.png", "for students", "Find your weak topics, not just a score",
     "Short adaptive tests that show what to revise next", accent={"weak", "topics"})
card("04_teachers.png", "for teachers & institutes", "One test. One link. Whole-class insights.",
     "See who is weak in which topic, automatically", accent={"link."})
card("05_free_bilingual.png", "free to start", "Practise free, in English or Hindi",
     "No password, no payment to begin", accent={"free"})
