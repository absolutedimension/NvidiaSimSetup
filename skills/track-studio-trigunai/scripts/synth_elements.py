#!/usr/bin/env python3
"""Generate NEW basic elements from scratch (numpy DSP synthesis) — proof that we can
DESIGN kick/bass/drone/stab instead of sampling them. 6s previews at 123 BPM, F# minor."""
import numpy as np, soundfile as sf, os
from scipy.signal import butter, sosfilt
SR=44100; BPM=123.0; beat=60/BPM; DUR=6.0; N=int(DUR*SR)
OUT="/home/ubuntu/sb_samples"; os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def sq(f,n,pw=0.5):
    ph=(np.cumsum(np.full(n,f/SR)))%1; return np.where(ph<pw,1.0,-1.0).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)
def norm(x,p=0.9): return (x/(np.max(np.abs(x))+1e-9)*p).astype(np.float32)
def place(one,times,hl):
    out=np.zeros(N,np.float32)
    for t in times:
        s=int(t*SR)
        if s<N: out[s:min(N,s+hl)]+=one[:max(0,min(hl,N-s))]
    return out

def kick(f0=165,f1=48,pdec=0.028,adec=0.34,drive=2.2,click=0.5):
    hl=int(0.42*SR); t=np.arange(hl)/SR
    f=f1+(f0-f1)*np.exp(-t/pdec); ph=np.cumsum(2*np.pi*f/SR)
    body=np.sin(ph)*np.exp(-t/adec)
    cn=int(0.006*SR); cl=np.zeros(hl); cl[:cn]=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.0015*SR))*click
    one=np.tanh((body+cl)*drive).astype(np.float32)
    return norm(place(one,np.arange(0,DUR,beat),hl))

def bass(note=92.5,mode='sub',cutoff=420):
    hl=int(beat*0.92*SR); t=np.arange(hl)/SR
    if mode=='sub': osc=np.sin(2*np.pi*note*np.arange(hl)/SR).astype(np.float32)
    else: osc=(saw(note,hl)+saw(note*1.007,hl)+saw(note*0.993,hl))/3
    env=np.minimum(1,t/0.01)*np.exp(-t/(beat*0.75))
    one=lp(osc*env,cutoff)
    return norm(hp(place(one,np.arange(beat*0.5,DUR,beat),hl),30),0.85)

def drone(root=92.5,voices=7,detune=0.02,cutoff=2200):
    acc=np.zeros(N,np.float32)
    for i in range(voices): acc+=saw(root*(1+(i-voices//2)*detune/voices),N)
    acc=acc/voices + saw(root*1.5,N)*0.4 + saw(root*2,N)*0.3
    swell=0.6+0.4*np.sin(2*np.pi*0.13*np.arange(N)/SR)
    return norm(hp(lp(acc,cutoff)*swell,60),0.8)

def stab(root=185.0,cutoff=2600):
    hl=int(0.28*SR); t=np.arange(hl)/SR
    freqs=[root,root*2**(3/12),root*2**(7/12),root*2]   # F# minor triad+oct
    ch=sum(saw(f,hl) for f in freqs)/len(freqs)
    one=lp(ch*np.exp(-t/0.11),cutoff)*np.minimum(1,t/0.003)
    return norm(hp(place(one,np.arange(0.75,DUR,beat),hl),150),0.72)

def hats(cutoff=8000):
    hl=int(0.05*SR); t=np.arange(hl)/SR
    one=hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.02),cutoff)
    return norm(place(one,np.arange(beat*0.5,DUR,beat),hl),0.5)

elements={
 "synth_kick_punchy":kick(f0=185,adec=0.26,drive=2.6),
 "synth_kick_deep":  kick(f0=140,f1=44,adec=0.46,drive=1.8,click=0.3),
 "synth_bass_sub":   bass(mode='sub'),
 "synth_bass_reese": bass(mode='reese',cutoff=760),
 "synth_drone_warm": drone(cutoff=1700),
 "synth_drone_bright":drone(cutoff=3200,voices=9),
 "synth_stab":       stab(),
 "synth_hats":       hats(),
}
for name,y in elements.items():
    sf.write(f"{OUT}/{name}.wav",y,SR); print("  ",name)
print("done", len(elements))
