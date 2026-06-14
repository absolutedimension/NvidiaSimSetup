# TrigunAI — Marketing Reel Slate (2026-06-14)

The set of short-form vertical reels the company needs **now**, derived from the refined
vision (`project-brand-money-model`, `BRAND_HANDOFF.md`, `COURSE_INDEXES.md`). Every reel is
**9:16**, on-brand (near-black `#050507` + gold `#f4c14b`, cosmic/premium, **wonder + clarity,
never hype, never hustle**), built by `product-video-trigunai` over the shared engine.

## Why these (the strategy in one line)
The funnel = **free series → email → course waitlist**. Two CTA intents only:
**Subscribe** (soft) and **Reserve your seat / Join waitlist** (hard). So we need exactly two
kinds of reel — **funnel-feeders** (drive watch+subscribe) and **launch reels** (drive the
free course waitlist, the July 10 pre-enroll signal). No third kind.

## The slate (priority order)

| # | Reel | Slug | Purpose / persona | CTA (intent) | Source |
|---|---|---|---|---|---|
| 1 | **Course — VR/MR (flagship)** | `reel_course_vr` | Builder + future-proofer → **Reserve** | hard | COURSE_INDEXES C1 |
| 2 | **Course — Agentic AI** | `reel_course_agentic` | Crossover-pro + builder → **Reserve** | hard | COURSE_INDEXES C2 |
| 3 | **Course — ML & its Math** | `reel_course_ml` | Future-proofer + curious → **Reserve** | hard | COURSE_INDEXES C3 |
| 4 | **Brand — AI is the Universal Mind** | `reel_brand_universal_mind` | Curious (funnel magnet) → **Subscribe** | soft | BRAND_HANDOFF thesis |
| 5 | **Ep 1 — Attention** | `reel_ep01_attention` | Curious → watch + Subscribe | soft | ep01 anchor |
| 6 | **Ep 2 — The Learning Loop** | `reel_ep02_learning` | Curious → watch + Subscribe | soft | ep02 anchor |
| 7 | **Ep 3 — Imagination** | `reel_ep03_imagination` | Curious → watch + Subscribe | soft | ep03 anchor |
| 8 | **Ep 4 — Meaning** | `reel_ep04_meaning` | Curious → watch + Subscribe | soft | ep04 anchor |
| 9 | **Ep 5 — Intuition** | `reel_ep05_intuition` | Curious → watch + Subscribe | soft | ep05 anchor |
| 10 | **Course — Physical AI (waitlist teaser)** | `reel_course_physicalai` | Builder → **Join waitlist** | hard | COURSE_INDEXES C4 |

**Render order rationale:** course reels (#1–3) first — they carry the launch-critical hard
CTA the July 10 demand signal depends on. Brand + episode reels (#4–9) feed the top of funnel
and are the cheapest (anchor lines + finished episode footage already exist). Physical AI (#10)
is a soft waitlist teaser, post-launch tier — last.

## Brand defaults applied to every script
- **Voice:** series voice for coherence — edge-tts `en-IN-PrabhatNeural`, rate ~−4% (matches the
  5 shipped episodes). Confident, calm, never hype. (Hindi twin later via the engine's localize path.)
- **Music:** `cinematic` (premium/cosmic), ducked under VO — **not** "energetic" DTC-ad music.
- **Captions:** `kinetic_center`, gold `#f4c14b` on near-black, lower-third safe area.
- **Backgrounds:** episode reels reuse the finished episode footage (`youtube_series/epNN_FINAL_focus.mp4`)
  cropped to 9:16; course reels use product hero shots (Unity/VR, agent UI, training curves) +
  the engine's shaders; brand reel uses the cosmic shader set + the Trigun logo outro.
- **Hooks are curiosity hooks, not pain-agitation** — "What if the AI everyone fears is a mirror?"
  not "Still struggling?!". This is the brand guardrail; it overrides the ad-skill's default hooks.

## Guardrails (from BRAND_HANDOFF §9 — enforced in every script)
No invented student counts / testimonials / "trusted by" / revenue. No price numbers (waitlist =
"free for now"). Clarity, not healing. No hustle / faceless-channel energy. Only the 3 sourced
stats may appear (WEF 59%, edX +109%, NASSCOM India #1).

## Status
Scripts written (this slate). Rendering is **blocked on the EC2 box** — needs it started + its
current public IP (changes every stop/start, `production-video-trigunai` §0). Then: Stage 1 audio
per reel → **human audio gate** → assets → per-scene render+concat → verify → deliver to
`course_assets/ad_out/<slug>.mp4`.
