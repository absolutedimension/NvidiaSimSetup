#!/usr/bin/env python3
"""Prep mantra/humming/vocalise voices: pitch toward F#, add reverb, normalize.
Output: ~/dj_engine/burmeister/voices_prep/{mantra,humming,vocalise}.wav"""
import os, json, numpy as np, librosa, soundfile as sf
from scipy.signal import fftconvolve
SR=44100; TARGET_PC=6  # F#
MAN="/home/ubuntu/dj_engine/burmeister/voices/manifest.json"
OUT="/home/ubuntu/dj_engine/burmeister/voices_prep"; os.makedirs(OUT,exist_ok=True)
man=json.load(open(MAN))
def bucket(b): return [x for x in man if x["bucket"]==b]
def load(x): y,_=librosa.load(x["file"],sr=SR,mono=True); return y.astype(np.float32)
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
def trim_head(y,thr=0.015):
    idx=np.where(np.abs(y)>thr)[0]; return y[idx[0]:] if len(idx) else y
def reverb(y,t60=2.2,wet=0.4):
    n=int(t60*SR); ir=(np.random.randn(n).astype(np.float32))*np.exp(-np.arange(n)/(t60*SR/6.0)); ir[0]=1.0
    w=fftconvolve(y,ir)[:len(y)+n].astype(np.float32); w/=(np.max(np.abs(w))+1e-9)
    o=np.zeros(len(w),np.float32); o[:len(y)]+=y*(1-wet); o+=w*wet; return o
def norm(y,p=0.9): return (y/(np.max(np.abs(y))+1e-6)*p).astype(np.float32)
def prep(x,pitch=True):
    y=trim_head(load(x))
    if pitch: y=librosa.effects.pitch_shift(y,sr=SR,n_steps=steps(detect_root(y)))
    return norm(reverb(y))
def pick(b,keys,minlen=6.0):
    c=[x for x in bucket(b) if x["dur"]>=minlen] or bucket(b)
    for k in keys:
        cand=[x for x in c if k.lower() in x["name"].lower()]
        if cand: return max(cand,key=lambda z:z["dur"])   # longest matching
    return max(c,key=lambda z:z["dur"]) if c else None

for name,b,keys in [("mantra","mantra",["rama","gayatri","prayer","om"]),
                    ("humming","humming",["humming","hum"]),
                    ("vocalise","vocalise",["adoration","reflection","awe","aah"])]:
    x=pick(b,keys)
    if x: sf.write(f"{OUT}/{name}.wav", prep(x), SR); print(name, "<-", x["name"][:40], f'{x["dur"]}s')
print("DONE ->",OUT)
