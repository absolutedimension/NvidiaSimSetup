#!/usr/bin/env python3
"""grammar_generate.py (v3 — ONE locked groove, slow arc) — hypnotic techno needs a
CONSISTENT rhythm that the listener locks into; interest comes from elements slowly
entering/leaving over a long arc, NOT from the groove changing.

So: take ONE core groove, seamlessly loop it (crossfade the loop seam = no click, same
rhythm), and apply ONE clean arc — slow build (drone -> kick -> bass -> hats enter
gradually) -> HOLD the peak -> gradual wind-down (strip back, end on the drone). Hats are
the last-in/first-out energy lever; bass+drone+kick are the locked bed (learned grammar).

Usage: python3 grammar_generate.py --core CORE.mp3 --minutes 15 --out OUT.wav
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
ap.add_argument("--break-at", type=float, default=0.62, help="one short breakdown at this track fraction (0=none)")
ap.add_argument("--work", default="/home/ubuntu/dj_engine/_genwork")
a=ap.parse_args()
SR=44100; T=int(a.minutes*60*SR); X=int(4.0*SR)
os.makedirs(a.work, exist_ok=True)

def lp(x,f): return sosfilt(butter(4,f/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def hp(x,f): return sosfilt(butter(4,f/(SR/2),btype="high",output="sos"),x).astype(np.float32)

# demucs the ONE core
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

# ONE clean arc: slow build -> hold peak -> gradual wind-down. Control points = (track-frac, gain).
def env(points):
    x=np.linspace(0,1,T); e=np.interp(x,[p[0] for p in points],[p[1] for p in points])
    c=np.cumsum(np.insert(e,0,0.0)); k=int(1.5*SR); s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s); return np.concatenate([np.full(pad//2,s[0]),s,np.full(pad-pad//2,s[-1])]).astype(np.float32)

# optional ONE short breakdown (drop kick+hats, keep bass+drone) — learned: ~60s, retains bed
bk=a.break_at
def with_break(pts, drop):  # drop the element around the breakdown if 'drop'
    if bk<=0: return pts
    return pts  # breakdown applied separately below via mask

# the bed is bass (rolling engine) + kick; hats = lever. The melodic "other"/piano is the
# constant tonal layer the listener disliked -> REMOVE it (keep only a faint SUB-filtered
# trace at the peak for warmth, no piano tone).
other_warm = lp(other, 200) * 0.30          # kill the piano tone, keep only low warmth
# kick comes in EARLY + clear so the beat establishes during the build (the "background beat")
kickE = env([(0,0.0),(0.03,0.35),(0.12,1.0),(0.88,1.0),(0.96,0.0)])
bassE = env([(0,0.0),(0.05,0.30),(0.25,1.0),(0.86,1.0),(0.96,0.0)])  # faint rumble early -> full by 25%
hatsE = env([(0,0.0),(0.40,0.0),(0.52,1.0),(0.80,1.0),(0.86,0.0)])   # hats LAST in (~52%) / FIRST out (~80%)
warmE = env([(0,0.0),(0.45,0.0),(0.55,1.0),(0.78,1.0),(0.85,0.0)])   # faint warmth only around the peak

# one short breakdown: drop kick+hats, keep bass (his signature)
if bk>0:
    w=int(60*SR); c0=int(bk*T); s0=max(0,c0-w//2); s1=min(T,c0+w//2); ramp=int(6*SR)
    m=np.ones(T,np.float32); m[s0:s1]=0.0
    if s0-ramp>0: m[s0-ramp:s0]=np.linspace(1,0,ramp)
    if s1+ramp<T: m[s1:s1+ramp]=np.linspace(0,1,ramp)
    kickE=kickE*m; hatsE=hatsE*m

# SMOOTH BUILD: the filter opens on the SYNTH/HAT content only (muffled->open). The KICK stays
# crisp the whole time so the beat is clear from early in the build.
bedmix = bass*bassE + hats*hatsE + other_warm*warmE
muff = lp(bedmix, 500)
openE = env([(0,0.10),(0.40,1.0),(0.78,1.0),(1.0,0.30)])
bedmix = muff*(1.0-openE) + bedmix*openE
mix = bedmix + kick*kickE                      # clear, unfiltered beat on top

# overall energy: slow rise -> plateau -> gentle decline
plate=env([(0,0.50),(0.32,1.0),(0.80,1.0),(1.0,0.45)])
mix=mix*(0.6+0.4*plate)
mix=mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out,mix,SR)

n=28; w=len(mix)//n
e=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); e/=e.max()
print("[gen] ONE locked groove, slow build -> hold -> wind-down" + (f" + breakdown @ {int(bk*100)}%" if bk>0 else ""))
print("[gen] arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in e))
print(f"[gen] DONE -> {a.out}")
