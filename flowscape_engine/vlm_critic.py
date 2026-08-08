#!/usr/bin/env python3
"""
AESTHETIC AUTO-FILTER — the drone VLM-critic pattern (CLAUDE.md §17.9), reused.

Scores each generated seed against the grammar (on-aesthetic? calming? artifact-
free?) and copies the keepers into seeds_clean/. This is the cheap 80%-of-RL move
we discussed: a reward model that curates the next training round without the
instability of DDPO/DRaFT.

Also usable to grade FINAL video keyframes (--mode video) before publishing.

Usage:
  python3 vlm_critic.py --mode seeds  --min-score 7
  python3 vlm_critic.py --mode video  --mp4 output/flowscape_30min.mp4
"""
import argparse, base64, glob, json, os, shutil, subprocess
import requests
import config as C

SYSTEM = """You grade an AI-generated ambient dreamscape image for a sleep/study
channel. Return STRICT JSON:
{ "on_aesthetic": 1-10, "calming": 1-10, "coherent": 1-10,
  "artifacts": 1-10 (10=none), "overall": 1-10,
  "issues": ["..."], "verdict": "keep" | "reject" }
CRITICAL: if the image is broken/garbled/has text or watermarks/looks generic-AI,
score low and verdict=reject. Do NOT be generous. JSON only."""


def b64(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def grade(path):
    r = requests.post(
        f"{C.LITELLM_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {C.LITELLM_KEY}"},
        json={"model": C.VLM_MODEL, "temperature": 0.2,
              "response_format": {"type": "json_object"},
              "messages": [
                  {"role": "system", "content": SYSTEM},
                  {"role": "user", "content": [
                      {"type": "text", "text": "Grade this image."},
                      {"type": "image_url", "image_url": {"url": b64(path)}},
                  ]}]},
        timeout=60)
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def filter_seeds(min_score):
    seeds = sorted(glob.glob(os.path.join(C.SEEDS, "seed_*.png")))
    kept = 0
    report = []
    for s in seeds:
        try:
            v = grade(s)
        except Exception as e:
            print(f"  ! {os.path.basename(s)}: {e}"); continue
        report.append({"file": s, **v})
        if v.get("verdict") == "keep" and v.get("overall", 0) >= min_score:
            base = os.path.basename(s)
            shutil.copy(s, os.path.join(C.SEEDS_CLEAN, base))
            txt = s.replace(".png", ".txt")
            if os.path.exists(txt):
                shutil.copy(txt, os.path.join(C.SEEDS_CLEAN, base.replace(".png", ".txt")))
            kept += 1
    with open(os.path.join(C.SEEDS_CLEAN, "critic_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nkept {kept}/{len(seeds)} -> {C.SEEDS_CLEAN}")
    print("NEXT: python3 train_lora.py")


def grade_video(mp4, n=6):
    tmp = os.path.join(C.OUTPUT, "_critic_frames"); os.makedirs(tmp, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vf", f"fps=1/30,scale=512:-1",
                    "-frames:v", str(n), os.path.join(tmp, "f_%02d.jpg")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    scores = [grade(p) for p in sorted(glob.glob(os.path.join(tmp, "*.jpg")))]
    avg = sum(s.get("overall", 0) for s in scores) / max(1, len(scores))
    print(json.dumps({"avg_overall": round(avg, 2), "frames": scores}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["seeds", "video"], default="seeds")
    ap.add_argument("--min-score", type=int, default=7)
    ap.add_argument("--mp4")
    args = ap.parse_args()
    if args.mode == "seeds":
        filter_seeds(args.min_score)
    else:
        grade_video(args.mp4)


if __name__ == "__main__":
    main()
