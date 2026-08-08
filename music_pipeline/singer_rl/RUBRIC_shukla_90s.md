# Style Rubric — Tanishk Shukla / 90s-Bollywood (`shukla_90s`)

*Style reference:* Tanishk Shukla, Indian Idol S16 — **4 tracks** (Tu Pyar Hai Kisi Aur Ka, Aur Kya, audition, Mujhe Raat Din).  

> **STYLE FEATURES ONLY.** No melody/lyrics/recording stored or reused. This is the RL reward yardstick; our output uses ORIGINAL melody+lyrics sung in our OWNED voice (`ravi`). The reference's actual notes are never a target.

## The musical bed (reward targets)

- **Tempo:** ~109 BPM  (per-track [99.4, 120.2, 99.4, 117.5]) → mid-tempo classic ballad pace
- **Key:** varies — ['F# minor', 'A# major', 'A major', 'C major'] → key is NOT style-defining; don't constrain it
- **Harmonic/percussive ratio:** 5.1 → **melody-dominant, acoustic — NOT beat-driven** (the core signature)
- **Percussion density:** 5.0 onsets/s → moderate tabla/dholak + rhythm, never busy
- **Brightness (centroid):** 2638 Hz (rolloff85 5841 Hz) → warm, not harsh
- **Dynamic range:** 12.2 dB → big emotional swells (soft verse → full chorus)
- **Energy arc (8 seg):** [0.849, 0.964, 0.923, 0.931, 0.94, 0.983, 0.955, 0.79] → builds to a peak ~2/3 in, gentle fade-out

## The singing manner (vocal reward targets)

- **Voiced fraction:** 0.86 → **vocal-forward; the voice is the star**
- **Ornament rate:** 19.1/s → **HIGH murki/melisma — THE defining marker** (rapid pitch inflections/harkat)
- **Pitch range:** 17.4 semitones → wide, expressive span
- **Glide (meend):** 0.10 semi/frame → smooth sliding between notes
- **Vibrato:** 0.78 semi std → expressive wobble on held notes
- **Median f0:** 236 Hz → reflects these HIGH Idol/duet performances; for our **male ravi** target we set register lower separately (this feature isn't a hard target)

## Reward weighting (draft — what the critic scores each take on)

| Feature | Weight | Why |
|---|---|---|
| ornament_rate (murki) | **0.30** | the single most Bollywood-defining trait |
| harmonic_percussive (melody-dominant) | 0.20 | keeps it a *song*, not a beat |
| pitch_range + glide + vibrato (expression) | 0.20 | the emotional delivery |
| dynamic_range + energy_arc (swell) | 0.15 | the ballad build |
| tempo in 99–120 band | 0.10 | right pace |
| brightness/warmth | 0.05 | mix character |

Each take's measured features → weighted distance to these targets → a 0–10 **style-score** (the 'have-we-reached-it' signal). Best-of-N keeps high scorers; generator nudges toward them. Key & absolute pitch are deliberately unconstrained.
