#!/usr/bin/env python3
"""Recreate the reference STYLE: a warm dark pluck-bass playing a NEW melodic line in
D Mixolydian @ 126 BPM (matches analysis: no drums, 95% low-end, ~4 notes/sec). Writes a
sample MIDI + renders it to MP3 with the synthesized element. Copyright-clean (new melody)."""
import numpy as np, soundfile as sf, os, subprocess, sys
try: import mido
except ImportError:
    subprocess.run([sys.executable,"-m","pip","install","--quiet","--break-system-packages","mido"]); import mido
from scipy.signal import butter, sosfilt
SR=44100; BPM=126.0; beat=60/BPM; TPB=480; OUT="/home/ubuntu/midi_demo"; os.makedirs(OUT,exist_ok=True)
def hz(m): return 440.0*2**((m-69)/12)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)

# ---- the recreated ELEMENT: warm dark pluck-bass ----
def plbass(m,db):
    dur=min(max(db,0.3),1.4); hl=int(dur*beat*SR+0.18*SR); t=np.arange(hl)/SR; f=hz(m)
    osc=saw(f,hl)*0.7 + np.sin(2*np.pi*(f/2)*np.arange(hl)/SR)*0.6   # saw + sub octave (heavy low end)
    body=osc*np.minimum(1,t/0.004)*np.exp(-t/(0.35+dur*0.25))
    return np.tanh(lp(body,1200)*1.4).astype(np.float32)             # dark lowpass + warm saturation
def darkpad(midis,n):
    acc=np.zeros(n,np.float32); V=4
    for m in midis:
        f=hz(m)
        for i in range(V): acc+=saw(f*(1+(i-V//2)*0.015/V),n)
    acc/=len(midis)*V; sw=0.55+0.45*np.sin(2*np.pi*0.05*np.arange(n)/SR)
    return hp(lp(acc,700)*sw,45)   # very dark warm pad under the melody

# ---- NEW melody in D Mixolydian (D E F# G A B C), low register ----
# (start_beat, dur_beat, midi)  ~32 beats, flowing ~4 notes/sec
mel=[(0,1,50),(1,0.5,57),(1.5,0.5,55),(2,1,54),(3,0.5,52),(3.5,0.5,50),
     (4,1,45),(5,0.5,50),(5.5,0.5,54),(6,1,55),(7,1,57),
     (8,0.5,59),(8.5,0.5,57),(9,1,55),(10,0.5,54),(10.5,0.5,52),(11,1,50),
     (12,0.5,48),(12.5,0.5,50),(13,1,52),(14,1,54),(15,1,50),
     (16,1,50),(17,0.5,57),(17.5,0.5,59),(18,1,60),(19,0.5,59),(19.5,0.5,57),
     (20,1,55),(21,0.5,54),(21.5,0.5,55),(22,1,57),(23,1,54),
     (24,0.5,50),(24.5,0.5,52),(25,1,54),(26,0.5,55),(26.5,0.5,57),(27,1,55),
     (28,1,52),(29,0.5,50),(29.5,0.5,48),(30,2,50)]
TOTB=32
# write MIDI
mid=mido.MidiFile(ticks_per_beat=TPB); tr=mido.MidiTrack(); mid.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(int(BPM))))
seq=[]
for sb,db,n in mel: seq+=[(int(sb*TPB),'on',n,96),(int((sb+db)*TPB),'off',n,0)]
seq.sort(key=lambda x:(x[0],x[1]=='on')); last=0
for tk,k,n,v in seq: tr.append(mido.Message('note_on' if k=='on' else 'note_off',note=n,velocity=v,time=tk-last)); last=tk
MID=f"{OUT}/ref_style_sample.mid"; mid.save(MID); print("MIDI:",MID)

# render from the MIDI note list
N=int((TOTB*beat+1.5)*SR); mix=np.zeros(N,np.float32)
for sb,db,n in mel:
    s=int(sb*beat*SR); one=plbass(n,db)
    if s<N: seg=one[:max(0,min(len(one),N-s))]; mix[s:s+len(seg)]+=seg
# subtle dark pad on D (root+fifth) under it
pad=darkpad([38,45],N)*0.18
mix=mix*0.9+pad
mix=np.tanh(mix*1.05).astype(np.float32); mix=mix/(np.max(np.abs(mix))+1e-6)*0.94
sf.write(f"{OUT}/ref_style_sample.wav",np.stack([mix,mix]).T,SR); print("WAV rendered",round(N/SR,1),"s")
