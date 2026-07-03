#!/usr/bin/env python3
"""Generate a COMPLETE unique stem set from scratch (DSP synthesis) — kick/bass/bass2/
hats/perc/drone/stab — 8-bar loops, F# minor, 123 BPM. Drop-in replacement for the
sampled stems_fs/ so a render uses a 100%-unique, copyright-clean palette."""
import numpy as np, soundfile as sf, os
from scipy.signal import butter, sosfilt
SR=44100; BPM=123.0; beat=60/BPM; BAR=4*beat; BARS=8; N=int(BARS*BAR*SR)
OUT="/home/ubuntu/stems_synth"; os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(11)
def hz(m): return 440.0*2**((m-69)/12)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)
def norm(x,p=0.9): return (x/(np.max(np.abs(x))+1e-9)*p).astype(np.float32)
def place(one,times):
    out=np.zeros(N,np.float32)
    for t in times:
        s=int(t*SR)
        if 0<=s<N:
            seg=one[:max(0,min(len(one),N-s))]; out[s:s+len(seg)]+=seg
    return out
def noise(hl,dec,fc):
    t=np.arange(hl)/SR; return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/dec),fc)

# --- one-shots ---
def mk_kick():
    hl=int(0.42*SR); t=np.arange(hl)/SR
    f=48+(165-48)*np.exp(-t/0.028); body=np.sin(np.cumsum(2*np.pi*f/SR))*np.exp(-t/0.34)
    cn=int(0.006*SR); cl=np.zeros(hl); cl[:cn]=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.0015*SR))*0.5
    return np.tanh((body+cl)*2.3).astype(np.float32)
def sub_note(m,db=0.9):
    hl=int(db*beat*SR); t=np.arange(hl)/SR
    o=np.sin(2*np.pi*hz(m)*np.arange(hl)/SR)*np.minimum(1,t/0.008)*np.exp(-t/(db*beat*0.8))
    return np.tanh(o*1.3).astype(np.float32)
def reese(m,db=0.5,cut=820):
    hl=int(db*beat*1.05*SR); t=np.arange(hl)/SR; f=hz(m)
    o=(saw(f,hl)+saw(f*1.008,hl)+saw(f*0.992,hl))/3*np.minimum(1,t/0.006)*np.exp(-t/(db*beat*0.7))
    return lp(o,cut)
def stab_note(ms,dur=0.22,cut=2600):
    hl=int(dur*SR); t=np.arange(hl)/SR
    ch=sum(saw(hz(m),hl) for m in ms)/len(ms)
    return (lp(ch*np.exp(-t/0.10),cut)*np.minimum(1,t/0.003)).astype(np.float32)
def mk_drone():
    acc=np.zeros(N,np.float32); V=5
    for m in [42,45,49]:
        f=hz(m)
        for i in range(V): acc+=saw(f*(1+(i-V//2)*0.02/V),N)
    acc/=(3*V); swell=0.6+0.4*np.sin(2*np.pi*0.06*np.arange(N)/SR)
    return norm(hp(lp(acc,2200)*swell,60),0.8)

# --- assemble ---
KICK=norm(place(mk_kick(), np.arange(0,BARS*4)*beat))
BASS=norm(hp(place(sub_note(30), np.arange(0.5,BARS*4,1)*beat),30),0.85)   # sub, offbeat root F#1
riff=[(0,42),(0.5,42),(1,45),(1.5,42),(2,40),(2.5,40),(3,42),(3.5,45),
      (4,42),(4.5,42),(5,47),(5.5,45),(6,44),(6.5,42),(7,40),(7.5,42)]     # 2-bar F# minor mid riff
B2=np.zeros(N,np.float32)
for rep in range(BARS//2):
    for bt,m in riff:
        s=int((rep*8+bt)*beat*SR); one=reese(m)
        if s<N: seg=one[:max(0,min(len(one),N-s))]; B2[s:s+len(seg)]+=seg
BASS2=norm(hp(B2,45),0.8)
ch=noise(int(0.06*SR),0.02,7000)
HATS=place(ch*0.8,np.arange(0.5,BARS*4,1)*beat)+place(ch*0.3,np.arange(0.25,BARS*4,0.5)*beat)\
     +place(noise(int(0.18*SR),0.09,6000)*0.5,np.array([b*4+3.75 for b in range(BARS)])*beat)
HATS=norm(HATS,0.6)
PERC=place(noise(int(0.04*SR),0.015,9000)*0.4,np.arange(0,BARS*4,0.5)*beat)\
     +place(noise(int(0.18*SR),0.09,1200)*0.7,np.array([b*4+1 for b in range(BARS)]+[b*4+3 for b in range(BARS)])*beat)
PERC=norm(hp(PERC,300),0.55)
DRONE=mk_drone()
STAB=norm(hp(place(stab_note([54,57,61]),
     np.array([b*4+o for b in range(BARS) for o in [0.75,2.5,3.75]])*beat),180),0.7)

for n,y in {"kick":KICK,"bass":BASS,"bass2":BASS2,"hats":HATS,"perc":PERC,"drone":DRONE,"stab":STAB}.items():
    sf.write(f"{OUT}/{n}.wav",y,SR); print("  ",n,round(len(y)/SR,1),"s")
print("unique stem set ->",OUT)
