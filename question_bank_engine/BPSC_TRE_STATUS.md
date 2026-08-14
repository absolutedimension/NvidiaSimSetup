# BPSC TRE (Teacher Recruitment) — status & ready-to-flip wiring

> Session 2026-08-14. The "TRE" line on the One Step Education note was the one **open**
> govt source still untapped. This documents exactly what was done, the hard blocker, and
> the one-commit path to go live the moment that blocker clears.
> Master ref: `SRB_PYQ_SOURCING_GUIDE.md`. Ingest lane owner: `HANDOFF_SRB_OTHER_SESSION.md`.

## TL;DR
- ✅ **Papers: DONE.** All **152 TRE booklets** (TRE 1.0 / 2.0 / 3.0, subject-wise) downloaded
  from the OPEN official source `bpsc.bihar.gov.in` → **`drop/bpsc_tre/`** (84 MB, all valid PDFs,
  `TRE_MANIFEST.csv` lists every file + source URL).
- ✅ **Extraction: DONE (text-layer, no GPU).** TRE booklets are **digitally-generated text-layer
  PDFs** (NOT scanned like the BPSC Prelims papers → **no Qwen/T4 needed**). New tool
  **`extract_tre.py`** (column-aware, 5-option A–E, bilingual EN/HI → serves EN). Curated run
  **`build_tre_staged.py`** → **1,281 verbatim questions** staged in
  **`drop/bpsc_tre/extracted/tre_staged_questions.json`**.
- ⛔ **BLOCKER: official answer keys are unreachable.** TRE final answer keys are published ONLY on
  **`bpsc.bih.nic.in`**, which is **firewalled from every egress path** (local Mac timeout, Gurukul
  geo-blocked, WebFetch ECONNREFUSED 164.100.251.54). This is the SAME wall as the 69th-Prelims
  Set-A key. Per the cardinal rule (**official key = trust anchor; never serve unverified Qs**), the
  1,281 staged questions have `answer: null`, `verified: 0`, `held_reason:"awaiting_official_answer_key"`
  and are **NOT stored in the live bank and NOT served**.
- ⏸️ **LMS + APK: NOT wired live** (deliberately). Wiring an exam with 0 servable Qs = a broken
  "BPSC TRE · available (empty)" tile. The exact one-commit patch is below — **apply it only after
  ≥1 TRE paper's official key is matched + stored + `/pool` serves it** (mirrors how BPSC Prelims
  was wired only after the 289 keyed Qs went live).

## What TRE is (structure, verified 2026-08-14)
`bpsc.bihar.gov.in/question-booklets/` → node **[6] Teacher Recruitment Examinations**:
- **TRE 1.0** (Advt 26/2023) — Class 09-10 & 11-12 subject booklets ("General Studies And <Subject>"),
  plus a **pure "General Studies, Paper-2"** (1st+2nd sitting) and "Language, Paper-1". 43 PDFs.
- **TRE 2.0** (Advt 27/2023) — Class 01-05 / 06-08 / 09-10 / 11-12, dated papers. 56 PDFs.
- **TRE 3.0** (Advt 22/2024, most recent) — Class 01-05 / 06-08 / 06-10 / 09-10 / 11-12. 53 PDFs.
- Every booklet carries a **Part-I General Studies** block (common Bihar GS/GK) + a subject part.
  Format = **5 options (A–E)**; D is usually "More than one of the above", E "None of the above".
  Bilingual (English then Hindi legacy font). ~120–150 Q/paper.
- **The Bihar GS/GK content is exactly the gap One Step wants** (e.g. "first floating solar power
  plant in Bihar", "Revolt of 1857 as First War of Independence").

## How the papers were fetched (reproducible)
The WP `question-booklets` plugin uses an AJAX cascade with a **rotating nonce** (expires ~24h):
1. GET `bpsc.bihar.gov.in/question-booklets/` → read `question_booklets_params = {... "nonce": "<10hex>"}`.
2. `POST admin-ajax.php action=get_children&parent_id=N&nonce=<nonce>` to walk the tree.
3. `POST admin-ajax.php action=get_question_booklets_pdfs&item_id=N&nonce=<nonce>` → PDF in **`file_url`**.
Crawler that self-fetches the nonce + walks the whole tree: scratch `tre_crawl.py` (writes `qb_all_files.json`).
**The local Mac reaches `bpsc.bihar.gov.in` directly** (unlike the T4) — download ran on the Mac, no
Gurukul disk pressure. Downloader: scratch `dl_tre.py` → `drop/bpsc_tre/` + `TRE_MANIFEST.csv`.

## Extraction tool — `extract_tre.py`
Column-aware, text-layer extractor (no GPU). Usage:
```bash
python3 extract_tre.py "drop/bpsc_tre/TRE1.0/*.pdf" --out /tmp/out.json     # batch
python3 build_tre_staged.py                                                  # curated 12-paper staged set
```
- 2-column, column-major reconstruction via word bboxes (split at page-width/2).
- Anchors on the (A)…(E) option cluster; keeps the **English** cluster (Hindi cluster skipped).
- **Yield:** clean prose (GS/GK/Science/Social/Polity/English) extracts at ~full 120/paper. **Math/
  quant** questions contain fractions/superscripts that reflow imperfectly in ANY text layer — those
  stems/options may need manual cleanup or Qwen vision OCR for perfect fidelity. Language/comprehension
  papers under-yield (passage format). This is fine for a staged artifact; do a clean re-extract of the
  exact keyed paper at key-matching time.

## ▶ When a key route opens — the go-live path (per paper)
> **KEY-ROUTE REALITY (corrected 2026-08-14 by the Prelims lane):** `bpsc.bih.nic.in` is **HOST-LEVEL
> DOWN / parked** — it TIMES OUT even from an Indian-egress Mac (which reaches `bpsc.bihar.gov.in` fine).
> So "find an Indian-egress box" is a **dead end**; the host is unreachable for everyone, not IP-filtering.
> `bpsc.bihar.gov.in` IS reachable but exposes **papers only** — its notification/AJAX feeds don't yield
> clean key PDFs (empty `fields`; key links render client-side). **The proven route for BOTH lanes =
> per-edition mirror re-hosts of BPSC's OWN official NB answer-key PDF** (ForumIAS did this for the 70th
> final `forumias.com/blog/wp-content/uploads/2025/01/NB-2025-01-17-02.pdf` and 71st Set-E provisional),
> **or a student who appeared (response sheet).** NOT coaching sites' own re-keyed answers (those are
> internal cross-check only, never served).

**Two binding constraints for TRE go-live (both owned by the Prelims/ingest lane):**
- **(a) Official key.** TRE 3.0 final keys DO exist as **no-login, subject-wise NB-format PDFs** (confirmed
  2026-08-14; "released as a PDF with the correct response") — so the ForumIAS-mirror route is viable for TRE
  exactly like Prelims. Just source the genuine official NB PDF (NOT a coaching site's own re-key) for a
  paper whose booklet+series we hold.
- **(b) 5-option (A–E) serving support — ✅ BUILT + VERIFIED 2026-08-14.** Turned out to be 3 tiny
  backward-compatible edits (the serving path was already A–E capable — `_letter_to_index` maps `E:4`,
  `_to_pack_question` passes all options, DB stores options as a JSONB array):
    1. `store_real_questions.py` — label loop `"ABCD"`→`"ABCDE"`.
    2. `qbank/validator.py` — answer regex `[A-D]`→`[A-E]`.
    3. `lms/app/static/exam/assess.html` — badge array `['A','B','C','D']`→`+'E'` (the `mcq()` renderer
       already iterates `v.opts` dynamically; `exam_prep_quick.html` was already A–E).
  Loader `store_tre_keyed.py` built; **proven end-to-end on a local test DB**: all 343 keyed TRE Qs stored
  `verified=1`, served via `iter_real`, E-answer → index 4 → badge E → "None of the above", D-answer →
  index 3, every correct index in range, backward-compatible with existing ≤4-option questions. This
  ALSO unblocks the Prelims 66/67/68 5-option papers.

1. Get the **official BPSC TRE final answer key** for a specific paper+**booklet series** (A/B/C/D/E —
   question order differs per series, so the key must match the booklet's series). Source = an **official
   BPSC NB-format key PDF re-hosted on a reachable mirror** (ForumIAS standard above) or a student response
   sheet. (`bpsc.bih.nic.in` direct is dead — see reality note.)
2. Re-extract that exact paper cleanly with `extract_tre.py` (verify option-count + math fidelity).
3. Match key → store: `python3 store_real_questions.py --exam "BPSC TRE" --id-prefix bpsctre ...`
   **NOTE: 5-option (A–E)** — needs the A–E path (parallel session's `qwen_extract_bpsc5.py` +
   store/validator/frontend A–E support). TRE is 5-option like BPSC 66/67/68.
4. `enable_pool_serving.py --prefix BPSCTRE` + add `BPSC TRE` to `skip_chapter`/`skip_difficulty` in
   **`storage.py` on Gurukul only** (do NOT overwrite the Gurukul storage.py from repo — it carries the
   parallel session's serving-gate patch).
5. Apply the LMS + APK wiring below, deploy, verify `/pool` serves real keyed Qs.

## Ready-to-flip wiring (DO NOT APPLY until step 4 above is done)

**`lms/app/examgen.py`** — add to `RAG_SUBJECTS`:
```python
    "bpsc-tre": {
        "label": "BPSC TRE GS (Teacher)", "exam": "BPSC TRE", "subject": "General Studies", "kw": "gs",
        "match": ["bpsc tre", "tre", "teacher recruitment", "bpsc teacher", "bpsc-tre",
                  "bihar teacher", "tre gs", "bpsc tre gs"],
    },
```
add to `GOALS`:
```python
    "bpsc-tre": {
        "label": "BPSC TRE (Teacher)", "tag": "Bihar · Teacher Recruitment", "emoji": "🧑‍🏫",
        "subjects": ["bpsc-tre"],
    },
```
add to `DIFFICULTY_LADDER` (real PYQs served from /pool, band nominal like BPSC/UPSC):
```python
    "BPSC TRE": {"easy": "3", "mix": "3", "hard": "3"},
```

**`lms/app/main.py`** — add to `EXAMS`:
```python
    {"id": "bpsc-tre", "subject": "bpsc-tre", "title": "BPSC TRE", "tag": "Bihar Teacher · real PYQs", "emoji": "🧑‍🏫"},
```
add to `STUDENT_EXAMS`:
```python
    {"id": "bpsc-tre", "title": "BPSC TRE", "tag": "Bihar Teacher · real PYQs", "emoji": "🧑‍🏫", "available": True},
```
(and add `"bpsc-tre"` to the goal list near main.py:2214 if that gates onboarding.)

**APK `AcharyaApp/lib/config/exams.dart`** — add:
```dart
  Exam('bpsc-tre', 'BPSC TRE', 'Bihar Teacher · real PYQs', '🧑‍🏫'),
```
and mirror the subject in `AcharyaApp/lib/config/subjects.dart` like the other `bpsc`/`ssc` entries, then
`flutter build apk --release`.

## Files added this session
- `extract_tre.py` — column-aware TRE text-layer extractor.
- `build_tre_staged.py` — curated 12-paper staged run.
- `drop/bpsc_tre/` — 152 PDFs + `TRE_MANIFEST.csv`.
- `drop/bpsc_tre/extracted/tre_staged_questions.json` — 1,281 verbatim staged questions (answer=null, held).
