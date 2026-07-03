---
name: reel-shorts-video-trigunai
description: >
  REELS / SHORTS video factory for TrigunAI — makes finished vertical (9:16)
  short-form videos on the EC2 A10G box: 3-second hook, punchy 2–5s cuts, BIG
  center kinetic captions, a tight VO, and a music-forward bed. Covers both
  PRODUCT/AD reels (product hero shots + Ken-Burns + b-roll/LTX motion; sub-modes
  polished-ad and UGC-style) AND CONCEPT / thought-leadership reels & Shorts
  (a topic → punchy vertical explainer). Use whenever the user wants a REEL or
  SHORT: "make a reel", "make a short", "reel", "short", "instagram reel",
  "youtube short", "tiktok", "vertical video", "reel on <topic>", "product video",
  "product showcase", "product demo", "ad", "ad reel", "ad creative", "UGC ad",
  "UGC video", "marketing video", "promo", "promo reel", "product reel",
  "Instagram reel ad", "TikTok ad", "Shorts ad", "e-commerce video", "DTC ad",
  "launch reel", "unboxing-style video", "testimonial video", "before/after ad",
  "feature highlight reel", or asks to turn a product / topic / photos into a
  vertical reel or short. Built on the same engine as production-video-trigunai
  (re-aimed for short-form). For long-form teaching / course / explainer videos
  use production-video-trigunai instead.
---

# TrigunAI Reel / Shorts Video Agent

You make **reels & shorts** — vertical short-form video (product/ad reels, UGC-style ads,
and concept/thought-leadership reels) — by driving the SAME pipeline that `production-video-trigunai` uses, with a different
**Style Profile**. You do not reinvent the engine; you re-aim it.

```
product OR topic (name + images / link / description)
        │
        ▼
[reel-shorts-video-trigunai]  →  AUDIO-FIRST  →  reel assets (hero shots / b-roll / LTX motion)
        →  composite (9:16 hero + scrim + BIG kinetic captions + presenter) + music bed
        →  verified vertical MP4
```

> **The engine lives in `production-video-trigunai`.** Read its SKILL.md §0–§8 for everything
> infrastructure: the EC2 box + IP-changes-on-restart rule (§0), the service toolkit
> (`shader_service`, `slide_service`, `render_service`, `compositor_service`, `f5tts_service`,
> `hallo2_service`, `music_service`) (§2), the STAGED PIPELINE with the **audio human-gate**
> (§4), the ffmpeg compositing recipes (§5), and the hard-won gotchas (§6). **Do not duplicate
> that here — cite it.** This skill only documents what's *different* for product/ad video.

---

## 1. What's different vs. the learning engine (the Style Profile)

Everything below is the delta. Same box, same services, same audio-first gate, same
"render scene-by-scene then concat" rule, same verify-by-frames-then-watch-with-sound finish.

| Knob | Learning (production-video) | **Product / ad (this skill)** |
|---|---|---|
| **Aspect** | 16:9 | **9:16 default** (1080×1920); 1:1 (1080×1080) for feed; 16:9 only if asked |
| **Background / clip source** | shader field / Manim / AI scene art | **product hero shots** (image-gen, studio backdrop) + **b-roll / LTX motion clips** + optional shader accent |
| **Foreground** | motion-graphics teaching diagrams | **product cutout with Ken-Burns push** + price/feature cards |
| **Scene / cut length** | 15–30s teaching beats | **2–5s punchy cuts** (8–14 scenes in a 20–40s reel) |
| **Captions** | line-reveal lower-third (Poppins) | **BIG center kinetic pop captions** (1–3 words, scale-pop, bottom-third for safe-area) |
| **Voice** | calm teacher (`female_confident`, speed 0.75) | **hype/energetic** (`female_excited`/`male_*`, speed 0.9–1.0) OR conversational UGC |
| **Audio bed** | 12 Hz focus bed (−20 dB, ducked) | **music-forward** (`music_service`, energetic, −8 to −12 dB, ducked under VO) |
| **Hook** | gentle intro | **3-second pattern-interrupt** (problem / bold claim / before-after / price) |
| **Structure** | hook→teach→CTA | **hook → problem → product reveal → 2–3 benefits → social proof → CTA/offer** |

Two **sub-modes** (ask which, default = polished):
- **`P` polished-ad** — clean studio hero shots, smooth Ken-Burns, premium music, scripted VO.
  Best for DTC/e-commerce, app/SaaS, launch reels.
- **`U` UGC-style** — looks phone-shot: casual conversational VO, a presenter (Hallo/circular
  avatar) "holding"/reacting to the product, handheld-feel (subtle shake + tighter crop),
  caption stickers. Best for social-proof / testimonial / feed-native ads.

---

## 2. The brief you need (Stage 0)

Gather (ask only what you can't infer):
- **Product**: name + one-line of what it is + who it's for.
- **Assets**: any product images/screenshots the user has (best). If none, you'll image-gen
  hero shots from the description — say so. A product URL → ask them to drop the key images.
- **Offer / CTA**: price, discount, "link in bio", app name, launch date.
- **Sub-mode** (P / U), **aspect** (default 9:16), **length** (default 25–30s), **voice**
  (hype vs conversational), **music vibe** (energetic / chill / cinematic), **brand colors**.
- 2–3 **benefits** and (optional) a **social-proof** line (review quote, rating).

If the user just says "make an ad for X", draft the whole script yourself (§3) and show it
before rendering — don't block on a full brief.

---

## 3. Script format (compatible with the engine, ad-shaped)

Reuse the `production-video-trigunai` scene-script contract so the engine's per-scene
audio + concat flow works unchanged. Frontmatter sets the Style Profile; scenes are short
ad beats. Save to `course_scripts/video_scripts/<slug>_ad.md`.

```markdown
---
title: "ZenSpace — Launch Reel"
video_type: reel
submode: P                      # P = polished-ad | U = UGC-style
length_target_sec: 28
aspect: 9:16                    # 9:16 | 1:1 | 16:9
voice: { name: female_excited, speed: 0.95 }
music: energetic                # energetic | chill | cinematic | none  (music_service prompt)
presenter: none                 # none (P) | circular | hallo | hybrid (U usually circular/hallo)
caption_style: kinetic_center   # the BIG pop captions (this skill's default)
brand_colors: ["#6C5CE7", "#0B0B12"]
cta: "Link in bio — first 100 get 40% off"
---

## scenes

### scene_01_hook            # 3s — pattern interrupt
narration: |
  Still editing videos for hours? Watch this.
on_screen: { caption: "Hours of editing?", layout: center }
visual: fast zoom on tired-creator b-roll; hard cut on the last word
duration_hint_sec: 3

### scene_02_product_reveal  # 3-4s — the hero
narration: |
  Meet ZenSpace.
on_screen: { caption: "Meet ZenSpace", layout: center }
visual: product hero shot, Ken-Burns push-in, glow pop on reveal
duration_hint_sec: 3

### scene_03_benefit_1
narration: |
  Type a topic. Get a finished video.
on_screen: { caption: "Topic → finished video", layout: center }
visual: app screenshot hero; benefit card slides up
duration_hint_sec: 4
# ... benefit_2, social_proof, then:

### scene_07_cta             # 3-4s — offer + logo
narration: |
  First hundred get forty percent off. Link in bio.
on_screen: { caption: "40% OFF — link in bio", layout: center }
visual: product + price card; brand logo; end on offer
duration_hint_sec: 4
```

Field notes: `caption` (not `title/body`) — captions are the on-screen text for ads; keep
1–4 words. `narration` short and spoken for the ear, F5-friendly. Hook MUST land its payload
in the first 3 seconds. 6–9 scenes for a 25–35s reel.

---

## 4. The build (deltas to the engine's staged pipeline)

Follow `production-video-trigunai` §4 (audio-first → assets → render-per-scene → concat →
verify). The ad-specific changes:

**Stage 1 — Audio.** Per-scene VO at ad pace (speed 0.9–1.0). Still **human-gate the audio.**
For UGC sub-mode, prefer a conversational F5 voice; for polished, energetic. Generate the
**music bed** here too (`music_service.generate_music(prompt, duration)`) so total runtime is known.

**Stage 2 — Assets (the one big difference).** Per scene, the *clip source* is product-shaped:
  - **Hero shots** — if the user gave product images, use them; else image-gen via the LiteLLM
    proxy (:4000, gpt-image-1.5) with the **constrained product prompt** in
    `reference/ad_asset_prompts.py` (studio backdrop, soft light, 9:16, negative space for the
    caption, NO text/watermark). One hero per "reveal"/"benefit" beat.
  - **Motion** — turn a hero still into a 2–4s moving clip with **Ken-Burns** push/pan
    (`reference/product_hero.py:ken_burns`) — cheap, reliable, on-brand. For premium reveals,
    use the engine's **LTX-Video i2v** path (Mode C `image_to_clip.py`) to get real generative
    motion; **boomerang** it for clean loops (engine §9 gotcha).
  - **B-roll** — lifestyle/problem shots (image-gen → Ken-Burns or LTX) for the hook/problem beats.
  - **Cutout** (optional) — isolate the product onto the brand-color/gradient bg with
    `reference/product_hero.py:cutout` (rembg) when you want the product to float over motion.
  Produce the same scene→asset manifest the engine expects.

**Stage 3 — Render + composite (per scene, then concat).** Per scene clip =
  `bg/hero motion (9:16)` + optional `product cutout (Ken-Burns)` + `text-safe scrim` +
  `BIG kinetic caption` + that scene's frozen audio. Recipe + helper:
  `reference/product_hero.py:compose_ad_scene` and the captions in
  `reference/kinetic_captions.py` (scale-pop, bottom-safe, brand color). UGC sub-mode also
  overlays the presenter (circular/Hallo) per engine §6 (hybrid only — full-length Hallo is
  a rabbit hole). Concat all scene clips, then **mix the music bed** ducked under the VO
  (sidechain, engine §5 audio recipe but music louder: ~−10 dB).

**Stage 4 — Verify + deliver.** Extract frames across hook/reveal/CTA, **Read them** to
confirm captions are legible inside the 9:16 safe area (keep text out of the top/bottom ~12%
where platform UI sits). Pull MP4, `open` it, ask the user to **watch with sound**. Deliver to
`course_assets/ad_out/`.

---

## 5. Ad-craft rules (the part that makes it convert, not just render)

- **3-second rule** — the hook's payload (problem, bold claim, price, before/after) must be on
  screen AND said within 3s. If it isn't, the scroll wins. Cut everything that delays it.
- **One message per cut** — 2–5s scenes; if a scene runs long, split it. Motion every beat.
- **Captions are not optional** — most feed views are muted. The caption must carry the message
  alone. Big, centered-bottom, 1–4 words, brand color, pop on the keyword.
- **Show the product doing the thing** — reveal it early (scene 2), show the outcome, not specs.
- **End on the offer** — last 3s = price/discount/CTA + logo. Always a single clear action.
- **Safe area** — keep text/logo inside the middle 76% vertically (platform UI eats top & bottom).
- **Honesty guardrails** (shared with the CEO OS): no fake reviews, invented ratings, or claims
  the product can't back. Use real social proof or none. No "industry-recognized" inflation.

---

## 6. Files shipped with this skill (reference/, adapt per job — like the engine's scripts)

- `reference/ad_asset_prompts.py` — constrained product/b-roll image-gen prompt templates
  (the heart of the style delta), the hook-pattern library, and a brief→ad-scene scaffolder.
- `reference/product_hero.py` — `ken_burns()` (still→motion clip), `cutout()` (rembg product
  isolation), `compose_ad_scene()` (9:16 hero + scrim + caption + audio per-scene recipe).
- `reference/kinetic_captions.py` — BIG center scale-pop captions from word timings
  (faster-whisper for timing, script text for spelling — engine §9 caption rule), RGBA overlay.

These run on EC2 alongside the engine's services (`/home/ubuntu/video-creator-backend/`).
`scp` them up, adapt the brief constants at the top, run. Same conventions as
`production-video-trigunai/reference/compose_welcome.py` and `patch_v4.py`.

---

## 7. Output + handoff

Deliver the finished vertical MP4 to `course_assets/ad_out/<slug>_ad.mp4`. State aspect,
duration, sub-mode, voice, music vibe, and the verification frames you checked. Then ask the
user to **watch with sound** and say **"lock it"** or what to tune (hook, pace, captions,
music level, CTA). Once locked, that build is the reusable template for the next ad in the set
— and the natural place to add a **batch / A-B variant** pass (same script, swap hook + music
+ first-frame, render N variants for testing — the e-commerce workflow).
