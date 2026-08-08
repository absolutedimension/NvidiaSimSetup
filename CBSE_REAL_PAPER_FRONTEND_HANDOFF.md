# CBSE Real Board Papers → Acharya Student Frontend — Integration Handoff

**For:** the frontend agent (skill `acharya-student-frontend`, canonical `lms` source).
**Owner of the data below:** the exact-question pipeline (skill `exact-question-making-pipeline-from-pdf`).
**Decision this implements:** serve official CBSE board questions as a **distinct "Real Board Paper (PYQ)" mode**, not blended into the synthetic practice pool.

---

## 1. What the data is (and where it lives)

Real, official **CBSE 2024‑25 + 2023‑24 Sample Question Papers + Marking Schemes** (source: cbseacademic.nic.in) were ingested verbatim into the live bank (`data/qbank.sqlite` on the Gurukul VM). These are **not** the ~77k synthetic NCERT MCQs already in the bank — they are the *actual* board papers, **all question types**.

| Field | Value |
|---|---|
| `exam` | `"CBSE Class 10"` or `"CBSE Class 12"` (same labels the frontend already knows) |
| `subject` | per subject, e.g. `"Business Studies"`, `"Economics"`, `"Accountancy"`, `"Social Science"`, `"Physics"` … |
| `generated` | `0` (real, not RAG-authored) |
| `source` | contains **`(official CBSE)`** — e.g. `"CBSE Class 12 Business Studies 2025 SQP 2024-25 (official CBSE)"` |
| `qtype` | `MCQ_single` (auto-gradable) **and** `descriptive` (short/long answer) |
| `correct_answer` | option letter for MCQ (from the official key) |
| `solution` | for `descriptive`: the **official marking-scheme model answer** |
| `year` | `2025` (2024‑25 SQP) and `2024` (2023‑24 SQP) |

**The distinguishing filter is `source LIKE '%official CBSE%'`.** That is the one predicate that separates real board questions from the synthetic pool.

## 2. Backend (pipeline side) — what's done vs pending

- **Done:** `storage.pool_questions` already serves `generated=0` rows for any `exam` starting `"CBSE Class"`, so these real rows are live-servable today.
- **Pending (pipeline owns this, not you):** an explicit `real_only` filter on `pool_questions` + the `/examgen/pool` API so you can request *official-only*. Until it lands, the real rows are diluted among the synthetic MCQs where those exist (Class 12). Track: adds an optional `real_only=1` query param → appends `source LIKE '%official CBSE%'`. Backward compatible.

## 3. Frontend wiring to add

1. **A "Real Board Paper (PYQ)" toggle/mode** on the Class 10 / Class 12 subject screens. When on, call `/examgen/pool` with `real_only=1` (once the backend param lands) → the student practices only official questions.
2. **A descriptive display mode.** MCQ rows work in the existing objective engine unchanged. `descriptive` rows have no options; render the question, let the student write/reveal, then show `solution` (the official model answer) for self-check (or AI-check via the existing chat layer). The current `QTYPES` set has no `descriptive`, so the objective engine will simply never request them — a dedicated mode is required to surface them.

## 4. Verify after deploy

```bash
# real BST MCQs serve (swap real_only once backend param lands)
curl -sk "https://gurukul.trigunai.com/examgen/pool?exam=CBSE+Class+12&subject=Business+Studies&type=MCQ_single&count=3"
#   ^ expect real stems whose source contains "(official CBSE)"
```

## 5. Known limits (launch-acceptable — tell Deepak, not blockers)

- **Coverage so far:** text-path subjects done (Business Studies, Economics, Accountancy, Social Science — 2 years each). Physics/Chemistry/Maths/Class‑10‑Science are on the VLM (GPU) path — in progress.
- **Descriptive model-answer completeness varies** by subject/year (MS layouts differ); MCQ keys are complete.
- **Figure-dependent questions are held** by the serving gate until a real figure is attached (PCM has many). They will not appear until figures are recovered.
- **English** under-extracts (long unseen reading passages) — deferred.

## 6. One-line summary

Real official CBSE board questions (all types, keyed + model-answered) are live under `exam="CBSE Class 10/12"`, filterable by `source LIKE '%official CBSE%'`; add a "Real Board Paper" mode (request `real_only=1`) and a descriptive-answer display, and students can practice the actual papers.
