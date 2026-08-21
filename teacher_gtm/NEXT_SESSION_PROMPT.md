# Prompt for the next Claude session

Copy everything inside the box.

---

```
Continue the BSSC / One Step test-paper work. Load the `bssc-test-prep` skill first — read the
section "📨 2026-08-21 — THE BALL IS WITH THE OWNER" before doing anything else.

Where things stand:

A 14-question survey is LIVE and was sent to One Step's owner on 21 Aug:
https://acharya.trigunai.com/paper-survey?inst=One%20Step%20Education
His answers are the specification for the next paper — difficulty mix, per-topic cap, what
"hard" means in each section, and question ordering.

START BY CHECKING WHETHER HE HAS REPLIED:
  - acharya.trigunai.com/admin  →  the "📝 Paper survey" section, or
  - query the `paper_surveys` table (Postgres; container secret `dburl` on app `lms`,
    resource group trigunai-video-creator)

IF HE HAS ANSWERED — that is the priority. Map his answers onto the generator:
  q6/q7 → --difficulty-mix (15:15:70 today, never validated)
  q10   → the per-concept cap in build_onestep_paper.py (currently 4)
  q2/q3/q4 → what each difficulty band should vary, per section
  q8    → question ORDER (the builder does no ordering at all today — this may be a build)
  q5    → his p-value target; the first number that puts his judgement and our tag in one unit
Then rebuild both sets and send them.

IF HE HAS NOT ANSWERED — do NOT chase him with a reminder. He answers papers more readily
than questions. Fix these two REAL defects I found by rendering the page and reading it, then
send one improved paper:
  1. Part II prints FOUR CONSECUTIVE IDENTICAL maths templates ((x)² + a/b − 15% of c).
     The topic quota is filled from one builder with no per-template cap and no shuffle.
     Part III has that cap; Part II does not.
  2. The Hindi for those reads "… - 140 का 15% का मान क्या है?", which is ambiguous about
     what the 15% applies to.

Also open, in value order:
  - Biology facts are BUILT but GATED. 27 rows in question_bank_engine/drop/bssc/
    SCIENCE_REVIEW.md need a human tick, then set BIO_REVIEWED=True in qbank/science_tables.py
    AND add ["Biology"] to that topic's `concepts` in drop/bssc/SYLLABUS_MAP.json at the same
    moment. Same pattern for history_tables.REVIEWED (39 rows, HISTORY_REVIEW.md).
  - GS still covers only 4 of 14 syllabus topics. That is the biggest remaining content gap.
  - Figure / non-verbal reasoning is the last question family the real papers use and we
    cannot generate. Needs SVG.

House rules that were learned the hard way this session — please keep them:
  - Every new builder needs an INDEPENDENT solver in teacher_gtm/test_papers.py that uses a
    DIFFERENT algorithm, and it must be SABOTAGE-TESTED (flip a key, confirm it fails) before
    it is trusted. A check that cannot fail is not a check.
  - Both papers must rebuild with "ALL CHECKS PASSED" and 150 of 150 re-solved. If coverage
    is below 150, find the unread questions — do not accept a green run with a short count.
  - RENDER THE PAGE AND LOOK AT IT. Three shipped defects this session were invisible to every
    structural check and obvious on the page.
  - For anything with a form or button, CLICK IT in a real browser. curl bypasses forms.

Rebuild command:
  cd teacher_gtm
  echo '{}' > InterLevel_sets_used.json
  python3 build_onestep_paper.py --set 1 --sets 2 --inter-level --all-generated \
      --difficulty-mix 15:15:70 --show-difficulty --logo onestep_logo.png \
      --out OneStep_BSSC_InterLevel_Set1_REVIEW.pdf
  (repeat with --set 2, then)
  python3 test_papers.py OneStep_BSSC_InterLevel_Set1_REVIEW.html \
      OneStep_BSSC_InterLevel_Set2_REVIEW.html
```

---

## What was committed (branch `srb-bpsc-tre`)

| commit | contents |
|---|---|
| `ae74aba` | Part III + Part II rebuilt — syllabus-driven draw, 8 new builders, verified fact tables |
| `106d36e` | `lms:v160` — the survey at `/paper-survey`, captured in three places |
| `bef793b` | Both rebuilt sets, the delivered-copy archive, the printable questionnaires |

38 files remain dirty; all of them were already uncommitted **before** this session and were
left untouched.

## State in one table

| | |
|---|---|
| Part III | 19 concepts, max 4 each · pool 8,161 · 150/150 independently re-solved |
| Part I (GS) | 6 question styles · **4 of 14 syllabus topics** — the big gap |
| Part II | every maths quota hit exactly · chemistry LIVE (PubChem-verified) · biology gated |
| Live survey | `acharya.trigunai.com/paper-survey` — `lms:v160`, awaiting his reply |
| Unverified | the WhatsApp alert has never been confirmed *delivered* — check `watoken` if silent |
