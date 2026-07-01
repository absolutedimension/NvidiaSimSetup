#!/usr/bin/env python3
"""psy_synth.py — clean-room psychedelic (Goa/psytrance) element synthesizer.

Renders SEPARATE stems (kick, bass, acid-303, arp, drone, hats) at a fixed BPM in a
chosen root + PHRYGIAN scale (the eastern Goa feel), 100% from DSP — NO samples, so the
source is copyright-clean. These stems feed the Goa-Gil arrangement engine (which already
knows his sequencing grammar). numpy + scipy only.

Usage: python3 psy_synth.py --bpm 145 --bars 8 --root 45 --seed 7 --out STEMS_DIR
"""
import argparse, os, numpy as np
from scipy.signal import butter, sosfilt
import soundfile as sf

ap=argparse.ArgumentParser()
ap.add_argument("--bpm", type=int, default=145)
ap.add_argument("--bars", type=int, default=8)
ap.add_argument("--root", type=int, default=45, help="MIDI root for acid region (45=A2)")
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--out", required=True)
a=ap.parse_args()
np.random.seed(a.seed)
SR=44100
spb=60.0/a.bpm; step=spb/4.0
nsteps=a.bars*16
N=int(round(nsteps*step*SR))
t=np.arange(N)/SR
os.makedirs(a.out, exist_ok=True)

PHRYG=[0,1,3,5,7,8,10]
def mfreq(m): return 440.0*2**((m-69)/12.0)
def scale_note(root,deg):
    return root+12*(deg//7)+PHRYG[deg%7]
def lp(x,f): return sosfilt(butter(4,min(f,SR*0.49)/(SR/2),btype="low",output="sos"),x).astype(np.float32)
def hp(x,f): return sosfilt(butter(4,f/(SR/2),btype="high",output="sos"),x).astype(np.float32)
def saw(ph): return (2.0*(ph/(2*np.pi)-np.floor(ph/(2*np.pi)+0.5))).astype(np.float32)

# time-varying resonant lowpass (Chamberlin SVF) — the 303 squelch
def svf_lp(x, fc, res):
    f=2*np.sin(np.pi*np.clip(fc,40,SR*0.22)/SR).astype(np.float64)
    q=2.0*(1.0-res); low=0.0; band=0.0
    out=np.empty(len(x),np.float64); xx=x.astype(np.float64)
    for i in range(len(xx)):
        high=xx[i]-low-q*band
        band=f[i]*high+band
        low=f[i]*band+low
        out[i]=low
    return out.astype(np.float32)

def place(y, seg, s):
    n=max(0,min(len(seg), N-s));  y[s:s+n]+=seg[:n]

# ---------- KICK: 4-on-floor psy kick (pitch-drop sine + click) ----------
def gen_kick():
    y=np.zeros(N,np.float32); kl=int(0.32*SR); kk=np.arange(kl)/SR
    pitch=50+(200-50)*np.exp(-kk/0.012)
    body=np.sin(2*np.pi*np.cumsum(pitch)/SR)*np.exp(-kk/0.12)
    cl=int(0.003*SR); click=np.random.randn(cl)*np.exp(-np.arange(cl)/(0.0015*SR))
    one=body.copy(); one[:cl]+=click*0.5; one=np.tanh(one*1.6).astype(np.float32)
    for b in range(a.bars*4): place(y,one,int(b*spb*SR))
    return y*0.95

# ---------- BASS: rolling 16ths on the off-kick steps (the psy engine) ----------
def gen_bass():
    y=np.zeros(N,np.float32); nl=int(step*0.92*SR); nn=np.arange(nl)/SR
    f=mfreq(a.root-12)  # one octave below acid root
    for st in range(nsteps):
        if st%4==0: continue   # leave the kick step open
        ph=2*np.pi*f*nn
        tone=(saw(ph)*0.55+np.sin(ph)*0.45)*np.exp(-nn/0.05)
        place(y, lp(tone,210), int(st*step*SR))
    return y*0.85

# ---------- ACID: 303 line, env-mod cutoff + accents + slides ----------
def gen_acid():
    pat=[(0,1,0),(None,0,0),(0,0,1),(7,0,0),(None,0,0),(0,1,0),(3,0,1),(0,0,0),
         (5,0,0),(None,0,0),(0,1,0),(0,0,1),(7,0,0),(None,0,0),(3,0,0),(10,0,0)]
    base=a.root+12
    osc=np.zeros(N,np.float32); cutoff=np.full(N,250.0,np.float32); amp=np.zeros(N,np.float32)
    ph=0.0; cur=mfreq(base)
    for bar in range(a.bars):
        for i,(deg,acc,sld) in enumerate(pat):
            st=bar*16+i; s=int(st*step*SR); e=int((st+1)*step*SR); n=e-s
            if n<=0 or deg is None: continue
            tgt=mfreq(scale_note(base,deg))
            fr=np.linspace(cur,tgt,n) if sld else np.full(n,tgt); cur=tgt
            sph=ph+2*np.pi*np.cumsum(fr)/SR; ph=sph[-1]
            peak=2400 if acc else 1100; dec=0.20 if acc else 0.10
            ce=peak*np.exp(-np.arange(n)/(dec*SR))+170
            ae=(1.0 if acc else 0.65)*np.exp(-np.arange(n)/(0.17*SR))
            osc[s:e]=saw(sph)[:n]; cutoff[s:e]=ce[:n]; amp[s:e]=ae[:n]
    filt=svf_lp(osc,cutoff,res=0.90)
    return (np.tanh(filt*amp*3.2)*0.5).astype(np.float32)

# ---------- ARP: phrygian pluck (8ths) + dotted feedback delay ----------
def gen_arp():
    notes=[0,2,4,6,4,2,4,5]; base=a.root+24
    y=np.zeros(N,np.float32); nl=int(step*1.5*SR); nn=np.arange(nl)/SR
    for st in range(nsteps):
        if st%2==1: continue
        f=mfreq(scale_note(base,notes[(st//2)%len(notes)]))
        o=saw(2*np.pi*f*nn)*np.exp(-nn/0.08)
        place(y, lp(o,3200)*0.45, int(st*step*SR))
    dt=int(spb*0.75*SR); d=y.copy()
    for _ in range(6):
        d=np.concatenate([np.zeros(dt,np.float32), d[:-dt]])*0.42; y=y+d
    return (hp(y,300)*0.5).astype(np.float32)

# ---------- DRONE: detuned supersaw + slow filter LFO + cheap reverb ----------
def gen_drone():
    dets=[-7,-3,0,3,7]
    def stack(m):
        s=np.zeros(N,np.float32)
        for c in dets: s+=saw(2*np.pi*mfreq(m)*2**(c/1200.0)*t)
        return s/len(dets)
    y=stack(a.root)+0.6*stack(a.root+7)
    lfo=0.5+0.5*np.sin(2*np.pi*0.05*t)
    y=svf_lp(y.astype(np.float32),(400+1700*lfo).astype(np.float32),res=0.45)
    rv=y.copy()
    for dms,g in [(37,0.5),(53,0.4),(71,0.35)]:
        dt=int(dms/1000*SR); rv=rv+np.concatenate([np.zeros(dt,np.float32),y[:-dt]])*g
    return (rv*0.22).astype(np.float32)

# ---------- HATS: offbeat-16th filtered-noise ticks ----------
def gen_hats():
    y=np.zeros(N,np.float32); hl=int(0.05*SR); nn=np.arange(hl)/SR
    for st in range(nsteps):
        if st%2==0: continue
        place(y, (np.random.randn(hl)*np.exp(-nn/0.012)).astype(np.float32), int(st*step*SR))
    return (hp(y,7000)*0.4).astype(np.float32)

for name,fn in [("kick",gen_kick),("bass",gen_bass),("acid",gen_acid),
                ("arp",gen_arp),("drone",gen_drone),("hats",gen_hats)]:
    print(f"[synth] {name} ...", flush=True)
    sf.write(f"{a.out}/{name}.wav", fn(), SR)
print(f"[synth] DONE -> {a.out}  ({a.bars} bars @ {a.bpm} BPM, root midi {a.root}, phrygian)")
