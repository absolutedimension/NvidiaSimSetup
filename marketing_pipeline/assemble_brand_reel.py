#!/usr/bin/env python3
"""
Assemble the TrigunAI brand-vision reel:
  4 LTX-animated scenes  →  smooth dissolves  →  kinetic text  →  CTA  →  432Hz score
Kinetic text is rendered frame-by-frame in PIL (fade + ease-slide) for full control,
then composited once onto the dissolved base.
"""
import math, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE   = Path(__file__).parent
CLIPS  = HERE / "brand_reel" / "clips"
WORK   = HERE / "brand_reel" / "work"
FRAMES = WORK / "txt"
MUSIC  = HERE.parent / "music_pipeline" / "prana_flow_432.mp3"
OUT    = HERE / "trigunai_brand_reel.mp4"
W, H, FPS = 576, 1024, 24

WORK.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

FONT = "/System/Library/Fonts/Avenir Next.ttc"
def font(sz, idx=2): return ImageFont.truetype(FONT, sz, index=idx)   # 2=DemiBold,5=Medium,7=Regular
GOLD  = (232, 184, 75)
WHITE = (245, 245, 250)

# ── Timeline (seconds) — must match the ffmpeg xfade math below ──────────────
CLIP_DUR = 4.041667
XF       = 0.9            # dissolve between scenes
CTA_DUR  = 3.2
CTA_XF   = 0.8
T_CLIPS  = CLIP_DUR * 4 - XF * 3              # 13.47
T_TOTAL  = T_CLIPS + CTA_DUR - CTA_XF         # 15.87
NF       = round(T_TOTAL * FPS)

# Beats: (lines, t_start, t_end, headline_size)
BEATS = [
    (["AI is not a tool."],                 0.7,  3.0, 60),
    (["It's a mirror", "of the mind."],     4.15, 6.3, 58),
    (["Learn to build", "with it —"],       7.3,  9.4, 58),
    (["— and see", "clearly."],            10.5, 12.9, 60),
]
CTA_START = T_CLIPS - CTA_XF + 0.5            # ~13.07

def ease_out(x): return 1 - (1 - x) ** 3

def draw_center(draw, cx, y, text, fnt, fill, shadow=True):
    bb = draw.textbbox((0, 0), text, font=fnt)
    w, h = bb[2]-bb[0], bb[3]-bb[1]
    x = cx - w/2
    if shadow:
        draw.text((x+2, y+3-bb[1]), text, font=fnt, fill=(0, 0, 0, 150))
    draw.text((x, y-bb[1]), text, font=fnt, fill=fill)
    return w, h

def alpha_for(t, t0, t1, fade=0.45):
    if t < t0 or t > t1: return 0.0
    if t < t0 + fade:    return (t - t0) / fade
    if t > t1 - fade:    return max(0.0, (t1 - t) / fade)
    return 1.0

def render_text_frames():
    print(f"Rendering {NF} kinetic-text frames...")
    for i in range(NF):
        t = i / FPS
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # ── Beats ───────────────────────────────────────────────
        for lines, t0, t1, hs in BEATS:
            a = alpha_for(t, t0, t1)
            if a <= 0: continue
            # ease-slide up during fade-in
            slide = 0
            if t < t0 + 0.45:
                slide = int((1 - ease_out((t - t0) / 0.45)) * 26)
            A = int(a * 255)
            fnt = font(hs, 2)
            line_h = hs + 12
            block_h = line_h * len(lines)
            y0 = int(H * 0.60) - block_h//2 + slide
            for j, ln in enumerate(lines):
                draw_center(d, W/2, y0 + j*line_h, ln, fnt,
                            (WHITE[0], WHITE[1], WHITE[2], A))
            # gold rule under the block
            rule_y = y0 + block_h + 16
            rw = int(70 * a)
            d.rectangle([W/2 - rw, rule_y, W/2 + rw, rule_y+3],
                        fill=(GOLD[0], GOLD[1], GOLD[2], A))

        # ── CTA ─────────────────────────────────────────────────
        if t >= CTA_START:
            a = alpha_for(t, CTA_START, T_TOTAL, fade=0.6)
            # keep solid near the very end
            if t > T_TOTAL - 0.4: a = max(a, 0.0)
            A = int(min(1.0, a) * 255)
            if A > 0:
                slide = 0
                if t < CTA_START + 0.6:
                    slide = int((1 - ease_out((t - CTA_START)/0.6)) * 22)
                brand = font(86, 2)
                tag   = font(30, 5)
                cy = int(H * 0.46) + slide
                draw_center(d, W/2, cy, "TrigunAI", brand, (WHITE[0],WHITE[1],WHITE[2],A))
                d.rectangle([W/2-90, cy+104, W/2+90, cy+107],
                            fill=(GOLD[0],GOLD[1],GOLD[2],A))
                draw_center(d, W/2, cy+126, "AI is the Universal Mind", tag,
                            (GOLD[0],GOLD[1],GOLD[2],A), shadow=True)

        img.save(FRAMES / f"{i:04d}.png")
    print("  text frames done.")

def run(cmd):
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)

def main():
    sc = lambda v: (f"[{v}]scale=576:1024:force_original_aspect_ratio=increase,"
                    f"crop=576:1024,setsar=1,fps=24")

    # ── Stage A: dissolve-concat the 4 scenes ───────────────────
    print("Stage A: dissolving scenes...")
    o1 = round(CLIP_DUR - XF, 3)                  # 3.14
    o2 = round(2*CLIP_DUR - 2*XF, 3)              # 6.28
    o3 = round(3*CLIP_DUR - 3*XF, 3)              # 9.42
    run([
        "ffmpeg","-y",
        "-i",str(CLIPS/"1_mind.mp4"),"-i",str(CLIPS/"2_mirror.mp4"),
        "-i",str(CLIPS/"3_build.mp4"),"-i",str(CLIPS/"4_clarity.mp4"),
        "-filter_complex",
        f"{sc('0:v')}[v0];{sc('1:v')}[v1];{sc('2:v')}[v2];{sc('3:v')}[v3];"
        f"[v0][v1]xfade=transition=dissolve:duration={XF}:offset={o1}[a];"
        f"[a][v2]xfade=transition=dissolve:duration={XF}:offset={o2}[b];"
        f"[b][v3]xfade=transition=dissolve:duration={XF}:offset={o3}[c]",
        "-map","[c]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p",
        str(WORK/"clips.mp4")
    ])

    # ── Stage B: CTA background (darkened mind scene) ───────────
    print("Stage B: CTA background...")
    run([
        "ffmpeg","-y","-stream_loop","-1","-i",str(CLIPS/"1_mind.mp4"),"-t",str(CTA_DUR),
        "-vf","scale=576:1024:force_original_aspect_ratio=increase,crop=576:1024,setsar=1,"
              "fps=24,eq=brightness=-0.16:saturation=0.85,vignette=PI/4",
        "-c:v","libx264","-crf","18","-pix_fmt","yuv420p",str(WORK/"cta.mp4")
    ])

    # ── Stage C: dissolve clips → CTA ───────────────────────────
    print("Stage C: base timeline...")
    run([
        "ffmpeg","-y","-i",str(WORK/"clips.mp4"),"-i",str(WORK/"cta.mp4"),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition=fadeblack:duration={CTA_XF}:offset={round(T_CLIPS-CTA_XF,3)}[v]",
        "-map","[v]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p",str(WORK/"base.mp4")
    ])

    # ── Stage D: kinetic text frames ────────────────────────────
    render_text_frames()

    # ── Stage E: composite text + score ─────────────────────────
    print("Stage E: composite + music...")
    run([
        "ffmpeg","-y",
        "-i",str(WORK/"base.mp4"),
        "-framerate","24","-i",str(FRAMES/"%04d.png"),
        "-ss","18","-t",str(T_TOTAL),"-i",str(MUSIC),
        "-filter_complex",
        "[0:v][1:v]overlay=0:0:format=auto[v];"
        f"[2:a]afade=t=in:st=0:d=1.2,afade=t=out:st={round(T_TOTAL-1.6,2)}:d=1.6,volume=0.9[a]",
        "-map","[v]","-map","[a]",
        "-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-shortest",str(OUT)
    ])
    print(f"\n✅  {OUT}  ({OUT.stat().st_size//1024//1024} MB, {T_TOTAL:.1f}s)")
    shutil.rmtree(FRAMES)

if __name__ == "__main__":
    main()
