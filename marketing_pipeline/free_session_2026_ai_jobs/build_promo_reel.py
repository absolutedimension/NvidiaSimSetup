#!/usr/bin/env python3
"""
Build the "2026 AI Job Market" vertical promo reel (9:16) on EC2.
Moving LTX backgrounds (per scene) + kinetic styled text + uplifting house music.
Run ON EC2:  ~/acestep_venv not needed; uses system python3 + comfyenv for LTX.
  python3 build_promo_reel.py
Output: /home/ubuntu/promo_out/aijobs_promo_en.mp4
Defensive: each stage skips if its artifact already exists, so reruns are cheap.
"""
import os, base64, subprocess, requests
from PIL import Image, ImageDraw, ImageFont

KEY="sk-trigunai-master-key-2026"
HOME="/home/ubuntu"
OUT=f"{HOME}/promo_out"; IMG=f"{OUT}/img"; CLIP=f"{OUT}/clip"; TXT=f"{OUT}/txt"; SCN=f"{OUT}/scn"
for d in (OUT,IMG,CLIP,TXT,SCN): os.makedirs(d,exist_ok=True)
PY=f"{HOME}/comfyenv/bin/python"
MUSIC=f"{HOME}/music_out/aijobs_house.mp3"
W,H=1080,1920          # final vertical
LW,LH=576,1024         # LTX gen res (9:16, /32)
ACCENT=(165,107,255)   # brand purple-light
WHITE=(255,255,255)
SUB=(200,200,210)

# ---- font detection ----
def find_font(*names):
    roots=["/home/ubuntu/.local/share/fonts","/usr/share/fonts","/usr/local/share/fonts"]
    files=[]
    for r in roots:
        for dp,_,fs in os.walk(r):
            for f in fs: files.append(os.path.join(dp,f))
    for n in names:                       # name priority, not dir order
        for path in files:
            if n.lower() in os.path.basename(path).lower(): return path
    return None
F_BOLD=find_font("Poppins-Bold","Montserrat-Bold","DejaVuSans-Bold") or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SEMI=find_font("Poppins-SemiBold","Poppins-Medium","DejaVuSans-Bold") or F_BOLD
print("FONT_BOLD:",F_BOLD,flush=True)

# ---- scenes: dur, image prompt, motion prompt, text lines [(txt,size,color,font)] ----
SCENES=[
 dict(id="s1", dur=3.0,
   img="A tired young Indian man late at night, face lit only by a laptop glow, slumped, an email inbox on screen showing no replies, cinematic, desaturated cold blue, shallow depth of field, vertical composition, moody",
   mot="subtle ambient motion, faint screen flicker, slow push in, melancholic, cinematic",
   lines=[("Sent 200 applications.",70,WHITE,F_BOLD),("Heard nothing.",78,WHITE,F_BOLD)]),
 dict(id="s2", dur=6.0,
   img="Rows of empty office desks in a dim corporate floor at dusk, a faint downward arrow of light over a city skyline, moody blue, cinematic, vertical composition, sense of decline",
   mot="slow drift, dust motes in light, gentle camera glide, cinematic, moody",
   lines=[("The entry-level jobs",58,WHITE,F_SEMI),("didn't vanish.",72,WHITE,F_BOLD),
          ("They changed shape.",72,ACCENT,F_BOLD),("entry-level IT roles down ~25%",36,SUB,F_SEMI)]),
 dict(id="s3", dur=9.0,
   img="A bright modern glass office tower of a global tech company at sunrise, engineers working at glowing AI dashboards, hopeful warm golden light, energetic, cinematic, vertical composition, optimistic",
   mot="energetic upward camera rise, light blooms, lively motion, golden hour, cinematic",
   lines=[("AI roles are",60,WHITE,F_SEMI),("EXPLODING",104,ACCENT,F_BOLD),
          ("1,000,000+ openings",58,WHITE,F_BOLD),("~1 qualified person per 10",36,SUB,F_SEMI)]),
 dict(id="s4", dur=8.0,
   img="Over the shoulder of a focused young developer building an AI agent, clean code and a working app on a large monitor, warm confident lighting, empowering, cinematic, vertical composition",
   mot="smooth glide, code and UI subtly animating, confident, warm, cinematic",
   lines=[("The jobs go to people who",52,WHITE,F_SEMI),("BUILD with AI.",86,ACCENT,F_BOLD),
          ("You can become one.",60,WHITE,F_BOLD)]),
 dict(id="s5", dur=7.0,
   img="A clean deep purple to indigo gradient background with soft glowing light and gentle particle bokeh, premium minimal, cinematic, vertical composition, brand feel",
   mot="soft glowing particles drifting upward, gentle light pulse, premium, minimal",
   lines=[("Free live session",58,WHITE,F_SEMI),("What to build first.",70,WHITE,F_BOLD),
          ("learn.trigunai.com",66,WHITE,F_BOLD,"btn"),("register free",40,WHITE,F_SEMI)]),
]
NEG="worst quality, blurry, jittery, warped, flickering, distorted faces, deformed, text, watermark, logo"

def gen_image(s):
    p=f"{IMG}/{s['id']}.png"
    if os.path.exists(p): print("img-reuse",s['id'],flush=True); return p
    r=requests.post("http://localhost:4000/v1/images/generations",
        headers={"Authorization":f"Bearer {KEY}"},
        json={"model":"gpt-image-1.5","size":"1024x1536","n":1,"prompt":s['img']},timeout=240)
    if r.status_code!=200: print("IMG ERR",s['id'],r.status_code,r.text[:160],flush=True); return None
    it=r.json()["data"][0]
    d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
    open(p,"wb").write(d); print("img-ok",s['id'],flush=True); return p

def gen_clip(s,img):
    raw=f"{CLIP}/{s['id']}.mp4"; boom=f"{CLIP}/{s['id']}_boom.mp4"
    if os.path.exists(boom): print("clip-reuse",s['id'],flush=True); return boom
    subprocess.run([PY,f"{HOME}/image_to_clip.py","--image",img,"--out",raw,
        "--frames","121","--width",str(LW),"--height",str(LH),"--steps","10",
        "--prompt",s['mot'],"--neg",NEG],cwd=HOME)
    if not os.path.exists(raw): print("CLIP FAIL",s['id'],flush=True); return None
    subprocess.run(["ffmpeg","-y","-i",raw,"-filter_complex",
        "[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]","-map","[v]",
        "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",boom],capture_output=True)
    print("clip-ok",s['id'],flush=True); return boom

def render_text(s):
    p=f"{TXT}/{s['id']}.png"
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    # measure
    rendered=[]; total=0; gap=26
    for line in s['lines']:
        txt,size,col,fp = line[0],line[1],line[2],line[3]
        btn = len(line)>4 and line[4]=="btn"
        f=ImageFont.truetype(fp,size)
        bb=d.textbbox((0,0),txt,font=f); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        rendered.append((txt,f,col,w,h,bb,btn)); total+=h+gap+(28 if btn else 0)
    y=int(H*0.60)-total//2
    for txt,f,col,w,h,bb,btn in rendered:
        x=(W-w)//2 - bb[0]
        yy=y-bb[1]
        if btn:
            # brand-purple rounded pill behind the URL so it pops maximally
            padx,pady=42,20; cx=(W-w)//2
            d.rounded_rectangle([cx-padx, y-pady, cx+w+padx, y+h+pady], radius=(h+2*pady)//2, fill=ACCENT+(255,))
            d.text((x,yy),txt,font=f,fill=(255,255,255,255))
            y+=h+gap+28
            continue
        # shadow for legibility over moving video
        for ox,oy in ((3,3),(-2,2),(2,-2)):
            d.text((x+ox,yy+oy),txt,font=f,fill=(0,0,0,170))
        d.text((x,yy),txt,font=f,fill=col+(255,))
        y+=h+gap
    im.save(p); print("txt-ok",s['id'],flush=True); return p

def scene_clip(s,bg,txt):
    out=f"{SCN}/{s['id']}.mp4"; dur=s['dur']
    # bg: loop boomerang to fill dur, scale-crop to 1080x1920; subtle dark scrim under text; text fade+drift
    vf=(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"setsar=1,fps=30[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[tx];"
        f"[bg][tx]overlay=0:(H*0.02)*(1-min(t/0.4\\,1))[ov];[ov]format=yuv420p[v]")
    subprocess.run(["ffmpeg","-y","-stream_loop","-1","-i",bg,"-loop","1","-i",txt,
        "-filter_complex",vf,"-map","[v]","-t",str(dur),
        "-c:v","libx264","-crf","19","-pix_fmt","yuv420p","-r","30",out],capture_output=True)
    ok=os.path.exists(out); print(("scn-ok" if ok else "SCN FAIL"),s['id'],flush=True); return out if ok else None

def main():
    scenes=[]
    for s in SCENES:
        img=gen_image(s)
        if not img: continue
        bg=gen_clip(s,img)
        if not bg: continue
        txt=render_text(s)
        sc=scene_clip(s,bg,txt)
        if sc: scenes.append(sc)
    if not scenes: print("NO SCENES — abort",flush=True); return
    # concat
    lst=f"{OUT}/concat.txt"; open(lst,"w").write("\n".join(f"file '{x}'" for x in scenes))
    silent=f"{OUT}/video_silent.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
        "-c:v","libx264","-crf","19","-pix_fmt","yuv420p","-r","30",silent],capture_output=True)
    total=sum(s['dur'] for s in SCENES)
    final=f"{OUT}/aijobs_promo_en.mp4"
    # music: trim to total, fade out last 1.2s
    subprocess.run(["ffmpeg","-y","-i",silent,"-i",MUSIC,
        "-filter_complex",f"[1:a]atrim=0:{total},afade=t=out:st={total-1.2}:d=1.2,volume=1.0[a]",
        "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",final],capture_output=True)
    print("FINAL:",final if os.path.exists(final) else "FAILED",flush=True)
    print("DONE_BUILD",flush=True)

if __name__=="__main__": main()
