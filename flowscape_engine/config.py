"""
Flowscape Engine — shared config.

Mirrors the dj_engine philosophy: reference material is a TEACHER only.
We learn the STYLE/GRAMMAR (not copyrightable) and RECREATE everything clean.
Downloaded corpus is NEVER fed to a trainer — only the VLM analyzer reads it.
"""
import os

# ---- paths (all relative to this file so it runs the same on Mac + EC2) ----
ROOT        = os.path.dirname(os.path.abspath(__file__))
CORPUS      = os.path.join(ROOT, "corpus")        # downloaded videos — ANALYSIS ONLY
KEYFRAMES   = os.path.join(ROOT, "keyframes")     # sampled stills for the VLM
GRAMMAR     = os.path.join(ROOT, "grammar")       # extracted visual-grammar JSON
SEEDS       = os.path.join(ROOT, "seeds")         # raw Flux generations from grammar
SEEDS_CLEAN = os.path.join(ROOT, "seeds_clean")   # VLM-critic-approved training set
LORAS       = os.path.join(ROOT, "loras")         # trained LoRA weights
SCENE_PLANS = os.path.join(ROOT, "scene_plans")   # grammar -> shot lists
OUTPUT      = os.path.join(ROOT, "output")        # final videos

# ---- VLM (reuse the drone pipeline's LiteLLM proxy: OpenAI-compatible) ----
# On EC2 this is the litellm-proxy container on :4000 (see CLAUDE.md §3).
LITELLM_BASE = os.environ.get("LITELLM_BASE", "http://localhost:4000/v1")
LITELLM_KEY  = os.environ.get("LITELLM_KEY",  "sk-trigunai-master-key-2026")
VLM_MODEL    = os.environ.get("VLM_MODEL",    "gpt-4o-mini")

# ---- open, commercially-usable generation models (VERIFY each license before ship) ----
# Text->image aesthetic base + our LoRA on top.
# DEFAULT = SDXL: ~7GB, commercial-OK (OpenRAIL++), fits comfortably on a tight disk.
# UPGRADE to Flux (better for this ethereal look, ~34GB, needs ~55GB free) with:
#   IMAGE_MODEL=black-forest-labs/FLUX.1-schnell   (Apache-2.0, commercial, non-gated)
# Do NOT use FLUX.1-dev commercially — its license is NON-COMMERCIAL (research only).
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
# Image->video motion base. Stable Video Diffusion (SVD-xt): image-conditioned,
# NO text encoder (light, ~9.5GB), purpose-built for subtle ambient motion.
# Alt (heavier, needs ~15GB more): Lightricks/LTX-Video or Wan for text-guided motion.
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "stabilityai/stable-video-diffusion-img2vid-xt")
SVD_MOTION_BUCKET = int(os.environ.get("SVD_MOTION_BUCKET", "30"))  # low = calm drift
SVD_W, SVD_H = 1024, 576   # SVD-xt native resolution
SVD_EXPORT_FPS = int(os.environ.get("SVD_EXPORT_FPS", "7"))  # 25 frames/7fps = 3.5s of motion
CROSSFADE = float(os.environ.get("CROSSFADE", "2"))          # dissolve between scenes (s)

# ---- render defaults for the ambient-loop format ----
FPS          = 24
CLIP_SECONDS = 5          # each img->video shot
TARGET_W     = 1280
TARGET_H     = 720
UPSCALE_TO   = 1920       # Real-ESRGAN pass target width

for d in (CORPUS, KEYFRAMES, GRAMMAR, SEEDS, SEEDS_CLEAN, LORAS, SCENE_PLANS, OUTPUT):
    os.makedirs(d, exist_ok=True)
