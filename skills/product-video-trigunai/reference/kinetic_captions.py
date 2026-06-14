#!/usr/bin/env python3
"""
kinetic_captions.py  —  BIG center scale-pop captions for ads.

The learning engine uses a calm line-reveal lower-third (caption_fx.py). Ads need
the opposite: huge, punchy, 1-3 words at a time that POP on the beat, parked in the
lower-third safe area, in the brand color. This renders an RGBA overlay clip you
composite over the scene (product_hero.compose_ad_scene caption_overlay=...).

Timing rule (engine §9): use faster-whisper for WORD TIMING, but the script text
for SPELLING (whisper drops diacritics / mangles brand names). So this takes the
already-correct caption text + the audio, aligns words to the audio, and animates.

Deps on EC2: pip install --break-system-packages pillow numpy faster-whisper
Font: Poppins/Montserrat Bold if present, else DejaVuSans-Bold (always in AMI).
"""
import os, subprocess, math
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W9, H9 = 1080, 1920
FONTS = [
    "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def _font(px):
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, px)
    return ImageFont.load_default()

def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

# ---- align caption words to the audio ----------------------------------------
def word_times(audio, caption_text):
    """
    Return [(word, start, end)] for the caption's words, timed to the audio.
    Uses faster-whisper word timestamps but REPLACES whisper's text with the
    provided caption words in order (script = source of truth for spelling).
    Falls back to even spacing if whisper is unavailable / counts mismatch.
    """
    words = caption_text.split()
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel("base", device="cpu", compute_type="int8")
        segs, info = m.transcribe(audio, word_timestamps=True)
        wt = [(w.start, w.end) for s in segs for w in (s.words or [])]
        if len(wt) >= len(words):
            wt = wt[:len(words)]
            return [(words[i], wt[i][0], wt[i][1]) for i in range(len(words))]
    except Exception:
        pass
    # even spacing fallback over the audio duration
    dur = _audio_dur(audio)
    step = dur / max(1, len(words))
    return [(w, i*step, (i+1)*step) for i, w in enumerate(words)]

def _audio_dur(audio):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", audio],
        capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 3.0

# ---- render the kinetic caption overlay --------------------------------------
def render_kinetic_captions(caption_text, audio, out, *, w=W9, h=H9, fps=30,
                            color="#FFFFFF", accent="#6C5CE7", group=2,
                            y_frac=0.72, max_px=150):
    """
    caption_text : the correct words (from the script, not whisper)
    audio        : this scene's frozen audio (drives timing + total duration)
    group        : words shown together per pop (1-3; 2 reads well on mobile)
    y_frac       : vertical center of the caption band (0.72 = lower third, safe)
    Writes an RGBA mp4 (yuva420p) you overlay in compose_ad_scene.
    """
    wt = word_times(audio, caption_text)
    dur = _audio_dur(audio)
    nfr = max(1, int(dur * fps))
    fg, ac = _hex(color), _hex(accent)
    tmp = "/tmp/kcap_frames"
    os.makedirs(tmp, exist_ok=True)
    os.system(f"rm -f {tmp}/*.png")

    # group words into chunks; each chunk shows from its first word's start
    chunks = []
    for i in range(0, len(wt), group):
        g = wt[i:i+group]
        chunks.append((" ".join(x[0] for x in g), g[0][1], g[-1][2]))

    cy = int(h * y_frac)
    for fi in range(nfr):
        t = fi / fps
        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        cur = next((c for c in chunks if c[1] <= t <= c[2] + 0.25), None)
        if cur:
            text, st, en = cur
            age = t - st
            # scale-pop: overshoot to 1.12 in 0.12s then settle to 1.0
            if age < 0.12:
                s = 1.0 + 0.12 * (age / 0.12)
            elif age < 0.22:
                s = 1.12 - 0.12 * ((age - 0.12) / 0.10)
            else:
                s = 1.0
            px = int(_fit(d, text, w * 0.86, max_px) * s)
            fnt = _font(px)
            bb = d.textbbox((0, 0), text, font=fnt)
            tw, th = bb[2]-bb[0], bb[3]-bb[1]
            x = (w - tw) // 2 - bb[0]
            y = cy - th // 2 - bb[1]
            # heavy stroke for legibility on any bg, accent for keyword punch
            d.text((x, y), text, font=fnt, fill=fg + (255,),
                   stroke_width=max(6, px//18), stroke_fill=(0, 0, 0, 230))
        frame.save(f"{tmp}/f{fi:05d}.png")

    subprocess.run(["ffmpeg", "-y", "-framerate", str(fps), "-i", f"{tmp}/f%05d.png",
                    "-c:v", "qtrle", "-pix_fmt", "argb", out], check=True)
    return out

def _fit(draw, text, max_w, max_px):
    """Largest font px that fits text within max_w."""
    px = max_px
    while px > 28:
        bb = draw.textbbox((0, 0), text, font=_font(px))
        if bb[2]-bb[0] <= max_w:
            return px
        px -= 6
    return px

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        render_kinetic_captions(sys.argv[1], sys.argv[2], sys.argv[3])
        print("wrote", sys.argv[3])
    else:
        print('usage: kinetic_captions.py "Caption text" scene_audio.mp3 out.mov')
