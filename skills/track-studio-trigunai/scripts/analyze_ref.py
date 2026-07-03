#!/usr/bin/env python3
import numpy as np, librosa, json, sys
y,SR=librosa.load("/home/ubuntu/ref_open.mp3",sr=44100,mono=True)
dur=len(y)/SR
# tempo
tempo,beats=librosa.beat.beat_track(y=y,sr=SR)
tempo=float(np.atleast_1d(tempo)[0])
# HPSS -> harmonic vs percussive energy
H,P=librosa.effects.hpss(y)
harm=float(np.sqrt(np.mean(H**2))); perc=float(np.sqrt(np.mean(P**2)))
# onsets
ons=librosa.onset.onset_detect(y=y,sr=SR,units='time'); onrate=len(ons)/dur
# spectral brightness
cen=float(np.mean(librosa.feature.spectral_centroid(y=y,sr=SR)))
roll=float(np.mean(librosa.feature.spectral_rolloff(y=y,sr=SR,roll_percent=0.85)))
# band energy
S=np.abs(librosa.stft(y,n_fft=4096)); freqs=librosa.fft_frequencies(sr=SR,n_fft=4096)
def band(lo,hi):
    m=(freqs>=lo)&(freqs<hi); return float(np.mean(S[m,:])) if m.any() else 0.0
bands={"sub_20_80":band(20,80),"bass_80_250":band(80,250),"lowmid_250_500":band(250,500),
       "mid_500_2k":band(500,2000),"high_2k_8k":band(2000,8000),"air_8k+":band(8000,20000)}
bt=sum(bands.values())+1e-9; bandpct={k:round(100*v/bt,1) for k,v in bands.items()}
# key estimate via chroma + Krumhansl profiles
chroma=librosa.feature.chroma_cqt(y=H,sr=SR); cmean=chroma.mean(axis=1)
maj=np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
mino=np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def bestkey(prof):
    best=(-9,None)
    for i in range(12):
        r=np.corrcoef(np.roll(prof,-i),cmean)[0,1]
        if r>best[0]: best=(r,names[i])
    return best
km=bestkey(maj); kn=bestkey(min if False else mino)
key = f"{km[1]} major" if km[0]>=kn[0] else f"{kn[1]} minor"
# top pitch classes
order=np.argsort(cmean)[::-1]; topnotes=[names[i] for i in order[:5]]
# monophonic melody (pyin) -> note events for MIDI reuse
f0,vf,vp=librosa.pyin(H,fmin=110,fmax=1200,sr=SR,frame_length=4096)
times=librosa.times_like(f0,sr=SR)
notes=[]
cur=None
for i,f in enumerate(f0):
    if f is not None and not np.isnan(f) and vf[i]:
        m=int(round(69+12*np.log2(f/440)))
        if cur and abs(m-cur['m'])<1 and times[i]-cur['end']<0.12: cur['end']=times[i]
        else:
            if cur and cur['end']-cur['start']>0.08: notes.append(cur)
            cur={'m':m,'start':float(times[i]),'end':float(times[i])}
    else:
        if cur and cur['end']-cur['start']>0.08: notes.append(cur); cur=None
if cur and cur['end']-cur['start']>0.08: notes.append(cur)
melody=[{'midi':n['m'],'start':round(n['start'],3),'dur':round(n['end']-n['start'],3)} for n in notes]
out={"duration":round(dur,1),"tempo_bpm":round(tempo,1),"key":key,
     "harmonic_vs_percussive":round(harm/(perc+1e-9),2),"onsets_per_sec":round(onrate,2),
     "spectral_centroid_hz":round(cen),"rolloff85_hz":round(roll),"band_pct":bandpct,
     "top_pitch_classes":topnotes,"n_melody_notes":len(melody),
     "melody_first12":melody[:12]}
print(json.dumps(out,indent=2))
import numpy as _np
_np.save("/home/ubuntu/ref_melody.npy",_np.array([(m['midi'],m['start'],m['dur']) for m in melody]))
