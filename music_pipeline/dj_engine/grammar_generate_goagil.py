#!/usr/bin/env python3
"""grammar_generate_goagil.py — GOA GIL arrangement grammar (forked from the Burmeister
v3 arranger). Goa trance is a DENSE psychedelic wall-of-sound, NOT sparse hypnotic techno.

Learned from 15 official Goa Gil album mixes (1995-2020):
  - DENSE bed from early; a short ambient/no-kick "invocation" intro (60% of his tracks).
  - the melodic "other" (acid 303 leads / arps / drone) is the SIGNATURE -> KEEP it near
    constant (active 0.90), do NOT delete it (that's the opposite of the techno recipe).
  - hats = the last-in/first-out energy lever (but earlier than techno, ~15-18%).
  - breakdowns: drop kick+hats, KEEP bass + the acid/drone float (learned retains:
    drone 0.75, bassline 0.62, stab 0.46, kick 0.0).
  - energy commits HIGH early (~0.79 by 10%) and PLATEAUS the whole journey, then a hard
    drop at the very end (the ▂ tail). NOT techno's slow 40% filter-open build.

Usage: python3 grammar_generate_goagil.py --core CORE.mp3 --minutes 15 --breaks 0.45,0.72 --out OUT.wav
Runs on the EC2 box (m2_venv demucs + soundfile + scipy).
"""
import argparse, os, subprocess, glob, sys
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

def sh(c):
    r=subprocess.run(c,shell=True,capture_output=True,text=True)
    if r.returncode: sys.stderr.write(r.stderr[-1500:]); raise SystemExit(f"failed: {c}")
    return r.stdout

ap=argparse.ArgumentParser()
ap.add_argument("--core", required=True)
ap.add_argument("--minutes", type=float, default=15.0)
ap.add_argument("--out", required=True)
ap.add_argument("--breaks", default="0.45,0.72", help="comma-separated breakdown fractions")
ap.add_argument("--intro", type=float, default=0.06, help="ambient invocation intro fraction (no kick)")
ap.add_argument("--work", default="/home/ubuntu/dj_engine/_genwork")
a=ap.parse_args()
SR=44100; T=int(a.minutes*60*SR); X=int(4.0*SR)
os.makedirs(a.work, exist_ok=True)

def lp(x,f): return sosfilt(butter(4,f/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def hp(x,f): return sosfilt(butter(4,f/(SR/2),btype="high",output="sos"),x).astype(np.float32)

# demucs the ONE core (locked groove)
cb=os.path.splitext(os.path.basename(a.core))[0]; sd=f"{a.work}/dem/htdemucs/{cb}"
if not os.path.exists(f"{sd}/bass.wav"):
    print("[gen] demucs split...", flush=True)
    sh(f'/home/ubuntu/m2_venv/bin/python -m demucs -n htdemucs -o "{a.work}/dem" "{a.core}"')
    sd=glob.glob(f"{a.work}/dem/htdemucs/{cb}*")[0]
def rd(n):
    y,_=sf.read(f"{sd}/{n}.wav", always_2d=True); return y.mean(axis=1).astype(np.float32)
dr=rd("drums"); kick=lp(dr,180); hats=hp(dr,2500); bass=rd("bass"); other=rd("other")

# seamless loop a stem to length T (crossfade the loop seam -> same groove, no click)
fin=np.linspace(0,1,X,dtype=np.float32); fout=fin[::-1]
def loop_to(y,T):
    if len(y)>=T+X: return y[:T]
    out=y.copy()
    while len(out)<T+X:
        out=np.concatenate([out[:-X], out[-X:]*fout + y[:X]*fin, y[X:]])
    return out[:T].astype(np.float32)
kick=loop_to(kick,T); hats=loop_to(hats,T); bass=loop_to(bass,T); other=loop_to(other,T)

def env(points):
    x=np.linspace(0,1,T); e=np.interp(x,[p[0] for p in points],[p[1] for p in points])
    c=np.cumsum(np.insert(e,0,0.0)); k=int(1.5*SR); s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s); return np.concatenate([np.full(pad//2,s[0]),s,np.full(pad-pad//2,s[-1])]).astype(np.float32)

breaks=[float(x) for x in a.breaks.split(",") if x.strip() and 0.0<float(x)<1.0]
I=a.intro

# --- GOA GIL envelopes: dense from early, ambient invocation intro, acid signature kept ---
# kick: silent through the invocation, then in fast & full by ~10%, out only at the very end
kickE = env([(0,0.0),(I,0.0),(I+0.02,0.85),(0.10,1.0),(0.94,1.0),(0.985,0.0)])
# bass: present from the invocation (drone-bass swell), full by ~10%
bassE = env([(0,0.18),(0.04,0.60),(0.10,1.0),(0.93,1.0),(0.985,0.0)])
# other (acid leads/arps/drone) = THE Goa signature: strong from early, near-constant 0.90
otherE= env([(0,0.40),(0.05,0.75),(0.12,1.0),(0.90,1.0),(0.99,0.55)])
# hats = last-in/first-out energy lever, but earlier than techno (~15%)
hatsE = env([(0,0.0),(0.12,0.0),(0.17,1.0),(0.86,1.0),(0.93,0.0)])

# keep the FULL melodic "other" (acid/drone) — light hp only to clear sub mud
other_sig = hp(other, 110)

# breakdowns: drop kick+hats, KEEP bass + acid/drone float (Goa's psychedelic breakdown)
for bk in breaks:
    w=int(60*SR); c0=int(bk*T); s0=max(0,c0-w//2); s1=min(T,c0+w//2); ramp=int(6*SR)
    m=np.ones(T,np.float32); m[s0:s1]=0.0
    if s0-ramp>0: m[s0-ramp:s0]=np.linspace(1,0,ramp)
    if s1+ramp<T: m[s1:s1+ramp]=np.linspace(0,1,ramp)
    kickE=kickE*m; hatsE=hatsE*m   # bass + acid stay -> the float

# MILD filter-open: bright/dense early (Goa is open with acid on top), only the
# invocation is muffled; opens fully by ~12%. slight close at the very end.
bedmix = bass*bassE + hats*hatsE + other_sig*otherE
muff = lp(bedmix, 650)
openE = env([(0,0.30),(0.12,1.0),(0.90,1.0),(1.0,0.45)])
bedmix = muff*(1.0-openE) + bedmix*openE
mix = bedmix + kick*kickE                      # crisp tribal kick on top

# overall energy: commit HIGH early -> long plateau -> hard drop at the very end
plate=env([(0,0.55),(0.10,1.0),(0.92,1.0),(0.965,1.0),(1.0,0.28)])
mix=mix*(0.65+0.35*plate)
mix=mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out,mix,SR)

n=28; w=len(mix)//n
e=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); e/=e.max()
print("[gen] GOA GIL grammar: ambient invocation -> dense plateau (acid+drone kept) + drone-float breakdowns @ " + ",".join(f"{int(b*100)}%" for b in breaks))
print("[gen] arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in e))
print(f"[gen] DONE -> {a.out}")
