#!/usr/bin/env python3
"""Generate 3 camera angles of the SAME rainy garden scene via Azure gpt-image-1.5."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "rain_reel" / "angles"
OUT.mkdir(parents=True, exist_ok=True)

EP  = "https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY = "3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER = "2025-04-01-preview"

# Same scene, consistent palette/elements, three camera angles
COMMON = ("rainy serene garden, large white cherry-blossom tree with pink accents, "
          "winding wet stone path, vibrant pink and yellow flower beds, green bamboo and "
          "trees in soft background, dramatic overcast sky, raindrops, ultra-detailed "
          "painterly digital art, dreamy saturated greens and pinks, cinematic, no text, no people")

ANGLES = {
    "front": f"Front-on eye-level view down the path. {COMMON}",
    "side":  f"Side three-quarter angle from the left, the blossom tree sweeping across frame, path curving to the right. {COMMON}",
    "low":   f"Low dramatic upward angle looking up at the towering blossom tree canopy against the stormy sky, path leading away below. {COMMON}",
}

def gen(name, prompt):
    url = f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r = requests.post(url, headers={"api-key": KEY, "Content-Type": "application/json"},
                      json={"prompt": prompt, "n": 1, "size": "1024x1536",
                            "quality": "high", "output_format": "png"}, timeout=180)
    r.raise_for_status()
    b64 = r.json()["data"][0]["b64_json"]
    p = OUT / f"{name}.png"
    p.write_bytes(base64.b64decode(b64))
    print(f"  ✓ {p}")

for name, prompt in ANGLES.items():
    print(f"Generating {name}...")
    gen(name, prompt)
print("Done.")
