#!/usr/bin/env python3
"""Same D-Mixolydian melody, 4 different element TIMBRES so the user can pick the match:
 1 saw-synth (current)  2 soft-round  3 plucked-string (Karplus-Strong)  4 mallet/marimba."""
import numpy as np, soundfile as sf, os
from scipy.signal import butter, sosfilt
SR=44100; BPM=126.0; beat=60/BPM; OUT="/home/ubuntu/midi_demo"; rng=np.random.default_rng(4)
def hz(m): return 440.0*2**((m-69)/12)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)

def v_saw(m,db):
    dur=min(max(db,0.3),1.4); hl=int(dur*beat*SR+0.18*SR); t=np.arange(hl)/SR; f=hz(m)
    o=saw(f,hl)*0.7+np.sin(2*np.pi*(f/2)*np.arange(hl)/SR)*0.6
    return np.tanh(lp(o*np.minimum(1,t/0.004)*np.exp(-t/(0.35+dur*0.25)),1200)*1.4).astype(np.float32)
def v_soft(m,db):   # rounded: sine + gentle 2nd/3rd harmonic, soft attack
    dur=min(max(db,0.3),1.4); hl=int(dur*beat*SR+0.2*SR); t=np.arange(hl)/SR; f=hz(m)
    o=(np.sin(2*np.pi*f*np.arange(hl)/SR)+0.35*np.sin(2*np.pi*2*f*np.arange(hl)/SR)
       +0.15*np.sin(2*np.pi*3*f*np.arange(hl)/SR)+0.5*np.sin(2*np.pi*(f/2)*np.arange(hl)/SR))
    return lp(o*np.minimum(1,t/0.010)*np.exp(-t/(0.5+dur*0.3)),1500).astype(np.float32)
def v_pluck(m,db):  # Karplus-Strong plucked string + sub layer
    dur=min(max(db,0.3),1.4); n=int(dur*beat*SR+0.25*SR); f=hz(m); L=max(2,int(SR/f))
    buf=rng.standard_normal(L).astype(np.float32); out=np.zeros(n,np.float32); damp=0.995
    for i in range(n):
        out[i]=buf[i%L]; buf[i%L]=damp*0.5*(buf[i%L]+buf[(i+1)%L])
    t=np.arange(n)/SR; sub=np.sin(2*np.pi*(f/2)*np.arange(n)/SR)*np.exp(-t/(dur*0.5))*0.5
    return lp((out*np.exp(-t/(dur*0.7))+sub),1600).astype(np.float32)
def v_mallet(m,db): # marimba/hang: fundamental + inharmonic partials, fast decay + click
    dur=min(max(db,0.3),1.4); hl=int(dur*beat*SR+0.15*SR); t=np.arange(hl)/SR; f=hz(m)
    y=(np.sin(2*np.pi*f*np.arange(hl)/SR)*np.exp(-t/(dur*0.45))
       +0.35*np.sin(2*np.pi*3.9*f*np.arange(hl)/SR)*np.exp(-t/(dur*0.18))
       +0.15*np.sin(2*np.pi*6.8*f*np.arange(hl)/SR)*np.exp(-t/(dur*0.10)))
    cn=int(0.003*SR); y[:cn]+=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.001*SR))*0.3
    y+=np.sin(2*np.pi*(f/2)*np.arange(hl)/SR)*np.exp(-t/(dur*0.5))*0.4
    return lp(y,2000).astype(np.float32)

mel=[(0,1,50),(1,0.5,57),(1.5,0.5,55),(2,1,54),(3,0.5,52),(3.5,0.5,50),(4,1,45),(5,0.5,50),
     (5.5,0.5,54),(6,1,55),(7,1,57),(8,0.5,59),(8.5,0.5,57),(9,1,55),(10,0.5,54),(10.5,0.5,52),
     (11,1,50),(12,0.5,48),(12.5,0.5,50),(13,1,52),(14,1,54),(15,1,50)]
TOTB=16
def render(fn):
    N=int((TOTB*beat+1.5)*SR); mix=np.zeros(N,np.float32)
    for sb,db,n in mel:
        s=int(sb*beat*SR); one=fn(n,db)
        if s<N: seg=one[:max(0,min(len(one),N-s))]; mix[s:s+len(seg)]+=seg
    return mix/(np.max(np.abs(mix))+1e-6)*0.94
for name,fn in [("1saw",v_saw),("2soft",v_soft),("3pluck",v_pluck),("4mallet",v_mallet)]:
    m=render(fn); sf.write(f"{OUT}/timbre_{name}.wav",np.stack([m,m]).T,SR); print("  ",name)
print("done")
