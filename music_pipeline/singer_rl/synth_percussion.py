#!/usr/bin/env python3
"""synth_percussion.py — synthesize a clean tabla/dholak KEHERWA groove (no samples).

Classic 8-matra Bollywood-ballad taal. Strokes are DSP-synthesized:
  dholak bass (dhaa)  = pitch-dropping damped low sine + body noise
  dholak slap / tabla na/tin = ringing mid sine + click noise (short)
  tabla ge (bass bend) = down-swept damped sine
Loops to a target duration, light velocity/timing humanization. Copyright-clean.

Usage:
  python synth_percussion.py --bpm 108 --duration 120 --out perc.wav [--fills]
"""
import argparse, numpy as np, soundfile as sf

SR = 44100

def _env(n, attack, decay):
    a = int(attack*SR); d = n-a
    e = np.ones(n)
    if a>0: e[:a] = np.linspace(0,1,a)
    e[a:] = np.exp(-np.linspace(0,1,max(d,1))*decay)
    return e

def stroke(kind, vel=1.0):
    if kind == "dha":      # dholak bass, pitch drop
        n = int(0.30*SR); t = np.arange(n)/SR
        f = np.linspace(115, 68, n)
        y = np.sin(2*np.pi*np.cumsum(f)/SR) * _env(n,0.002,5.5)
        y += 0.25*np.random.randn(n)*_env(n,0.001,22)   # body thud
    elif kind == "ge":     # tabla bass, deeper bend
        n = int(0.38*SR); t = np.arange(n)/SR
        f = np.linspace(150, 74, n)
        y = np.sin(2*np.pi*np.cumsum(f)/SR) * _env(n,0.002,4.0)
        y += 0.12*np.random.randn(n)*_env(n,0.001,26)
    elif kind == "na":     # tabla treble, ringing rim
        n = int(0.22*SR)
        y = np.sin(2*np.pi*430*np.arange(n)/SR) * _env(n,0.001,9)
        y += 0.5*np.sin(2*np.pi*860*np.arange(n)/SR) * _env(n,0.001,16)
        y += 0.4*np.random.randn(n)*_env(n,0.0005,60)    # click
    elif kind == "tin":    # higher ping
        n = int(0.20*SR)
        y = np.sin(2*np.pi*560*np.arange(n)/SR) * _env(n,0.001,10)
        y += 0.35*np.random.randn(n)*_env(n,0.0005,70)
    elif kind == "ka":     # dry closed slap (short)
        n = int(0.10*SR)
        y = 0.6*np.random.randn(n)*_env(n,0.0005,55)
        y += 0.4*np.sin(2*np.pi*300*np.arange(n)/SR)*_env(n,0.001,25)
    else:
        n = int(0.1*SR); y = np.zeros(n)
    return (y/ (np.max(np.abs(y))+1e-9)) * vel

# Keherwa, 8 eighth-note slots per bar. (bol, velocity) ; None = rest
PATTERN = [
    ("dha", 1.00), ("na", 0.55), ("na", 0.75), ("tin", 0.65),
    ("ge", 0.85),  ("ka", 0.5),  ("dha", 0.7), ("na", 0.6),
]
FILL = [  # occasional bar-end fill
    ("dha", 1.0), ("na", 0.7), ("tin", 0.7), ("na", 0.6),
    ("ge", 0.8),  ("ka", 0.6), ("na", 0.8), ("tin", 0.9),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=float, default=108)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fills", action="store_true")
    ap.add_argument("--swing", type=float, default=0.04, help="offbeat delay fraction")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.RandomState(a.seed); np.random.seed(a.seed)

    quarter = 60.0/a.bpm
    slot = quarter/2.0                 # eighth-note
    bar = slot*8
    total = int((a.duration+1.0)*SR)
    out = np.zeros(total)

    nbars = int(a.duration/bar)+1
    for b in range(nbars):
        pat = FILL if (a.fills and b>0 and b%4==3) else PATTERN
        for i,(bol,vel) in enumerate(pat):
            if bol is None: continue
            v = vel * (0.85+0.3*rng.rand())          # velocity humanize
            sw = a.swing*slot if i%2==1 else 0.0
            jit = (rng.rand()-0.5)*0.006             # timing humanize
            start = int((b*bar + i*slot + sw + jit)*SR)
            s = stroke(bol, v)
            e = min(start+len(s), total)
            if start<total: out[start:e] += s[:e-start]

    out = out[:int(a.duration*SR)]
    out = out/(np.max(np.abs(out))+1e-9)*0.85
    sf.write(a.out, out.astype(np.float32), SR)
    print(f"[perc] {a.out}  {a.duration:.0f}s @ {a.bpm} bpm keherwa"
          f"{' +fills' if a.fills else ''}")

if __name__ == "__main__":
    main()
