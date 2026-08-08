#!/usr/bin/env python3
"""
Acharya Quiz-Video pipeline  —  content JSON  ->  narrated MP4 with countdown timer.

New sibling to the production-video pipeline, purpose-built for the assessment engine:
exam-prep quiz shorts that "hold the student" with a ticking countdown, then reveal
the answer + a one-line explanation.

  python3 make_quiz_video.py content/units_measurements.json out/quiz_sample.mp4

Self-contained on a Mac: PIL (frames) + macOS `say` (Rishi en-IN narration) +
numpy (audio mix) + ffmpeg (encode/mux). No GPU / EC2 needed for a sample.
Format: vertical 1080x1920 @ 30fps (Shorts / Reels / WhatsApp status).
"""
import sys, os, json, math, wave, subprocess, tempfile, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------- config ----------
W, H, FPS = 1080, 1920, 30
SR = 44100
VOICE = "Rishi"                 # en-IN; falls back to Samantha
F_SUP = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"   # has ⁻¹ ⁻²
F_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
F_BLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# Acharya dark-gold palette (premium video variant of the app tokens)
BG_TOP  = (23, 17, 11)
BG_BOT  = (38, 27, 16)
GOLD    = (232, 165, 75)
GOLD_DK = (194, 89, 31)
INK     = (243, 233, 216)
MUTED   = (183, 164, 136)
CARD    = (42, 32, 21)
CARD_BD = (64, 49, 28)
GREEN   = (47, 169, 104)
GREEN_BD= (60, 200, 128)
RED_DIM = (120, 70, 55)

# ---------- font cache ----------
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# ---------- background (built once) ----------
def make_bg():
    top = np.array(BG_TOP, np.float32); bot = np.array(BG_BOT, np.float32)
    ramp = np.linspace(0, 1, H)[:, None]
    grad = (top[None, :] * (1 - ramp) + bot[None, :] * ramp).astype(np.uint8)
    img = np.repeat(grad[:, None, :], W, axis=1)
    bg = Image.fromarray(img, "RGB")
    d = ImageDraw.Draw(bg, "RGBA")
    # soft gold vignette glow top-center
    for r, a in [(700, 10), (500, 12), (320, 16)]:
        d.ellipse([W//2 - r, 180 - r, W//2 + r, 180 + r], fill=(232, 165, 75, a))
    return bg
BG = make_bg()

def new_frame():
    return BG.copy()

def draw_header(d, sub, chap):
    # gold diamond brandmark (polygon, not a glyph)
    cx, cy, s = 92, 96, 22
    d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)],
              fill=GOLD, outline=GOLD_DK)
    d.text((128, 66), "ACHARYA", font=font(F_BLD, 52), fill=GOLD)
    d.text((70, 150), f"{sub}  ·  {chap}", font=font(F_REG, 34), fill=MUTED)
    d.line([70, 205, W - 70, 205], fill=CARD_BD, width=2)

def qnum_badge(d, n, total):
    d.rounded_rectangle([70, 240, 250, 320], radius=18, fill=GOLD_DK)
    d.text((92, 254), f"Q{n}", font=font(F_BLD, 50), fill=(255, 245, 235))
    d.text((272, 262), f"of {total}", font=font(F_REG, 40), fill=MUTED)

def draw_question(d, qtext, y=360):
    lines = wrap(d, qtext, font(F_BLD, 62), W - 150)
    for ln in lines:
        d.text((70, y), ln, font=font(F_BLD, 62), fill=INK)
        y += 78
    return y + 20

def option_boxes(d, options, y0, reveal=None):
    """reveal=None during quiz; reveal=idx to highlight the correct option green."""
    labels = "ABCD"
    x, w = 70, W - 140
    boxh, gap = 150, 34
    for i, opt in enumerate(options):
        y = y0 + i * (boxh + gap)
        if reveal is not None and i == reveal:
            fill, bd, tcol, lcol = (28, 66, 46), GREEN_BD, (223, 247, 233), GREEN
        else:
            fill, bd, tcol, lcol = CARD, CARD_BD, INK, GOLD
        d.rounded_rectangle([x, y, x + w, y + boxh], radius=26, fill=fill,
                            outline=bd, width=3)
        # letter chip
        d.rounded_rectangle([x + 26, y + 34, x + 108, y + 116], radius=18,
                            fill=lcol if reveal is None or i != reveal else GREEN)
        chipcol = (30, 22, 12) if (reveal is None or i != reveal) else (240, 255, 246)
        d.text((x + 47, y + 46), labels[i], font=font(F_BLD, 60), fill=chipcol)
        # option text (unicode font for ⁻¹ ⁻²), vertically centred, wrap if long
        of = font(F_SUP, 50)
        olines = wrap(d, opt, of, w - 190)
        oy = y + boxh//2 - (len(olines) * 58)//2
        for ln in olines:
            d.text((x + 140, oy), ln, font=of, fill=tcol)
            oy += 58
        if reveal is not None and i == reveal:
            d.text((x + w - 96, y + 40), "✓", font=font(F_SUP, 78), fill=GREEN_BD)
    return y0 + len(options) * (boxh + gap)

def draw_timer(d, cx, cy, r, frac, secs_left):
    """frac 1->0 depletes the arc; number ticks down."""
    # track
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CARD_BD, width=16)
    # arc (start top, clockwise)
    start = -90
    end = start + 360 * frac
    col = GREEN_BD if secs_left > 5 else (GOLD if secs_left > 3 else (214, 96, 62))
    if frac > 0.001:
        d.arc([cx - r, cy - r, cx + r, cy + r], start, end, fill=col, width=16)
    nf = font(F_BLD, 150)
    txt = str(secs_left)
    tw = d.textlength(txt, font=nf)
    d.text((cx - tw/2, cy - 108), txt, font=nf, fill=col)
    lf = font(F_REG, 34)
    lw = d.textlength("seconds", font=lf)
    d.text((cx - lw/2, cy + 66), "seconds", font=lf, fill=MUTED)

def cta_bar(d, text):
    d.rounded_rectangle([70, H - 190, W - 70, H - 90], radius=28,
                        fill=GOLD_DK)
    tf = font(F_BLD, 46)
    tw = d.textlength(text, font=tf)
    d.text((W/2 - tw/2, H - 168), text, font=tf, fill=(255, 245, 235))

# ---------- audio helpers ----------
def sine(freq, dur, vol=0.5, decay=True):
    n = int(SR * dur)
    t = np.arange(n) / SR
    wv = np.sin(2 * math.pi * freq * t)
    env = np.exp(-t * (6 if decay else 0)) if decay else np.ones(n)
    return (wv * env * vol).astype(np.float32)

def two_tone(f1, f2, dur, vol=0.5):
    a = sine(f1, dur/2, vol); b = sine(f2, dur/2, vol)
    return np.concatenate([a, b])

def buzzer(dur=0.5, vol=0.5):
    n = int(SR * dur); t = np.arange(n) / SR
    wv = 0.6*np.sin(2*math.pi*160*t) + 0.4*np.sin(2*math.pi*180*t)
    env = np.minimum(1, np.minimum(t*20, (dur - t)*20))
    return (wv * env * vol).astype(np.float32)

def read_wav_mono(path):
    with wave.open(path, "rb") as wf:
        n = wf.getnframes(); sw = wf.getsampwidth(); ch = wf.getnchannels()
        raw = wf.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16 if sw == 2 else np.uint8).astype(np.float32)
    if sw == 2: a /= 32768.0
    else: a = (a - 128) / 128.0
    if ch == 2: a = a.reshape(-1, 2).mean(axis=1)
    return a

def say_clip(text, tmpdir, idx):
    aiff = os.path.join(tmpdir, f"n{idx}.aiff")
    wavp = os.path.join(tmpdir, f"n{idx}.wav")
    v = VOICE
    if subprocess.call(["say", "-v", v, "-o", aiff, text],
                       stderr=subprocess.DEVNULL) != 0:
        subprocess.check_call(["say", "-v", "Samantha", "-o", aiff, text])
    subprocess.check_call(["ffmpeg", "-y", "-i", aiff, "-ar", str(SR), "-ac", "1",
                           wavp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a = read_wav_mono(wavp)
    return a, len(a) / SR

# ---------- main build ----------
def build(content_path, out_path):
    data = json.load(open(content_path))
    qs = data["questions"]
    TIMER = int(data.get("timer_seconds", 10))
    sub, chap = data["subject"], data["chapter"]
    cta = data.get("cta", "Practise on Acharya")

    tmp = tempfile.mkdtemp(prefix="quizvid_")
    frames_dir = os.path.join(tmp, "frames"); os.makedirs(frames_dir)

    # --- pre-render all narration so segment lengths can adapt to speech ---
    nidx = 0
    def narr(text):
        nonlocal nidx
        a, dur = say_clip(text, tmp, nidx); nidx += 1
        return {"aud": a, "dur": dur}
    intro_n = narr(data.get("intro_voice", "Can you beat the timer?"))
    for q in qs:
        q["_nq"] = narr(q["voice_q"])
        q["_na"] = narr(q["voice_a"])
    outro_n = narr(data.get("outro_voice", "Practise on Acharya."))

    # --- timeline: list of segments {kind, dur, ...} ---
    segs = []
    segs.append({"kind": "intro", "dur": max(3.0, intro_n["dur"] + 0.6)})
    for i, q in enumerate(qs):
        segs.append({"kind": "qintro", "dur": max(2.0, q["_nq"]["dur"] + 0.5), "qi": i})
        segs.append({"kind": "count", "dur": float(TIMER), "qi": i})
        segs.append({"kind": "timesup", "dur": 0.9, "qi": i})
        segs.append({"kind": "reveal", "dur": max(4.5, q["_na"]["dur"] + 1.2), "qi": i})
    segs.append({"kind": "outro", "dur": max(4.0, outro_n["dur"] + 0.8)})

    # absolute start times
    t = 0.0
    for s in segs:
        s["t0"] = t; t += s["dur"]
    total = t
    total_frames = int(round(total * FPS))
    print(f"Total {total:.1f}s  ·  {total_frames} frames  ·  {len(qs)} questions")

    # --- audio timeline (numpy mix) ---
    audio = np.zeros(int(total * SR) + SR, np.float32)
    def place(clip, at):
        i = int(at * SR); j = min(i + len(clip), len(audio))
        audio[i:j] += clip[: j - i]
    tick     = sine(1250, 0.05, 0.35)
    tick_hot = sine(1650, 0.07, 0.5)
    ding     = two_tone(880, 1320, 0.34, 0.5)
    buzz     = buzzer(0.5, 0.45)
    for s in segs:
        if s["kind"] == "intro": place(intro_n["aud"], s["t0"] + 0.3)
        elif s["kind"] == "qintro": place(qs[s["qi"]]["_nq"]["aud"], s["t0"] + 0.25)
        elif s["kind"] == "count":
            for k in range(TIMER):
                place(tick_hot if (TIMER - k) <= 3 else tick, s["t0"] + k)
        elif s["kind"] == "timesup": place(buzz, s["t0"])
        elif s["kind"] == "reveal":
            place(ding, s["t0"]); place(qs[s["qi"]]["_na"]["aud"], s["t0"] + 0.45)
        elif s["kind"] == "outro": place(outro_n["aud"], s["t0"] + 0.3)
    peak = np.max(np.abs(audio)) or 1.0
    audio = (audio / peak * 0.92)
    audio_i16 = (audio * 32767).astype(np.int16)
    audio_path = os.path.join(tmp, "audio.wav")
    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(audio_i16.tobytes())

    # --- render frames ---
    def seg_at(fi):
        tt = fi / FPS
        for s in segs:
            if s["t0"] <= tt < s["t0"] + s["dur"]:
                return s, (tt - s["t0"]) / s["dur"], tt - s["t0"]
        return segs[-1], 1.0, segs[-1]["dur"]

    for fi in range(total_frames):
        s, prog, local = seg_at(fi)
        img = new_frame(); d = ImageDraw.Draw(img, "RGBA")
        kind = s["kind"]
        if kind == "intro":
            f1 = font(F_BLD, 92)
            d.text((70, 520), sub.upper(), font=f1, fill=GOLD)
            f2 = font(F_BLD, 120)
            lines = wrap(d, chap, f2, W - 140)
            yy = 640
            for ln in lines:
                d.text((70, yy), ln, font=f2, fill=INK); yy += 140
            d.text((70, yy + 30), data.get("topic_line", ""), font=font(F_REG, 44), fill=MUTED)
            # pulsing prompt
            a = int(140 + 100 * abs(math.sin(local * 3)))
            pf = font(F_BLD, 60)
            d.text((70, 1180), "Beat the timer!", font=pf, fill=(232, 165, 75, a))
            draw_header(d, sub, chap)
            cta_bar(d, cta)
        elif kind in ("qintro", "count", "timesup"):
            q = qs[s["qi"]]
            draw_header(d, sub, chap)
            qnum_badge(d, s["qi"] + 1, len(qs))
            oy = draw_question(d, q["q"], 360)
            # options fade in during qintro
            option_boxes(d, q["options"], oy + 10, reveal=None)
            if kind == "count":
                secs_left = max(0, int(math.ceil(s["dur"] - local - 1e-6)))
                secs_left = min(TIMER, max(1, secs_left))
                frac = max(0.0, 1 - local)
                draw_timer(d, W//2, H - 340, 190, frac, secs_left)
            elif kind == "timesup":
                blink = (int(local * 8) % 2 == 0)
                col = (214, 96, 62) if blink else (240, 130, 90)
                tf = font(F_BLD, 110)
                tw = d.textlength("TIME'S UP!", font=tf)
                d.text((W/2 - tw/2, H - 430), "TIME'S UP!", font=tf, fill=col)
            else:
                cta_hint = font(F_REG, 40)
                d.text((70, H - 300), "Read fast — timer starts now…",
                       font=cta_hint, fill=MUTED)
        elif kind == "reveal":
            q = qs[s["qi"]]
            draw_header(d, sub, chap)
            qnum_badge(d, s["qi"] + 1, len(qs))
            oy = draw_question(d, q["q"], 360)
            oy2 = option_boxes(d, q["options"], oy + 10, reveal=q["answer"])
            # explanation card
            ey = oy2 + 40
            elines = wrap(d, "Why: " + q["explain"], font(F_SUP, 44), W - 210)
            eh = 60 + len(elines) * 56
            d.rounded_rectangle([70, ey, W - 70, ey + eh], radius=24,
                                fill=(30, 40, 30), outline=GREEN_BD, width=2)
            yy = ey + 28
            for ln in elines:
                d.text((104, yy), ln, font=font(F_SUP, 44), fill=(210, 235, 218))
                yy += 56
        elif kind == "outro":
            draw_header(d, sub, chap)
            f2 = font(F_BLD, 96)
            d.text((70, 620), "Nice work.", font=f2, fill=INK)
            lines = wrap(d, data.get("outro_voice", ""), font(F_REG, 58), W - 150)
            yy = 780
            for ln in lines:
                d.text((70, yy), ln, font=font(F_REG, 58), fill=MUTED); yy += 74
            cta_bar(d, cta)
        img.save(os.path.join(frames_dir, f"{fi:06d}.png"))
        if fi % 60 == 0:
            print(f"  frame {fi}/{total_frames}")

    # --- encode + mux ---
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    subprocess.check_call([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "%06d.png"),
        "-i", audio_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
        "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
        "-shortest", out_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n✅  {out_path}")

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "content/units_measurements.json"
    o = sys.argv[2] if len(sys.argv) > 2 else "out/quiz_sample.mp4"
    build(c, o)
