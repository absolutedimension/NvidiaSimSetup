# DK Voice Model — Recording Brief v3

*Why this doc exists:* the current DK fine-tune (8.87 min, `singer_dataset/`, trained 2026-07-19) doesn't sound like you.
We diagnosed it on 2026-07-20 in two rounds: (1) comparing zero-shot base model vs step-1000/1500/final checkpoints
— all four nearly identical, so **the fine-tune itself isn't the bottleneck**; (2) five live test recordings via
the MacBook's built-in mic at different volumes/distances/techniques, plus a validation check against a real
professional vocal stem. Conclusion updated after round 2 below.

## What the diagnostic found (the numbers)

A clean, present vocal recording usually has ~45-70% of its energy in 300Hz-2kHz, ~7-25% in the 2-6kHz
"presence/consonant clarity" band, and a percent or few above 6kHz ("air"). We validated this against a real
studio reference (Tanishk Shukla vocal stem, demucs-isolated): 44.1% / **6.9%** / **1.6%**.

| Source | 300Hz-2kHz | 2-6kHz (presence) | >6kHz (air) |
|---|---|---|---|
| Professional vocal (validation reference) | 47.4% | **6.9%** | **1.6%** |
| Your reference clip (`USERVOICE_ref.wav`) | 81.4% | 1.4% | 0.1% |
| Your raw `D_hindi.wav` recording (phone) | 85.5% | 1.1% | 0.1% |
| DK zero-shot / step-1000 / step-1500 / final | ~89-90% | ~1.7-2.5% | ~0.1-0.2% |
| Live take 3 (MacBook mic, moderate/clean volume) | 90.0% | 0.6% | 0.1% |
| Live take 5 (MacBook mic, loud — but 16.5% clipped/distorted) | 73.2% | 2.7% | 0.2% |

Codec is not the cause — the source `.m4a` files are 226 kbps AAC, well above what would start cutting highs.
**Round 1 hypothesis (phone "voice/call" recording mode) was ruled out in round 2:** the exact same muffled
signature showed up on the MacBook's raw built-in mic too, across multiple volumes and a countdown-timed vs.
immediate-start test. Louder/closer speech measurably helped (0.6% → 2.7% presence going from moderate to loud),
which matches the acoustic-phonetics fact that presence/air content lives in consonant transients that are the
first thing lost when speech is soft or off-axis — but even the loudest clean attempt was still ~2.5x below the
professional reference, and pushing volume further just caused clipping distortion, not real presence.

**Working conclusion: this is a mic-proximity + articulation issue, not a settings or device issue** — but it's
hard to nail through blind trial-and-error recording without a visual level meter. See the revised Step 0 below.

## STEP 0 — Do this FIRST, before recording anything else

Record **one 30-60 second test clip** reading anything (Hindi or English, doesn't matter) and send it over.
Rules for the test clip, updated after the round-2 live test:

- Use your phone's **plain/default voice memo app** — NOT WhatsApp voice notes, NOT any "call recording" app,
  NOT any mode labeled "noise reduction," "voice isolation," or "meeting mode."
- **Use an app with a visible level/waveform meter while recording** (stock Voice Memos on iPhone shows this;
  on Android most default recorders do too). Watch it live and aim for the meter peaking **around 70-85% of
  max, never pinned to the top/red** — that's the proximity sweet spot between "too soft, no presence" and
  "clipping/distorted." Blind recording (no meter) made this hard to hit in our live test — 0.6% presence at a
  safe volume, 2.7% at a loud-but-clipped volume, neither acceptable.
- Hold the phone **10-15cm from your mouth** (closer than originally suggested — proximity is what recovers
  the missing presence band), mic-side facing you directly, no case covering the mic port.
- **Articulate a bit more crisply than feels natural** — slightly exaggerate consonants (s/sh/t/k/f sounds).
  This isn't about talking robotically, just not letting consonants go soft/mumbled.
- Record in a quiet room; some room tone is fine.
- Export/share as the original file, no re-compression through messaging apps.

I'll run it through the same diagnostic script and tell you immediately whether the presence/air bands are
healthy (target: get meaningfully closer to the professional reference's 6.9%/1.6%, even if not exact — a
2-4% presence band without clipping would already be a big improvement over what we've measured so far).
**Only after that check passes** should you invest time recording the full set below.

## STEP 1 — Once the test clip passes: what to record

Assuming Step 0 confirms clean capture, here's the full content list. Your original session already covered
warmups/vowels/sargam/short lines/emotion (~9 min) — keep that structure, but this version adds more **natural,
varied, conversational** content, since a model trained mostly on drills doesn't generalize well to natural
singing/speaking content it's asked to convert later (that mismatch was likely also hurting identity match,
independent of the muffling issue).

Target: **20-25 minutes total** (roughly 2.5x what you have), same file-naming scheme so it slots into the
existing `singer_dataset/` pipeline.

| File | Content | Target length | Why |
|---|---|---|---|
| `A_warmup_hindi.wav` / `A_warmup_english.wav` | *(already have these — keep)* | ~75s each | vocal warm-up range |
| `B_vowels.wav` | *(already have — keep)* | ~40s | pure vowel identity |
| `C_sargam_full.wav` / `C_sargam_pitch1.wav` | *(already have — keep)* | ~80s / 20s | pitch range / melodic identity |
| `G_conversational_hindi.wav` | **NEW** — talk naturally in Hindi for 3-4 min like you're explaining something to a friend (not reading a script) | 3-4 min | natural prosody/rhythm the model has never seen |
| `G_conversational_english.wav` | **NEW** — same, in English | 2-3 min | same, other language |
| `H_singing_natural.wav` | **NEW** — sing along to 2-3 short familiar tunes (hum is fine, doesn't need to be in-key) at a natural, comfortable volume — NOT the careful/exercise tone of the sargam takes | 2-3 min | singing timbre differs from spoken/drilled timbre; this is what we're actually trying to generate |
| `D_hindi.wav` / `E_english.wav` | *(already have — keep, or re-record if Step 0 test fails on your current device)* | ~2 min / ~1 min | scripted natural sentences |
| `F_emotion.wav` | *(already have — keep)* | ~1.5 min | emotional range (matters for expressive singing) |
| `I_wide_range.wav` | **NEW** — read the same short paragraph 3 times: once low/calm, once normal, once loud/energetic (like calling out to someone across a room) | 1-2 min | dynamic range the current set is missing (everything so far is one steady volume/energy) |

## STEP 2 — how to send it to me

Keep the same naming convention (letters group by category). Send as `.wav` if your recording app supports it;
`.m4a` at your current 226kbps is also fine quality-wise, codec was never the problem. Once I have it, I'll:

1. Re-run the spectral diagnostic on the new raw files first (catch any capture problems before spending GPU time)
2. Re-segment (`ft_seg`) and re-run the fine-tune (same `config_dit_mel_seed_uvit_whisper_base_f0_44k.yml`, ~2000 steps)
3. A/B the new checkpoint against zero-shot + the old DK checkpoint on the same test sentence, same way we
   diagnosed this round, before calling it done

## What NOT to do

- Don't just record 20 more minutes on the same device/app without doing Step 0 first — if the capture chain
  is the problem, more volume of muffled audio makes the overfitting risk worse, not better.
- Don't over-index on hitting an exact duration target — natural, varied, *clean* content matters more than
  padding minutes with more drills.
