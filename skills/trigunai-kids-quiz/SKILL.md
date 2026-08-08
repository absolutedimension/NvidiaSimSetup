---
name: trigunai-kids-quiz
description: >
  Autonomous daily engine for the KIDS educational quiz videos — cartoon "Treasure Trackers"
  maths quizzes for Deepak's son (ICSE Grade 3), starring LEGO characters JJ (bunny) & Mikey
  (turtle), published to the TrigunAI-KidsEducation YouTube channel. Generates fresh Grade-3
  Maths questions across 18 topics, renders 4 videos/day on the EC2 render box (start→render→
  stop), and uploads them Made-for-Kids. Runs from the always-on Gurukul VM as the conductor.
  USE WHEN: "kids quiz", "kids video", "JJ and Mikey", "Treasure Trackers", "grade 3 maths video",
  "kids channel", "run the kids pipeline", "publish kids videos", "my son's videos", or to add a
  new topic/subject (GK, EVS) or a new day to the plan. Companion to trigunai-quiz-video (the
  parent exam engine) and maintain-trigunai-system.
---

# trigunai-kids-quiz — daily kids Maths quiz videos (Treasure Trackers)

Cartoon, treasure-hunt quiz videos for a Grade-3 (ICSE) child. Each video = one "adventure"
(one Maths topic) with 5 friendly questions, a countdown, celebrated correct-answer reveals
(which REPEAT the answer to reinforce it), a gem-collection bar, and a treasure finish. Hosts =
**LEGO JJ 🐰 (red-hood bunny + mic) & Mikey 🐢 (green turtle)**, animated (breathe/sway, hop on wins).

## Where things live
- **Engine + automation:** `NvidiaSimSetup/kids_quiz/` (this repo). Key files:
  - `make_kids_quiz_video.py` — renderer (cross-platform: bundled font + baked emoji PNGs → runs on Linux/EC2)
  - `assets/jj.png`, `assets/mikey.png` — LEGO sprites (regen via `assets/make_lego_characters.py`)
  - `assets/fonts/kid_rounded.ttf`, `assets/emoji/*.png` — bundled so EC2 needs no mac fonts
  - `gen_content.py` — Grade-3 Maths QUESTION GENERATOR, 18 topics, 5 fresh MCQs each (seeded → endless)
  - `plan_maths_15day.json` — 60 adventures (4/day × 15 days), all topics, weighted to core ops
  - `run_day_kids.py` — **DAILY DRIVER** (the conductor)
  - `publish_kids.py` — uploads to the kids channel (Made-for-Kids)
  - `com.trigunai.kidsquiz.daily.plist` — Mac launchd cron (alt to the VM cron)
- **Render box (EC2):** `34.192.145.204` = `i-047ebf759f2386e71` "TrigunAI-Omniverse" (us-east-1, stable EIP),
  `ubuntu@`, key `~/.ssh/trigunai_key.pem`, engine at `~/kids_quiz`. The pipeline STARTs it, renders, STOPs it.
- **Conductor (always-on):** Gurukul VM `dk_trigun@20.219.2.53` (key `~/.ssh/gurukul_key`). Runs the daily cron.
- **YouTube channel:** TrigunAI-KidsEducation, ID `UC9QWXw-M6W4eqo1dmbHYbLQ` (Brand acct under deepak@trigunai.com).
  Uploader = `youtube_series/yt_upload.py` with `YT_TOKEN=token_kids.json`.

## The daily flow (`run_day_kids.py`)
1. Skip if a `PAUSE` file exists.
2. day N from ANCHOR (2026-07-31); plan loops every 15 days, **seed = absolute day → fresh questions forever**.
3. Generate 4 content JSONs (`gen_content.py`).
4. **START EC2 if it's off** (never touches it if already running — someone may be using it).
5. rsync engine+assets+content → render the 4 **in parallel** on EC2 → pull the mp4s.
6. **STOP EC2 — only if this run started it** (never disrupts an in-use box).
7. Publish the 4 to the kids channel (Made-for-Kids). Log to `run_log.txt`.

Manual runs: `python3 run_day_kids.py --day N [--no-upload] [--privacy unlisted|public]`.
Pause: `touch kids_quiz/PAUSE`.

## PREREQUISITES / secrets (place once — these are Deepak's to install)
On whichever host runs the conductor (Gurukul VM for always-on, or the Mac):
1. **YouTube token (one-time OAuth, interactive):**
   `cd youtube_series && YT_TOKEN=token_kids.json /usr/bin/python3 yt_upload.py auth` → pick TrigunAI-KidsEducation.
   Then in YouTube Studio set the CHANNEL as "Made for kids".
2. **EC2 ssh key** `~/.ssh/trigunai_key.pem` (to reach the render box).
3. **AWS creds** for `ec2 start/stop/describe` on `i-047ebf759f2386e71` (least-privilege IAM user recommended).
4. **Python libs** on the conductor: `google-api-python-client google-auth-oauthlib` (for upload).

## GOTCHAS (learned the hard way)
- **Apple Color Emoji strikes:** PIL loads only sizes 20/32/40/48/64/96/160 — 137 throws. We sidestep this
  entirely by **pre-baking emoji to PNGs** (`assets/emoji/`), so EC2 (no color-emoji font) renders identically.
- **Parallel SSH render:** `cd dir && mkdir && pyA &` backgrounds the *cd* too → later jobs lose the cwd.
  Use `cd dir; mkdir; pyA & pyB & … wait` (`;` not `&&`). Fixed in run_day_kids.py.
- **Gurukul VM is LIVE (real students).** The conductor must stay LIGHT — it only generates + orchestrates +
  uploads; it NEVER renders on the VM (2 cores / ~2GB free). Schedule at a low-traffic hour; no service restarts.
- **EC2 = TrigunAI-Omniverse**, shared with RTX studio. The safe-stop logic (only stop if we started it)
  protects other work; keep it.
- Kids metadata carries NO exam CTA (it's a children's channel), unlike the parent quiz engine.

## Extending
- New topic: add a `g_<topic>` generator to `gen_content.py` (must yield ≥5 distinct 4-option Qs) + map in `GEN`.
- New subject (GK/EVS): new generator module + adventures; reuse the renderer + driver unchanged.
- New days: edit `plan_maths_15day.json` (`days[].slots[]` = {slot, topic, adventure, seed}).

See also: `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md` (curriculum map + design), memory `[[project-kids-quiz-video]]`.
