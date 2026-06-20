#!/usr/bin/env python3
"""LinkedIn Product images for the VR/MR App Dev course — 1280x720, dark+gold brand.
Output: course_assets/linkedin_product/vr_product_N.jpg"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=os.path.dirname(os.path.abspath(__file__))
F=f"{HERE}/youtube_series/thumbs/fonts"
OUT=f"{HERE}/course_assets/linkedin_product"; os.makedirs(OUT,exist_ok=True)
POP=f"{F}/Poppins-ExtraBold.ttf"; POPB=f"{F}/Poppins-Bold.ttf"; MUK=f"{F}/Mukta-ExtraBold.ttf"
W,H=1280,720
GOLD=(255,201,82); INK=(247,249,255); BLUE=(120,156,235); PURPLE=(186,148,255); DIMW=(168,178,210); GREEN=(127,214,160)
YY,XX=np.mgrid[0:H,0:W]

def base():
    a=np.zeros((H,W,3),np.float32)
    for y in range(H):
        t=y/H; a[y,:,0]=20*(1-t)+5*t; a[y,:,1]=26*(1-t)+7*t; a[y,:,2]=62*(1-t)+15*t
    return a
def glow(a,cx,cy,r,col,s=1.0,p=2.2):
    d=np.sqrt((XX-cx)**2+(YY-cy)**2); g=np.clip(1-d/r,0,1)**p*s
    for c in range(3): a[...,c]+=g*col[c]
    return a
def img(a): return Image.fromarray(np.clip(a,0,255).astype(np.uint8),"RGB").convert("RGBA")
def fnt(p,s): return ImageFont.truetype(p,s,layout_engine=ImageFont.Layout.RAQM)
def sh(d,xy,t,f,fill,off=4,s=(0,0,0,210)):
    x,y=xy
    for dx,dy in [(off,off),(off,0),(0,off)]: d.text((x+dx,y+dy),t,font=f,fill=s)
    d.text((x,y),t,font=f,fill=fill)
def wordmark(d):
    wm=fnt(POPB,30); sh(d,(64,46),"TrigunAI",wm,GOLD,3)
    sw=d.textlength("TrigunAI",font=wm); d.text((64+sw+14,53),"Trigun Studio",font=fnt(POPB,22),fill=DIMW)
def headset(d,cx,cy,sc=1.0,col=GOLD):
    w,h=int(150*sc),int(78*sc)
    d.rounded_rectangle([cx-w,cy-h,cx+w,cy+h],radius=int(34*sc),outline=col,width=int(6*sc))
    for s in (-1,1):  # two lenses
        d.ellipse([cx+s*int(58*sc)-int(34*sc),cy-int(30*sc),cx+s*int(58*sc)+int(34*sc),cy+int(30*sc)],outline=col,width=int(5*sc))
    d.line([cx-w,cy-int(20*sc),cx-w-int(46*sc),cy-int(52*sc)],fill=col,width=int(5*sc))   # strap
    d.line([cx+w,cy-int(20*sc),cx+w+int(46*sc),cy-int(52*sc)],fill=col,width=int(5*sc))

def hero():
    a=base(); a=glow(a,1010,330,420,BLUE,0.10); a=glow(a,1010,300,240,GOLD,0.9,2.6); a=glow(a,1010,300,90,(255,240,210),0.8,2.0)
    im=img(a); d=ImageDraw.Draw(im); wordmark(d); headset(d,1010,300,1.05,GOLD)
    f1=fnt(POP,72); sh(d,(64,250),"Build & Ship Your",f1,INK,5); sh(d,(64,332),"First VR/MR App",f1,INK,5)
    d.text((64,210),"COURSE",font=fnt(POPB,30),fill=GOLD)
    d.text((66,438),"9 modules · free on YouTube · English + हिंदी",font=fnt(POPB,30,) if False else fnt(MUK,30),fill=DIMW)
    d.text((64,520),"learn.trigunai.com",font=fnt(POPB,26),fill=GOLD)
    im.convert("RGB").save(f"{OUT}/vr_product_1_hero.jpg","JPEG",quality=92); print("✔ hero")

def modules():
    a=base(); a=glow(a,1080,150,360,GOLD,0.5,2.6)
    im=img(a); d=ImageDraw.Draw(im); wordmark(d)
    sh(d,(64,150),"Zero to a shipped Quest app",fnt(POP,50),INK,4)
    mods=["Your First VR Scene","Your AI Coding Partner","Hands & Grabbing","UI & Menus in VR","Audio & Ambience","Movement & Locomotion","Saving & Persistence","Multiplayer","Mixed Reality"]
    nf=fnt(POP,30); tf=fnt(POPB,28)
    for i,m in enumerate(mods):
        col=i//5; row=i%5; x=70+col*620; y=250+row*86
        d.ellipse([x,y,x+52,y+52],outline=GOLD,width=3); d.text((x+15 if i+1<10 else x+8,y+8),str(i+1),font=nf,fill=GOLD)
        d.text((x+74,y+10),m,font=tf,fill=INK)
    im.convert("RGB").save(f"{OUT}/vr_product_2_modules.jpg","JPEG",quality=92); print("✔ modules")

def model():
    a=base(); a=glow(a,360,360,300,GREEN,0.25); a=glow(a,920,360,320,GOLD,0.45,2.4)
    im=img(a); d=ImageDraw.Draw(im); wordmark(d)
    sh(d,(64,140),"Free to understand. Paid to transform.",fnt(POP,42),INK,4)
    # two panels
    d.rounded_rectangle([70,250,610,640],radius=22,outline=(60,90,70),width=2)
    d.text((100,278),"FREE",font=fnt(POP,40),fill=GREEN); d.text((100,340),"Recorded Course",font=fnt(POPB,32),fill=INK)
    for k,line in enumerate(["9 modules on YouTube","English + हिंदी","Lifetime access","Learn the craft"]):
        d.text((100,400+k*46),"•  "+line,font=fnt(MUK,26),fill=DIMW)
    d.rounded_rectangle([670,250,1210,640],radius=22,outline=(90,74,30),width=2)
    d.text((700,278),"LIVE COHORT",font=fnt(POP,38),fill=GOLD); d.text((700,340),"Build your own app",font=fnt(POPB,32),fill=INK)
    for k,line in enumerate(["Provided NVIDIA GPU + Isaac Sim","Class taught inside VR","Small-group, live","Ship a real app"]):
        d.text((700,400+k*46),"•  "+line,font=fnt(MUK,26),fill=DIMW)
    im.convert("RGB").save(f"{OUT}/vr_product_3_model.jpg","JPEG",quality=92); print("✔ model")

def moat():
    a=base(); a=glow(a,640,360,500,GOLD,0.4,2.6); a=glow(a,640,330,150,(255,240,210),0.5,2.0)
    im=img(a); d=ImageDraw.Draw(im); wordmark(d)
    sh(d,(64,140),"The part no other course offers",fnt(POP,46),INK,4)
    items=[("⚡","Provided NVIDIA GPU"),("◈","Isaac Sim, set up for you"),("▣","Class taught inside VR")]
    for i,(ic,t) in enumerate(items):
        y=300+i*100
        d.text((150,y),ic,font=fnt(POP,46),fill=GOLD); d.text((230,y+4),t,font=fnt(POPB,40),fill=INK)
    d.text((150,610),"learn.trigunai.com",font=fnt(POPB,28),fill=GOLD)
    im.convert("RGB").save(f"{OUT}/vr_product_4_moat.jpg","JPEG",quality=92); print("✔ moat")

hero(); modules(); model(); moat()
print("done ->",OUT)
