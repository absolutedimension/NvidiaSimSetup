#!/usr/bin/env python3
"""singerize.py — M2 step. Re-sing a song's vocal in one of our owned AI singers.
Runs on the EC2 box with m2_venv (demucs + seed-vc) + ffmpeg.

Pipeline: input song -> Demucs (split vocal/instrumental) -> seed-vc convert vocal
to <singer> -> remix with instrumental -> loudness master -> MP3.

Singers (persistent reference identities) live in /home/ubuntu/singers/<name>_ref.wav:
  maya = female   |   ravi = male   (add more by dropping a clean ref clip there)

Usage:
  m2_venv/bin/python singerize.py --input song.wav --singer maya --out out.mp3
"""
import argparse, os, subprocess, glob, sys

M2 = "/home/ubuntu/m2_venv/bin/python"
SEEDVC = "/home/ubuntu/seed-vc/inference.py"
SINGERS = "/home/ubuntu/singers"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1500:]); raise RuntimeError(f"failed: {cmd}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="song WAV (with vocals)")
    ap.add_argument("--singer", required=True, help="maya | ravi | <name in /home/ubuntu/singers>")
    ap.add_argument("--out", required=True, help="final mp3")
    ap.add_argument("--work", default="/home/ubuntu/m2_work")
    ap.add_argument("--steps", type=int, default=30, help="seed-vc diffusion steps")
    ap.add_argument("--cfg", type=float, default=0.7, help="seed-vc inference cfg rate")
    ap.add_argument("--semitone", type=int, default=0, help="pitch shift (semitones)")
    ap.add_argument("--voc-gain", type=float, default=1.1)
    ap.add_argument("--inst-gain", type=float, default=0.9)
    ap.add_argument("--lufs", type=float, default=-15.0)
    ap.add_argument("--vocal-only", action="store_true")
    a = ap.parse_args()

    ref = os.path.join(SINGERS, f"{a.singer}_ref.wav")
    if not os.path.exists(ref):
        ap.error(f"no singer ref: {ref}")
    base = os.path.splitext(os.path.basename(a.input))[0]
    wd = os.path.join(a.work, f"sing_{base}_{a.singer}")
    os.makedirs(wd, exist_ok=True)

    # 1. Demucs split
    print(f"[sing] demucs splitting {base}...", flush=True)
    sh(f'{M2} -m demucs --two-stems vocals -n htdemucs -o "{wd}/dem" "{a.input}"')
    voc = glob.glob(f"{wd}/dem/htdemucs/*/vocals.wav")[0]
    inst = glob.glob(f"{wd}/dem/htdemucs/*/no_vocals.wav")[0]

    # 2. seed-vc convert vocal -> singer
    print(f"[sing] converting vocal -> {a.singer}...", flush=True)
    vcout = f"{wd}/vc"
    os.makedirs(vcout, exist_ok=True)
    sh(f'cd /home/ubuntu/seed-vc && {M2} {SEEDVC} --source "{voc}" --target "{ref}" '
       f'--output "{vcout}" --diffusion-steps {a.steps} --length-adjust 1.0 '
       f'--inference-cfg-rate {a.cfg} --f0-condition True --auto-f0-adjust True '
       f'--semi-tone-shift {a.semitone}')
    sung = glob.glob(f"{vcout}/*.wav")[0]

    # 3. remix + master
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    if a.vocal_only:
        sh(f'ffmpeg -y -i "{sung}" -af "loudnorm=I={a.lufs}:TP=-1.5:LRA=11" -b:a 192k "{a.out}"')
    else:
        sh(f'ffmpeg -y -i "{sung}" -i "{inst}" -filter_complex '
           f'"[0:a]volume={a.voc_gain}[v];[1:a]volume={a.inst_gain}[i];'
           f'[v][i]amix=inputs=2:duration=longest:normalize=0[m];'
           f'[m]loudnorm=I={a.lufs}:TP=-1.5:LRA=11[out]" -map "[out]" -b:a 192k "{a.out}"')
    print(f"[sing] DONE -> {a.out}", flush=True)


if __name__ == "__main__":
    main()
