#!/usr/bin/env python3
"""
Episode 2 — "The Learning Loop" — FULL ANIMATED.
Per-scene bespoke motion graphics over reactive circuit_mind shader + frozen audio.
Frames render to /dev/shm (RAM) with per-scene cleanup → no EBS I/O starvation.
Output: /home/ubuntu/youtube_series/ep02_attention_v2.mp4  (ep02_learning_v2.mp4)
"""
import os, sys, math, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.shader_service import render_shader_video

W, H, FPS = 1920, 1080, 30
BUILD = "/home/ubuntu/youtube_series/ep02_build"        # s01.mp3..s13.mp3 (frozen audio)
WORK  = "/home/ubuntu/youtube_series/ep02_v2"
SHM   = "/dev/shm/ep02_frames"
OUT   = "/home/ubuntu/youtube_series/ep02_learning_v2.mp4"
os.makedirs(WORK, exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(s): return ImageFont.truetype(FB, s)
f_big,f_title,f_lbl,f_cap,f_small = F(70),F(48),F(30),F(40),F(24)

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                     capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0
def lerp(a,b,t): return a+(b-a)*t
def sm(t): return 0.0 if t<=0 else 1.0 if t>=1 else t*t*(3-2*t)
def cl(x): return max(0.0,min(1.0,x))
def frame():
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    img=Image.alpha_composite(img,Image.new("RGBA",(W,H),(6,8,20,120)))
    return img, ImageDraw.Draw(img)
def tc(d,cx,cy,txt,font,fill):
    b=d.textbbox((0,0),txt,font=font); d.text((cx-(b[2]-b[0])/2,cy-(b[3]-b[1])/2-b[1]),txt,font=font,fill=fill)
def node(d,x,y,r,rgb,a):
    d.ellipse([x-r,y-r,x+r,y+r],fill=rgb+(int(a),))
GOLD=(255,200,80); BLUE=(110,150,235); GREY=(150,165,205); GREEN=(120,210,150)

# ---------------- scene renderers: render_sNN(d,img,t,NF) ----------------
def s01(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,200,"What do they share?",f_title,(235,238,250,int(230*a)))
    items=[("a child","learning to walk"),("a discipline","held for years"),("a robot","learning to balance")]
    xs=[W//2-560,W//2,W//2+560]; y=H//2
    for i,(t1,t2) in enumerate(items):
        ai=sm(cl((t-0.5-i*0.5)/1.2)); node(d,xs[i],y,46,GOLD,200*ai)
        tc(d,xs[i],y+90,t1,f_lbl,(235,238,250,int(230*ai))); tc(d,xs[i],y+128,t2,f_small,(160,175,215,int(200*ai)))
    p=sm(cl((t-3)/3))
    if p>0:
        d.line([(xs[0],y),(xs[0]+(xs[2]-xs[0])*p,y)],fill=(120,150,210,int(160*p)),width=3)
def s02(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,200,"Nobody writes the skill down",f_title,(235,238,250,int(230*a)))
    fade=cl((t-2)/4)
    # left: rules fading
    for i in range(5):
        al=int(180*(1-fade)*a); d.text((230,360+i*70),f"if x < {i}.5: stop", font=f_lbl, fill=(150,165,205,al))
    # right: web forming
    rng=np.random.default_rng(3); pts=rng.uniform([1150,330],[1750,820],(10,2))
    for i in range(len(pts)):
        for j in range(i+1,len(pts)):
            if np.linalg.norm(pts[i]-pts[j])<320:
                d.line([tuple(pts[i]),tuple(pts[j])],fill=(110,150,235,int(120*fade)),width=2)
    for p_ in pts: node(d,p_[0],p_[1],7,GOLD,200*fade)
def s03(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"The Learning Loop",f_title,(235,238,250,int(230*a)))
    cx,cy,R=W//2,H//2+40,210
    labels=["TRY","FEEDBACK","UPDATE","REPEAT"]; ang0=-90
    pos=[]
    for i in range(4):
        ang=math.radians(ang0+i*90); x=cx+R*math.cos(ang); y=cy+R*math.sin(ang); pos.append((x,y))
    for i in range(4):
        x,y=pos[i]; x2,y2=pos[(i+1)%4]
        d.line([(x,y),(x2,y2)],fill=(90,120,190,int(150*a)),width=3)
    spin=(t*0.6)%1
    for i in range(4):
        x,y=pos[i]; hot=abs(((i/4)-spin)%1)<0.18
        node(d,x,y,58,GOLD if hot else (40,55,95),(255 if hot else 200)*a)
        tc(d,x,y,labels[i],f_small,(20,20,30,255) if hot else (220,228,245,int(230*a)))
def s04(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"From effort to autopilot",f_title,(235,238,250,int(230*a)))
    cx,cy=W//2,H//2+30
    d.ellipse([cx-300,cy-180,cx+300,cy+180],outline=(120,140,200,int(180*a)),width=3)
    shift=sm(cl((t-2)/4))
    # prefrontal (front/right) glows then hands to basal (deep/left)
    front=(cx+170,cy-30); deep=(cx-120,cy+40)
    node(d,*front,70,GOLD,(220*(1-shift)+60)*a); tc(d,front[0],front[1]-110,"prefrontal cortex",f_small,(235,238,250,int(220*a)))
    node(d,*deep,70,GOLD,(60+200*shift)*a); tc(d,deep[0],deep[1]+110,"basal ganglia",f_small,(235,238,250,int(220*a)))
    if shift>0: d.line([front,deep],fill=(255,210,110,int(200*shift)),width=4)
    # effort bar drops
    eh=int(200*(1-shift)); d.rectangle([cx+360,cy-100,cx+390,cy+100],outline=(120,140,200,int(150*a)),width=2)
    d.rectangle([cx+360,cy+100-eh,cx+390,cy+100],fill=(235,120,120,int(200*a)))
    tc(d,cx+375,cy+135,"effort",f_small,(180,150,150,int(200*a)))
def s05(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,160,'Dopamine: "do that again"',f_title,(235,238,250,int(230*a)))
    cx,cy=W//2,H//2+30; pts=[(cx-360,cy),(cx-120,cy-60),(cx+120,cy+50),(cx+360,cy-20)]
    grow=cl((t-2)/4); width=int(2+10*grow)
    for i in range(len(pts)-1): d.line([pts[i],pts[i+1]],fill=(255,200,90,int((120+120*grow)*a)),width=width)
    pulse=(t*0.5)%1; idx=int(pulse*(len(pts)-1)); px=lerp(pts[idx][0],pts[idx+1][0],pulse*(len(pts)-1)-idx); py=lerp(pts[idx][1],pts[idx+1][1],pulse*(len(pts)-1)-idx)
    node(d,px,py,14,(255,235,150),230)
    for p_ in pts: node(d,p_[0],p_[1],10,GOLD,220*a)
    tc(d,W//2,cy+170,"neurons that fire together, wire together",f_lbl,(160,175,215,int(220*a)))
def s06(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"Reinforcement learning",f_title,(235,238,250,int(230*a)))
    steps=["try an action","reward: how good?","nudge the weights","repeat"]
    cx,cy=W//2,H//2+30; n=len(steps)
    for i,s in enumerate(steps):
        x=W//2-540+i*360; ai=sm(cl((t-1-i*0.5)/1));
        d.rounded_rectangle([x-150,cy-44,x+150,cy+44],radius=14,fill=(20,26,52,int(220*ai)),outline=(120,150,220,int(220*ai)),width=2)
        tc(d,x,cy,s,f_small,(225,232,250,int(255*ai)))
        if i<n-1: d.line([(x+150,cy),(x+210,cy)],fill=(110,140,210,int(180*ai)),width=3)
    rep=cl((t-4)/3); tc(d,W//2,cy+150,f"repeat  ×  {int(lerp(1,1000000,rep)):,}",f_lbl,(255,200,90,int(230*rep)))
def s07(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,160,"Same loop, two languages",f_title,(235,238,250,int(230*a)))
    rows=[("reward","dopamine"),("weight update","rewiring"),("millions of tries","practice")]
    for i,(h,r) in enumerate(rows):
        y=H//2-60+i*120; ai=sm(cl((t-1-i*0.8)/1.2))
        tc(d,W//2-360,y,h,f_cap,(120,170,255,int(255*ai)))
        tc(d,W//2+360,y,r,f_cap,(255,200,90,int(255*ai)))
        d.line([(W//2-180,y),(W//2+180,y)],fill=(200,200,220,int(150*ai)),width=2)
        tc(d,W//2,y-6,"=",f_lbl,(200,210,230,int(220*ai)))
def s08(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,120,"One life vs. four thousand",f_title,(235,238,250,int(230*a)))
    core=(W//2,260); node(d,*core,40,(255,220,120),230*a)
    grow=cl((t-2)/5); cols,rows=24,12; cell=46; gx=W//2-cols*cell//2; gy=380
    total=cols*rows; show=int(total*grow)
    rng=np.random.default_rng(5)
    for k in range(show):
        i=k//cols; j=k%cols; x=gx+j*cell; y=gy+i*cell
        jit=2*math.sin(t*4+k); node(d,x+jit,y,9,(120,160,235),200)
        if k%37==0: d.line([(x,y),core],fill=(120,150,220,40),width=1)
    tc(d,W//2,gy+rows*cell+40,f"1  →  {min(4096,show*14):,}  copies, one shared brain",f_lbl,(255,200,90,int(230*grow)))
def s09(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,160,"Practice in the wind and the rain",f_title,(235,238,250,int(230*a)))
    cx,cy=W//2,H//2+30
    # buffet: jittered tint streaks
    rng=np.random.default_rng(int(t*8)%9999)
    for _ in range(40):
        x=rng.uniform(W*0.2,W*0.8); y=rng.uniform(cy-150,cy+150)
        d.line([(x,y),(x+rng.uniform(-30,30),y+rng.uniform(-30,30))],fill=(150,170,220,40),width=1)
    node(d,cx,cy,60,GOLD,220*a); tc(d,cx,cy,"balanced",f_small,(20,20,30,255))
    tc(d,W//2,cy+150,"random friction · lighting · weights  →  robustness",f_lbl,(160,175,215,int(220*a)))
def s10(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"Same loop. Two substrates.",f_title,(235,238,250,int(230*a)))
    beat=int((t*1.2)%4)
    for side,cx,col,lab in [(-1,W//2-380,GOLD,"neurons"),(1,W//2+380,BLUE,"numbers")]:
        rng=np.random.default_rng(1 if side<0 else 2); pts=rng.uniform([cx-160,H//2-120],[cx+160,H//2+160],(9,2))
        for i in range(len(pts)):
            for j in range(i+1,len(pts)):
                if np.linalg.norm(pts[i]-pts[j])<170: d.line([tuple(pts[i]),tuple(pts[j])],fill=col+(60,),width=1)
        for k,p_ in enumerate(pts): node(d,p_[0],p_[1],10,col,(120+120*(k%4==beat)))
        tc(d,cx,H//2+230,lab,f_lbl,(220,228,245,int(220*a)))
    # shared loop indicator
    tc(d,W//2,H//2+40,["TRY","FEEDBACK","UPDATE","REPEAT"][beat],f_cap,(255,200,90,230))
def s11(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"Where the analogy breaks",f_title,(235,238,250,int(230*a)))
    # machine steady (right), human sprouts new branch (left)
    for side,cx,col,lab in [(-1,W//2-380,GOLD,"you"),(1,W//2+380,BLUE,"the machine")]:
        rng=np.random.default_rng(1 if side<0 else 2); pts=rng.uniform([cx-150,H//2-100],[cx+150,H//2+150],(8,2))
        for i in range(len(pts)):
            for j in range(i+1,len(pts)):
                if np.linalg.norm(pts[i]-pts[j])<170: d.line([tuple(pts[i]),tuple(pts[j])],fill=col+(60,),width=1)
        for p_ in pts: node(d,p_[0],p_[1],10,col,180)
        tc(d,cx,H//2+220,lab,f_lbl,(220,228,245,int(220*a)))
    reach=sm(cl((t-3)/4))
    if reach>0:
        sx,sy=W//2-380,H//2-100; tx,ty=W//2-540,H//2-260
        ex,ey=lerp(sx,tx,reach),lerp(sy,ty,reach)
        d.line([(sx,sy),(ex,ey)],fill=(255,210,110,int(220*reach)),width=4); node(d,ex,ey,12,(255,235,150),230*reach)
        tc(d,tx,ty-40,"a wish to change",f_small,(255,210,110,int(220*reach)))
def s12(d,img,t,NF):
    a=sm(cl(t/2)); tc(d,W//2,150,"You can't delete it — you outvote it",f_title,(235,238,250,int(230*a)))
    trig=W//2+420; y_old,y_new=H//2-20,H//2+120
    d.line([(W//2-480,y_old),(trig,y_old)],fill=(150,165,205,int(120*a)),width=int(10))      # old thick
    new_w=int(2+10*cl((t-2)/5)); d.line([(W//2-480,y_new),(trig,y_new)],fill=(120,210,150,int(160*a)),width=new_w)
    d.line([(trig,y_old-80),(trig,y_new+80)],fill=(255,200,90,int(200*a)),width=4); tc(d,trig+70,H//2+50,"trigger",f_small,(255,200,90,int(220*a)))
    cyc=(t*0.7)%1; ox=lerp(W//2-480,trig,cyc); winnew=cl((t-4)/3)
    nx=lerp(W//2-480,trig,min(1,cyc*(1+winnew)))
    node(d,ox,y_old,12,GREY,220); node(d,nx,y_new,12,GREEN,220)
    tc(d,W//2-300,y_old-50,"old habit",f_small,(170,180,205,int(200*a))); tc(d,W//2-300,y_new+45,"new pattern",f_small,(140,210,160,int(200*a)))
def s13(d,img,t,NF):
    a=sm(cl(t/2.2))
    tc(d,W//2,H//2-70,"You can't delete a pattern.",f_big,(240,243,252,int(255*a)))
    tc(d,W//2,H//2+20,"You can only outweigh it with reps of a better one.",f_cap,(240,243,252,int(255*a)))
    b=sm(cl((t-3)/2)); tc(d,W//2,H//2+130,"AI is the Universal Mind   ·   Ep.2 — The Learning Loop",f_lbl,(180,150,235,int(230*b)))
    e=sm(cl((t-5)/2)); tc(d,W//2,H//2+185,"Look closely at one — and you understand the other.",f_small,(160,175,215,int(220*e)))

SCENES=[("s01",s01),("s02",s02),("s03",s03),("s04",s04),("s05",s05),("s06",s06),("s07",s07),
        ("s08",s08),("s09",s09),("s10",s10),("s11",s11),("s12",s12),("s13",s13)]

clips=[]
for i,(sid,fn) in enumerate(SCENES,1):
    audio=f"{BUILD}/s{i:02d}.mp3"; D=dur(audio); NF=int(D*FPS)
    if os.path.isdir(SHM): shutil.rmtree(SHM)
    os.makedirs(SHM,exist_ok=True)
    print(f">> {sid}: {D:.1f}s {NF}f",flush=True)
    for f in range(NF):
        img,d=frame(); fn(d,img,f/FPS,NF); img.save(os.path.join(SHM,f"f{f:04d}.png"))
    bg=os.path.join(WORK,f"{sid}_bg.mp4")
    render_shader_video(shader_name="circuit_mind",audio_path=audio,output_path=bg,duration=D,fps=FPS,width=W,height=H)
    clip=os.path.join(WORK,f"{sid}.mp4")
    subprocess.run(["ffmpeg","-y","-i",bg,"-framerate",str(FPS),"-i",os.path.join(SHM,"f%04d.png"),"-i",audio,
        "-filter_complex","[0:v][1:v]overlay=0:0[v]","-map","[v]","-map","2:a",
        "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",clip],
        capture_output=True)
    clips.append(clip); print(f"   {sid} clip done",flush=True)
shutil.rmtree(SHM,ignore_errors=True)
lst=os.path.join(WORK,"concat.txt")
open(lst,"w").write("".join(f"file '{c}'\n" for c in clips))
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",OUT],capture_output=True)
print(f"\n✅ DONE: {OUT} ({dur(OUT):.1f}s)",flush=True)
