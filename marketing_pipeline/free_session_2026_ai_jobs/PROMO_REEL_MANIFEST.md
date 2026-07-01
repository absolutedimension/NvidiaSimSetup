# Promo Reel — "2026 AI Job Market" free session
### Build spec · vertical 9:16 · ~33s · music + kinetic text (no VO) · contextual b-roll

> Audio: `aijobs_house.mp3` (uplifting house, 124 BPM, build→drop). Drop lands at Scene 3 (~9s).
> CTA target: **learn.trigunai.com**. Brand: help-first, no "guaranteed job", no inflated proof.

| # | t (s) | Kinetic text (on-screen) | B-roll (image-gen → LTX clip) | Beat |
|---|---|---|---|---|
| 1 | 0–3 | **"Sent 200 applications.**<br>**Heard nothing."** | A tired young Indian man at night, glow of a laptop, inbox with "no reply", cinematic, desaturated, vertical | HOOK / pain |
| 2 | 3–9 | **"The entry-level jobs didn't vanish.**<br>**They changed shape."**<br><sub>↳ entry-level IT roles down ~25%</sub> | Empty office desks dissolving / a downward arrow over a city skyline at dusk, moody blue, vertical | TENSION (riser builds) |
| 3 | 9–18 | **"AI roles are EXPLODING."**<br>**1,000,000+ openings**<br><sub>~1 qualified person per 10</sub> | Bright modern GCC office, glass towers, engineers at AI dashboards, sunrise, hopeful, energetic, vertical | **TURN — DROP HITS** |
| 4 | 18–26 | **"The jobs go to people who**<br>**BUILD with AI."**<br>**You can become one.** | Over-the-shoulder of a young dev building an AI agent, code + a working app on screen, warm, empowering, vertical | AGENCY / lift |
| 5 | 26–33 | **Free live session**<br>**What to build first.**<br>**👉 learn.trigunai.com**<br><sub>register free</sub> | Clean brand-purple gradient + Trigun mark, confident, bright, vertical (or building montage freeze) | CTA |

## Style
- **Captions:** bold Poppins, word/line-reveal kinetic, high contrast white + purple accent (`#7a1fff`), safe lower-third + center for the punch lines. Beat-synced cuts (cut on the kick).
- **Color arc:** desaturated cold (S1–2) → bright warm/euphoric on the drop (S3–4) → brand purple (S5). The color lifts WITH the music.
- **Background loops:** boomerang each LTX clip for seamless motion.
- **Stat overlays:** small, sourced, honest (no fake precision).

## Pipeline (once music approved)
1. gen 5 contextual images (gpt-image-1.5, dark/cinematic, vertical 9:16) — `gen_assets.py`
2. start ComfyUI (manual) → LTX i2v → 5 bg clips → boomerang loops
3. kinetic-text overlay per scene (Poppins, beat timing) on transparent scrim
4. composite per-scene clips + `aijobs_house.mp3` → concat → `aijobs_promo_en.mp4`
5. verify frames → pull to Mac → watch with sound → lock
6. Hindi caption swap after EN locks

## Output
`course_assets/intro_out/aijobs_promo_en.mp4` (9:16). Then embed as the clickable hero on learn.trigunai.com with a Register button.
