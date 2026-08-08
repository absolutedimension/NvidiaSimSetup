#!/usr/bin/env python3
"""
Part C.2 — SEQUENCING GRAMMAR -> SHOT LIST (video analog of grammar_generate.py).

The DJ engine turns the arrangement grammar into a track structure (intro -> peak
-> breakdown ...). Here we turn the visual grammar into a SHOT LIST for a long
ambient video: a sequence of scenes + camera moves + hold times that gives the
video a slow arc instead of one flat loop.

Output: scene_plans/<name>.json consumed by render_flowscape.py.

Usage: python3 scene_plan.py --minutes 30 --name flowscape_30min
"""
import argparse, json, os, random
import config as C

# ambient long-form arc (mirrors the DJ intro->peak->breakdown->outro idea):
# a slow procession of scenes, each held long, gentle motion, occasional "reveal".
ARC = ["establish", "drift", "reveal", "drift", "hold", "reveal", "wind_down"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=30)
    ap.add_argument("--name", default="flowscape_30min")
    ap.add_argument("--grammar", default=os.path.join(C.GRAMMAR, "flowscape_grammar.json"))
    ap.add_argument("--hold", type=int, default=25, help="seconds each scene holds (loop target)")
    args = ap.parse_args()

    with open(args.grammar) as f:
        grammar = json.load(f)
    scenes = grammar.get("scene_taxonomy") or ["celestial palace", "floating island"]
    motions = grammar.get("motion_signature") or ["slow drift", "gentle push-in", "slow orbit"]
    templates = grammar.get("prompt_templates") or ["{scene}, ethereal dreamscape, soft light"]

    total_s = args.minutes * 60
    n_shots = max(1, total_s // args.hold)
    shots = []
    for i in range(n_shots):
        scene = random.choice(scenes).replace("_", " ")
        beat = ARC[i % len(ARC)]
        motion = random.choice(motions)
        t = random.choice(templates)
        prompt = (t.replace("{scene}", scene) if "{scene}" in t else f"{t}, {scene}")
        shots.append({
            "idx": i, "beat": beat, "scene": scene,
            "prompt": f"{prompt}, palette {', '.join(grammar.get('palette_hex', [])[:3])}",
            "motion": motion,
            "hold_seconds": args.hold,
            "clip_seconds": C.CLIP_SECONDS,   # img->video length; the rest is slow-loop pad
        })

    plan = {"name": args.name, "minutes": args.minutes, "n_shots": len(shots),
            "lora": "flowscape_v1", "shots": shots}
    out = os.path.join(C.SCENE_PLANS, f"{args.name}.json")
    with open(out, "w") as f:
        json.dump(plan, f, indent=2)
    print(f"wrote {out}: {len(shots)} shots ~{args.minutes} min")
    print("NEXT: python3 render_flowscape.py --plan", out)


if __name__ == "__main__":
    main()
