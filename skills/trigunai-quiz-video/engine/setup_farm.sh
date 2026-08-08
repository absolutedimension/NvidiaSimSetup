#!/usr/bin/env bash
# One-time, idempotent setup for the trigunai-quiz-video engine on the EC2 render farm.
# Installs the Devanagari + superscript-capable fonts and confirms the python deps.
set -e
echo "[quiz-video] installing fonts (Noto Devanagari + Noto core for superscripts)…"
sudo apt-get update -qq || true
sudo apt-get install -y fonts-noto-devanagari fonts-noto-core >/dev/null 2>&1 || \
  sudo apt-get install -y fonts-noto-devanagari fonts-noto >/dev/null 2>&1 || true
fc-cache -f >/dev/null 2>&1 || true

echo "[quiz-video] ensuring python deps (edge-tts, pillow, numpy)…"
python3 -m pip install --user --quiet --upgrade edge-tts pillow numpy 2>&1 | tail -1 || true

echo "[quiz-video] verifying…"
python3 - <<'PY'
import os
from PIL import features
print("  raqm (Devanagari shaping):", features.check("raqm"))
import edge_tts, numpy  # noqa
print("  edge-tts + numpy: OK")
paths = {
  "Deva regular": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
  "Deva bold":    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
  "Latin sup":    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
  "Latin bold":   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
for k,p in paths.items():
    print(("  ok  " if os.path.exists(p) else "  MISS"), k, "->", p)
PY
echo "[quiz-video] setup complete."
