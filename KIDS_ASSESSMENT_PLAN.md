# Kids Education on Acharya — Grade 3 (ICSE) Implementation Plan

> **Goal:** stand up a Kids Education category (starting **Grade 3, ICSE, Maths first**) on the
> **existing** `acharya.trigunai.com` pipeline. Same app, same test engine, same teacher flow, same
> mastery tracking — **only the data + taxonomy change**, plus ~4 frontend config edits and (optionally)
> a kid-friendly theme later.

---

## The key realization

Adding "Grade 3" is **identical to how JEE / NEET / UPSC / CBSE-10 / CBSE-12 were added.** The pattern
(proven 5×) is:

```
Backend:  taxonomy (syllabus.py)  →  data into the bank/pool  →  /pool + /generate serve it
Frontend: examgen.py (RAG_SUBJECTS + GOALS + DIFFICULTY_LADDER + match_subject)
          + main.py (EXAMS + STUDENT_EXAMS + EXAM_SUBJECT)  →  deploy lms:vN
```

- **No database migration** — no new columns or tables. (New exams are pure config + data.)
- **No test-engine changes** — `assess.html`, the teacher class-test flow, mastery (`ConceptStat`),
  reports, mock papers all work unchanged the moment the data + config exist.
- **The one twist for kids Maths:** the data source. See Phase 1.

---

## The one twist: Maths doesn't need RAG — it needs the generator we already built

For JEE/NEET the bank is **RAG over real past-paper exemplars** (because those answers require reasoning).
**Grade-3 Maths is arithmetic — exactly computable.** We already have `kids_quiz/gen_content.py`, which
**computes** correct answers (18 topics). So for kids Maths we **don't train RAG** — we run the generator
and load its output straight into the question pool as `generated=1, verified=1` rows.

| | JEE / NEET / UPSC | Grade-3 Maths | Grade-3 EVS / GK / English (later) |
|---|---|---|---|
| Source | RAG over real bank + LLM | **`gen_content.py` (computed)** | RAG grounded on Grade-3 content **or** real textbook via the exact-question PDF pipeline |
| Correctness | validated / real keys | **guaranteed (it's maths)** | validated / real |
| Cost | Azure tokens | **free, offline** | tokens / one-time extraction |

**Bonus synergy:** the *same* `gen_content.py` already feeds the **Treasure Trackers videos**. One generator
→ both the YouTube funnel **and** the practice app. When we add EVS/GK, RAG (the exam engine) or the
textbook-scan pipeline covers the non-computable subjects.

---

## Phase 0 — Decisions (lock these first)

1. **Exam string:** `"ICSE Class 3"` (matches the `"CBSE Class 10"` convention). Subject: `"Mathematics"`.
2. **IDs:** RAG subject `icse3-maths`; goal `class3` (label "Class 3 · ICSE"). (Room for `icse3-evs`,
   `icse3-english`, `icse3-gk` later.)
3. **Difficulty band:** Grade 3 = **easiest** → `DIFFICULTY_LADDER["ICSE Class 3"] = ("1","1-2","2")`.
4. **Domain:** reuse `acharya.trigunai.com` (fastest). Optionally point **`kids-education.trigunai.com`**
   at the same app later (a kids landing that deep-links into `/exam-prep?exam=class3`).
5. **Who's the buyer?** A Grade-3 child can't self-serve/pay like a JEE student — the buyer is the
   **parent** (or a **primary-school teacher** via the teacher flow). This shapes the funnel (Phase 4),
   not the build.

---

## Phase 1 — Backend: Grade-3 Maths into the pool  (~half day)

**All in `question_bank_engine/` (live on the Gurukul VM).**

1. **Taxonomy** — new `qbank/grade3_maths.py`: the 11 ICSE Class-3 Maths chapters → concepts → keywords
   (from `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md`), mapping each chapter to its `gen_content.py` topic(s).
   Register: `TAXONOMIES[("ICSE Class 3","Mathematics")] = GRADE3_MATHS`.
2. **Ingest adapter** — new `qbank/ingest_grade3_maths.py`: run each `gen_content` generator → convert each
   question to a `Question` row (`exam="ICSE Class 3"`, `subject="Mathematics"`, `chapter=<chapter>`,
   `concept=<topic>`, `stem=q`, `options`, `correct_answer=<letter>`, `solution=explain`,
   `difficulty="1-2"`, `qtype="MCQ_single"`, `generated=1`, `verified=1`) → `store.upsert`. Loop to fill
   ~50–100 per chapter → an instant pool of ~600–1,000 Qs, all correct-by-construction.
   *(This is a new "computed generator" source — simpler than any RAG ingest because there's nothing to
   solve or verify.)*
3. **Serving** — `/pool` already serves `generated=1` rows, so no bypass needed (unlike the CBSE/UPSC
   real-PYQ bypass). Back up `data/qbank.sqlite` first; run the ingest on Gurukul (or the worker VM);
   `sudo systemctl restart qbank-api`.
4. **Verify:** `curl ".../examgen/chapters?exam=ICSE%20Class%203&subject=Mathematics"` and
   `.../examgen/pool?exam=ICSE%20Class%203&subject=Mathematics&count=5`.

---

## Phase 2 — Frontend: wire Grade 3 into the app  (~2–3 hrs — the proven UPSC/CBSE edit set)

**All in `lms/` (repo `~/Documents/01_Active/NvidiaSimSetup/lms`).**

1. **`app/examgen.py`:**
   - `RAG_SUBJECTS["icse3-maths"] = {exam:"ICSE Class 3", subject:"Mathematics", title:"Class 3 · Maths"}`
   - `GOALS["class3"] = ["icse3-maths"]` (+ label)
   - `DIFFICULTY_LADDER["ICSE Class 3"] = ("1","1-2","2")`
   - `match_subject` entries so "Class 3 Maths" resolves.
2. **`app/main.py`:**
   - `EXAMS["class3"] = {label:"Class 3 · ICSE", subjects:["icse3-maths"], available:True}`
   - add to `STUDENT_EXAMS` (available) + `EXAM_SUBJECT["class3"] = "icse3-maths"`.
3. **Onboarding** (`exam_prep_onboarding.html`) picks it up from `GOALS` automatically — Grade 3 appears
   as a goal, subject multi-select works.
4. **Deploy** `lms:vN` (build-from-`/tmp` snapshot recipe — §0.2 of the frontend skill) → **verify in a
   real browser** (§0 rule): pick Class 3 → take a Maths test → check questions render + mastery saves.

That's a working Grade-3 Maths practice product on the existing app — student self-practice, **teacher can
create Class-3 tests and share a no-signup link**, mastery + reports, all reused.

---

## Phase 3 — Kid-friendly UI layer  (optional, AFTER Phase 1–2 prove the loop)

The current "Saffron Dawn" exam theme *works* for kids but reads adult. A **"kids mode"** (keyed off
`goal == class3`) would add: bright playful palette, big rounded cards, **JJ & Mikey mascots**, picture
answer options, encouraging (non-shaming) feedback, gentler/no timer. This is more than "minimal UI," so
it's a deliberate later phase — the assessment loop is identical underneath.

---

## Phase 4 — Funnel / GTM (parent-buyer)  — where the videos connect

- **Top of funnel = the Treasure Trackers YouTube channel** (already live) → description links to
  **kids-education.trigunai.com** → a kids landing → free trial of the Class-3 practice app.
- **Buyer = parent** (signs up for the child) **or primary teacher** (creates & assigns tests — the B2B
  flow already exists). Pricing/copy targets parents ("help your child master Class-3 maths"), not the kid.
- Same Razorpay plumbing as the student product (currently inert → WhatsApp close).

---

## Data expansion after Maths (same category, more subjects)

| Subject | How | Effort |
|---|---|---|
| **Maths** | `gen_content.py` → pool (Phase 1) | done-ish |
| **EVS / Science, Social, GK** | RAG-generate grounded on Grade-3 exemplars, **or** real textbook via the exact-question PDF pipeline (scan his books) | medium |
| **English (grammar/vocab)** | partly generatable (opposites, tenses, plurals) + RAG for comprehension | medium |
| Other grades (1, 2, 4, 5…) | repeat the whole pattern — taxonomy + generator/RAG per grade | scales linearly |

---

## Smoothest path (recommended order)

1. **Phase 1 + Phase 2 for Grade-3 Maths** → ~1 day → **live Class-3 Maths practice on Acharya** (student
   + teacher), reusing everything.
2. Watch real usage (even your son + a few parents) → decide if **Phase 3 kids-theme** is worth it.
3. Add **EVS / GK** (Phase-1 pattern with RAG or textbook scans) to broaden the category.
4. Wire **kids-education.trigunai.com** + the video funnel (Phase 4).

**Effort:** Maths end-to-end ≈ **1 focused day** (mostly the ingest adapter + the 4 config edits + a
browser-verified deploy). No migrations, no engine rewrites — that's why this is smooth.

**One honest CEO note:** this is a *build*, and the company gate is still "0 paid." It's a smart build
(reuses the pipeline, opens the huge primary-K12 market, and the video channel gives it a real top-of-
funnel) — but pair it with a *sell* motion (parents/teachers) from day one rather than only shipping the
category. Start Maths, get one parent/teacher using it, then expand.

---

## Appendix — exact files to touch (nothing else)

**Backend (`question_bank_engine/`):** `qbank/grade3_maths.py` (new) · `qbank/syllabus.py` (register) ·
`qbank/ingest_grade3_maths.py` (new adapter over `kids_quiz/gen_content.py`) · deploy to Gurukul + restart.
**Frontend (`lms/app/`):** `examgen.py` (RAG_SUBJECTS, GOALS, DIFFICULTY_LADDER, match_subject) ·
`main.py` (EXAMS, STUDENT_EXAMS, EXAM_SUBJECT) · deploy `lms:vN` + browser-verify.
**No changes to:** models/seed (no migration), `assess.html` (engine), teacher flow, mock papers, mastery.
