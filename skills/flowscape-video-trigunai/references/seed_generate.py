#!/usr/bin/env python3
"""
Part B — COPYRIGHT-CLEAN SEED LIBRARY (video analog of the clean element library).

Generate our OWN images from the extracted grammar's prompt templates + palette,
using a commercially-licensed base model (Flux). These clean seeds — never the
downloaded frames — are the training set for the LoRA.

This is the crux of the copyright story: the fine-tune only ever sees images WE
generated. Paper trail = "trained only on images we generated ourselves."

Usage:
  python3 seed_generate.py --n 300 --grammar grammar/flowscape_grammar.json
Runs on the EC2 A10G. First run downloads Flux weights (~24 GB) to HF cache.
"""
import argparse, json, os, random
import config as C


def build_prompts(grammar, n):
    scenes = grammar.get("scene_taxonomy") or ["celestial palace", "floating island kingdom"]
    templates = grammar.get("prompt_templates") or [
        "a {scene}, ethereal fantasy dreamscape, soft volumetric light, "
        "calming atmosphere, cinematic, highly detailed, dreamy haze"
    ]
    palette = ", ".join(grammar.get("palette_hex", [])[:4])
    mood = ", ".join(grammar.get("mood", ["serene", "ethereal"]))
    out = []
    for _ in range(n):
        scene = random.choice(scenes).replace("_", " ")
        t = random.choice(templates)
        p = t.replace("{scene}", scene) if "{scene}" in t else f"{t}, {scene}"
        out.append(f"{p}, palette {palette}, mood: {mood}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--grammar", default=os.path.join(C.GRAMMAR, "flowscape_grammar.json"))
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.grammar) as f:
        grammar = json.load(f)
    prompts = build_prompts(grammar, args.n)
    neg = "; ".join(grammar.get("negative_prompts", ["text, watermark, logo, low quality, distorted"]))

    from imagegen import load_pipeline
    _, gen = load_pipeline()   # SDXL or Flux per config.IMAGE_MODEL

    manifest = []
    for i, prompt in enumerate(prompts):
        img = gen(prompt, seed=args.seed + i, negative=neg)
        fn = os.path.join(C.SEEDS, f"seed_{i:04d}.png")
        img.save(fn)
        # sidecar caption for LoRA training (kohya/diffusers expect .txt next to image)
        with open(fn.replace(".png", ".txt"), "w") as t:
            t.write(prompt)
        manifest.append({"file": fn, "prompt": prompt, "negative": neg})
        if i % 20 == 0:
            print(f"  {i}/{len(prompts)}")

    with open(os.path.join(C.SEEDS, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\ngenerated {len(manifest)} clean seeds in {C.SEEDS}")
    print("NEXT: python3 vlm_critic.py   (auto-filter -> seeds_clean/)")


if __name__ == "__main__":
    main()
