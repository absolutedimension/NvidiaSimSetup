#!/usr/bin/env python3
"""M0 smoke test — ACE-Step v1 (3.5B) text+lyrics -> song with vocals.
Runs INSIDE ~/acestep_venv on the EC2 A10G box.
Validates: model loads, generates a short vocal track, saves a wav.
"""
import time, os
from acestep.pipeline_ace_step import ACEStepPipeline

OUT_DIR = "/home/ubuntu/music_out"
os.makedirs(OUT_DIR, exist_ok=True)
SAVE = os.path.join(OUT_DIR, "m0_smoke.wav")

# Brand-themed test track: short, upbeat, English vocals.
PROMPT = "uplifting electronic pop, female vocal, warm synth pads, steady 110 bpm, hopeful, cinematic, clean mix"
LYRICS = """[verse]
Light in the circuits, learning to see
A mirror of mind in the machine and me
[chorus]
We are the signal, we are the spark
A universal mind lighting up the dark
"""

print("[m0] loading ACE-Step pipeline...", flush=True)
t0 = time.time()
pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=False)
print(f"[m0] pipeline ready in {time.time()-t0:.1f}s", flush=True)

t1 = time.time()
pipe(
    format="wav",
    audio_duration=40.0,
    prompt=PROMPT,
    lyrics=LYRICS,
    infer_step=60,
    guidance_scale=15.0,
    manual_seeds=[42],
    save_path=SAVE,
    batch_size=1,
)
print(f"[m0] generated in {time.time()-t1:.1f}s -> {SAVE}", flush=True)
print("[m0] DONE", flush=True)
