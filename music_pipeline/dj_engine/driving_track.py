#!/usr/bin/env python3
"""Full ~90s sample built on the DRIVING groove (rhythm1). All synth elements, F# minor,
123 BPM, with arrangement: intro build -> groove -> breakdown -> drop -> outro."""
import numpy as np, soundfile as sf, os
from scipy.signal import butter, sosfilt
SR=44100; BPM=123.0; beat=60/BPM; MIN=1.5; N=int(MIN*60*SR); TB=int(MIN*60/beat)+2
OUT="/home/ubuntu/midi_demo"; rng=np.random.default_rng(9)
def hz(m): return 440.0*2**((m-69)/12)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)
def env(pts):
    x=np.linspace(0,1,N); e=np.interp(x,[p[0] for p in pts],[p[1] for p in pts]).astype(np.float32)
    k=int(0.08*SR); c=np.cumsum(np.insert(e,0,0)); s=(c[k:]-c[:-k])/k
    return np.concatenate([np.full(N-len(s),s[0]),s]).astype(np.float32)
def duck(depth=0.22,tau=0.09):
    tt=(np.arange(N)/SR)%(60/BPM); return (1-depth*np.exp(-tt/tau)).astype(np.float32)
D=duck()
def place(one,times_beats,g=1.0):
    out=np.zeros(N,np.float32)
    for tb in times_beats:
        s=int(tb*beat*SR)
        if 0<=s<N: seg=one[:max(0,min(len(one),N-s))]*g; out[s:s+len(seg)]+=seg
    return out
# --- one-shots ---
def kick():
    hl=int(0.42*SR); t=np.arange(hl)/SR; f=48+(165-48)*np.exp(-t/0.028)
    b=np.sin(np.cumsum(2*np.pi*f/SR))*np.exp(-t/0.34); cn=int(0.006*SR)
    b[:cn]+=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.0015*SR))*0.5
    return np.tanh(b*2.3).astype(np.float32)
def sub(m=30,db=0.9):
    hl=int(db*beat*SR); t=np.arange(hl)/SR
    return np.tanh(np.sin(2*np.pi*hz(m)*np.arange(hl)/SR)*np.minimum(1,t/0.008)*np.exp(-t/(db*beat*0.8))*1.3).astype(np.float32)
def reese(m,db=0.5):
    hl=int(db*beat*1.05*SR); t=np.arange(hl)/SR; f=hz(m)
    return lp((saw(f,hl)+saw(f*1.008,hl)+saw(f*0.992,hl))/3*np.minimum(1,t/0.006)*np.exp(-t/(db*beat*0.7)),820)
def chat():
    hl=int(0.06*SR); t=np.arange(hl)/SR; return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.02),7000)
def ohat():
    hl=int(0.18*SR); t=np.arange(hl)/SR; return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.09),6000)
def stab_note(ms,dur=0.22,cut=2600):
    hl=int(dur*SR); t=np.arange(hl)/SR; ch=sum(saw(hz(m),hl) for m in ms)/len(ms)
    return (lp(ch*np.exp(-t/0.10),cut)*np.minimum(1,t/0.003)).astype(np.float32)
def pluck(m):
    hl=int(0.3*SR); t=np.arange(hl)/SR; f=hz(m)
    return lp((saw(f,hl)+saw(f*1.005,hl))/2*np.minimum(1,t/0.002)*np.exp(-t/0.11),3200)
def mk_drone():
    acc=np.zeros(N,np.float32); V=5
    for m in [42,45,49]:
        f=hz(m)
        for i in range(V): acc+=saw(f*(1+(i-V//2)*0.02/V),N)
    acc/=15; sw=0.6+0.4*np.sin(2*np.pi*0.06*np.arange(N)/SR); return hp(lp(acc,2200)*sw,60)

# --- raw layers (driving groove) ---
KICK=place(kick(),np.arange(0,TB,1))
SUB =hp(place(sub(),np.arange(0.5,TB,1)),30)
HAT =place(chat()*0.8,np.arange(0.5,TB,1))+place(chat()*0.3,np.arange(0.25,TB,0.5))+place(ohat()*0.5,[bar*4+3.75 for bar in range(TB//4)])
STAB=hp(place(stab_note([54,57,61]),[bar*4+o for bar in range(TB//4) for o in (0.75,2.5,3.75)]),180)
arp=[66,69,73,76,73,69]; leadt=np.arange(0,TB,0.25)
LEAD=hp(sum(place(pluck(arp[i%len(arp)]),[leadt[i]]) for i in range(len(leadt))),200)
riff=[(0,42),(0.5,42),(1,45),(1.5,42),(2,40),(2.5,40),(3,42),(3.5,45),(4,42),(4.5,42),(5,47),(5.5,45),(6,44),(6.5,42),(7,40),(7.5,42)]
B2=np.zeros(N,np.float32)
for rep in range(TB//8+1):
    for bt,m in riff:
        s=int((rep*8+bt)*beat*SR); one=reese(m)
        if s<N: seg=one[:max(0,min(len(one),N-s))]; B2[s:s+len(seg)]+=seg
B2=hp(B2,45); DRONE=mk_drone()

# --- arrangement envelopes (breakdown ~0.64-0.755, outro fade tail) ---
mix =KICK*env([(0,0),(0.02,0.6),(0.06,1),(0.62,1),(0.645,0),(0.755,0),(0.77,1),(0.94,1),(1,0.5)])
mix+=SUB *env([(0,0),(0.03,0.7),(0.62,0.85),(0.645,0.1),(0.77,1),(0.94,0.9),(1,0)])*D
mix+=HAT *env([(0,0),(0.05,0),(0.09,0.55),(0.62,0.6),(0.645,0.2),(0.77,0.9),(0.9,0.6),(1,0)])
mix+=DRONE*env([(0,0),(0.05,0.2),(0.10,0.5),(0.62,0.5),(0.645,0.72),(0.755,0.66),(0.95,0.4),(1,0.12)])*duck(0.10)
mix+=STAB*env([(0,0),(0.26,0),(0.30,0.4),(0.62,0.42),(0.645,0.22),(0.77,0.5),(0.88,0.4),(0.92,0)])*D
mix+=LEAD*env([(0,0),(0.43,0),(0.47,0.38),(0.62,0.4),(0.645,0.12),(0.77,0.42),(0.9,0.28),(0.94,0)])*D
mix+=B2 *env([(0,0),(0.758,0),(0.775,0.5),(0.93,0.4),(0.95,0)])*D
mix=np.tanh(mix*1.05).astype(np.float32); mix=mix/(np.max(np.abs(mix))+1e-6)*0.95
sf.write(f"{OUT}/driving_sample.wav",np.stack([mix,mix]).T,SR); print("DONE driving_sample.wav",round(N/SR,1),"s")
