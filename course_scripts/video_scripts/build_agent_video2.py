#!/usr/bin/env python3
"""Build v2: multi-image-per-scene (no boomerang), new voice. Animate each shot, concat, caption. Runs on EC2."""
import os, subprocess, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
from faster_whisper import WhisperModel

B=os.environ.get("BUILD_DIR","/home/ubuntu/agent_vid_build"); WORK=f"{B}/work2"; os.makedirs(WORK,exist_ok=True)
W,H=1280,720
POP_B="/home/ubuntu/.local/share/fonts/Poppins-Bold.ttf"; POP_XB="/home/ubuntu/.local/share/fonts/Poppins-ExtraBold.ttf"
AMB="/home/ubuntu/welcome_voice/bg_ambient.mp3"
MAN=json.load(open(f"{B}/manifest.json"))
ORDER=sorted(MAN.keys())
MOTION={"s01":"subtle natural motion, gentle slow camera push in, soft warm light, person breathes slightly",
        "s02":"soft gentle motion, shallow depth of field, warm cozy light, very subtle",
        "s03":"gentle candid motion, soft background movement, daylight, subtle",
        "s04":"subtle natural motion, gentle typing and ambient movement, soft daylight",
        "s05":"gentle ambient office motion, subtle natural movement, warm light",
        "s06":"very gentle motion, subtle breathing and warm lamp glow, calm",
        "s07":"subtle realistic motion, code gently on screen, gentle hand movement"}

def ff(a): subprocess.run(["ffmpeg","-y","-loglevel","error"]+a,check=True)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())

def make_scrim():
    ys=np.arange(H); bot=np.clip((ys-H*0.45)/(H*0.55),0,1)*195; top=np.clip((H*0.20-ys)/(H*0.20),0,1)*115
    a=np.maximum(bot,top).astype(np.uint8); arr=np.dstack([np.zeros((H,W),np.uint8)]*3+[np.repeat(a[:,None],W,axis=1)])
    Image.fromarray(arr,"RGBA").save(f"{WORK}/scrim.png")
def make_label(text,path):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); f=ImageFont.truetype(POP_B,34)
    tb=d.textbbox((0,0),text,font=f); tw,th=tb[2]-tb[0],tb[3]-tb[1]; padx,pady=24,13; x,y=54,46
    d.rounded_rectangle([x,y,x+tw+2*padx,y+th+2*pady],radius=(th+2*pady)//2,fill=(124,92,246,215))
    d.text((x+padx-tb[0],y+pady-tb[1]),text,font=f,fill=(255,255,255,255)); im.save(path)
def make_caption(text,path,fs=50):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); f=ImageFont.truetype(POP_XB,fs)
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)>W-260 and cur: lines.append(cur); cur=w
        else: cur=t
    if cur: lines.append(cur)
    lh=fs+14; total=lh*len(lines); y0=H-140-total
    for i,ln in enumerate(lines):
        tw=d.textlength(ln,font=f); x=(W-tw)/2; y=y0+i*lh
        for dx,dy in [(-2,2),(2,2),(0,3),(-3,0),(3,0)]: d.text((x+dx,y+dy),ln,font=f,fill=(0,0,0,210))
        d.text((x,y),ln,font=f,fill=(255,255,255,255))
    im.save(path)

print("whisper…",flush=True); model=WhisperModel("base",device="cpu",compute_type="int8")
def phrases(audio):
    segs,_=model.transcribe(audio,word_timestamps=True); ws=[]
    for s in segs:
        for w in (s.words or []): ws.append((w.start,w.end,w.word.strip()))
    out=[]; cur=[]; st=None
    for (s,e,w) in ws:
        if not cur: st=s
        cur.append(w)
        if len(cur)>=4 or (e-st)>=2.0: out.append((st,e," ".join(cur))); cur=[]
    if cur and ws: out.append((st,ws[-1][1]," ".join(cur)))
    cl=[]
    for i,(s,e,t) in enumerate(out):
        if i+1<len(out): e=min(e,out[i+1][0]-0.06)
        if e>s: cl.append((s,e,t))
    return cl

def frames_for(slot):
    f=round(slot*25/8)*8+1
    return max(97,min(137,f))   # cap ~5.5s/clip to avoid ComfyUI VRAM crash

def kenburns(img,out,t):
    nf=max(2,int(t*25))
    ff(["-loop","1","-i",img,"-t",f"{t:.2f}",
        "-vf",f"scale=2560:-1,zoompan=z='min(zoom+0.0009,1.14)':d={nf}:s={W}x{H}:fps=25,format=yuv420p",
        "-c:v","libx264","-crf","19","-an",out])

make_scrim(); scene_files=[]
for sid in ORDER:
    m=MAN[sid]; d=m["dur"]; N=m["N"]; slot=d/N; audio=m["audio"]; label=m["label"]
    out=f"{WORK}/{sid}_scene.mp4"
    if os.path.exists(out) and os.path.getsize(out)>10000:
        print(f"== skip {sid} (already built)",flush=True); scene_files.append(out); continue
    print(f">> {sid} N={N} dur={d:.1f}",flush=True)
    norm_clips=[]
    for k,img in enumerate(m["images"]):
        raw=f"{WORK}/{sid}_v{k}_raw.mp4"; nclip=f"{WORK}/{sid}_v{k}.mp4"
        if os.path.exists(nclip) and os.path.getsize(nclip)>10000:
            print("   reuse clip",nclip,flush=True); norm_clips.append(nclip); continue
        ok=False
        for attempt in range(2):
            subprocess.run(["/home/ubuntu/comfyenv/bin/python","/home/ubuntu/image_to_clip.py",
                "--image",img,"--prompt",MOTION[sid],"--out",raw,
                "--frames",str(frames_for(slot+0.4)),"--width","768","--height","448","--steps","10"],
                capture_output=True,text=True)
            if os.path.exists(raw) and os.path.getsize(raw)>10000: ok=True; break
        if ok:
            ff(["-i",raw,"-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=25,format=yuv420p","-an","-c:v","libx264","-crf","19",nclip])
        else:
            print("   LTX failed → Ken-Burns fallback",img,flush=True)
            kenburns(img,nclip,slot+0.4)
        norm_clips.append(nclip)
    # concat N clips (hard cut, no boomerang) -> scene bg
    cc=f"{WORK}/{sid}_cc.txt"; open(cc,"w").write("".join(f"file '{p}'\n" for p in norm_clips))
    base=f"{WORK}/{sid}_base.mp4"
    ff(["-f","concat","-safe","0","-i",cc,"-c","copy",base])
    # freeze-pad base to audio length so narration is never truncated (no loop/boomerang)
    bdur=dur(base); adur=dur(audio)
    if bdur < adur-0.05:
        padded=f"{WORK}/{sid}_basep.mp4"
        ff(["-i",base,"-vf",f"tpad=stop_mode=clone:stop_duration={adur-bdur+0.2:.2f}","-an","-c:v","libx264","-crf","20",padded])
        base=padded
    # overlays
    lab=f"{WORK}/{sid}_lab.png"; make_label(label,lab)
    caps=[];
    for i,(s,e,txt) in enumerate(phrases(audio)):
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
nomusic=f"{B}/nomusic.mp4"
ff(["-f","concat","-safe","0","-i",cf,"-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",nomusic])
total=dur(nomusic); final=f"{B}/FINAL.mp4"
ff(["-i",nomusic,"-stream_loop","-1","-i",AMB,
    "-filter_complex",f"[1:a]volume=0.06,afade=in:st=0:d=2,afade=out:st={total-2:.2f}:d=2[m];[0:a][m]amix=inputs=2:duration=first[a]",
    "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-t",f"{total:.2f}",final])
print(f"FINAL -> {final}  ({total:.1f}s)",flush=True)
