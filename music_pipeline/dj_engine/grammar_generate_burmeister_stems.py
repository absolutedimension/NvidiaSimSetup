#!/usr/bin/env python3
"""grammar_generate_burmeister_stems.py — v7: held-back build -> breakdown -> DROP that
EXPLODES into a fuller peak (adds a 2nd bass + extra offbeat open-hats + more sitar/bansuri),
SUSTAINS the high, then RELEASES elements ONE BY ONE (open-hats->perc->stab->bass2->hats->
kick->bass) back to the sparse drone we started on. v2 mixing kept; gentle master.

Stems: kick, bass, bass2, drone, hats, stab (+perc). Accents: accents_prep/{sitar,bansuri}.wav
"""
import argparse, os, gc, numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

ap=argparse.ArgumentParser()
ap.add_argument("--stems", required=True); ap.add_argument("--accents", default=None)
ap.add_argument("--minutes", type=float, default=7.0); ap.add_argument("--bpm", type=float, default=123.0)
ap.add_argument("--drop", type=float, default=0.48); ap.add_argument("--sr", type=int, default=44100)
ap.add_argument("--out", required=True)
a=ap.parse_args()
SR=a.sr; T=int(a.minutes*60*SR); X=int(4.0*SR); BPM=a.bpm; BAR=4*60.0/BPM; dp=a.drop; MIN=a.minutes
PK=dp+0.20   # sustained-peak end

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
    x=np.linspace(0,1,T); e=np.interp(x,[p[0] for p in points],[p[1] for p in points])
    c=np.cumsum(np.insert(e,0,0.0)); k=int(0.15*SR); s=(c[k:]-c[:-k])/k
    pad=len(e)-len(s); out=np.concatenate([np.full(pad//2,s[0]),s,np.full(pad-pad//2,s[-1])]).astype(np.float32)
    del e,c,s; return out
def win_env(spans,lvl,ramp=0.008):
    pts=[(0.0,0.0)]
    for s,e in spans: pts+=[(s,0.0),(min(s+ramp,e),lvl),(max(e-ramp,s),lvl),(e,0.0)]
    pts+=[(1.0,0.0)]; return env(pts)
def duck_env(depth=0.20,tau=0.09):
    tt=(np.arange(T)/SR)%(60.0/BPM); return (1.0-depth*np.exp(-tt/tau)).astype(np.float32)
duck=duck_env()

bd=np.ones(T,np.float32); b0=int(dp*T-3.5*BAR*SR); b1=int(dp*T)
if b0>0: bd[b0:b1]=np.linspace(0.55,0.03,b1-b0)

# energy: held-back build -> breakdown dip -> EXPLODE -> sustain -> staggered descent
plate=env([(0,0.40),(0.14,0.64),(0.30,0.70),(0.42,0.70),(dp-0.03,0.30),(dp-0.002,0.30),(dp,1.05),(PK,1.05),(0.74,0.9),(0.82,0.72),(0.90,0.5),(0.95,0.32),(1.0,0.15)])

# bass1 (sub): build 0.82 -> peak full -> out ~93% (near the end)
b=lp(hp(loop_to(rd("bass",-17),T),32),700)
mix=b*env([(0,0.0),(0.04,0.4),(0.15,0.82),(0.42,0.82),(dp,1.0),(PK,1.0),(0.88,0.9),(0.93,0.0)])*duck*bd; del b; gc.collect()
# bass2 (different, more mid): PEAK ONLY -> released early in the outro
if has("bass2"):
    b2=lp(hp(loop_to(rd("bass2",-18),T),50),1600)
    mix+=b2*env([(0,0.0),(dp-0.005,0.0),(dp,0.6),(PK,0.6),(0.80,0.0)])*duck; del b2; gc.collect()
# peak SUB reinforcement — big HELD saturated root sub (F#1) so the bass HOLDS full
subf=46.25; sub=np.tanh(np.sin(2*np.pi*subf*np.arange(T)/SR)*1.6).astype(np.float32)  # sat -> audible+full
subduck=duck_env(depth=0.10,tau=0.07)   # only a light pump -> the bass HOLDS
mix+=sub*env([(0,0.0),(dp-0.005,0.0),(dp,1.0),(PK,1.0),(0.82,0.0)])*subduck*0.8; del sub,subduck; gc.collect()
# PUNCHY 808-style bass at the peak (offbeat 8ths, tuned F#2) — transient PUNCH + clarity
f808=92.5; hl=int(0.42*SR); th=np.arange(hl)/SR
hit=np.sin(2*np.pi*np.cumsum(f808*(1+4*np.exp(-th/0.018)))/SR)*np.exp(-th/0.22)   # pitch-drop punch
clk=int(0.004*SR); hit[:clk]+=np.random.randn(clk)*np.exp(-np.arange(clk)/(0.0018*SR))*0.5
hit=np.tanh(hit*1.9).astype(np.float32)                                          # drive -> clear on all speakers
pb=np.zeros(T,np.float32); tcur=0.5*(60.0/BPM)
while tcur<MIN*60:
    s=int(tcur*SR)
    if s<T: pb[s:min(T,s+hl)]+=hit[:max(0,min(hl,T-s))]
    tcur+=60.0/BPM
mix+=pb*env([(0,0),(dp-0.005,0),(dp,1.0),(PK,1.0),(0.80,0.0)])*0.65; del pb,hit; gc.collect()
# drone/chord: fuller post-drop, LAST to fade (back to the start)
if has("drone"):
    d=lp(hp(loop_to(rd("drone",-23),T),180),3200)
    mix+=d*env([(0,0.12),(0.12,0.42),(0.30,0.48),(0.42,0.48),(dp,0.72),(PK,0.72),(0.95,0.45),(1.0,0.2)])*duck; del d; gc.collect()
# stab: subtle build + prominent peak, out ~75%
if has("stab"):
    s=hp(loop_to(rd("stab",-26),T),300)
    mix+=s*(win_env([(0.26,0.40)],0.22)+win_env([(dp,0.75)],0.5))*duck*bd; del s; gc.collect()
# perc: light build, busy peak, out ~72%
if has("perc"):
    p=hp(loop_to(rd("perc",-25),T),260)
    mix+=p*(win_env([(0.33,0.42)],0.18)+win_env([(dp,0.72)],0.46))*duck*bd; del p; gc.collect()
# hats: light build -> full peak -> out ~82%
h=hp(loop_to(rd("hats",-21),T),600)
mix+=h*env([(0,0.0),(0.16,0.0),(0.24,0.5),(0.42,0.52),(dp-0.03,0.28),(dp-0.002,0.28),(dp,1.0),(PK,1.0),(0.78,0.6),(0.82,0.0)])*bd; del h; gc.collect()

# filter: half-open build -> full peak -> CLOSES back toward the intro in the outro
openE=env([(0,0.10),(0.22,0.6),(0.42,0.6),(dp,1.0),(PK,1.0),(0.85,0.55),(1.0,0.22)])
muff=lp(mix,500); mix=muff*(1.0-openE)+mix*openE; del muff,openE; gc.collect()

# kick: build 0.82 -> peak full -> out ~90%
k=lp(loop_to(rd("kick",-13),T),7000)
mix+=k*env([(0,0.0),(0.02,0.4),(0.08,0.82),(0.42,0.85),(dp,1.0),(PK,1.0),(0.86,0.95),(0.90,0.0)])*bd; del k; gc.collect()

# extra OFFBEAT OPEN-HAT in the peak only (explosion drive), released FIRST (~70%)
oh=int(0.14*SR); nn=np.arange(oh)/SR
click=hp((np.random.randn(oh)*np.exp(-nn/0.045)).astype(np.float32),6500)*0.5
ohat=np.zeros(T,np.float32); tcur=0.5*(60.0/BPM)
while tcur<MIN*60:
    s=int(tcur*SR)
    if s<T: ohat[s:min(T,s+oh)]+=click[:max(0,min(oh,T-s))]
    tcur+=60.0/BPM
mix+=ohat*env([(0,0),(dp-0.005,0),(dp,0.9),(PK,0.9),(0.70,0.0)]); del ohat,click; gc.collect()

# SHARP anticipation gate: near-silence the groove for the LAST BEAT, then INSTANT slam at dp
gate=np.ones(T,np.float32); beat=60.0/BPM
gs=int(dp*T-1.0*beat*SR); ge=int(dp*T)
if gs>0:
    gate[gs:ge]=0.05; gate[gs:gs+int(0.008*SR)]=np.linspace(1,0.05,int(0.008*SR))
mix*=gate; del gate; gc.collect()

# riser + impact for the drop (added AFTER the gate so they ring through the silence)
rl=int(4*BAR*SR); tt=np.arange(rl)/SR; ramp=(tt/tt[-1])
riser=hp(np.random.randn(rl).astype(np.float32),600)*(ramp**2)*0.7
riser+=np.sin(2*np.pi*(200+2600*ramp)*tt).astype(np.float32)*(ramp**3)*0.35
e0=int(dp*T); s0=e0-rl
if s0>0: mix[s0:e0]+=riser[:e0-s0]
il=int(2.4*SR); ti=np.arange(il)/SR
imp=(np.sin(2*np.pi*(75*np.exp(-ti/0.3))*ti)*np.exp(-ti/0.5)).astype(np.float32)*1.4   # bigger sub boom
imp[:int(0.03*SR)]+=np.random.randn(int(0.03*SR)).astype(np.float32)*0.7
mix[e0:e0+il]+=imp[:max(0,min(il,T-e0))]; del imp
# crash cymbal at the exact drop (the explosion signal)
cl2=int(1.9*SR); tc2=np.arange(cl2)/SR
crash=hp(np.random.randn(cl2).astype(np.float32),3000)*np.exp(-tc2/0.85)*0.55
mix[e0:e0+cl2]+=crash[:max(0,min(cl2,T-e0))]; del riser,crash; gc.collect()

# sitar/bansuri: frequent in build; MORE (both) over the peak; bansuri closes the outro
adir=a.accents
def place(clip,frac,g):
    s=int(frac*T); e=min(T,s+len(clip)); mix[s:e]+=clip[:e-s]*g
if adir:
    si=rd("sitar",dir=adir) if has("sitar",adir) else None
    ba=rd("bansuri",dir=adir) if has("bansuri",adir) else None
    for i,f in enumerate([0.09,0.13,0.17,0.21,0.25,0.29,0.33,0.37,0.41,0.45]):
        c=(ba if i%2 else si)
        if c is not None: place(c,f,0.58)
    for c,f,g in [(ba,dp+0.01,0.7),(si,dp+0.05,0.55),(ba,0.56,0.62),(si,0.60,0.5),(ba,0.64,0.6),(ba,0.86,0.55),(ba,0.95,0.5)]:
        if c is not None: place(c,f,g)
    gc.collect()

mix*=(0.6+0.4*plate); del plate; gc.collect()

# --- PEAK FULLNESS (researched hypnotic-techno craft): airy noise atmosphere that
#     "nestles into the high end" + 16th-note shaker density + peak saturation harmonics ---
ps=int(dp*T); pe=int(min(1.0,PK+0.05)*T); pl=pe-ps
if pl>0:
    nn=np.random.randn(pl).astype(np.float32)
    lfo=(0.55+0.45*np.sin(2*np.pi*0.08*np.arange(pl)/SR)).astype(np.float32)   # slow breathing
    atm=hp(nn,2600)*lfo
    fd=int(0.04*pl); atm[:fd]*=np.linspace(0,1,fd); atm[-fd:]*=np.linspace(1,0,fd)
    mix[ps:pe]+=atm*0.07; del nn,atm,lfo
    sh=int(0.05*SR); nss=np.arange(sh)/SR
    tick=hp((np.random.randn(sh)*np.exp(-nss/0.018)).astype(np.float32),8500)*0.32
    st=(60.0/BPM)/4.0; tc=dp*MIN*60.0
    while tc<(PK+0.02)*MIN*60.0:
        s=int(tc*SR)
        if ps<=s<pe: mix[s:min(pe,s+sh)]+=tick[:max(0,min(sh,pe-s))]
        tc+=st
    del tick; gc.collect()
# peak-weighted soft saturation -> harmonics fill the spectrum = fuller (not EQ boosts)
satE=win_env([(dp,PK)],1.0,ramp=0.05)
mix=mix+(np.tanh(mix*2.2)-mix)*(0.5*satE); del satE; gc.collect()

mix=mix/(np.max(np.abs(mix))+1e-6)*0.97
sf.write(a.out,mix,SR)
n=40; w=len(mix)//n
e=np.array([np.sqrt(np.mean(mix[i*w:(i+1)*w]**2)) for i in range(n)]); e/=e.max()
print(f"[gen] BURMEISTER v7: build -> drop@{int(dp*100)}% -> fuller peak (bass2+accents) -> sustain -> one-by-one outro")
print("[gen] arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in e))
print(f"[gen] DONE -> {a.out}  ({a.minutes}min @ {SR}Hz)")
