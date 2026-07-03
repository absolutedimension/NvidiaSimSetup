#!/usr/bin/env python3
"""Create a real multi-track MIDI (drums+bass+lead, F# minor, 123 BPM), then READ IT BACK
and render it through synthesized elements -> audio. Proves the MIDI->your-synth->sound flow."""
import numpy as np, soundfile as sf, os, subprocess, sys
try: import mido
except ImportError:
    subprocess.run([sys.executable,"-m","pip","install","--quiet","--break-system-packages","mido"]); import mido

SR=44100; BPM=123.0; beat=60/BPM; TPB=480
def hz(m): return 440.0*2**((m-69)/12)
from scipy.signal import butter, sosfilt
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)
rng=np.random.default_rng(5)

# ---------- 1) BUILD THE MIDI ----------
BARS=8
mid=mido.MidiFile(ticks_per_beat=TPB)
def add_track(events):   # events: (start_beat, dur_beat, note, vel)
    tr=mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(int(BPM))))
    seq=[]
    for sb,db,n,v in events:
        seq.append((int(sb*TPB),'on',n,v)); seq.append((int((sb+db)*TPB),'off',n,0))
    seq.sort(key=lambda x:(x[0], x[1]=='on'))
    last=0
    for tick,kind,n,v in seq:
        tr.append(mido.Message('note_on' if kind=='on' else 'note_off',note=n,velocity=v,time=tick-last)); last=tick
# DRUMS: kick(36) every beat, closed hat(42) offbeats + 16ths
drums=[]
for b in range(BARS*4): drums.append((b,0.25,36,110))
for b in np.arange(0.5,BARS*4,1): drums.append((b,0.1,42,90))
for b in np.arange(0.25,BARS*4,0.5): drums.append((b,0.05,42,45))
add_track(drums)
# BASS: 2-bar F# minor riff x4
riff=[(0,42),(0.5,42),(1,45),(1.5,42),(2,40),(2.5,40),(3,42),(3.5,45),
      (4,42),(4.5,42),(5,47),(5.5,45),(6,44),(6.5,42),(7,40),(7.5,42)]
bass=[]
for rep in range(BARS//2):
    for bt,n in riff: bass.append((rep*8+bt,0.5,n,100))
add_track(bass)
# LEAD: F# minor arp (F#4 A4 C#5 E5), 16ths, bars 3-7
arp=[66,69,73,76,73,69]
lead=[]
for b in range(2*4,7*4):           # beats in bars 3..7
    for i,step in enumerate(np.arange(0,1,0.25)):
        lead.append((b+step,0.22,arp[(b*4+i)%len(arp)],80))
add_track(lead)
os.makedirs("/home/ubuntu/midi_demo",exist_ok=True)
MID="/home/ubuntu/midi_demo/sample_pattern.mid"; mid.save(MID); print("MIDI saved:",MID)

# ---------- 2) READ IT BACK + RENDER through synth elements ----------
loaded=mido.MidiFile(MID)
def track_notes(tr):
    out=[]; t=0; on={}
    for m in tr:
        t+=m.time
        if m.type=='note_on' and m.velocity>0: on[m.note]=(t,m.velocity)
        elif (m.type=='note_off') or (m.type=='note_on' and m.velocity==0):
            if m.note in on: st,v=on.pop(m.note); out.append((st,t-st,m.note,v))
    return out
TOT=int((BARS*4*beat+2)*SR); mixL=np.zeros(TOT,np.float32); mixR=np.zeros(TOT,np.float32)
def kick():
    hl=int(0.42*SR); t=np.arange(hl)/SR
    f=48+(165-48)*np.exp(-t/0.028); b=np.sin(np.cumsum(2*np.pi*f/SR))*np.exp(-t/0.34)
    cn=int(0.006*SR); b[:cn]+=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.0015*SR))*0.5
    return np.tanh(b*2.3).astype(np.float32)
def chat():
    hl=int(0.06*SR); t=np.arange(hl)/SR
    return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.02),7000)
def reese(m,db):
    hl=int(max(db,0.3)*beat*1.05*SR); t=np.arange(hl)/SR; f=hz(m)
    o=(saw(f,hl)+saw(f*1.008,hl)+saw(f*0.992,hl))/3*np.minimum(1,t/0.006)*np.exp(-t/(db*beat*0.7))
    return lp(o,820)
def pluck(m,db):
    hl=int(0.3*SR); t=np.arange(hl)/SR; f=hz(m)
    o=(saw(f,hl)+saw(f*1.005,hl))/2*np.minimum(1,t/0.002)*np.exp(-t/0.11)
    return lp(o,3200)
def stereo_add(one,tsec,pan,g):
    s=int(tsec*SR); seg=one[:max(0,min(len(one),TOT-s))]*g
    if s<TOT: mixL[s:s+len(seg)]+=seg*(1-pan)*0.5+seg*0.5; mixR[s:s+len(seg)]+=seg*pan*0.5+seg*0.5
t2s=lambda tick:(tick/TPB)*beat
for ti,tr in enumerate(loaded.tracks):
    for st,du,n,v in track_notes(tr):
        ts=t2s(st); dus=max(t2s(du)/beat,0.2); g=v/127
        if ti==0:  # drums
            if n==36: stereo_add(kick(),ts,0.5,0.95*g)
            else:     stereo_add(chat(),ts,0.62,0.5*g)
        elif ti==1: stereo_add(hp(reese(n,dus),40),ts,0.5,0.6*g)      # bass
        else:       stereo_add(hp(pluck(n,dus),200),ts,0.40,0.42*g)   # lead
st=np.stack([mixL,mixR]); st=st/(np.max(np.abs(st))+1e-6)*0.92
sf.write("/home/ubuntu/midi_demo/sample_pattern.wav",st.T,SR); print("WAV rendered from the MIDI")
