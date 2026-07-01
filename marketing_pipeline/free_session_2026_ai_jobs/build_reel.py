#!/usr/bin/env python3
"""
Generic vertical-reel builder (9:16) — moving LTX backgrounds + kinetic Poppins text + music.
Reuses the proven reel-1 engine. Two configs: 'learn' (courses) and 'brand' (trigunai.com hero).
Run ON EC2:  python3 build_reel.py --config learn  --music ~/music_out/warm_bed.mp3
             python3 build_reel.py --config brand  --music ~/music_out/warm_bed.mp3
Defensive: per-config out dir; skips existing image/clip/scene artifacts on rerun.
"""
import os, base64, subprocess, requests, argparse
from PIL import Image, ImageDraw, ImageFont

KEY="sk-trigunai-master-key-2026"; HOME="/home/ubuntu"; PY=f"{HOME}/comfyenv/bin/python"
W,H=1080,1920; LW,LH=576,1024
ACCENT=(165,107,255); WHITE=(255,255,255); SUB=(205,205,215)
NEG="worst quality, blurry, jittery, warped, flickering, distorted faces, deformed, text, watermark, logo"

def find_font(*names):
    roots=["/home/ubuntu/.local/share/fonts","/usr/share/fonts","/usr/local/share/fonts"]
    files=[os.path.join(dp,f) for r in roots for dp,_,fs in os.walk(r) for f in fs]
    for n in names:
        for p in files:
            if n.lower() in os.path.basename(p).lower(): return p
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_BOLD=find_font("Poppins-Bold","DejaVuSans-Bold"); F_SEMI=find_font("Poppins-SemiBold","Poppins-Medium","DejaVuSans-Bold")

CONFIGS={
 "learn":[
  dict(id="s1",dur=4.0,
    img="A person passively typing into a generic AI chatbot on a laptop, bored, flat dim lighting, cinematic, vertical composition, ordinary",
    mot="subtle ambient motion, faint screen glow, slow, calm",
    lines=[("Everyone is",54,WHITE,F_SEMI),("USING AI.",84,WHITE,F_BOLD)]),
  dict(id="s2",dur=6.0,
    img="Close over-the-shoulder of hands building something on screen, code and a 3D scene coming alive, warm creative lighting, cinematic, vertical composition, empowering",
    mot="warm gentle motion, elements coming alive on screen, smooth glide",
    lines=[("Almost no one is",54,WHITE,F_SEMI),("BUILDING with it.",78,ACCENT,F_BOLD),
           ("that gap is the opportunity",36,SUB,F_SEMI)]),
  dict(id="s3",dur=9.0,
    img="A cinematic montage feel of a VR headset glowing, a humanoid robot, neural network visualization, and a game world, premium dark with warm accents, vertical composition",
    mot="slow cinematic drift between glowing tech elements, premium, warm",
    lines=[("Build real things:",50,WHITE,F_SEMI),("VR/MR · AI Agents",60,WHITE,F_BOLD),
           ("ML · Physical AI",60,WHITE,F_BOLD),("8 live cohort tracks",36,SUB,F_SEMI)]),
  dict(id="s4",dur=8.0,
    img="A developer in a warm studio with a powerful NVIDIA GPU workstation, a live class on a second screen, shipping a real app, confident cinematic lighting, vertical composition",
    mot="confident smooth motion, screens glowing, warm, cinematic",
    lines=[("Real NVIDIA GPU. Live cohort.",46,WHITE,F_SEMI),("Projects you SHIP.",72,ACCENT,F_BOLD),
           ("taught by a founder who shipped",34,SUB,F_SEMI)]),
  dict(id="s5",dur=6.0,
    img="A clean deep purple to indigo gradient with soft glowing particle bokeh, premium minimal, cinematic, vertical composition, brand feel",
    mot="soft glowing particles drifting upward, gentle light pulse, premium",
    lines=[("From watching to building",50,WHITE,F_SEMI),("Start free.",72,WHITE,F_BOLD),
           ("learn.trigunai.com",64,WHITE,F_BOLD,"btn")]),
 ],
 "brand":[
  dict(id="s1",dur=5.0,
    img="A lone figure standing in vast dark space looking up at a faint imagined world of light, cinematic, deep indigo, sense of longing and wonder, vertical composition",
    mot="very slow cinematic drift, faint particles, contemplative, wonder",
    lines=[("I needed a world",54,WHITE,F_SEMI),("that didn't exist.",70,WHITE,F_BOLD)]),
  dict(id="s2",dur=6.0,
    img="A luminous world forming out of darkness, geometry and light assembling into a beautiful space, cinematic, deep blue to warm gold, vertical composition, creation",
    mot="a world gently assembling from light and geometry, smooth, cinematic",
    lines=[("So I",60,WHITE,F_SEMI),("built it.",92,ACCENT,F_BOLD)]),
  dict(id="s3",dur=9.0,
    img="An abstract glowing human mind/brain made of light reflected in a mirror of flowing AI neural patterns, cinematic, deep indigo and gold, vertical composition, profound",
    mot="gentle mirrored motion between mind and neural light, slow, profound",
    lines=[("AI is the clearest",50,WHITE,F_SEMI),("MIRROR",92,ACCENT,F_BOLD),
           ("we've built for the mind",44,WHITE,F_SEMI)]),
  dict(id="s4",dur=7.0,
    img="A person at dawn building and shaping light with their hands, empowered and calm, warm golden sunrise, cinematic, vertical composition, agency",
    mot="warm dawn light, hands shaping glowing forms, uplifting, smooth",
    lines=[("You don't have to wait.",50,WHITE,F_SEMI),("You can build it.",76,WHITE,F_BOLD)]),
  dict(id="s5",dur=6.0,
    img="A clean deep purple to indigo gradient with a soft glowing triskelion-like light mark and gentle particle bokeh, premium minimal, cinematic, vertical composition",
    mot="soft glowing particles drifting, gentle light pulse, premium, serene",
    lines=[("AI is the Universal Mind",52,WHITE,F_SEMI),("Begin.",74,WHITE,F_BOLD),
           ("trigunai.com",64,WHITE,F_BOLD,"btn")]),
 ],
 "ghibli":[
  dict(id="s1",dur=4.0,
    img="Studio Ghibli anime style, a lush green river valley, a young girl with short brown hair in a simple dress stepping barefoot into a clear shallow stream under a giant ancient tree with pink cherry blossoms, soft misty morning light, mountains behind, painterly, dreamy, cinematic, vertical composition",
    mot="gentle flowing water, blossom petals drifting down, soft breeze, slow cinematic, dreamy",
    lines=[("Some worlds only exist",46,WHITE,F_SEMI),("in your head.",64,WHITE,F_BOLD)]),
  dict(id="s2",dur=6.0,
    img="Studio Ghibli anime style, the same young girl with short brown hair joyfully running and splashing through a shallow clear stream in a lush green valley, cherry blossom petals falling, waterfalls, warm sunlight, painterly, dreamy, cinematic, vertical composition",
    mot="water splashing, petals falling, joyful running motion, soft sunlight flicker, cinematic",
    lines=[("I got tired of just",46,WHITE,F_SEMI),("imagining mine.",62,WHITE,F_BOLD)]),
  dict(id="s3",dur=8.0,
    img="Studio Ghibli anime style, the same girl running toward warm golden light and a glowing waterfall, the valley opening into a magical sunlit clearing, god rays through trees, lush green and gold, painterly, dreamy, cinematic, vertical composition",
    mot="golden god rays shimmering, waterfall flowing, warm light blooming, slow forward motion, magical",
    lines=[("So I",54,WHITE,F_SEMI),("learned to build it.",66,(244,193,75),F_BOLD)]),
  dict(id="s4",dur=7.0,
    img="Studio Ghibli anime style, back view of the same girl running forward with arms out into a bright open sunlit valley, free and joyful, distant mountains and blossoms, warm radiant light ahead, painterly, dreamy, cinematic, vertical composition",
    mot="forward running into bright light, hair and dress in the wind, radiant glow ahead, uplifting, cinematic",
    lines=[("Now I build the worlds",44,WHITE,F_SEMI),("I want to live in.",58,WHITE,F_BOLD),("So can you.",56,(244,193,75),F_BOLD)]),
  dict(id="s5",dur=7.0,
    img="Studio Ghibli anime style, a serene wide view of the magical green river valley at soft golden dusk, cherry blossoms, gentle mist, calm and beautiful, painterly, dreamy, cinematic, vertical composition",
    mot="gentle drifting mist and petals, calm water, soft glowing dusk light, serene slow motion",
    lines=[("Build the worlds",50,WHITE,F_SEMI),("you imagine.",64,WHITE,F_BOLD),("trigunai.com",62,WHITE,F_BOLD,"btn")]),
 ],
}

def gen_image(s,IMG):
    p=f"{IMG}/{s['id']}.png"
    if os.path.exists(p): print("img-reuse",s['id'],flush=True); return p
    r=requests.post("http://localhost:4000/v1/images/generations",headers={"Authorization":f"Bearer {KEY}"},
        json={"model":"gpt-image-1.5","size":"1024x1536","n":1,"prompt":s['img']},timeout=240)
    if r.status_code!=200: print("IMG ERR",s['id'],r.status_code,r.text[:160],flush=True); return None
    it=r.json()["data"][0]; d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
    open(p,"wb").write(d); print("img-ok",s['id'],flush=True); return p

def gen_clip(s,img,CLIP):
    raw=f"{CLIP}/{s['id']}.mp4"; boom=f"{CLIP}/{s['id']}_boom.mp4"
    if os.path.exists(boom): print("clip-reuse",s['id'],flush=True); return boom
    subprocess.run([PY,f"{HOME}/image_to_clip.py","--image",img,"--out",raw,"--frames","121",
        "--width",str(LW),"--height",str(LH),"--steps","10","--prompt",s['mot'],"--neg",NEG],cwd=HOME)
    if not os.path.exists(raw): print("CLIP FAIL",s['id'],flush=True); return None
    subprocess.run(["ffmpeg","-y","-i",raw,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",boom],capture_output=True)
    print("clip-ok",s['id'],flush=True); return boom

def render_text(s,TXT):
    p=f"{TXT}/{s['id']}.png"; im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    rendered=[]; total=0; gap=26
    for line in s['lines']:
        txt,size,col,fp=line[0],line[1],line[2],line[3]; btn=len(line)>4 and line[4]=="btn"
        f=ImageFont.truetype(fp,size); bb=d.textbbox((0,0),txt,font=f); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        rendered.append((txt,f,col,w,h,bb,btn)); total+=h+gap+(28 if btn else 0)
    y=int(H*0.60)-total//2
    for txt,f,col,w,h,bb,btn in rendered:
        x=(W-w)//2-bb[0]; yy=y-bb[1]
        if btn:
            padx,pady=42,20; cx=(W-w)//2
            d.rounded_rectangle([cx-padx,y-pady,cx+w+padx,y+h+pady],radius=(h+2*pady)//2,fill=ACCENT+(255,))
            d.text((x,yy),txt,font=f,fill=(255,255,255,255)); y+=h+gap+28; continue
        for ox,oy in ((3,3),(-2,2),(2,-2)): d.text((x+ox,yy+oy),txt,font=f,fill=(0,0,0,170))
        d.text((x,yy),txt,font=f,fill=col+(255,)); y+=h+gap
    im.save(p); print("txt-ok",s['id'],flush=True); return p

def scene_clip(s,bg,txt,SCN):
    out=f"{SCN}/{s['id']}.mp4"
    vf=(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[tx];"
        f"[bg][tx]overlay=0:(H*0.02)*(1-min(t/0.4\\,1))[ov];[ov]format=yuv420p[v]")
    subprocess.run(["ffmpeg","-y","-stream_loop","-1","-i",bg,"-loop","1","-i",txt,"-filter_complex",vf,
        "-map","[v]","-t",str(s['dur']),"-c:v","libx264","-crf","19","-pix_fmt","yuv420p","-r","30",out],capture_output=True)
    ok=os.path.exists(out); print(("scn-ok" if ok else "SCN FAIL"),s['id'],flush=True); return out if ok else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True,choices=list(CONFIGS))
    ap.add_argument("--music",required=True); ap.add_argument("--out",default=None); a=ap.parse_args()
    SCENES=CONFIGS[a.config]
    base=f"{HOME}/reel_{a.config}"; IMG=f"{base}/img"; CLIP=f"{base}/clip"; TXT=f"{base}/txt"; SCN=f"{base}/scn"
    for dd in (base,IMG,CLIP,TXT,SCN): os.makedirs(dd,exist_ok=True)
    out=a.out or f"{base}/reel_{a.config}.mp4"
    scenes=[]
    for s in SCENES:
        img=gen_image(s,IMG);  bg=gen_clip(s,img,CLIP) if img else None
        if not bg: continue
        sc=scene_clip(s,render_text(s,TXT),0,SCN) if False else scene_clip(s,bg,render_text(s,TXT),SCN)
        if sc: scenes.append(sc)
    if not scenes: print("NO SCENES",flush=True); return
    lst=f"{base}/concat.txt"; open(lst,"w").write("\n".join(f"file '{x}'" for x in scenes))
    silent=f"{base}/silent.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c:v","libx264","-crf","19",
        "-pix_fmt","yuv420p","-r","30",silent],capture_output=True)
    total=sum(s['dur'] for s in SCENES)
    subprocess.run(["ffmpeg","-y","-i",silent,"-i",a.music,"-filter_complex",
        f"[1:a]atrim=0:{total},afade=t=in:st=0:d=1,afade=t=out:st={total-1.2}:d=1.2[ax]",
        "-map","0:v","-map","[ax]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",out],capture_output=True)
    print("FINAL:",out if os.path.exists(out) else "FAILED",flush=True); print("DONE_BUILD",flush=True)

if __name__=="__main__": main()
