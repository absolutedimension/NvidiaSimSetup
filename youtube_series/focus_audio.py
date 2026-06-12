#!/usr/bin/env python3
"""Generate a research-grounded FOCUS background bed for lectures.
Layers:
  1. Isochronic pulse — a warm carrier amplitude-modulated at BEAT Hz (default 12 Hz,
     alpha/beta border = calm-alert intake). Speaker-safe (no headphones needed).
     Basis: amplitude-modulation in 12-20 Hz boosts sustained attention (Northeastern 2024).
  2. Ambient pad — a soft detuned chord with a slow swell, so the bed is musical not clinical.
  3. Pink noise — very low, band-limited; masks speech-range distractions (gentlest masker).
Output: stereo WAV, slow fade in/out, normalized low so it sits UNDER narration.
Usage: python3 focus_audio.py --dur 345 --beat 12 --out focus_bed.wav
"""
import numpy as np, argparse, wave, struct
SR=44100

def tone(freq, n, detune=0.0):
    t=np.arange(n)/SR
    return np.sin(2*np.pi*freq*t) + (0.5*np.sin(2*np.pi*(freq+detune)*t) if detune else 0)

def pink(n):
    white=np.random.randn(n)
    X=np.fft.rfft(white); f=np.fft.rfftfreq(n); f[0]=f[1]
    X=X/np.sqrt(f)                       # 1/f -> pink
    # band-limit: roll off above ~3.5 kHz so it doesn't fight consonants
    X[f>3500]*=0.25
    out=np.fft.irfft(X,n); return out/(np.max(np.abs(out))+1e-9)

def fade(sig, secs=4.0):
    n=int(secs*SR); e=np.ones(len(sig))
    e[:n]=np.linspace(0,1,n)**2; e[-n:]=np.linspace(1,0,n)**2
    return sig*e

ap=argparse.ArgumentParser()
ap.add_argument("--dur",type=float,default=345)
ap.add_argument("--beat",type=float,default=12.0)   # Hz (alpha/beta border)
ap.add_argument("--root",type=float,default=146.83) # D3 — warm, below vocal formants
ap.add_argument("--out",default="focus_bed.wav")
a=ap.parse_args()
n=int(a.dur*SR); t=np.arange(n)/SR

# 1) isochronic carrier (root + soft fifth) gated at beat freq with a smooth pulse
carrier = 0.6*tone(a.root,n) + 0.4*tone(a.root*1.5,n)        # root + perfect fifth
gate = (0.5+0.5*np.sin(2*np.pi*a.beat*t - np.pi/2))          # 0..1 smooth
gate = gate**1.6                                            # crisper pulse, still soft
iso = carrier*gate

# 2) ambient pad — detuned chord (D-A-D) with slow swell LFO
pad = (0.5*tone(a.root,n,detune=0.4) + 0.35*tone(a.root*1.5,n,detune=0.5)
       + 0.3*tone(a.root*2,n,detune=0.6))
swell = 0.75+0.25*np.sin(2*np.pi*0.05*t)                    # ~20s breathing
pad = pad*swell

# 3) pink noise bed (low, band-limited)
pn = pink(n)

mix = 0.16*iso + 0.42*pad + 0.05*pn
mix = mix/(np.max(np.abs(mix))+1e-9)*0.6                    # headroom; further attenuated at video mix
mix = fade(mix, 4.0)

# subtle stereo width: tiny inter-channel delay on the pad side
L = mix.copy()
R = np.concatenate([np.zeros(28), mix[:-28]])               # ~0.6ms haas widening
R = R/(np.max(np.abs(R))+1e-9)*0.6
stereo=np.stack([L,R],axis=1)
pcm=(np.clip(stereo,-1,1)*32767).astype(np.int16)

with wave.open(a.out,"w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"✅ {a.out} — {a.dur:.0f}s, beat {a.beat} Hz, root {a.root:.1f} Hz")
