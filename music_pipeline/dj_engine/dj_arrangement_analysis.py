#!/usr/bin/env python3
"""dj_arrangement_analysis.py — reverse-engineer a DJ/track's ARRANGEMENT.

Reads a full track and maps, over time, which sonic ELEMENTS (sub / kick+bass /
bassline / drone / stab / hats) are active — producing the "sequencing grid" that
shows how the DJ introduces, drops, and recombines elements across the whole track.
This is the teacher signal for our arrangement-learning engine.

Usage: python3 dj_arrangement_analysis.py --in TRACK.mp3 --out report.md [--bin 20]
Runs on the EC2 box (librosa).
"""
import argparse, numpy as np, librosa, warnings, json, os
warnings.filterwarnings("ignore")

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", default=None, help="markdown report path")
ap.add_argument("--json", default=None, help="machine-readable timeline path")
ap.add_argument("--bin", type=float, default=20.0, help="timeline bin seconds")
a = ap.parse_args()

SR = 22050
print(f"loading {a.inp} ...", flush=True)
y, sr = librosa.load(a.inp, sr=SR, mono=True)
dur = len(y) / sr

# ---- element bands (Hz) ----
BANDS = [("sub", 20, 60), ("kick+bass", 60, 150), ("bassline", 150, 400),
         ("drone", 400, 900), ("stab", 900, 3000), ("hats", 3000, 9000)]
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
frame_t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=512)

# per-band energy over time
band_e = {}
for n, lo, hi in BANDS:
    m = (fr >= lo) & (fr < hi)
    band_e[n] = S[m].mean(axis=0) if m.any() else np.zeros(S.shape[1])
rms = librosa.feature.rms(y=y, hop_length=512)[0]
cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)

# ---- bin into timeline ----
nbins = int(np.ceil(dur / a.bin))
def binned(arr):
    out = np.zeros(nbins)
    for i in range(nbins):
        m = (frame_t >= i*a.bin) & (frame_t < (i+1)*a.bin)
        out[i] = arr[m].mean() if m.any() else 0.0
    return out
B = {n: binned(band_e[n]) for n, _, _ in BANDS}
Brms = binned(rms); Bcent = binned(cent); Bons = binned(oenv)

# normalize each band 0..1 by its own 95th pct (so "present" = active for THAT element)
def norm(x):
    p = np.percentile(x, 95) or 1.0
    return np.clip(x / p, 0, 1)
Bn = {n: norm(B[n]) for n, _, _ in BANDS}
rms_n = norm(Brms)

# ---- element-presence grid (rows=elements, cols=time bins) ----
LV = " ▁▂▃▄▅▆▇█"
def row(x): return "".join(LV[min(8, int(v*8.0))] for v in x)
print(f"\n=== ELEMENT SEQUENCING GRID  ({a.bin:.0f}s/col, {dur/60:.1f} min) ===")
hdr = "".join(str(int(i*a.bin/60)%10) if (i*a.bin)%60==0 else " " for i in range(nbins))
lines = [f"{'min':>10s} |{hdr}"]
for n, _, _ in BANDS:
    lines.append(f"{n:>10s} |{row(Bn[n])}")
lines.append(f"{'ENERGY':>10s} |{row(rms_n)}")
print("\n".join(lines))

# ---- detect section boundaries: big changes in the element vector ----
feat = np.vstack([Bn[n] for n, _, _ in BANDS]).T   # bins x 6
d = np.r_[0, np.linalg.norm(np.diff(feat, axis=0), axis=1)]
thr = np.percentile(d, 80)
bounds = [0] + [i for i in range(1, nbins) if d[i] > thr] + [nbins]
# merge tiny sections (<2 bins)
merged = [bounds[0]]
for b in bounds[1:]:
    if b - merged[-1] >= 2: merged.append(b)
if merged[-1] != nbins: merged.append(nbins)

def label(secfeat, energy):
    on = {n: secfeat[k] > 0.35 for k, (n, _, _) in enumerate(BANDS)}
    if energy < 0.30 and not on["kick+bass"]: return "INTRO/BREAKDOWN (ambient)"
    if not on["kick+bass"]: return "breakdown (no kick)"
    parts = [n for n in ["kick+bass","bassline","drone","stab","hats"] if on[n]]
    tag = "PEAK" if energy > 0.75 else ("build" if energy > 0.5 else "groove")
    return f"{tag}: " + "+".join(parts)

print(f"\n=== ARRANGEMENT SECTIONS ({len(merged)-1}) ===")
secrows = []
for i in range(len(merged)-1):
    s, e = merged[i], merged[i+1]
    sf = feat[s:e].mean(axis=0); en = rms_n[s:e].mean()
    t0 = s*a.bin; t1 = e*a.bin
    lab = label(sf, en)
    secrows.append({"start_s": round(t0,1), "end_s": round(t1,1),
                    "dur_s": round(t1-t0,1), "energy": round(float(en),2),
                    "elements": {n: round(float(sf[k]),2) for k,(n,_,_) in enumerate(BANDS)},
                    "label": lab})
    print(f"  {int(t0//60):2d}:{int(t0%60):02d}-{int(t1//60):2d}:{int(t1%60):02d} "
          f"({t1-t0:4.0f}s) E{en:.2f}  {lab}")

if a.out:
    with open(a.out, "w") as f:
        f.write(f"# Arrangement analysis — {os.path.basename(a.inp)}\n\n")
        f.write(f"- duration: {dur/60:.1f} min · bin: {a.bin:.0f}s · sections: {len(merged)-1}\n\n")
        f.write("## Element sequencing grid\n```\n" + "\n".join(lines) + "\n```\n\n")
        f.write("## Sections\n| time | dur | energy | label |\n|---|---|---|---|\n")
        for r in secrows:
            f.write(f"| {int(r['start_s']//60)}:{int(r['start_s']%60):02d} | {r['dur_s']:.0f}s | {r['energy']} | {r['label']} |\n")
    print(f"\nreport -> {a.out}")
if a.json:
    json.dump({"file": a.inp, "duration_s": dur, "bin_s": a.bin,
               "bands": [n for n,_,_ in BANDS], "sections": secrows}, open(a.json,"w"), indent=2)
    print(f"json -> {a.json}")
print("DONE")
