#!/usr/bin/env python3
"""hindi_sing_bank.py — Stage 2+3 of the vowel-bank singer.

Per syllable: keep the TTS CONSONANT ONSET (correct diction) but replace the sustained
vowel with a clean SUNG BANK VOWEL (vowel_bank.py formant synth) at the note pitch,
crossfaded. Vowel identity per syllable is parsed from the Devanagari text. Rhythm +
melody from the learned phrasing profile. Copyright-clean.

Runs in audio_pipeline/venv. Reuses hindi_sing.py + vowel_bank.py (same dir, 32 kHz).

Usage:
  audio_pipeline/venv/bin/python hindi_sing_bank.py --lyrics lyrics/tu_nahin_toh.txt \
    --phrasing phrasing_shukla.json --root 45 --out bank.wav
"""
import argparse, asyncio, os, tempfile
import numpy as np, soundfile as sf, pyworld as pw
from scipy.signal import find_peaks, lfilter
import vowel_bank as vb
from hindi_sing import tts_line, load_wav, voiced_runs, walk_notes, FP

FSv = vb.FS  # 32000

# ---- Devanagari -> ordered vowel label per syllable ----
VMATRA = {'ा':'aa','ि':'i','ी':'i','ु':'u','ू':'u','ृ':'i','े':'e','ै':'ai','ो':'o','ौ':'au'}
VINDEP = {'अ':'a','आ':'aa','इ':'i','ई':'i','उ':'u','ऊ':'u','ऋ':'i','ए':'e','ऐ':'ai','ओ':'o','औ':'au'}
NASALS = set('ंँः़')
VIRAMA = '्'
def is_cons(ch): return ('क'<=ch<='ह') or ('क़'<=ch<='य़')
def devanagari_vowels(text):
    out=[]; i=0; s=text; n=len(s)
    while i<n:
        ch=s[i]
        if ch in VINDEP: out.append(VINDEP[ch]); i+=1
        elif is_cons(ch):
            i+=1
            while i+1<n and s[i]==VIRAMA and is_cons(s[i+1]): i+=2   # conjunct cluster
            if i<n and s[i] in VMATRA: out.append(VMATRA[s[i]]); i+=1
            elif i<n and s[i]==VIRAMA: i+=1                          # half consonant, no vowel
            else: out.append('a')                                   # inherent schwa
            while i<n and s[i] in NASALS: i+=1
        else: i+=1
    return out

def bank_note(vowel, hz, dur, prev_hz, glide=0.08, vib_hz=5.4, vib_depth=0.014):
    n=max(int(dur*FSv),8); f0c=np.full(n,hz)
    gl=min(int(glide*FSv),n//2)
    if prev_hz>0 and gl>1: f0c[:gl]=np.linspace(prev_hz,hz,gl)
    t=np.arange(n)/FSv; venv=np.clip((t-0.12)/0.4,0,1)
    f0c=f0c*(1+vib_depth*venv*np.sin(2*np.pi*vib_hz*t))
    y=vb.glottal_contour(f0c)
    for (F,B) in vb.VOWELS.get(vowel, vb.VOWELS['a']): y=vb.formant(y,F,B)
    rlp=np.exp(-2*np.pi*5000/FSv); y=lfilter([1-rlp],[1,-rlp],y)
    at=int(0.02*FSv); rl=int(0.05*FSv); env=np.ones(n)
    env[:at]=np.linspace(0,1,at); env[-rl:]=np.linspace(1,0,rl)
    return (y*env)/(np.max(np.abs(y))+1e-9)*0.85

def env_to_fir(power_env):
    """min-phase FIR from a WORLD power spectral envelope (the TTS voice's vowel timbre)"""
    mag = np.sqrt(np.maximum(power_env, 1e-12))
    full = np.concatenate([mag, mag[-2:0:-1]]); L = len(full)
    cep = np.fft.ifft(np.log(full+1e-12)).real
    w = np.zeros(L); w[0]=1; w[1:L//2]=2; w[L//2]=1
    fir = np.fft.ifft(np.exp(np.fft.fft(cep*w))).real
    return fir

def sustain_from_tts(env, hz, dur, prev_hz):
    """sustain the TTS vowel's OWN timbre with the clean Rosenberg source at the note -> ONE voice, sung"""
    n=max(int(dur*FSv),8); f0c=np.full(n,hz)
    gl=min(int(0.08*FSv),n//2)
    if prev_hz>0 and gl>1: f0c[:gl]=np.linspace(prev_hz,hz,gl)
    t=np.arange(n)/FSv; venv=np.clip((t-0.12)/0.4,0,1)
    f0c=f0c*(1.0+0.014*venv*np.sin(2*np.pi*5.4*t))
    src=vb.glottal_contour(f0c)
    fir=env_to_fir(env)
    y=np.convolve(src,fir)[:n]
    at=int(0.02*FSv); rl=int(0.05*FSv); e=np.ones(n)
    e[:at]=np.linspace(0,1,at); e[-rl:]=np.linspace(1,0,rl)
    return (y*e)/(np.max(np.abs(y))+1e-9)*0.85

def wsynth(f0s, sps, aps, sr):
    if len(f0s)<1: return np.zeros(1)
    return pw.synthesize(np.ascontiguousarray(f0s,dtype=np.float64),
                         np.ascontiguousarray(sps), np.ascontiguousarray(aps), sr, FP*1000)

def syllabify_audio(f0, sp):
    runs=voiced_runs(f0)
    if not runs: return []
    energy=sp.sum(1); energy=np.convolve(energy,np.ones(3)/3,mode='same'); syl=[]
    for (a,b) in runs:
        seg=energy[a:b]
        if b-a<int(0.18/FP): syl.append((a,b)); continue
        pk,_=find_peaks(seg,distance=int(0.09/FP),prominence=seg.max()*0.12)
        if len(pk)<=1: syl.append((a,b)); continue
        bnds=[a]
        for p1,p2 in zip(pk[:-1],pk[1:]): bnds.append(a+p1+int(np.argmin(seg[p1:p2])))
        bnds.append(b); syl+=list(zip(bnds[:-1],bnds[1:]))
    return syl

def build_syllable(f0,sp,ap,sr,a,b,hz,dur,prev_hz):
    run_len=b-a
    attack_n=min(run_len, int(0.22/FP))
    onf0=f0[a:a+attack_n].astype(np.float64).copy(); onf0[onf0>0]=hz   # pitch onset to note
    o=wsynth(onf0,sp[a:a+attack_n],ap[a:a+attack_n],sr); o=o/(np.max(np.abs(o))+1e-9)*0.9
    cs=sp[a+run_len//2:b]; env=cs.mean(0) if len(cs)>0 else sp[max(a,b-1)]
    v=sustain_from_tts(env, hz, max(dur-len(o)/sr,0.12), prev_hz)       # TTS-timbre sung sustain
    xf=min(int(0.05*sr), len(o)//2, len(v)//2)
    if xf>1:
        o2=o.copy(); v2=v.copy(); o2[-xf:]*=np.linspace(1,0,xf); v2[:xf]*=np.linspace(0,1,xf)
        return np.concatenate([o2[:-xf], o2[-xf:]+v2[:xf], v2[xf:]])
    return np.concatenate([o,v])

def sing_line(text, root, line_idx, tmp, phrasing):
    """PER-WORD: TTS each word alone (crisp diction, clean boundaries) -> map onto melody/rhythm."""
    words=[w for w in text.split() if w.strip()]
    rng=np.random.RandomState(1000+line_idx)
    notes=walk_notes(60, phrasing["interval_samples"], root, rng)       # long walk, indexed per syllable
    dsamp=np.array(phrasing["dur_samples"]); dhi=dsamp[dsamp>=np.percentile(dsamp,70)]
    drng=np.random.RandomState(2000+line_idx)
    pieces=[]; ni=0; prev_hz=0.0; sr=FSv
    for wi,w in enumerate(words):
        mp3=os.path.join(tmp,f"w{line_idx}_{wi}.mp3"); asyncio.run(tts_line(w,"hi-IN-MadhurNeural",mp3))
        x,sr=load_wav(mp3)
        if len(x)<sr*0.05: continue
        f0,t=pw.harvest(x,sr,frame_period=FP*1000); sp=pw.cheaptrick(x,f0,t,sr); ap=pw.d4c(x,f0,t,sr)
        syl=syllabify_audio(f0,sp)
        if not syl: continue
        prev_b=0
        for k,(a,b) in enumerate(syl):
            hz=vb.midi2hz(notes[min(ni,len(notes)-1)])
            last=(wi==len(words)-1 and k==len(syl)-1)
            dur=float(drng.choice(dhi if last else dsamp))
            if a>prev_b:                                                # word's leading/unvoiced consonants
                g=wsynth(f0[prev_b:a],sp[prev_b:a],ap[prev_b:a],sr); g=g/(np.max(np.abs(g))+1e-9)*0.75
                pieces.append(g)
            pieces.append(build_syllable(f0,sp,ap,sr,a,b,hz,dur,prev_hz))
            prev_b=b; prev_hz=hz; ni+=1
        pieces.append(np.zeros(int(0.09*sr)))                          # small gap between words
    return np.concatenate(pieces) if pieces else np.zeros(int(0.2*sr))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lyrics",required=True); ap.add_argument("--phrasing",required=True)
    ap.add_argument("--root",type=int,default=45); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    import json; phrasing=json.load(open(a.phrasing))
    lines=[l.strip() for l in open(a.lyrics,encoding="utf-8") if l.strip() and not l.strip().startswith("[")]
    tmp=tempfile.mkdtemp(prefix="hsb_"); pieces=[]
    for i,ln in enumerate(lines):
        print(f"[bank] line {i+1}/{len(lines)}: {ln[:36]}",flush=True)
        y=sing_line(ln,a.root,i,tmp,phrasing)
        na=int(0.04*FSv); nr=int(0.14*FSv)
        if len(y)>na+nr: y[:na]*=np.linspace(0,1,na); y[-nr:]*=np.linspace(1,0,nr)
        pieces.append(y); pieces.append(np.zeros(int(0.18*FSv)))
    out=np.concatenate(pieces); out=out/(np.max(np.abs(out))+1e-9)*0.9
    sf.write(a.out, out.astype(np.float32), FSv)
    print(f"[bank] wrote {a.out}  {len(out)/FSv:.1f}s")

if __name__=="__main__": main()
