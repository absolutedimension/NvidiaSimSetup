#!/usr/bin/env python3
"""grammar_generate.py — arrange a core groove into a full track that FOLLOWS a
learned DJ grammar (from grammar_extract.py). Encodes the DJ's rules:
constant bed (bass+drone+kick), hats as the energy lever, short breakdowns that
keep bass+drone but drop hats, and the DJ's plateau energy arc.

Splits the core into stems (Demucs) and band-splits drums -> kick (low) + hats (high)
so hats can be automated independently. Runs on the EC2 box (m2_venv demucs + soundfile).

Usage: python3 grammar_generate.py --core CORE.mp3 --grammar grammar.json --minutes 8 --out OUT.wav
"""
import argparse, os, subprocess, glob, json, sys
import numpy as np, soundfile as sf

def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    if r.returncode: sys.stderr.write(r.stderr[-1500:]); raise SystemExit(f"failed: {c}")
    return r.stdout

ap = argparse.ArgumentParser()
ap.add_argument("--core", required=True)
ap.add_argument("--grammar", required=True)
ap.add_argument("--minutes", type=float, default=8.0)
ap.add_argument("--out", required=True)
ap.add_argument("--work", default="/home/ubuntu/dj_engine/_genwork")
a = ap.parse_args()
SR = 44100; T = int(a.minutes*60*SR)
os.makedirs(a.work, exist_ok=True)
G = json.load(open(a.grammar))

# 1. Demucs split the core (cache)
cb = os.path.splitext(os.path.basename(a.core))[0]
stemdir = f"{a.work}/dem/htdemucs/{cb}"
if not os.path.exists(f"{stemdir}/bass.wav"):
    print("[gen] demucs split...", flush=True)
    sh(f'/home/ubuntu/m2_venv/bin/python -m demucs -n htdemucs -o "{a.work}/dem" "{a.core}"')
    stemdir = glob.glob(f"{a.work}/dem/htdemucs/*")[0]

def load(name):
    y,_ = sf.read(f"{stemdir}/{name}.wav", always_2d=True); y = y.mean(axis=1)
    if len(y) < T: y = np.tile(y, int(np.ceil(T/len(y))))
    return y[:T].astype(np.float32)

drums = load("drums"); bass = load("bass"); other = load("other")

# band-split drums -> kick (low) + hats (high), so hats = independent lever
from scipy.signal import butter, sosfilt
def lp(x, f): return sosfilt(butter(4, f/(SR/2), btype="low", output="sos"), x).astype(np.float32)
def hp(x, f): return sosfilt(butter(4, f/(SR/2), btype="high", output="sos"), x).astype(np.float32)
kick = lp(drums, 180); hats = hp(drums, 2500)

# 2. build a section plan that FOLLOWS the grammar
secdur = G["section_durations_s"]
D = {t: secdur.get(t, {}).get("median", 90) for t in ["intro/ambient","build","peak","breakdown","groove"]}
bk_per_hr = G["breakdowns_per_hour"]["mean"]
# template sequence (the DJ's transition habit: intro -> alternating build/peak, periodic breakdowns, outro)
plan = [("intro/ambient", D["intro/ambient"])]
t_used = plan[0][1]; toggle = 0; since_bk = 0
target_bk_gap = 3600.0 / max(0.5, bk_per_hr)
while t_used < a.minutes*60 - D["peak"]:
    if since_bk >= target_bk_gap:
        plan.append(("breakdown", D["breakdown"])); since_bk = 0; t_used += D["breakdown"]; continue
    ty = "build" if toggle == 0 else "peak"; toggle ^= 1
    plan.append((ty, D[ty])); t_used += D[ty]; since_bk += D[ty]
plan.append(("outro", D["peak"]*0.6))
# scale plan to exactly target
tot = sum(d for _, d in plan); plan = [(t, d*a.minutes*60/tot) for t, d in plan]

# per-section element gains, from the grammar's roles
# bed = bass+drone+kick (retained); hats = lever (off in breakdown/intro); stab~other
def gains(ty):
    if ty == "intro/ambient": return dict(kick=0.0, bass=0.35, other=0.7, hats=0.0)
    if ty == "breakdown":     return dict(kick=0.0, bass=0.85, other=0.9, hats=0.0)  # keep bass+drone, drop kick+hats
    if ty == "outro":         return dict(kick=0.3, bass=0.6, other=0.7, hats=0.1)
    if ty == "build":         return dict(kick=1.0, bass=1.0, other=0.9, hats=0.6)
    return dict(kick=1.0, bass=1.0, other=1.0, hats=1.0)  # peak/groove

# 3. build smooth sample-envelopes per element + an overall plateau energy curve
arc = np.array(G["energy_arc_24"])
def smooth(e, k):
    c = np.cumsum(np.insert(e, 0, 0.0)); s = (c[k:]-c[:-k])/k
    pad = len(e)-len(s); return np.concatenate([np.full(pad//2, s[0]), s, np.full(pad-pad//2, s[-1])])
envs = {e: np.zeros(T, np.float32) for e in ["kick","bass","other","hats"]}
i0 = 0
bounds = []
for ty, d in plan:
    i1 = min(T, i0 + int(d*SR)); g = gains(ty)
    for e in envs: envs[e][i0:i1] = g[e]
    bounds.append((i0, i1, ty)); i0 = i1
for e in envs: envs[e] = smooth(envs[e], int(1.0*SR)).astype(np.float32)   # 1s ramps
# overall plateau gain from the DJ's energy arc
xe = np.linspace(0,1,T); plate = np.interp(xe, np.linspace(0,1,len(arc)), arc/arc.max())
plate = smooth(plate, int(2.0*SR)).astype(np.float32)

mix = (kick*envs["kick"] + bass*envs["bass"] + other*envs["other"] + hats*envs["hats"]) * (0.55 + 0.45*plate)
mix = mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out, mix, SR)

# report the arc + section plan
n=24; w=len(mix)//n
en=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); en/=en.max()
print("[gen] plan:", " ".join(f"{t.split('/')[0][:4]}{int(d)}s" for t,d in plan))
print("[gen] energy arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in en))
print(f"[gen] DONE -> {a.out}")
