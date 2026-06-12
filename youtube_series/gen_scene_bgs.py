#!/usr/bin/env python3
"""Generate contextual-abstract background image + LTX clip for each non-hero Ep1 scene."""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

# scene -> (image prompt, motion prompt) — dark, abstract, echoing the scene's concept
PROMPTS={
 "s01":("Abstract dark background, faint glowing threads connecting scattered points of light across darkness, the idea of hidden links between things, deep indigo blue, very dark empty center, minimal cinematic, NO text NO objects",
        "faint glowing connection threads slowly drifting in deep blue, very dark, subtle ambient motion"),
 "s02":("Abstract dark background, a faint branching tree of light spreading outward into darkness like a growing network, deep blue, subtle, very dark, minimal negative space, NO text",
        "faint branching light slowly spreading outward, deep blue, very dark, subtle motion"),
 "s05":("Abstract dark background, a soft wide beam of light slowly sweeping across deep darkness like a search, deep blue, minimal, very dark, lots of empty space, NO text",
        "a soft light beam slowly sweeping across darkness, deep blue, subtle cinematic"),
 "s07":("Abstract dark background, two distant glowing orbs of light with a faint forming bridge of light between them across darkness, deep blue with a warm gold accent, very dark minimal, NO text",
        "two glowing orbs with a faint connecting light gently pulsing, deep blue and gold, very dark, subtle"),
 "s08":("Abstract dark background, an endless faint lattice of glowing points receding into infinite depth, vast scale, deep indigo, very dark, minimal cinematic, NO text",
        "an endless lattice of glowing points slowly receding into depth, deep indigo, vast, subtle motion"),
 "s10":("Abstract dark calm background, soft converging rays of gentle light into a quiet luminous center, deep indigo and violet, very dark, minimal serene cinematic, NO text",
        "soft converging rays of light slowly breathing toward center, deep indigo violet, calm, very dark"),
}

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_{sid}.png"
    r=requests.post("http://localhost:4000/v1/images/generations",headers={"Authorization":f"Bearer {KEY}"},
        json={"model":"gpt-image-1.5","size":"1536x1024","n":1,"prompt":imgp},timeout=200)
    if r.status_code!=200: print("IMG ERR",sid,r.status_code,r.text[:150],flush=True); continue
    it=r.json()["data"][0]; d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
    open(img,"wb").write(d); print("img",sid,flush=True)
    subprocess.run([PY,"/home/ubuntu/image_to_clip.py","--image",img,"--out",f"{CLIPDIR}/bg_{sid}.mp4",
        "--frames","161","--width","1024","--height","576","--steps","10","--prompt",vidp],cwd="/home/ubuntu")
    print("clip",sid,flush=True)
print("ALL_BG_DONE",flush=True)
