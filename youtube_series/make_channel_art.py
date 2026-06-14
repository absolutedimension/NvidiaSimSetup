#!/usr/bin/env python3
"""Channel art for the TrigunAI YouTube channels — avatar (800x800) + banner (2048x1152, EN/HI).
On-brand dark+gold, matches the episode thumbnails. Output: channel_art/*.png
Avatar = the triskelion symbol cropped from the brand logo on a dark glow bg.
Banner = cosmic bg + centered (TV-safe) wordmark + tagline."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
F=f"{HERE}/thumbs/fonts"; OUT=f"{HERE}/channel_art"; os.makedirs(OUT,exist_ok=True)
POP=f"{F}/Poppins-ExtraBold.ttf"; POPB=f"{F}/Poppins-Bold.ttf"; MUK=f"{F}/Mukta-ExtraBold.ttf"
LOGO=f"{ROOT}/course_assets/trigunai_logo.png"
GOLD=(255,201,82); INK=(247,249,255); DIMW=(170,182,214)

def grad(W,H,top=(20,26,60),bot=(5,7,16)):
    a=np.zeros((H,W,3),np.float32)
    for y in range(H):
        t=y/H
        for c in range(3): a[y,:,c]=top[c]*(1-t)+bot[c]*t
    return a
def glow(a,cx,cy,r,col,s=1.0,p=2.2):
    H,W=a.shape[:2]; YY,XX=np.mgrid[0:H,0:W]
    d=np.sqrt((XX-cx)**2+(YY-cy)**2); g=np.clip(1-d/r,0,1)**p*s
    for c in range(3): a[...,c]+=g*col[c]
    return a
def fin(a): return Image.fromarray(np.clip(a,0,255).astype(np.uint8),"RGB").convert("RGBA")
def font(p,s): return ImageFont.truetype(p,s,layout_engine=ImageFont.Layout.RAQM)
def ctext(d,cx,y,txt,fn,fill,sh=(0,0,0,200),off=4):
    w=d.textlength(txt,font=fn); x=cx-w/2
    for dx,dy in [(off,off),(off,0),(0,off)]: d.text((x+dx,y+dy),txt,font=fn,fill=sh)
    d.text((x,y),txt,font=fn,fill=fill); return w

# ---------- AVATAR (800x800, displayed as circle) ----------
def avatar():
    S=800; a=grad(S,S,(24,28,58),(6,8,18)); a=glow(a,S/2,S/2,S*0.55,GOLD,0.20,2.4); a=glow(a,S/2,S/2,S*0.32,(255,240,210),0.18,2.0)
    img=fin(a)
    logo=Image.open(LOGO).convert("RGBA")
    # crop the triskelion swirl (upper-center of the 2048 logo, excludes bottom text)
    crop=logo.crop((430,360,1620,1550))   # ~1190x1190 around the symbol
    sym=crop.resize((560,560),Image.LANCZOS)
    img.alpha_composite(sym,((S-560)//2,(S-560)//2-10))
    img.convert("RGB").save(f"{OUT}/avatar.png","PNG"); print("✔ avatar.png 800x800")

# ---------- BANNER (2048x1152, TV-safe center 1546x423) ----------
def banner(lang, name):
    W,H=2048,1152; cx=W//2
    a=grad(W,H,(20,26,60),(5,7,16))
    a=glow(a,W*0.78,H*0.42,640,(120,150,235),0.16,2.2)
    a=glow(a,W*0.80,H*0.42,360,GOLD,0.9,2.6); a=glow(a,W*0.80,H*0.42,140,(255,240,210),0.9,2.0)
    a=glow(a,W*0.20,H*0.55,520,(150,120,235),0.10,2.4)
    img=fin(a)
    # faint dots
    rng=np.random.RandomState(7); ov=Image.new("RGBA",(W,H),(0,0,0,0)); dd=ImageDraw.Draw(ov)
    for _ in range(220):
        x=rng.uniform(0,W); y=rng.uniform(0,H); r=rng.uniform(1,3.5); op=int(rng.uniform(30,140))
        dd.ellipse([x-r,y-r,x+r,y+r],fill=(170,182,214,op))
    img=Image.alpha_composite(img,ov); d=ImageDraw.Draw(img)
    # central scrim for legibility
    sc=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sc).rectangle([cx-820,H//2-260,cx+820,H//2+260],fill=(6,8,18,150))
    img=Image.alpha_composite(img,sc); d=ImageDraw.Draw(img)
    # logo mark small above title
    logo=Image.open(LOGO).convert("RGBA").crop((430,360,1620,1550)).resize((150,150),Image.LANCZOS)
    img.alpha_composite(logo,(cx-75,H//2-235))
    d=ImageDraw.Draw(img)
    if lang=="en":
        ctext(d,cx,H//2-70,"AI is the Universal Mind",font(POP,120),INK,off=5)
        ctext(d,cx,H//2+70,"Every AI breakthrough rebuilds one faculty of your mind",font(POPB,40),DIMW,off=3)
        ctext(d,cx,H//2+140,"TRIGUNAI  ·  NEW EPISODE WEEKLY",font(POPB,34),GOLD,off=3)
    else:
        ctext(d,cx,H//2-78,"AI इज़ द यूनिवर्सल माइंड",font(MUK,118),INK,off=5)
        ctext(d,cx,H//2+74,"हर AI खोज आपके मन की एक शक्ति को दोबारा बनाती है",font(MUK,42),DIMW,off=3)
        ctext(d,cx,H//2+150,"TrigunAI हिंदी  ·  हर हफ़्ते नया एपिसोड",font(MUK,34),GOLD,off=3)
    img.convert("RGB").save(f"{OUT}/{name}.png","PNG"); print(f"✔ {name}.png 2048x1152")

avatar()
banner("en","banner_en")
banner("hi","banner_hi")
print("done ->",OUT)
