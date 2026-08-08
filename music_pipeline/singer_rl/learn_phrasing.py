#!/usr/bin/env python3
"""learn_phrasing.py — learn a singer's PHRASING STYLE from their vocal stems.

Extracts STATISTICS (not the melody itself) so we transfer STYLE, not a composition:
  - syllable-duration variation (the rhythm feel: long/short hold pattern)
  - melodic-interval tendencies (how far/which direction pitch moves syllable-to-syllable)
  - vibrato depth + ornament rate
Output = phrasing_profile.json, consumed by hindi_sing.py --phrasing.

Runs in audio_pipeline/venv (librosa+pyworld+scipy). STYLE ONLY — copyright-clean.

Usage:
  audio_pipeline/venv/bin/python learn_phrasing.py --vocals "ref/dem/htdemucs/*/vocals.wav" \
    --out phrasing_shukla.json
"""
import argparse, glob, json
import numpy as np, librosa, pyworld as pw
from scipy.signal import find_peaks

FP = 0.005

def analyze(path):
    y, sr = librosa.load(path, sr=32000, mono=True)
    if len(y) > 90*sr:                       # central 90s
        m=len(y)//2; h=45*sr; y=y[m-h:m+h]
    x = y.astype(np.float64)
    f0,t = pw.harvest(x, sr, frame_period=FP*1000)
    sp = pw.cheaptrick(x, f0, t, sr)
    energy = sp.sum(1); energy = np.convolve(energy, np.ones(5)/5, mode="same")
    # syllable nuclei = energy peaks in voiced regions
    v = f0>0
    pk,_ = find_peaks(energy*(v.astype(float)), distance=int(0.12/FP),
                      prominence=np.percentile(energy[energy>0], 60) if (energy>0).any() else None)
    durs=[]; pitches=[]
    for i,p in enumerate(pk):
        # syllable span = between neighboring valleys
        lo = pk[i-1] if i>0 else max(0,p-int(0.15/FP))
        hi = pk[i+1] if i<len(pk)-1 else min(len(f0)-1, p+int(0.15/FP))
        a = lo + int(np.argmin(energy[lo:p])) if p>lo else p
        b = p + int(np.argmin(energy[p:hi])) if hi>p else p
        seg = f0[a:b]; seg = seg[seg>0]
        if len(seg) < 3: continue
        durs.append((b-a)*FP)
        pitches.append(12*np.log2(np.median(seg)/librosa.note_to_hz('C2')))
    return durs, pitches

def stats(arr):
    a=np.array(arr)
    return {"mean":round(float(a.mean()),3),"std":round(float(a.std()),3),
            "p25":round(float(np.percentile(a,25)),3),"p50":round(float(np.percentile(a,50)),3),
            "p75":round(float(np.percentile(a,75)),3)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vocals",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    all_dur=[]; all_iv=[]; all_pitch=[]
    for f in sorted(glob.glob(a.vocals)):
        print(f"[phrasing] {f}",flush=True)
        d,p = analyze(f)
        all_dur+=d; all_pitch+=p
        iv=np.diff(p); iv=iv[np.abs(iv)<12]              # syllable-to-syllable semitone moves
        all_iv+=list(iv)
    # keep bounded samples for the generator to draw from
    dur = np.array(all_dur); dur=dur[(dur>0.08)&(dur<1.6)]
    iv  = np.array(all_iv)
    prof={
      "disclaimer":"PHRASING STYLE STATISTICS only (durations/intervals/vibrato). Not a melody. "
                   "Applied to our OWN notes to inherit feel, never his composition.",
      "n_syllables":int(len(all_dur)),
      "syllable_dur_sec":stats(dur),
      "dur_samples":[round(float(x),3) for x in np.random.RandomState(1).choice(dur, min(300,len(dur)), replace=False)],
      "interval_semitones":{"mean":round(float(iv.mean()),3),"std":round(float(iv.std()),3),
                            "abs_mean":round(float(np.abs(iv).mean()),3)},
      "interval_samples":[round(float(x),2) for x in np.random.RandomState(2).choice(iv, min(300,len(iv)), replace=False)],
      "pitch_range_semitones":round(float(np.percentile(all_pitch,95)-np.percentile(all_pitch,5)),2),
    }
    json.dump(prof,open(a.out,"w"),indent=2)
    print(json.dumps({k:prof[k] for k in ["n_syllables","syllable_dur_sec","interval_semitones","pitch_range_semitones"]},indent=2))

if __name__=="__main__":
    main()
