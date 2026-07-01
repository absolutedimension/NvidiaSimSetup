#!/usr/bin/env python3
"""Generate the two studio-chooser card base images (gpt-image-1.5), in the same
cinematic 'alive thumbnail' style as the trigunai.com persona cards."""
import base64, requests
from pathlib import Path

OUT = Path(__file__).parent / "studio_thumbs" / "scenes"
OUT.mkdir(parents=True, exist_ok=True)
EP = "https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com"
KEY = "3BCCtGZV2hkdG4jjQoWVNdgdtD92EzZeGx8r9Mcu2cjYlG519aoBJQQJ99CCACHYHv6XJ3w3AAAAACOGZ2cP"
VER = "2025-04-01-preview"

BASE = ("premium 3D render, near-black background, volumetric glow, ultra-detailed, "
        "cinematic, centered subject, no text, no words, no letters, no logos")

SCENES = {
    # Shader Studio — audio-reactive sacred geometry / meditation (gold-cosmic,
    # matches the landing palette since this studio is the healing/ambient one)
    "shader": ("A luminous Sri Yantra sacred-geometry mandala made of golden light glowing over "
               "deep indigo cosmic space, concentric audio-waveform rings rippling outward, soft "
               "particles, meditative tech-spiritual aesthetic, warm gold and amber with indigo "
               f"accents. {BASE}"),
    # RTX Variant Studio — photoreal automotive product render (dark studio, the
    # RTX/MDL look the studio actually produces)
    "rtx": ("A sleek photoreal hypercar in a dark professional studio, glossy reflective carpaint, "
            "chrome and carbon-fibre details, dramatic rim lighting and reflections, a subtle "
            "emerald-green accent light, premium automotive product render, moody and cinematic. "
            f"{BASE}"),
}


def gen(name, prompt):
    url = f"{EP}/openai/deployments/gpt-image-1.5/images/generations?api-version={VER}"
    r = requests.post(url, headers={"api-key": KEY, "Content-Type": "application/json"},
                      json={"prompt": prompt, "n": 1, "size": "1024x1024",
                            "quality": "high", "output_format": "png"}, timeout=180)
    r.raise_for_status()
    (OUT / f"{name}.png").write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print("  ✓", name)


for n, p in SCENES.items():
    print("Generating", n, flush=True)
    gen(n, p)
print("Done ->", OUT)
