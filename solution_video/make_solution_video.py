#!/usr/bin/env python3
"""
Acharya — Descriptive Solution Video engine.
Real exam question + worked solution -> a landscape 1920x1080 "teacher at the board"
video: LaTeX formulas (matplotlib mathtext) reveal step-by-step, narrated per step.

CPU-only, no TeX install, no GPU. Deps: matplotlib, Pillow, numpy, edge-tts, ffmpeg.

Usage:  python3 make_solution_video.py content/<file>.json out/<name>.mp4
"""
import sys, os, re, json, asyncio, subprocess, hashlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (13, 20, 32)                 # deep slate board
GOLD = (222, 184, 120)            # Acharya accent
WHITE = (238, 242, 248)
DIM = (120, 132, 150)             # dimmed prior steps
SUBGRAY = (150, 160, 175)
GREEN = (120, 200, 150)
VOICE = "en-IN-PrabhatNeural"     # calm male teacher
RATE = "-6%"

BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BASE, "work")
os.makedirs(WORK, exist_ok=True)

# ---- brand logo (TrigunAI chrome lockup, transparent) ----
_LOCKUP = os.path.join(BASE, "assets", "trigunai_lockup.png")
def logo(height):
    im = Image.open(_LOCKUP).convert("RGBA")
    w, h = im.size
    return im.resize((int(w*height/h), height), Image.LANCZOS)

# ---- fonts (matplotlib ships DejaVu; guaranteed present) ----
_SANS = font_manager.findfont("DejaVu Sans")
_SANS_B = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold"))
def font(sz, bold=False): return ImageFont.truetype(_SANS_B if bold else _SANS, sz)

# ---- math rendering via mathtext -> tightly cropped transparent PNG ----
def _plainify(latex):
    """Fallback: strip LaTeX to readable plain text if mathtext can't parse it."""
    s = latex.strip().strip("$")
    s = re.sub(r"\\d?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\left|\\right|\\,|\\!|\\;|\\:|\\quad|\\qquad|\\big|\\Big", " ", s)
    s = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", s)
    reps = {r"\times":"x", r"\cdot":"·", r"\pi":"π", r"\varepsilon":"ε", r"\Delta":"Δ",
            r"\Rightarrow":"=>", r"\approx":"≈", r"\alpha":"α", r"\beta":"β", r"\theta":"θ",
            r"\omega":"ω", r"\mu":"μ", r"\lambda":"λ", r"\sqrt":"√", r"\pm":"±", r"\infty":"∞"}
    for a,b in reps.items(): s = s.replace(a,b)
    s = s.replace("\\","").replace("{","").replace("}","").replace("^","^").replace("_","_")
    return s

_mathcache = {}
def render_math(latex, fontsize=42, color=(238,242,248)):
    key = hashlib.md5(f"{latex}|{fontsize}|{color}".encode()).hexdigest()
    p = os.path.join(WORK, f"m_{key}.png")
    if key in _mathcache: return _mathcache[key]
    c = (color[0]/255, color[1]/255, color[2]/255)
    for attempt in (latex, r"$" + _plainify(latex).replace("$","") + r"$", None):
        if attempt is None:                                  # last resort: plain PIL text
            img = Image.new("RGBA", (10,10), (0,0,0,0))
            _mathcache[key] = img; return img
        try:
            if not os.path.exists(p):
                fig = plt.figure(figsize=(16, 2.4)); fig.patch.set_alpha(0)
                ax = fig.add_axes([0,0,1,1]); ax.axis("off")
                txt = attempt if attempt.strip().startswith("$") else attempt
                ax.text(0.005, 0.5, txt, fontsize=fontsize, color=c, ha="left", va="center")
                fig.savefig(p, transparent=True, dpi=200, bbox_inches="tight", pad_inches=0.04)
                plt.close(fig)
            img = Image.open(p).convert("RGBA")
            _mathcache[key] = img
            return img
        except Exception:
            plt.close("all")
            if os.path.exists(p): os.remove(p)
            continue

def fit(img, max_w, max_h):
    w, h = img.size
    s = min(max_w/w, max_h/h, 1.0)
    if s < 1.0:
        img = img.resize((int(w*s), int(h*s)), Image.LANCZOS)
    return img

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur+" "+wd).strip()
        if draw.textlength(t, font=fnt) <= max_w: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def board():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # subtle top vignette line
    return im, d

def header(im, d, right_text):
    lg = logo(52)
    im.paste(lg, (70, 40), lg)
    tw = d.textlength(right_text, font=font(28))
    d.text((W-70-tw, 52), right_text, font=font(28), fill=SUBGRAY)
    d.line((70, 108, W-70, 108), fill=(40, 52, 70), width=2)

# ============================================================
def build(content, outpath):
    exam_tag = content["exam_tag"]              # "JEE Advanced 2016 · Physics · Nuclear Physics"
    q_reminder = content["q_reminder"]          # short one-line context on solution boards
    steps = content["steps"]                    # [{label, eqs:[latex], narration}]

    # --- per-scene layout: big equations, block vertically centered, accumulate + dim ---
    REGION_TOP, REGION_BOT = 205, 1015
    LBL_H, gap_lbl, gap_eq, gap_step = 56, 12, 22, 46
    EQ_MAXW, EQ_MAXH = 1480, 156
    avail = REGION_BOT - REGION_TOP

    def draw_step_rows(im, d, upto):
        # build rows with a gap-after; measure at base size, then GLOBAL-scale to fit
        rows = []          # (si, kind, payload, base_h, gap_after)
        for si in range(upto+1):
            neq = len(steps[si]["eqs"])
            rows.append((si, "label", steps[si]["label"], LBL_H, gap_lbl))
            for ei, eq in enumerate(steps[si]["eqs"]):
                img = fit(render_math(eq, 48, WHITE), EQ_MAXW, EQ_MAXH)
                gap = gap_step if ei == neq-1 else gap_eq
                rows.append((si, "eq", (si, ei), img.size[1], gap))
        total = sum(bh + ga for (_, _, _, bh, ga) in rows)
        g = min(1.0, avail / total) if total > 0 else 1.0     # uniform shrink when crowded
        y = REGION_TOP + max(0, (avail - total*g) / 2)
        for (si, kind, payload, bh, ga) in rows:
            current = (si == upto)
            if kind == "label":
                d.text((90, y), payload, font=font(max(24, int(46*g)), True),
                       fill=(GOLD if current else DIM))
            else:
                col = WHITE if current else DIM
                img = fit(render_math(steps[si]["eqs"][payload[1]], 48, col), EQ_MAXW, EQ_MAXH)
                if g < 1.0:
                    img = img.resize((max(1,int(img.size[0]*g)), max(1,int(img.size[1]*g))), Image.LANCZOS)
                im.paste(img, (150, int(y)), img)
            y += (bh + ga) * g

    scenes = []   # (frame_png, narration_text)

    # ---- Scene 0: the question ----
    im, d = board()
    header(im, d, exam_tag)
    d.text((70, 150), "Solve step by step", font=font(30), fill=SUBGRAY)
    d.text((70, 205), content["title"], font=font(56, True), fill=WHITE)
    # question prose
    yy = 300
    for ln in wrap(d, content["q_prose"], font(34), W-140):
        d.text((70, yy), ln, font=font(34), fill=(205,214,226)); yy += 46
    # given formula
    gf = fit(render_math(content["given_eq"], 46, GOLD), 1500, 150)
    im.paste(gf, (70, yy+14), gf); yy += gf.size[1] + 46
    # options row
    d.text((70, yy), "Options:", font=font(30, True), fill=SUBGRAY); yy += 46
    ox = 70
    for i, op in enumerate(content["options"]):
        oimg = fit(render_math(op, 40, WHITE), 360, 70)
        lbl = chr(65+i)
        d.text((ox, yy+8), lbl+".", font=font(34, True), fill=GOLD)
        im.paste(oimg, (ox+46, yy), oimg)
        ox += 470
        if ox > W-300: ox = 70; yy += 92
    f0 = os.path.join(WORK, "s0.png"); im.save(f0)
    scenes.append((f0, content["q_narration"]))

    # ---- Scene per step (accumulating) ----
    for i, st in enumerate(steps):
        im, d = board()
        header(im, d, exam_tag)
        d.text((70, 150), q_reminder, font=font(26), fill=SUBGRAY)
        draw_step_rows(im, d, i)
        fp = os.path.join(WORK, f"s{i+1}.png"); im.save(fp)
        scenes.append((fp, st["narration"]))

    # ---- Answer scene ----
    im, d = board()
    header(im, d, exam_tag)
    d.text((70, 150), q_reminder, font=font(26), fill=SUBGRAY)
    # boxed answer
    ans = fit(render_math(content["answer_eq"], 70, GREEN), 1200, 170)
    bx0, by0 = 70, 300
    d.rounded_rectangle((bx0, by0, bx0+ans.size[0]+80, by0+ans.size[1]+70), radius=18, outline=GREEN, width=4)
    im.paste(ans, (bx0+40, by0+35), ans)
    d.text((70, by0+ans.size[1]+120), content["answer_label"], font=font(46, True), fill=GOLD)
    # CTA
    d.text((70, 900), content["cta_line"], font=font(38, True), fill=WHITE)
    d.text((70, 958), "acharya.trigunai.com/exam-prep", font=font(40, True), fill=GOLD)
    # brand sign-off (chrome mark, bottom-right)
    _mark = Image.open(os.path.join(BASE, "assets", "trigunai_mark.png")).convert("RGBA")
    mh = 260; _mark = _mark.resize((int(_mark.size[0]*mh/_mark.size[1]), mh), Image.LANCZOS)
    im.paste(_mark, (W-_mark.size[0]-110, H-_mark.size[1]-120), _mark)
    fa = os.path.join(WORK, "sa.png"); im.save(fa)
    scenes.append((fa, content["answer_narration"]))

    # ---- narration -> mp3 per scene ----
    import edge_tts
    async def tts(text, path):
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
    clips = []
    for idx, (frame, narr) in enumerate(scenes):
        mp3 = os.path.join(WORK, f"a{idx}.mp3")
        nh = os.path.join(WORK, f"a{idx}.txt")
        prev = open(nh).read() if os.path.exists(nh) else ""
        if not (os.path.exists(mp3) and prev == narr):   # regen only if text changed
            asyncio.run(tts(narr, mp3)); open(nh, "w").write(narr)
        dur = float(subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0", mp3]).decode().strip())
        dur += 0.7  # tail padding
        clip = os.path.join(WORK, f"c{idx}.mp4")
        subprocess.run(["ffmpeg","-y","-loop","1","-i",frame,"-i",mp3,
            "-c:v","libx264","-tune","stillimage","-pix_fmt","yuv420p","-r","30",
            "-vf","fade=t=in:st=0:d=0.3,scale=1920:1080",
            "-c:a","aac","-b:a","192k","-af","apad","-t",f"{dur:.2f}",
            clip], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(clip)
        print(f"  scene {idx} ok ({dur:.1f}s)")
    # ---- concat ----
    lst = os.path.join(WORK, "concat.txt")
    with open(lst,"w") as f:
        for c in clips: f.write(f"file '{c}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
        "-c","copy", outpath], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅", outpath)

if __name__ == "__main__":
    content = json.load(open(sys.argv[1]))
    build(content, sys.argv[2])
