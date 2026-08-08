# UPSC → Acharya Student Frontend — Integration Handoff

**For:** the Acharya frontend agent (skill `acharya-student-frontend`, owns the real `lms` source + deploy)
**From:** the assessment-backend agent (skill `trigunai-assessment-backend-data`)
**Date:** 2026-07-27
**Goal:** add UPSC Civil Services (Prelims) as a selectable exam so students practise **REAL past-paper PYQs**.

> ⚠️ **DO NOT deploy from the Gurukul `~/acharya_frontend` repo** — it is STALE (v111-era) and is NOT the source of the live UI (v117). Apply the wiring below to **your canonical `lms` source** (the one v117 was built from) and deploy on top of v117. A previous deploy from the stale repo reverted 6 versions of UI; that mistake is why this is a handoff, not a direct edit.

---

## 1. Where the UPSC data is (and how it got there)

**The data is 100% done and LIVE on the backend.** Nothing to ingest. You only wire the frontend.

| | |
|---|---|
| **Store of record** | Gurukul VM `dk_trigun@20.219.2.53` → `~/question_bank_engine/data/qbank.sqlite`, table `questions` |
| **Serving API** | `qbank-api` systemd unit (uvicorn `127.0.0.1:8020`) → public `https://gurukul.trigunai.com/examgen` (via Caddy) — this is exactly what your frontend's `EXAMGEN_URL` already points at |
| **How sourced** | Official upsc.gov.in prelims PDFs (2023–2025) → extracted with **Qwen2.5-VL-7B** vision model on EC2 → answer keys hand-transcribed from official keys → stored + verified |
| **Count** | **517 verified** questions: **324 General Studies + 193 CSAT** |
| **Shape** | all `qtype=MCQ_single`, `difficulty=3`, `verified=1`, `generated=0`, `chapter` = NULL |
| **Figures** | **0 figure-dependent** — UPSC is text/statement/table based (tables captured inline as markdown). No image assets to serve. |

**Exact DB identifiers your API calls must use:**
- `exam = "UPSC Civil Services (Preliminary)"`
- `subject = "General Studies"` (324 Qs) OR `subject = "CSAT"` (193 Qs)

Quick proof it's live (run anywhere):
```bash
curl -s "https://gurukul.trigunai.com/examgen/pool?exam=UPSC+Civil+Services+%28Preliminary%29&subject=General+Studies&difficulty=3&type=MCQ_single&count=3"
```
Returns 3 real UPSC GS questions with clean stems, 4 options, `correct_answer`.

---

## 2. Backend work already done (DO NOT redo — just rely on it)

All committed on Gurukul `~/question_bank_engine` (commit `f9946cb`) and **live** (qbank-api restarted). Two changes in `qbank/storage.py` make UPSC serve correctly:

1. **`generated=1` gate bypassed for UPSC** in `pool_questions` + `pool_stats` (mirrors the existing CBSE bypass). Without it the real bank (`generated=0`) would never serve. → Students get **authentic PYQs, not LLM-generated** questions (critical: UPSC GS is fact-heavy, generation would hallucinate facts).
2. **Chapter filter skipped for UPSC** in `pool_questions`. UPSC rows are `chapter=NULL` (one mixed prelims paper) but the frontend sends topic-named chapters — without the skip every request matched 0 rows and fell to slow LLM `/generate`. The **subject** filter still applies, so GS and CSAT stay separate.

Also: the 517 stems were cleaned (the vision extraction had duplicated the `(a)–(d)` option block inside the stem — removed, so options don't render twice). DB backup at `~/question_bank_engine/data/qbank.sqlite.bak_upsc_stems`.

UPSC taxonomy is registered: `~/question_bank_engine/qbank/upsc_syllabus.py` (GS 10 topics, CSAT 5) → confirmed live via `/chapters`.

**Net effect for you:** your existing `fetch_pool()` → `EXAMGEN_URL/pool` path already returns authentic UPSC questions the moment the frontend requests `exam="UPSC Civil Services (Preliminary)"`. No API changes needed on your side.

---

## 3. Frontend wiring to add (apply to your canonical `lms` source)

These are the exact blocks. (They are already correct in the stale Gurukul repo — copy them into your real source, don't invent new ones.)

### `app/examgen.py`

**In `RAG_SUBJECTS`** (add both entries):
```python
# ---- UPSC Civil Services (Preliminary) — REAL past-paper PYQs (2023-2025), not RAG-generated ----
"upsc-gs": {
    "label": "UPSC GS (Prelims)", "exam": "UPSC Civil Services (Preliminary)",
    "subject": "General Studies", "kw": "gs",
    "match": ["upsc gs", "upsc general studies", "upsc prelims gs", "civil services gs",
              "upsc-gs", "general studies prelims", "ias prelims gs"],
},
"upsc-csat": {
    "label": "UPSC CSAT (Prelims)", "exam": "UPSC Civil Services (Preliminary)",
    "subject": "CSAT", "kw": "csat",
    "match": ["upsc csat", "csat", "upsc aptitude", "civil services aptitude", "upsc-csat",
              "csat prelims"],
},
```

**In `GOALS`** (add):
```python
"upsc": {
    "label": "UPSC Civil Services", "tag": "Civil Services · IAS", "emoji": "🏛️",
    "subjects": ["upsc-gs", "upsc-csat"],
},
```

**In `DIFFICULTY_LADDER`** (add — all bands = "3" because every UPSC PYQ is stored at difficulty 3):
```python
"UPSC Civil Services (Preliminary)": {"easy": "3", "mix": "3", "hard": "3"},
```

### `app/main.py`

**In `EXAMS`** (add):
```python
{"id": "upsc", "subject": "upsc-gs", "title": "UPSC", "tag": "Civil Services · IAS", "emoji": "🏛️"},
```

**In `STUDENT_EXAMS`** (add — `available: True` makes the picker card selectable, not "Soon"):
```python
{"id": "upsc", "title": "UPSC", "tag": "Civil Services", "emoji": "🏛️", "available": True},
```

**In `_student_goal(...)` fallback** (add before the default return):
```python
if "upsc" in hay or "civil services" in hay:
    return "upsc"
```

That's the entire frontend change. No template edits — the picker, subject page, and test engine all read these structures.

---

## 4. Verify after deploy

```bash
# 1. UPSC card is selectable (should NOT be in the "soon" list)
curl -s "https://acharya.trigunai.com/exam-prep?cb=$(date +%s)" | grep -o 'exam soon[^>]*>[^<]*<[^<]*<b>[^<]*' | grep -i upsc
#   ^ expect NO output (empty = UPSC is available)

# 2. Pool serves authentic UPSC end-to-end (GS + CSAT), even with a topic chapter
curl -s "https://gurukul.trigunai.com/examgen/pool?exam=UPSC+Civil+Services+%28Preliminary%29&subject=General+Studies&chapter=Polity+%26+Governance&difficulty=3&type=MCQ_single&count=5"
curl -s "https://gurukul.trigunai.com/examgen/pool?exam=UPSC+Civil+Services+%28Preliminary%29&subject=CSAT&difficulty=3&type=MCQ_single&count=5"
#   ^ both return count=5 with real stems + 4 options + correct_answer
```
Then take a real UPSC test in the UI and confirm questions render once (no duplicated options) and grade correctly.

---

## 5. Known limits (launch-acceptable — mention to Deepak, not blockers)

- **No per-topic filtering yet.** All UPSC draws mix across the whole GS (or whole CSAT) pool, because the PYQs aren't topic-tagged (`chapter=NULL`). Topic chips still work as a UI, but every one pulls from the full subject pool. (Next improvement: LLM-tag the 517 into the UPSC taxonomy topics.)
- **Pool is finite** (324 GS / 193 CSAT). If a heavy user drains it, the frontend falls back to LLM `/generate`, which for UPSC facts is hallucination-prone. Won't hit for normal test sizes.
- **Coverage gaps** (parked, not blocking): 2026 paper, ~8–16 gap Qs/paper, and 2022 are not ingested yet (need an EC2 restart to finish extraction).

---

## 6. One-line summary

The 517 authentic UPSC PYQs (324 GS + 193 CSAT) are **already live and serving** from the Gurukul examgen API your frontend already calls. To turn UPSC on for students: **add the 6 wiring blocks in §3 to your real `lms` source and deploy on top of v117** — the backend needs nothing more.
