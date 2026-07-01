#!/usr/bin/env python3
"""Generate WIDE landscape base images for full-width card banners (build + persona)."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "wide_thumbs" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)
EP="https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY="3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER="2025-04-01-preview"

WIDE = ("wide cinematic landscape composition 16:9, premium 3D render, dramatic volumetric glow, "
        "ultra-detailed, depth of field, no text, no words, no letters")
DARK = "dark charcoal background (#0a0a0f),"
GOLD = "near-black background, warm golden amber light with deep indigo cosmic accents,"

SCENES = {
  # build capability cards (per-category color)
  "ai_agents":  f"A glowing violet AI voice orb of neural filaments with concentric sound waves rippling "
                f"across the frame, vivid violet and magenta light. {DARK} {WIDE}",
  "xr_vr":      f"A sleek futuristic VR/MR headset with holographic spatial UI panels drifting across a "
                f"wide scene, teal and cyan glow. {DARK} {WIDE}",
  "fullstack":  f"A wide cloud-software network: glowing server nodes and flowing data streams spanning "
                f"the frame, electric blue light. {DARK} {WIDE}",
  "robotics":   f"A robotic arm (Franka Panda) in a dark NVIDIA Isaac simulation grid with holographic "
                f"trajectory lines sweeping across, orange and coral rim light. {DARK} {WIDE}",
  # trigunai persona cards (gold-cosmic)
  "curious":    f"A luminous human eye opening into a wide mirror of stars and galaxies, cosmic reflection "
                f"spanning the frame, gold light radiating. {GOLD} {WIDE}",
  "futureproof":f"Golden seedlings and circuitry of light growing upward across a wide scene, particles "
                f"rising, future-energy. {GOLD} {WIDE}",
  "noncoder":   f"Glowing handwriting and voice waves flowing across the frame into a luminous holographic "
                f"app interface, idea-to-software, golden light. {GOLD} {WIDE}",
  "builder":    f"Golden luminous hands assembling a glowing holographic 3D / VR construct mid-air across a "
                f"wide scene, sparks of creation. {GOLD} {WIDE}",
}
def gen(n,p):
    url=f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r=requests.post(url,headers={"api-key":KEY,"Content-Type":"application/json"},
        json={"prompt":p,"n":1,"size":"1536x1024","quality":"high","output_format":"png"},timeout=180)
    r.raise_for_status()
    (OUT/f"{n}.png").write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"])); print("  ✓",n)
for n,p in SCENES.items():
    print("Generating",n); gen(n,p)
print("Done.")
