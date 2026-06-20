#!/usr/bin/env python3
"""TrigunFlowArt channel assets: 2 video thumbnails (1280x720) + avatar (800x800) + banner (2048x1152).
Local numpy + PIL. Output: flowart/out/*."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(HERE))
F=f"{os.path.dirname(HERE)}/thumbs/fonts"; OUT=f"{HERE}/out"; os.makedirs(OUT,exist_ok=True)
POP=f"{F}/Poppins-ExtraBold.ttf"; POPB=f"{F}/Poppins-Bold.ttf"
LOGO=f"{ROOT}/course_assets/trigunai_logo.png"
GOLD=(255,201,82); INK=(247,249,255); VIOLET=(178,140,255); CYAN=(120,210,235); ROSE=(255,120,170); DIMW=(170,182,214)

def grad(W,H,top,bot):
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
def dots(img,n,xr,yr,cols,rmin,rmax,opr,seed):
    rng=random.Random(seed); ov=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    for _ in range(n):
        x=rng.uniform(*xr); y=rng.uniform(*yr); r=rng.uniform(rmin,rmax); op=int(rng.uniform(*opr))
        c=rng.choice(cols); d.ellipse([x-r,y-r,x+r,y+r],fill=(c[0],c[1],c[2],op))
    return Image.alpha_composite(img,ov)
def left_scrim(img,W,H,strength=0.84):
    a=np.array(img).astype(np.float32); YY,XX=np.mgrid[0:H,0:W]
    gx=np.clip(1-XX/(W*0.62),0,1); gy=np.clip((YY-H*0.16)/(H*0.8),0,1)
    al=np.clip(strength*(0.62*gx+0.5*gy),0,0.88)
    a[...,:3]*=(1-al[...,None]); return Image.fromarray(a.astype(np.uint8),"RGBA")
def shadow(d,xy,txt,fn,fill,off=5,sh=(0,0,0,210)):
    x,y=xy
    for dx,dy in [(off,off),(off,0),(0,off)]: d.text((x+dx,y+dy),txt,font=fn,fill=sh)
    d.text((x,y),txt,font=fn,fill=fill)
def ctext(d,cx,y,txt,fn,fill,off=4):
    w=d.textlength(txt,font=fn); shadow(d,(cx-w/2,y),txt,fn,fill,off); return w

# ---------- THUMBNAILS ----------
def thumb(name, tag, big, sub, mood):
    W,H=1280,720
    if mood=="dance":
        a=grad(W,H,(40,16,46),(10,6,18)); a=glow(a,920,300,520,VIOLET,0.20); a=glow(a,980,340,300,GOLD,1.0,2.6); a=glow(a,980,340,120,(255,240,210),0.9,2.0); a=glow(a,700,520,260,ROSE,0.25)
        cols=[GOLD,VIOLET,ROSE,(255,235,200)]
    else:
        a=grad(W,H,(10,22,46),(4,7,16)); a=glow(a,940,360,540,CYAN,0.18); a=glow(a,960,360,300,(120,160,235),0.8,2.6); a=glow(a,960,360,110,(220,240,255),0.9,2.0)
        cols=[CYAN,(120,160,235),DIMW]
    img=fin(a); img=dots(img,140,(540,1260),(40,690),cols,1,4,(40,150),hash(name)%97)
    img=left_scrim(img,W,H); d=ImageDraw.Draw(img)
    wm=font(POPB,30); shadow(d,(64,48),"TrigunFlowArt",wm,GOLD,3)
    tg=font(POPB,38); shadow(d,(64,150),tag,tg,(GOLD if mood=="dance" else CYAN),3)
    # big text adaptive
    for size in (150,134,120,108,96):
        bf=font(POP,size); lines=big.split("\n")
        if all(d.textlength(l,font=bf)<=760 for l in lines): break
    y=300
    for l in lines: shadow(d,(64,y),l,bf,INK,6); y+=int(size*1.06)
    sf=font(POPB,32); shadow(d,(66,y+6),sub,sf,DIMW,3)
    img.convert("RGB").save(f"{OUT}/{name}.jpg","JPEG",quality=92); print("✔",name)

# ---------- AVATAR ----------
def avatar():
    S=800; a=grad(S,S,(46,20,60),(10,6,20)); a=glow(a,S/2,S/2,S*0.55,VIOLET,0.30); a=glow(a,S/2,S/2,S*0.33,GOLD,0.22,2.2)
    img=fin(a)
    logo=Image.open(LOGO).convert("RGBA").crop((430,360,1620,1550)).resize((560,560),Image.LANCZOS)
    img.alpha_composite(logo,((S-560)//2,(S-560)//2-10))
    img.convert("RGB").save(f"{OUT}/avatar.png","PNG"); print("✔ avatar.png")

# ---------- BANNER ----------
def banner():
    W,H=2048,1152; cx=W//2
    a=grad(W,H,(44,18,58),(8,6,18))
    a=glow(a,W*0.74,H*0.45,640,VIOLET,0.22); a=glow(a,W*0.80,H*0.42,330,GOLD,0.8,2.6); a=glow(a,W*0.22,H*0.55,520,CYAN,0.14)
    img=fin(a); img=dots(img,240,(0,W),(0,H),[GOLD,VIOLET,CYAN,DIMW],1,3.5,(30,140),9)
    sc=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sc).rectangle([cx-840,H//2-250,cx+840,H//2+250],fill=(8,6,18,140))
    img=Image.alpha_composite(img,sc); d=ImageDraw.Draw(img)
    logo=Image.open(LOGO).convert("RGBA").crop((430,360,1620,1550)).resize((140,140),Image.LANCZOS)
    img.alpha_composite(logo,(cx-70,H//2-230)); d=ImageDraw.Draw(img)
    ctext(d,cx,H//2-80,"TrigunFlowArt",font(POP,116),INK,5)
    ctext(d,cx,H//2+70,"Music to enter flow — dance · focus · deep work",font(POPB,42),DIMW,3)
    ctext(d,cx,H//2+142,"1-HOUR ISOCHRONIC SESSIONS  ·  ALPHA & BETA",font(POPB,32),GOLD,3)
    img.convert("RGB").save(f"{OUT}/banner.png","PNG"); print("✔ banner.png")

thumb("thumb_flow_dance","1 HOUR · DANCE & MOVEMENT","ENTER\nTHE FLOW","130 BPM TECHNO  ·  10 Hz ALPHA","dance")
thumb("thumb_flow_focus","1 HOUR · STUDY & DEEP WORK","DEEP\nFOCUS","DEEP HOUSE  ·  BETA ISOCHRONIC","focus")
avatar(); banner()
print("done ->",OUT)
