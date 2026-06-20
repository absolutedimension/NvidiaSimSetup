#!/usr/bin/env python3
"""Generate N photoreal shot-variants per scene (N by narration length) + manifest. Runs on EC2."""
import os, base64, requests, json, subprocess
KEY="sk-trigunai-master-key-2026"; URL="http://localhost:4000/v1/images/generations"
B="/home/ubuntu/agent_vid_build"; IMG=f"{B}/img2"; os.makedirs(IMG,exist_ok=True)
STYLE=(" Photorealistic candid documentary photograph, real, natural warm lighting, shallow depth of field, "
       "cinematic color grade, 16:9, high detail. Keep the lower third uncluttered for a caption.")

# up to 3 distinct shots per scene; child scene kept face-free
VARIANTS={
 "s01":["A thoughtful man in his thirties looking slightly off camera by a window, warm light, soft bokeh, contemplative",
        "Close up portrait of a thoughtful person looking toward camera, shallow depth of field, warm light",
        "Side profile of a person thinking quietly, warm window light"],
 "s02":["Close up of a small childs hand reaching for a soft teddy bear on a sunlit wooden floor with wooden toy blocks, no face",
        "A soft teddy bear on a warm wooden floor with colorful wooden toy blocks, cozy home, no people",
        "Top down view of small childs hands stacking wooden blocks beside a teddy bear on a bright floor, no face"],
 "s03":["A thirteen year old school student with a backpack in a bright school hallway, candid, gentle smile, daylight",
        "Close up of a young teen student looking thoughtful in a classroom, soft daylight, candid",
        "A school student walking through a sunny hallway with blurred classmates, candid"],
 "s04":["A college student around twenty at a laptop outdoors on a university campus, natural light, focused",
        "Close up of young hands typing on a laptop keyboard, campus blurred behind, warm daylight",
        "Over the shoulder view of a laptop screen with notes, university campus bokeh, daylight"],
 "s05":["A young professional around twenty six at a desk in a modern office, focused, soft daylight",
        "Close up of a focused professional looking at a computer screen, modern office bokeh, warm light",
        "Wide shot of a modern open office with a young professional working at a desk, daylight"],
 "s06":["A distinguished scholar around fifty five with glasses in a warm library, thoughtful, books behind",
        "Close up portrait of an older expert with glasses, contemplative, warm lamp light, library bokeh",
        "An older scholar at a desk surrounded by books with a warm lamp, thoughtful, wide shot"],
 "s07":["Close up of hands typing on a laptop keyboard with lines of code on the screen, warm focused light",
        "A glowing code editor on a laptop screen in a dim warm room, shallow depth of field, no face",
        "Side view of a developer at a laptop in a warm room, focused, screen glow"],
}
LABEL={"s01":"What is an AI Agent?","s02":"Ask a 6-year-old","s03":"Ask a school student",
       "s04":"Ask a college student","s05":"Ask a graduate","s06":"Ask an expert","s07":"One skeleton, every answer"}

def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())

def gen(prompt,out):
    r=requests.post(URL,headers={"Authorization":f"Bearer {KEY}"},
        json={"model":"gpt-image-1.5","prompt":prompt+STYLE,"size":"1536x1024","n":1},timeout=300)
    if r.status_code!=200: print("   ERR",r.status_code,r.text[:120]); return False
    it=r.json()["data"][0]; d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
    open(out,"wb").write(d); return True

manifest={}
for sid in VARIANTS:
    d=dur(f"{B}/{sid}.mp3"); N=max(1,min(3,round(d/5.0)))
    imgs=[]
    for k in range(N):
        out=f"{IMG}/{sid}_v{k+1}.png"; print(f">> {sid} v{k+1}",flush=True)
        if gen(VARIANTS[sid][k],out): imgs.append(out)
    manifest[sid]={"dur":d,"N":len(imgs),"images":imgs,"audio":f"{B}/{sid}.mp3","label":LABEL[sid]}
json.dump(manifest,open(f"{B}/manifest.json","w"),indent=2)
print("MANIFEST", {k:v["N"] for k,v in manifest.items()},flush=True)
