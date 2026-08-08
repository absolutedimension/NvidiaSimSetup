#!/usr/bin/env python3
"""make_ballad.py — build an original Bollywood-ballad backing: melody + MIDI + instrumental.

Outputs (all synthesized, copyright-clean):
  - saanson.mid       : melody + chords + tabla (open in any DAW)
  - instrumental.wav  : tanpura drone + harmonium + tabla keherwa + sarangi/strings + bansuri
  - guide.wav         : the vocal MELODY on a lead reed (sing along to this, then run through DK)

Key D minor, ~90 BPM. Runs in audio_pipeline/venv (numpy+scipy+soundfile).
"""
import argparse, os, struct, subprocess, numpy as np, soundfile as sf
from scipy.signal import lfilter

FS=32000; BPM=90; BEAT=60.0/BPM
ROOT=50                      # D3
MINOR=[0,2,3,5,7,8,10,12,14]
def deg2midi(d): return ROOT + (MINOR[d%len(MINOR)] + 12*(d//len(MINOR)))
def hz(m): return 440.0*2**((m-69)/12.0)
def lp(x,fc): r=np.exp(-2*np.pi*fc/FS); return lfilter([1-r],[1,-r],x)

# ---- melody: (scale-degree, beats) per phrase. Mukhda hook + antara ----
MUKHDA=[(4,1),(4,.5),(3,.5),(2,1.5),(4,1),(5,.5),(4,.5),(3,2),
        (3,1),(3,.5),(2,.5),(0,1.5),(2,1),(3,.5),(2,.5),(0,2)]
ANTARA=[(5,1),(5,.5),(4,.5),(5,1),(7,1.5),(5,1),(4,.5),(3,.5),(2,2),
        (3,1),(4,.5),(5,.5),(4,1),(3,1.5),(2,1),(0,.5),(2,.5),(0,2)]
FORM=[MUKHDA,ANTARA,MUKHDA,ANTARA,MUKHDA]   # full arrangement
INTRO_BEATS=8; OUTRO_BEATS=8

def adsr(n,a,d,s,r,sl=0.7):
    e=np.ones(n); ai=int(a*FS); di=int(d*FS); ri=int(r*FS)
    if ai>0: e[:ai]=np.linspace(0,1,ai)
    if di>0: e[ai:ai+di]=np.linspace(1,sl,di)
    e[ai+di:n-ri]=sl
    if ri>0: e[n-ri:]=np.linspace(sl,0,ri)
    return e

def reed(m,dur,detune=1.004,trem=0.05):     # harmonium
    n=int(dur*FS); t=np.arange(n)/FS; f=hz(m); y=np.zeros(n)
    for h,a in [(1,1),(2,.5),(3,.3),(4,.18),(5,.11)]: y+=a*np.sin(2*np.pi*f*h*t)
    y+=.3*np.sin(2*np.pi*f*detune*t); y*=(1+trem*np.sin(2*np.pi*5*t))
    return y*adsr(n,.08,.1,.7,.18)/(np.max(np.abs(y))+1e-9)

def sarangi(m,dur):                          # bowed string: rich saw + vibrato + slow bow
    n=int(dur*FS); t=np.arange(n)/FS
    vib=1+0.008*np.clip((t-0.1)/0.3,0,1)*np.sin(2*np.pi*5.5*t); f=hz(m)*vib
    ph=2*np.pi*np.cumsum(f)/FS; y=np.zeros(n)
    for k in range(1,14): y+=(1.0/k)*np.sin(k*ph)     # sawtooth-ish (bowed)
    y=lp(y,3200)*adsr(n,.12,.15,.75,.2)
    return y/(np.max(np.abs(y))+1e-9)

def bansuri(m,dur):                          # breathy flute: sine + air noise + soft attack
    n=int(dur*FS); t=np.arange(n)/FS; f=hz(m)*(1+0.006*np.clip((t-0.15)/0.3,0,1)*np.sin(2*np.pi*5*t))
    y=np.sin(2*np.pi*np.cumsum(f)/FS)+0.15*np.sin(2*np.pi*2*np.cumsum(f)/FS)
    y+=0.06*lp(np.random.randn(n),4000)      # breath
    return y*adsr(n,.10,.1,.8,.18)/(np.max(np.abs(y))+1e-9)

def render_line(phrase, inst):
    parts=[]
    for deg,beats in phrase:
        parts.append(inst(deg2midi(deg), beats*BEAT))
    return np.concatenate(parts)

def chord_bed(total_n):
    # Dm - Bb - C - Dm  (i - VI - VII - i)
    PROG=[[50,53,57],[46,50,53],[48,52,55],[50,53,57]]
    bed=[]; i=0
    while sum(len(x) for x in bed) < total_n:
        ch=PROG[i%4]; seg=sum(reed(m,4.0) for m in ch)/len(ch); bed.append(seg); i+=1
    return np.concatenate(bed)[:total_n]

def drone(total_n):
    t=np.arange(total_n)/FS; y=np.zeros(total_n)
    for m,a in [(38,0.6),(50,0.5),(45,0.35)]:    # D2, D3, A2
        for h,aa in [(1,1),(2,.4),(3,.2)]: y+=a*aa*np.sin(2*np.pi*hz(m)*h*t+np.random.rand())
    return (y*(1+0.03*np.sin(2*np.pi*0.2*t)))/(np.max(np.abs(y))+1e-9)

# ---- minimal Standard MIDI File writer ----
def _vlq(n):
    b=[n&0x7f]; n>>=7
    while n: b.insert(0,(n&0x7f)|0x80); n>>=7
    return bytes(b)
def write_midi(path, phrases):
    TPQ=480; ev=[]  # (tick, bytes)
    # melody ch0, chords ch1, tabla ch9
    tick=0
    def note(ch,m,start,dur,vel=90):
        ev.append((start,bytes([0x90|ch,m,vel]))); ev.append((start+dur,bytes([0x80|ch,m,0])))
    tabla=[38,42,38,46,38,42,44,42]   # simple keherwa on GM perc-ish notes
    for phrase in phrases:
        for deg,beats in phrase:
            d=int(beats*TPQ); note(0,deg2midi(deg),tick,d)
            tick+=d
    # chords + tabla across the whole timeline
    total=tick; t=0; ci=0; PROG=[[50,53,57],[46,50,53],[48,52,55],[50,53,57]]
    while t<total:
        for m in PROG[ci%4]: note(1,m,t,int(4*TPQ))
        for i in range(8):
            note(9,tabla[i],t+int(i*0.5*TPQ),int(0.25*TPQ),70)
        t+=int(4*TPQ); ci+=1
    ev.sort(key=lambda e:e[0])
    trk=b''; last=0
    for tk,b in ev: trk+=_vlq(tk-last)+b; last=tk
    trk+=_vlq(0)+b'\xff\x2f\x00'
    with open(path,'wb') as f:
        f.write(b'MThd'+struct.pack('>IHHH',6,0,1,TPQ))
        f.write(b'MTrk'+struct.pack('>I',len(trk))+trk)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out-dir",default="/home/ubuntu/music_out/ballad"); a=ap.parse_args()
    os.makedirs(a.out_dir,exist_ok=True); np.random.seed(7)
    intro_n=int(INTRO_BEATS*BEAT*FS); outro_n=int(OUTRO_BEATS*BEAT*FS)
    # guide melody (sarangi lead) = the tune to sing, with instrumental intro/outro (rests)
    mel=np.concatenate([render_line(p, sarangi) for p in FORM])
    guide=np.concatenate([np.zeros(intro_n), mel, np.zeros(outro_n)]); N=len(guide)
    # instrumental layers span the whole length (play through intro/outro)
    dr=lp(drone(N),1400); harm=lp(chord_bed(N),1900)
    # bansuri doubles the melody during sung sections only
    ban_mel=np.concatenate([render_line(p, bansuri) for p in FORM])
    ban=np.concatenate([np.zeros(intro_n), ban_mel, np.zeros(outro_n)])[:N]
    # tabla
    perc_wav=os.path.join(a.out_dir,"perc.wav")
    subprocess.run(f'~/audio_pipeline/venv/bin/python ~/singer_rl/synth_percussion.py --bpm {BPM} --duration {N/FS:.1f} --fills --out "{perc_wav}"',
                   shell=True,check=True,capture_output=True,text=True)
    perc,_=sf.read(perc_wav); perc=perc[:N] if len(perc)>=N else np.pad(perc,(0,N-len(perc))); perc=lp(perc,4000)
    # instrumental mix (no lead melody — that's the vocal's job; keep a soft bansuri)
    inst=0.16*dr+0.22*harm+0.24*perc+0.14*ban
    inst=inst/(np.max(np.abs(inst))+1e-9)*0.9
    sf.write(os.path.join(a.out_dir,"instrumental.wav"),inst.astype(np.float32),FS)
    # guide = melody lead + soft bed so the singer hears the tune in context
    g=0.7*guide + 0.10*dr + 0.12*harm + 0.14*perc
    g=g/(np.max(np.abs(g))+1e-9)*0.9
    sf.write(os.path.join(a.out_dir,"guide.wav"),g.astype(np.float32),FS)
    write_midi(os.path.join(a.out_dir,"saanson.mid"), FORM)
    print(f"[ballad] {N/FS:.1f}s -> instrumental.wav, guide.wav, saanson.mid")

if __name__=="__main__": main()
