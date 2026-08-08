#!/usr/bin/env python3
"""score_take.py — the RL critic. Scores a generated take against the style rubric.

Measures the same features on the take (mix + demucs-vocal) and returns a weighted
0-10 style-score = the "have we reached Shukla's style yet" signal. Calibrated to
the REAL reference's measured mean/range (not idealized numbers).

Runs in audio_pipeline venv; uses m2_venv demucs to split the take's vocal.

Usage:
  audio_pipeline/venv/bin/python score_take.py --take out.mp3 --rubric rubric_shukla_90s.json \
    --out out.score.json
"""
import argparse, json, os, subprocess, glob, sys
import numpy as np
from build_style_rubric import analyze_mix, analyze_vocal

M2 = "/home/ubuntu/m2_venv/bin/python"

def closeness(x, target, tol):
    """1.0 at target, decays linearly to 0 at target±tol."""
    if tol <= 0: return 1.0 if x == target else 0.0
    return float(max(0.0, 1.0 - abs(x - target) / tol))

def band(x, lo, hi, soft):
    """1.0 inside [lo,hi], decays over `soft` outside."""
    if lo <= x <= hi: return 1.0
    d = (lo - x) if x < lo else (x - hi)
    return float(max(0.0, 1.0 - d / soft))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", required=True)
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default="/home/ubuntu/singer_rl/_score")
    a = ap.parse_args()
    R = json.load(open(a.rubric)); M, V = R["mix"], R["vocal"]

    os.makedirs(a.work, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.take))[0]
    # split take -> vocal stem
    print(f"[score] demucs split {base}...", flush=True)
    subprocess.run(f'{M2} -m demucs --two-stems vocals -n htdemucs -o "{a.work}/dem" "{a.take}"',
                   shell=True, check=True, capture_output=True, text=True)
    voc = glob.glob(f"{a.work}/dem/htdemucs/{base}/vocals.wav")[0]

    print("[score] analyzing take...", flush=True)
    tm = analyze_mix(a.take); tv = analyze_vocal(voc)

    # ---- sub-scores (each 0-1), calibrated to the reference mean/range ----
    def rng(key, dct):
        r = dct.get(key + "_range");
        return (r[0], r[1]) if r else (dct[key], dct[key])
    sub = {}
    # ornamentation (murki) — the signature, weight .30
    olo, ohi = rng("ornament_rate_per_sec", V)
    sub["ornament"] = (band(tv.get("ornament_rate_per_sec",0), olo, ohi, soft=8.0), 0.30)
    # melody-dominant — weight .20
    hlo, hhi = rng("harmonic_percussive_ratio", M)
    sub["melody_dominant"] = (band(tm["harmonic_percussive_ratio"], hlo, hhi, soft=3.0), 0.20)
    # expression: pitch range + glide + vibrato — weight .20 (avg of 3)
    e_pr = closeness(tv.get("pitch_range_semitones",0), V["pitch_range_semitones"], tol=10.0)
    e_gl = closeness(tv.get("glide_semitone_per_frame",0), V["glide_semitone_per_frame"], tol=0.12)
    e_vb = closeness(tv.get("vibrato_semitone_std",0), V["vibrato_semitone_std"], tol=0.6)
    sub["expression"] = (float(np.mean([e_pr,e_gl,e_vb])), 0.20)
    # dynamics: dynamic range — weight .15
    dlo, dhi = rng("dynamic_range_db", M)
    sub["dynamics"] = (band(tm["dynamic_range_db"], dlo, dhi, soft=8.0), 0.15)
    # tempo in 99-120 band — weight .10
    sub["tempo"] = (band(tm["tempo_bpm"], 99, 120, soft=25.0), 0.10)
    # warmth/brightness — weight .05
    blo, bhi = rng("brightness_centroid_hz", M)
    sub["warmth"] = (band(tm["brightness_centroid_hz"], blo, bhi, soft=1500.0), 0.05)

    score10 = round(10.0 * sum(s*w for s,w in sub.values()), 2)
    verdict = ("in-style" if score10 >= 7.5 else
               "close-needs-tuning" if score10 >= 5.0 else
               "off-style")
    out = {
        "take": a.take, "style_score_0_10": score10, "verdict": verdict,
        "subscores": {k: {"score": round(s,3), "weight": w} for k,(s,w) in sub.items()},
        "measured": {"mix": tm, "vocal": tv},
        "targets": {"ornament": [olo,ohi], "harmonic_percussive": [hlo,hhi],
                    "tempo_band": [99,120]},
    }
    json.dump(out, open(a.out,"w"), indent=2)
    print(json.dumps({"style_score_0_10": score10, "verdict": verdict,
                      "subscores": {k: round(s,3) for k,(s,w) in sub.items()},
                      "measured_ornament": tv.get("ornament_rate_per_sec"),
                      "measured_hp": tm["harmonic_percussive_ratio"],
                      "measured_tempo": tm["tempo_bpm"]}, indent=2))

if __name__ == "__main__":
    main()
