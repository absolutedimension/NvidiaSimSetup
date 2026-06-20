#!/usr/bin/env python3
"""make_music.py — TrigunAI M1 music pipeline (runs in ~/acestep_venv on the EC2 box).

One command: generate -> extend to any length (unique segments + seamless crossfades)
-> optional isochronic tones / 432Hz tuning -> loudness master -> WAV + MP3.

Examples:
  make_music.py --style focus-house --freq beta --minutes 30 --out study.mp3
  make_music.py --style meditation-432 --minutes 20 --out morning.mp3
  make_music.py --style ghazal --lyrics-file couplets.txt --ref ref.wav --minutes 4 --out ghazal.mp3
"""
import argparse, os, subprocess, sys, time, math, tempfile

# ---------- style presets ----------
PRESETS = {
    "focus-house": dict(
        prompt="upbeat deep house, study focus music, four on the floor groove, steady 122 bpm, "
               "warm analog synth, melodic plucks, driving bassline, hypnotic, bright, instrumental, no vocals, clean mix",
        lyrics="[inst]", lufs=-14.0, tune432=False),
    "meditation-432": dict(
        prompt="indian classical meditation, raga, tanpura drone, bansuri flute, soft santoor, slow, calm, "
               "peaceful, ambient, spiritual, serene, morning, instrumental, no vocals",
        lyrics="[inst]", lufs=-16.0, tune432=True),
    "sitar-heal": dict(
        prompt="indian classical, sitar lead, sarangi, gentle tabla, slow, soothing, meditative, deep relaxation, "
               "ambient, calming, raga, instrumental, no vocals",
        lyrics="[inst]", lufs=-16.0, tune432=False),
    "techno-hypnotic": dict(
        prompt="hypnotic techno, driving four-on-the-floor kick, rolling deep bassline, "
               "repetitive hypnotic groove, dark warehouse club, analog synth stabs, modular bleeps, "
               "slowly building tension and release, immersive, trance-inducing, ecstatic peak-time "
               "energy, continuous DJ set, propulsive, instrumental, no vocals",
        lyrics="[inst]", lufs=-12.0, tune432=False),
    "lofi": dict(
        prompt="lofi hip hop, chill study beats, mellow, warm vinyl, soft piano, boom bap drums, relaxed, "
               "instrumental, no vocals",
        lyrics="[inst]", lufs=-14.0, tune432=False),
    "ambient": dict(
        prompt="ambient drone, deep atmospheric pads, evolving textures, cinematic, calm, spacious, "
               "instrumental, no vocals",
        lyrics="[inst]", lufs=-16.0, tune432=False),
    "ghazal": dict(
        prompt="hindi ghazal, soulful female vocal, harmonium, tabla, sarangi, slow tempo, melancholic, "
               "emotional, intimate, acoustic, reverb, classical indian",
        lyrics="", lufs=-15.0, tune432=False),
    "pop": dict(
        prompt="uplifting electronic pop, female vocal, warm synth pads, 110 bpm, hopeful, cinematic, clean mix",
        lyrics="", lufs=-14.0, tune432=False),
}
ISO_FREQ = {"beta": 15.0, "alpha": 10.0, "theta": 6.0, "delta": 3.0}


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        raise RuntimeError(f"cmd failed: {cmd}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=list(PRESETS), help="preset")
    ap.add_argument("--prompt", help="override prompt")
    ap.add_argument("--lyrics", default=None)
    ap.add_argument("--lyrics-file", default=None)
    ap.add_argument("--minutes", type=float, default=3.0, help="target length")
    ap.add_argument("--seg-len", type=float, default=180.0, help="per-segment gen seconds")
    ap.add_argument("--unique", type=int, default=4, help="distinct segments to generate")
    ap.add_argument("--xfade", type=float, default=6.0, help="crossfade seconds between joins")
    ap.add_argument("--bpm", type=int, default=0, help="lock tempo (improves flow across joins)")
    ap.add_argument("--freq", choices=list(ISO_FREQ), help="isochronic entrainment band")
    ap.add_argument("--iso-db", type=float, default=-20.0, help="isochronic tone level (dB)")
    ap.add_argument("--tune432", action="store_true")
    ap.add_argument("--tune440", action="store_true", help="force off 432 even if preset sets it")
    ap.add_argument("--lufs", type=float, default=None)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--ref-strength", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=100)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--cpu-offload", action="store_true", help="lower VRAM (coexist with other GPU jobs); slower")
    ap.add_argument("--workdir", default="/home/ubuntu/music_out/_m1work")
    ap.add_argument("--out", required=True, help="final mp3 path")
    a = ap.parse_args()

    preset = PRESETS.get(a.style, {})
    prompt = a.prompt or preset.get("prompt")
    if not prompt:
        ap.error("need --style or --prompt")
    if a.bpm:
        # tempo lock => independently-generated segments stay beat-consistent, so
        # crossfade joins don't break the groove ("loses flow at some points")
        prompt = f"exactly {a.bpm} BPM, steady constant tempo, seamless continuous groove, " + prompt
    lyrics = a.lyrics if a.lyrics is not None else preset.get("lyrics", "[inst]")
    if a.lyrics_file:
        lyrics = open(a.lyrics_file, encoding="utf-8").read()
    lufs = a.lufs if a.lufs is not None else preset.get("lufs", -14.0)
    tune432 = (preset.get("tune432", False) or a.tune432) and not a.tune440

    os.makedirs(a.workdir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    target_s = a.minutes * 60.0

    # ---------- 1. load model once, generate unique segments ----------
    from acestep.pipeline_ace_step import ACEStepPipeline
    print(f"[m1] style={a.style} target={a.minutes}min freq={a.freq} 432={tune432}", flush=True)
    t0 = time.time()
    pipe = ACEStepPipeline(checkpoint_dir="", dtype="bfloat16", cpu_offload=a.cpu_offload)
    print(f"[m1] model ready in {time.time()-t0:.1f}s", flush=True)

    n_unique = max(1, a.unique if target_s > a.seg_len else 1)
    seg_paths = []
    for i in range(n_unique):
        seg = os.path.join(a.workdir, f"seg_{i}.wav")
        kw = dict(format="wav", audio_duration=a.seg_len, prompt=prompt, lyrics=lyrics,
                  infer_step=a.steps, guidance_scale=15.0,
                  guidance_scale_lyric=2.5 if lyrics not in ("", "[inst]") else 0.0,
                  manual_seeds=[a.seed + i * 7], save_path=seg, batch_size=1)
        if a.ref:
            kw.update(audio2audio_enable=True, ref_audio_input=a.ref, ref_audio_strength=a.ref_strength)
        ts = time.time()
        pipe(**kw)
        print(f"[m1] seg {i+1}/{n_unique} in {time.time()-ts:.1f}s", flush=True)
        seg_paths.append(seg)

    # ---------- 2. build playlist (repeat sequence) & crossfade-concat ----------
    if len(seg_paths) == 1 and target_s <= a.seg_len:
        long_wav = seg_paths[0]
    else:
        # repeat the unique sequence enough to exceed target (account for xfade loss)
        eff_seg = a.seg_len - a.xfade
        reps = math.ceil(target_s / (eff_seg * n_unique)) + 1
        playlist = (seg_paths * reps)
        # cap inputs to keep ffmpeg sane
        playlist = playlist[:max(2, math.ceil(target_s / eff_seg) + 1)]
        print(f"[m1] crossfading {len(playlist)} segments (xfade={a.xfade}s)...", flush=True)
        inputs = " ".join(f'-i "{p}"' for p in playlist)
        # chained acrossfade
        fc, prev = [], "0"
        for k in range(1, len(playlist)):
            out = f"a{k}"
            fc.append(f"[{prev}][{k}]acrossfade=d={a.xfade}:c1=tri:c2=tri[{out}]"
                      if prev.isdigit() else f"[{prev}][{k}]acrossfade=d={a.xfade}:c1=tri:c2=tri[{out}]")
            prev = out
        long_wav = os.path.join(a.workdir, "long.wav")
        filt = ";".join(fc)
        sh(f'ffmpeg -y {inputs} -filter_complex "{filt}" -map "[{prev}]" "{long_wav}"')

    # ---------- 3. trim to exact target ----------
    trimmed = os.path.join(a.workdir, "trimmed.wav")
    sh(f'ffmpeg -y -i "{long_wav}" -t {target_s:.2f} "{trimmed}"')

    # ---------- 4. tuning (432Hz) ----------
    tuned = trimmed
    if tune432:
        tuned = os.path.join(a.workdir, "tuned.wav")
        sh(f'ffmpeg -y -i "{trimmed}" -af "rubberband=pitch=0.981818" "{tuned}"')
        print("[m1] applied 432Hz tuning", flush=True)

    # ---------- 5. optional isochronic layer + 6. master ----------
    master_af = f"loudnorm=I={lufs}:TP=-1.5:LRA=11"
    if a.freq:
        f = ISO_FREQ[a.freq]
        # 210Hz carrier gated at f Hz, low level, mixed under the track, then loudnorm
        sh(f'ffmpeg -y -i "{tuned}" -f lavfi -i "sine=frequency=210:sample_rate=48000:duration={target_s:.2f}" '
           f'-filter_complex "[1:a]tremolo=f={f}:d=1.0,volume={a.iso_db}dB[iso];'
           f'[0:a][iso]amix=inputs=2:duration=first:normalize=0[m];[m]{master_af}[out]" '
           f'-map "[out]" "{a.out}.master.wav"')
        print(f"[m1] mixed {a.freq} ({f}Hz) isochronic tones", flush=True)
    else:
        sh(f'ffmpeg -y -i "{tuned}" -af "{master_af}" "{a.out}.master.wav"')

    sh(f'ffmpeg -y -i "{a.out}.master.wav" -b:a 192k "{a.out}"')
    dur = sh(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{a.out}"').strip()
    print(f"[m1] DONE -> {a.out}  ({float(dur)/60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
