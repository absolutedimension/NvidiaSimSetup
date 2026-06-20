#!/usr/bin/env python3
"""Generate photoreal per-scene people stills via LiteLLM proxy (Azure gpt-image-1.5). Runs on EC2."""
import os, base64, requests

KEY = "sk-trigunai-master-key-2026"
URL = "http://localhost:4000/v1/images/generations"
OUT = "/home/ubuntu/agent_vid_build/img"
os.makedirs(OUT, exist_ok=True)

STYLE = (" Photorealistic candid documentary photograph, real human, natural lighting, "
         "shallow depth of field, cinematic warm color grade, 16:9, high detail, authentic. "
         "Keep the lower third relatively uncluttered for a text caption.")

PROMPTS = {
    "s01_hook":     "A thoughtful person in their thirties looking slightly off camera, warm window light, "
                    "soft bokeh background, contemplative expression." + STYLE,
    "s02_child":    "A curious young child around six years old looking upward with wonder and a slight smile, "
                    "cozy warm home interior, candid moment." + STYLE,
    "s03_school":   "A school student around thirteen years old with a backpack in a bright school hallway, "
                    "candid, gently smiling, daylight." + STYLE,
    "s04_college":  "A college student around twenty years old working at a laptop outdoors on a university campus, "
                    "natural daylight, candid, focused." + STYLE,
    "s05_graduate": "A young professional around twenty six years old at a desk in a modern office, focused on work, "
                    "candid, soft daylight." + STYLE,
    "s06_expert":   "A distinguished scholar around fifty five years old wearing glasses in a warm library, "
                    "thoughtful expression, books behind, warm light." + STYLE,
    "s07_close":    "Close up of human hands typing on a laptop keyboard with lines of code visible on the screen, "
                    "warm focused light, shallow depth of field." + STYLE,
}

for name, prompt in PROMPTS.items():
    print(f">> {name} …", flush=True)
    try:
        r = requests.post(URL, headers={"Authorization": f"Bearer {KEY}"},
                          json={"model": "gpt-image-1.5", "prompt": prompt, "size": "1536x1024", "n": 1},
                          timeout=300)
        if r.status_code != 200:
            print(f"   ERROR {r.status_code}: {r.text[:200]}", flush=True); continue
        item = r.json()["data"][0]
        data = base64.b64decode(item["b64_json"]) if item.get("b64_json") else requests.get(item["url"]).content
        open(f"{OUT}/{name}.png", "wb").write(data)
        print(f"   saved {name}.png ({len(data)//1024} KB)", flush=True)
    except Exception as e:
        print(f"   FAILED {name}: {e}", flush=True)
print("done", flush=True)
