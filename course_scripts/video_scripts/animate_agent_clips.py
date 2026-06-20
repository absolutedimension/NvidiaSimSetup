#!/usr/bin/env python3
"""Drive LTX i2v over the 7 photoreal stills → short clips. Runs on EC2."""
import subprocess, os

IMG = "/home/ubuntu/agent_vid_build/img"
OUT = "/home/ubuntu/agent_vid_build/clips"
os.makedirs(OUT, exist_ok=True)

# gentle, realistic motion — subtle so photoreal humans don't warp
JOBS = [
    ("s01_hook",     "subtle natural motion, the person breathes and blinks slightly, very gentle slow camera push in, warm light"),
    ("s02_child",    "the small child hand gently reaches toward the soft teddy bear, soft natural motion, shallow depth of field"),
    ("s03_school",   "the student smiles slightly and shifts, blurred students move softly in the background, gentle camera"),
    ("s04_college",  "the student types on the laptop, subtle natural hand and head movement, soft ambient motion"),
    ("s05_graduate", "the professional types and glances at the screen, gentle ambient office motion, subtle"),
    ("s06_expert",   "the scholar shifts thoughtfully and blinks, subtle breathing, warm lamp glow, very gentle"),
    ("s07_close",    "hands typing on the keyboard, code gently scrolls on the screen, subtle realistic motion"),
]

for name, prompt in JOBS:
    src = f"{IMG}/{name}.png"
    out = f"{OUT}/{name}.mp4"
    print(f">> {name}", flush=True)
    r = subprocess.run(["/home/ubuntu/comfyenv/bin/python", "/home/ubuntu/image_to_clip.py",
                        "--image", src, "--prompt", prompt, "--out", out,
                        "--frames", "97", "--width", "768", "--height", "448", "--steps", "10"],
                       capture_output=True, text=True)
    ok = os.path.exists(out) and os.path.getsize(out) > 10000
    print(f"   {'OK' if ok else 'FAIL'} {out}", flush=True)
    if not ok:
        print("   stderr:", r.stderr[-300:], flush=True)
print("done", flush=True)
