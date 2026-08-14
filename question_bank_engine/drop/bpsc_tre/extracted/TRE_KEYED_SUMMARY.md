# BPSC TRE — keyed papers summary (cross-source pipeline, 2026-08-14)

Real BPSC TRE questions answer-keyed WITHOUT the dead official-key host — by sourcing the answers
that are already published (exact-question solved PYQs on Testbook/Prepp/Sarthaks/careers360, cross-checked
+ independent verification; numericals solved by computation). Only the answer *letter* is used (a fact),
never any site's explanation text. HELD on any conflict/ambiguity/figure-only question. See
`TRE_KEYING_PILOT.md` (method) and `TRE_FULLPAPER_KEYING_RESULT.md` (the 81%→99% deep dive).

## Coverage: one keyed paper per edition (breadth-first)

| Paper | Total | Keyed | % | high/med/low | Held | Re-extract | Artifact |
|---|---:|---:|---:|---|---:|---:|---|
| **TRE 1.0** — Class 9-10 GS & Science | 120 | **119** | **99%** | 110/9/0 | 1 | 0 | `tre_science_09_10_KEYED.json` |
| **TRE 2.0** — Class 1-5 Language & GS | 121 | **108** | **89%** | 103/4/1 | 7 | 6 | `tre2_c1_5_gs_KEYED.json` |
| **TRE 3.0** — Class 1-5 Language & GS | 120 | **117** | **97%** | 110/7/0 | 2 | 1 | `tre3_c1_5_gs_KEYED.json` |
| **TOTAL** | **361** | **344** | **95%** | 323/20/1 | 10 | 7 | |

- **344 cross-verified keyed real TRE questions across all three editions.** Answer distributions are
  healthy/non-degenerate per paper (e.g. TRE 3.0: A29·B33·C36·D15·E4 — the D15 reflects statement-based
  "more than one of the above" GK traps, correctly caught).
- **The held/re-extract residue is the honest floor:** figure-only questions (count-the-rectangles,
  circuit diagrams) that need the image, plus a few OCR-garbled math options. TRE 1.0 was pushed 81%→99%
  with a parser fix + exact-Q recovery pass; the same recovery pass would lift TRE 2.0/3.0 similarly but
  wasn't run here (breadth-first).

## What's proven
- The pipeline is **repeatable per paper** at ~90-99% clean-key yield, in ~3-5 min of parallel agent time.
- GK / Bihar-GK / current-affairs — the category One Step actually wants — keys *most* reliably (sourcing,
  not guessing). Applies verbatim to the parallel lane's stuck 66/67/68/69 Prelims papers.

## Still required before any of this serves students (unchanged)
1. **5-option (A–E) serving support** in `store_real_questions.py` / validator / frontend (same dependency
   as BPSC Prelims 66/67/68). Nothing serves until this lands.
2. A **final official-key spot-check** on flagged discrepancies (a few med-confidence D/E calls) — treat
   the cross-source key as "serve-ready pending official-key review", per the trust-anchor discipline.
3. Optional: recovery pass on TRE 2.0/3.0 tails; extractor enhancement for section-restart papers (TRE 1.0
   Social Science under-extracts its Part-II — the richest pure Bihar GK — pending that fix).

## Pipeline artifacts (repo)
`extract_tre.py` (extractor, sequential-number stem fix), `tre_qa.py` (QA classifier), keyed JSONs above.
Per-question schema: `{seq, exam, edition, paper, stem, options{A..E}, answer, status, confidence, sources, note, quality}`.
