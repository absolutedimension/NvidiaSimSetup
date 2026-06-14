#!/usr/bin/env python3
"""Upbeat house study/focus music — INSTRUMENTAL. ACE-Step v1 3.5B.
The isochronic-tone layer is added afterward with ffmpeg (precise gating)."""
import time, os
from acestep.pipeline_ace_step import ACEStepPipeline

OUT = "/home/ubuntu/music_out/focus_house_raw.wav"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

PROMPT = ("upbeat deep house, study focus music, four on the floor groove, steady 122 bpm, "
          "warm analog synth, melodic plucks, driving bassline, hypnotic, bright, energetic, "
          "instrumental, no vocals, clean mix")
LYRICS = "[inst]"   # instrumental

print("[focus] loading...", flush=True)
t0 = time.time()
pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=False)
print(f"[focus] ready in {time.time()-t0:.1f}s", flush=True)

t1 = time.time()
pipe(
    format="wav",
    audio_duration=120.0,
    prompt=PROMPT,
    lyrics=LYRICS,
    infer_step=60,
    guidance_scale=15.0,
    manual_seeds=[123],
    save_path=OUT,
    batch_size=1,
)
print(f"[focus] generated in {time.time()-t1:.1f}s -> {OUT}", flush=True)
print("[focus] DONE", flush=True)
