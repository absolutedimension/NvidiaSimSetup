#!/usr/bin/env python3
"""Composite final 'What is an AI Agent?' video. Runs on EC2."""
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel

B="/home/ubuntu/agent_vid_build"; CLIPS=f"{B}/clips"; WORK=f"{B}/work"; os.makedirs(WORK,exist_ok=True)
W,H=1280,720
POP_B="/home/ubuntu/.local/share/fonts/Poppins-Bold.ttf"
POP_XB="/home/ubuntu/.local/share/fonts/Poppins-ExtraBold.ttf"
AMB="/home/ubuntu/welcome_voice/bg_ambient.mp3"

SCENES=[("s01","s01_hook","What is an AI Agent?"),
        ("s02","s02_child","Ask a 6-year-old"),
        ("s03","s03_school","Ask a school student"),
        ("s04","s04_college","Ask a college student"),
        ("s05","s05_graduate","Ask a graduate"),
        ("s06","s06_expert","Ask an expert"),
        ("s07","s07_close","One skeleton, every answer")]

def ff(a): subprocess.run(["ffmpeg","-y","-loglevel","error"]+a,check=True)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())

def make_scrim():
    ys=np.arange(H)
    bot=np.clip((ys-H*0.45)/(H*0.55),0,1)*195
    top=np.clip((H*0.20-ys)/(H*0.20),0,1)*115
    a=np.maximum(bot,top).astype(np.uint8)
    arr=np.dstack([np.zeros((H,W),np.uint8)]*3+[np.repeat(a[:,None],W,axis=1)])
    Image.fromarray(arr,"RGBA").save(f"{WORK}/scrim.png")

def make_label(text,path):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(POP_B,34); tb=d.textbbox((0,0),text,font=f)
    tw,th=tb[2]-tb[0],tb[3]-tb[1]; padx,pady=24,13; x,y=54,46
    d.rounded_rectangle([x,y,x+tw+2*padx,y+th+2*pady],radius=(th+2*pady)//2,fill=(124,92,246,215))
    d.text((x+padx-tb[0],y+pady-tb[1]),text,font=f,fill=(255,255,255,255))
    im.save(path)

def make_caption(text,path,fs=50):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(POP_XB,fs)
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)>W-260 and cur: lines.append(cur); cur=w
        else: cur=t
    if cur: lines.append(cur)
    lh=fs+14; total=lh*len(lines); y0=H-140-total
    for i,ln in enumerate(lines):
        tw=d.textlength(ln,font=f); x=(W-tw)/2; y=y0+i*lh
        for dx,dy in [(-2,2),(2,2),(0,3),(-3,0),(3,0)]:
            d.text((x+dx,y+dy),ln,font=f,fill=(0,0,0,210))
        d.text((x,y),ln,font=f,fill=(255,255,255,255))
    im.save(path)

print("loading whisper…",flush=True)
model=WhisperModel("base",device="cpu",compute_type="int8")
def phrases(audio):
    segs,_=model.transcribe(audio,word_timestamps=True)
    ws=[]
    for s in segs:
        for w in (s.words or []): ws.append((w.start,w.end,w.word.strip()))
    out=[]; cur=[]; st=None
    for (s,e,w) in ws:
        if not cur: st=s
        cur.append(w)
        if len(cur)>=4 or (e-st)>=2.0: out.append((st,e," ".join(cur))); cur=[]
    if cur and ws: out.append((st,ws[-1][1]," ".join(cur)))
    # clamp each window to end before the next starts → never two captions at once
    clamped=[]
    for i,(s,e,t) in enumerate(out):
        if i+1<len(out): e=min(e,out[i+1][0]-0.06)
        if e>s: clamped.append((s,e,t))
    return clamped

make_scrim()
scene_files=[]
for sid,clipname,label in SCENES:
    print(">> scene",sid,flush=True)
    clip=f"{CLIPS}/{clipname}.mp4"; audio=f"{B}/{sid}.mp3"; d=dur(audio)
    fwd=f"{WORK}/{sid}_f.mp4"; rev=f"{WORK}/{sid}_r.mp4"; boom=f"{WORK}/{sid}_b.mp4"; base=f"{WORK}/{sid}_base.mp4"
    ff(["-i",clip,"-vf","scale=768:448,fps=25,format=yuv420p","-an","-c:v","libx264","-crf","18",fwd])
    ff(["-i",fwd,"-vf","reverse","-an","-c:v","libx264","-crf","18",rev])
    cc=f"{WORK}/{sid}_cc.txt"; open(cc,"w").write(f"file '{fwd}'\nfile '{rev}'\n")
    ff(["-f","concat","-safe","0","-i",cc,"-c","copy",boom])
    ff(["-stream_loop","-1","-i",boom,"-t",f"{d:.2f}",
        "-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=25,format=yuv420p","-an",base])
    lab=f"{WORK}/{sid}_lab.png"; make_label(label,lab)
    phs=phrases(audio); caps=[]
    for i,(s,e,txt) in enumerate(phs):
        p=f"{WORK}/{sid}_c{i}.png"; make_caption(txt,p); caps.append((p,s,e))
    inputs=["-i",base,"-i",f"{WORK}/scrim.png","-i",lab]
    for (p,s,e) in caps: inputs+=["-i",p]
    fc="[0:v][1:v]overlay=0:0[v1];[v1][2:v]overlay=0:0[a2]"; prev="a2"; n=3
    for (p,s,e) in caps:
        fc+=f";[{prev}][{n}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[a{n}]"; prev=f"a{n}"; n+=1
    out=f"{WORK}/{sid}_scene.mp4"
    ff(inputs+["-i",audio,"-filter_complex",fc,"-map",f"[{prev}]","-map",f"{n}:a",
       "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",out])
    scene_files.append(out)

cf=f"{WORK}/concat.txt"; open(cf,"w").write("".join(f"file '{p}'\n" for p in scene_files))
nomusic=f"{B}/what_is_an_agent_nomusic.mp4"
ff(["-f","concat","-safe","0","-i",cf,"-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",nomusic])
total=dur(nomusic)
final=f"{B}/what_is_an_agent_FINAL.mp4"
ff(["-i",nomusic,"-stream_loop","-1","-i",AMB,
    "-filter_complex",f"[1:a]volume=0.06,afade=in:st=0:d=2,afade=out:st={total-2:.2f}:d=2[m];[0:a][m]amix=inputs=2:duration=first[a]",
    "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-t",f"{total:.2f}",final])
print(f"FINAL -> {final}  ({total:.1f}s)",flush=True)
