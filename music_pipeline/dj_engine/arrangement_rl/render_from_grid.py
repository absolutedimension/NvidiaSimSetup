#!/usr/bin/env python3
"""
render_from_grid.py — turn an RL-composed arrangement grid into AUDIO.

The arrangement-RL policy composes WHICH elements are active over time (a T x 6
grid). This renderer maps each of the 6 element tracks onto a real stem and uses
the grid column as that stem's GAIN AUTOMATION — so the structure you hear is the
one the policy composed, not a hand-authored arc.

element (analysis band)   -> stem
  sub       (20-60 Hz)     -> synth sat-sub sine (no dedicated stem)
  kick+bass (60-150)       -> kick.wav
  bassline  (150-400)      -> bass.wav
  drone     (400-900)      -> drone.wav
  stab      (900-3000)     -> stab.wav
  hats      (3000-9000)    -> hats.wav

Runs on EC2 in ~/audio_pipeline/venv (numpy+soundfile+librosa+scipy).
Usage:
  python3 render_from_grid.py --grid burmeister_rl_grid.json \
     --stems ~/dj_engine/burmeister/stems_fs --minutes 6 --bpm 123 \
     --out burmeister_rl.wav
"""
import argparse, json, gc, numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

ELEMENTS = ["sub", "kick+bass", "bassline", "drone", "stab", "hats"]
STEM = {"kick+bass": "kick", "bassline": "bass", "drone": "drone", "stab": "stab", "hats": "hats"}
# per-element mix level (dBFS-ish) and band filter (hp, lp).
# rebalanced 2026-07-18 (critic said 91% bass): sub pulled way down, drone/stab/hats up.
# faithful bass-forward balance (real Burmeister measures L0.96) — a light sub trim
# only, the aggressive de-mud moved us AWAY from the DJ sound (critic was miscalibrated).
# bassline high-passed to 95 Hz so it sits ABOVE the sub (EQ separation = clarity, un-haze).
# clean TONAL synth-sub carries <95 Hz; the smeared bass STEM is hp'd to 130 so it only
# adds the note movement above the sub — replaces noise-like low smear with a tonal low
# (lowers <200 Hz spectral flatness = the measured "haze"). AI-stem smear is the ceiling.
# hats declutter (ear: "hi-hat getting mixed, not clear"): our high-band was 4x the DJ's
# (0.23 vs 0.058) — the hat was buried in a wash of stab-tops + drone-highs + air boost.
# stab now lp'd to 3600 so it stays OUT of the hat's range; hat gets its own clean top.
# per-band diagnostic vs real Burmeister showed: our SUB (20-100) too thin (0.19 vs DJ 0.40)
# and our LOWMID (250-600) bloated+smeared (0.22/flat0.96 vs DJ 0.14/0.86) = the "hazy
# background". Fix: strong clean tonal sub (foundation) + drone lifted to its own 480-2000
# band so it stops hazing the low-mid.
MIX = {"sub": (-12, None, 150), "kick+bass": (-12, None, 7000), "bassline": (-15, 150, 700),
       "drone": (-24, 480, 2000), "stab": (-24, 300, 3600), "hats": (-18, 550, None)}

ap = argparse.ArgumentParser()
ap.add_argument("--grid", required=True)
ap.add_argument("--stems", required=True)
ap.add_argument("--minutes", type=float, default=6.0)
ap.add_argument("--bpm", type=float, default=123.0)
ap.add_argument("--sr", type=int, default=44100)
ap.add_argument("--out", required=True)
ap.add_argument("--mute", default="", help="comma-separated elements to silence (e.g. drone,sub) for A/B testing")
ap.add_argument("--structure", action="store_true",
                help="impose a rise-and-fall song arc (intro build -> breakdown -> DROP -> peak -> breakdown -> drop -> outro)")
a = ap.parse_args()
MUTE = {m.strip() for m in a.mute.split(",") if m.strip()}
SR = a.sr; T = int(a.minutes * 60 * SR); BPM = a.bpm

def lp(x, f): return sosfilt(butter(4, f / (SR / 2), btype="low", output="sos"), x).astype(np.float32)
def hp(x, f): return sosfilt(butter(2, f / (SR / 2), btype="high", output="sos"), x).astype(np.float32)
def rms(y): return float(np.sqrt(np.mean(y ** 2)) + 1e-9)

def loop_to(y, T):
    X = int(4.0 * SR); xf = max(1, min(X, len(y) // 2))
    fin = np.linspace(0, 1, xf, dtype=np.float32); fout = fin[::-1]
    if len(y) >= T + xf: return y[:T].copy()
    out = y.copy()
    while len(out) < T + xf:
        out = np.concatenate([out[:-xf], out[-xf:] * fout + y[:xf] * fin, y[xf:]])
    return out[:T].astype(np.float32)

def load(name, db):
    y, _ = librosa.load(f"{a.stems}/{name}.wav", sr=SR, mono=True)
    y = y.astype(np.float32)
    return (y * (10 ** (db / 20.0) / rms(y))).astype(np.float32)

def gate(col, lo=0.52, hi=0.82):
    """occupancy -> PRESENCE. Low-occupancy steps go truly silent (elements drop
    OUT in sparse sections) instead of merely quiet. This is what makes the RL
    arrangement's structure audible AND measurable (per-band normalization ignores
    volume, so an element must actually go to ~0 to read as 'off')."""
    return np.clip((col - lo) / (hi - lo), 0.0, 1.0)

def grid_gain(col, T, smooth_s=1.2):
    """turn a length-N step column (0..1) into a sample-rate gain automation,
    smoothed so on/off transitions become musical fades (no clicks)."""
    N = len(col)
    step_centers = (np.arange(N) + 0.5) / N
    g = np.interp(np.linspace(0, 1, T), step_centers, col).astype(np.float32)
    k = int(smooth_s * SR)
    if k > 1:
        c = np.cumsum(np.insert(g, 0, 0.0))
        s = (c[k:] - c[:-k]) / k
        pad = len(g) - len(s)
        g = np.concatenate([np.full(pad // 2, s[0]), s, np.full(pad - pad // 2, s[-1])]).astype(np.float32)
    return g

def duck_env(depth=0.20, tau=0.09):
    tt = (np.arange(T) / SR) % (60.0 / BPM)
    return (1.0 - depth * np.exp(-tt / tau)).astype(np.float32)

# per-element sidechain: DEEP pump on sub/bass so they get out of the kick's way
# (the fix for "hazy bass" — clears the low-end pile-up into a defined pulse).
# kick is the trigger (no duck); drone light; stab/hats none.
# sub ducks less now (0.35) so the low-bass drone SUSTAINS solidly instead of pumping away.
DUCK = {"sub": duck_env(0.35, 0.10), "kick+bass": None, "bassline": duck_env(0.48, 0.11),
        "drone": duck_env(0.36, 0.11), "stab": duck_env(0.12, 0.09), "hats": None}

# --- load the RL-composed grid ---
G = json.load(open(a.grid))
probs = np.array(G["probs"], np.float32)          # (N steps, 6)
els = G.get("elements", ELEMENTS)
print(f"[render] grid: {probs.shape[0]} steps x {len(els)} elements, DJ={G.get('dj')}")

# detect the kick's actual phase so the synth bass LOCKS to the real kicks, not a t=0
# grid (the kick loop has a ~0.5s lead-in; ignoring it put the bass out of sync).
_kyy, _ = librosa.load(f"{a.stems}/kick.wav", sr=SR, mono=True)
_kon = librosa.onset.onset_detect(y=_kyy, sr=SR, units="time")
KICK_PHASE = float(_kon[0]) if len(_kon) else 0.0
del _kyy
print(f"[render] kick phase = {KICK_PHASE*1000:.0f} ms (bass locked to this)")

# ---- optional RISE-AND-FALL song structure (intro build -> breakdown -> DROP -> peak ...) ----
def penv(points):
    return np.interp(np.linspace(0, 1, T), [p[0] for p in points],
                     [p[1] for p in points]).astype(np.float32)
def psmooth(x, s=0.25):
    k = int(s * SR)
    if k <= 1: return x
    c = np.cumsum(np.insert(x, 0, 0.0)); o = (c[k:] - c[:-k]) / k
    pad = len(x) - len(o)
    return np.concatenate([np.full(pad // 2, o[0]), o, np.full(pad - pad // 2, o[-1])]).astype(np.float32)

BD = []; DROPS = []; STRUCT = {}; MACRO_FILTER = None
if a.structure:
    dur = T / SR; bar = 4 * 60.0 / BPM
    def snap_frac(frac):             # snap a drop to the nearest DOWNBEAT so the slam lands on the kick
        n = round((frac * dur - KICK_PHASE) / bar)
        return min(0.97, max(0.03, (KICK_PHASE + n * bar) / dur))
    DROPS = [snap_frac(0.40), snap_frac(0.70)]
    d1, d2 = DROPS
    BD = [(0.30, d1), (0.60, d2)]    # long breakdowns that flow straight into each drop
    def bdgate(keep):                # 1 normally, `keep` inside breakdowns
        g = np.ones(T, np.float32)
        for s, e in BD: g[int(s * T):int(e * T)] = keep
        return psmooth(g, 0.20)
    intro = penv([(0, 0.0), (0.02, 0.35), (0.12, 1.0), (1, 1.0)])          # slow build in
    introlate = penv([(0, 0.0), (0.14, 0.0), (0.24, 1.0), (1, 1.0)])       # hats/stab in later
    outro = penv([(0, 1), (0.86, 1.0), (0.95, 0.2), (1.0, 0.0)])           # longer wind down
    outro_last = penv([(0, 1), (0.92, 1.0), (1.0, 0.12)])                  # drone lingers last
    # Burmeister breakdown signature: kick+hats OUT, bass+drone KEPT
    STRUCT = {
        "sub":       intro * bdgate(1.0) * outro,
        "kick+bass": intro * bdgate(0.0) * outro,
        "bassline":  intro * bdgate(0.80) * outro,
        "drone":     intro * bdgate(1.0) * outro_last,
        "stab":      introlate * bdgate(0.35) * outro,
        "hats":      introlate * bdgate(0.0) * outro,
    }
    MACRO_FILTER = penv([(0, 0.12), (0.12, 0.55), (0.28, 0.82), (0.30, 0.5),
                         (d1 - 0.008, 0.22), (d1, 1.0), (0.58, 1.0), (0.60, 0.5),
                         (d2 - 0.008, 0.22), (d2, 1.0), (0.86, 0.92), (1.0, 0.3)])
    print(f"[render] STRUCTURE: build -> breakdown -> DROP@{d1*dur:.0f}s -> peak -> breakdown -> DROP@{d2*dur:.0f}s -> outro")

mix = np.zeros(T, np.float32)

for ei, e in enumerate(els):
    if e in MUTE:
        print(f"[render]  {e:>10s} -> MUTED (A/B test)")
        continue
    col = gate(probs[:, ei])                        # occupancy -> presence (elements drop OUT)
    gain = grid_gain(col, T)                        # <- the RL arrangement drives this
    db, hpf, lpf = MIX[e]
    if e == "sub":
        # rich musical sub-bass DRONE (ear: "proper low bass-like sound", not a thin tone):
        # root F#1 + octave for pitch/body + light saturation for warmth + slow breath so
        # it's a living drone. Synthesized = clean (no stem smear).
        tt = np.arange(T) / SR
        root = np.sin(2 * np.pi * 46.25 * tt)
        octv = 0.40 * np.sin(2 * np.pi * 92.5 * tt)          # octave -> you HEAR the note, body
        fifth = 0.15 * np.sin(2 * np.pi * 69.3 * tt)         # a touch of 5th for warmth
        breath = (0.88 + 0.12 * np.sin(2 * np.pi * 0.06 * tt)).astype(np.float32)  # alive, not static
        src = (np.tanh((root + octv + fifth) * 1.5) * breath).astype(np.float32)
        src = src * (10 ** (db / 20.0))
    elif e == "bassline":
        # CLEAN SYNTH BASSLINE — replaces the smeared AI bass stem (confirmed by A/B as the
        # hazy "background bass" the ear kept catching). Offbeat filtered-saw plucks in F#
        # minor (Burmeister's key), so it NEVER overlaps the kick = clean + defined.
        beat = 60.0 / BPM
        ndur = beat * 0.46
        nn = int(ndur * SR); tn = np.arange(nn) / SR
        atk = int(0.004 * SR)
        def bnote(freq):
            y = sum((1.0 / h) * np.sin(2 * np.pi * freq * h * tn) for h in range(1, 7))  # bandlimited saw
            y = y * np.exp(-tn / (ndur * 0.34))          # plucky decay
            if atk > 1: y[:atk] *= np.linspace(0, 1, atk)  # no click
            return y.astype(np.float32)
        seq = [92.5, 92.5, 92.5, 110.0, 92.5, 92.5, 82.41, 92.5]  # F#2 root-heavy, hints of A2 / E2
        src = np.zeros(T, np.float32)
        tcur = KICK_PHASE + 0.5 * beat; i = 0             # offbeat, LOCKED to the real kick phase
        while tcur < a.minutes * 60:
            s = int(tcur * SR); nt = bnote(seq[i % len(seq)])
            e2 = min(T, s + len(nt))
            if s < T: src[s:e2] += nt[:e2 - s]
            tcur += beat; i += 1                          # one hit per beat, on the offbeat
        src = hp(src, 80); src = lp(src, 500)            # warm, out of the pure sub
        src = (src * (10 ** (db / 20.0) / (rms(src) + 1e-9))).astype(np.float32)
    elif e == "drone":
        src = load(STEM[e], db); src = loop_to(src, T)
        src = hp(src, hpf); src = lp(src, lpf)          # drone lifted to 480-2000 (out of the low-mid haze)
    else:
        src = load(STEM[e], db)
        src = loop_to(src, T)
        if hpf: src = hp(src, hpf)
        if lpf: src = lp(src, lpf)
    d = DUCK[e]
    s_env = STRUCT.get(e, 1.0)       # rise-and-fall structure (1.0 if --structure off)
    mix += src * gain * (d if d is not None else 1.0) * s_env
    del src, gain; gc.collect()
    print(f"[render]  {e:>10s} -> {STEM.get(e,'synth-sub'):>10s}  mean-gain {col.mean():.2f}")

# global filter-open: macro song-arc sweep if --structure, else arrangement-density driven
if MACRO_FILTER is not None:
    openE = MACRO_FILTER
else:
    density = probs.mean(axis=1)
    openE = grid_gain(np.clip(density * 1.4, 0, 1), T, smooth_s=3.0)
muff = lp(mix, 500)
mix = muff * (1.0 - openE) + mix * openE
del muff, openE; gc.collect()

# risers + drops + anticipation gate at each DROP point (the "fall then slam" moments)
if a.structure:
    beat = 60.0 / BPM
    for dp in DROPS:
        e0 = int(dp * T)
        # anticipation gate: near-silence the last beat before the drop
        gs = e0 - int(beat * SR)
        if gs > 0:
            g = np.ones(e0 - gs, np.float32) * 0.06
            g[:int(0.01 * SR)] = np.linspace(1, 0.06, int(0.01 * SR))
            mix[gs:e0] *= g
        # riser (long noise + tone sweep up into the drop = more tension/anticipation)
        rl = int(8 * beat * SR); s0 = e0 - rl        # 2-bar swell (was 3 beats)
        if s0 > 0:
            tt = np.arange(rl) / SR; ramp = tt / tt[-1]
            riser = hp(np.random.randn(rl).astype(np.float32), 500) * (ramp ** 2.2) * 0.6
            riser += np.sin(2 * np.pi * (180 + 3000 * ramp) * tt).astype(np.float32) * (ramp ** 3) * 0.35
            mix[s0:e0] += riser[:e0 - s0]
        # sub impact + crash at the drop (the slam)
        il = int(2.4 * SR); ti = np.arange(il) / SR
        imp = (np.sin(2 * np.pi * (78 * np.exp(-ti / 0.32)) * ti) * np.exp(-ti / 0.55)).astype(np.float32) * 1.5
        imp[:int(0.03 * SR)] += np.random.randn(int(0.03 * SR)).astype(np.float32) * 0.6  # transient click
        cl = int(1.9 * SR); tc = np.arange(cl) / SR
        crash = hp(np.random.randn(cl).astype(np.float32), 2800) * np.exp(-tc / 0.85) * 0.5
        mix[e0:e0 + il] += imp[:max(0, min(il, T - e0))]
        mix[e0:e0 + cl] += crash[:max(0, min(cl, T - e0))]
    gc.collect()

# de-HAZE: light low-mid mud trim (250-450) + gentle air. The bulk of the de-haze is
# the source split above (tonal sub carries <95, bass hp'd to 130).
mud = lp(hp(mix, 250), 600)          # cut the bloated/smeared low-mid (the hazy background)
mix = mix - 0.32 * mud
del mud
# NO broadband air boost — it washed out the hats. The hat carries its own top now.
gc.collect()

mix = mix / (np.max(np.abs(mix)) + 1e-6) * 0.97
sf.write(a.out, mix, SR)
n = 48; w = len(mix) // n
e = np.array([np.sqrt(np.mean(mix[i * w:(i + 1) * w] ** 2)) for i in range(n)]); e /= e.max()
print("[render] energy arc:", "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v * 8))] for v in e))
print(f"[render] DONE -> {a.out}  ({a.minutes}min @ {SR}Hz)")
