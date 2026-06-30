#!/usr/bin/env python3
"""progressive_arrange.py — turn a flat full-energy techno groove into a PROGRESSIVE
story-arc track by stem automation. Splits the core into drums/bass/other (Demucs) and
automates each stem's volume over the timeline: sparse intro (atmos only, NO bass),
gradual build, peak, breakdown (drop bass+drums), rebuild, outro. This removes the
"constant dominant element" and creates the build/journey.

Runs on the EC2 box (needs m2_venv demucs + librosa/soundfile).
Usage: python3 progressive_arrange.py --core CORE.mp3 --minutes 6 --out OUT.wav
"""
import argparse, os, subprocess, glob, sys
import numpy as np, soundfile as sf

def sh(c):
    r=subprocess.run(c,shell=True,capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-1500:]); raise SystemExit(f"failed: {c}")
    return r.stdout

ap=argparse.ArgumentParser()
ap.add_argument("--core", required=True)
ap.add_argument("--minutes", type=float, default=6.0)
ap.add_argument("--out", required=True)
ap.add_argument("--work", default="/home/ubuntu/music_out/_arrwork")
a=ap.parse_args()
SR=44100; T=int(a.minutes*60*SR)
os.makedirs(a.work, exist_ok=True)

# 1. Demucs split the core (drums / bass / other / vocals) — skip if already split
core_base=os.path.splitext(os.path.basename(a.core))[0]
stemdir=f"{a.work}/dem/htdemucs/{core_base}"
if os.path.exists(f"{stemdir}/bass.wav"):
    print("[arr] stems already present, skipping demucs", flush=True)
else:
    print("[arr] demucs split...", flush=True)
    sh(f'/home/ubuntu/m2_venv/bin/python -m demucs -n htdemucs -o "{a.work}/dem" "{a.core}"')
    stemdir=glob.glob(f"{a.work}/dem/htdemucs/*")[0]

def load_loop(name):
    y,_=sf.read(f"{stemdir}/{name}.wav", always_2d=True)
    y=y.mean(axis=1)                      # mono
    if len(y)<T: y=np.tile(y, int(np.ceil(T/len(y))))
    return y[:T].astype(np.float32)

drums=load_loop("drums"); bass=load_loop("bass"); other=load_loop("other")

# 2. per-stem volume ENVELOPES over the track (control points: fraction -> gain)
def env(points):
    fr=np.array([p[0] for p in points]); gn=np.array([p[1] for p in points])
    x=np.linspace(0,1,T)
    e=np.interp(x, fr, gn)
    # smooth (~0.4s) via O(N) cumsum moving average (np.convolve would be O(N*K) -> hangs)
    k=int(0.4*SR)
    c=np.cumsum(np.insert(e,0,0.0))
    s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s)
    e=np.concatenate([np.full(pad//2, s[0]), s, np.full(pad-pad//2, s[-1])])
    return e.astype(np.float32)

# the journey: intro=atmos only -> drums -> bass build -> peak -> breakdown -> peak2 -> outro
e_drums=env([(0,0),(0.10,0),(0.14,0.9),(0.55,1.0),(0.58,0.0),(0.66,0.0),(0.70,1.0),(0.92,1.0),(1.0,0.15)])
e_bass =env([(0,0),(0.20,0),(0.24,0.25),(0.37,1.0),(0.55,1.0),(0.57,0.0),(0.69,0.0),(0.75,1.0),(0.90,1.0),(0.96,0.0)])
e_other=env([(0,0.45),(0.05,0.8),(0.55,0.9),(0.60,0.65),(0.66,0.85),(0.90,0.9),(1.0,0.25)])

mix = drums*e_drums + bass*e_bass + other*e_other
mix = mix / (np.max(np.abs(mix))+1e-6) * 0.97      # normalize, leave headroom
sf.write(a.out, mix, SR)
# report the resulting arc
n=16; w=len(mix)//n
en=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); en/=en.max()
print("[arr] energy arc:", "".join("▁▂▃▄▅▆▇█"[min(7,int(v*7.999))] for v in en), flush=True)
print(f"[arr] DONE -> {a.out}", flush=True)
