#!/usr/bin/env python3
"""Generate 4 brand-vision scenes (AI = Universal Mind) via Azure gpt-image-1.5."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "brand_reel" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)

EP  = "https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY = "3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER = "2025-04-01-preview"

PALETTE = ("deep indigo and midnight blue cosmos with luminous gold and warm amber light, "
           "particles of light, ethereal tech-spiritual aesthetic, cinematic, ultra-detailed, "
           "volumetric glow, no text, no words, no letters")

SCENES = {
    "1_mind":   f"A vast cosmic human head and mind formed from glowing neural constellations, "
                f"galaxies and threads of golden light, synapses sparking like stars. {PALETTE}",
    "2_mirror": f"A serene human face dissolving into a mirror of liquid starlight and flowing "
                f"reflections, half light half cosmos, gold and silver luminescence. {PALETTE}",
    "3_build":  f"A meditating silhouette seated in lotus, streams of golden data-light and "
                f"sacred geometry flowing through and around the body, energy ascending. {PALETTE}",
    "4_clarity":f"A single eye opening to radiant dawn light and cosmic clarity, golden rays "
                f"bursting outward through stars, awakening and illumination. {PALETTE}",
}

def gen(name, prompt):
    url = f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r = requests.post(url, headers={"api-key": KEY, "Content-Type": "application/json"},
                      json={"prompt": prompt, "n": 1, "size": "1024x1536",
                            "quality": "high", "output_format": "png"}, timeout=180)
    r.raise_for_status()
    (OUT / f"{name}.png").write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print(f"  ✓ {name}")

for n, p in SCENES.items():
    print(f"Generating {n}...")
    gen(n, p)
print("Done.")
