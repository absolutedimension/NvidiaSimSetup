#!/usr/bin/env python3
"""grammar_generate_goagil_stems.py — arrange clean psy stems into a full track using
GOA GIL's learned sequencing grammar (no demucs). MEMORY-LEAN: folds each element into
the mix and frees it immediately, so 60-min renders fit in RAM.

Stems in --stems: kick, bass, acid, arp, drone, hats (+optional chant, riser).
Grammar: ambient/chant invocation -> DENSE acid plateau committed early -> hats last-in
lever -> drone+acid FLOAT breakdowns (drop kick+hats, keep bass+acid+drone) -> hard end.

Usage: python3 grammar_generate_goagil_stems.py --stems DIR --minutes 60 --breaks 0.35,0.70 --out OUT.wav
"""
import argparse, os, gc, numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

ap=argparse.ArgumentParser()
ap.add_argument("--stems", required=True)
ap.add_argument("--minutes", type=float, default=15.0)
ap.add_argument("--breaks", default="0.45,0.72")
ap.add_argument("--intro", type=float, default=0.06)
ap.add_argument("--sr", type=int, default=44100)
ap.add_argument("--out", required=True)
a=ap.parse_args()
SR=a.sr; T=int(a.minutes*60*SR); X=int(4.0*SR)
I=a.intro
breaks=[float(x) for x in a.breaks.split(",") if x.strip() and 0.0<float(x)<1.0]

def lp(x,f): return sosfilt(butter(4,f/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def rd(n):
    y,_=librosa.load(f"{a.stems}/{n}.wav", sr=SR, mono=True); return y.astype(np.float32)

fin=np.linspace(0,1,X,dtype=np.float32); fout=fin[::-1]
def loop_to(y,T):
    if len(y)>=T+X: return y[:T].copy()
    out=y.copy()
    while len(out)<T+X:
        out=np.concatenate([out[:-X], out[-X:]*fout + y[:X]*fin, y[X:]])
    return out[:T].astype(np.float32)

def env(points):
    x=np.linspace(0,1,T); e=np.interp(x,[p[0] for p in points],[p[1] for p in points])
    c=np.cumsum(np.insert(e,0,0.0)); k=int(1.5*SR); s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s); out=np.concatenate([np.full(pad//2,s[0]),s,np.full(pad-pad//2,s[-1])]).astype(np.float32)
    del e,c,s; return out

# breakdown mask (drop kick+hats, thin arp; keep bass+acid+drone)
def break_mask(thin=False):
    m=np.ones(T,np.float32)
    for bk in breaks:
        w=int(64*SR); c0=int(bk*T); s0=max(0,c0-w//2); s1=min(T,c0+w//2); ramp=int(6*SR)
        m[s0:s1]=0.0
        if s0-ramp>0: m[s0-ramp:s0]=np.linspace(1,0,ramp)
        if s1+ramp<T: m[s1:s1+ramp]=np.linspace(0,1,ramp)
    return np.clip(m+0.25,0,1) if thin else m

# --- build mix incrementally, freeing each big array right after use ---
# bass bed
mix = loop_to(rd("bass"),T) * env([(0,0.0),(I*0.5,0.25),(0.04,0.6),(0.10,1.0),(0.93,1.0),(0.985,0.0)])
gc.collect()
# acid signature (near-constant)
mix += loop_to(rd("acid"),T) * env([(0,0.0),(0.05,0.25),(0.14,1.0),(0.90,1.0),(0.99,0.5)]); gc.collect()
# arp (ducks in breakdowns)
arpE = env([(0,0.0),(0.20,0.0),(0.27,0.9),(0.62,0.9),(0.70,0.3),(0.80,0.9),(0.90,0.0)]) * break_mask(thin=True)
mix += loop_to(rd("arp"),T) * arpE; del arpE; gc.collect()
# drone (invocation pad + breakdown float, near-constant)
mix += loop_to(rd("drone"),T) * env([(0,0.5),(0.03,0.9),(0.10,1.0),(0.95,1.0),(1.0,0.6)]); gc.collect()
# hats (last-in lever, out in breakdowns)
hatsE = env([(0,0.0),(0.12,0.0),(0.17,1.0),(0.86,1.0),(0.93,0.0)]) * break_mask()
mix += loop_to(rd("hats"),T) * hatsE; del hatsE; gc.collect()

# mild filter-open on the non-kick psychedelic content (invocation muffled, open by ~12%)
openE = env([(0,0.30),(0.12,1.0),(0.90,1.0),(1.0,0.45)])
muff = lp(mix, 600)
mix = muff*(1.0-openE) + mix*openE; del muff,openE; gc.collect()

# crisp kick on top (silent through invocation, out in breakdowns + at the very end)
kickE = env([(0,0.0),(I,0.0),(I+0.02,0.85),(0.10,1.0),(0.94,1.0),(0.985,0.0)]) * break_mask()
mix += loop_to(rd("kick"),T) * kickE; del kickE; gc.collect()

# energy: commit HIGH early -> plateau -> hard drop at the very end
plate=env([(0,0.55),(0.10,1.0),(0.92,1.0),(0.965,1.0),(1.0,0.28)])
mix *= (0.65+0.35*plate); del plate; gc.collect()

# chant invocation in the intro
cpath=f"{a.stems}/chant.wav"
if os.path.exists(cpath):
    yc=lp(rd("chant"),3500); L=min(len(yc),T)
    cg=env([(0,0.85),(I*0.8,0.7),(I+0.04,0.0),(1.0,0.0)])
    mix[:L]+= yc[:L]*cg[:L]*0.55; del yc,cg; gc.collect()

# FX risers crescendo INTO each drop (end of intro + each breakdown re-entry)
rpath=f"{a.stems}/riser.wav"
if os.path.exists(rpath):
    yr=rd("riser"); yr=yr/(np.max(np.abs(yr))+1e-6)*0.5
    for dp in [I]+[min(0.999, bk+32.0/(a.minutes*60)) for bk in breaks]:
        e=int(dp*T); s=e-len(yr)
        if s>0: mix[s:e]+=yr[:e-s]
    del yr

mix=mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out,mix,SR)
n=28; w=len(mix)//n
e=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); e/=e.max()
print("[gen] GOA GIL set: chant invocation -> dense acid plateau + drone-float breakdowns @ "+",".join(f"{int(b*100)}%" for b in breaks))
print("[gen] arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in e))
print(f"[gen] DONE -> {a.out}  ({a.minutes}min @ {SR}Hz)")
