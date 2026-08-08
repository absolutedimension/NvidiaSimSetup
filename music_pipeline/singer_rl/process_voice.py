#!/usr/bin/env python3
"""process_voice.py — clean + gently tune a USER-SUNG line into the song key (A minor).

Keeps the natural voice; only snaps pitch toward the nearest scale note (blend) + trims
silence + normalizes. Copyright-clean (the user's own consenting voice). Runs in
audio_pipeline/venv (pyworld+librosa+soundfile).

Usage:
  audio_pipeline/venv/bin/python process_voice.py --in line1_raw.m4a --out line1.wav [--blend 0.8]
"""
import argparse, numpy as np, soundfile as sf, librosa, pyworld as pw, subprocess, os

FP=0.005; MINOR=[0,2,3,5,7,8,10]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in",dest="inp",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--root",type=int,default=45)      # A2
    ap.add_argument("--blend",type=float,default=0.8)  # 1=hard autotune, 0=untouched
    ap.add_argument("--trim-db",type=float,default=30)
    a=ap.parse_args()
    # decode anything (m4a/mp3/wav) to wav 32k via ffmpeg first
    wav=a.inp
    if not a.inp.lower().endswith(".wav"):
        wav=os.path.splitext(a.out)[0]+"_in.wav"
        subprocess.run(["ffmpeg","-y","-i",a.inp,"-ar","32000","-ac","1",wav],capture_output=True)
    x,sr=librosa.load(wav,sr=32000,mono=True); x=x.astype(np.float64)
    x,_=librosa.effects.trim(x,top_db=a.trim_db)
    f0,t=pw.harvest(x,sr,frame_period=FP*1000); sp=pw.cheaptrick(x,f0,t,sr); ap=pw.d4c(x,f0,t,sr)
    scale=[a.root+o+12*k for k in range(-1,4) for o in MINOR]
    v=f0>0; nf0=f0.copy()
    if v.sum()>0:
        m=librosa.hz_to_midi(f0[v])
        snap=np.array([min(scale,key=lambda s:abs(s-mm)) for mm in m])
        tuned=a.blend*snap+(1-a.blend)*m
        nf0[v]=librosa.midi_to_hz(tuned)
    y=pw.synthesize(np.ascontiguousarray(nf0),sp,ap,sr,FP*1000)
    y=y/(np.max(np.abs(y))+1e-9)*0.9
    sf.write(a.out,y.astype(np.float32),sr)
    print(f"[voice] {a.out}  {len(y)/sr:.1f}s  voiced_frac={float(v.mean()):.2f}")

if __name__=="__main__": main()
