#!/usr/bin/env python3
"""fs_prep_accents.py — prep sitar + bansuri melodic accents: pitch to F#, add elegant
reverb tail, trim, normalize. Output: burmeister/accents_prep/{sitar,bansuri}.wav
"""
import os, json, numpy as np, librosa, soundfile as sf
from scipy.signal import fftconvolve
SR=44100; TARGET_PC=6  # F#
MAN="/home/ubuntu/dj_engine/burmeister/accents/manifest.json"
OUT="/home/ubuntu/dj_engine/burmeister/accents_prep"; os.makedirs(OUT,exist_ok=True)
man=json.load(open(MAN))
def bucket(b): return [x for x in man if x["bucket"]==b]
def load(x):
    y,_=librosa.load(x["file"],sr=SR,mono=True); return y.astype(np.float32)
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
def trim_head(y,thr=0.02):
    idx=np.where(np.abs(y)>thr)[0]; return y[idx[0]:] if len(idx) else y
def reverb(y,t60=2.0,wet=0.38):
    n=int(t60*SR); ir=(np.random.randn(n).astype(np.float32))*np.exp(-np.arange(n)/(t60*SR/6.0)); ir[0]=1.0
    wetsig=fftconvolve(y,ir)[:len(y)+n].astype(np.float32); wetsig/= (np.max(np.abs(wetsig))+1e-9)
    out=np.zeros(len(wetsig),np.float32); out[:len(y)]+=y*(1-wet); out+=wetsig*wet
    return out
def norm(y,p=0.9): return (y/(np.max(np.abs(y))+1e-6)*p).astype(np.float32)
def prep(x):
    y=trim_head(load(x)); y=librosa.effects.pitch_shift(y,sr=SR,n_steps=steps(detect_root(y)))
    return norm(reverb(y))

# BANSURI: prefer a melodic raga phrase
bc=bucket("bansuri")
if bc:
    pref=[x for x in bc if any(k in x["name"].lower() for k in ["rag","set 3","set 5","set 6"])] or bc
    sf.write(f"{OUT}/bansuri.wav", prep(pref[0]), SR); print("bansuri:", pref[0]["name"])
# SITAR: prefer the melodic one
sc=bucket("sitar")
if sc:
    pref=[x for x in sc if "melody" in x["name"].lower()] or sc
    sf.write(f"{OUT}/sitar.wav", prep(pref[0]), SR); print("sitar:", pref[0]["name"])
print("DONE ->",OUT)
