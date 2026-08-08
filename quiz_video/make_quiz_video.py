#!/usr/bin/env python3
"""
Acharya Quiz-Video engine  v2  —  content JSON  ->  narrated, animated MP4.

Multi-template assessment videos for the daily posting calendar. Each question has a
"type" (mcq | match | ...); the engine dispatches to that renderer. Upgrades over v1:
  • ALIVE voice        — edge-tts en-IN-NeerjaExpressiveNeural (natural, expressive), no EC2
  • LIGHT living bg     — soft warm Acharya-cream gradient with slow-drifting gold light
                          (seamless precomputed loop, so render stays fast)
  • CLEAR typography    — dark ink on white cards, high contrast
  • CELEBRATION         — confetti burst + glow ring + "Correct!" pop on the right answer
  • ISOCHRONIC bed      — gentle ~10 Hz alpha focus pulse layered low under everything
  • INNOVATIVE formats  — Match-the-Following (animated connecting lines) + MCQ

  python3 make_quiz_video.py content/sample_v2.json out/quiz_v2.mp4

Self-contained on a Mac: PIL + edge-tts (needs internet) + numpy + ffmpeg.
Vertical 1080x1920 @ 30fps.
"""
import sys, os, json, math, wave, subprocess, tempfile, shutil, asyncio
import numpy as np
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- config ----------
W, H, FPS = 1080, 1920, 30
SR = 44100
VOICE = "en-IN-NeerjaExpressiveNeural"   # alive, expressive Indian-English
F_SUP = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
F_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
F_BLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# Acharya LIGHT palette (soothing, warm)
CREAM_TOP = (253, 246, 236)
CREAM_BOT = (246, 226, 205)
INK       = (42, 32, 24)
MUTED     = (122, 106, 87)
FAINT     = (160, 138, 114)
GOLD      = (194, 89, 31)
GOLD_DK   = (168, 72, 26)
GOLD_BRT  = (212, 112, 58)
CARD      = (255, 255, 255)
CARD_BD   = (234, 221, 202)
GREEN     = (47, 169, 104)
GREEN_DK  = (31, 139, 82)
GREEN_BG  = (228, 245, 236)

# ---------- fonts ----------
KOHI = "/System/Library/Fonts/Kohinoor.ttc"   # idx0 Regular · idx3 Bold (Devanagari)
_fc = {}
def font(path, size, index=0):
    k = (path, size, index)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size, index=index)
    return _fc[k]

# language-aware content fonts + UI microcopy (set by set_lang)
LANG = "en"
def fh(sz):   # heading / bold content text
    return font(F_BLD, sz) if LANG == "en" else font(KOHI, sz, 3)
def fo(sz):   # body / option content text (Arial Unicode carries ⁻¹ ² for EN formulas)
    return font(F_SUP, sz) if LANG == "en" else font(KOHI, sz, 0)
_UI = {
    "en": {"beat": "Beat the timer!", "lockin": "Lock in your answer…",
           "pair": "Pair them in your head…", "nice": "Nice work!",
           "timesup": "TIME'S UP!", "seconds": "seconds", "why": "Why: ",
           "correct": "Correct!", "match": "MATCH", "of": "of %d"},
    "hi": {"beat": "टाइमर को हराओ!", "lockin": "अपना उत्तर सोचो…",
           "pair": "मन में जोड़ी बनाओ…", "nice": "शाबाश!",
           "timesup": "समय समाप्त!", "seconds": "सेकंड", "why": "क्यों: ",
           "correct": "सही!", "match": "जोड़ी", "of": "/ %d"},
}
UI = _UI["en"]
def set_lang(lang):
    global LANG, UI
    LANG = "hi" if lang == "hi" else "en"
    UI = _UI[LANG]

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

def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ---------- living background (seamless loop, precomputed) ----------
BG_LOOP_N = 120           # 4 s loop
def build_bg_loop():
    hw, hh = W // 2, H // 2
    ys = np.linspace(0, 1, hh)[:, None, None]
    top = np.array(CREAM_TOP, np.float32); bot = np.array(CREAM_BOT, np.float32)
    base = top * (1 - ys) + bot * ys           # (hh,1,3)
    base = np.repeat(base, hw, axis=1)          # (hh,hw,3)
    yy, xx = np.mgrid[0:hh, 0:hw].astype(np.float32)
    # warm soft light orbs drifting on closed sinus paths (period = loop)
    blobs = [
        # cx, cy, rx, ry, k(int cycles), phase, sigma, color, alpha
        (0.30, 0.24, 0.10, 0.06, 1, 0.0, 210, (255, 226, 178), 0.55),
        (0.74, 0.34, 0.08, 0.10, 1, 1.7, 240, (250, 214, 210), 0.42),
        (0.50, 0.60, 0.12, 0.05, 1, 3.0, 300, (247, 223, 170), 0.40),
        (0.20, 0.78, 0.07, 0.09, 2, 0.6, 200, (255, 232, 200), 0.38),
        (0.82, 0.80, 0.09, 0.06, 1, 4.2, 250, (245, 210, 185), 0.36),
        (0.55, 0.12, 0.06, 0.05, 2, 2.2, 190, (255, 236, 205), 0.34),
    ]
    frames = []
    for f in range(BG_LOOP_N):
        t = f / BG_LOOP_N
        img = base.copy()
        for cx, cy, rx, ry, k, ph, sig, col, a in blobs:
            px = (cx + rx * math.cos(2 * math.pi * k * t + ph)) * hw
            py = (cy + ry * math.sin(2 * math.pi * k * t + ph)) * hh
            d2 = (xx - px) ** 2 + (yy - py) ** 2
            w = (a * np.exp(-d2 / (2 * sig * sig)))[..., None]
            img = img * (1 - w) + np.array(col, np.float32) * w
        arr = np.clip(img, 0, 255).astype(np.uint8)
        im = Image.fromarray(arr, "RGB").resize((W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.GaussianBlur(6))
        frames.append(im)
    return frames

# ---------- brand logo (TrigunAI lockup) ----------
_BASEQ = os.path.dirname(os.path.abspath(__file__))
try:
    _LOCKUP_Q = Image.open(os.path.join(_BASEQ, "assets", "trigunai_lockup.png")).convert("RGBA")
except Exception:
    _LOCKUP_Q = None
def paste_logo(img, cx, cy, h):
    """Center a logo of height h at (cx,cy) on a soft dark pill for contrast."""
    if _LOCKUP_Q is None: return
    lg = _LOCKUP_Q.resize((int(_LOCKUP_Q.size[0]*h/_LOCKUP_Q.size[1]), h), Image.LANCZOS)
    pw, ph = lg.size[0]+80, h+44
    pill = Image.new("RGBA", (pw, ph), (18, 24, 34, 235))
    img.paste(pill, (int(cx-pw/2), int(cy-ph/2)), pill)
    img.paste(lg, (int(cx-lg.size[0]/2), int(cy-lg.size[1]/2)), lg)

# ---------- shared UI ----------
def header(d, sub, chap):
    cx, cy, s = 94, 98, 22
    d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], fill=GOLD)
    d.text((132, 68), "ACHARYA", font=font(F_BLD, 52), fill=GOLD_DK)
    d.text((134, 138), f"{sub}  ·  {chap}", font=fo(33), fill=MUTED)
    d.line([70, 200, W - 70, 200], fill=(0, 0, 0, 22), width=2)

def qbadge(d, n, total, label):
    d.rounded_rectangle([70, 236, 250, 314], radius=18, fill=GOLD)
    d.text((92, 248), f"Q{n}", font=font(F_BLD, 50), fill=(255, 248, 240))
    d.text((272, 256), label, font=fh(36), fill=GOLD_DK)

def soft_card(d, box, radius, fill, outline, width=3, shadow=True):
    x0, y0, x1, y1 = box
    if shadow:
        d.rounded_rectangle([x0 + 4, y0 + 7, x1 + 4, y1 + 7], radius=radius,
                            fill=(120, 90, 60, 34))
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def timer_ring(d, cx, cy, r, frac, secs):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 0, 0, 26), width=16)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=(255, 255, 255, 150))
    col = GREEN if secs > 5 else (GOLD if secs > 2 else (200, 70, 45))
    if frac > 0.001:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=col, width=16)
    nf = font(F_BLD, 140)
    tw = d.textlength(str(secs), font=nf)
    d.text((cx - tw / 2, cy - 100), str(secs), font=nf, fill=col)
    lf = fo(32); lbl = UI["seconds"]
    lw = d.textlength(lbl, font=lf)
    d.text((cx - lw / 2, cy + 62), lbl, font=lf, fill=MUTED)

def cta_bar(d, text):
    soft_card(d, [70, H - 196, W - 70, H - 96], 30, GOLD, GOLD_DK, 0, shadow=True)
    tf = fh(46)
    tw = d.textlength(text, font=tf)
    d.text((W / 2 - tw / 2, H - 174), text, font=tf, fill=(255, 248, 240))

# ---------- celebration particles ----------
def celebrate(d, origin, local, dur=1.8):
    """confetti burst + expanding glow ring + Correct! pop, anchored at origin."""
    ox, oy = origin
    # glow ring
    if local < 0.9:
        rr = 40 + local * 520
        al = int(150 * (1 - local / 0.9))
        for k in range(3):
            d.ellipse([ox - rr + k*10, oy - rr + k*10, ox + rr - k*10, oy + rr - k*10],
                      outline=(47, 169, 104, max(0, al - k*40)), width=6)
    # confetti (deterministic)
    rng = np.random.default_rng(1234)
    cols = [(212,112,58),(47,169,104),(255,196,120),(194,89,31),(120,200,150),(255,170,150)]
    N = 70
    for i in range(N):
        ang = rng.uniform(0, 2*math.pi)
        spd = rng.uniform(320, 820)
        vx, vy = math.cos(ang)*spd, math.sin(ang)*spd - 260
        g = 900
        px = ox + vx*local
        py = oy + vy*local + 0.5*g*local*local
        life = rng.uniform(1.2, 1.8)
        if local > life: continue
        al = int(255 * max(0, 1 - local/life))
        sz = rng.uniform(9, 20)
        spin = rng.uniform(0, 2*math.pi) + local*rng.uniform(-6, 6)
        col = cols[i % len(cols)] + (al,)
        c, s = math.cos(spin), math.sin(spin)
        pts = [(-sz, -sz*0.6), (sz, -sz*0.6), (sz, sz*0.6), (-sz, sz*0.6)]
        poly = [(px + x*c - y*s, py + x*s + y*c) for x, y in pts]
        d.polygon(poly, fill=col)
    # Correct! pop
    if local < 1.4:
        p = min(1, local / 0.4)
        sc = ease_out_back(p)
        bw, bh = 360*sc, 96*sc
        bx, by = ox - bw/2, oy - bh/2
        al = int(255 * (1 if local < 1.0 else max(0, 1-(local-1.0)/0.4)))
        d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=int(bh/2),
                            fill=(47,169,104,al))
        if sc > 0.5:
            cf = font(F_SUP, 52); wf = fh(52); word = UI["correct"]
            cw = d.textlength("✓ ", font=cf); ww = d.textlength(word, font=wf)
            x0 = ox - (cw + ww) / 2
            d.text((x0, oy - 34), "✓ ", font=cf, fill=(255,255,255,al))
            d.text((x0 + cw, oy - 34), word, font=wf, fill=(255,255,255,al))

# ---------- audio ----------
def sine(freq, dur, vol=0.5, decay=6):
    n = int(SR*dur); t = np.arange(n)/SR
    env = np.exp(-t*decay) if decay else np.ones(n)
    return (np.sin(2*math.pi*freq*t)*env*vol).astype(np.float32)

def chime(dur=0.5, vol=0.5):
    out = sine(880, dur, vol, 5) + sine(1320, dur, vol*0.7, 5)
    hi = sine(1760, dur*0.6, vol*0.4, 6)
    out[:len(hi)] += hi
    return out

def sparkle(vol=0.5):
    out = np.zeros(int(SR*0.9), np.float32)
    for i, fr in enumerate([784, 988, 1319, 1568, 2093]):
        c = sine(fr, 0.5, vol*0.5, 7); at = int(i*0.06*SR)
        out[at:at+len(c)] += c[:len(out)-at]
    return out

def soft_tick(vol=0.28): return sine(680, 0.05, vol, 30)
def hot_tick(vol=0.4):  return sine(920, 0.06, vol, 26)
def buzz(dur=0.4, vol=0.35):
    n=int(SR*dur); t=np.arange(n)/SR
    env=np.minimum(1, np.minimum(t*18,(dur-t)*18))
    return ((0.6*np.sin(2*math.pi*196*t)+0.4*np.sin(2*math.pi*233*t))*env*vol).astype(np.float32)

def isochronic_bed(total, vol=0.05):
    """gentle alpha (~10 Hz) focus pulse on a soft low pad; loops the whole video, low."""
    n = int(SR*total); t = np.arange(n)/SR
    pad = 0.5*np.sin(2*math.pi*110*t) + 0.35*np.sin(2*math.pi*164.8*t) + 0.2*np.sin(2*math.pi*220*t)
    gate = 0.55 + 0.45*np.sin(2*math.pi*10*t - math.pi/2)   # 10 Hz isochronic pulse
    shimmer = 0.15*np.sin(2*math.pi*528*t) * (0.5+0.5*np.sin(2*math.pi*0.1*t))
    sig = (pad*gate + shimmer)
    # fade in/out
    fade = int(1.2*SR)
    sig[:fade] *= np.linspace(0,1,fade); sig[-fade:] *= np.linspace(1,0,fade)
    return (sig/ (np.max(np.abs(sig)) or 1) * vol).astype(np.float32)

def read_wav_mono(p):
    with wave.open(p,"rb") as wf:
        n=wf.getnframes(); sw=wf.getsampwidth(); ch=wf.getnchannels(); raw=wf.readframes(n)
    a=np.frombuffer(raw, np.int16 if sw==2 else np.uint8).astype(np.float32)
    if sw==2: a/=32768.0
    else: a=(a-128)/128.0
    if ch==2: a=a.reshape(-1,2).mean(1)
    return a

async def _tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate="+5%", pitch="+6Hz").save(path)

def say_clip(text, tmp, i):
    mp3=os.path.join(tmp,f"n{i}.mp3"); wavp=os.path.join(tmp,f"n{i}.wav")
    asyncio.run(_tts(text, mp3))
    subprocess.check_call(["ffmpeg","-y","-i",mp3,"-ar",str(SR),"-ac","1",wavp],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a=read_wav_mono(wavp); return a, len(a)/SR

# ---------- template renderers ----------
def render_mcq(d, q, phase, local, seg_dur, TIMER, sub, chap, qi, nq):
    header(d, sub, chap); qbadge(d, qi+1, f"of {nq}", UI["of"]%nq)
    # question
    y=352; qf=fh(60)
    for ln in wrap(d, q["q"], qf, W-150):
        d.text((70,y), ln, font=qf, fill=INK); y+=76
    y+=16
    labels="ABCD"; x=70; w=W-140; bh=146; gap=30
    reveal = phase=="reveal"
    for i,opt in enumerate(q["options"]):
        oy=y+i*(bh+gap); correct = reveal and i==q["answer"]
        if correct:
            soft_card(d,[x,oy,x+w,oy+bh],26, GREEN_BG, GREEN,4)
            lc, lt = GREEN, (255,255,255)
        else:
            soft_card(d,[x,oy,x+w,oy+bh],26, CARD, CARD_BD,3)
            lc, lt = GOLD, (255,248,240)
        d.rounded_rectangle([x+24,oy+32,x+106,oy+114], radius=16, fill=lc)
        d.text((x+45,oy+42), labels[i], font=font(F_BLD,58), fill=lt)
        opf=fo(50); ol=wrap(d,opt,opf,w-200)
        ty=oy+bh//2-(len(ol)*58)//2
        for ln in ol: d.text((x+140,ty),ln,font=opf,fill=INK); ty+=58
        if correct:
            d.text((x+w-96,oy+34),"✓",font=font(F_SUP,78),fill=GREEN_DK)
    ylast = y+4*(bh+gap)
    if phase=="count":
        secs=min(TIMER,max(1,int(math.ceil(seg_dur-local-1e-6))))
        timer_ring(d, W//2, H-330, 180, max(0,1-local/seg_dur), secs)
    elif phase=="timesup":
        blink=int(local*8)%2==0
        tf=fh(104); txt=UI["timesup"]
        tw=d.textlength(txt,font=tf)
        d.text((W/2-tw/2,H-400),txt,font=tf,fill=(200,70,45) if blink else GOLD_BRT)
    elif phase=="reveal":
        ey=ylast+20; ef=fo(42)
        el=wrap(d,UI["why"]+q["explain"],ef,W-200)
        eh=52+len(el)*54
        soft_card(d,[70,ey,W-70,ey+eh],22, GREEN_BG, GREEN,2)
        yy=ey+26
        for ln in el: d.text((104,yy),ln,font=ef,fill=GREEN_DK); yy+=54
        # celebration anchored on correct option
        cyc = y+q["answer"]*(bh+gap)+bh//2
        if local < 1.9: celebrate(d,(W//2,cyc),local)
    elif phase=="qintro":
        d.text((70,H-250),UI["lockin"],font=fo(40),fill=MUTED)

def render_match(d, q, phase, local, seg_dur, TIMER, sub, chap, qi, nq):
    header(d, sub, chap); qbadge(d, qi+1, f"of {nq}", UI["match"])
    pf=fh(54); y=330
    for ln in wrap(d, q["prompt"], pf, W-150):
        d.text((70,y),ln,font=pf,fill=INK); y+=66
    y+=12
    left=q["left"]; right=q["right"]; pairs=dict(q["pairs"])
    n=len(left); rowh=150; gap=44; colw=430
    lx0=60; rx0=W-60-colw
    ys=[y+i*(rowh+gap) for i in range(n)]
    reveal = phase=="reveal"
    # column headers
    d.text((lx0+10,y-4),"", font=font(F_REG,30), fill=MUTED)
    # draw connecting lines first (behind cards) during reveal
    def lcenter(i): return (lx0+colw, ys[i]+rowh//2)
    def rcenter(j): return (rx0, ys[j]+rowh//2)
    done_left=set(); done_right=set()
    if reveal:
        for k,(li,rj) in enumerate(sorted(pairs.items())):
            t0=0.35+k*0.55
            if local< t0: continue
            p=min(1,(local-t0)/0.45)
            sx,sy=lcenter(li); ex,ey=rcenter(rj)
            # slight arc via midpoint lift
            mx,my=(sx+ex)/2,(sy+ey)/2-30
            pts=[]
            steps=26
            for s in range(steps+1):
                tt=(s/steps)*p
                a=(1-tt)**2; b=2*(1-tt)*tt; c=tt*tt
                pts.append((a*sx+b*mx+c*ex, a*sy+b*my+c*ey))
            if len(pts)>1:
                d.line(pts, fill=(47,169,104,120), width=12, joint="curve")
                d.line(pts, fill=(120,210,160), width=5, joint="curve")
            cx,cy=pts[-1]; d.ellipse([cx-11,cy-11,cx+11,cy+11], fill=GREEN)
            if p>=1: done_left.add(li); done_right.add(rj)
    # left cards (numbers)
    for i,item in enumerate(left):
        oy=ys[i]; hot = i in done_left
        soft_card(d,[lx0,oy,lx0+colw,oy+rowh],24,
                  GREEN_BG if hot else CARD, GREEN if hot else CARD_BD, 4 if hot else 3)
        d.rounded_rectangle([lx0+20,oy+30,lx0+92,oy+rowh-30],radius=14,
                            fill=GREEN if hot else GOLD)
        d.text((lx0+40,oy+rowh//2-34), str(i+1), font=font(F_BLD,54), fill=(255,248,240))
        itf=fo(44); il=wrap(d,item,itf,colw-120)
        ty=oy+rowh//2-(len(il)*50)//2
        for ln in il: d.text((lx0+112,ty),ln,font=itf,fill=INK); ty+=50
    # right cards (letters)
    for j,item in enumerate(right):
        oy=ys[j]; hot = j in done_right
        soft_card(d,[rx0,oy,rx0+colw,oy+rowh],24,
                  GREEN_BG if hot else CARD, GREEN if hot else CARD_BD, 4 if hot else 3)
        d.rounded_rectangle([rx0+colw-92,oy+30,rx0+colw-20,oy+rowh-30],radius=14,
                            fill=GREEN if hot else GOLD_BRT)
        d.text((rx0+colw-74,oy+rowh//2-34), "ABCD"[j], font=font(F_BLD,52), fill=(255,248,240))
        itf=fo(44); il=wrap(d,item,itf,colw-120)
        ty=oy+rowh//2-(len(il)*50)//2
        for ln in il: d.text((rx0+24,ty),ln,font=itf,fill=INK); ty+=50
    ylast=ys[-1]+rowh
    if phase=="count":
        secs=min(TIMER,max(1,int(math.ceil(seg_dur-local-1e-6))))
        timer_ring(d, W//2, H-300, 168, max(0,1-local/seg_dur), secs)
    elif phase=="timesup":
        blink=int(local*8)%2==0
        tf=fh(96); txt=UI["timesup"]
        tw=d.textlength(txt,font=tf); d.text((W/2-tw/2,H-360),txt,font=tf,
                                              fill=(200,70,45) if blink else GOLD_BRT)
    elif phase=="qintro":
        d.text((70,H-250),UI["pair"],font=fo(40),fill=MUTED)
    elif phase=="reveal":
        if local>2.6 and local<4.5:
            celebrate(d,(W//2, ylast+180), local-2.6, dur=1.6)
        ey=max(ylast+30, H-330)

# ---------- build ----------
def build(content_path, out_path):
    global VOICE
    data=json.load(open(content_path)); qs=data["questions"]
    set_lang(data.get("lang","en"))
    VOICE=data.get("voice", "hi-IN-SwaraNeural" if LANG=="hi" else "en-IN-NeerjaExpressiveNeural")
    TIMER=int(data.get("timer_seconds",8)); sub=data["subject"]; chap=data["chapter"]
    cta=data.get("cta","Practise on Acharya")
    tmp=tempfile.mkdtemp(prefix="qv2_"); fdir=os.path.join(tmp,"frames"); os.makedirs(fdir)

    print("Precomputing living background loop…")
    BG=build_bg_loop()

    print("Synthesizing alive narration (edge-tts)…")
    ni=0
    def narr(txt):
        nonlocal ni; a,dur=say_clip(txt,tmp,ni); ni+=1; return {"aud":a,"dur":dur}
    intro_n=narr(data.get("intro_voice","Can you beat the timer?"))
    for q in qs: q["_nq"]=narr(q["voice_q"]); q["_na"]=narr(q["voice_a"])
    outro_n=narr(data.get("outro_voice","Practise on Acharya."))

    segs=[{"kind":"intro","dur":max(3.2,intro_n["dur"]+0.5)}]
    for i,q in enumerate(qs):
        segs.append({"kind":"qintro","dur":max(2.2,q["_nq"]["dur"]+0.3),"qi":i})
        segs.append({"kind":"count","dur":float(TIMER),"qi":i})
        segs.append({"kind":"timesup","dur":0.8,"qi":i})
        segs.append({"kind":"reveal","dur":max(5.0,q["_na"]["dur"]+1.4),"qi":i})
    segs.append({"kind":"outro","dur":max(4.2,outro_n["dur"]+0.8)})
    t=0.0
    for s in segs: s["t0"]=t; t+=s["dur"]
    total=t; TF=int(round(total*FPS))
    print(f"Total {total:.1f}s · {TF} frames · {len(qs)} questions")

    # audio mix
    audio=np.zeros(int(total*SR)+SR, np.float32)
    def place(clip, at, gain=1.0):
        i=int(at*SR); j=min(i+len(clip),len(audio)); audio[i:j]+=clip[:j-i]*gain
    audio[:len(isochronic_bed(total))] += isochronic_bed(total)
    tk, htk, cm, bz, sp = soft_tick(), hot_tick(), chime(0.5,0.55), buzz(), sparkle(0.5)
    for s in segs:
        k=s["kind"]
        if k=="intro": place(intro_n["aud"], s["t0"]+0.3, 1.2)
        elif k=="qintro": place(qs[s["qi"]]["_nq"]["aud"], s["t0"]+0.2, 1.2)
        elif k=="count":
            for c in range(TIMER): place(htk if (TIMER-c)<=3 else tk, s["t0"]+c)
        elif k=="timesup": place(bz, s["t0"])
        elif k=="reveal":
            place(cm, s["t0"]); place(sp, s["t0"]+0.15)
            place(qs[s["qi"]]["_na"]["aud"], s["t0"]+0.5, 1.25)
        elif k=="outro": place(outro_n["aud"], s["t0"]+0.3, 1.2)
    peak=np.max(np.abs(audio)) or 1; audio=audio/peak*0.94
    ap=os.path.join(tmp,"audio.wav")
    with wave.open(ap,"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio*32767).astype(np.int16).tobytes())

    def seg_at(fi):
        tt=fi/FPS
        for s in segs:
            if s["t0"]<=tt<s["t0"]+s["dur"]: return s,(tt-s["t0"])
        return segs[-1], segs[-1]["dur"]

    for fi in range(TF):
        s,local=seg_at(fi); k=s["kind"]
        img=BG[fi%BG_LOOP_N].copy(); d=ImageDraw.Draw(img,"RGBA")
        if k=="intro":
            header(d,sub,chap)
            d.text((70,540),sub.upper(),font=fh(92),fill=GOLD)
            yy=660
            for ln in wrap(d,chap,fh(118),W-140):
                d.text((70,yy),ln,font=fh(118),fill=INK); yy+=138
            d.text((70,yy+18),data.get("topic_line",""),font=fo(44),fill=MUTED)
            a=int(150+95*abs(math.sin(local*3)))
            d.text((70,1190),UI["beat"],font=fh(62),fill=(194,89,31,a))
            cta_bar(d,cta)
        elif k=="outro":
            header(d,sub,chap)
            d.text((70,600),UI["nice"],font=fh(100),fill=INK)
            yy=760
            for ln in wrap(d,data.get("outro_voice",""),fo(56),W-150):
                d.text((70,yy),ln,font=fo(56),fill=MUTED); yy+=72
            if local<2.0: celebrate(d,(W//2,520),local)
            paste_logo(img, W//2, H-330, 92)
            cta_bar(d,cta)
        else:
            q=qs[s["qi"]]; typ=q.get("type","mcq")
            phase=k
            if typ=="match":
                render_match(d,q,phase,local,s["dur"],TIMER,sub,chap,s["qi"],len(qs))
            else:
                render_mcq(d,q,phase,local,s["dur"],TIMER,sub,chap,s["qi"],len(qs))
        img.convert("RGB").save(os.path.join(fdir,f"{fi:06d}.png"))
        if fi%90==0: print(f"  frame {fi}/{TF}")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    subprocess.check_call(["ffmpeg","-y","-framerate",str(FPS),"-i",
        os.path.join(fdir,"%06d.png"),"-i",ap,"-c:v","libx264","-pix_fmt","yuv420p",
        "-crf","19","-preset","medium","-c:a","aac","-b:a","192k","-shortest",out_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n✅  {out_path}")

if __name__=="__main__":
    c=sys.argv[1] if len(sys.argv)>1 else "content/sample_v2.json"
    o=sys.argv[2] if len(sys.argv)>2 else "out/quiz_v2.mp4"
    build(c,o)
