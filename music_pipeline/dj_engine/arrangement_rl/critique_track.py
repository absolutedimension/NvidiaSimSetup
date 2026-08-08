#!/usr/bin/env python3
"""
critique_track.py — the AUDIO CRITIC for the arrangement-RL loop.

Grades a generated track against a DJ's learned grammar, the SAME way we learned
the DJ (reuses the dj_arrangement_analysis.py band grid), plus objective audio
health. Returns a structured verdict — the machine half of the two-tier feedback
system (this = fast/objective/in-the-loop reward; the human ear = ground-truth taste).

Honest scope (the drone §17.10 lesson):
  - This is a PROXY, calibrated to your ear — not a replacement for it.
  - It reliably catches OBJECTIVE failures (no kick, clipping, wrong density, flat/
    dead arc, muddy/harsh spectrum) and measures grammar-match.
  - It CANNOT judge groove/feel/"does it slap". Those stay with the human gate.
  - Optional --vlm reasons over a spectrogram via gpt-4o-mini (LiteLLM proxy); that
    is a weak secondary signal, flagged as such, with a "if you can't tell, say so"
    preamble so it doesn't hallucinate quality (the drone blank-scene trap).

Runs on EC2 in ~/audio_pipeline/venv.
Usage:
  python3 critique_track.py --track burmeister_rl_6min.mp3 \
     --grammar ~/dj_engine/burmeister_grammar.json --bpm 123 \
     [--out verdict.json] [--vlm]
"""
import argparse, json, os, base64, numpy as np, librosa, warnings
warnings.filterwarnings("ignore")

BANDS = [("sub", 20, 60), ("kick+bass", 60, 150), ("bassline", 150, 400),
         ("drone", 400, 900), ("stab", 900, 3000), ("hats", 3000, 9000)]
ELEMENTS = [b[0] for b in BANDS]
THR = 0.35   # same "element on" cutoff dj_arrangement_analysis.py uses

ap = argparse.ArgumentParser()
ap.add_argument("--track", required=True)
ap.add_argument("--grammar", required=True)
ap.add_argument("--bin", type=float, default=20.0)
ap.add_argument("--bpm", type=float, default=None, help="expected BPM (for tempo check)")
ap.add_argument("--out", default=None)
ap.add_argument("--vlm", action="store_true", help="also get a gpt-4o-mini spectrogram opinion")
ap.add_argument("--proxy", default="http://172.31.32.216:4000/v1/chat/completions")
a = ap.parse_args()

SR = 22050
y, _ = librosa.load(a.track, sr=SR, mono=True)
dur = len(y) / SR

# ---- element grid (identical method to dj_arrangement_analysis.py) ----
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
fr = librosa.fft_frequencies(sr=SR, n_fft=2048)
frame_t = librosa.frames_to_time(np.arange(S.shape[1]), sr=SR, hop_length=512)
nbins = max(1, int(np.ceil(dur / a.bin)))
def binned(arr):
    out = np.zeros(nbins)
    for i in range(nbins):
        m = (frame_t >= i * a.bin) & (frame_t < (i + 1) * a.bin)
        out[i] = arr[m].mean() if m.any() else 0.0
    return out
def norm(x):
    p = np.percentile(x, 95) or 1.0
    return np.clip(x / p, 0, 1)
band_e = {}
for n, lo, hi in BANDS:
    m = (fr >= lo) & (fr < hi)
    band_e[n] = norm(binned(S[m].mean(axis=0) if m.any() else np.zeros(S.shape[1])))
rms = librosa.feature.rms(y=y, hop_length=512)[0]
rms_n = norm(binned(rms))
grid = np.vstack([band_e[n] for n in ELEMENTS]).T           # (nbins, 6), 0..1

# ---- generated-track stats ----
active = {n: float((grid[:, i] > THR).mean()) for i, n in enumerate(ELEMENTS)}
entry = {}
for i, n in enumerate(ELEMENTS):
    on = np.where(grid[:, i] > THR)[0]
    entry[n] = float(on[0] / nbins) if len(on) else 1.0
ki, bi, di = ELEMENTS.index("kick+bass"), ELEMENTS.index("bassline"), ELEMENTS.index("drone")
bd_rate = float(((grid[:, ki] < THR) & (grid[:, bi] > THR) & (grid[:, di] > THR)).mean())
gen_arc = rms_n

# ---- objective audio health ----
peak = float(np.max(np.abs(y)))
rms_all = float(np.sqrt(np.mean(y ** 2)) + 1e-9)
dbfs = 20 * np.log10(rms_all)
crest = 20 * np.log10(peak / rms_all + 1e-9)                # dynamics; ~very low = over-compressed
clip_frac = float(np.mean(np.abs(y) > 0.985))
cent = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=SR)))
# spectral balance
full = np.abs(librosa.stft(y, n_fft=2048))
frq = librosa.fft_frequencies(sr=SR, n_fft=2048)
low = full[frq < 250].mean(); mid = full[(frq >= 250) & (frq < 4000)].mean(); high = full[frq >= 4000].mean()
tot = low + mid + high + 1e-9
bal = {"low": float(low / tot), "mid": float(mid / tot), "high": float(high / tot)}
# low-end CLARITY (catches "hazy bass" — the ear-feedback the balance check missed).
# haze = noise-like/smeared low end = high spectral flatness in <200 Hz. Calibrated to
# real Burmeister (low_flatness 0.59). Higher than the DJ = hazy/smeared.
lb = frq < 200
lowspec = full[lb].mean(axis=1) + 1e-9
low_flat = float(np.exp(np.log(lowspec).mean()) / lowspec.mean())
lowf = full[lb].sum(axis=0)
low_pump = float(np.percentile(lowf, 90) / (np.percentile(lowf, 20) + 1e-9))
# high-end / HAT clutter (ear: "hi-hat getting mixed, not clear"). fine STFT to match the
# DJ ref; real Burmeister high-band (>5 kHz) fraction = 0.058. Way above = the hat is
# buried in a wash of stab-tops/drone-highs/air rather than a distinct clean element.
Sf = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
frf = librosa.fft_frequencies(sr=SR, n_fft=1024)
high_frac = float(Sf[frf >= 5000].sum() / (Sf.sum() + 1e-9))
try:
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=SR)[0])[0])
    if tempo < 1:  # beat tracker failed -> fall back to tempo estimator
        tempo = float(np.atleast_1d(librosa.feature.tempo(y=y, sr=SR))[0])
except Exception:
    tempo = 0.0
arc_flat = float(np.std(gen_arc))                          # ~0 = dead flat, no dynamics

# ---- grammar match ----
G = json.load(open(a.grammar))
g_active = G["element_active_fraction"]
af_err = float(np.mean([abs(active[n] - g_active[n]) for n in ELEMENTS]))
# entry-order rank agreement (Spearman-ish): fraction of element pairs ordered the same
g_entry = G["element_mean_entry_s"]
def order(d): return sorted(ELEMENTS, key=lambda n: d[n])
go, po = order(g_entry), order(entry)
pairs = concord = 0
for x in range(len(ELEMENTS)):
    for yy in range(x + 1, len(ELEMENTS)):
        pairs += 1
        if (go.index(ELEMENTS[x]) - go.index(ELEMENTS[yy])) * (po.index(ELEMENTS[x]) - po.index(ELEMENTS[yy])) > 0:
            concord += 1
entry_agree = concord / pairs
g_bd = G["breakdowns_per_hour"]["median"] * (dur / 3600.0) / max(1, nbins)  # rough expected rate
g_arc = np.interp(np.linspace(0, 1, nbins), np.linspace(0, 1, 24), np.array(G["energy_arc_24"]))
arc_corr = float(np.corrcoef(gen_arc, g_arc)[0, 1]) if nbins > 2 and np.std(gen_arc) > 1e-6 else 0.0

# ---- scores (0..10) ----
grammar_match = max(0.0, 10 * (1 - af_err / 0.30))          # 0.30 L1 err -> 0
order_score = 10 * entry_agree
dynamics = 10.0 if 7 <= crest <= 16 else max(0.0, 10 - abs(crest - 11) * 0.8)  # ~14 dB crest is healthy
# spectral scored vs the DJ's REAL balance, not an abstract ideal (measured real
# Burmeister = L0.96/M0.04/H0.01 — hypnotic techno IS bass-dominant). Per-DJ ref;
# TODO scale-up: store measured balance per DJ in grammar.json.
DJ_BAL = tuple(G.get("spectral_balance", (0.90, 0.07, 0.03)))
spectral = 10.0 - min(10.0, (abs(bal["low"] - DJ_BAL[0]) + abs(bal["mid"] - DJ_BAL[1]) +
                             abs(bal["high"] - DJ_BAL[2])) * 14)
liveliness = min(10.0, arc_flat * 60)                       # some arc movement expected
DJ_LOWFLAT = G.get("low_flatness", 0.59)                    # measured real Burmeister
clarity = 10.0 - min(10.0, max(0.0, low_flat - DJ_LOWFLAT) * 45)  # hazier than DJ -> lower
DJ_HIGHFRAC = G.get("high_frac", 0.058)                     # measured real Burmeister
hat_clarity = 10.0 - min(10.0, max(0.0, high_frac - DJ_HIGHFRAC * 1.6) * 28)  # washy highs -> lower
overall = round(float(np.mean([grammar_match, order_score, dynamics, spectral,
                               liveliness, clarity, hat_clarity])), 1)

issues = []
if active["kick+bass"] < 0.3: issues.append("kick barely present")
if clip_frac > 0.001: issues.append(f"clipping ({clip_frac*100:.2f}% of samples)")
if crest < 5: issues.append(f"over-compressed (crest {crest:.1f} dB)")
if arc_flat < 0.05: issues.append("energy arc is dead-flat (no build/breakdown)")
if af_err > 0.12: issues.append(f"element densities off-grammar (L1 {af_err:.2f})")
if entry_agree < 0.6: issues.append("entry order doesn't match the DJ")
if bal["low"] > DJ_BAL[0] + 0.05: issues.append("more bass-heavy than the DJ (muddy)")
if bal["high"] > DJ_BAL[2] + 0.12: issues.append("brighter than the DJ (harsh vs the reference sound)")
if low_flat > DJ_LOWFLAT + 0.06: issues.append(f"low-end hazy/smeared (flatness {low_flat:.2f} vs DJ ~{DJ_LOWFLAT})")
if high_frac > DJ_HIGHFRAC * 2.2: issues.append(f"hats washy/cluttered (high-band {high_frac:.2f} vs DJ ~{DJ_HIGHFRAC})")

if active["kick+bass"] < 0.15 or clip_frac > 0.02 or dbfs < -30:
    verdict = "broken"
elif overall >= 7 and not [i for i in issues if "kick" in i or "clip" in i]:
    verdict = "ship-it"
else:
    verdict = "needs-work"

report = {
    "track": os.path.basename(a.track), "dj": G.get("dj"), "duration_min": round(dur / 60, 1),
    "scores": {"grammar_match": round(grammar_match, 1), "entry_order": round(order_score, 1),
               "dynamics": round(dynamics, 1), "spectral": round(spectral, 1),
               "liveliness": round(liveliness, 1), "clarity": round(clarity, 1),
               "hat_clarity": round(hat_clarity, 1), "overall": overall},
    "grammar": {"active_frac_L1_err": round(af_err, 3), "entry_order_agree": round(entry_agree, 2),
                "energy_arc_corr": round(arc_corr, 2),
                "gen_active": {n: round(active[n], 2) for n in ELEMENTS},
                "target_active": {n: round(g_active[n], 2) for n in ELEMENTS}},
    "audio": {"dbfs": round(dbfs, 1), "crest_db": round(crest, 1), "clip_frac": round(clip_frac, 4),
              "spectral_balance": {k: round(v, 2) for k, v in bal.items()},
              "low_flatness": round(low_flat, 3), "low_pump": round(low_pump, 2),
              "high_frac": round(high_frac, 3),
              "centroid_hz": round(cent), "tempo_bpm": round(tempo, 1)},
    "issues": issues, "verdict": verdict,
    "note": "machine PROXY — objective + grammar only; groove/feel needs the human ear",
}

# ---- optional VLM spectrogram opinion (secondary, weak signal) ----
if a.vlm:
    try:
        import io, requests
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        M = librosa.feature.melspectrogram(y=y, sr=SR, n_mels=128)
        Mdb = librosa.power_to_db(M, ref=np.max)
        fig = plt.figure(figsize=(8, 3)); librosa.display.specshow(Mdb, sr=SR, x_axis="time", y_axis="mel")
        buf = io.BytesIO(); plt.tight_layout(); plt.savefig(buf, format="jpg", dpi=90); plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode()
        sys = ("You are grading a mel-spectrogram of an electronic music track. "
               "CRITICAL: if the image is too uniform/ambiguous to judge structure, say so and "
               "return low confidence — do NOT invent qualities you cannot see. Return JSON: "
               "{has_structure:bool, has_breakdown:bool, looks_dynamic:bool, confidence:0-1, note:str}.")
        r = requests.post(a.proxy, headers={"Authorization": "Bearer sk-trigunai-master-key-2026"},
                          json={"model": "gpt-4o-mini", "temperature": 0.2,
                                "response_format": {"type": "json_object"},
                                "messages": [{"role": "system", "content": sys},
                                             {"role": "user", "content": [
                                                 {"type": "text", "text": "Grade this spectrogram."},
                                                 {"type": "image_url", "image_url":
                                                     {"url": f"data:image/jpeg;base64,{b64}"}}]}]},
                          timeout=40)
        report["vlm_spectrogram"] = json.loads(r.json()["choices"][0]["message"]["content"])
        report["vlm_spectrogram"]["_caveat"] = "weak secondary proxy, not the human ear"
    except Exception as e:
        report["vlm_spectrogram"] = {"error": str(e)}

# ---- print ----
s = report["scores"]
print(f"\n=== AUDIO CRITIC — {report['track']}  (DJ: {report['dj']}, {report['duration_min']} min) ===")
print(f"  grammar_match {s['grammar_match']}/10 | entry_order {s['entry_order']}/10 | "
      f"dynamics {s['dynamics']}/10 | spectral {s['spectral']}/10 | liveliness {s['liveliness']}/10 | "
      f"clarity {s['clarity']}/10 | hat_clarity {s['hat_clarity']}/10")
print(f"  OVERALL {s['overall']}/10   VERDICT: {report['verdict'].upper()}")
print(f"  grammar: density-L1 {report['grammar']['active_frac_L1_err']} | "
      f"entry-order-agree {report['grammar']['entry_order_agree']} | arc-corr {report['grammar']['energy_arc_corr']}")
print("  gen density :", " ".join(f"{n[:4]}={report['grammar']['gen_active'][n]}" for n in ELEMENTS))
print("  DJ  density :", " ".join(f"{n[:4]}={report['grammar']['target_active'][n]}" for n in ELEMENTS))
a2 = report["audio"]
print(f"  audio: {a2['dbfs']} dBFS | crest {a2['crest_db']} dB | clip {a2['clip_frac']} | "
      f"balance L{a2['spectral_balance']['low']}/M{a2['spectral_balance']['mid']}/H{a2['spectral_balance']['high']} | "
      f"low-haze {a2['low_flatness']} (DJ~{DJ_LOWFLAT}) | ~{a2['tempo_bpm']} BPM")
print("  issues:", "; ".join(report["issues"]) if report["issues"] else "none")
if "vlm_spectrogram" in report:
    print("  VLM(spectrogram):", report["vlm_spectrogram"])
print(f"  [{report['note']}]")

if a.out:
    json.dump(report, open(a.out, "w"), indent=2)
    print(f"\nsaved -> {a.out}")
