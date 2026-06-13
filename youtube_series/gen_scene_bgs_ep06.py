#!/usr/bin/env python3
"""Contextual-abstract backgrounds (image + LTX clip + boomerang) for each Ep6 scene.
Theme: goal-pursuit / the pull. Dark, abstract, NO text/objects. Output: clips/bg_ep06_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, a distant glowing golden goal-point with a faint trail of light reaching toward it across deep darkness, wanting and pursuit, deep blue with gold, very dark empty center, minimal cinematic, NO text NO objects",
        "a faint trail of light slowly reaching toward a distant gold goal, deep blue, very dark, subtle"),
 "s02":("Abstract dark background, two points of light with a glowing taut tension line stretched between them across darkness, a gap, deep blue and gold, very dark, minimal, NO text",
        "a glowing tension line gently pulsing between two points, blue and gold, very dark, subtle"),
 "s03":("Abstract dark background, a glowing goal-point beside a rising vertical bar of warm light, a reward meter, deep blue with gold, very dark, minimal, NO text",
        "a vertical bar of warm light slowly rising beside a glow, gold, very dark, subtle"),
 "s04":("Abstract dark background, many faint trial paths of light fanning outward, a few brightening into gold toward a goal-point, learning to pursue, deep blue and gold, very dark, minimal, NO text",
        "faint trial paths fanning out, a few brightening toward a goal, blue and gold, very dark, subtle"),
 "s05":("Abstract dark background, a glowing ring of light with an arrow of light aimed toward a distant golden goal-point, a control loop, deep blue and gold, very dark, minimal, NO text",
        "a glowing ring with a beam aimed at a distant goal, blue and gold, very dark, subtle"),
 "s06":("Abstract dark background, a branching tree of faint light paths spreading outward with one path brightening into gold, planning, deep indigo and gold, very dark, minimal, NO text",
        "a branching tree of light with one path slowly brightening, indigo and gold, very dark, subtle"),
 "s07":("Abstract dark background, one large glowing goal-point splitting into several smaller connected goal-points, sub-goals, deep blue and gold, very dark, minimal, NO text",
        "a large glow splitting into smaller connected glows, blue and gold, very dark, subtle"),
 "s08":("Abstract dark background, a warm glow leaning toward a far golden goal while faint side tendrils of light tug it sideways, temptation, deep blue gold and rose, very dark, minimal, NO text",
        "a warm glow leaning toward a far goal with faint side-tugs, blue gold rose, very dark, subtle"),
 "s09":("Abstract dark background, a fixed glowing horizontal bar of light above and a path of light racing toward a goal beneath it, an unquestioned objective, deep blue and gold, very dark, minimal, NO text",
        "a path of light racing toward a goal beneath a fixed glowing bar, blue and gold, very dark, subtle"),
 "s10":("Abstract dark background, a glow turning away from a dim old goal-point toward a new bright unlit goal in a different direction, deep blue and gold, very dark, minimal, NO text",
        "a glow turning from a dim goal toward a new bright one, blue and gold, very dark, subtle"),
 "s11":("Abstract dark background, three small soft gap-and-pull motifs side by side, each a point pulled toward a glow, deep green blue and gold, very dark, minimal, NO text",
        "three small soft pull motifs glowing softly side by side, green blue gold, very dark, subtle"),
 "s12":("Abstract dark calm background, a moving point of light finally reaching and blooming into a distant golden goal, resolution, deep indigo and gold, very dark, minimal serene cinematic, NO text",
        "a point of light reaching and blooming into a distant goal, indigo and gold, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep06_{sid}.png"; clip=f"{CLIPDIR}/bg_ep06_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep06_{sid}_boom.mp4"
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
print("ALL_BG_EP06_DONE",flush=True)
