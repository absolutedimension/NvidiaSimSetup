#!/usr/bin/env python3
"""Contextual-abstract backgrounds (image + LTX clip + boomerang) for each Ep4 scene.
Theme: meaning as geometry — words becoming points, constellations, maps, vectors, a galaxy
of words. Dark, abstract, NO text/objects. Output: clips/bg_ep04_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, a single soft point of light in deep darkness sending out faint glowing threads to many distant points, meaning as a web of connection, deep indigo blue, very dark empty space, minimal cinematic, NO text NO objects",
        "a point of light sending faint glowing threads outward to distant points, deep indigo, very dark, subtle drift"),
 "s02":("Abstract dark background, countless tiny points of light gently lifting and arranging themselves into a vast floating three-dimensional constellation in deep space, meaning becoming geometry, deep blue and gold, very dark, minimal cinematic, NO text",
        "tiny points of light slowly arranging into a floating three-dimensional constellation, deep blue gold, very dark, subtle"),
 "s03":("Abstract dark background, a bright central glow surrounded by smaller glints of light orbiting and linking to it with delicate lines, a constellation of related stars, warm gold on deep indigo, very dark, minimal, NO text",
        "a central glow with smaller glints orbiting and linking by delicate lines, gold on indigo, very dark, gentle"),
 "s04":("Abstract dark background, a dark map scattered with glowing points that gather into tight bright clusters in some regions and lie far apart in others, a map of meaning, deep blue with gold clusters, very dark, minimal cinematic, NO text",
        "glowing points gathering into tight clusters with empty space between, deep blue gold, very dark, subtle"),
 "s05":("Abstract dark background, a single brilliant point of light among a vast starfield of hundreds of fainter points in deep space, one coordinate in an enormous space, deep indigo and blue, very dark, minimal cinematic, NO text",
        "a single bright point among a vast starfield of fainter points, deep indigo, very dark, slow parallax"),
 "s06":("Abstract dark background, scattered points of light slowly drifting and converging toward one another into small glowing groups, words finding their neighborhood, deep blue brightening to gold, very dark, minimal, NO text",
        "scattered points slowly drifting and converging into small glowing groups, blue to gold, very dark, subtle"),
 "s07":("Abstract dark background, luminous straight vectors and glowing arrows travelling between bright points in a dark constellation, arithmetic in a space of meaning, deep blue with warm gold arrows, very dark, minimal cinematic, NO text",
        "glowing arrows travelling between bright points in a constellation, blue and gold, very dark, smooth motion"),
 "s08":("Abstract dark background, several pairs of points connected by perfectly parallel glowing arrows all pointing the same direction across a dark field, repeating relationships, deep indigo and gold, very dark, minimal, NO text",
        "pairs of points joined by parallel glowing arrows pointing the same way, indigo gold, very dark, subtle"),
 "s09":("Abstract dark background, a new point of light gently descending into an existing cluster and lighting up the points around it, finding its place, deep blue and violet brightening to gold, very dark, minimal, NO text",
        "a new point descending into a cluster and lighting up its neighbors, blue violet to gold, very dark, gentle"),
 "s10":("Abstract dark background, a free-floating web of glowing points on one side and a similar web whose roots reach downward into a deeper warm glow on the other, words touching only words versus words touching the world, deep blue and warm gold, very dark, minimal cinematic, NO text",
        "a free web of points beside a web with roots reaching down into a warm glow, blue and gold, very dark, subtle"),
 "s11":("Abstract dark background, a single dim isolated point of light slowly brightening as glowing connections form between it and surrounding points, meaning living in the relationships, deep indigo brightening to gold, very dark, minimal, NO text",
        "a dim point brightening as connections form to surrounding points, indigo to gold, very dark, subtle"),
 "s12":("Abstract dark calm background, a slow pull back from one glowing point to reveal an immense serene galaxy of countless points of light stretching into deep space, deep indigo and violet, very dark, minimal serene cinematic, NO text",
        "a slow pull back from one point to reveal a vast galaxy of countless points, indigo violet, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep04_{sid}.png"; clip=f"{CLIPDIR}/bg_ep04_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep04_{sid}_boom.mp4"
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
print("ALL_BG_EP04_DONE",flush=True)
