#!/usr/bin/env python3
"""3 different MIDI rhythms rendered through the synth elements. Same key (F# minor)/sounds,
different grooves: DRIVING (4-on-floor), BROKEN (syncopated), TRIBAL (halftime + toms)."""
import numpy as np, soundfile as sf, os, subprocess, sys
try: import mido
except ImportError:
    subprocess.run([sys.executable,"-m","pip","install","--quiet","--break-system-packages","mido"]); import mido
from scipy.signal import butter, sosfilt
SR=44100; BPM=123.0; beat=60/BPM; TPB=480; BARS=4
OUT="/home/ubuntu/midi_demo"; os.makedirs(OUT,exist_ok=True); rng=np.random.default_rng(3)
def hz(m): return 440.0*2**((m-69)/12)
def saw(f,n):
    ph=np.cumsum(np.full(n,2*np.pi*f/SR)); return (2*((ph/(2*np.pi))%1)-1).astype(np.float32)
def lp(x,fc): return sosfilt(butter(4,min(fc,SR/2-100)/(SR/2),'low',output='sos'),x).astype(np.float32)
def hp(x,fc): return sosfilt(butter(2,max(20,fc)/(SR/2),'high',output='sos'),x).astype(np.float32)
# --- element synths ---
def kick():
    hl=int(0.42*SR); t=np.arange(hl)/SR
    f=48+(165-48)*np.exp(-t/0.028); b=np.sin(np.cumsum(2*np.pi*f/SR))*np.exp(-t/0.34)
    cn=int(0.006*SR); b[:cn]+=rng.standard_normal(cn)*np.exp(-np.arange(cn)/(0.0015*SR))*0.5
    return np.tanh(b*2.3).astype(np.float32)
def chat():
    hl=int(0.06*SR); t=np.arange(hl)/SR; return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.02),7000)
def ohat():
    hl=int(0.18*SR); t=np.arange(hl)/SR; return hp(rng.standard_normal(hl).astype(np.float32)*np.exp(-t/0.09),6000)
def clap():
    hl=int(0.16*SR); t=np.arange(hl)/SR; n=hp(rng.standard_normal(hl).astype(np.float32),1400); e=np.exp(-t/0.08)
    for d in (0.006,0.012,0.018):
        k=int(d*SR); e[k:]+=np.exp(-t[:hl-k]/0.05)
    return (n*np.minimum(e,2.5)*0.7).astype(np.float32)
def tom(f0):
    hl=int(0.3*SR); t=np.arange(hl)/SR; fr=f0*0.55+(f0-f0*0.55)*np.exp(-t/0.04)
    return (np.sin(np.cumsum(2*np.pi*fr/SR))*np.exp(-t/0.17)).astype(np.float32)
def sub(m,db):
    hl=int(max(db,0.3)*beat*SR); t=np.arange(hl)/SR
    return np.tanh(np.sin(2*np.pi*hz(m)*np.arange(hl)/SR)*np.minimum(1,t/0.008)*np.exp(-t/(db*beat*0.8))*1.3).astype(np.float32)
def reese(m,db):
    hl=int(max(db,0.3)*beat*1.05*SR); t=np.arange(hl)/SR; f=hz(m)
    return lp((saw(f,hl)+saw(f*1.008,hl)+saw(f*0.992,hl))/3*np.minimum(1,t/0.006)*np.exp(-t/(db*beat*0.7)),820)
DRUM={36:lambda:kick(),42:lambda:chat(),46:lambda:ohat(),38:lambda:clap(),45:lambda:tom(150),47:lambda:tom(230)}

def add_track(mid,events):
    tr=mido.MidiTrack(); mid.tracks.append(tr); tr.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(int(BPM))))
    seq=[]
    for sb,db,n,v in events: seq+=[(int(sb*TPB),'on',n,v),(int((sb+db)*TPB),'off',n,0)]
    seq.sort(key=lambda x:(x[0],x[1]=='on')); last=0
    for tk,k,n,v in seq: tr.append(mido.Message('note_on' if k=='on' else 'note_off',note=n,velocity=v,time=tk-last)); last=tk
def track_notes(tr):
    out=[]; t=0; on={}
    for m in tr:
        t+=m.time
        if m.type=='note_on' and m.velocity>0: on[m.note]=t
        elif m.type=='note_off' or (m.type=='note_on' and m.velocity==0):
            if m.note in on: st=on.pop(m.note); out.append((st,t-st,m.note))
    return out

def build_and_render(name,drums,bass):
    mid=mido.MidiFile(ticks_per_beat=TPB); add_track(mid,drums); add_track(mid,bass)
    mp=f"{OUT}/{name}.mid"; mid.save(mp)
    lo=mido.MidiFile(mp); TOT=int((BARS*4*beat+1.5)*SR); L=np.zeros(TOT,np.float32); R=np.zeros(TOT,np.float32)
    def place(one,tsec,pan,g):
        s=int(tsec*SR); seg=one[:max(0,min(len(one),TOT-s))]*g
        if s<TOT: L[s:s+len(seg)]+=seg*(0.6+0.4*(1-pan)); R[s:s+len(seg)]+=seg*(0.6+0.4*pan)
    for ti,tr in enumerate(lo.tracks):
        for st,du,n in track_notes(tr):
            ts=(st/TPB)*beat; dus=max((du/TPB),0.25)
            if ti==0: place(DRUM.get(n,lambda:chat())(),ts,0.5 if n in(36,38) else 0.65,0.9 if n==36 else 0.5)
            else:     place(hp(reese(n,dus) if n>=45 else sub(n,dus),36),ts,0.5,0.6)
    st=np.stack([L,R]); st=st/(np.max(np.abs(st))+1e-6)*0.92; sf.write(f"{OUT}/{name}.wav",st.T,SR)
    print("  ",name,"->",mp)

# ---- 1) DRIVING ----
d=[(b,0.25,36,110) for b in range(BARS*4)]
d+=[(b,0.1,42,95) for b in np.arange(0.5,BARS*4,1)]+[(b,0.05,42,45) for b in np.arange(0.25,BARS*4,0.5)]
d+=[(bar*4+3.75,0.2,46,80) for bar in range(BARS)]
bass=[(b,0.5,30,100) for b in np.arange(0.5,BARS*4,1)]
build_and_render("rhythm1_driving",d,bass)
# ---- 2) BROKEN / SYNCOPATED ----
d=[];
for bar in range(BARS):
    for k in (0,0.75,1.5,2.5,3.25): d.append((bar*4+k,0.25,36,108))
    d+=[(bar*4+1,0.15,38,100),(bar*4+3,0.15,38,100)]
d+=[(b,0.05,42,70) for b in np.arange(0,BARS*4,0.25)]
bass=[]
for bar in range(BARS): bass+=[(bar*4+0,0.5,30,100),(bar*4+1.5,0.5,42,90),(bar*4+2,0.5,30,100),(bar*4+3.25,0.75,37,95)]
build_and_render("rhythm2_broken",d,bass)
# ---- 3) TRIBAL / HALFTIME ----
d=[]
for bar in range(BARS):
    d+=[(bar*4+0,0.25,36,112),(bar*4+2,0.25,36,112)]
    for k in (0.25,0.75,1.25,1.75,2.75,3.25,3.75): d.append((bar*4+k,0.2,45 if (k*4)%2<1 else 47,90))
    d+=[(bar*4+1,0.1,42,60),(bar*4+3,0.1,42,60)]
bass=[(bar*4+0,1.4,30,100) for bar in range(BARS)]+[(bar*4+2,1.4,35,90) for bar in range(BARS)]
build_and_render("rhythm3_tribal",d,bass)
print("done")
