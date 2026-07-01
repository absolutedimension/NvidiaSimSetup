#!/usr/bin/env python3
"""fs_prep_stems.py — turn picked Freesound CC0 loops into tempo+key-aligned stems for
the Goa-Gil arranger. Target: 148 BPM, key D. numpy/scipy/librosa/soundfile.
"""
import os, json, numpy as np, librosa, soundfile as sf
SR=44100; BPM=148; TARGET_PC=2  # D
BAR=4*60.0/BPM
MAN="/home/ubuntu/dj_engine/goa-gil/fs_samples/manifest.json"
OUT="/home/ubuntu/dj_engine/goa-gil/stems_fs"; os.makedirs(OUT, exist_ok=True)
man=json.load(open(MAN))

def find(bucket, sub):
    cands=[x for x in man if x["bucket"]==bucket]
    for x in cands:
        if sub.lower() in x["name"].lower(): return x
    return cands[0] if cands else None

def load(x):
    y,_=librosa.load(x["file"], sr=SR, mono=True); return y.astype(np.float32)

def detect_bpm(y, default=140):
    try:
        t=np.atleast_1d(librosa.feature.tempo(y=y, sr=SR, start_bpm=145))[0]
        t=float(t)
        while t<130: t*=2
        while t>165: t/=2
        return t
    except Exception: return default

def detect_root_pc(y):
    ch=librosa.feature.chroma_cqt(y=y, sr=SR).mean(1)
    maj=np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    mino=np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    best=(-9,0)
    for i in range(12):
        for prof in (maj,mino):
            c=np.corrcoef(np.roll(prof,i), ch)[0,1]
            if c>best[0]: best=(c,i)
    return best[1]

def to_steps(root_pc):
    return ((TARGET_PC-root_pc+6)%12)-6  # nearest shift in [-5,6]

def stretch_to_bpm(y, src_bpm):
    return librosa.effects.time_stretch(y, rate=BPM/float(src_bpm)).astype(np.float32)

def trim_bars(y, max_bars=8):
    bs=int(BAR*SR); nb=max(1, min(max_bars, round(len(y)/bs)))
    need=nb*bs
    if len(y)>=need: return y[:need]
    return np.pad(y,(0,need-len(y)))

def norm(y,p=0.97): return (y/(np.max(np.abs(y))+1e-6)*p).astype(np.float32)

def save(name,y): sf.write(f"{OUT}/{name}.wav", y, SR); print(f"  {name}: {len(y)/SR:.2f}s")

# ---- KICK: program 4-on-floor from a one-shot ----
kx=find("kick","Kick 019") or find("kick","Kick")
ko=load(kx); ko=ko[:int(0.45*SR)]
bs=int(BAR*SR); nbars=4; y=np.zeros(nbars*bs,np.float32)
for b in range(nbars*4):
    s=int(b*(60.0/BPM)*SR); seg=ko[:max(0,min(len(ko), len(y)-s))]; y[s:s+len(seg)]+=seg
save("kick", norm(y,0.95))

# ---- BASS: analog C @140 -> D @148 ----
bx=find("bass","140bpm") or find("bass","bass")
yb=load(bx); yb=stretch_to_bpm(yb,140); yb=librosa.effects.pitch_shift(yb,sr=SR,n_steps=to_steps(0))
save("bass", norm(trim_bars(yb,8),0.9))

# ---- ACID: detect bpm+key -> 148/D ----
ax=find("acid","ACID 8") or find("acid","ACID")
ya=load(ax); ab=detect_bpm(ya,142); ya=stretch_to_bpm(ya,ab)
ya=librosa.effects.pitch_shift(ya,sr=SR,n_steps=to_steps(detect_root_pc(ya)))
save("acid", norm(trim_bars(ya,8),0.7))

# ---- LEAD(->arp slot): FM 147 E maj -> 148/D ----
lx=find("lead","147 BPM") or find("lead","psy")
yl=load(lx); yl=stretch_to_bpm(yl,147)
yl=librosa.effects.pitch_shift(yl,sr=SR,n_steps=to_steps(4))  # E=4 -> D
save("arp", norm(trim_bars(yl,8),0.6))

# ---- DRONE: long ambient, no stretch, trimmed to 8 bars, shifted toward D ----
dx=find("drone","ABYSS") or find("drone","Disquiet") or find("drone","drone")
yd=load(dx)
st=int(len(yd)*0.3); yd=yd[st:st+int(BAR*8*SR)]
save("drone", norm(yd,0.55))

# ---- HATS: 145 -> 148 ----
hx=find("hats","145 hat") or find("hats","hat")
yh=load(hx); yh=stretch_to_bpm(yh,145)
save("hats", norm(trim_bars(yh,8),0.45))

# ---- CHANT: keep a clip for the invocation intro ----
cx=find("chant","Ohm of Creation") or find("chant","Monk") or find("chant","chant")
yc=load(cx); yc=yc[:int(40*SR)]
save("chant", norm(yc,0.6))

# ---- FX RISER: a transition sweep (no tempo align) ----
fx=find("fx","riser 1") or find("fx","riser") or find("fx","Rise")
if fx:
    yf=load(fx); yf=yf[:int(10*SR)]
    save("riser", norm(yf,0.7))

print("DONE ->", OUT, "@",BPM,"BPM key D")
