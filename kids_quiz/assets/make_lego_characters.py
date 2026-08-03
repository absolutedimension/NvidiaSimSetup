#!/usr/bin/env python3
"""Render LEGO-minifigure-style JJ (red-hooded bunny w/ mic) + Mikey (green turtle) as
transparent PNG sprites for the kids quiz engine.  Drawn with PIL, supersampled for smooth edges.

  python3 make_lego_characters.py            # writes jj.png, mikey.png (+ previews)
"""
import math
from PIL import Image, ImageDraw, ImageFilter

S = 4                      # supersample factor
OUT_H = 640                # final sprite height (px)
BASEW, BASEH = 340, 680    # working canvas (1x)

def C(*rgb): return tuple(rgb)
EDGE = C(38, 34, 46)       # soft dark edge for definition on the sky

def new_canvas():
    return Image.new("RGBA", (BASEW * S, BASEH * S), (0, 0, 0, 0))

def rrect(d, box, r, fill, edge=EDGE, ew=3):
    x0, y0, x1, y1 = [v * S for v in box]
    d.rounded_rectangle([x0, y0, x1, y1], radius=r * S, fill=fill,
                        outline=edge, width=int(ew * S))

def ellipse(d, box, fill, edge=EDGE, ew=3):
    x0, y0, x1, y1 = [v * S for v in box]
    d.ellipse([x0, y0, x1, y1], fill=fill, outline=edge, width=int(ew * S))

def poly(d, pts, fill, edge=EDGE, ew=3):
    p = [(x * S, y * S) for x, y in pts]
    d.polygon(p, fill=fill, outline=edge, width=int(ew * S))

def gloss(d, box, r, strength=70):
    """LEGO plastic highlight: soft white bar across the upper third of a piece."""
    x0, y0, x1, y1 = box
    hb = [x0 + (x1 - x0) * 0.14, y0 + (y1 - y0) * 0.10,
          x1 - (x1 - x0) * 0.14, y0 + (y1 - y0) * 0.34]
    xx0, yy0, xx1, yy1 = [v * S for v in hb]
    d.rounded_rectangle([xx0, yy0, xx1, yy1], radius=r * S * 0.6, fill=(255, 255, 255, strength))

def stud(d, cx, cy, rw, rh, fill):
    ellipse(d, [cx - rw, cy - rh, cx + rw, cy + rh], fill, ew=2.4)
    d.ellipse([(cx - rw*0.55)*S, (cy - rh*0.7)*S, (cx + rw*0.55)*S, (cy + rh*0.1)*S],
              fill=(255, 255, 255, 70))

def minifig(torso_fill, leg_fill, head_fill, draw_head_extra, draw_torso_extra,
            hand_fill=None, arm_fill=None):
    """Shared LEGO minifigure. Returns an RGBA image cropped to content."""
    img = new_canvas(); d = ImageDraw.Draw(img, "RGBA")
    arm_fill = arm_fill or torso_fill
    hand_fill = hand_fill or head_fill

    # ---- legs (hips + two legs) ----
    rrect(d, [92, 470, 248, 516], 10, leg_fill)                 # hips
    rrect(d, [98, 508, 165, 612], 9, leg_fill)                  # left leg
    rrect(d, [175, 508, 242, 612], 9, leg_fill)                 # right leg
    gloss(d, [98, 508, 165, 612], 9); gloss(d, [175, 508, 242, 612], 9)

    # ---- torso (trapezoid) ----
    torso = [(120, 330), (220, 330), (238, 474), (102, 474)]
    poly(d, torso, torso_fill)
    gloss(d, [110, 330, 230, 474], 14)

    # ---- arms + hands (drawn over torso sides) ----
    poly(d, [(120, 344), (150, 356), (128, 452), (96, 446)], arm_fill)   # left arm
    poly(d, [(220, 344), (190, 356), (212, 452), (244, 446)], arm_fill)  # right arm
    ellipse(d, [78, 436, 126, 484], hand_fill)                 # left hand (C)
    ellipse(d, [214, 436, 262, 484], hand_fill)                # right hand
    d.ellipse([(92)*S, (450)*S, (112)*S, (470)*S], fill=(0, 0, 0, 0))    # (hand holes handled by extra)

    draw_torso_extra(d)

    # ---- neck + head ----
    rrect(d, [150, 316, 190, 334], 5, head_fill)               # neck
    rrect(d, [116, 244, 224, 330], 30, head_fill)              # head (rounded cylinder)
    gloss(d, [116, 244, 224, 330], 30, strength=60)

    # face
    d.ellipse([(150)*S, (280)*S, (166)*S, (298)*S], fill=EDGE)  # left eye
    d.ellipse([(174)*S, (280)*S, (190)*S, (298)*S], fill=EDGE)  # right eye
    d.arc([(150)*S, (296)*S, (190)*S, (318)*S], 20, 160, fill=EDGE, width=int(3*S))  # smile
    # blush
    for bx in (138, 202):
        d.ellipse([(bx-11)*S, (300)*S, (bx+11)*S, (312)*S], fill=(255, 150, 150, 150))

    # stud on top of head
    stud(d, 170, 244, 20, 10, head_fill)

    draw_head_extra(d)

    bb = img.getbbox()
    img = img.crop(bb)
    h = OUT_H; w = max(1, int(img.size[0] * h / img.size[1]))
    return img.resize((w, h), Image.LANCZOS)

# ---------------- JJ : red-hooded bunny with a mic ----------------
JJ_RED = C(226, 46, 42); JJ_WHITE = C(248, 246, 244); JJ_LEG = C(44, 50, 74)
def jj_head_extra(d):
    # red hood back + two bunny ears rising from the head
    poly(d, [(120, 300), (220, 300), (232, 262), (108, 262)], JJ_RED)       # hood collar behind head base
    for x0 in (120, 176):                                                    # ears
        ex = [(x0, 250), (x0+24, 250), (x0+30, 150), (x0+6, 150)]
        poly(d, ex, JJ_RED)
        d.polygon([((x0+7)*S,240*S),((x0+17)*S,240*S),((x0+20)*S,168*S),((x0+4)*S,168*S)],
                  fill=(255,190,190,120))                                     # inner-ear pink
    # red hood cap over the top edge of the head
    poly(d, [(116, 268), (224, 268), (216, 244), (124, 244)], JJ_RED)
def jj_torso_extra(d):
    # white hoodie zipper stripe + drawstrings
    rrect(d, [163, 332, 177, 470], 4, JJ_WHITE, ew=2)
    d.line([(150)*S,(360)*S,(158)*S,(372)*S], fill=JJ_WHITE, width=int(3*S))
    # microphone in the right hand (gray head + handle)
    ellipse(d, [232, 452, 268, 488], C(70, 74, 82), ew=2.4)
    for gy in (460, 468, 476):
        d.line([(238)*S,(gy)*S,(262)*S,(gy)*S], fill=(30,30,34), width=int(1.4*S))
    rrect(d, [246, 486, 258, 520], 5, C(90, 94, 102), ew=2)

# ---------------- Mikey : green turtle ----------------
MK_GREEN = C(139, 199, 74); MK_GREEN_D = C(110, 168, 54); MK_SHELL = C(168, 116, 66)
def mk_head_extra(d):
    pass
def mk_torso_extra(d):
    # turtle shell on the chest with segment lines
    ellipse(d, [126, 356, 214, 462], MK_SHELL, ew=3)
    d.arc([(126)*S,(356)*S,(214)*S,(462)*S], 0, 360, fill=C(120,80,44), width=int(2*S))
    cx = 170
    for a in range(0, 360, 60):
        x = cx + 30*math.cos(math.radians(a)); y = 409 + 34*math.sin(math.radians(a))
        d.line([(cx)*S,(409)*S,(x)*S,(y)*S], fill=C(120,80,44), width=int(2*S))
    d.ellipse([(154)*S,(393)*S,(186)*S,(425)*S], fill=MK_SHELL, outline=C(120,80,44), width=int(2*S))

def build():
    jj = minifig(JJ_RED, JJ_LEG, JJ_WHITE, jj_head_extra, jj_torso_extra,
                 hand_fill=JJ_WHITE, arm_fill=JJ_RED)
    mk = minifig(MK_GREEN, MK_GREEN_D, MK_GREEN, mk_head_extra, mk_torso_extra,
                 hand_fill=MK_GREEN, arm_fill=MK_GREEN)
    jj.save("jj.png"); mk.save("mikey.png")
    for name, s in [("jj", jj), ("mikey", mk)]:
        bg = Image.new("RGB", (s.size[0]+60, s.size[1]+60), (150, 205, 255))
        bg.paste(s, (30, 30), s); bg.save(f"preview_{name}.png")
        print(name, s.size)

if __name__ == "__main__":
    build()
