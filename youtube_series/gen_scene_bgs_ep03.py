#!/usr/bin/env python3
"""Contextual-abstract backgrounds (image + LTX clip + boomerang) for each Ep3 scene.
Theme: noise resolving into form. Dark, abstract, NO text/objects. Output: clips/bg_ep03_sNN_boom.mp4"""
import base64, requests, os, subprocess
KEY="sk-trigunai-master-key-2026"
OUTDIR="/home/ubuntu/youtube_series/bg_options"; CLIPDIR="/home/ubuntu/youtube_series/clips"
os.makedirs(OUTDIR,exist_ok=True); os.makedirs(CLIPDIR,exist_ok=True)
PY="/home/ubuntu/comfyenv/bin/python"

PROMPTS={
 "s01":("Abstract dark background, faint scattered particles of light softly hinting at the ghost of a forming presence in deep darkness, something emerging from nothing, deep indigo blue, very dark empty center, minimal cinematic, NO text NO objects",
        "faint particles of light gently drifting and hinting at a forming presence, deep indigo, very dark, subtle"),
 "s02":("Abstract dark background, a pale empty luminous rectangle floating in darkness beginning to crack and fragment, the myth of the blank canvas breaking, deep blue, very dark, minimal negative space, NO text",
        "a pale empty rectangle slowly cracking and fragmenting in darkness, deep blue, very dark, subtle"),
 "s03":("Abstract dark background, a vast field of fine grainy static noise flickering across deep darkness, television snow with no signal, cold blue-grey grain, very dark, minimal cinematic, NO text",
        "a field of fine grainy static noise softly flickering, cold blue-grey, very dark, restless subtle"),
 "s04":("Abstract dark background, a rough noisy mass with chips and flakes of grain breaking away to reveal a smooth glowing form beneath, sculpting by subtraction, deep blue with warm gold, very dark, minimal, NO text",
        "chips of grain slowly flaking away revealing a smooth glow beneath, blue and gold, very dark, subtle"),
 "s05":("Abstract dark background, a clear glowing ordered structure on one side gradually dissolving into chaotic static grain toward the other side, order falling into noise, deep blue, very dark, minimal, NO text",
        "a clear glowing structure slowly dissolving into static grain, deep blue, very dark, subtle drift"),
 "s06":("Abstract dark background, a grainy noisy patch with a single soft layer of static being lifted away to reveal a cleaner glow underneath, denoising one step, deep blue brightening to gold, very dark, minimal, NO text",
        "a layer of static gently lifting away to reveal a cleaner glow, blue to gold, very dark, subtle"),
 "s07":("Abstract dark background, a field of pure noise slowly resolving in soft sweeps into a single coherent glowing form rising out of static, creation from chaos, deep indigo brightening to warm gold, very dark, minimal cinematic, NO text",
        "a field of noise slowly resolving in sweeps into a glowing coherent form, indigo to gold, very dark, smooth"),
 "s08":("Abstract dark background, drifting streams of fine particles being gently bent and pulled toward a forming luminous center by an unseen gravity, guidance shaping chaos, deep blue with warm gold accent, very dark, minimal, NO text",
        "streams of particles gently bending toward a forming center, blue and gold, very dark, subtle pull"),
 "s09":("Abstract dark background, a soft blurry cloud of diffuse light slowly tightening and sharpening into a clear focused shape, fog becoming form, deep blue and violet, very dark, minimal, NO text",
        "a blurry cloud of light slowly tightening into a clear shape, blue violet, very dark, subtle"),
 "s10":("Abstract dark background, a cold complete crystalline lattice of light beside a warm soft living glow that gently reaches, machine and human, deep blue and warm gold, very dark, minimal, NO text",
        "a cold crystalline lattice beside a warm soft glow gently reaching, blue and gold, very dark, subtle"),
 "s11":("Abstract dark background, a swirl of random scattered points of light slowly organizing into a clean ordered glowing lattice, structure pulled from chaos, deep indigo brightening to gold, very dark, minimal, NO text",
        "scattered random points slowly organizing into a clean glowing lattice, indigo to gold, very dark, subtle"),
 "s12":("Abstract dark calm background, a last soft wash of gentle noise resolving into a quiet luminous center, resolution and stillness, deep indigo and violet, very dark, minimal serene cinematic, NO text",
        "a soft wash of noise slowly resolving into a calm luminous center, indigo violet, very dark, serene"),
}

def boom(clip,out):
    subprocess.run(["ffmpeg","-y","-i",clip,"-filter_complex","[0:v]reverse[r];[0:v][r]concat=n=2:v=1:a=0[v]",
        "-map","[v]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",out],capture_output=True)

for sid,(imgp,vidp) in PROMPTS.items():
    img=f"{OUTDIR}/bg_ep03_{sid}.png"; clip=f"{CLIPDIR}/bg_ep03_{sid}.mp4"; boomp=f"{CLIPDIR}/bg_ep03_{sid}_boom.mp4"
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
print("ALL_BG_EP03_DONE",flush=True)
