#!/usr/bin/env python3
"""vowel_bank.py — synthesize the core Hindi VOWELS as sustained SUNG tones (formant synthesis).

Your phoneme idea, foundation stage: each Hindi vowel = a set of formants (F1,F2,F3,F4).
We build a glottal source at the note pitch (with vibrato/jitter/shimmer + spectral tilt) and
shape it through the vowel's formant resonators -> a clean sustained sung vowel at any pitch.
Fully synthetic, copyright-clean. Later stages concatenate: TTS consonant onset + bank vowel.

Runs in audio_pipeline/venv (numpy+scipy+soundfile).

Usage (demo):  python vowel_bank.py --demo --out vowels_demo.wav
"""
import argparse, numpy as np, soundfile as sf
from scipy.signal import lfilter

FS = 32000

# Hindi vowels -> formants [(F_Hz, bandwidth_Hz), ...]  (male voice, tuned by ear-target)
VOWELS = {
    "a":  [(650,80),(1100,90),(2500,120),(3400,160)],   # अ  (schwa/uh)
    "aa": [(750,90),(1150,90),(2550,120),(3400,160)],   # आ  (open ah)
    "i":  [(320,60),(2200,100),(2900,140),(3600,180)],  # इ/ई (ee)
    "u":  [(350,60),(820,90),(2400,120),(3400,160)],    # उ/ऊ (oo)
    "e":  [(450,70),(1900,100),(2550,120),(3400,160)],  # ए  (ay)
    "ai": [(620,90),(1700,100),(2500,120),(3400,160)],  # ऐ  (eh)
    "o":  [(450,70),(900,90),(2400,120),(3400,160)],    # ओ  (oh)
    "au": [(600,90),(950,90),(2450,120),(3400,160)],    # औ  (aw)
}

def glottal_contour(f0c, OQ=0.62):
    """Rosenberg glottal-flow pulses over a per-sample f0 contour -> natural rolloff, no buzz."""
    n = len(f0c); flow = np.zeros(n); i = 0
    while i < n:
        f = f0c[min(i, n-1)]; T = max(int(FS/f), 10)
        Tp = max(int(0.72*OQ*T), 2); Tn = max(int(0.28*OQ*T), 2)  # open rise, closing fall
        pulse = np.zeros(T)
        r = np.arange(Tp); pulse[:Tp] = 0.5*(1 - np.cos(np.pi*r/Tp))     # smooth open
        if Tp+Tn <= T:
            c = np.arange(Tn); pulse[Tp:Tp+Tn] = np.cos(np.pi*c/(2*Tn))  # smooth close
        end = min(i+T, n)
        flow[i:end] += pulse[:end-i]*(1.0 + 0.03*np.random.randn())      # shimmer
        i += T
    src = np.gradient(flow) + 0.0006*np.random.randn(n)  # excitation + minimal breath
    return src

def glottal_source(f0, dur, vib_hz=5.4, vib_depth=0.012):
    n = int(dur*FS); t = np.arange(n)/FS
    venv = np.clip((t-0.15)/0.4, 0, 1)
    f0c = f0*(1.0 + vib_depth*venv*np.sin(2*np.pi*vib_hz*t))
    return glottal_contour(f0c), t

def formant(x, F, B):
    r = np.exp(-np.pi*B/FS); th = 2*np.pi*F/FS
    return lfilter([1.0-r], [1.0, -2*r*np.cos(th), r*r], x)

def synth_vowel(vowel, f0, dur):
    src, t = glottal_source(f0, dur)
    y = src.copy()
    for (F,B) in VOWELS[vowel]:                            # cascade formant resonators
        y = formant(y, F, B)
    # tame residual high-end buzz: gentle lowpass (~one-pole @ ~5 kHz)
    rlp = np.exp(-2*np.pi*5000/FS)
    y = lfilter([1-rlp], [1, -rlp], y)
    # amplitude envelope: soft attack, sustain, soft release
    n = len(y); a=int(0.03*FS); rl=int(0.08*FS)
    env = np.ones(n)
    env[:a] = np.linspace(0,1,a); env[-rl:] = np.linspace(1,0,rl)
    y = y*env
    return y/(np.max(np.abs(y))+1e-9)*0.9

def midi2hz(m): return 440.0*2**((m-69)/12.0)

def sing_melody(vowel, midis, durs, glide=0.09, vib_hz=5.4, vib_depth=0.014):
    """continuous LEGATO phrase on one vowel: gliding f0 between notes + per-note swell."""
    segs=[]; env_parts=[]
    for i,(m,d) in enumerate(zip(midis,durs)):
        nn=int(d*FS); seg=np.full(nn, midi2hz(m))
        gl=min(int(glide*FS), nn//2)
        if i>0 and gl>1: seg[:gl]=np.linspace(midi2hz(midis[i-1]), midi2hz(m), gl)  # portamento
        segs.append(seg)
        e=np.ones(nn); at=int(0.06*nn); rl=int(0.10*nn)
        e[:at]=np.linspace(0.6,1,at); e[-rl:]=np.linspace(1,0.7,rl)                  # gentle swell
        env_parts.append(e)
    f0c=np.concatenate(segs); n=len(f0c); t=np.arange(n)/FS
    venv=np.clip((t-0.12)/0.4,0,1)
    f0c=f0c*(1.0+vib_depth*venv*np.sin(2*np.pi*vib_hz*t))
    y=glottal_contour(f0c)
    for (F,B) in VOWELS[vowel]: y=formant(y,F,B)
    rlp=np.exp(-2*np.pi*5000/FS); y=lfilter([1-rlp],[1,-rlp],y)
    y=y*np.concatenate(env_parts)
    return y/(np.max(np.abs(y))+1e-9)*0.9

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--vowel", default=None)
    ap.add_argument("--midi", type=int, default=48)
    ap.add_argument("--dur", type=float, default=1.5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    np.random.seed(3)
    if a.demo:
        pieces=[]
        # 1) each vowel held on C3
        for v in VOWELS:
            pieces.append(synth_vowel(v, midi2hz(48), 1.1))
            pieces.append(np.zeros(int(0.15*FS)))
        pieces.append(np.zeros(int(0.4*FS)))
        # 2) LEGATO vocalise on 'aa' — gliding phrase, varied note lengths (musical, not mechanical)
        mel =[45,48,50,52,50,48,47,45,43,45]
        durs=[0.55,0.4,0.5,0.75,0.45,0.5,0.4,0.6,0.4,1.0]
        pieces.append(sing_melody("aa", mel, durs))
        out=np.concatenate(pieces)
    else:
        out=synth_vowel(a.vowel, midi2hz(a.midi), a.dur)
    sf.write(a.out, (out/(np.max(np.abs(out))+1e-9)*0.92).astype(np.float32), FS)
    print(f"[vowel_bank] wrote {a.out}  {len(out)/FS:.1f}s")

if __name__ == "__main__":
    main()
