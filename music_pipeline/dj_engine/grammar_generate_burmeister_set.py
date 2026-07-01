#!/usr/bin/env python3
"""grammar_generate_burmeister_set.py — chain N track-units into ONE long continuous
hypnotic-techno SET. Energy CARRIES between tracks: kick/bass/drone/hats never die
(floor ~0.6); each unit has build -> anticipation gate -> DROP (punchy explosion) -> peak,
then merges straight into the next unit (no gap/delay). Intro only at the very start,
outro only at the very end. Accents vary per unit so each feels like a different track.

Stems: kick, bass, bass2, drone, hats, stab (+perc). Accents: accents_prep/{sitar,bansuri}.wav
"""
import argparse, os, gc, numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

ap=argparse.ArgumentParser()
ap.add_argument("--stems", required=True); ap.add_argument("--accents", default=None)
ap.add_argument("--minutes", type=float, default=28.0); ap.add_argument("--tracks", type=int, default=0)
ap.add_argument("--bpm", type=float, default=123.0); ap.add_argument("--sr", type=int, default=44100)
ap.add_argument("--out", required=True)
a=ap.parse_args()
SR=a.sr; T=int(a.minutes*60*SR); X=int(4.0*SR); BPM=a.bpm; BAR=4*60.0/BPM; MIN=a.minutes
N=a.tracks or max(2, round(MIN/6.0))
beat=60.0/BPM

def lp(x,f): return sosfilt(butter(4,f/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def hp(x,f): return sosfilt(butter(2,f/(SR/2),btype="high",output="sos"),x).astype(np.float32)
def rms(y): return float(np.sqrt(np.mean(y**2))+1e-9)
def rd(n,db=None,dir=None):
    y,_=librosa.load(f"{dir or a.stems}/{n}.wav", sr=SR, mono=True); y=y.astype(np.float32)
    return (y*(10**(db/20.0)/rms(y))).astype(np.float32) if db is not None else y
def has(n,dir=None): return os.path.exists(f"{dir or a.stems}/{n}.wav")
def loop_to(y,T):
    xf=max(1,min(X,len(y)//2)); fin=np.linspace(0,1,xf,dtype=np.float32); fout=fin[::-1]
    if len(y)>=T+xf: return y[:T].copy()
    out=y.copy()
    while len(out)<T+xf: out=np.concatenate([out[:-xf],out[-xf:]*fout+y[:xf]*fin,y[xf:]])
    return out[:T].astype(np.float32)
def env(points):
    pts=sorted((min(1.0,max(0.0,x)),v) for x,v in points)
    x=np.linspace(0,1,T); e=np.interp(x,[p[0] for p in pts],[p[1] for p in pts])
    c=np.cumsum(np.insert(e,0,0.0)); k=int(0.15*SR); s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s); out=np.concatenate([np.full(pad//2,s[0]),s,np.full(pad-pad//2,s[-1])]).astype(np.float32)
    del e,c,s; return out
def tiled(local):
    """tile a per-unit template (local frac 0-1) across all N units -> global env."""
    pts=[]
    for u in range(N):
        b=u/N
        for lf,lv in local: pts.append((b+lf/N, lv))
    return env(pts)
def duck_env(depth=0.20,tau=0.09):
    tt=(np.arange(T)/SR)%beat; return (1.0-depth*np.exp(-tt/tau)).astype(np.float32)
duck=duck_env()

drops=[(u+0.5)/N for u in range(N)]          # one drop per unit (unit-centre)
# global shape: intro ramp at the very start, outro fade at the very end ONLY
gshape=env([(0,0.0),(0.02,1.0),(0.95,1.0),(1.0,0.0)])
# breakdown mask (short dip) + anticipation gate (1 beat near-silence) before EACH drop
bd=np.ones(T,np.float32); gate=np.ones(T,np.float32)
for dpf in drops:
    b0=int(dpf*T-2.5*BAR*SR); b1=int(dpf*T)
    if b0>0: bd[b0:b1]=np.linspace(0.75,0.12,b1-b0)     # gentler dip (energy stays up)
    gs=int(dpf*T-1.0*beat*SR); ge=int(dpf*T)
    if gs>0:
        gate[gs:ge]=0.06; gate[gs:gs+int(0.008*SR)]=np.linspace(1,0.06,int(0.008*SR))

# per-unit energy: HIGH floor 0.75 (carries between tracks) -> build -> dip -> DROP -> peak
plate=tiled([(0.0,0.75),(0.15,0.82),(0.42,0.86),(0.47,0.45),(0.50,1.05),(0.80,1.0),(0.92,0.82),(1.0,0.75)])

# --- continuous DRIVING bed (high floors so energy never dies between tracks) ---
mix=lp(hp(loop_to(rd("bass",-17),T),32),700)*tiled([(0.0,0.9),(0.46,0.95),(0.5,1.0),(0.84,1.0),(1.0,0.9)])*duck*bd*gshape; gc.collect()
if has("drone"):
    d=lp(hp(loop_to(rd("drone",-23),T),180),3200)
    mix+=d*tiled([(0.0,0.55),(0.5,0.62),(0.84,0.62),(1.0,0.55)])*duck*gshape; del d; gc.collect()
if has("stab"):
    s=hp(loop_to(rd("stab",-26),T),300)
    mix+=s*tiled([(0.0,0.12),(0.28,0.2),(0.44,0.2),(0.5,0.45),(0.8,0.45),(0.95,0.15),(1.0,0.12)])*duck*bd*gshape; del s; gc.collect()
if has("perc"):
    p=hp(loop_to(rd("perc",-25),T),260)
    mix+=p*tiled([(0.0,0.12),(0.38,0.18),(0.5,0.42),(0.8,0.42),(0.95,0.15),(1.0,0.12)])*duck*bd*gshape; del p; gc.collect()
h=hp(loop_to(rd("hats",-21),T),600)
mix+=h*tiled([(0.0,0.6),(0.3,0.65),(0.46,0.7),(0.5,1.0),(0.84,1.0),(0.94,0.68),(1.0,0.6)])*bd*gshape; del h; gc.collect()

# filter: never fully closes mid-set (stays fairly open so the groove keeps driving)
openE=tiled([(0.0,0.6),(0.42,0.65),(0.5,1.0),(0.84,1.0),(1.0,0.6)])
muff=lp(mix,500); mix=muff*(1.0-openE)+mix*openE; del muff,openE; gc.collect()

# kick on top: near-full continuous, full at peaks
mix+=lp(loop_to(rd("kick",-13),T),7000)*tiled([(0.0,0.92),(0.46,0.95),(0.5,1.0),(0.84,1.0),(1.0,0.92)])*bd*gshape; gc.collect()

# apply the anticipation gate to the whole groove (before per-drop FX)
mix*=gate; del gate; gc.collect()

# --- per-drop explosion: held sub + punchy 808 + bass2 + riser + impact + crash + atmosphere ---
if has("bass2"): b2=lp(hp(loop_to(rd("bass2",-18),T),50),1600)
else: b2=None
subwave=np.tanh(np.sin(2*np.pi*46.25*np.arange(T)/SR)*1.6).astype(np.float32)
subduck=duck_env(depth=0.10,tau=0.07)
# BASELINE sub throughout the set (low-end energy carries) + per-drop boost added below
mix+=subwave*tiled([(0.0,0.4),(0.5,0.5),(0.84,0.5),(1.0,0.4)])*subduck*0.5*gshape; gc.collect()
# punchy 808 hit
f808=92.5; hl=int(0.42*SR); th=np.arange(hl)/SR
hit=np.sin(2*np.pi*np.cumsum(f808*(1+4*np.exp(-th/0.018)))/SR)*np.exp(-th/0.22)
clk=int(0.004*SR); hit[:clk]+=np.random.randn(clk)*np.exp(-np.arange(clk)/(0.0018*SR))*0.5
hit=np.tanh(hit*1.9).astype(np.float32)
def peakwin(dpf,end):  # window a peak region [dpf, dpf+end*unit]
    return env([(0,0),(dpf-0.004,0),(dpf,1.0),(dpf+end/N,1.0),(dpf+(end+0.06)/N,0.0)])
for dpf in drops:
    pw=peakwin(dpf,0.30)
    mix+=subwave*pw*subduck*0.45
    if b2 is not None: mix+=b2*pw*duck*0.6
    # punchy 808 on offbeat 8ths through this peak
    ps=int(dpf*T); pe=int(min(1.0,dpf+0.34/N)*T); tcur=(int(dpf*MIN*60/beat)+0.5)*beat
    while tcur*SR<pe:
        s=int(tcur*SR)
        if ps<=s<pe and s<T: mix[s:min(pe,s+hl)]+=hit[:max(0,min(hl,pe-s))]*0.62
        tcur+=beat
    del pw
del subwave,subduck,hit
if b2 is not None: del b2
gc.collect()

# riser + impact + crash at each drop
rl=int(4*BAR*SR); tt=np.arange(rl)/SR; ramp=(tt/tt[-1])
riser=hp(np.random.randn(rl).astype(np.float32),600)*(ramp**2)*0.7 + np.sin(2*np.pi*(200+2600*ramp)*tt).astype(np.float32)*(ramp**3)*0.35
il=int(2.4*SR); ti=np.arange(il)/SR
imp=(np.sin(2*np.pi*(75*np.exp(-ti/0.3))*ti)*np.exp(-ti/0.5)).astype(np.float32)*1.4
imp[:int(0.03*SR)]+=np.random.randn(int(0.03*SR)).astype(np.float32)*0.7
cl2=int(1.9*SR); tc2=np.arange(cl2)/SR
crash=hp(np.random.randn(cl2).astype(np.float32),3000)*np.exp(-tc2/0.85)*0.55
for dpf in drops:
    e0=int(dpf*T); s0=e0-rl
    if s0>0: mix[s0:e0]+=riser[:e0-s0].astype(np.float32)
    mix[e0:e0+il]+=imp[:max(0,min(il,T-e0))]
    mix[e0:e0+cl2]+=crash[:max(0,min(cl2,T-e0))]
del riser,imp,crash; gc.collect()

# accents: vary per unit (odd units lean sitar, even lean bansuri); build hits + peak phrase
adir=a.accents
def place(clip,frac,g):
    s=int(frac*T); e=min(T,s+len(clip)); mix[s:e]+=clip[:e-s]*g
if adir:
    si=rd("sitar",dir=adir) if has("sitar",adir) else None
    ba=rd("bansuri",dir=adir) if has("bansuri",adir) else None
    for u in range(N):
        b=u/N
        lead=(si if (u%2==1 and si is not None) else ba); other=(ba if lead is si else si)
        for j,lf in enumerate([0.10,0.18,0.26,0.34,0.42]):
            c=(lead if j%2==0 else other)
            if c is None: c=lead if lead is not None else other
            if c is not None: place(c,b+lf/N,0.58)
        if ba is not None:
            place(ba,b+0.52/N,0.62); place(ba,b+0.66/N,0.55)
    gc.collect()

mix*=(0.6+0.4*plate); del plate; gc.collect()
# peak-weighted saturation across all peaks (fuller)
satE=np.zeros(T,np.float32)
for dpf in drops: satE+=env([(0,0),(dpf-0.004,0),(dpf,1.0),(dpf+0.28/N,1.0),(dpf+0.33/N,0.0)])
satE=np.clip(satE,0,1)
mix=mix+(np.tanh(mix*2.2)-mix)*(0.5*satE); del satE; gc.collect()

mix=mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out,mix,SR)
n=60; w=len(mix)//n
e=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); e/=e.max()
print(f"[gen] BURMEISTER SET: {N} track-units over {MIN}min, energy carries between drops")
print("[gen] arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in e))
print(f"[gen] DONE -> {a.out}")
