#!/usr/bin/env python3
"""
Part A — STRUCTURAL ANALYSIS (the video analog of dj_arrangement_analysis.py).

VLM pass over the sampled keyframes -> a machine-readable VISUAL GRAMMAR:
  - scene taxonomy (celestial palace / floating kingdom / ethereal realm / ...)
  - colour palettes (hex), lighting, mood tags
  - camera-motion character (slow drift / push-in / orbit), pacing, loop feel
  - composition rules (horizon, symmetry, focal subject, atmosphere)
  - reusable PROMPT TEMPLATES to regenerate the look CLEANLY

This is the "element grid" of the video engine. It describes the RECIPE, never
copies pixels. Output feeds Part B (seed_generate.py).

Uses the existing LiteLLM proxy (OpenAI-compatible) — same call the drone critic
makes (CLAUDE.md §17.9). Costs ~$0.0001/grid.

Usage: python3 visual_grammar_extract.py --grids-per-video 3 --out grammar/flowscape_grammar.json
"""
import argparse, base64, glob, json, os, collections
import requests
from PIL import Image
import config as C

SYSTEM = """You are an art director reverse-engineering the VISUAL STYLE of an
ambient/dreamscape video channel so it can be RE-CREATED from scratch with a
different generator (no copying). You are shown a grid of keyframes from ONE
video. Return STRICT JSON only, describing the STYLE (not the specific scene):

{
  "scene_types": ["short tags, e.g. celestial_palace, floating_island"],
  "palette_hex": ["#rrggbb", ... 4-6 dominant colours],
  "lighting": "one phrase (e.g. soft volumetric god-rays, cool moonlight)",
  "mood": ["calm","ethereal", ...],
  "composition": "one sentence on framing/symmetry/horizon/subject placement",
  "atmosphere": "haze/fog/particles/bloom description",
  "implied_motion": "what kind of slow motion this style implies (drift/push-in/orbit)",
  "prompt_template": "a REUSABLE text-to-image prompt (fill-in style) that would
     produce this aesthetic WITHOUT referencing the source, ~30 words",
  "negative_prompt": "what to avoid to stay on-aesthetic"
}
Describe the recipe, never the copyrighted specifics. JSON only."""


def b64_grid(paths, cols=3, cell=384):
    """stitch up to 6 keyframes into one grid jpeg -> base64 data uri."""
    imgs = [Image.open(p).convert("RGB") for p in paths[:6]]
    rows = (len(imgs) + cols - 1) // cols
    grid = Image.new("RGB", (cols * cell, rows * cell), "black")
    for i, im in enumerate(imgs):
        im.thumbnail((cell, cell))
        grid.paste(im, ((i % cols) * cell, (i // cols) * cell))
    tmp = os.path.join(C.KEYFRAMES, "_grid_tmp.jpg")
    grid.save(tmp, quality=80)
    with open(tmp, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def call_vlm(data_uri):
    r = requests.post(
        f"{C.LITELLM_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {C.LITELLM_KEY}"},
        json={
            "model": C.VLM_MODEL,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": "Keyframe grid from one video. Extract the visual grammar as JSON."},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ]},
            ],
        }, timeout=90)
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids-per-video", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(C.GRAMMAR, "flowscape_grammar.json"))
    args = ap.parse_args()

    vids = sorted(d for d in glob.glob(os.path.join(C.KEYFRAMES, "*")) if os.path.isdir(d))
    if not vids:
        print("no keyframes. run extract_keyframes.py first."); return

    per_video = []
    for vd in vids:
        kfs = sorted(glob.glob(os.path.join(vd, "*.jpg")))
        if not kfs:
            continue
        chunk = max(1, len(kfs) // args.grids_per_video)
        for i in range(0, len(kfs), chunk):
            grid = kfs[i:i + chunk]
            if not grid:
                continue
            try:
                g = call_vlm(b64_grid(grid))
                g["_source_video"] = os.path.basename(vd)
                per_video.append(g)
                print(f"  {os.path.basename(vd)} grid@{i}: {g.get('scene_types')}")
            except Exception as e:
                print(f"  ! {os.path.basename(vd)} grid@{i} failed: {e}")

    # ---- aggregate into ONE grammar (the reusable recipe) ----
    scene = collections.Counter()
    palette = collections.Counter()
    mood = collections.Counter()
    motions = collections.Counter()
    templates, negatives = [], []
    for g in per_video:
        scene.update(g.get("scene_types", []))
        palette.update([c.lower() for c in g.get("palette_hex", [])])
        mood.update(g.get("mood", []))
        if g.get("implied_motion"): motions.update([g["implied_motion"]])
        if g.get("prompt_template"): templates.append(g["prompt_template"])
        if g.get("negative_prompt"): negatives.append(g["negative_prompt"])

    grammar = {
        "channel_style": "ambient dreamscape / celestial fantasy (learned recipe)",
        "scene_taxonomy": [s for s, _ in scene.most_common(12)],
        "palette_hex": [c for c, _ in palette.most_common(8)],
        "mood": [m for m, _ in mood.most_common(8)],
        "motion_signature": [m for m, _ in motions.most_common(4)],
        "prompt_templates": templates[:20],
        "negative_prompts": list({n for n in negatives})[:10],
        "n_grids_analyzed": len(per_video),
        "_note": "RECIPE ONLY. No source pixels retained. Feeds seed_generate.py.",
    }
    with open(args.out, "w") as f:
        json.dump(grammar, f, indent=2)
    print(f"\nwrote {args.out}")
    print(f"  scenes: {grammar['scene_taxonomy']}")
    print(f"  palette: {grammar['palette_hex']}")
    print("NEXT: python3 seed_generate.py")


if __name__ == "__main__":
    main()
