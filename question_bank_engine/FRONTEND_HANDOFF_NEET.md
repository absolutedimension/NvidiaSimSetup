# examgen API — Frontend Handoff (NEET: Biology + Physics + Chemistry)

**Status (2026-07-23):** NEET is live on the same API as IIT JEE. All three NEET subjects
are ingested, tagged against a chapter taxonomy, and verified.

> Companion to `FRONTEND_HANDOFF_IIT.md` (JEE Advanced + JEE Main). **Same base URL,
> same auth, same request/response contract** — only the `exam`/`subject` strings change.
> Read that document for the full `/generate` schema; this one covers what is NEET-specific.

---

## 1. What's available

| `exam` | `subject` | Chapters | Exemplar Qs | Worked solutions | Source |
|---|---|---|---|---|---|
| `NEET` | `Biology` | 36 | 832 | 821 (100% of non-diagram) | NCERT-style text bank + real NEET 2024/25/26 papers |
| `NEET` | `Physics` | 25 | 129 | 87 (100% of non-diagram) | real NEET 2024/25/26 papers |
| `NEET` | `Chemistry` | 25 | 104 | 83 (100% of non-diagram) | real NEET 2024/25/26 papers |

**Exact strings matter** — `"NEET"` and `"Biology"` / `"Physics"` / `"Chemistry"` verbatim.
Note NEET uses **`Biology`**, not the paper's `Botany`/`Zoology` split — those are folded
into one subject, because that is how students pick a topic.

Difficulty band: NEET content sits at **2–3** (JEE Advanced is 3–4). Ask for `"2-3"`.

---

## 2. The one NEET-specific behaviour: borrowed exemplars

NEET Physics and Chemistry have only ~130 and ~104 real questions spread over ~25
chapters, which is too thin to retrieve 3 same-chapter exemplars for every topic. NEET
Phy/Chem sit on the **same syllabus as JEE Main**, so when a chapter has nothing of its
own, the generator borrows JEE Main exemplars for that chapter and still authors at the
NEET difficulty you asked for.

This shows up in `GET /chapters`:

```
GET /chapters?exam=NEET&subject=Physics
```
```json
{
  "exam": "NEET", "subject": "Physics",
  "exemplar_fallback_exam": "JEE Main",
  "chapters": [
    {"chapter": "Current Electricity", "concepts": [...],
     "exemplars_banked": 174,      // what the generator can actually draw on
     "exemplars_own": 12}          // real NEET questions specifically
  ]
}
```

- **Keep filtering on `exemplars_banked > 0`** — unchanged behaviour, nothing to migrate.
- `exemplars_own` is informational (e.g. to badge "from real NEET papers").
- `exemplar_fallback_exam` is `null` for Biology and for all JEE banks.

---

## 3. Everything else is identical to the IIT handoff

- `GET /health` — same
- `POST /generate` — same body, just `"exam": "NEET"`, `"subject": "Biology"`, `"difficulty": "2-3"`
- Same response shape (`questions[]`, `answer_key`, `solution`, `figure_svg` / `figure_url`)
- Same auth (Bearer key, server-side only), same LaTeX rendering requirement

Example:
```json
{"exam":"NEET","subject":"Biology","chapter":"Molecular Basis of Inheritance",
 "difficulty":"2-3","type":"MCQ_single","count":5,"exemplars":3}
```

---

## 4. Wiring NEET into the student LMS

Same two-file change as the IIT handoff §6:

1. `lms/app/examgen.py` → add to `RAG_SUBJECTS`:
   ```python
   "neet-biology":   {"label": "NEET Biology",   "exam": "NEET", "subject": "Biology",   "match": [...]},
   "neet-physics":   {"label": "NEET Physics",   "exam": "NEET", "subject": "Physics",   "match": [...]},
   "neet-chemistry": {"label": "NEET Chemistry", "exam": "NEET", "subject": "Chemistry", "match": [...]},
   ```
2. `lms/app/main.py` → add matching `EXAMS` entries so they appear at `/exam-prep`.
3. Deploy `lms:vN` (see the `maintain-trigunai-system` skill).

No API change needed.

---

## 5. Quality notes (honest)

- **Biology text bank** (~600 of the 832) is NCERT-style recall Q&A, not verbatim past
  papers. Keys were spot-audited by hand: **25/25 correct**. Good for practice and as RAG
  exemplars; it is not a substitute for a real past paper.
- **Image-sourced questions** (NEET 2024/25/26, ~465) are real past-paper questions with
  official keys. A hand audit of 12 found **11/12 keys correct**; the one failure was a
  mis-transcribed *option text* from the vision model, not a wrong key.
  → Treat the occasional garbled option as a known limitation of the image path. The
  solution pass flags questions where an independent solve disagrees with the official
  key (`solution_needs_review`), which surfaces most of these.
- **74 diagram questions** (42 Physics, 21 Chemistry, 11 Biology) carry `needs_figure`
  and are excluded from automatic solving — they need the figure to answer. They are
  still valid exemplars and still served.
- **90 questions carry `solution_needs_review`** (55 Bio / 15 Phy / 20 Chem): an
  independent solve disagreed with the official key. The stored solution argues toward
  the **official** answer (students never see the contradicting one), and the row is
  flagged for human adjudication. No frontend impact.
- Figures are served from `https://gurukul.trigunai.com/examgen/figures/<id>.png`
  (previously pointed at the EC2 GPU box, which 404'd whenever that box was off).

**Questions / key access:** Deepak (deepak@trigunai.com).
