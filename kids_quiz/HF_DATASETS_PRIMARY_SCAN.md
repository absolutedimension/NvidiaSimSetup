# HuggingFace datasets scan — primary school (Class 1–5), for the kids question bank

**Scanned 2026-08-03.** Goal: find ready-made datasets (questions / worksheets) for Class 1–5 across boards,
the way the SENIOR bank was seeded from HF (JEE/NEET etc.). **Headline finding: for Indian primary boards
specifically, HF has essentially NO clean, ready-to-serve question bank** — unlike seniors. This confirms the
KB+templates engine was the right call (the data doesn't exist to download for primary CBSE/ICSE). What DOES exist
is (a) one all-class CBSE textbook-chunk corpus, and (b) generic English elementary science/math sets usable as
SEED / enrichment / grounding, not drop-in.

## A. India board-specific, primary (Class 1–5) — THIN
| Dataset | Size | Covers | Fields | License | Verdict |
|---|---|---|---|---|---|
| `ayush7/CBSE_ALL_DATA_all_sub_all_class_v0.4` (dup: `tejubhai/...`) | 166K rows / 128 MB parquet | **Class 1→12, all subjects** (confirmed Class 1 English at start, Class 12 Pol-Sci at offset 120k) | Classroom, Subject, Book, Chunk_Number, **Chunk_Data** (textbook text), Question, Answer | **none shown ⚠️** | Q&A are auto-generated *comprehension/meta* questions ABOUT the lesson-plan/textbook ("What is the title of the chapter?", "What is the first activity?") — **NOT student practice items**. Real value = the **Chunk_Data textbook text** as a grounding/RAG corpus + mineable facts. Reference only (no license). |
| `AdithyaSNair/cbse-papers-2009-2025` | 1K–10K docs | CBSE papers | document scans | CC-BY-4.0 | Papers, almost all SENIOR. |
| `ParthKadam2003/NCERT_Dataset`, `KadamParth/NCERT_*` (Science 6–10, Bio/Chem/Phys/… 11–12) | 1K–100K | **Class 6–12 only** | Q/A CSV | MIT | Nothing 1–5. Great for seniors, useless for primary. |
| ICSE primary | — | — | — | — | **Nothing found.** |

## B. Generic English elementary — usable as SEED / enrichment (mostly Class 3–5; needs re-tagging + Hindi localization)
| Dataset | Size | Level / subject | Fields | License | Use for us |
|---|---|---|---|---|---|
| `allenai/ai2_arc` (ARC-Easy) | 5.2K (+2.6K Challenge) | **grade 3–9 science MCQ** | question, 4 choices, answerKey | **CC-BY-SA-4.0 ✓ (commercial OK)** | Best license-safe science/EVS seed for upper-primary (Class 4–5). |
| `allenai/openbookqa` | ~6K | elementary science MCQ | question_stem, 4 choices, answerKey, **`fact1`** (the core science fact) | **unknown ⚠️** | The `fact1` column is basically a **fact bank** — mine those facts into our verified KB (Opus-verify first). License unclear → treat facts as leads, re-verify, don't copy verbatim. |
| `allenai/sciq` | 13.7K | school science (phys/chem/bio) MCQ | question, correct_answer, 3 distractors, **support** passage | **CC-BY-NC-3.0 ⚠️ (NON-commercial)** | Can't use commercially. Reference only. |
| `openai/gsm8k`, `qwedsacf/grade-school-math-instructions` (52♥) | ~8K | grade-school MATH word problems (~grade 5–8) | question, answer (worked) | MIT | Above our Class 1–3 core; we already COMPUTE maths → low value. Maybe Class 5 word-problems. |
| `ChilleD/SVAMP`, ASDiv, MAWPS | ~1–2K each | elementary arithmetic word problems | problem, equation, answer | mixed | Small; arithmetic we already compute. |
| `emozilla/elementary_math-v1` | 100K–1M | computed elementary math | q/a | — | Redundant with our computed maths engine. |

## C. "Worksheets" specifically — almost nothing
`christian-bick/edugraph-worksheets` (image+text, AGPL), `KN123/UE22AM343BB4-Worksheet-1` (tiny). No real worksheet corpus.

## Conclusion + recommended use
1. **No shortcut bank for Indian primary.** Keep generating via **KB + templates** (correct-by-construction) — that remains the engine. HF won't replace it for Class 1–5 CBSE/ICSE.
2. **Enrichment worth doing:** mine **ARC-Easy** (CC-BY-SA, safe) + **OpenBookQA `fact1`** for EVS/GK facts → Opus verifies → fold into `kb/evs_class3.json` / new science KBs. This grows KB coverage from vetted real questions without the licensing risk of copying items.
3. **Grounding corpus:** `ayush7/CBSE_ALL_DATA` Chunk_Data (Class 1–5 slice) = a textbook-text corpus for the RAG-**verify** idea — reference only (no license), never ship its rows.
4. **Maths:** skip — our computed generators already beat the grade-5–8 word-problem sets for Class 1–3.

Downloading any of these = a `datasets`/parquet pull (needs an explicit go-ahead).

## What we actually pulled + did (2026-08-03)
- **OpenBookQA + ARC-Easy pulled** (via HF auto-parquet). OpenBookQA has 1,326 unique `fact1` facts; ~463 pass a Grade-3 EVS
  filter. **Mined → Opus-verified → 10 clean, non-duplicate facts folded into `kb/evs_class3.json`** (e.g. "A flower makes seeds.",
  "Bees carry pollen from flower to flower.", "A cactus stores water in its stem.", "A desert gets very little rain."). Regenerated
  EVS banks (still 0 degenerate) + **deployed v47**. NOTE: the yield is modest — most of OBQA/ARC is above Grade-3 or US-benchmark
  flavored, and some facts are wrong/outdated (e.g. "Pluto is a planet") → confirms **verify, never copy**.
- **CBSE_ALL_DATA corpus = ABANDONED** (see `kids_quiz/corpus_cbse_primary/_README.txt`). On pulling: Class-1 slice is only
  English+Maths, 27 unique chunks (mostly duplicated auto-generated meta-Q&A); Class 2-5 blocked (7376 shards, /statistics 501,
  /filter 504, string-sorted). **Not a viable grounding source.** If we build RAG-verify, ground against the real NCERT EVS PDF the
  curriculum cells already cite, not this dataset.

## Bottom line
HF does not shortcut primary Indian-board content. The one concrete win = **using OBQA/ARC as a FACT-ENRICHMENT feed for the KB**
(mine → verify → fold), which we did for EVS. Keep the KB+templates engine + hand-authoring as the backbone.
