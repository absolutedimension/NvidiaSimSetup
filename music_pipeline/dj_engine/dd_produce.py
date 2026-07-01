#!/usr/bin/env python3
"""Produce the final track through DawDreamer: base music + cleanly-rebuilt voice layer,
real EQ + compressor + reverb + master limiter. Fixes the metallic artifact (gentle pitch,
real reverb instead of numpy convolution)."""
import glob, numpy as np, librosa, soundfile as sf, dawdreamer as daw
from scipy.signal import butter, sosfilt
SR=44100; BPM=123
BASE="/home/ubuntu/dj_engine/burmeister/burmeister_track_v12.mp3"
OUT="/home/ubuntu/dj_engine/burmeister/burmeister_v12_DAW.wav"

def loadf(f,dur=None):
    y,_=librosa.load(f,sr=SR,mono=True,duration=dur); return y.astype(np.float32)
def longest(pat):
    fs=glob.glob(pat); return max(fs,key=lambda f:librosa.get_duration(path=f)) if fs else None
def gentle_pitch(y, target=6, clamp=4):
    ch=librosa.feature.chroma_cqt(y=y,sr=SR).mean(1); r=int(np.argmax(ch))
    s=((target-r+6)%12)-6; s=max(-clamp,min(clamp,s))            # small shift only -> no metallic artifact
    return librosa.effects.pitch_shift(y,sr=SR,n_steps=s).astype(np.float32) if s else y
def duck(n,depth,tau=0.11):
    beat=60.0/BPM; tt=(np.arange(n)/SR)%beat; return (1.0-depth*np.exp(-tt/tau)).astype(np.float32)
def trim(y,thr=0.015):
    idx=np.where(np.abs(y)>thr)[0]; return y[idx[0]:idx[-1]] if len(idx) else y

base=loadf(BASE); T=len(base)
def most_melodic(pats):
    fs=[]; [fs.extend(glob.glob(p)) for p in pats]
    best=None; bestv=-1
    for f in fs:
        try:
            y=loadf(f); y=trim(y)[:15*SR]
            f0=librosa.yin(y,fmin=110,fmax=700,sr=SR); v=float(np.nanstd(f0))
            print(f"  f0std={v:6.1f}  {f.split('/')[-1]}")
            if v>bestv: bestv=v; best=f
        except Exception: pass
    return best
mantra=gentle_pitch(trim(loadf(longest("/home/ubuntu/dj_engine/burmeister/voices/mantra/*.mp3"))))
# Magnus Choir (id 278903) = harmonic choir pad, NOT a single-tone drone -> won't horn.
cand=glob.glob("/home/ubuntu/dj_engine/burmeister/vocals/female/*278903*") or \
     glob.glob("/home/ubuntu/dj_engine/burmeister/vocals/female/*639837*")
fpick=cand[0]; print("female <-", fpick.split("/")[-1])
female=gentle_pitch(trim(loadf(fpick)))

def chunk(y,ls,i):
    L=int(ls*SR)
    seg=(np.pad(y,(0,L-len(y))) if len(y)<=L else y[(i*int(5.3*SR))%(len(y)-L):][:L]).copy()
    fd=int(0.4*SR); seg[:fd]*=np.linspace(0,1,fd); seg[-fd:]*=np.linspace(1,0,fd); return seg

# DRY rotating voice layer (reverb added later by the DAW)
vlayer=np.zeros(T,np.float32); mlevel=np.ones(T,np.float32)   # mlevel dips the mantra (rarer+lower)
pat=["female","female","mantra","female","female","female","mantra","female"]; t=int(40*SR); i=0  # start AFTER the intro is dense
while t<T-SR:
    k=pat[i%len(pat)]; seg={"mantra":mantra*0.7,"female":chunk(female,12,i)}[k]  # mantra lower
    n=min(len(seg),T-t); vlayer[t:t+n]+=seg[:n]; t+=int((15+(i%3)*3)*SR); i+=1
# slow tremolo so the female drone breathes instead of sounding like a held horn
trem=(0.72+0.28*np.sin(2*np.pi*0.4*np.arange(T)/SR)).astype(np.float32)
vlayer*=trem*duck(T,0.6)

# ---- DawDreamer production graph ----
eng=daw.RenderEngine(SR,512)
b=eng.make_playback_processor("base", np.stack([base,base]))
v=eng.make_playback_processor("voice", np.stack([vlayer,vlayer]))
bcomp=eng.make_compressor_processor("bcomp")
vhp=eng.make_filter_processor("vhp","high",170.0,0.7,1.0)   # (name, mode, freq, q, gain)
vlp=eng.make_filter_processor("vlp","low",5200.0,0.7,1.0)
vnotch=eng.make_filter_processor("vnotch","notch",2600.0,3.0,1.0)  # kill the harsh 'annoying' band
vrev=eng.make_reverb_processor("vrev")
mix=eng.make_add_processor("mix",[1.0,0.55])
mlim=eng.make_compressor_processor("mlim")
for proc,attrs in [(bcomp,dict(threshold=-16.0,ratio=2.0,attack=15.0,release=150.0)),
                   (mlim,dict(threshold=-8.0,ratio=4.0,attack=5.0,release=80.0)),
                   (vrev,dict(room_size=0.55,damping=0.78,wet_level=0.40,dry_level=0.6,width=1.0))]:
    for a_,val in attrs.items():
        try: setattr(proc,a_,val)
        except Exception as e: print("attr skip",a_,repr(e)[:60])
eng.load_graph([(b,[]),(bcomp,["base"]),(v,[]),(vhp,["voice"]),(vlp,["vhp"]),(vnotch,["vlp"]),(vrev,["vnotch"]),
                (mix,["bcomp","vrev"]),(mlim,["mix"])])
eng.render(T/SR+1.0)
out=eng.get_audio()
out=out/(np.max(np.abs(out))+1e-6)*0.97
sf.write(OUT,out.T,SR)
print("DONE ->",OUT,out.shape)
