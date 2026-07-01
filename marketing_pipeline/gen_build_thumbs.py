#!/usr/bin/env python3
"""Generate contextual square base images for build.trigunai.com capability cards."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "build_thumbs" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)

EP  = "https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY = "3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER = "2025-04-01-preview"

BASE = ("premium 3D render, dark charcoal background (#0a0a0f), dramatic volumetric glow, "
        "ultra-detailed, cinematic studio lighting, depth of field, no text, no words, "
        "centered hero subject, sleek high-tech product-shot aesthetic")

SCENES = {
    "ai_agents": f"A glowing AI voice-agent orb made of luminous neural filaments and concentric "
                 f"sound waves rippling outward, vivid violet and magenta light. {BASE}",
    "xr_vr":     f"A sleek futuristic VR/MR headset floating, glowing teal and cyan accent light, "
                 f"holographic spatial UI panels drifting around it. {BASE}",
    "fullstack": f"An abstract cloud-software architecture: glowing server nodes, flowing data "
                 f"streams and code particles forming a network, electric blue light. {BASE}",
    "robotics":  f"A robotic arm (Franka Panda style) in a dark NVIDIA Isaac simulation grid, "
                 f"glowing orange and coral rim light, holographic motion-trajectory lines. {BASE}",
}

def gen(name, prompt):
    url = f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r = requests.post(url, headers={"api-key": KEY, "Content-Type": "application/json"},
                      json={"prompt": prompt, "n": 1, "size": "1024x1024",
                            "quality": "high", "output_format": "png"}, timeout=180)
    r.raise_for_status()
    (OUT / f"{name}.png").write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print(f"  ✓ {name}")

for n, p in SCENES.items():
    print(f"Generating {n}...")
    gen(n, p)
print("Done.")
