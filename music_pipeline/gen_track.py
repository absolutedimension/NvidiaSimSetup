#!/usr/bin/env python3
"""Reusable ACE-Step track generator (seed of M1).
Usage: gen_track.py --prompt "..." --out /path.wav [--lyrics "[inst]"]
       [--dur 120] [--seed 42] [--steps 60] [--ref REF.wav --ref-strength 0.5]
"""
import argparse, time, os
from acestep.pipeline_ace_step import ACEStepPipeline

ap = argparse.ArgumentParser()
ap.add_argument("--prompt", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--lyrics", default="[inst]")
ap.add_argument("--dur", type=float, default=120.0)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--steps", type=int, default=60)
ap.add_argument("--guidance", type=float, default=15.0)
ap.add_argument("--lyric-guidance", type=float, default=0.0)
ap.add_argument("--ref", default=None)
ap.add_argument("--ref-strength", type=float, default=0.5)
a = ap.parse_args()

os.makedirs(os.path.dirname(a.out), exist_ok=True)
print(f"[gen] {a.out} | dur={a.dur} seed={a.seed} loading...", flush=True)
t0 = time.time()
pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=False)
print(f"[gen] ready in {time.time()-t0:.1f}s", flush=True)

kw = dict(
    format="wav", audio_duration=a.dur, prompt=a.prompt, lyrics=a.lyrics,
    infer_step=a.steps, guidance_scale=a.guidance, guidance_scale_lyric=a.lyric_guidance,
    manual_seeds=[a.seed], save_path=a.out, batch_size=1,
)
if a.ref:
    kw.update(audio2audio_enable=True, ref_audio_input=a.ref, ref_audio_strength=a.ref_strength)

t1 = time.time()
pipe(**kw)
print(f"[gen] done in {time.time()-t1:.1f}s -> {a.out}", flush=True)
print("[gen] DONE", flush=True)
