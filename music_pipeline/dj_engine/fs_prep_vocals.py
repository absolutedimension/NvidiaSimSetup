#!/usr/bin/env python3
"""Prep female + deep-male wordless vocals: pick longest, pitch to F#, reverb, normalize.
Output: voices_prep/{female,male_deep}.wav"""
import os, glob, numpy as np, librosa, soundfile as sf
from scipy.signal import fftconvolve
SR=44100; TARGET_PC=6  # F#
BASE="/home/ubuntu/dj_engine/burmeister/vocals"
OUT="/home/ubuntu/dj_engine/burmeister/voices_prep"; os.makedirs(OUT,exist_ok=True)
def load(f): y,_=librosa.load(f,sr=SR,mono=True); return y.astype(np.float32)
def detect_root(y):
    ch=librosa.feature.chroma_cqt(y=y,sr=SR).mean(1)
    mino=np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    maj=np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    best=(-9,0)
    for i in range(12):
        for p in (maj,mino):
            c=np.corrcoef(np.roll(p,i),ch)[0,1]
            if c>best[0]: best=(c,i)
    return best[1]
def steps(r): return ((TARGET_PC-r+6)%12)-6
def trim(y,thr=0.015):
    idx=np.where(np.abs(y)>thr)[0]; return y[idx[0]:idx[-1]] if len(idx) else y
def reverb(y,t60=2.6,wet=0.45):
    n=int(t60*SR); ir=(np.random.randn(n).astype(np.float32))*np.exp(-np.arange(n)/(t60*SR/6.0)); ir[0]=1.0
    w=fftconvolve(y,ir)[:len(y)+n].astype(np.float32); w/=(np.max(np.abs(w))+1e-9)
    o=np.zeros(len(w),np.float32); o[:len(y)]+=y*(1-wet); o+=w*wet; return o
def norm(y,p=0.9): return (y/(np.max(np.abs(y))+1e-6)*p).astype(np.float32)
def longest(d):
    fs=glob.glob(f"{BASE}/{d}/*.mp3")
    return max(fs, key=lambda f: librosa.get_duration(path=f)) if fs else None

for name,d,extra_down in [("female","female",0),("male_deep","male_deep",-12)]:
    f=longest(d)
    if not f: print("no",name); continue
    y=trim(load(f))
    y=librosa.effects.pitch_shift(y,sr=SR,n_steps=steps(detect_root(y))+extra_down)  # male -> octave down = deep
    sf.write(f"{OUT}/{name}.wav", norm(reverb(y)), SR)
    print(name,"<-",os.path.basename(f), round(librosa.get_duration(path=f),1),"s")
print("DONE ->",OUT)
