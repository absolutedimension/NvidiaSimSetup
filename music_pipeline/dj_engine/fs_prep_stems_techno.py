#!/usr/bin/env python3
"""fs_prep_stems_techno.py — turn CC0 techno loops into tempo+key-aligned stems for the
Burmeister arranger. Target: 123 BPM, key F#. Auto-picks the best loop per bucket.
"""
import os, json, numpy as np, librosa, soundfile as sf
SR=44100; BPM=123; TARGET_PC=6  # F#
BAR=4*60.0/BPM
MAN="/home/ubuntu/dj_engine/burmeister/fs_samples/manifest.json"
OUT="/home/ubuntu/dj_engine/burmeister/stems_fs"; os.makedirs(OUT, exist_ok=True)
man=json.load(open(MAN))

def bucket(b): return [x for x in man if x["bucket"]==b]
def load(x):
    y,_=librosa.load(x["file"], sr=SR, mono=True); return y.astype(np.float32)
def detect_bpm(y, d=123):
    try:
        t=float(np.atleast_1d(librosa.feature.tempo(y=y,sr=SR,start_bpm=BPM))[0])
        while t<108: t*=2
        while t>138: t/=2
        return t
    except Exception: return d
def detect_root_pc(y):
    ch=librosa.feature.chroma_cqt(y=y,sr=SR).mean(1)
    maj=np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    mino=np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    best=(-9,0)
    for i in range(12):
        for p in (maj,mino):
            c=np.corrcoef(np.roll(p,i),ch)[0,1]
            if c>best[0]: best=(c,i)
    return best[1]
def steps(root_pc): return ((TARGET_PC-root_pc+6)%12)-6
def stretch(y,src): return librosa.effects.time_stretch(y, rate=BPM/float(src)).astype(np.float32)
def trim_bars(y,mx=8):
    bs=int(BAR*SR); nb=max(1,min(mx,round(len(y)/bs))); need=nb*bs
    return y[:need] if len(y)>=need else np.pad(y,(0,need-len(y)))
def norm(y,p=0.97): return (y/(np.max(np.abs(y))+1e-6)*p).astype(np.float32)
def save(n,y): sf.write(f"{OUT}/{n}.wav",y,SR); print(f"  {n}: {len(y)/SR:.2f}s")

def pick_loop(b):
    c=bucket(b)
    if not c: return None
    tagged=[x for x in c if x["bpm"]]
    return (tagged or c)[0]
def align_tonal(x, pitch=True):
    y=load(x); src=x["bpm"] or detect_bpm(y); y=stretch(y,src)
    if pitch: y=librosa.effects.pitch_shift(y,sr=SR,n_steps=steps(detect_root_pc(y)))
    return trim_bars(y,8)

# KICK: shortest = one-shot -> 4-on-floor
kc=bucket("kick")
if kc:
    kx=min(kc,key=lambda z:z["dur"]); ko=load(kx)[:int(0.55*SR)]
    bs=int(BAR*SR); y=np.zeros(4*bs,np.float32)
    for bt in range(4*4):
        s=int(bt*(60.0/BPM)*SR); seg=ko[:max(0,min(len(ko),len(y)-s))]; y[s:s+len(seg)]+=seg
    save("kick", norm(y,0.95))
# BASS (avoid dubstep/jazz/bounce -> want a clean rolling sub)
bc=bucket("bass")
if bc:
    bad=["dubstep","jazz","bounce","wobble","future","happy"]
    bg=[x for x in bc if not any(w in x["name"].lower() for w in bad)]
    bx=(bg or bc)[0]
    save("bass", norm(align_tonal(bx),0.9))
    # BASS2: a DIFFERENT bass for the peak (adds variety/fullness)
    others=[x for x in bg if x["file"]!=bx["file"]] or [x for x in bc if x["file"]!=bx["file"]]
    if others:
        save("bass2", norm(align_tonal(others[0]),0.85))
# DRONE: longest sustained -> pitch to F#, trim
dc=bucket("drone")
if dc:
    dx=max(dc,key=lambda z:z["dur"]); yd=load(dx)
    yd=librosa.effects.pitch_shift(yd,sr=SR,n_steps=steps(detect_root_pc(yd)))
    st=int(len(yd)*0.2); yd=yd[st:st+int(BAR*8*SR)]
    save("drone", norm(yd,0.6))
# STAB (modular bleeps)
sx=pick_loop("stab"); save("stab", norm(align_tonal(sx),0.5)) if sx else None
# HATS
hx=pick_loop("hats"); save("hats", norm(align_tonal(hx,pitch=False),0.5)) if hx else None
# PERC
px=pick_loop("perc"); save("perc", norm(align_tonal(px,pitch=False),0.5)) if px else None
print("DONE ->",OUT,"@",BPM,"BPM key F#")
