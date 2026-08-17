# How the question pool is actually produced (traced from code + live DB, 2026-08-15)

Written to answer "are these questions embedded in a vector DB, and do we RAG similar ones?"
Short answer: **the questions ARE embedded (pgvector, 384-dim), but vector search is used for
DIVERSITY and DUPLICATE-DETECTION — not for retrieval.** Exemplar retrieval is tag-filtered SQL.

## Three different production paths (not one)

### 1. Compute-the-answer generators — NO LLM, NO RAG, NO embeddings
`qbank/quantgen.py` · `reasoninggen.py` · `englishgen.py` · `staticgkgen.py`
Python builders that construct the question **and compute its answer** (or look it up in an
embedded verified fact table). Correct-by-construction → impossible to serve a wrong key,
copyright-clean, effectively unlimited (bounded only by the builders/fact-tables — which is why
English and Static-GK had to be *expanded* to clear 1,000).
**This is most of the govt-job pool: SSC/Railway/Banking Maths, Reasoning, English, Static-GK.**

### 2. RAG generation — LLM writes a NEW question from retrieved exemplars
`qbank/generator.py::generate_test()`. Used for JEE / NEET / CBSE.
1. **Retrieve exemplars — by SQL TAG FILTER, not vector search.** `_ladder()` narrows on
   (exam, subject, chapter, qtype, difficulty) and widens progressively: exact → chapter+difficulty
   → chapter only; if the exam has nothing, retry against its companion exam
   (`syllabus.EXEMPLAR_FALLBACK`, e.g. NEET Phy/Chem ← JEE Main). Pulls `max(k*5, 15)` candidates.
2. **Embeddings diversify that shortlist** — `semantic.diversify_indices()` picks `k` semantically
   spread exemplars so the LLM sees varied patterns, not near-identical ones.
3. **The prompt IS the RAG** — `_exemplar_block()` puts those exemplars in the prompt; the LLM
   authors a NEW question (never copies one).
4. **Novelty gate** — `semantic.max_similarity()` runs a pgvector cosine search over banked
   questions in scope and rejects near-duplicates (with a TF-IDF fallback if pgvector is down).
5. **Feedback loop** — accepted questions are embedded back via `semantic.upsert_embedding()`.

### 3. Real PYQs — not generated at all
UPSC / BPSC / BPSC TRE. Ingested verbatim with an official (or cross-source verified) answer key
and served straight from `/pool` (`generated=0`). See `BPSC_TRE_STATUS.md`.

## The vector layer
| | |
|---|---|
| Store of record | **SQLite** `data/qbank.sqlite` (~151k verified) |
| Vector mirror | **Postgres + pgvector**, table `questions`, column `embedding` |
| Model | `BAAI/bge-small-en-v1.5`, 384-dim, local ONNX via fastembed (no API cost) |
| Used for | novelty/dedup (`max_similarity`) + exemplar diversification (`diversify_indices`) |
| NOT used for | exemplar **retrieval** (that's tag-filtered SQL) |
| Degrades to | TF-IDF novelty if pgvector/model unavailable — silently, by design |

**Drift is the failure mode:** anything written straight into SQLite (ingested PYQs, the
compute-the-answer pools) never calls `upsert_embedding()`, so it falls out of the vector mirror
and becomes invisible to duplicate detection. Found 6,212 such rows on 2026-08-15 (all of TRE,
BPSC, and the SSC generated pools) → `backfill_embeddings.py` (idempotent, resumable) closes the
gap. **Re-run it after any bulk ingest/fill.**

## Worth doing next (not done)
- **True vector retrieval for exemplars.** Most valuable for TRE/BPSC, where questions are stored
  `chapter=NULL`, so tag-filtering can only narrow to "subject" — embeddings could retrieve
  *topically similar* exemplars instead of a blunt subject-wide sample.
- A cron/post-ingest hook that runs the backfill automatically so the mirror can't drift again.
