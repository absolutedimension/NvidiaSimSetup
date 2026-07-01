#!/usr/bin/env python3
"""Generate gold-cosmic square base images for trigunai.com persona cards."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "persona_thumbs" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)
EP="https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY="3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER="2025-04-01-preview"

BASE=("premium 3D render, near-black background, warm golden and amber luminous light with deep "
      "indigo cosmic accents, volumetric glow, ethereal tech-spiritual aesthetic, ultra-detailed, "
      "cinematic, centered subject, no text, no words, no letters")

SCENES={
  "curious":      f"A luminous human eye opening into a reflective mirror of stars and galaxies, "
                  f"cosmic reflection, gold light radiating. {BASE}",
  "futureproof":  f"A glowing seedling sprout made of golden light and circuitry growing upward, "
                  f"particles rising, future-energy. {BASE}",
  "noncoder":     f"Glowing handwritten words and voice waves transforming into a small luminous "
                  f"holographic app interface, idea-to-software, golden light. {BASE}",
  "builder":      f"Golden luminous hands assembling a glowing geometric 3D object / holographic "
                  f"VR construct mid-air, sparks of creation. {BASE}",
}
def gen(n,p):
    url=f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r=requests.post(url,headers={"api-key":KEY,"Content-Type":"application/json"},
        json={"prompt":p,"n":1,"size":"1024x1024","quality":"high","output_format":"png"},timeout=180)
    r.raise_for_status()
    (OUT/f"{n}.png").write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"])); print("  ✓",n)
for n,p in SCENES.items():
    print("Generating",n); gen(n,p)
print("Done.")
