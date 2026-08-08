---
name: trigunai-quiz-video
description: "Produce a finished, narrated, animated QUIZ / ASSESSMENT video (vertical 1080x1920) for the Acharya assessment engine — exam-prep quiz shorts that 'hold the student' with a ticking countdown timer, then reveal the answer with celebration + a one-line explanation. Multi-template (MCQ, Match-the-Following, and more from the catalog), bilingual EN + हिंदी, alive neural voice, soft living Acharya background, isochronic focus tone. Use when the user wants a 'quiz video', 'assessment video', 'quiz reel/short', 'MCQ video', 'match the following video', 'daily quiz post', 'test video for students', or the daily engine needs the day's quiz. Renders on the EC2 farm; posts via studio-social (IG+FB) + studio-youtube — the SAME posting flow as reels. NOT for teaching/explainer video (studio-video) or product reels (studio-reel)."
metadata:
  openclaw:
    emoji: "🧩"
    os:
      - linux
      - darwin
    requires:
      bins:
        - ssh
        - scp
---

# trigunai-quiz-video — Quiz / Assessment Videos

The video arm of the Acharya **assessment engine**. Turns a content JSON into a finished
vertical MP4: countdown timer → answer reveal → celebration → CTA. Self-contained
(PIL + edge-tts + ffmpeg + numpy), **CPU-only**, renders on the EC2 farm in ~7 min.
No GPU, no avatar box needed.

## When to Use
✅ Daily quiz/assessment shorts for exam prep (JEE/NEET/Boards/…), single-topic, 60–90s.
✅ MCQ, Match-the-Following, and other formats in `ASSESSMENT_TEMPLATE_CATALOG.md`.
✅ Bilingual: render an English AND a Hindi cut from a paired JSON.

## When NOT to Use
❌ Teaching / explainer / module video → `studio-video`.
❌ Product or thought-leadership reel → `studio-reel`.
❌ Audio only → `studio-music`.

## Where it lives (already deployed)
- **Render box:** EC2 farm — `~/.openclaw/ec2.env` → `EC2_IP=34.192.145.204`, `EC2_USER=ubuntu`, `EC2_KEY=~/.ssh/trigunai_key.pem`.
- **Engine on the box:** `/home/ubuntu/quiz_video/make_quiz_video.py` (+ `content/`).
- **One-time setup (done):** `setup_farm.sh` installed `fonts-noto-core` (Devanagari + Latin superscripts) and confirmed edge-tts / numpy / Pillow-with-raqm. Re-run it only if a render fails on a missing-font error.

## Content JSON schema
One file = one video. Pair an `_en.json` and `_hi.json` for the bilingual cut.

```jsonc
{
  "lang": "en",                       // "en" | "hi"  → drives fonts + UI microcopy
  "voice": "en-IN-NeerjaExpressiveNeural",  // hi → "hi-IN-SwaraNeural" (or "hi-IN-MadhurNeural" male)
  "subject": "Physics",               // header + intro
  "chapter": "Units & Measurements",
  "topic_line": "Chapter 1 · where every aspirant begins",
  "timer_seconds": 5,                 // countdown per question
  "cta": "Get your full adaptive test on Acharya",
  "intro_voice": "…",                 // spoken hook (voice-only)
  "outro_voice": "…",                 // spoken CTA (also shown on outro)
  "questions": [
    { "type": "mcq", "q": "…", "options": ["…","…","…","…"], "answer": 1,
      "explain": "…", "voice_q": "…", "voice_a": "…" },
    { "type": "match", "prompt": "…",
      "left": ["Force","Pressure","Energy","Power"],
      "right": ["Pascal","Watt","Newton","Joule"],   // shown shuffled
      "pairs": [[0,2],[1,0],[2,3],[3,1]],            // left idx → right idx (correct)
      "explain": "…", "voice_q": "…", "voice_a": "…" }
  ]
}
```
Notes: `answer` is 0-based. `voice_q`/`voice_a` are what the narrator SAYS (write S.I. as "एस.आई." / "S I" for clean TTS). Keep option text short. Hindi = full Devanagari; EN formulas may use unicode superscripts (⁻¹ ²). See `ASSESSMENT_TEMPLATE_CATALOG.md` for all 18 formats + a weekly posting rhythm.

## Produce a video (the ONLY correct path)
1. **Resolve the farm** and make sure it's up (retry — sshd is intermittent):
```bash
source ~/.openclaw/ec2.env
SSH(){ ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"; }
for i in 1 2 3 4 5; do SSH 'echo up' 2>/dev/null | grep -q up && { UP=1; break; }; sleep 8; done
[ -z "$UP" ] && { echo "farm down — start EC2 (TrigunAI-Omniverse), IP stays 34.192.145.204"; exit 1; }
```
2. **Push the content JSON(s)** Deepak gave you (write them locally first, show him, get a yes):
```bash
scp -i "$EC2_KEY" quiz_en.json quiz_hi.json "$EC2_USER@$EC2_IP":/home/ubuntu/quiz_video/content/
```
3. **Render** (both cuts, detached, in parallel — each ~7 min on the A10G box's CPUs):
```bash
SSH 'cd ~/quiz_video && setsid nohup python3 make_quiz_video.py content/quiz_en.json out_en.mp4 >/tmp/q_en.log 2>&1 </dev/null & \
                        setsid nohup python3 make_quiz_video.py content/quiz_hi.json out_hi.mp4 >/tmp/q_hi.log 2>&1 </dev/null &'
# poll: SSH 'tail -3 /tmp/q_en.log /tmp/q_hi.log; ls -la ~/quiz_video/out_*.mp4'
```
The engine prints `✅  <out>` when done. **Never write your own render_*.py** — always drive `make_quiz_video.py`. If a step's tool is missing, STOP and report.

## Post it (reuses the existing pipeline — "one template added")
The render box **is** the post box, so the MP4 is already where `studio-social` needs it.
- **IG + Facebook** → hand `out_en.mp4` (and/or `out_hi.mp4`) to **`studio-social`** (hosts on `rtx.trigunai.com/reels`, posts as a Reel). Caption = hook + CTA + 3–5 exam hashtags (`#JEE #NEET #Physics …`), `?utm_source=ig`.
- **YouTube Short** → **`studio-youtube`** (English → main channel; Hindi → the Hindi channel).
- **LinkedIn / Stories** → not automated; deliver to Deepak on Telegram.

## Daily engine hook (`studio-daily`)
A quiz day in `~/.openclaw/content_plan.json` sets `"format": "quiz"` (+ a `quiz_en`/`quiz_hi` content ref). `studio-daily` then: ensure farm → **this skill** renders both cuts → `studio-social` posts EN to IG/FB → `studio-youtube` posts EN Short (main) + HI Short (Hindi channel) → log. Honors `~/.openclaw/PAUSE_DAILY`. Content is authored by Deepak (or a content skill) — this skill never invents quiz questions.

## Voices
- EN: `en-IN-NeerjaExpressiveNeural` (expressive female). Male alt: `en-IN-PrabhatNeural`.
- HI: `hi-IN-SwaraNeural` (female). Male alt: `hi-IN-MadhurNeural`.

## Guardrails
- The MP4 is self-branded (ACHARYA header + CTA); the T4 talking-avatar intro is **optional** for this format (full-screen quiz, not a talking head) — only add it if Deepak asks.
- Timer default 5s; keep options terse so cards stay clear.
- One JSON → one language. Bilingual = two JSONs, same questions.
