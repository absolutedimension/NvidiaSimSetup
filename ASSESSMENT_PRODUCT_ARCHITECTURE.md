# Acharya Assessment — the two-section product architecture

> Decided 2026-07-29 (Deepak). The exam-prep product has **two clearly separated sections**, both
> anchored in REAL questions. Companion to `VISION.md` (the sequencing) and
> [[reference-mock-paper-test-series]] (the mock-paper engine). Owner: Deepak.

## The two sections

**Section A — Real-exam simulation ("attempt the real thing").**
Take REAL past questions in a real exam environment — full paper, real pattern, timed, no feedback
until submit. A faithful simulation of the actual test.
- Source: the REAL question pool (`/pool` serves verified real PYQs) + real papers Deepak ingests
  over time (via `exact-question-making-pipeline-from-pdf`).
- Surface today: the **test series** (`/exam-prep/papers`) — mock papers built from real questions
  (UPSC = real GS+CSAT PYQs; boards = real NCERT; JEE/NEET = real-format).
- Value: authenticity + exam-day realism. This is the "am I ready?" section.

**Section B — Daily practice (RAG-generated, but AUTHENTIC because it's grounded in real questions).**
Subject- and subtopic-wise practice, unlimited, generated on demand.
- Source: the SAME RAG generator (`/generate` + pre-filled `/pool`) that JEE/NEET use — it retrieves
  REAL banked questions as **exemplars** and authors NEW questions in that exact pattern/quality.
  Grounding in real exemplars is *why* the generated questions are authentic, not generic.
- Value: infinite fresh practice, targeted at weak subtopics, copyright-clean by construction.
- Verified 2026-07-29: `/generate` already produces valid grounded questions for **UPSC and CBSE**
  (10/12/Commerce), not just JEE/NEET — the engine needs no new capability.

## Why this is the right shape

- **Real** = trust + exam realism (Section A); **Generated** = volume + personalization (Section B).
- It IS the vision's step 2→3 made concrete: real questions → the data + the generated practice loop
  → (later) adaptive/agentic selection of what to practice next. See `VISION.md`.
- Copyright posture is clean: real PYQs are the internal exemplar corpus; the SOLD/served practice is
  GENERATED + validated (the qbank engine's settled strategy). Real PYQs served in Section A are
  public past-exam papers (students already buy PYQ books) — fine for UPSC/boards; keep this in view.

## State (2026-07-29) — Section B pools FILLED for UPSC + CBSE

| | Section A (real simulation) | Section B (authentic daily practice) |
|---|---|---|
| JEE Adv / Main / NEET | ✅ real-format mock papers | ✅ generated pool live |
| UPSC | ✅ real PYQ papers (GS+CSAT) | ✅ **57 pool Qs** (GS 10ch + CSAT 4ch), serves instantly |
| CBSE 10 / 12 PCB / Commerce | ✅ real NCERT MCQ papers | ✅ **CBSE10 63 + CBSE12 294** pool Qs across all subjects |

## The root cause + how the fill was done (2026-07-29)

Per-chapter generation for UPSC/CBSE was returning 0 — NOT a difficulty-band issue. Two data problems:
- **CBSE**: `/chapters` (taxonomy) names didn't match the stored NCERT chapter names (e.g. taxonomy
  "Electrostatics" vs stored "Electric Charges and Fields"). Generation grounds on real exemplars
  filtered by the EXACT chapter string → a mismatch = 0 exemplars = 0 generated.
  **Fix:** generate against the ACTUAL stored chapter names (query `SELECT DISTINCT chapter … WHERE
  verified=1`), not the taxonomy names.
- **UPSC**: the 518 real PYQs were stored **chapter-untagged** (`chapter=NULL`). `/chapters` showed
  taxonomy chapters that don't exist in the data → 0 exemplars per chapter.
  **Fix:** `parallel_tag.py --exam "UPSC Civil Services (Preliminary)"` tagged all 518 into GS/CSAT
  chapters (494 high-conf), THEN generate per real chapter.

**How filled (no worker VM needed):** every `/generate` call PERSISTS its question to the live DB
(`generated=1, verified=1`) → becomes servable via `/pool`. So the fill = loop the real stored
chapters, call `{EXAMGEN}/generate` count=4 per chapter, 4 concurrent, grounded in 3 real exemplars.
Scripts: `scratchpad/fill_cbse.py` + `fill_upsc.py` (chapter lists from DB). No qbank-api restart
(WAL; pool reads DB live). DB backed up `backups/qbank.sqlite.pre_upsctag_*`. Result: **346 CBSE +
56 UPSC** new grounded practice Qs; `/pool` verified serving (UPSC Geography 0→10).

**Deepen later** = re-run the fills with higher count, or fold into the nightly `auto_refill.sh`
cron. Same recipe adds any new exam once its real questions are tagged with real chapter names.
