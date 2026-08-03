#!/usr/bin/env python3
"""
Treasure Trackers — KIDS quiz-video engine (ICSE Grade 3).  content JSON -> narrated MP4.

A cartoon, treasure-hunt spin on the Acharya quiz engine, tuned for young children:
  • BRIGHT treasure-island look  — sky + sun + drifting clouds + grassy hill
  • CARTOON MASCOT               — an emoji fox (🦊) that bobs and cheers (Apple Color Emoji)
  • GEM PROGRESS                 — collect one 💎 per question, on the way to the treasure 🏆
  • KIND reveals                 — the correct answer is always celebrated & repeated (no shaming)
  • FRIENDLY timer               — slower, playful countdown
  • Picture prompts              — a big contextual emoji per question

  python3 make_kids_quiz_video.py content/mult_mountain_en.json out/mult_mountain.mp4

Self-contained on a Mac: PIL + edge-tts (needs internet) + numpy + ffmpeg. Vertical 1080x1920 @30.
"""
import sys, os, json, math, wave, subprocess, tempfile, shutil, asyncio
import numpy as np
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- config ----------
W, H, FPS = 1080, 1920, 30
SR = 44100
VOICE = "en-IN-NeerjaExpressiveNeural"

# ---- cross-platform font resolution (bundled -> macOS -> Linux) ----
_BASE = os.path.dirname(os.path.abspath(__file__))
def _pick(*cands):
    for p in cands:
        if p and os.path.exists(p): return p
    return cands[-1]
F_RND = _pick(os.path.join(_BASE, "assets", "fonts", "kid_rounded.ttf"),
              "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
F_BLD = _pick(os.path.join(_BASE, "assets", "fonts", "kid_rounded.ttf"),
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
F_REG = _pick("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
EMOJI = _pick("/System/Library/Fonts/Apple Color Emoji.ttc")   # macOS only; EC2 uses baked PNGs

# BRIGHT kids palette
SKY_TOP = (120, 200, 255)
SKY_BOT = (196, 232, 255)
GRASS   = (128, 206, 110)
GRASS_D = (96, 178, 88)
SUN     = (255, 214, 92)
INK     = (38, 52, 84)          # deep friendly navy
CARD    = (255, 255, 255)
GOLD    = (255, 176, 40)
GOLD_D  = (232, 146, 20)
GREEN   = (74, 200, 122)
GREEN_D = (44, 168, 96)
GREEN_BG= (226, 248, 234)
RED     = (240, 120, 110)
OPT_COL = [(94, 170, 255), (255, 150, 120), (120, 205, 140), (196, 150, 240)]  # blue/orange/green/purple
OPT_DK  = [(58, 132, 220), (224, 112, 84), (78, 168, 100), (156, 110, 206)]

_fc = {}
def font(path, size, index=0):
    k = (path, size, index)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size, index=index)
    return _fc[k]
def fh(sz): return font(F_RND, sz)          # headings / bold
def fo(sz): return font(F_RND, sz)          # options / body (rounded everywhere for kids)

# ---------- emoji rendering (Apple Color Emoji has fixed bitmap strikes; 160 is valid, 137 is NOT) ----------
EMOJI_STRIKE = 160
_ec = {}
def emoji_img(ch, size):
    k = (ch, size)
    if k in _ec: return _ec[k]
    ef = font(EMOJI, EMOJI_STRIKE)
    im = Image.new("RGBA", (EMOJI_STRIKE, EMOJI_STRIKE), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=ef, embedded_color=True)
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    im = im.resize((size, size), Image.LANCZOS)
    _ec[k] = im
    return im
def _emoji_key(ch):
    return "-".join(f"{ord(c):x}" for c in ch)

def draw_emoji(img, ch, cx, cy, size):
    # 1) prefer a PRE-BAKED PNG (portable: works on Linux/EC2 with no emoji font)
    try:
        p = os.path.join(_BASE, "assets", "emoji", _emoji_key(ch) + ".png")
        k = ("baked", p, size)
        if k not in _ec:
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                h = size; w = max(1, int(im.size[0] * h / im.size[1]))
                _ec[k] = im.resize((w, h), Image.LANCZOS)
            else:
                _ec[k] = None
        em = _ec[k]
        if em is not None:
            img.paste(em, (int(cx - em.size[0] / 2), int(cy - em.size[1] / 2)), em); return
    except Exception:
        pass
    # 2) fall back to the system color-emoji font (macOS)
    try:
        em = emoji_img(ch, size)
    except Exception:
        return
    img.paste(em, (int(cx - em.size[0] / 2), int(cy - em.size[1] / 2)), em)

# ---------- character sprites (hand-drawn JJ / Mikey PNGs) ----------
_BASE = os.path.dirname(os.path.abspath(__file__))
_sc = {}
def sprite(name, h):
    k = (name, h)
    if k in _sc: return _sc[k]
    im = Image.open(os.path.join(_BASE, "assets", name)).convert("RGBA")
    w = max(1, int(im.size[0] * h / im.size[1]))
    im = im.resize((w, h), Image.LANCZOS); _sc[k] = im; return im
def draw_char(img, ctx, who, cx, cy, h):
    """draw JJ/Mikey as a PNG sprite if provided, else fall back to the emoji. cy = BOTTOM anchor."""
    name = ctx.get(who + "_img")
    if name:
        try:
            s = sprite(name, h)
            img.paste(s, (int(cx - s.size[0] / 2), int(cy - s.size[1])), s); return
        except Exception:
            pass
    draw_emoji(img, ctx.get("mascot" if who == "m1" else "mascot2", "🦊"), cx, cy - h/2, h)

# ---------- TrigunAI branding (ownership / copyright) ----------
_lc = {}
def _logo(name, w, alpha=255):
    k = (name, w, alpha)
    if k in _lc: return _lc[k]
    try:
        im = Image.open(os.path.join(_BASE, "assets", name)).convert("RGBA")
    except Exception:
        _lc[k] = None; return None
    h = max(1, int(im.size[1] * w / im.size[0]))
    im = im.resize((w, h), Image.LANCZOS)
    if alpha < 255:
        a = im.split()[3].point(lambda p: int(p * alpha / 255)); im.putalpha(a)
    _lc[k] = im; return im
def draw_logo(img, name, cx, cy, w, alpha=255):
    im = _logo(name, w, alpha)
    if im is not None:
        img.paste(im, (int(cx - im.size[0] / 2), int(cy - im.size[1] / 2)), im)
def watermark(img):
    """small TrigunAI mark, bottom-left — a light ownership stamp on every frame."""
    draw_logo(img, "trigunai_mark.png", 96, H - 74, 92, alpha=120)

def draw_char_live(img, ctx, who, cx, ground_y, h, local, excited=False, ph=0.0):
    """ALIVE version: breathe+sway while idle, hop+wiggle when excited. Feet anchored to ground_y."""
    name = ctx.get(who + "_img")
    if not name:
        draw_emoji(img, ctx.get("mascot" if who == "m1" else "mascot2", "🦊"), cx, ground_y - h/2, h)
        return
    try:
        s = sprite(name, h)
    except Exception:
        return
    t = local + ph
    if excited:
        hop = abs(math.sin(t * 7.0)) * (h * 0.12)      # happy bounce
        ang = math.sin(t * 13.0) * 7.0                 # wiggle
    else:
        hop = (math.sin(t * 2.3) * (h * 0.018))        # gentle breathing bob
        ang = math.sin(t * 1.5) * 2.5                  # slow sway
    r = s.rotate(ang, resample=Image.BICUBIC, expand=True)
    img.paste(r, (int(cx - r.size[0] / 2), int(ground_y - hop - r.size[1])), r)

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines
def ctext(d, cx, y, s, fnt, fill):
    d.text((cx - d.textlength(s, font=fnt) / 2, y), s, font=fnt, fill=fill)
def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ---------- background (sky + sun + grass, with drifting clouds loop) ----------
BG_LOOP_N = 150   # 5s cloud drift loop
def build_bg_loop():
    ys = np.linspace(0, 1, H)[:, None, None]
    top = np.array(SKY_TOP, np.float32); bot = np.array(SKY_BOT, np.float32)
    sky = top * (1 - ys) + bot * ys
    base = np.repeat(sky, W, axis=1).astype(np.float32)
    grass_y = int(H * 0.72)
    yy = np.arange(H)[:, None]
    # rolling grassy hill
    hill = grass_y + (28 * np.sin(np.linspace(0, math.pi, W))).astype(int)[None, :]
    mask = yy >= hill
    g = np.array(GRASS, np.float32)
    base[mask] = g
    frames = []
    static = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    # sun (static, top-left) baked once
    sd = ImageDraw.Draw(static, "RGBA")
    sd.ellipse([70, 90, 250, 270], fill=SUN)
    sd.ellipse([70, 90, 250, 270], outline=(255, 232, 150, 120), width=14)
    clouds = [(0.15, 0.22, 150, 60), (0.62, 0.14, 190, 70),
              (0.80, 0.34, 130, 52), (0.35, 0.40, 110, 44)]
    for f in range(BG_LOOP_N):
        im = static.copy(); d = ImageDraw.Draw(im, "RGBA")
        drift = (f / BG_LOOP_N) * 120
        for cx, cy, cw, chh in clouds:
            x = (cx * W + drift) % (W + 260) - 130; y = cy * H
            for dx, dy, r in [(0, 20, chh), (cw*0.4, 0, chh*1.1), (cw*0.8, 22, chh*0.9), (cw*0.4, 30, chh)]:
                d.ellipse([x+dx-r, y+dy-r, x+dx+r, y+dy+r], fill=(255, 255, 255, 235))
        frames.append(im)
    return frames

# ---------- brand / mascot ----------
def bob(local, amp=10, spd=2.4):
    return amp * math.sin(local * spd)

def header(img, d, ctx):
    d.rounded_rectangle([54, 40, W - 54, 150], radius=40, fill=(255, 255, 255, 220))
    draw_char(img, ctx, "m1", 112, 150, 118)
    d.text((196, 52), ctx["series"].upper(), font=fh(46), fill=GOLD_D)
    d.text((198, 104), f"{ctx['sub']}  •  {ctx['chap']}", font=fo(34), fill=INK)

def gem_bar(img, d, earned, total):
    """row of gem slots near the top; filled = collected so far."""
    slot = 96; gap = 20; tw = total * slot + (total - 1) * gap
    x0 = W / 2 - tw / 2; y = 186
    d.rounded_rectangle([x0 - 26, y - 12, x0 + tw + 26, y + slot + 12], radius=34,
                        fill=(255, 255, 255, 170))
    for i in range(total):
        cx = x0 + i * (slot + gap) + slot / 2; cy = y + slot / 2
        if i < earned:
            draw_emoji(img, "💎", cx, cy, 78)
        else:
            d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], outline=(150, 170, 200, 200), width=6)

def kid_card(d, box, radius, fill, outline, width=6):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 5, y0 + 8, x1 + 5, y1 + 8], radius=radius, fill=(40, 60, 100, 40))
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def timer_ring(img, d, cx, cy, r, frac, secs):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 210))
    col = GREEN if secs > 4 else (GOLD if secs > 2 else RED)
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=col, width=22)
    nf = fh(150)
    ctext(d, cx, cy - 108, str(secs), nf, col)
    ctext(d, cx, cy + 66, "seconds", fo(34), INK)

# ---------- celebration ----------
def celebrate(d, origin, local, dur=1.9):
    ox, oy = origin
    rng = np.random.default_rng(7)
    cols = [(255,120,110),(94,170,255),(120,205,140),(255,196,90),(196,150,240),(255,160,120)]
    for i in range(90):
        ang = rng.uniform(0, 2*math.pi); spd = rng.uniform(300, 860)
        vx, vy = math.cos(ang)*spd, math.sin(ang)*spd - 260; g = 900
        px = ox + vx*local; py = oy + vy*local + 0.5*g*local*local
        life = rng.uniform(1.2, 1.9)
        if local > life: continue
        al = int(255*max(0, 1-local/life)); sz = rng.uniform(10, 22)
        spin = rng.uniform(0, 2*math.pi) + local*rng.uniform(-6, 6)
        c, s = math.cos(spin), math.sin(spin)
        pts = [(-sz,-sz*0.6),(sz,-sz*0.6),(sz,sz*0.6),(-sz,sz*0.6)]
        d.polygon([(px+x*c-y*s, py+x*s+y*c) for x, y in pts], fill=cols[i % len(cols)]+(al,))

# ---------- audio ----------
def sine(freq, dur, vol=0.5, decay=6):
    n = int(SR*dur); t = np.arange(n)/SR
    env = np.exp(-t*decay) if decay else np.ones(n)
    return (np.sin(2*math.pi*freq*t)*env*vol).astype(np.float32)
def chime(vol=0.55):
    out = sine(880, 0.5, vol, 5) + sine(1320, 0.5, vol*0.7, 5)
    hi = sine(1760, 0.3, vol*0.4, 6); out[:len(hi)] += hi
    return out
def sparkle(vol=0.5):
    out = np.zeros(int(SR*0.9), np.float32)
    for i, fr in enumerate([784, 988, 1319, 1568, 2093]):
        c = sine(fr, 0.5, vol*0.5, 7); at = int(i*0.06*SR)
        out[at:at+len(c)] += c[:len(out)-at]
    return out
def pop(vol=0.5):   # cheerful rising "boing" for the countdown-end (not a scary buzz)
    n=int(SR*0.35); t=np.arange(n)/SR
    f=400+500*t/0.35; env=np.minimum(1, np.minimum(t*20,(0.35-t)*20))
    return (np.sin(2*math.pi*f*t)*env*vol).astype(np.float32)
def soft_tick(vol=0.24): return sine(700, 0.05, vol, 30)
def hot_tick(vol=0.36):  return sine(940, 0.06, vol, 26)

def read_wav_mono(p):
    with wave.open(p,"rb") as wf:
        n=wf.getnframes(); sw=wf.getsampwidth(); ch=wf.getnchannels(); raw=wf.readframes(n)
    a=np.frombuffer(raw, np.int16 if sw==2 else np.uint8).astype(np.float32)
    if sw==2: a/=32768.0
    else: a=(a-128)/128.0
    if ch==2: a=a.reshape(-1,2).mean(1)
    return a
async def _tts(text, path, rate, pitch):
    await edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch).save(path)
def say_clip(text, tmp, i, rate, pitch):
    mp3=os.path.join(tmp,f"n{i}.mp3"); wavp=os.path.join(tmp,f"n{i}.wav")
    asyncio.run(_tts(text, mp3, rate, pitch))
    subprocess.check_call(["ffmpeg","-y","-i",mp3,"-ar",str(SR),"-ac","1",wavp],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a=read_wav_mono(wavp); return a, len(a)/SR

# ---------- question renderer ----------
def render_q(img, d, q, phase, local, seg_dur, TIMER, ctx, qi, nq):
    header(img, d, ctx)
    earned = qi + (1 if phase == "reveal" else 0)
    gem_bar(img, d, earned, nq)
    # contextual picture + question
    emo = q.get("emoji")
    qy = 330
    if emo:
        draw_emoji(img, emo, W/2, qy + 40, 120); qy += 120
    qf = fh(58)
    for ln in wrap(d, q["q"], qf, W-160):
        ctext(d, W/2, qy, ln, qf, INK); qy += 72
    qy += 12
    # options (2x2 friendly grid)
    labels = ["A", "B", "C", "D"]; reveal = phase == "reveal"
    ox = 70; ow = (W - 70*2 - 40) / 2; oh = 190; gapx = 40; gapy = 34
    oy0 = qy
    for i, opt in enumerate(q["options"]):
        r, c = divmod(i, 2)
        bx = ox + c*(ow+gapx); by = oy0 + r*(oh+gapy)
        correct = reveal and i == q["answer"]
        if correct:
            kid_card(d, [bx, by, bx+ow, by+oh], 34, GREEN_BG, GREEN, 8)
            chipc = GREEN
        else:
            dim = reveal and not correct
            base = OPT_COL[i]; edge = OPT_DK[i]
            if dim: base = tuple(int(v*0.55+255*0.45) for v in base)
            kid_card(d, [bx, by, bx+ow, by+oh], 34, CARD, edge, 8)
            chipc = base
        # answer chip
        d.rounded_rectangle([bx+22, by+22, bx+96, by+96], radius=20, fill=chipc)
        ctext(d, bx+59, by+34, labels[i], fh(52), (255,255,255))
        of = fh(70)
        ctext(d, bx+ow/2+30, by+oh/2-40, opt, of, INK)
        if correct:
            draw_emoji(img, "✅", bx+ow-46, by+46, 64)
    ylast = oy0 + 2*(oh+gapy)
    # JJ + Mikey standing on the grass, ALIVE — they hop & wiggle on the reveal
    gy = int(H*0.72)
    excited = phase == "reveal" and local < 3.2
    draw_char_live(img, ctx, "m1", W-215, gy+48, 235, local, excited, ph=0.0)
    if ctx.get("m2_img") or ctx.get("mascot2"):
        draw_char_live(img, ctx, "m2", W-92, gy+40, 198, local, excited, ph=0.5)
    if phase == "count":
        secs = min(TIMER, max(1, int(math.ceil(seg_dur-local-1e-6))))
        timer_ring(img, d, 200, int(H*0.72)-70, 130, max(0, 1-local/seg_dur), secs)
    elif phase == "qintro":
        ctext(d, W/2, ylast+20, "Think it through…", fo(42), INK)
    elif phase == "timesup":
        ctext(d, W/2, ylast+6, "Let's see!", fh(72), GOLD_D)
    elif phase == "reveal":
        ey = ylast + 8
        el = wrap(d, q["explain"], fo(44), W-220)
        eh = 46 + len(el)*54
        kid_card(d, [70, ey, W-70, ey+eh], 28, GREEN_BG, GREEN, 5)
        yy = ey+24
        for ln in el: ctext(d, W/2, yy, ln, fo(44), GREEN_D); yy += 54
        draw_emoji(img, "💎", W/2, ylast-16, 96)
        if local < 1.9: celebrate(d, (W//2, ey-60), local)

# ---------- build ----------
def build(content_path, out_path):
    global VOICE
    data = json.load(open(content_path)); qs = data["questions"]
    VOICE = data.get("voice", "en-IN-NeerjaExpressiveNeural")
    RATE = data.get("rate", "+2%"); PITCH = data.get("pitch", "+14Hz")   # playful
    TIMER = int(data.get("timer_seconds", 8))
    ctx = {"series": data.get("series","Treasure Trackers"), "sub": data["subject"],
           "chap": data.get("adventure", data.get("chapter","")), "mascot": data.get("mascot","🦊"),
           "mascot2": data.get("mascot2"), "mname": data.get("mascot_name"),
           "m2name": data.get("mascot2_name"),
           "m1_img": data.get("mascot_img"), "m2_img": data.get("mascot2_img")}
    nq = len(qs)
    tmp = tempfile.mkdtemp(prefix="kids_"); fdir = os.path.join(tmp, "frames"); os.makedirs(fdir)

    print("Building bright island background…"); BG = build_bg_loop()
    print("Synthesizing playful narration (edge-tts)…")
    ni = 0
    def narr(txt):
        nonlocal ni; a, dur = say_clip(txt, tmp, ni, RATE, PITCH); ni += 1; return {"aud": a, "dur": dur}
    intro_n = narr(data.get("intro_voice", "Let's find the treasure!"))
    for q in qs: q["_nq"] = narr(q["voice_q"]); q["_na"] = narr(q["voice_a"])
    outro_n = narr(data.get("outro_voice", "You found the treasure!"))

    segs = [{"kind":"intro","dur":max(4.0, intro_n["dur"]+0.7)}]
    for i, q in enumerate(qs):
        segs.append({"kind":"qintro","dur":max(2.6, q["_nq"]["dur"]+0.4),"qi":i})
        segs.append({"kind":"count","dur":float(TIMER),"qi":i})
        segs.append({"kind":"timesup","dur":0.8,"qi":i})
        segs.append({"kind":"reveal","dur":max(5.2, q["_na"]["dur"]+1.5),"qi":i})
    segs.append({"kind":"outro","dur":max(4.6, outro_n["dur"]+1.0)})
    t = 0.0
    for s in segs: s["t0"] = t; t += s["dur"]
    total = t; TF = int(round(total*FPS))
    print(f"Total {total:.1f}s · {TF} frames · {nq} questions")

    audio = np.zeros(int(total*SR)+SR, np.float32)
    def place(clip, at, gain=1.0):
        i = int(at*SR); j = min(i+len(clip), len(audio)); audio[i:j] += clip[:j-i]*gain
    tk, htk, cm, pp, sp = soft_tick(), hot_tick(), chime(), pop(), sparkle()
    for s in segs:
        k = s["kind"]
        if k == "intro": place(intro_n["aud"], s["t0"]+0.35, 1.2)
        elif k == "qintro": place(qs[s["qi"]]["_nq"]["aud"], s["t0"]+0.2, 1.2)
        elif k == "count":
            for c in range(TIMER): place(htk if (TIMER-c) <= 3 else tk, s["t0"]+c)
        elif k == "timesup": place(pp, s["t0"])
        elif k == "reveal":
            place(cm, s["t0"]); place(sp, s["t0"]+0.15)
            place(qs[s["qi"]]["_na"]["aud"], s["t0"]+0.55, 1.25)
        elif k == "outro": place(outro_n["aud"], s["t0"]+0.35, 1.2)
    peak = np.max(np.abs(audio)) or 1; audio = audio/peak*0.94
    ap = os.path.join(tmp, "audio.wav")
    with wave.open(ap, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio*32767).astype(np.int16).tobytes())

    def seg_at(fi):
        tt = fi/FPS
        for s in segs:
            if s["t0"] <= tt < s["t0"]+s["dur"]: return s, (tt-s["t0"])
        return segs[-1], segs[-1]["dur"]

    for fi in range(TF):
        s, local = seg_at(fi); k = s["kind"]
        img = BG[fi % BG_LOOP_N].copy(); d = ImageDraw.Draw(img, "RGBA")
        watermark(img)                      # light TrigunAI ownership stamp on every frame
        if k == "intro":
            header(img, d, ctx)
            draw_emoji(img, "🗺️", W/2, 450, 210)
            tf = fh(92)
            ty = 600
            for ln in wrap(d, ctx["chap"], tf, W-140):
                ctext(d, W/2, ty, ln, tf, INK); ty += 104
            for j, ln in enumerate(wrap(d, data.get("topic_line",""), fo(50), W-160)):
                ctext(d, W/2, ty+8+j*62, ln, fo(50), GOLD_D)
            # JJ + Mikey side by side with name labels (feet bottom-anchored, names below)
            by = 1380
            if ctx.get("m2_img") or ctx.get("mascot2"):
                draw_char_live(img, ctx, "m1", W/2-195, by, 330, local, ph=0.0)
                draw_char_live(img, ctx, "m2", W/2+195, by, 285, local, ph=0.6)
                if ctx.get("mname"): ctext(d, W/2-195, by+16, ctx["mname"], fh(56), INK)
                if ctx.get("m2name"): ctext(d, W/2+195, by+16, ctx["m2name"], fh(56), INK)
            else:
                draw_char_live(img, ctx, "m1", W/2, by, 330, local)
            gem_bar(img, d, 0, nq)
        elif k == "outro":
            header(img, d, ctx)
            gem_bar(img, d, nq, nq)
            draw_emoji(img, "🏆", W/2, 640, 300)
            ctext(d, W/2, 840, "TREASURE FOUND!", fh(96), GOLD_D)
            ctext(d, W/2, 960, "You're a Maths Superstar!", fh(60), INK)
            by = 1360
            if ctx.get("m2_img") or ctx.get("mascot2"):
                draw_char_live(img, ctx, "m1", W/2-195, by, 300, local, excited=True, ph=0.0)
                draw_char_live(img, ctx, "m2", W/2+195, by, 258, local, excited=True, ph=0.5)
            else:
                draw_char_live(img, ctx, "m1", W/2, by, 300, local, excited=True)
            # TrigunAI end-card (ownership / brand)
            d.rounded_rectangle([250, 1470, W-250, 1660], radius=36, fill=(255, 255, 255, 235))
            draw_logo(img, "trigunai_lockup.png", W/2, 1540, 460)
            ctext(d, W/2, 1600, "kids-education.trigunai.com", fo(38), GOLD_D)
            ctext(d, W/2, 1700, "Original content © TrigunAI", fo(34), INK)
            if local < 2.2: celebrate(d, (W//2, 600), local)
        else:
            render_q(img, d, qs[s["qi"]], k, local, s["dur"], TIMER, ctx, s["qi"], nq)
        img.convert("RGB").save(os.path.join(fdir, f"{fi:06d}.png"))
        if fi % 90 == 0: print(f"  frame {fi}/{TF}")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    subprocess.check_call(["ffmpeg","-y","-framerate",str(FPS),"-i",
        os.path.join(fdir,"%06d.png"),"-i",ap,"-c:v","libx264","-pix_fmt","yuv420p",
        "-crf","19","-preset","medium","-c:a","aac","-b:a","192k","-shortest",out_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n✅  {out_path}")

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "content/mult_mountain_en.json"
    o = sys.argv[2] if len(sys.argv) > 2 else "out/mult_mountain.mp4"
    build(c, o)
