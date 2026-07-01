---
name: add-trigunai-course
description: Add a NEW course to the TrigunAI Gurukul multi-course pipeline end-to-end — the AI-tutor concept bank (WhatsApp + web Acharya) plus the LMS catalog + course journey + the rich course-detail page. Use when Deepak says "add a new course", "add course X to the Gurukul / LMS", "build the curriculum for X", "make X teachable by Acharya", or wants a new course listed on acharya.trigunai.com and taught by the tutor. Covers the concept-bank schema, the LMS COURSES + landing-grid + course_details + seed entries, deploy, and verify. NO bridge restart needed — adding a course never disrupts live students.
---

# Add a new TrigunAI course (multi-course Gurukul)

The Gurukul teaches whatever course each student is registered for. A course = **(1) a tutor concept
bank** (data the bridge injects so Acharya teaches it) **+ (2) an LMS catalog entry + landing-grid card +
rich detail + journey**. Adding one is additive and **needs NO bridge/gateway restart** — students stay live.

> **DOMAIN TOPOLOGY (2026-06-30 — important):** **`acharya.trigunai.com` is now the CANONICAL course
> catalogue** (it serves the whole LMS). `lms.trigunai.com` still works but **301-redirects to acharya**,
> and **`learn.trigunai.com` is RETIRED** (also 301→acharya). The "main course page" a learner sees is:
> the gold landing `acharya.trigunai.com/` (hero + 9-course grid) and the picker `acharya.trigunai.com/login`
> (cards + syllabus + rich detail). Both are served by the SAME `lms` Container App. The whole UI is the
> **Acharya dark-gold brand** — read [[reference-acharya-brand]] before touching any course-facing markup.
> When adding a course you must update ALL the LMS surfaces below, not just `COURSES`.

## Architecture (what a course consists of)
| Piece | Where | Per-course? |
|---|---|---|
| Tutor concept bank | `agentic_cohort/gurukul_pipeline/courses/<id>.json` → VM `~/.openclaw/gurukul/courses/<id>.json` | YES — one file per course |
| Tutor teaching method (sequence, mastery-gate, hooks) | `gurukul-tutor` skill on the VM | shared — course-agnostic, never changes |
| Bridge (injects course + order + current step) | VM `~/wa_bridge.mjs` | course-agnostic — **don't touch it for a new course** |
| Per-student course tag | `students/<id>.json` `course` field; set via `add_student --course <id>` or LMS | — |
| **LMS catalog** (login picker + course title) | `lms/app/main.py` → `COURSES` list | YES — one entry |
| **Acharya landing grid** (`acharya.trigunai.com/`) | `lms/app/main.py` → `ACHARYA_BLURBS` (one-line blurb) + `ACHARYA_THUMBS` (`[shader_index, seed]`, shaders 0–5) | YES — one entry in each dict |
| **Rich course detail** (the "full details" learner page) | `lms/app/course_details.py` → `COURSE_DETAILS` (tagline, level, modules, duration, what_you_build[], curriculum[], prerequisites, outcome) | YES — full block |
| LMS journey (modules/lessons) | `lms/app/seed.py` → `<ID>_MODULES` / `<ID>_LESSONS` arrays | YES |

Key IDs: VM `dk_trigun@20.219.2.53` (key `~/.ssh/gurukul_key`). LMS = Azure Container App `lms` in RG
`trigunai-video-creator`, registry `trigunaicr`, **canonical domain `acharya.trigunai.com`**. Course ids
are kebab-case (e.g. `ml-and-math`) and must match across ALL surfaces.

## Inputs to gather
- **id** (kebab), **title** (full course name), and the **curriculum**: modules and, per concept,
  a `hook` (curiosity gap), a `recall` question, and the `answer` gist. Pull the curriculum from the
  course's source doc if one exists in the repo (e.g. `COMMAND_THE_CODING_AGENT_INDEX.md`).

## STEP 1 — Build the tutor concept bank  → `gurukul_pipeline/courses/<id>.json`
```json
{
  "course_id": "<id>",
  "name": "<Full Title>",
  "order": ["concept_a", "concept_b", "..."],          // STRICT teaching sequence
  "assessments": { "1": {"title":"...","url":"https://lms.trigunai.com/lesson/<slug>"} },  // optional, per module number
  "concepts": {
    "concept_a": {"module":1, "hook":"open a curiosity gap...", "recall":"the recall question?", "answer":"answer gist"},
    "...": {}
  }
}
```
- `module` groups concepts (for the module-checkpoint). `hook` opens the concept; `recall`+`answer`
  drive spaced repetition + grading. Mirror the style of `courses/agentic.json` / `courses/remote-swe.json`.

## STEP 2 — Deploy the bank to the VM (tutor goes live immediately, NO restart)
```bash
scp -i ~/.ssh/gurukul_key agentic_cohort/gurukul_pipeline/courses/<id>.json \
  dk_trigun@20.219.2.53:/home/dk_trigun/.openclaw/gurukul/courses/<id>.json
```
The bridge reads `courses/<id>.json` live. WhatsApp + web Acharya now teach `<id>` for any student whose
`profile.course == <id>`. (The `gurukul-tutor` skill is course-agnostic; the bridge injects the course.)

## STEP 3 — LMS catalog + landing grid + rich detail  (all in `lms/app/`)
Adding a course touches **four** data spots so it appears everywhere a learner looks:

**3a. `main.py` → `COURSES`** (login picker + course title):
```python
{"id": "<id>", "title": "<Full Title>", "ready": True},   # ready=False => shows "Coming soon"
```
**3b. `main.py` → `ACHARYA_BLURBS`** (one-line hook on the gold landing grid) **and `ACHARYA_THUMBS`**
(which live shader animates the card — index 0–5: 0 streams · 1 circuit · 2 particles · 3 orbit · 4 portal · 5 waveform, plus a time seed to vary reuse):
```python
ACHARYA_BLURBS["<id>"] = "Design agents that plan, use tools, and act on their own."
ACHARYA_THUMBS["<id>"] = [2, 0.0]   # pick the shader that best fits the course; vary seed if reusing one
```
**3c. `course_details.py` → `COURSE_DETAILS`** (the FULL course-detail block the learner page renders —
this is the rich content the old learn.trigunai.com page had):
```python
COURSE_DETAILS["<id>"] = {
    "tagline": "<one punchy hook>",
    "level": "<Beginner → Shipped>", "modules": <int>, "duration": "<3 months>",
    "what_you_build": ["<deliverable>", "..."],          # 2–4 concrete things they ship
    "curriculum": ["<module 1 one-liner>", "..."],       # full ordered module list
    "prerequisites": "<one line>", "outcome": "<one line — what they can do after>",
}
```
Mirror an existing entry's depth — every field filled, `curriculum` is the real module list. This is
what makes the course page feel complete; don't skip it.

## STEP 4 — LMS journey  → `lms/app/seed.py`
Add a modules array + wire it into the seed loop (course-keyed):
```python
<ID>_MODULES = [ (week, code, title, "", summary), ... ]   # week 0..N
# in run():  for course, mods in (("agentic", MODULES), ("remote-swe", SWE_MODULES), ("<id>", <ID>_MODULES)):
```
Optional `<ID>_LESSONS = [(week, slug, title, gems, available, sort), ...]` — wire it into the lessons
loop too. Each lesson `week` must match an existing Module week for the course.

## STEP 4.5 — Interactive lessons (Duolingo-style) — DON'T hand-write HTML
Lessons are data-driven: a shared engine + a per-lesson `STEPS` array. Pipeline (see [[project-lms-lessons]]):
1. Author `lms/lesson_src/<id>/<slug>.json` = `{slug,title,steps:[...]}` per `lms/tools/STEP_SCHEMA.md`
   (10 step types; first=intro, last=done, ~9–12 steps, one `reflect capture:true`). Scales well with
   parallel authoring agents — one per course, each fed the schema + the concept bank + an example lesson
   (`lms/app/lessons/what-is-an-agent.html`).
2. `python3 lms/tools/build_lessons.py` → validates + writes `lms/app/lessons/<slug>.html`.
3. Set those lessons `available=True` in `<ID>_LESSONS`. Deploy (STEP 5) ships the built HTML; the seed
   registers them. (This is LMS-side; the OpenClaw copy of this skill can't build lessons — needs the Mac repo.)

## STEP 5 — Deploy the LMS (Azure; bump the image tag)
```bash
cd lms
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
```
The seed migration + new modules apply on container startup.

## STEP 6 — Verify
- **Tutor:** mint a course token (`email|<id>|exp|hmac(CHAT_SECRET)` base64url) → POST `/chat/api` on
  `gurukul.trigunai.com` → Acharya welcomes to the right course. Or `openclaw agent` with the injected
  course context.
- **LMS:** `curl -s https://acharya.trigunai.com/login | grep "<Full Title>"` → the picker card shows;
  `curl -s https://acharya.trigunai.com/ | grep "<Full Title>"` → the landing grid card shows. Open the
  course on `/login` and confirm the **rich detail** (level · modules · duration · what-you-build ·
  curriculum) renders from `COURSE_DETAILS`.
- **Enrol a tester:** WhatsApp `node ~/.openclaw/gurukul/add_student.mjs --course <id> "Name:9198..."`,
  or web via `/admin/set-course?email=...&course=<id>`.

## RULES
- **Never restart `wa-bridge` / `openclaw-gateway` to add a course** — it's course-agnostic. Step 2 (scp) and
  Step 5 (LMS deploy) are independent and non-disruptive to live students.
- Course ids are kebab-case and must match between the bank filename, `COURSES`, the seed, and `add_student`.
- Keep repo copies in `agentic_cohort/gurukul_pipeline/courses/` so the VM and repo stay in sync.
- The full reference for the running system is on the VM at `~/.openclaw/docs/`.
