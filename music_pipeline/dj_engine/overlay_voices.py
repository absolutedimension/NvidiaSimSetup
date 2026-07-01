#!/usr/bin/env python3
"""Blend mantra + Indian female 'aaa' + deep male 'aaa' onto a base track. Voice EVENTS
rotate through the three (varied mix), sidechain-ducked under the kick + softened + low
so they COMPLEMENT the groove. usage: overlay_voices.py BASE.mp3 VDIR OUT.wav [--bpm 123]"""
import sys, math, numpy as np, librosa, soundfile as sf
from scipy.signal import butter, sosfilt
SR=44100
BASE, VDIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BPM = float(sys.argv[sys.argv.index("--bpm")+1]) if "--bpm" in sys.argv else 123.0
def hp(x,f): return sosfilt(butter(2,f/(SR/2),btype="high",output="sos"),x).astype(np.float32)
def lp(x,f): return sosfilt(butter(2,f/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def loadv(n):
    y,_=librosa.load(f"{VDIR}/{n}.wav",sr=SR,mono=True); return y.astype(np.float32)
def duck(n,depth,tau=0.12):
    beat=60.0/BPM; tt=(np.arange(n)/SR)%beat; return (1.0-depth*np.exp(-tt/tau)).astype(np.float32)
def chunk(y,length_s,i):
    L=int(length_s*SR)
    if len(y)<=L: seg=np.pad(y,(0,L-len(y)))
    else:
        st=(i*int(5.3*SR))%(len(y)-L); seg=y[st:st+L].copy()
    fd=int(0.35*SR); seg[:fd]*=np.linspace(0,1,fd); seg[-fd:]*=np.linspace(1,0,fd)
    return seg

base,_=librosa.load(BASE,sr=SR,mono=True); base=base.astype(np.float32); T=len(base)
mantra=lp(hp(loadv("mantra"),200),3200)      # devotional phrase, warm
female =lp(hp(loadv("female"),180),4200)     # ethereal female 'aaa'
male   =lp(hp(loadv("male_deep"),55),2400)   # deep male 'aaa' (keep the lows)

# --- rotating voice events: female is the frequent 'aaa', deep-male accents, mantra sometimes ---
layer=np.zeros(T,np.float32)
pattern=["female","mantra","male_deep","female","male_deep","mantra","female","male_deep"]
t=int(3*SR); i=0
while t < T-SR:
    kind=pattern[i%len(pattern)]
    if   kind=="mantra":    seg=mantra
    elif kind=="female":    seg=chunk(female,11,i)
    else:                   seg=chunk(male,12,i)
    n=min(len(seg),T-t); layer[t:t+n]+=seg[:n]
    t += int((16 + (i%3)*3)*SR); i+=1
out = base + layer * duck(T,0.6) * 0.20

# subtle continuous DEEP-MALE drone bed for warmth, heavily ducked
mb=np.tile(male,math.ceil(T/len(male)))[:T]*(0.7+0.3*np.sin(2*np.pi*np.arange(T)/SR*0.025)).astype(np.float32)
out += mb * duck(T,0.5) * 0.07

out = out/(np.max(np.abs(out))+1e-6)*0.97
sf.write(OUT, out, SR)
print("DONE ->", OUT, round(T/SR,1),"s (bpm",BPM,")")
