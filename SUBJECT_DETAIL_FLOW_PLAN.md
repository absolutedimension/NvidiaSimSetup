# Subject-Detail Flow — integrating the JEE Physics RAG generator

> **Goal:** when a student opens a subject (JEE Physics first), let them drill **subject → chapter
> (topic) → concept (subtopic)** and take a test of **real RAG-generated questions** from the live
> `/examgen` API. Repo: `lms/`. Date: 2026-07-23.

## The live generator (verified)
- `https://rtx.trigunai.com/examgen` · healthy · 127 exemplars · gpt-4o via LiteLLM.
- `GET /chapters` (no auth) → `{exam, subject, chapters:[{chapter, concepts:[...], exemplars_banked}]}`.
- `POST /generate` (Bearer key) → `{questions:[{stem, options:[{label,text}], correct_answer, solution, qtype, chapter, concept, difficulty}], answer_key}`. **LaTeX** stems/options/solutions; ~6–12s/question.
- Hierarchy: **JEE Physics → Chapter → Concept.** Physics only for now (18 chapters).

## Target flow
```
Dashboard → "JEE Physics" topic → tap
   ▼
Subject page  /exam-prep/subject/jee-physics
   • chapters (only exemplars_banked>0): name · concept count · "N past-paper styles"
   • tap a chapter → expands to CONCEPTS (subtopic chips): Projectile Motion, …
       • pick whole-chapter OR a concept · difficulty (Medium/Hard) · 5 questions
       • ▶ Generate & take test
   ▼
Test  → assess.html engine + MathJax, fed a pack from the LMS proxy
   • "Generating fresh JEE questions for <concept>…" skeleton (~30–60s)
   • LaTeX MCQs · solutions on review · finish → per-concept weak/solid → saved → back to subject
```

## Architecture — LMS is the secure proxy (key never in the browser)
```
Browser → LMS  /api/examgen/chapters           → proxies /examgen/chapters (cache ~1h)
Browser → LMS  /exam-prep/subject/jee-physics   → renders the chapter/concept explorer
Browser → LMS  /api/examgen/generate {chapter,concept,difficulty,count}
                 └ LMS adds Bearer key (EXAMGEN_KEY env) → /examgen/generate
                 └ transforms /examgen output → assess.html "pack" shape → returns
assess.html boots from the pack (MathJax renders the LaTeX)
```
- New LMS env (container secrets): `EXAMGEN_URL=https://rtx.trigunai.com/examgen`, `EXAMGEN_KEY=<QBANK_API_KEY>`.
- Same-origin (browser→LMS), so no CORS concerns; the /examgen key stays server-side.
- **Routing:** JEE-Physics topics → `/examgen` (RAG, chapters/concepts, MathJax). Every other subject → the existing in-LMS `assess_gen` (unchanged), until RAG data is added for it.

## Transform (examgen → assess.html pack)
- `stem` → `en.q` (and `hi.q = en.q`; examgen is English-only, JEE students read English) · `options[].text` → `en.opts` (strip labels) · `correct_answer` letter → option index · `solution` → `en.explain` · `qtype MCQ_single` → mcq.
- assess.html gains **MathJax** (typeset after each render) to show LaTeX. The generated set is fixed (not per-question adaptive) — feed it as a flat pack; per-concept weak/solid still works.

## REFINED SPEC (Deepak, 2026-07-23)
- **"Take test" → subtopic picker**, not a straight test. Student **multi-selects** one or more
  subtopics (concepts) OR "full subject" → **builds a custom paper** of RAG questions.
- **On-request RAG:** if the subject isn't in the RAG yet (everything except IIT Physics today),
  the detail page shows **"your test is being set up — request submitted, coming soon"** + logs a
  course request. (+ a small "take a quick AI test meanwhile" fallback so the student isn't dead-ended.)
- **Authentic paper style:** RAG imitates real IIT-JEE Physics templates → same style, new questions.
- **Scores saved + suggested-next** across many tests per subject *(Phase B — needs a small progress
  table; the existing LearningEvent loop is consent-gated OFF, so store product progress separately)*.
- Available chapters today (exemplars>0): all except **Magnetism, Wave Optics, Semiconductors** (0 → hidden/"soon").

## Build order
- **Phase A (now):** examgen proxy + subject-detail page (multi-select subtopics · full-subject ·
  difficulty · count) + RAG test via assess.html+MathJax + coming-soon/request for unavailable +
  route dashboard "Take test" → subject page.
- **Phase B (next):** `TopicAttempt` progress table (scores saved, not consent-gated) + "Acharya
  suggests next" (weakest concept) on the subject page + per-concept mastery trend.

## Open design decisions (lock before building)
1. **Test UI:** reuse `assess.html` + MathJax + a pack adapter (keeps progress/review/weak-area/save machinery) — vs. a new dedicated LaTeX test page.
2. **Dashboard topic granularity:** a JEE-Physics dashboard topic = the **subject** (opens the chapter/concept explorer), so the 5-cap is on subjects — vs. each chapter/concept being its own dashboard topic.
3. **v1 scope:** JEE Physics only via examgen; other subjects keep the existing generator (hybrid routing).

## Handoff reference
`question_bank_engine/FRONTEND_HANDOFF.md` (full API schema), `README.md`, `api.py` (the service).
