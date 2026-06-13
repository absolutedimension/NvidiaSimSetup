#!/usr/bin/env python3
"""Contextual-abstract backgrounds (image + LTX clip + boomerang) for each Ep5 scene.
Theme: intuition / neural networks — signals firing across a glowing web, layers, a curve
bending through points, experience compressed into a pattern. Dark, abstract, NO text/objects.
Output: clips/bg_ep05_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, a soft glow at the center sending faint concentric ripples outward into deep darkness, a wordless flash of recognition, deep indigo blue with warm gold, very dark empty space, minimal cinematic, NO text NO objects",
        "a soft central glow sending faint ripples outward into darkness, indigo and gold, very dark, subtle"),
 "s02":("Abstract dark background, a delicate web of glowing nodes and threads lighting up in a rippling cascade across deep darkness, a sense firing across a network, deep blue and violet, very dark, minimal cinematic, NO text",
        "a web of glowing nodes lighting up in a rippling cascade, deep blue violet, very dark, subtle"),
 "s03":("Abstract dark background, a single smooth luminous arc sweeping swiftly and effortlessly across deep darkness, motion faster than thought, deep blue with a warm gold trail, very dark, minimal cinematic, NO text",
        "a smooth luminous arc sweeping swiftly across darkness, blue with gold trail, very dark, graceful"),
 "s04":("Abstract dark background, several faint threads of light converging into one bright pulsing point that flares as it crosses a threshold, a single unit firing, warm gold on deep indigo, very dark, minimal, NO text",
        "faint threads converging into one bright point that flares, gold on indigo, very dark, subtle pulse"),
 "s05":("Abstract dark background, layered columns of soft glowing points connected by fine threads receding into depth, simple parts stacked into layers, deep blue and violet, very dark, minimal cinematic, NO text",
        "layered columns of glowing points connected by threads receding into depth, blue violet, very dark, subtle"),
 "s06":("Abstract dark background, a flexible luminous ribbon flexing and bending smoothly to thread through a scattered field of glowing points, fitting any shape, deep blue with warm gold ribbon, very dark, minimal cinematic, NO text",
        "a luminous ribbon flexing and bending smoothly through scattered points, blue and gold, very dark, smooth"),
 "s07":("Abstract dark background, a web of glowing connections subtly brightening and dimming as it tunes and settles, learning, deep blue brightening to gold, very dark, minimal, NO text",
        "a web of connections subtly brightening and dimming as it settles, blue to gold, very dark, subtle"),
 "s08":("Abstract dark background, one bright answer-glow surrounded by countless tiny faint scattered sparks, a knowing with its reasons hidden, warm gold on deep indigo, very dark, minimal cinematic, NO text",
        "one bright glow surrounded by countless tiny faint sparks, gold on indigo, very dark, subtle shimmer"),
 "s09":("Abstract dark background, many faint streams of light flowing inward and compressing into one steady calm glow, experience compressed, deep blue flowing into warm gold, very dark, minimal cinematic, NO text",
        "faint streams of light flowing inward and compressing into one steady glow, blue to gold, very dark, smooth"),
 "s10":("Abstract dark background, a crisp clean glow on one side faintly disrupted by a dusting of fine static, beside a calm warm steady glow, certainty versus doubt, deep blue and warm gold, very dark, minimal, NO text",
        "a clean glow faintly dusted with static beside a calm warm glow, blue and gold, very dark, subtle"),
 "s11":("Abstract dark background, a tangle of scattered points of light slowly settling into one calm self-pulsing pattern, experience becoming intuition, deep indigo brightening to gold, very dark, minimal cinematic, NO text",
        "scattered points slowly settling into one calm self-pulsing pattern, indigo to gold, very dark, subtle"),
 "s12":("Abstract dark calm background, a slow pull back from one calm steady glow to a serene field of soft points of light in deep space, deep indigo and violet, very dark, minimal serene cinematic, NO text",
        "a slow pull back from one calm glow to a serene field of soft points, indigo violet, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep05_{sid}.png"; clip=f"{CLIPDIR}/bg_ep05_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep05_{sid}_boom.mp4"
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
print("ALL_BG_EP05_DONE",flush=True)
