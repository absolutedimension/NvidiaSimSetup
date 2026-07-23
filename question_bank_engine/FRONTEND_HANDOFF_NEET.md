# examgen API — Frontend Handoff (NEET: Biology + Physics + Chemistry)

**Status (2026-07-23):** NEET is live on the same API as IIT JEE — **~33k verified
questions** across Biology / Physics / Chemistry, tagged, ~99–100% with worked solutions.
The LMS wiring is already in code (see §4); verify + deploy is the only step left.

> Companion to `FRONTEND_HANDOFF_IIT.md` (JEE Advanced + JEE Main). **Same base URL,
> same auth, same request/response contract** — only the `exam`/`subject` strings change.
> Read that document for the full `/generate` schema; this one covers what is NEET-specific.

---

## 1. What's available

| `exam` | `subject` | Chapters | Exemplar Qs | Worked solutions | Source |
|---|---|---|---|---|---|
| `NEET` | `Biology` | 38 | **13,961** | 100% of non-diagram | datavorous entrance-exam bank + NCERT text + real NEET 2024–26 papers |
| `NEET` | `Physics` | 32 | **5,343** | 100% of non-diagram | datavorous entrance-exam bank + real NEET 2024–26 papers |
| `NEET` | `Chemistry` | 35 | **13,507** | ~99% of non-diagram | datavorous entrance-exam bank + real NEET 2024–26 papers |

> Scaled up 2026-07-23 from ~1k to ~33k via `datavorous/entrance-exam-dataset` (pre-tagged, pre-keyed, pre-solved). Every chapter now has exemplars.

**Exact strings matter** — `"NEET"` and `"Biology"` / `"Physics"` / `"Chemistry"` verbatim.
Note NEET uses **`Biology`**, not the paper's `Botany`/`Zoology` split — those are folded
into one subject, because that is how students pick a topic.

Difficulty band: NEET content sits at **2–3** (JEE Advanced is 3–4). Ask for `"2-3"`.

---

## 2. Chapters

NEET now has its own deep bank per subject with NEET-specific chapter names (derived from
the datavorous source), so **there is no exemplar borrowing anymore** — every chapter
generates from real NEET questions.

```
GET /chapters?exam=NEET&subject=Physics
```
```json
{
  "exam": "NEET", "subject": "Physics",
  "exemplar_fallback_exam": null,
  "chapters": [
    {"chapter": "Laws of Motion", "concepts": [],
     "exemplars_banked": 295, "exemplars_own": 295}
  ]
}
```

- Filter on `exemplars_banked > 0` (all NEET chapters now satisfy this).
- `exemplars_own` == `exemplars_banked` for NEET (no borrowing).
- NEET chapter names are NEET's own (e.g. "Laws of Motion", "p Block Elements (Group 15,
  16, 17 & 18)") — do **not** assume they equal the JEE chapter names.

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

## 4. LMS integration — mostly wired already

The student LMS (`lms/`, served at `acharya.trigunai.com/exam-prep`) proxies `/examgen`
server-side so the API key never reaches the browser. **The NEET wiring is already in the
LMS code** — you do NOT need to re-add it. Verify + deploy is the only step left.

Already present (confirm, don't re-create):

- `lms/app/examgen.py` → `RAG_SUBJECTS` has `neet-biology`, `neet-physics`,
  `neet-chemistry` (with `exam:"NEET"`, the right `subject`, and title `match` phrases).
- `lms/app/examgen.py` → `GOALS["neet"]` maps the NEET goal to those three subjects
  (order: Biology, Physics, Chemistry — Biology is the default).
- `lms/app/main.py` → `EXAMS` has `{"id":"neet","subject":"neet-biology","title":"NEET",…}`
  as the first entry, so NEET shows on `/exam-prep`.
- `EXAMGEN_URL` defaults to `https://gurukul.trigunai.com/examgen` (the always-on VM) and
  `EXAMGEN_KEY` is the container secret — both already set.

**Status at handoff:** `acharya.trigunai.com/exam-prep` already renders NEET. But
`lms/app/examgen.py` is untracked in git and `lms/app/main.py` has uncommitted local
edits — so **before relying on it, confirm the running container actually has this code**
and commit it. Deploy path is owned by the `maintain-trigunai-system` skill (`lms:vN`).

**Verify checklist (5 min):**
```bash
# 1. backend banks are live
curl -s "https://gurukul.trigunai.com/examgen/health"          # bank_verified ~44k
curl -sG "https://gurukul.trigunai.com/examgen/chapters" \
     --data-urlencode "exam=NEET" --data-urlencode "subject=Biology" | head
# 2. student path end-to-end: log in at acharya.trigunai.com/exam-prep, pick NEET,
#    start a Biology practice test, confirm questions render (LaTeX + options + solution).
```

If you build a **custom** NEET UI instead of the LMS flow, call `/examgen` directly per
§1–§3 (server-side, Bearer key). No backend change is needed for either path.

---

## 5. Quality notes (honest)

- **Bulk source is `datavorous/entrance-exam-dataset`** (~33k of the NEET rows): real
  past-paper-style Qs, pre-keyed and pre-solved. The correct answer is cross-checked two
  independent ways at ingest and disagreements are dropped — **0 disagreements across
  49,771 rows**. Hand-audited key samples were correct.
- **Real NEET 2024–26 papers** (~465, image-sourced via vision) carry official keys; a
  hand audit found 11/12 keys correct — the miss was a mis-transcribed *option text*, not
  a wrong key. Treat occasional garbled option text as a known image-path limit.
- **~74 diagram questions** carry `needs_figure` and are excluded from auto-solving (they
  need the figure to answer). Still valid exemplars, still served.
- **~90 questions carry `solution_needs_review`** — an independent solve disagreed with
  the official key. The stored solution argues toward the **official** answer (students
  never see the contradicting one) and the row is flagged for human adjudication. **No
  frontend impact.**
- **LaTeX everywhere** — `stem`, `options[].text`, `solution` contain `$...$` / `\mathrm{}`.
  Render with KaTeX/MathJax (same as JEE). Figures: inline `figure_svg` if present, else
  `<img src=figure_url>` (served from `https://gurukul.trigunai.com/examgen/figures/…`).
- **NEET difficulty is 2–3**, not 3–4. Ask for `"difficulty":"2-3"`.

**Questions / key access:** Deepak (deepak@trigunai.com).
