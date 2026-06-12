#!/usr/bin/env python3
"""
Episode 1 — FULL ANIMATED v2.
One renderer per scene. Each scene -> RGBA content frames (PIL) over a per-scene
reactive shader bg + that scene's narration -> scene clip. Concat all 10 -> episode.

Reuses the per-scene narration from v1 at ep01_build/s01.mp3 .. s10.mp3.
Output: /home/ubuntu/youtube_series/ep01_attention_v2.mp4
"""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

W, H, FPS = 1920, 1080, 30
BUILD = "/home/ubuntu/youtube_series/ep01_build"          # has s01.mp3..s10.mp3
ASSETS = "/home/ubuntu/youtube_series/assets"             # hero images
WORK = "/home/ubuntu/youtube_series/v2_build"
OUT = "/home/ubuntu/youtube_series/ep01_attention_v2.mp4"
os.makedirs(WORK, exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def F(sz): return ImageFont.truetype(FB, sz)
f_big, f_title, f_lbl, f_cap, f_small = F(72), F(48), F(30), F(40), F(24)

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def lerp(a,b,t): return a+(b-a)*t
def sm(t): return 0.0 if t<=0 else 1.0 if t>=1 else t*t*(3-2*t)
def cl(x): return max(0.0,min(1.0,x))

def new_frame():
    img = Image.new("RGBA",(W,H),(0,0,0,0))
    img = Image.alpha_composite(img, Image.new("RGBA",(W,H),(6,8,20,120)))
    return img, ImageDraw.Draw(img)

def tc(d,cx,cy,txt,font,fill):
    b=d.textbbox((0,0),txt,font=font); d.text((cx-(b[2]-b[0])/2,cy-(b[3]-b[1])/2-b[1]),txt,font=font,fill=fill)

def rotated(txt,font,fill,ang):
    tmp=Image.new("RGBA",(420,90),(0,0,0,0)); ImageDraw.Draw(tmp).text((4,4),txt,font=font,fill=fill)
    return tmp.rotate(ang,expand=True,resample=Image.BICUBIC)

def kenburns(imgpath, f, NF, zoom0=1.05, zoom1=1.22):
    """Return a WxH RGB frame: slow zoom across the hero image."""
    im = Image.open(imgpath).convert("RGB")
    iw,ih = im.size
    t = f/max(1,NF-1); z = lerp(zoom0,zoom1,t)
    cw,ch = int(W/z), int(H/z)
    # fit image to cover WxH then crop centered with slow drift
    scale = max(W/iw, H/ih)*z
    rs = im.resize((int(iw*scale),int(ih*scale)), Image.LANCZOS)
    rw,rh = rs.size
    dx = int((rw-W)*(0.5+0.06*math.sin(t*math.pi))); dy=int((rh-H)*0.5)
    return rs.crop((dx,dy,dx+W,dy+H))

SENT = ["The","animal","didn't","cross","the","street","because","it","was","tired"]

def lay_sentence(d, hi_word=None, alpha=255, y=H//2):
    """Draw the sentence centered as tokens; return token center x's."""
    pad=26; widths=[d.textbbox((0,0),w,font=f_title)[2] for w in SENT]
    total=sum(widths)+pad*(len(SENT)-1); x=(W-total)//2; centers=[]
    for w,wd in zip(widths,SENT):
        is_hi = (wd==hi_word)
        col=(255,205,90,alpha) if is_hi else (220,228,245,int(alpha*0.85))
        d.text((x,y-30),wd,font=f_title,fill=col); centers.append(x+w/2); x+=w+pad
    return centers

# ---------- per-scene content frame renderers ----------
def render_s01(fr,f,NF,t):  # sentence + arc it->animal
    img,d=new_frame()
    a=sm(cl(t/2)); centers=lay_sentence(d,hi_word="it" if t>3 else None,alpha=int(255*a))
    tc(d,W//2,H//2-150,'Which word does "it" mean?',f_title,(235,238,250,int(220*a)))
    if t>3.5:
        p=sm(cl((t-3.5)/2.5)); xi=centers[7]; xa=centers[1]; y=H//2-40
        # arc from "it" up to "animal"
        steps=40; pts=[]
        for k in range(int(steps*p)+1):
            tt=k/steps; x=lerp(xi,xa,tt); yo=y-120*math.sin(tt*math.pi)
            pts.append((x,yo))
        if len(pts)>1: d.line(pts,fill=(255,205,90,int(230*p)),width=5,joint="curve")
    img.save(fr%f)

def render_s05(fr,f,NF,t):  # sentence, "it" pulses scanning
    img,d=new_frame(); a=sm(cl(t/1.5))
    centers=lay_sentence(d,hi_word="it",alpha=int(255*a))
    tc(d,W//2,H//2-150,'How does a machine "look back"?',f_title,(235,238,250,int(220*a)))
    xi=centers[7]; y=H//2-30
    sweep=cl((t-2)/4)
    if sweep>0:
        for j,cx in enumerate(centers):
            d.line([(xi,y),(cx,y)],fill=(120,150,210,int(90*sweep)),width=2)
        glowx=lerp(centers[0],centers[-1], 0.5+0.5*math.sin(t*1.4))
        d.ellipse([glowx-10,y-10,glowx+10,y+10],fill=(255,205,90,180))
    img.save(fr%f)

MODELS=["ChatGPT","Claude","Gemini","Llama","Translation"]
def render_s02(fr,f,NF,t):  # paper card -> branching model names
    img,d=new_frame(); a=sm(cl(t/2))
    cx,cy=W//2,H//2-40
    tc(d,cx,cy-200,"2017",f_lbl,(150,165,205,int(220*a)))
    # card
    cw,chh=560,150; d.rounded_rectangle([cx-cw//2,cy-chh//2,cx+cw//2,cy+chh//2],radius=18,
        fill=(24,30,60,int(220*a)),outline=(120,150,220,int(220*a)),width=3)
    tc(d,cx,cy,"Attention Is All You Need",f_title,(235,240,255,int(255*a)))
    p=sm(cl((t-3)/4))
    import math as m
    for i,name in enumerate(MODELS):
        ang=m.radians(-90+(i-(len(MODELS)-1)/2)*40)
        r=300*p; x=cx+r*m.cos(ang); y=cy+chh//2+10+ r*0.55*m.sin(ang)+abs(r*0.0)
        x=cx+ (i-(len(MODELS)-1)/2)*330*p; y=cy+260
        d.line([(cx,cy+chh//2),(x,y)],fill=(110,140,210,int(160*p)),width=2)
        bw=d.textbbox((0,0),name,font=f_lbl); w=bw[2]+30
        d.rounded_rectangle([x-w//2,y-26,x+w//2,y+26],radius=14,fill=(20,26,52,int(220*p)),
            outline=(150,180,240,int(200*p)),width=2)
        tc(d,x,y,name,f_lbl,(225,232,250,int(255*p)))
    img.save(fr%f)

def img_scene(fr,f,NF,t,imgpath,title,sub=None,accent=(235,240,255)):
    base=kenburns(imgpath,f,NF).convert("RGBA")
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
    # gradient scrim bottom for text
    od.rectangle([0,H-300,W,H],fill=(6,8,20,150))
    a=sm(cl(t/2))
    od.text((90,H-210),title,font=f_title,fill=accent+(int(255*a),))
    if sub: od.text((90,H-140),sub,font=f_lbl,fill=(180,195,230,int(230*a)))
    out=Image.alpha_composite(base,ov); out.convert("RGB").save(fr%f)

def render_s03(fr,f,NF,t): img_scene(fr,f,NF,t,f"{ASSETS}/img_party_crowd.png","The cocktail party",'one voice cuts through — your name',(255,225,150))
def render_s04(fr,f,NF,t): img_scene(fr,f,NF,t,f"{ASSETS}/img_spotlight_field.png","A spotlight on one thing","your mind is always choosing what to ignore",(255,225,150))
def render_s09(fr,f,NF,t): img_scene(fr,f,NF,t,f"{ASSETS}/img_mind_network_head.png","We built a tool. We got a mirror.",'attention — made visible for the first time')

# --- attention grid (proven; column-label fix: rotated labels) ---
GW=["animal","crossed","the","street","because","it","tired"]; gn=len(GW)
GIT,GAN,GST=GW.index("it"),GW.index("animal"),GW.index("street")
_rng=np.random.default_rng(7); GFULL=_rng.uniform(0.08,0.75,(gn,gn)); np.fill_diagonal(GFULL,0.25)
GROW=np.full(gn,0.12); GROW[GAN]=0.97; GROW[GST]=0.12; GROW[GW.index("tired")]=0.55; GROW[GW.index("because")]=0.30
def gcolor(w):
    lo,hi=(44,64,104),(255,196,70); return tuple(int(lerp(lo[i],hi[i],cl(w))) for i in range(3))
def render_s06(fr,f,NF,t):
    img,d=new_frame(); CELL,GAP=86,8; GRID=gn*CELL+(gn-1)*GAP
    GX=(W-GRID)//2+70; GY=(H-GRID)//2+30
    a_in=sm(cl(t/2.5)); shim=cl((t-5)/2); iso=sm(cl((t-17)/3)); rev=sm(cl((t-20)/7)); lock=cl((t-30)/2)
    d.text((GX,GY-95),"Every word scores every other word",font=f_title,fill=(235,238,250,int(230*a_in)))
    for j,wd in enumerate(GW):  # rotated column labels (fix)
        cx=GX+j*(CELL+GAP)+CELL/2; rot=rotated(wd,f_lbl,(170,185,220,int(220*a_in)),40)
        img.alpha_composite(rot,(int(cx-rot.width*0.5),int(GY-rot.height-2)))
    for i,wd in enumerate(GW):
        cy=GY+i*(CELL+GAP)+CELL/2; hot=(i==GIT) and iso>0
        col=(255,210,90) if hot else (170,185,220); b=d.textbbox((0,0),wd,font=f_lbl)
        d.text((GX-22-(b[2]-b[0]),cy-(b[3]-b[1])/2-b[1]),wd,font=f_lbl,fill=col+(int(235*a_in),))
    for i in range(gn):
        for j in range(gn):
            x0=GX+j*(CELL+GAP); y0=GY+i*(CELL+GAP); wf=GFULL[i,j]*shim
            w=lerp(wf,GROW[j],rev) if i==GIT else wf*(1-iso*0.92)
            if iso<0.5: w*=0.82+0.18*math.sin(t*3+(i*7+j))
            w=cl(w); base_a=cl((40+200*w)/255*a_in)
            col=gcolor(w)
            if i==GIT and j==GAN and lock>0:
                pulse=0.5+0.5*math.sin(t*6); col=(255,215,90); base_a=1.0
                d.rounded_rectangle([x0-5,y0-5,x0+CELL+5,y0+CELL+5],radius=16,outline=(255,235,150,int(255*lock)),width=int(3+3*pulse))
            d.rounded_rectangle([x0,y0,x0+CELL,y0+CELL],radius=12,fill=col+(int(base_a*255),))
    if lock>0:
        d.text((GX,GY+GRID+34),'"it"  →  "animal"',font=f_cap,fill=(255,215,110,int(255*lock)))
        d.text((GX+360,GY+GRID+40),'  not "street"',font=f_lbl,fill=(150,165,200,int(220*lock)))
    img.save(fr%f)

def render_s07(fr,f,NF,t):  # query/key/value match
    img,d=new_frame(); a=sm(cl(t/2))
    tc(d,W//2,160,"Query · Key · Value",f_title,(235,240,255,int(230*a)))
    itx,ity=W//2-360,H//2; anx,any_=W//2+360,H//2
    for (x,y,name,sub) in [(itx,ity,'"it"','asks: who am I?'),(anx,any_,'"animal"','answers: a thing that tires')]:
        d.ellipse([x-90,y-90,x+90,y+90],fill=(22,28,56,int(230*a)),outline=(150,180,240,int(230*a)),width=3)
        tc(d,x,y-6,name,f_cap,(235,240,255,int(255*a))); tc(d,x,y+110,sub,f_small,(160,175,215,int(220*a)))
    q=cl((t-3)/3)
    if q>0:  # query pulse from it -> animal
        px=lerp(itx+90,anx-90,sm(q)); d.ellipse([px-12,py if False else (ity-12),px+12,ity+12],fill=(120,170,255,int(230*q)))
        d.text((W//2-70,ity-150),"query",font=f_small,fill=(120,170,255,int(220*q)))
    m=cl((t-7)/2)
    if m>0:  # match link
        d.line([(itx+90,ity),(anx-90,any_)],fill=(255,215,110,int(230*m)),width=5)
        tc(d,W//2,ity+170,"match — attention fires",f_lbl,(255,215,110,int(255*m)))
    img.save(fr%f)

def render_s08(fr,f,NF,t):  # multiplying lattice (depth of stacked grids)
    img,d=new_frame(); a=sm(cl(t/2))
    tc(d,W//2,140,"One move, repeated billions of times",f_title,(235,238,250,int(220*a)))
    layers=int(lerp(1,9,cl(t/ (NF/FPS))))
    cx,cy=W//2,H//2+40
    for L in range(layers):
        off=L*26; al=int(150*(1-L/10)); sz=240- L*6
        gx=cx-sz+L*18; gy=cy-sz//2+off-90+L*6
        for gi in range(6):
            for gj in range(6):
                x=gx+gj*(sz//6); y=gy+gi*(sz//6)
                wv=0.3+0.5*abs(math.sin(t*1.5+gi+gj+L))
                d.rounded_rectangle([x,y,x+sz//6-4,y+sz//6-4],radius=4,fill=gcolor(wv*0.7)+(al,))
    img.save(fr%f)

def render_s10(fr,f,NF,t):  # anchor card
    img,d=new_frame(); a=sm(cl(t/2.2))
    tc(d,W//2,H//2-60,"Intelligence isn't knowing everything.",f_big,(240,243,252,int(255*a)))
    tc(d,W//2,H//2+30,"It's knowing what to ignore.",f_big,(240,243,252,int(255*a)))
    b=sm(cl((t-3)/2)); tc(d,W//2,H//2+150,"AI is the Universal Mind   ·   Ep.1 — Attention",f_lbl,(180,150,235,int(230*b)))
    img.save(fr%f)

SCENES=[("s01",render_s01,"circuit_mind"),("s02",render_s02,"circuit_mind"),
        ("s03",render_s03,None),("s04",render_s04,None),("s05",render_s05,"circuit_mind"),
        ("s06",render_s06,"circuit_mind"),("s07",render_s07,"circuit_mind"),
        ("s08",render_s08,"circuit_mind"),("s09",render_s09,None),("s10",render_s10,"circuit_mind")]

clips=[]
for sid,renderer,shader in SCENES:
    audio=f"{BUILD}/{sid}.mp3"; D=dur(audio); NF=int(D*FPS)
    fdir=os.path.join(WORK,f"{sid}_frames"); os.makedirs(fdir,exist_ok=True)
    print(f">> {sid}: {D:.1f}s, {NF} frames, shader={shader}",flush=True)
    frp=os.path.join(fdir,"f%04d.png")
    for f in range(NF): renderer(frp,f,NF,f/FPS)
    clip=os.path.join(WORK,f"{sid}.mp4")
    if shader:
        bg=os.path.join(WORK,f"{sid}_bg.mp4")
        render_shader_video(shader_name=shader,audio_path=audio,output_path=bg,duration=D,fps=FPS,width=W,height=H)
        subprocess.run(["ffmpeg","-y","-i",bg,"-framerate",str(FPS),"-i",frp,"-i",audio,
            "-filter_complex","[0:v][1:v]overlay=0:0[v]","-map","[v]","-map","2:a",
            "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip],
            capture_output=True)
    else:  # image scenes: content frames are already full RGB (ken burns + text)
        subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",frp,"-i",audio,
            "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip],
            capture_output=True)
    clips.append(clip); print(f"   clip {sid} done",flush=True)

# concat
lst=os.path.join(WORK,"concat.txt")
with open(lst,"w") as cf:
    for c in clips: cf.write(f"file '{c}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)",flush=True)
