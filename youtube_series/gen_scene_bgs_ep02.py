#!/usr/bin/env python3
"""Generate contextual-abstract background (image + LTX clip + boomerang) for each Ep2 scene.
Dark, abstract, NO text/objects — echoes each scene's concept. Output: clips/bg_ep02_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, three distant points of light joined by a single faint glowing thread across darkness, hidden connection between different things, deep indigo blue, very dark empty center, minimal cinematic, NO text NO objects",
        "three points of light joined by a faint thread, gently drifting, deep blue, very dark, subtle"),
 "s02":("Abstract dark background, a faint grid of rigid lines dissolving into a soft diffuse glowing web of light, order becoming a network, deep blue, very dark, minimal negative space, NO text",
        "rigid lines slowly dissolving into a soft glowing web, deep blue, very dark, subtle motion"),
 "s03":("Abstract dark background, a single glowing ring of warm light slowly rotating in deep darkness, an endless cycle, soft gold and amber, very dark empty center, minimal cinematic, NO text",
        "a glowing ring of warm light slowly rotating, gold amber, very dark, smooth continuous"),
 "s04":("Abstract dark background, a soft glowing region of light handing a bright trail across to a deeper quieter region, front to depth, deep blue with warm gold, very dark, minimal, NO text",
        "a bright trail of light slowly flowing from one glow to a deeper one, blue and gold, very dark, subtle"),
 "s05":("Abstract dark background, a faint neural pathway of light thickening and brightening into a strong worn channel, deep blue brightening to gold, very dark, minimal, NO text",
        "a faint light pathway slowly thickening and brightening, blue to gold, very dark, subtle pulsing"),
 "s06":("Abstract dark background, a small glowing core with faint shimmering filaments adjusting around it and a soft reward pulse rising, machine learning, deep teal and gold, very dark, minimal, NO text",
        "shimmering filaments gently adjusting around a glowing core, teal and gold, very dark, subtle"),
 "s07":("Abstract dark background, two vertical columns of soft light with faint glowing links bridging across between them, translation between two worlds, deep blue and green, very dark, minimal, NO text",
        "faint glowing links bridging between two columns of light, blue and green, very dark, subtle"),
 "s08":("Abstract dark background, an endless faint lattice of glowing points receding into infinite depth, vast multitude, deep indigo, very dark, minimal cinematic, NO text",
        "an endless lattice of glowing points slowly receding into depth, deep indigo, vast, subtle"),
 "s09":("Abstract dark background, a calm field of soft light buffeted by drifting turbulent noise and flickering grain, chaos testing order, deep blue with restless motion, very dark, minimal, NO text",
        "a field of soft light buffeted by drifting noise and flicker, deep blue, very dark, restless subtle"),
 "s10":("Abstract dark background, two glowing clusters of networked light side by side pulsing softly in unison, deep blue and green, very dark, minimal, NO text",
        "two glowing network clusters pulsing softly in unison, blue and green, very dark, subtle"),
 "s11":("Abstract dark background, two glowing clusters, one steady and one reaching a tendril of light toward a new distant unlit point, deep blue and warm gold, very dark, minimal, NO text",
        "one glowing cluster reaching a tendril of light toward a new distant point, blue and gold, very dark, subtle"),
 "s12":("Abstract dark background, two parallel channels of light racing toward a single bright point, one fading one strengthening, deep red and green, very dark, minimal, NO text",
        "two parallel light channels racing toward a bright point, red and green, very dark, subtle motion"),
 "s13":("Abstract dark calm background, soft converging rays of gentle light into a quiet luminous center, resolution and stillness, deep indigo and violet, very dark, minimal serene cinematic, NO text",
        "soft converging rays of light slowly breathing toward a calm center, indigo violet, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep02_{sid}.png"; clip=f"{CLIPDIR}/bg_ep02_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep02_{sid}_boom.mp4"
    if os.path.exists(boomp): print("skip",sid,flush=True); continue
    if not os.path.exists(img):                       # reuse image if already generated
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
print("ALL_BG_EP02_DONE",flush=True)
