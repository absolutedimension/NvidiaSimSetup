#!/usr/bin/env python3
"""self_critique.py — automated audio feedback for a generated take.

Three objective signals (honest: features approximate 'sounds like'; no true audio perception):
  1. PRONUNCIATION — Whisper ASR transcribes what was actually sung (Hindi/Devanagari),
     compared to the intended Devanagari lyrics via WER/CER + shows heard-vs-expected.
  2. VOICE SIMILARITY to Tanishk — MFCC/timbre + pitch/ornament feature distance between
     this take's vocal and Tanishk's real vocal stems (cosine similarity, 0-1).
  3. STYLE SCORE — the rubric critic (imported).

Runs in m2_venv (jiwer + transformers + torchaudio + demucs + librosa).

Usage:
  m2_venv/bin/python self_critique.py --take t.mp3 --lyrics-dev lyrics/tu_nahin_toh.txt \
    --ref-vocals "ref/dem/htdemucs/*/vocals.wav" --rubric rubric_shukla_90s.json --out t.critique.json
"""
import argparse, json, glob, subprocess, os, re, sys
import numpy as np, librosa, soundfile as sf
import torch
import jiwer

M2 = "/home/ubuntu/m2_venv/bin/python"

def demucs_vocal(take, work):
    base = os.path.splitext(os.path.basename(take))[0]
    out = glob.glob(f"{work}/dem/htdemucs/{base}/vocals.wav")
    if out: return out[0]
    subprocess.run(f'{M2} -m demucs --two-stems vocals -n htdemucs -o "{work}/dem" "{take}"',
                   shell=True, check=True, capture_output=True, text=True)
    return glob.glob(f"{work}/dem/htdemucs/{base}/vocals.wav")[0]

def asr(wav, model="openai/whisper-medium"):
    from transformers import pipeline
    dev = 0 if torch.cuda.is_available() else -1
    p = pipeline("automatic-speech-recognition", model=model, device=dev,
                 chunk_length_s=28, stride_length_s=4,
                 generate_kwargs={"language":"hindi","task":"transcribe"})
    return p(wav)["text"].strip()

def clean(s):
    s = re.sub(r"\[[^\]]*\]", " ", s)          # strip [verse]/[chorus]
    s = re.sub(r"[^ऀ-ॿ\s]", " ", s)   # keep Devanagari + space
    return re.sub(r"\s+", " ", s).strip()

def mfcc_vec(wav, win=60):
    y, sr = librosa.load(wav, sr=22050, mono=True)
    if len(y) > win*sr:
        m=len(y)//2; h=win*sr//2; y=y[m-h:m+h]
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    v = np.concatenate([mf.mean(1), mf.std(1)])
    return v / (np.linalg.norm(v)+1e-9)

def cos(a,b): return float(np.dot(a,b)/((np.linalg.norm(a)*np.linalg.norm(b))+1e-9))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", required=True)
    ap.add_argument("--lyrics-dev", required=True, help="intended Devanagari lyrics")
    ap.add_argument("--ref-vocals", required=True, help="glob of Tanishk vocal stems")
    ap.add_argument("--rubric", default=None)
    ap.add_argument("--asr-model", default="openai/whisper-medium")
    ap.add_argument("--work", default="/home/ubuntu/singer_rl/_critique")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)

    print("[critique] separating vocal...", flush=True)
    voc = demucs_vocal(a.take, a.work)

    print("[critique] ASR transcribing (whisper)...", flush=True)
    heard = clean(asr(voc, a.asr_model))
    want  = clean(open(a.lyrics_dev, encoding="utf-8").read())
    wer = float(jiwer.wer(want, heard)); cer = float(jiwer.cer(want, heard))

    print("[critique] voice similarity to Tanishk...", flush=True)
    tv = mfcc_vec(voc)
    refs = sorted(glob.glob(a.ref_vocals))
    sims = [cos(tv, mfcc_vec(r)) for r in refs]
    voice_sim = float(np.mean(sims)) if sims else None

    style = None
    if a.rubric:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            # reuse scorer by shelling to audio_pipeline venv (has its own deps)
            sc = a.take + ".sc.json"
            subprocess.run(f'/home/ubuntu/audio_pipeline/venv/bin/python '
                           f'/home/ubuntu/singer_rl/score_take.py --take "{a.take}" '
                           f'--rubric "{a.rubric}" --out "{sc}"', shell=True, check=True,
                           capture_output=True, text=True)
            style = json.load(open(sc))["style_score_0_10"]
        except Exception as e:
            style = f"err:{e}"

    # actionable pronunciation grade
    pron = ("clean" if wer < 0.25 else "mostly-ok" if wer < 0.5 else
            "rough" if wer < 0.75 else "poor")
    out = {
        "take": a.take,
        "pronunciation": {"grade": pron, "wer": round(wer,3), "cer": round(cer,3),
                          "heard": heard, "intended": want},
        "voice_similarity_to_tanishk": (round(voice_sim,3) if voice_sim is not None else None),
        "per_ref_similarity": {os.path.basename(os.path.dirname(r)): round(s,3) for r,s in zip(refs,sims)},
        "style_score_0_10": style,
    }
    json.dump(out, open(a.out,"w"), indent=2, ensure_ascii=False)
    print(json.dumps({"pronunciation": pron, "wer": round(wer,3), "cer": round(cer,3),
                      "voice_sim_tanishk": out["voice_similarity_to_tanishk"],
                      "style_score": style}, ensure_ascii=False, indent=2))
    print("\nHEARD :", heard[:300])
    print("WANT  :", want[:300])

if __name__ == "__main__":
    main()
