#!/usr/bin/env python3
"""Generate 6 YouTube thumbnails (3 episodes x EN/HI) — procedural dark+gold bases + bold text.
Fully local: numpy bases, PIL text (raqm shapes Devanagari). Output: thumbs/out/*.jpg (1280x720)."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE=os.path.dirname(os.path.abspath(__file__))
F=f"{HERE}/thumbs/fonts"; OUT=f"{HERE}/thumbs/out"; os.makedirs(OUT,exist_ok=True)
POP=f"{F}/Poppins-ExtraBold.ttf"; POPB=f"{F}/Poppins-Bold.ttf"; MUK=f"{F}/Mukta-ExtraBold.ttf"
W,H=1280,720
GOLD=(255,201,82); INK=(247,249,255); BLUE=(120,156,235); PURPLE=(186,148,255); DIMW=(165,176,208)
YY,XX=np.mgrid[0:H,0:W]

def base():
    a=np.zeros((H,W,3),np.float32)
    for y in range(H):
        t=y/H
        a[y,:,0]=20*(1-t)+5*t; a[y,:,1]=26*(1-t)+7*t; a[y,:,2]=60*(1-t)+15*t
    return a
def glow(a,cx,cy,r,col,s=1.0,p=2.2):
    d=np.sqrt((XX-cx)**2+(YY-cy)**2); g=np.clip(1-d/r,0,1)**p*s
    for c in range(3): a[...,c]+=g*col[c]
    return a
def ring(a,cx,cy,R,wd,col,s=1.0):
    d=np.sqrt((XX-cx)**2+(YY-cy)**2); g=np.clip(1-np.abs(d-R)/wd,0,1)**2*s
    for c in range(3): a[...,c]+=g*col[c]
    return a
def finish(a): return Image.fromarray(np.clip(a,0,255).astype(np.uint8),"RGB").convert("RGBA")

def dots(img,n,xr,yr,cols,rmin,rmax,opr,seed):
    rng=random.Random(seed); ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for _ in range(n):
        x=rng.uniform(*xr); y=rng.uniform(*yr); r=rng.uniform(rmin,rmax); op=int(rng.uniform(*opr))
        c=rng.choice(cols); d.ellipse([x-r,y-r,x+r,y+r],fill=(c[0],c[1],c[2],op))
    return Image.alpha_composite(img,ov)

def left_scrim(img,strength=0.86):
    a=np.array(img).astype(np.float32)
    gx=np.clip(1-XX/820,0,1); gy=np.clip((YY-120)/600,0,1)
    al=np.clip(strength*(0.62*gx+0.55*gy),0,0.9)
    a[...,:3]*=(1-al[...,None]); return Image.fromarray(a.astype(np.uint8),"RGBA")

def ep1():   # attention — one bright gold focus among dim points
    a=base(); a=glow(a,912,330,430,(120,150,235),0.10); a=glow(a,912,330,250,GOLD,1.15,2.6); a=glow(a,912,330,90,(255,240,210),1.0,2.0)
    img=finish(a); img=dots(img,150,(560,1260),(60,680),[BLUE,DIMW,PURPLE],1,4,(40,150),11)
    return img
def ep2():   # learning — glowing gold loop ring
    a=base(); a=glow(a,930,360,360,(120,150,235),0.10); a=ring(a,930,360,210,46,GOLD,1.25); a=ring(a,930,360,210,16,(255,240,210),1.0)
    img=finish(a); img=dots(img,90,(600,1260),(80,650),[GOLD,BLUE,DIMW],1,3,(40,140),7)
    return img
def ep3():   # imagination — noise resolving into gold form
    a=base(); a=glow(a,980,360,330,GOLD,1.1,2.6); a=glow(a,980,360,110,(255,240,210),1.0,2.0)
    img=finish(a)
    img=dots(img,520,(40,720),(60,680),[DIMW,BLUE,PURPLE,(120,130,150)],1,3,(40,160),3)   # static left
    img=dots(img,70,(760,1200),(150,580),[GOLD,(255,235,200)],1,3,(60,170),5)
    return img

def ep4():   # meaning — bright "word" points in space, constellation feel
    a=base(); a=glow(a,900,330,400,(120,150,235),0.10)
    a=glow(a,860,250,120,GOLD,1.0,2.4); a=glow(a,1060,360,120,GOLD,1.0,2.4)
    a=glow(a,940,520,110,GOLD,0.9,2.4); a=glow(a,900,360,70,(255,240,210),1.0,2.0)
    img=finish(a); img=dots(img,160,(560,1260),(60,680),[BLUE,DIMW,PURPLE,GOLD],1,4,(40,150),14)
    return img
def ep5():   # intuition — one bright firing node within a network
    a=base(); a=glow(a,930,350,420,(120,150,235),0.12); a=glow(a,930,350,230,GOLD,1.2,2.6); a=glow(a,930,350,80,(255,240,210),1.0,2.0)
    a=glow(a,760,250,70,GOLD,0.6,2.4); a=glow(a,1110,470,70,GOLD,0.6,2.4)
    img=finish(a); img=dots(img,140,(560,1260),(60,680),[BLUE,DIMW,PURPLE,GOLD],1,4,(40,150),15)
    return img

def ep6():   # will — a goal-point and the pull toward it
    a=base(); a=glow(a,1030,360,300,(120,150,235),0.10); a=glow(a,1030,360,200,GOLD,1.2,2.6); a=glow(a,1030,360,72,(255,240,210),1.0,2.0)
    a=ring(a,1030,360,150,10,GOLD,0.7)
    img=finish(a)
    # converging trail of points pulling toward the goal
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); dd=ImageDraw.Draw(ov); rng=random.Random(6)
    for t in range(60):
        f=t/60.0; x=560+f*420+rng.uniform(-14,14); y=440-f*70+rng.uniform(-14,14); r=2+f*3
        op=int(70+f*150); dd.ellipse([x-r,y-r,x+r,y+r],fill=(255,201,82,op))
    img=Image.alpha_composite(img,ov)
    img=dots(img,90,(540,1240),(60,680),[BLUE,DIMW,PURPLE],1,3,(40,140),16)
    return img

def font(path,size): return ImageFont.truetype(path,size,layout_engine=ImageFont.Layout.RAQM)
def wrap(d,txt,fn,maxw):
    out=[]; cur=""
    for w in txt.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=fn)<=maxw: cur=t
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out
def shadow(d,xy,txt,fn,fill,off=5,sh=(0,0,0,210)):
    x,y=xy
    for dx,dy in [(off,off),(off,0),(0,off)]: d.text((x+dx,y+dy),txt,font=fn,fill=sh)
    d.text((x,y),txt,font=fn,fill=fill)

def compose(imgfn, big, tag, lang, name):
    img=imgfn(); img=left_scrim(img); d=ImageDraw.Draw(img)
    bigfont_path = POP if lang=="en" else MUK
    tagfont_path = POPB if lang=="en" else MUK
    # wordmark
    wm=font(POPB,32); shadow(d,(70,52),"TrigunAI",wm,GOLD,3)
    sw=d.textlength("TrigunAI",font=wm)
    sub=font(POPB,24); d.text((70+sw+16,60),"AI is the Universal Mind",font=sub,fill=DIMW)
    # big text — adaptive size
    maxw=720
    for size in (132,120,110,100,92,84):
        bf=font(bigfont_path,size); lines=wrap(d,big,bf,maxw)
        if all(d.textlength(l,font=bf)<=maxw for l in lines) and len(lines)<=3: break
    lh=int(size*1.12); total=lh*len(lines)
    tagf=font(tagfont_path,40)
    y0=640-total-58
    shadow(d,(70,y0-58),tag,tagf,GOLD,3)
    y=y0
    for l in lines:
        shadow(d,(70,y),l,bf,INK,5); y+=lh
    img.convert("RGB").save(f"{OUT}/{name}.jpg","JPEG",quality=92)
    print("✔",name)

JOBS=[
 (ep1,"WHAT TO IGNORE","EP 1 · ATTENTION","en","thumb_ep01_en"),
 (ep1,"क्या अनदेखा करें","एपिसोड 1 · ध्यान","hi","thumb_ep01_hi"),
 (ep2,"CAN'T DELETE A HABIT","EP 2 · THE LEARNING LOOP","en","thumb_ep02_en"),
 (ep2,"आदत मिटती नहीं","एपिसोड 2 · सीखने का चक्र","hi","thumb_ep02_hi"),
 (ep3,"CREATION FROM NOISE","EP 3 · IMAGINATION","en","thumb_ep03_en"),
 (ep3,"शोर से सृजन","एपिसोड 3 · कल्पना","hi","thumb_ep03_hi"),
 (ep4,"MEANING IS A PLACE","EP 4 · MEANING","en","thumb_ep04_en"),
 (ep4,"अर्थ एक स्थान है","एपिसोड 4 · अर्थ","hi","thumb_ep04_hi"),
 (ep5,"WHAT IS A HUNCH?","EP 5 · INTUITION","en","thumb_ep05_en"),
 (ep5,"अंदेशा क्या है?","एपिसोड 5 · अंतर्ज्ञान","hi","thumb_ep05_hi"),
 (ep6,"WHAT IS WANTING?","EP 6 · WILL","en","thumb_ep06_en"),
 (ep6,"चाह क्या है?","एपिसोड 6 · इच्छा","hi","thumb_ep06_hi"),
]
for fn,big,tag,lang,name in JOBS: compose(fn,big,tag,lang,name)
print("done ->",OUT)
