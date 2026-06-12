#!/usr/bin/env python3
"""Generate Episode 1 hero image assets via the LiteLLM proxy (Azure gpt-image-1.5)."""
import os, base64, requests, sys

KEY = "sk-trigunai-master-key-2026"
URL = "http://localhost:4000/v1/images/generations"
OUT = "/home/ubuntu/youtube_series/assets"
os.makedirs(OUT, exist_ok=True)

STYLE = ("Dark cinematic minimal editorial illustration, NOT photoreal. "
         "Deep indigo and near-black palette with cool light and subtle gold accents. "
         "Lots of negative space for text overlay. 16:9 composition, elegant, moody.")

PROMPTS = {
    "img_party_crowd": "A crowded party seen as many abstract dark human silhouettes in a warm hazy room, "
                       "one single figure subtly glowing as if their voice cuts through the noise, the rest dim. "
                       "Sense of sound and overlapping conversation. " + STYLE,
    "img_spotlight_field": "A dark top-down field scattered with many small simple glowing objects, "
                          "and one bright focused spotlight pool illuminating a single object while everything else "
                          "fades into shadow. A metaphor for attention choosing one thing to ignore the rest. " + STYLE,
    "img_mind_network_head": "A human head in profile formed entirely from glowing connected nodes and thin light lines, "
                            "like a neural network shaped into a mind, deep indigo background, the network gently radiant. "
                            "Brain-as-network. " + STYLE,
}

for name, prompt in PROMPTS.items():
    print(f">> generating {name} …", flush=True)
    try:
        r = requests.post(URL, headers={"Authorization": f"Bearer {KEY}"},
                          json={"model": "gpt-image-1.5", "prompt": prompt,
                                "size": "1536x1024", "n": 1}, timeout=240)
        if r.status_code != 200:
            print(f"   ERROR {r.status_code}: {r.text[:300]}", flush=True); continue
        item = r.json()["data"][0]
        data = base64.b64decode(item["b64_json"]) if item.get("b64_json") else requests.get(item["url"]).content
        path = os.path.join(OUT, name + ".png")
        open(path, "wb").write(data)
        print(f"   saved {path} ({len(data)//1024} KB)", flush=True)
    except Exception as e:
        print(f"   FAILED {name}: {e}", flush=True)

print("done", flush=True)
