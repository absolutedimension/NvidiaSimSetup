#!/usr/bin/env python3
"""complete_song.py — stitch sung lines + lay a key-matched SOFT BED (drone + harmonium + tabla).

Detects the singer's key from the vocal and builds a tanpura-style FIFTH-drone (no third ->
never clashes with the melody) + soft harmonium (root+fifth) + light tabla. Works with the
natural (untuned) voice. Copyright-clean bed; the vocal is the user's own.

Runs in audio_pipeline/venv. Usage:
  audio_pipeline/venv/bin/python complete_song.py --vocals l1.wav l2.wav l3.wav l4.wav --out song.wav
  (or --vocal one.wav for a single pre-stitched vocal)
"""
import argparse, subprocess, os, numpy as np, soundfile as sf, librosa
from scipy.signal import lfilter

FS = 32000
def hzof(m): return 440.0*2**((m-69)/12.0)
def lowpass(x, fc):
    r=np.exp(-2*np.pi*fc/FS); return lfilter([1-r],[1,-r],x)

def load32(p):
    y,sr=sf.read(p)
    if y.ndim>1: y=y.mean(1)
    if sr!=FS: y=librosa.resample(y.astype(float),orig_sr=sr,target_sr=FS)
    return y.astype(float)

def detect_root(v):
    ch=librosa.feature.chroma_cqt(y=v.astype(float),sr=FS).mean(1)
    pc=int(np.argmax(ch))            # 0=C ... 11=B
    root=36+pc                       # C2..B2
    return root

def reed(hz, dur):
    n=int(dur*FS); t=np.arange(n)/FS; y=np.zeros(n)
    for h,amp in [(1,1),(2,0.5),(3,0.3),(4,0.18),(5,0.11)]:
        y+=amp*np.sin(2*np.pi*hz*h*t)
    y+=0.3*np.sin(2*np.pi*hz*1.004*t)
    y*=(1.0+0.05*np.sin(2*np.pi*5.0*t))
    a=int(0.12*FS); r=int(0.25*FS); e=np.ones(n)
    e[:a]=np.linspace(0,1,a); e[-r:]=np.linspace(1,0,r)
    return y*e/(np.max(np.abs(y))+1e-9)

def drone(root, dur):
    n=int(dur*FS); t=np.arange(n)/FS; y=np.zeros(n)
    for hz,amp in [(hzof(root-12),0.6),(hzof(root),0.5),(hzof(root+7),0.4),(hzof(root+12),0.25)]:
        for h,a in [(1,1),(2,0.35),(3,0.18)]:
            y+=amp*a*np.sin(2*np.pi*hz*h*t+np.random.rand())
    y*=(1.0+0.03*np.sin(2*np.pi*0.2*t))
    return y/(np.max(np.abs(y))+1e-9)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vocals",nargs="*",default=[]); ap.add_argument("--vocal",default=None)
    ap.add_argument("--gap",type=float,default=0.45); ap.add_argument("--out",required=True)
    ap.add_argument("--work",default="/home/ubuntu/singer_rl/_song")
    a=ap.parse_args(); os.makedirs(a.work,exist_ok=True); np.random.seed(5)

    # stitch vocal(s)
    files=a.vocals if a.vocals else ([a.vocal] if a.vocal else [])
    parts=[]
    for f in files:
        parts.append(load32(f)); parts.append(np.zeros(int(a.gap*FS)))
    v=np.concatenate(parts) if parts else np.zeros(FS)
    v=v/(np.max(np.abs(v))+1e-9)*0.9
    D=len(v)/FS
    root=detect_root(v)
    print(f"[song] {len(files)} lines, {D:.1f}s, detected key root=midi {root} ({librosa.midi_to_note(root)})")

    # fifth-drone (no third -> safe) + soft harmonium (root+fifth) + light tabla
    dr = lowpass(drone(root, D)[:len(v)], 1200)
    harm=[]
    while sum(len(x) for x in harm) < len(v):
        harm.append((reed(hzof(root),6.0)+reed(hzof(root+7),6.0))/2)
    harm = lowpass(np.concatenate(harm)[:len(v)], 1600)
    perc_wav=os.path.join(a.work,"perc.wav")
    subprocess.run(f'~/audio_pipeline/venv/bin/python ~/singer_rl/synth_percussion.py '
                   f'--bpm 66 --duration {D:.1f} --out "{perc_wav}"', shell=True, check=True,
                   capture_output=True, text=True)
    perc=load32(perc_wav); perc=perc[:len(v)] if len(perc)>=len(v) else np.pad(perc,(0,len(v)-len(perc)))
    perc=lowpass(perc,3500)

    mix = 1.0*v + 0.10*harm + 0.11*dr + 0.13*perc      # bed well under the voice
    mix = mix/(np.max(np.abs(mix))+1e-9)*0.95
    tmp=os.path.join(a.work,"mix.wav"); sf.write(tmp, mix.astype(np.float32), FS)
    subprocess.run(f'ffmpeg -y -i "{tmp}" -af '
                   f'"highpass=f=45,equalizer=f=3500:t=q:w=1.8:g=2,'
                   f'acompressor=threshold=-16dB:ratio=2.0:attack=8:release=200:makeup=1.5,'
                   f'loudnorm=I=-14:TP=-1.5:LRA=9" -b:a 192k "{a.out}"',
                   shell=True, check=True, capture_output=True, text=True)
    print(f"[song] wrote {a.out}  {D:.1f}s")

if __name__=="__main__": main()
