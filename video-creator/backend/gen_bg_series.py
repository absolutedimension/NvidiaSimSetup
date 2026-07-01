#!/usr/bin/env python3
import json, base64, subprocess, os
OUT=os.path.expanduser("~/dj_engine/burmeister/series_bg"); os.makedirs(OUT, exist_ok=True)
KEY="sk-trigunai-master-key-2026"; URL="http://localhost:4000/v1/images/generations"
prompts={
 "01_attention":"A single luminous golden eye of concentrated light in deep cosmic darkness, focused golden rays converging, minimal, sharp, deep gold and black, sacred meditative, ultra detailed",
 "02_learning":"Glowing neural root network growing and branching, warm amber and emerald green bioluminescence, organic fractal growth spreading, dark background, spiritual, ultra detailed",
 "03_imagination":"Swirling dreamlike nebula of violet magenta and soft pink luminous mist, cosmic dream clouds emerging from darkness, ethereal psychedelic, ultra detailed",
 "04_meaning":"A vast constellation web of glowing indigo blue nodes connected by threads of light, deep cosmic network, everything interconnected, dark spacious, ultra detailed",
 "05_intuition":"Flowing liquid light in teal and cyan, smooth effortless luminous currents of energy, serene, dark background, dreamy ultra detailed",
 "06_will":"Intense solar fire, radiating crimson and orange energy from a blazing core, powerful directed flames, dark cosmic dramatic, ultra detailed",
 "07_better":"Ascending crystalline light, white gold and silver geometric shards rising in refined precision, ethereal luminous, dark background, ultra detailed",
 "08_flow":"Transcendent cosmic aurora, all colors dissolving into flowing luminous golden iridescent unity, expansive ecstatic light, spiritual surrender, ultra detailed",
}
for name,p in prompts.items():
    body=json.dumps({"model":"gpt-image-1.5","prompt":p,"size":"1536x1024","n":1})
    r=subprocess.run(["curl","-s","-m","150",URL,"-H",f"Authorization: Bearer {KEY}",
      "-H","Content-Type: application/json","-d",body], capture_output=True,text=True)
    try:
        d=json.loads(r.stdout); open(f"{OUT}/{name}.png","wb").write(base64.b64decode(d["data"][0]["b64_json"])); print("OK",name)
    except Exception as e: print("FAIL",name,str(e)[:120])
