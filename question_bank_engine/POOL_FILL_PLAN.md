# One Step Education — "≥1000 pool questions per subject" plan (2026-08-14)

Their handwritten note lists the subjects below. This maps each to what's in the live bank TODAY
(`data/qbank.sqlite` on Gurukul, verified + non-duplicate) and the concrete route to ≥1000 servable
pool questions each. Source of counts = live query 2026-08-14.

## Current state (govt-job / One Step subjects)

| Note subject | Bank source | Have now | To 1000 |
|---|---|---:|---|
| **Maths** (Quant Aptitude) | `quantgen` + Banking-Quant pool 579 | **580** | generate +420 |
| **Reasoning** | `reasoninggen` | **22** | generate +978 |
| **English** (SSC CGL) | `englishgen` | **9** | generate +991 |
| **Static GK** | `staticgkgen` (finite fact tables) | **5** | generate to ceiling + source |
| **GS · Physics** | NEET Physics (borrow) | **5,677** | ✅ covered — map/tag |
| **GS · Chemistry** | NEET Chemistry (borrow) | **13,873** | ✅ covered — map/tag |
| **GS · Biology** | NEET Biology (borrow) | **14,450** | ✅ covered — map/tag |
| **GS · Polity** | real GS (UPSC 365 + BPSC 289 + BPSC TRE 323), NOT sub-tagged | ~part of **977** | sub-tag + source |
| **GS · Geography** | same mixed real GS | ~part of 977 | sub-tag + source |
| **GS · History** | same mixed real GS | ~part of 977 | sub-tag + source |
| **GS · Economics** | same mixed real GS | ~part of 977 | sub-tag + source |
| **Current Affairs** | manual-entry pipeline | **4** | rolling monthly (can't generate) |
| **BPSC TRE** | real keyed PYQs (LIVE) | **323** | extend keying to all 152 papers |
| **Daroga** | no open papers | **0** | generators + shared GS; papers only via student response sheets |

**Headline:** Science GS (Physics/Chem/Bio) is already >1000 each (NEET banks). The real gaps are the
**generated skills** (Maths/Reasoning/English/Static-GK — thin pools) and the **social GS + Current Affairs**
(need real sourcing/tagging).

## The plan — 3 tiers

### TIER 1 — GENERATE (fast, ~1 day; compute-the-answer = unlimited unique)
`quantgen` / `reasoninggen` / `englishgen` build exam-authentic questions AND compute the answer
(no LLM, no key risk), upsert as `verified=1, generated=1`. A batch-fill loop calls `generate_test(store,
spec, count)` per chapter until each subject pool hits the target.
- **Maths → 1000**, **Reasoning → 1000**, **English → 1000**. Trivial — the generators already exist + self-test 100%.
- **Static GK → fill to its ceiling** (finite ~15 fact tables → likely a few hundred unique), THEN expand the
  fact tables and/or source Lucent-style static-GK to top up to 1000.
- **DECISION NEEDED:** these skill subjects are identical across SSC/Railway/Banking. Two options:
  (a) fill ONE shared govt tag (e.g. "SSC CGL") + a tiny serving tweak so govt exams reuse it — **recommended, 1× work**; or
  (b) fill each exam's (exam,subject) pool separately — clean isolation, 3× the rows.

### TIER 2 — MAP / BORROW (already have the content; wire the serving)
GS-Science is covered by the NEET banks. Serve Physics/Chem/Bio to govt-exam students by pointing the
govt GS-Science subject at those banks (the Railway `railway-science` subject already borrows CBSE10 Science —
same pattern). No generation needed; just a RAG_SUBJECTS/serving mapping. **Effort: hours.**

### TIER 3 — SOURCE + TAG (real work, ~weeks)
- **GS-Social (Polity/Geo/History/Economics):** we hold ~977 real GS Qs (UPSC + BPSC + BPSC TRE) but they're
  a single "General Studies" bucket. Run a **tagging pass** (the same cross-source/agent method) to split them
  into the 4 social dimensions, THEN source more real PYQs (more BPSC/TRE editions, UPSC years) to reach 1000
  EACH. The BPSC TRE keying pipeline is the reusable engine here.
- **BPSC TRE → thousands:** we keyed 3 of 152 downloaded papers. Running the pipeline over the rest yields
  several thousand more real Bihar-GK/GS/Science/Maths Qs (feeds Static-GK + GS-Social + TRE line).
- **Current Affairs:** cannot be generated (time-sensitive). Realistic target = a **rolling ~200-300 curated
  set + monthly human entry** via `current_affairs/` importer, NOT 1000 static. Set expectations with One Step.
- **Daroga:** no open papers. Serve Maths/Reasoning/English from the generators + GS from the shared banks;
  real Daroga PYQs only via a student's response sheet (deferred).

## TIER 1 RESULTS (executed 2026-08-14, `fill_pool.py`, live Gurukul bank, DB backed up)
Filled under the **SSC CGL** tag (students already hit these subjects; reusable across Railway/Banking
with a small serving tweak). Live-serving verified via `/examgen/pool`.

| Subject | Before | After | Result |
|---|---:|---:|---|
| **Maths** (Quant Aptitude) | 580 | **1,007** | ✅ 1000 hit (combinatorial → unlimited) |
| **Reasoning** | 22 | **1,007** | ✅ 1000 hit (combinatorial → unlimited) |
| **English** | 9 | **420** | ⚠️ generator CEILING (finite templates) |
| **Static GK** | 5 | **323** | ⚠️ generator CEILING (finite ~15 fact tables) |

**English + Static-GK stalled at their generators' unique-combination ceiling** — as the plan predicted for
finite-content subjects. To reach 1000 each, ONE of:
- **Expand the generators** (add builder types to `englishgen`: cloze, error-spotting, para-jumble, reading-
  comprehension, one-word-substitution; add fact tables to `staticgkgen`: more awards/rivers/dynasties/
  schemes/books-authors/sports/organizations). Each new builder/table adds a block of unique questions —
  cheapest path, no key risk. **← recommended next.**
- **Source real SSC English + Static-GK PYQs** via the exact-question / cross-source keying pipeline.

## Recommended sequence
1. **TIER 1 batch-fill** Maths + Reasoning + English to 1000 (1 day) — biggest visible jump for Rohan's pitch.
2. **TIER 2 map** GS-Science → NEET banks (hours) — instantly puts Physics/Chem/Bio "1000+ live".
3. **TIER 1 Static-GK** fill + fact-table expansion.
4. **TIER 3** GS-Social tagging + more BPSC/TRE keying (ongoing); Current-Affairs monthly cadence.

After Tiers 1-2, **10 of the 13 note subjects are at ≥1000**; the remaining 3 (GS-Social split, Current
Affairs, Daroga papers) are the honest medium-term work.
