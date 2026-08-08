#!/usr/bin/env python3
"""build_style_rubric.py — Stage 0 of the singer-RL loop.

Extracts MEASURABLE *style features* from a reference track (a teacher, e.g. a
Tanishk Shukla / 90s-Bollywood performance) into a rubric the RL critic scores
against. We learn STYLE ONLY — tempo, key, ornamentation, phrasing, mood, mix
character. We never store or reuse the melody/lyrics/recording. Copyright-clean.

Runs in the EC2 audio_pipeline venv (librosa+soundfile+scipy). Optionally takes a
Demucs-separated vocal stem to compute vocal-specific ornamentation.

Usage:
  audio_pipeline/venv/bin/python build_style_rubric.py \
    --mix ref/shukla_tupyaar.mp3 --vocal ref/vocals.wav \
    --name shukla_90s --out rubric_shukla_90s.json --md RUBRIC_shukla_90s.md
"""
import argparse, json, os, sys
import numpy as np
import librosa

def _pct(x, p): return float(np.percentile(x, p)) if len(x) else 0.0

def analyze_mix(path):
    y, sr = librosa.load(path, sr=44100, mono=True)
    dur = len(y) / sr
    # tempo (fold octave-errors into a musical 70-140 band — librosa often 2x/0.5x)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    while tempo > 140: tempo /= 2.0
    while tempo < 70:  tempo *= 2.0
    # key / scale via chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    root = int(np.argmax(chroma_mean))
    # major vs minor: compare thirds
    maj_third = chroma_mean[(root+4) % 12]; min_third = chroma_mean[(root+3) % 12]
    mode = 'minor' if min_third >= maj_third else 'major'
    # brightness / warmth
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0]
    # dynamics / energy arc — measure over ACTIVE frames only (silence inflates range)
    rms = librosa.feature.rms(y=y)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-6)
    active = rms_db > (rms_db.max() - 40.0)
    rdb = rms_db[active] if active.sum() > 10 else rms_db
    dyn_range = float(_pct(rdb, 95) - _pct(rdb, 5))
    # percussion density (onset rate) -> tabla/dholak busy-ness proxy
    onset = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    onset_rate = float(len(onset) / dur) if dur else 0.0
    # harmonic/percussive balance -> acoustic vs beat-driven
    yh, yp = librosa.effects.hpss(y)
    hp_ratio = float(np.sum(yh**2) / (np.sum(yp**2) + 1e-9))
    # energy arc: normalized rms over 8 segments (mood build)
    seg = np.array_split(rms, 8)
    arc = [float(np.mean(s)) for s in seg]
    m = max(arc) or 1.0; arc = [round(a/m, 3) for a in arc]
    return {
        "duration_sec": round(dur, 1),
        "tempo_bpm": round(tempo, 1),
        "key": f"{NOTES[root]} {mode}",
        "brightness_centroid_hz": round(float(np.median(cent)), 1),
        "rolloff85_hz": round(float(np.median(rolloff)), 1),
        "dynamic_range_db": round(dyn_range, 1),
        "onset_rate_per_sec": round(onset_rate, 2),
        "harmonic_percussive_ratio": round(hp_ratio, 2),
        "energy_arc_8": arc,
    }

def analyze_vocal(path, win_sec=90):
    # lower sr + central window keeps pyin fast; ample for STYLE features
    y, sr = librosa.load(path, sr=22050, mono=True)
    if len(y) > win_sec * sr:
        mid = len(y) // 2; half = (win_sec * sr) // 2
        y = y[mid - half: mid + half]
    # f0 via pyin (male-ish + female duet range)
    f0, vflag, vprob = librosa.pyin(y, fmin=80, fmax=800, sr=sr, frame_length=2048)
    voiced = f0[~np.isnan(f0)]
    if len(voiced) < 10:
        return {"note": "insufficient voiced frames"}
    voiced_frac = float(np.mean(~np.isnan(f0)))
    semis = 12 * np.log2(voiced / librosa.note_to_hz('C2'))
    pitch_range_semi = float(_pct(semis, 95) - _pct(semis, 5))
    # ornamentation: rate of pitch-direction changes per voiced second (murki/melisma)
    df = np.diff(voiced)
    sign_changes = np.sum(np.diff(np.sign(df)) != 0)
    voiced_sec = len(voiced) * (512 / sr)  # hop 512 default
    ornament_rate = float(sign_changes / voiced_sec) if voiced_sec else 0.0
    # glide (meend): median absolute semitone change per frame
    dsemi = np.abs(np.diff(semis))
    glide_semi_per_frame = float(np.median(dsemi))
    # vibrato proxy: std of f0 within short windows
    vib = float(np.median([np.std(semis[i:i+20]) for i in range(0, len(semis)-20, 20)] or [0]))
    return {
        "voiced_fraction": round(voiced_frac, 3),
        "pitch_range_semitones": round(pitch_range_semi, 1),
        "median_f0_hz": round(float(np.median(voiced)), 1),
        "ornament_rate_per_sec": round(ornament_rate, 2),
        "glide_semitone_per_frame": round(glide_semi_per_frame, 3),
        "vibrato_semitone_std": round(vib, 3),
    }

def _agg(dicts):
    """mean + [min,max] range across a list of feature dicts (numeric keys only)."""
    out = {}
    keys = [k for k in dicts[0] if isinstance(dicts[0][k], (int, float))]
    for k in keys:
        vals = [d[k] for d in dicts if isinstance(d.get(k), (int, float))]
        if vals:
            out[k] = round(float(np.mean(vals)), 3)
            out[k + "_range"] = [round(min(vals), 3), round(max(vals), 3)]
    # energy_arc: element-wise mean
    arcs = [d.get("energy_arc_8") for d in dicts if d.get("energy_arc_8")]
    if arcs:
        out["energy_arc_8"] = [round(float(np.mean(c)), 3) for c in zip(*arcs)]
    # modal string key
    strkeys = [k for k in dicts[0] if isinstance(dicts[0][k], str)]
    for k in strkeys:
        vals = [d.get(k) for d in dicts if isinstance(d.get(k), str)]
        if vals:
            out[k] = max(set(vals), key=vals.count)
            out[k + "_all"] = vals
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mix", nargs="+", required=True, help="one or more reference mixes")
    ap.add_argument("--vocal", nargs="*", default=[], help="matching vocal stems (same order)")
    ap.add_argument("--name", default="style")
    ap.add_argument("--source-title", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    a = ap.parse_args()

    per_track = []
    mixes, vocs = [], []
    for i, mpath in enumerate(a.mix):
        print(f"[rubric] analyzing mix {i+1}/{len(a.mix)}: {mpath}", flush=True)
        mrow = analyze_mix(mpath); mixes.append(mrow)
        vrow = {}
        vpath = a.vocal[i] if i < len(a.vocal) else None
        if vpath and os.path.exists(vpath):
            print(f"[rubric]   vocal stem: {vpath}", flush=True)
            vrow = analyze_vocal(vpath); vocs.append(vrow)
        per_track.append({"mix": mpath, "mix_features": mrow, "vocal_features": vrow})

    mix = _agg(mixes) if len(mixes) > 1 else mixes[0]
    voc = (_agg(vocs) if len(vocs) > 1 else (vocs[0] if vocs else {}))

    rubric = {
        "name": a.name,
        "source_title": a.source_title,
        "n_reference_tracks": len(a.mix),
        "disclaimer": "STYLE FEATURES ONLY. Melody/lyrics/recording NOT stored or reused. "
                      "Used solely as an RL reward yardstick; output uses original content + owned voice.",
        "mix": mix, "vocal": voc, "per_track": per_track,
    }
    with open(a.out, "w") as f: json.dump(rubric, f, indent=2)

    L = []
    L.append(f"# Style Rubric — {a.name}\n")
    if a.source_title: L.append(f"*Style reference:* {a.source_title}  \n")
    L.append(f"> {rubric['disclaimer']}\n")
    L.append("## Musical fingerprint (the reward targets)\n")
    L.append(f"- **Tempo:** {mix['tempo_bpm']} BPM")
    L.append(f"- **Key:** {mix['key']}")
    L.append(f"- **Duration:** {mix['duration_sec']} s")
    L.append(f"- **Brightness (centroid):** {mix['brightness_centroid_hz']} Hz  "
             f"(rolloff85 {mix['rolloff85_hz']} Hz) — mix warmth/air")
    L.append(f"- **Dynamic range:** {mix['dynamic_range_db']} dB — emotional swell room")
    L.append(f"- **Percussion density:** {mix['onset_rate_per_sec']} onsets/s — tabla/dholak busy-ness")
    L.append(f"- **Harmonic/percussive ratio:** {mix['harmonic_percussive_ratio']} — acoustic-melodic vs beat-driven")
    L.append(f"- **Energy arc (8 seg):** {mix['energy_arc_8']} — how the mood builds\n")
    if voc:
        L.append("## Vocal ornamentation (the singing *manner*)\n")
        L.append(f"- **Voiced fraction:** {voc.get('voiced_fraction')} — how much of the track is sung")
        L.append(f"- **Pitch range:** {voc.get('pitch_range_semitones')} semitones — expressive span")
        L.append(f"- **Median f0:** {voc.get('median_f0_hz')} Hz — register (duet, mixed M/F)")
        L.append(f"- **Ornament rate:** {voc.get('ornament_rate_per_sec')} /s — murki/melisma density")
        L.append(f"- **Glide (meend):** {voc.get('glide_semitone_per_frame')} semi/frame — sliding between notes")
        L.append(f"- **Vibrato:** {voc.get('vibrato_semitone_std')} semi std — sustained-note wobble\n")
    L.append("## How the RL critic uses this\n")
    L.append("Each generated take (original melody+lyrics, sung in the owned voice) is scored on "
             "how close its measured features sit to these targets — tempo/feel, ornament density, "
             "glide, brightness, energy arc, dynamic range. A weighted distance → a single style-score "
             "(0–10), the 'have-we-reached-it-yet' signal. Best-of-N keeps the high scorers; the "
             "generator is nudged toward them. **The reference's actual notes are never a target.**\n")
    with open(a.md, "w") as f: f.write("\n".join(L))
    print(f"[rubric] wrote {a.out} + {a.md}", flush=True)
    print(json.dumps(rubric, indent=2))

if __name__ == "__main__":
    main()
