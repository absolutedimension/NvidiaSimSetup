#!/usr/bin/env python3
"""Contextual-abstract backgrounds (image + LTX clip + boomerang) for each Ep7 scene.
Theme: error landscape / descending the slope. Dark, abstract, NO text/objects. Output: clips/bg_ep07_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, a faint distant target with a glowing line measuring a gap to an off-target point, the idea of error, deep blue with gold, very dark empty center, minimal cinematic, NO text NO objects",
        "a faint glowing gap between a target and an off-point gently pulsing, deep blue gold, very dark, subtle"),
 "s02":("Abstract dark background, two points with a bright measured glowing gap between them, the size and direction of a mistake, deep blue and gold, very dark, minimal, NO text",
        "a bright measured gap between two points softly pulsing, blue and gold, very dark, subtle"),
 "s03":("Abstract dark background, a glowing slope where one direction glows warning red and the other calm green, which way is less wrong, deep blue with red and green accents, very dark, minimal, NO text",
        "a glowing slope shifting between red and green sides, blue red green, very dark, subtle"),
 "s04":("Abstract dark background, a smooth curved hill of soft light with a single glowing arrow pointing down the incline, the gradient, deep blue with gold, very dark, minimal, NO text",
        "a soft curved hill with a glowing downhill arrow, blue and gold, very dark, subtle"),
 "s05":("Abstract dark background, a small glowing point descending a smooth hill in small steps toward the bottom, gradient descent, deep blue and gold, very dark, minimal, NO text",
        "a glowing point stepping down a smooth hill, blue and gold, very dark, subtle"),
 "s06":("Abstract dark background, a vast rolling landscape of soft glowing hills and valleys receding into depth, an error landscape, deep indigo and gold, very dark, minimal cinematic, NO text",
        "a vast rolling glowing landscape of hills and valleys slowly drifting, indigo and gold, very dark, subtle"),
 "s07":("Abstract dark background, layered columns of glowing nodes with a pulse of light rippling backward through them, backpropagation, deep blue and gold, very dark, minimal, NO text",
        "a pulse of light rippling backward through layered glowing nodes, blue and gold, very dark, subtle"),
 "s08":("Abstract dark background, a glowing correction arrow scaling in size beside a target, proportional adjustment, deep blue and gold, very dark, minimal, NO text",
        "a glowing correction arrow gently growing and shrinking beside a target, blue and gold, very dark, subtle"),
 "s09":("Abstract dark background, a tiny faint arrow beside a huge bright glowing arrow, the bigger the error the bigger the lesson, deep blue and gold, very dark, minimal, NO text",
        "a small faint arrow beside a large bright arrow softly pulsing, blue and gold, very dark, subtle"),
 "s10":("Abstract dark background, a crisp glowing measured value beside a soft formless felt glow, measurable versus unmeasurable, deep blue and gold, very dark, minimal, NO text",
        "a crisp glowing value beside a soft formless glow, blue and gold, very dark, subtle"),
 "s11":("Abstract dark background, a glowing point descending a smooth hill in clean steps settling toward a low basin, the loop of improvement, deep blue and gold, very dark, minimal, NO text",
        "a glowing point descending a hill in clean steps to a basin, blue and gold, very dark, subtle"),
 "s12":("Abstract dark calm background, a glowing point resting at the bottom of a soft luminous valley, resolution, deep indigo and gold, very dark, minimal serene cinematic, NO text",
        "a glowing point resting in a soft luminous valley, indigo and gold, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep07_{sid}.png"; clip=f"{CLIPDIR}/bg_ep07_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep07_{sid}_boom.mp4"
    if os.path.exists(boomp): print("skip",sid,flush=True); continue
    if not os.path.exists(img):
        r=requests.post("http://localhost:4000/v1/images/generations",headers={"Authorization":f"Bearer {KEY}"},
            json={"model":"gpt-image-1.5","size":"1536x1024","n":1,"prompt":imgp},timeout=200)
        if r.status_code!=200: print("IMG ERR",sid,r.status_code,r.text[:150],flush=True); continue
        it=r.json()["data"][0]; d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
        open(img,"wb").write(d); print("img",sid,flush=True)
    else: print("img-reuse",sid,flush=True)
    subprocess.run([PY,"/home/ubuntu/image_to_clip.py","--image",img,"--out",clip,
        "--frames","161","--width","1024","--height","576","--steps","10","--prompt",vidp],cwd="/home/ubuntu")
    if os.path.exists(clip): boom(clip,boomp); print("boom",sid,flush=True)
    else: print("CLIP FAIL",sid,flush=True)
print("ALL_BG_EP07_DONE",flush=True)
