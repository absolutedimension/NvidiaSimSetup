---
name: acharya-student-frontend
description: >
  Control tower for the ACHARYA STUDENT EXAM-PREP FRONTEND — the self-serve product at
  acharya.trigunai.com/exam-prep where students (IIT-JEE Physics/Chemistry/Maths) take AI-generated
  practice tests, sit full JEE-Advanced mock papers, and track mastery. Load this for ANY work on the
  student-facing UI or flow: the Today screen, subject/chapter/subtopic pickers, the test engine
  (assess.html), exam mode, mock test series, Report & Improvement, saved test history, the
  challenge → 14-day trial → ₹199 funnel, or the pool-first question-serving model. Holds the route
  map, file map, data model, deploy recipe, the roadmap of what's built vs next, and — most
  importantly — the RENDER GOTCHAS that repeatedly broke this product in ways API tests could not
  see. Triggers on: "student frontend", "exam-prep UI", "Today screen", "Smart Practice", "mock
  paper", "test series", "exam mode", "syllabus map", "assess.html", "student dashboard", "improve
  the frontend", "acharya student". Companion to maintain-trigunai-system (owns the LMS deploy) and
  trigunai-assessment-backend-data (owns the question bank + /examgen API this consumes).
---

# Acharya — Student Exam-Prep Frontend

> **The product:** a student registers (goal = IIT-JEE), gets **14 days free → ₹199/mo**, and
> practises against a real question bank: targeted subtopic tests, full JEE-Advanced mock papers,
> and a mastery report that tells them what to fix next.
>
> **Live:** `https://acharya.trigunai.com/exam-prep` · **Current image: `lms:v94`**
> **Repo:** `~/Documents/01_Active/NvidiaSimSetup/lms` (FastAPI + Jinja2 + Postgres on Azure Container Apps)

---

## 0. ⚠️ READ THIS FIRST — the rule that matters most

**A green API test does NOT mean the product works.** Four separate bugs shipped this way in one
session: the API returned perfect JSON and the student saw a blank page or raw LaTeX.

**Before calling ANY student-facing change done, render it in a real browser.** The recipe:

```bash
# 1. capture a real pack/page, 2. serve it locally, 3. screenshot it
python3 -m http.server 8899 --directory /tmp/rendercheck &
# then use the browser tool: navigate → screenshot → click through a question
```
Answer a question. Check the maths. Check the solution box. **Look at it.**

---

## 1. Route map (all student-facing)

| Route | What it is | Template |
|---|---|---|
| `/` | Landing — **Student / Teacher split** | `acharya.html` (`.split` section) |
| `/exam-prep/quick` | The ad landing: 11-Q **free diagnostic** → sign in → dashboard. Logged-in users are redirected to the dashboard. | `exam_prep_quick.html` |
| `/exam-prep/start` (POST) | Email signup → session → **starts the 14-day trial** → dashboard | — |
| `/api/auth/google` (POST) | Google One-Tap signup (verified email, no magic link) → dashboard | — |
| **`/exam-prep/dashboard`** | **The "Today" home** — goal chip, mastery ring, chosen-for-you, Smart Practice, mode chips, focus areas, this week, My Topics | `exam_prep_dashboard.html` |
| `/exam-prep/smart` | **Smart Practice** — targets weakest + cold concepts, difficulty from real mastery → redirects into a test | — |
| `/exam-prep/subject/{topic_id}` | Subject detail — chapters → subtopic multi-select → build a test. Non-RAG subjects show "being set up" + logs a request | `exam_prep_subject.html` |
| `/exam-prep/test` | The test engine. `?src=examgen&subject=&sel=Chapter::Concept\|…&diff=&n=&fig=` for RAG tests | `static/exam/assess.html` |
| `/api/examgen/generate` | **Server-side proxy** to the question API (key never reaches the browser) | — |
| `/exam-prep/papers` | **Test series** — the shared pre-generated mock papers | `exam_prep_papers.html` |
| `/exam-prep/paper/{id}` | **Exam mode** — timer, palette, mark-for-review, no feedback | `exam_prep_paper.html` |
| `/api/paper/{id}/submit` (POST) | Scores server-side (JEE Advanced marking) | — |
| `/exam-prep/paper/result/{attempt_id}` | Scorecard + solutions | `exam_prep_paper_result.html` |
| `/exam-prep/report` | **Report & Improvement** — mastery SWOT, recommended difficulty, practise-next, saved tests | `exam_prep_report.html` |
| `/exam-prep/attempt/{id}` | Reopen a past test (questions + answers + solutions) | `exam_prep_attempt.html` |
| `/exam-prep/upgrade` | ₹199 Razorpay checkout | `exam_prep_upgrade.html` |

---

## 2. Files

```
lms/app/
  main.py                     routes + _prep_stats() + _student_topics/_add_topic + _chapter_for_concept
  examgen.py                  question API client: RAG_SUBJECTS, match_subject, get_chapters,
                              fetch_pool (POOL-FIRST), generate_pack, _to_pack_question, _wrap_pack
  mockpaper.py                mock-paper BLUEPRINT (derived from real papers) + score_attempt()
  models.py                   StudentTopic, ConceptStat, TopicAttempt, SeenQuestion, MockPaper, PaperAttempt
  config.py                   EXAMGEN_URL/KEY/TIMEOUT, ASSESS_* (₹199, 14-day trial), GOOGLE_CLIENT_ID
  static/exam/assess.html     THE TEST ENGINE (adaptive quiz; MathJax; figures)
  templates/exam_prep_*.html  all the screens above
lms/tools/build_mock_papers.py  batch generator for the shared mock-paper series
```

---

## 3. Data model (what powers the UI)

| Table | Purpose |
|---|---|
| `StudentTopic` | the student's topics, **max 5** (`MAX_TOPICS`) — the ₹199 unit |
| `ConceptStat` | per-concept running mastery: `seen`, `correct` (solid=1 / shaky=0.5 / weak=0) → **mastery, focus areas, Smart Practice targeting** |
| `TopicAttempt` | one finished test: score, total, concepts, **`detail`** = the full paper (reopenable) → streak, weekly stats, history |
| `SeenQuestion` | question IDs already served → passed to `/pool` as `exclude` (no repeats) |
| `MockPaper` | **shared** pre-generated mock papers (not per-student) |
| `PaperAttempt` | a student's sitting of a MockPaper (answers, marks, timing) |

> **Progress tables are deliberately NOT gated by `LOOP_CAPTURE_ENABLED`** — that flag governs the
> Acharya *learning loop* (DPDP consent). A student's own product progress is separate.

---

## 4. How questions are served (POOL-FIRST)

```
generate_pack()
  1. GET /pool   → instant, no LLM, no auth   ← preferred
  2. whatever the pool can't cover → POST /generate (slow: ~40-55s/question on gpt-5.5)
```
- **`/pool` may be 404** (backend hadn't deployed it as of 2026-07-23) — `fetch_pool()` returns
  `None` and the code falls back automatically. **When the backend ships the pool, tests get
  instant with NO code change here.** Verify with: `curl <EXAMGEN_URL>/pool?...`
- `EXAMGEN_URL` default = `https://gurukul.trigunai.com/examgen` (always-on VM; survives EC2 stop).
  **Keep the default on gurukul** — the old `rtx.trigunai.com` lives on an EC2 box that gets powered off.
- Subjects live in `examgen.RAG_SUBJECTS`: **jee-physics (18 ch) · jee-chemistry (25) · jee-maths (27)**.
  Adding JEE Main = one entry per subject. `match_subject()` maps a topic title → subject id.

---

## 5. Deploy + verify

```bash
cd ~/Documents/01_Active/NvidiaSimSetup/lms
python3 -m py_compile app/*.py                 # always
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
# WAIT for 100% traffic before testing — stale-revision reads cause false failures:
az containerapp revision list -n lms -g trigunai-video-creator \
  --query "[?properties.trafficWeight==\`100\`].properties.template.containers[0].image" -o tsv
curl -s -o /dev/null -w "%{http_code}\n" https://acharya.trigunai.com/healthz
```
**Local smoke tests** need python3.11 (`/tmp/lmsv` venv) — the app uses 3.10+ union syntax and
system python3 is 3.9. Use SQLite + `Base.metadata.create_all` and `starlette.testclient`.

> **Bump the tag every time.** Reusing a tag does NOT roll a new revision.

---

## 6. 🔴 GOTCHAS — every one of these actually broke the product

**Rendering (all invisible to API tests):**
1. **Pack missing `intro` → the whole test renders BLANK.** The engine's `intro()` does
   `S.intro[LANG]`; no key = TypeError = nothing. `_wrap_pack()` always emits it — don't remove.
2. **MathJax `skipHtmlTags` must NOT contain `'button'`** — the MCQ options *are* `<button>`s, so
   they rendered as raw `$\dfrac{}{}$`.
3. **MathJax loads async → typeset must POLL.** At first paint `window.MathJax` is only the *config*
   object (no `typesetPromise`), so a one-shot call silently no-ops forever. Both `assess.html` and
   `exam_prep_paper.html` use a retry loop.
4. **Anything appended to the DOM AFTER the initial render must be typeset explicitly** — the
   solution/feedback box is appended post-answer; that's what `fbAdd()` exists for.
5. Question stems/options/solutions are LaTeX with **both** `$…$` and `\(…\)` delimiters — configure both.

**Backend/infra:**
6. **gunicorn `--timeout` must be 240** (Dockerfile). At 60 it killed the worker mid-generation and
   returned an **empty response** at ~61s.
7. **Never exceed ~4 concurrent requests to `/examgen`** — 10 workers took `qbank-api` down (stuck
   "deactivating") on the 3.9 GB Gurukul VM that also runs the LIVE WhatsApp tutor.
8. Batch generation needs a **≥420s** client timeout: the backend does generate(≤180s) + key-withheld
   validate(≤180s) per question.
9. `qbank/llm.py` on the VM had `OpenAI(timeout=45)` → ~30% of gpt-5.5 calls 500'd. Raised to 180.
   **If the backend agent redeploys that file, re-apply it.**

**Correctness:**
10. **The exam page MUST strip `correct` + `solution`** before sending questions to the browser.
    There's a smoke test asserting no leak — keep it.
11. **A test often repeats one concept.** Upserting `ConceptStat` per result created duplicate rows →
    unique-constraint violation → **500 → the whole test silently failed to save.** Use a
    per-request cache (a pending row is invisible to a re-query).
12. **Cache chapters PER SUBJECT.** One shared slot served Physics chapters for Chemistry.
13. **Don't fabricate metrics.** XP / cohort rank / spaced-revision schedules aren't tracked — omit
    them rather than print fake numbers on a student's own progress screen.

---

## 7. Built vs NEXT (the frontend roadmap)

**✅ Built:** Student/Teacher split landing · challenge diagnostic · 14-day trial → ₹199 ·
**Today screen** (mastery ring, chosen-for-you, Smart Practice, mode chips, focus areas, this week) ·
subject → chapter → subtopic picker (3 subjects) · adaptive test engine w/ MathJax + SVG diagrams ·
**mock test series** (5 papers, exam mode, negative marking, solutions) · **Report & Improvement** ·
saved test history · pool-first serving · no-repeat tracking.

**🔜 Next (from `question_bank_engine/FRONTEND_HANDOFF_POOL.md` §5 + blueprint):**
1. **Syllabus Map** — every chapter with fillable mastery bars, expandable to concepts, filters
   (All / Weak / Untouched / Strong). *The breadth-discovery screen; highest-value remaining piece.*
2. **Subject-strength radar** on Today (data exists in `ConceptStat`, needs chapter grouping).
3. **Onboarding** — explicit goal pick (IIT-JEE / NEET) + quick diagnostic. Goal is currently
   *inferred* from the student's topics.
4. **Practice screen polish** — bookmark, confidence tap, progressive hint→solution, report-issue.
5. **Mock papers**: currently **15-16 of 17** questions (1-2 generations time out per paper) and
   Physics-only. Needs a retry pass for full 17s; Chemistry/Maths papers need their own blueprint
   derived from those subjects' real per-year type mix.
6. XP / streak rewards / cohort rank — only if you decide to actually track them.

---

## 8. Design system

Warm "Saffron Dawn" light theme (student surfaces): `--gold:#C2591F` `--gold2:#A8481A`
`--ink:#2A2018` `--muted:#7A6A57` `--line:#EFE0CE` `--cream:#FAF5EC`; serif = **Bricolage
Grotesque** (headings), sans = **Figtree**, Devanagari = Tiro. Mobile-first, max-width 560-620px on
task screens, 1040px on Today. Brand rules: `[[reference-acharya-brand]]`.

**Related:** `[[project-acharya-student-product]]` (full build history + decisions) ·
`maintain-trigunai-system` (LMS deploy/infra) · `trigunai-assessment-backend-data` (question bank + API).
