#!/usr/bin/env python3
"""hindi_sing.py — pronunciation-first Hindi singing (Azure/edge-TTS -> WORLD melody-warp).

Words come from edge-tts hi-IN-MadhurNeural (correct diction by construction). We keep the
formants (=the words) and REPLACE pitch with a composed minor-key melody via the WORLD vocoder,
stretching voiced vowels to sustain on each note. Result: real Hindi words, sung. Copyright-clean.

Runs in audio_pipeline/venv (edge_tts + pyworld + librosa + soundfile).

Usage:
  audio_pipeline/venv/bin/python hindi_sing.py --lyrics lyrics/tu_nahin_toh.txt \
    --bpm 92 --out sung.wav [--voice hi-IN-MadhurNeural]
"""
import argparse, asyncio, os, subprocess, tempfile
import numpy as np, soundfile as sf, librosa, pyworld as pw
from scipy.signal import find_peaks
import edge_tts

FP = 0.005                       # WORLD frame period (s)
SCALE = [0,2,3,5,7,8,10,12,14]   # natural minor scale degrees (semitones)
# per-line melodic phrases as indices into SCALE (rise-fall shapes)
PHRASES = [
    [0,2,3,2,4,3,2,0],
    [2,3,4,3,5,4,3,2],
    [4,3,2,3,2,1,0,0],
    [0,1,2,4,3,2,1,0],
]

async def tts_line(text, voice, mp3):
    comm = edge_tts.Communicate(text, voice, rate="-12%")
    marks=[]; f=open(mp3,"wb")
    async for ch in comm.stream():
        if ch["type"]=="audio": f.write(ch["data"])
        elif ch["type"]=="WordBoundary":
            marks.append({"t":ch["offset"]/1e7,"dur":ch["duration"]/1e7,"w":ch["text"]})
    f.close(); return marks

def load_wav(mp3):
    wav = mp3[:-4]+".wav"
    subprocess.run(["ffmpeg","-y","-i",mp3,"-ar","32000","-ac","1",wav],
                   capture_output=True)
    y,sr = sf.read(wav); return y.astype(np.float64), sr

def midi2hz(m): return 440.0*2**((m-69)/12.0)

def interp_frames(mat, idx):
    """linear-interpolate spectral frames at fractional indices (smooth, no stepping)"""
    i0 = np.floor(idx).astype(int); i1 = np.minimum(i0+1, len(mat)-1)
    fr = (idx - i0)[:, None]
    return mat[i0]*(1-fr) + mat[i1]*fr

def phrase_notes(n_words, phrase, root):
    """resample a phrase (scale indices) to n_words notes -> midi list"""
    idx = np.linspace(0, len(phrase)-1, max(n_words,1))
    notes=[]
    for x in idx:
        deg = phrase[int(round(x))]
        notes.append(root + SCALE[deg % len(SCALE)] + 12*(deg//len(SCALE)))
    return notes

MINOR = [0,2,3,5,7,8,10]
def snap_scale(m, root):
    rel = m-root; oc = rel//12; deg = rel%12
    near = min(MINOR+[12], key=lambda s: abs(s-deg))
    return root + 12*oc + near

def walk_notes(n, intervals, root, rng, span=17):
    """melody as a random walk using the LEARNED interval distribution (his movement, not his song)"""
    notes=[]; cur = root + 3
    for _ in range(n):
        notes.append(snap_scale(int(round(cur)), root))
        cur = cur + float(rng.choice(intervals))
        cur = min(max(cur, root), root+span)
    return notes

def voiced_runs(f0, min_frames=4):
    """contiguous f0>0 spans = syllable nuclei (edge-tts gives no Hindi word marks)"""
    v = f0>0; runs=[]; i=0; N=len(f0)
    while i<N:
        if v[i]:
            j=i
            while j<N and v[j]: j+=1
            if j-i>=min_frames: runs.append((i,j))
            i=j
        else: i+=1
    return runs

def sing_line(text, voice, root, bpm, line_idx, tmp, base=0.6, phrasing=None):
    mp3 = os.path.join(tmp, f"l{line_idx}.mp3")
    asyncio.run(tts_line(text, voice, mp3))
    x, sr = load_wav(mp3)
    if len(x) < sr*0.1: return np.zeros(int(0.2*sr)), sr
    f0,t = pw.harvest(x, sr, frame_period=FP*1000)
    sp = pw.cheaptrick(x, f0, t, sr); ap = pw.d4c(x, f0, t, sr)
    N = len(f0)
    runs = voiced_runs(f0)
    if not runs: return np.zeros(int(0.2*sr)), sr

    # split each voiced run into SYLLABLES via energy (vowel-nuclei) peaks -> even rhythm
    energy = sp.sum(1); energy = np.convolve(energy, np.ones(3)/3, mode="same")
    syllables=[]
    for (a,b) in runs:
        seg = energy[a:b]
        if b-a < int(0.18/FP):
            syllables.append((a,b)); continue
        pk,_ = find_peaks(seg, distance=int(0.09/FP), prominence=seg.max()*0.12)
        if len(pk) <= 1:
            syllables.append((a,b)); continue
        bnds=[a]
        for p1,p2 in zip(pk[:-1], pk[1:]):
            bnds.append(a + p1 + int(np.argmin(seg[p1:p2])))
        bnds.append(b)
        syllables += list(zip(bnds[:-1], bnds[1:]))

    beat = 60.0/bpm
    if phrasing:                                        # LEARNED phrasing (his rhythm + movement)
        rng = np.random.RandomState(1000+line_idx)
        notes = walk_notes(len(syllables), phrasing["interval_samples"], root, rng)
        dsamp = np.array(phrasing["dur_samples"]); dhi = dsamp[dsamp>=np.percentile(dsamp,70)]
        drng = np.random.RandomState(2000+line_idx)
    else:
        notes = phrase_notes(len(syllables), PHRASES[line_idx % len(PHRASES)], root)

    out_f0=[]; out_sp=[]; out_ap=[]; prev=0; prev_hz=0.0
    for k,(a,b) in enumerate(syllables):
        if a>prev:                                    # keep consonants/silence natural
            out_f0.append(np.zeros(a-prev)); out_sp.append(sp[prev:a]); out_ap.append(ap[prev:a])
        # ---- SINGING model: quick consonant/attack onset + SUSTAINED pure vowel ----
        run_len = b-a
        last = (k==len(syllables)-1)
        if phrasing:                                    # draw hold-time from HIS distribution
            tgt = float(drng.choice(dhi if last else dsamp))
        else:
            tgt = beat*(1.5 if last else 0.62)
        tgt_n = max(int(tgt/FP), run_len)               # never compress below natural
        attack_n = min(run_len, int(0.11/FP))           # more onset = clearer consonants
        core = np.arange(a+run_len//2, b)               # vowel steady-state = latter half
        if len(core) < 2: core = np.arange(max(a, b-2), b)
        sustain_n = max(tgt_n - attack_n, int(0.12/FP))
        # attack = natural onset frames
        aidx = np.linspace(a, a+attack_n-1, attack_n)
        att_sp = interp_frames(sp, aidx); att_ap = interp_frames(ap, aidx)
        # sustain = slow sweep THROUGH the steady vowel frames (held, alive but pure)
        cidx = a+run_len//2 + np.linspace(0, len(core)-1, sustain_n)
        sus_sp = interp_frames(sp, cidx); sus_ap = interp_frames(ap, cidx)
        seg_sp = np.vstack([att_sp, sus_sp]); seg_ap = np.vstack([att_ap, sus_ap])
        seg_n = attack_n + sustain_n
        # melody f0 across the whole (voiced) note: glide in, vibrato grows on the sustain
        hz = midi2hz(notes[k]); f0seg = np.full(seg_n, hz)
        gl = min(int(0.13/FP), seg_n//2)
        if prev_hz>0 and gl>1:   f0seg[:gl] = np.linspace(prev_hz, hz, gl)
        elif prev_hz==0 and gl>1: f0seg[:gl] = np.linspace(hz*0.94, hz, gl)
        tt = np.arange(seg_n)*FP
        rate = 5.2 + 0.5*np.sin(k*1.7)
        env = np.clip((tt-0.18)/0.4, 0, 1)*0.016
        f0seg = f0seg*(1.0 + env*np.sin(2*np.pi*rate*tt))
        out_f0.append(f0seg); out_sp.append(seg_sp); out_ap.append(seg_ap)
        prev=b; prev_hz=hz
    if prev<N:
        out_f0.append(np.zeros(N-prev)); out_sp.append(sp[prev:N]); out_ap.append(ap[prev:N])

    F0 = np.concatenate(out_f0); SP=np.concatenate(out_sp); AP=np.concatenate(out_ap)
    # glide (meend) across note boundaries: smooth voiced f0 a touch
    v = F0>0
    if v.sum()>5:
        sm = F0.copy()
        for _ in range(2):
            sm[1:-1] = np.where(v[1:-1], 0.25*sm[:-2]+0.5*sm[1:-1]+0.25*sm[2:], sm[1:-1])
        F0 = np.where(v, sm, 0.0)
    y = pw.synthesize(F0.astype(np.float64), SP.astype(np.float64), AP.astype(np.float64), sr, FP*1000)
    return y, sr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lyrics", required=True)
    ap.add_argument("--voice", default="hi-IN-MadhurNeural")
    ap.add_argument("--root", type=int, default=45, help="root MIDI note (A2=45)")
    ap.add_argument("--bpm", type=float, default=92)
    ap.add_argument("--phrasing", default=None, help="learned phrasing_profile.json (his feel)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import json
    phrasing = json.load(open(a.phrasing)) if a.phrasing else None
    lines = [l.strip() for l in open(a.lyrics, encoding="utf-8")
             if l.strip() and not l.strip().startswith("[")]
    tmp = tempfile.mkdtemp(prefix="hsing_")
    pieces=[]; sr=32000
    for i,ln in enumerate(lines):
        print(f"[sing] line {i+1}/{len(lines)}: {ln[:40]}", flush=True)
        y,sr = sing_line(ln, a.voice, a.root, a.bpm, i, tmp, phrasing=phrasing)
        # soft line-edge fades (de-chop the start/end of each phrase)
        na=int(0.045*sr); nr=int(0.16*sr)
        if len(y)>na+nr:
            y[:na]*=np.linspace(0,1,na); y[-nr:]*=np.linspace(1,0,nr)
        pieces.append(y); pieces.append(np.zeros(int(0.18*sr)))   # short rest between lines
    out = np.concatenate(pieces)
    out = out/(np.max(np.abs(out))+1e-9)*0.9
    sf.write(a.out, out.astype(np.float32), sr)
    print(f"[sing] wrote {a.out}  {len(out)/sr:.1f}s")

if __name__ == "__main__":
    main()
