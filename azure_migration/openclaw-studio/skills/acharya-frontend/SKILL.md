---
name: acharya-frontend
description: "The FRONTEND agent for Acharya — the student exam-prep app, the teacher/institute B2B app, AND the landing pages, all served by the `lms` container app at acharya.trigunai.com. Use whenever Deepak wants to change/deploy the student flow (exam picker, onboarding, Today screen, test engine, mock papers, report), the teacher flow (create test, share link, class dashboard, printable), the Acharya landing page, wire a new EXAM into the student app, fix a UI/render bug, or ship a frontend change LIVE. Triggers: 'the frontend', 'acharya app', 'exam-prep UI', 'teacher app', 'student flow', 'landing page', 'wire exam X to the LMS', 'deploy the lms', 'add a subject to the app', 'the Today screen', 'fix the UI', 'change pricing on the site'. CODE changes → edit via `trigun-coding` (Codex) on the Gurukul box, then deploy with the helper below. Sibling of `qbank-data` (the DATA backend this frontend consumes via the examgen API). NOT for the question bank itself (that's qbank-data), audio/video (studio-*), or the WhatsApp tutor (Maya/gurukul)."
metadata: { "openclaw": { "emoji": "🖥️", "requires": { "bins": ["ssh","scp"] } } }
---

# acharya-frontend — the Acharya student + teacher + landing app

You maintain the **`lms` container app** (`acharya.trigunai.com`). You EDIT its code via Codex on the
Gurukul box and DEPLOY it with a helper (service principal → ACR build → container app). You never
hand-edit prod; you change the repo, deploy, and **verify in a real browser**.

## Where the code lives + how to reach it
`source ~/.openclaw/qbank.env` (GURUKUL, GKEY). The frontend is a **git repo on the Gurukul box**:
`~/acharya_frontend` (FastAPI + Jinja2 + Postgres, Azure Container App). Run everything via
`ssh -i $GKEY $GURUKUL '<cmd>'`.

## The three surfaces (one codebase, one question engine, one test engine)
- **STUDENT** `acharya.trigunai.com/exam-prep` — exam picker → email/Google signup → 14-day trial →
  goal onboarding → Today screen → practice tests / mock papers / report. Engine = `static/exam/assess.html`.
- **TEACHER** `acharya.trigunai.com/teacher` — create a real JEE/NEET/CBSE test → share `/t/{code}` (students
  take with NO signup) → live weak-topic dashboard. Same `assess.html` in class-test mode.
- **LANDING** `acharya.trigunai.com/` (`templates/acharya.html`) + `/exam-prep` landing.

## Key files (`~/acharya_frontend/app/`)
- `main.py` — ALL routes + `STUDENT_EXAMS`/`EXAMS` (the exam picker) + student/teacher/chat blocks.
- `examgen.py` — the question-API client: **RAG_SUBJECTS**, **GOALS**, **DIFFICULTY_LADDER**, `match_subject`.
  This is what maps a student's exam/subject to the live question bank (the `qbank-data` backend).
- `models.py`, `seed.py` (`_migrate()` ALTERs for new columns), `config.py` (env/secrets), `mockpaper.py`.
- `templates/` — `exam_prep*.html` (student), `teacher_*.html` (teacher), `acharya.html` (landing),
  `static/exam/assess.html` (THE test engine — MathJax, figures, EN/हिं).

## To CHANGE the frontend → Codex on Gurukul, then deploy
1. Edit via **`trigun-coding`** (Codex) pointed at `~/acharya_frontend` ON the Gurukul box (Codex there uses
   gpt-5.6-terra via the litellm proxy). Make the smallest change; match style. `git commit` in the repo.
2. Deploy: `ssh -i $GKEY $GURUKUL 'cd ~/acharya_frontend && ./lms_deploy.sh'`
   — compiles, builds `lms:vN` (auto-bumped) in ACR via the service principal, rolls the container app,
   waits for 100% traffic, prints `healthz`. (Pass a tag to override: `./lms_deploy.sh v120`.)
3. **VERIFY in a real browser** — a 200/health is NOT proof the UI works (see gotchas). Tell Deepak the
   URL to eyeball, or screenshot it.

## Wire a NEW exam into the student app (so students can pick it)
In `~/acharya_frontend/app/examgen.py`: add the subject(s) to **RAG_SUBJECTS** (its `exam`+`subject` must
EXACTLY match the bank on the examgen API, e.g. `"CBSE Class 12"/"Physics"`), add a **GOALS** entry, add a
**DIFFICULTY_LADDER** band (boards `2/2-3/3`). In `app/main.py`: flip the exam to `available: True` in
**STUDENT_EXAMS** + point its **EXAMS** `subject` at a real RAG id. New DB columns need an ALTER in
`seed._migrate`. Then `./lms_deploy.sh` + browser-verify. (The bank must already be live — that's `qbank-data`.)

## 🔴 GOTCHAS (each actually broke the product — invisible to API tests)
- **Always render in a browser after a change** — bugs that shipped green: blank test (missing `intro`),
  raw `$…$` (MathJax `skipHtmlTags` must NOT include `button`), un-checked radio (a `<label>` around a
  hidden radio doesn't reliably check it — set `input.checked=true` in JS), missing diagram (`figure_url`-only).
- **Per-exam difficulty band** — asking a NEET test at JEE's `3-4` returns no exemplars. Use `difficulty_ladder(subject)`.
- **The class-test / student / curated completion branches in `assess.html` are distinct** — keep `__CLASSTEST` first.
- **Bump the image tag every deploy** (the helper does). gunicorn timeout is 240s. **≤4 concurrent to examgen.**
- **Don't paywall/regress existing students** (`grandfathered` cohort). Secrets stay server-side (container secrets).

## State (2026-07-25)
Live ≈ `lms:v105` (deployed from the Gurukul repo via the helper). Student + teacher + chat + landing all
shipped. Exams LIVE: JEE, NEET, **CBSE Class 10 + Class 12** (Science/PCB), Banking Quant. `trigunai.com`
(the OTHER public homepage) is a SEPARATE repo (`ShaderStudio`) in a different Azure sub — not this skill yet.
