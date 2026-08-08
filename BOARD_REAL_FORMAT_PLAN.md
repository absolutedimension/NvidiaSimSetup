# Real CBSE board-format mock papers — scope

> **Today (2026-07-29):** CBSE Class 10 / 12 PCB / Commerce have **MCQ Practice** papers only (3 each,
> real NCERT MCQs, honestly labeled, lms:v129). The bank holds ONLY `MCQ_single` for boards — no
> subjective questions. JEE/NEET/Banking/UPSC already have genuine real-format papers (those exams
> are objective). This doc scopes what real *board* format (Sections A–E, written answers) needs.

## Why it's not a config change — two real gaps

**1. DATA — the bank has no subjective board questions.**
A real CBSE paper is Section A (MCQ/assertion-reason, 1 mark), B (short, 2 marks), C (short, 3 marks),
D (long, 5 marks), E (case-study). We have none of B/C/D/E.
- **Source:** official CBSE **sample papers + past board papers** (PDFs, published per subject per year).
- **Tool:** the proven `exact-question-making-pipeline-from-pdf` skill (Qwen2.5-VL extract → verbatim
  question + official marking-scheme model answer → store `generated=0, verified=1`). Same pipeline
  that gave UPSC its 517 real PYQs.
- **Store per question:** `qtype` ∈ {mcq, assertion_reason, case_study, short_2, short_3, long_5},
  the **marking-scheme model answer**, and mark value. Per subject: Class 10 Science; Class 12
  Physics / Chemistry / Biology / Accountancy / Economics. Start ~2–3 recent CBSE sample papers each.

**2. ENGINE — the mock engine can't hold or grade written answers.**
- `mockpaper.BLUEPRINTS` gains a real board section structure (A/B/C/D/E with per-section marks).
- Paper-sit UI (`exam_prep_paper.html`) needs a **text-answer input** for subjective questions
  (today: MCQ/integer/numeric only).
- **Grading:** `score_attempt` can't score prose. Add an **LLM-graded path** — send {student answer,
  marking-scheme model answer, max marks} to the LLM, get 0..max + feedback. The Acharya tutor
  already does answer-evaluation, so the capability exists to adapt. Async (one LLM call per
  subjective answer).
- Result page shows per-question marks + the model answer + where marks were lost.

## Effort
- Data ingest (PDF → verified subjective bank): ~1–2 days per subject bundle (pipeline is proven; the
  work is sourcing official PDFs + extraction + verification).
- Engine (board blueprint + subjective input + LLM grading + result display): ~2–3 days.

## Sequencing recommendation (CEO lens)
Gate is **0 paid**; boards are one of 8 exams. **Do NOT build this speculatively.** Build it when
there's a board-student demand signal (a board student asking, or board traffic converting on
`/exam-prep`). Until then: honest **MCQ Practice** for boards + "written sections coming" is the
right holding state, and the push stays on JEE/NEET/Banking/UPSC, which already have genuinely
real-format papers. See [[reference-trigunai-systems-map]] (product depth is low-leverage until R1
closes) and [[project-acharya-positioning]] (exam-authentic is the brand — don't dilute it).

*Owner: Deepak. Trigger to execute: real board-student demand.*
