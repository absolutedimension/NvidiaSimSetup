# Merchant Navy — GP Rating (Synergy CET) as an Acharya exam

> ## ✅ STATUS 2026-08-19 — Phases 1–2 BUILT (text-only track)
>
> Decision taken: ship the text-only technical bank + aptitude first; figures deferred.
>
> | | |
> |---|---|
> | **Ingested** | 769 parsed → 93 duplicates → **676 unique, all verified** |
> | **Servable text-only** | **593** (Ship Knowledge 420 · Marine Engineering 167 exemplars) |
> | **Held back as `needs_figure`** | **164** — picture-identification, gated out of serving *and* out of exemplar retrieval |
> | **Copyright gate** | ✅ verified — `pool_questions(exam="Synergy CET")` returns **0 rows** |
> | **Chapters** | 22, real DG-syllabus names, taxonomy strings match the DB **exactly** |
>
> **New/changed files:** `qbank/gp_rating.py` (new) · `qbank/extractor.py` (`from_synergy_pdf`)
> · `qbank/pipeline.py` (`ingest_synergy`) · `run.py` (`ingest-synergy`) · `qbank/syllabus.py`
> · `qbank/models.py` (figure detector) · `qbank/validator.py` (short-stem rule)
> · `lms/app/examgen.py` + `lms/app/main.py` (5 subjects, goal card, ladder)
>
> ```bash
> python3 run.py ingest-synergy --pdf "/path/to/SYNERGY .pdf"
> ```
>
> ### Phase 3–4 also done (on qbank-worker VM, 2026-08-19)
>
> | | |
> |---|---|
> | **Generated** | **218** — Ship Knowledge 89, Marine Engineering 129, **0 failed cells** |
> | **Key audit** (`run.py audit-keys --k 5 --style auto`) | **216 passed / 0 disagreed / 2 rejected** = 99.1% |
> | Cross-model check (gpt-4o, 30 sampled) | 30/30 — so the pass rate is not pure self-agreement |
> | Aptitude (§C/E/F) | **already live in production** at ~1,000 each under the `SSC CGL` tag — no work needed |
>
> **The 2 rejects were real defects**, not noise: both ullage questions had arithmetically
> wrong keys *and* the correct value absent from the options (8.60−6.95 = 1.65, keyed 1.35).
> They are now `verified=0` and unservable.
>
> **NOT done — nothing is live:** the 218 sit on the worker's disk, un-synced; the LMS code
> changes are local and uncommitted. Two separate deploys remain (§6 Phase 5), plus the human
> spot-check of 30 by someone who knows ships. Worker deallocated.


> Plan only. Nothing built. Written 2026-08-19 from `~/Downloads/SYNERGY .pdf` (612 pp, 36.5 MB)
> after a working extraction prototype was run against it.
> **Revised 2026-08-19: copyright-clean GENERATION chosen. The PDF is never served.**
>
> ⚠️ **Vow check first — see §0.** New exam vertical, no named institute, no rupee attached.
> Under `SANKALPA.md` आगार 3 that is *building*, not selling.

---

## 0. The gate (read before anything else)

The live vow (`SANKALPA.md`, expires 2026-09-07): no build work until the day's one selling
action for the Patna institutes is done. आगार 3 permits build work only when **a named person
asked and a rupee is attached.** Merchant Navy has neither today; One Step's money ask is still
unmade since 12 Aug.

**Phase 0 (§6) is a phone call, not code.** Everything after it is one day of work.

---

## 1. What the exam is

**Synergy Common Entrance Test (CET)** — Synergy Marine Group, one of the world's largest ship
managers. A **sponsorship** exam, not a college entrance: clear it and Synergy pays for your
pre-sea training and takes you onto their ships. GP Rating is the 10th-pass entry route — the
highest-volume, lowest-income segment, and the one that buys coaching.

### Verified against the official site (not the PDF)

| Item | Reality (2026 cycle) |
|---|---|
| 2026 CET date | **17 May 2026** (registration closed 4 May) |
| GP Rating age | Born **on/after 1 Dec 2001** (max 25) |
| GP Rating marks | Class X: 50% aggregate **and 50% in English**; ITI: 50% final year + 50% English |
| Contact | examinationcell@synergyship.com |

⚠️ **Two corrections to the original premise:**

1. **The 2026 exam was in May, not March.** Confirm the 2027 date before any content calendar
   is built on it.
2. **The PDF is stale and unofficial** — community-compiled, credited to an Instagram handle.
   Eligibility says "born after 1997"; GK is July-2021. Treat every claim in it as unverified.

### Exam pattern

180 minutes · 200 MCQs · +1 correct, **−0.25 wrong**, 0 unattempted.

| § | Section | Qs |
|---|---|---|
| A | Navigation, cargo handling & safety | 50 |
| B | Machinery ops, workshop practice & safety | 50 |
| C | Basic numerical reasoning | 25 |
| D | Basic pattern recognition | 25 |
| E | Basic logical reasoning | 25 |
| F | General knowledge & mechanical reasoning | 25 |

A + B come from the **approved DG Shipping syllabus for GP Ratings (Training Circular 1 of
2018)** — a fixed, public, *government* syllabus. That matters twice over: it makes the
knowledge half a stable taxonomy, and **the syllabus itself is a citable non-copyright source**
for grounding generation.

---

## 2. What is in the PDF (extraction already proven)

I ran a real parser. **1,450 of 1,453 answer-keyed questions parsed first pass — 99.8% yield,
regex only, zero LLM cost, ~3 seconds.** Two rigidly consistent formats:

```
Ques 25. <stem>            |   25. <stem>
A. <opt>                   |       A. <opt>
Answer: Option D           |   Right Answers : A
Explanation: <worked soln> |
```

### Page map (612 pp)

| Pages | Content | Keyed Qs | Role under the new plan |
|---|---|---|---|
| 5–139 | Numerical reasoning | 437 | ❌ **not needed** — `quantgen.py` covers § C |
| 154–175, 241–283 | Logical reasoning, series, dice | 147 | ❌ **not needed** — `reasoninggen.py` covers § E |
| 176–240 | Spatial / pattern | 2 | ❌ not needed — `figuregen.py` covers § D |
| 284–307 | General knowledge (July 2021) | 95 | ❌ **stale, discard** — `staticgkgen.py` covers § F |
| **410–509** | **Section A — GSK chapters 1,2,3,5,6,7,8,9,10** | **523** | ✅ **RAG exemplars (never served)** |
| **510–575** | **Section B — MEK chapters 1,2,7,9,10,12,13,14,15,16,17,18,20** | **249** | ✅ **RAG exemplars (never served)** |
| 331–360 | GP Rating study material + nautical glossary | — | ✅ **grounding corpus** (see §4) |
| 308–323 | Interview questions | — | ✅ later — content, not MCQs |
| 576–612 | Scanned pages | 0 | ❌ skip |

**The decision to generate collapses the PDF's role from 1,450 questions to 772.** Everything
in sections C/D/E/F now comes from generators we already own and that never touched this book.

### The best find

pp. 410–575 aren't a book — they're a dump from an MTI's exam software
(`Exam Title : Chapter GSK 2` … `Right Answers : A`). The 772 maritime questions arrive
**already tagged to DG-syllabus chapters**, so the LLM tagging pass is free and it's ground truth.
That tagging is exactly what `retrieve_exemplars()` filters on.

```
GSK  1: 64   GSK  2: 44   GSK  3: 40   GSK  5: 47   GSK  6: 71
GSK  7: 84   GSK  8: 61   GSK  9: 75   GSK 10: 35        → 521
MEK  1: 22   MEK  2: 28   MEK  7: 58   MEK  9: 20   MEK 10: 21
MEK 12: 17   MEK 13: 10   MEK 14: 10   MEK 15:  8   MEK 16: 12
MEK 17: 10   MEK 18: 21   MEK 20: 11                     → 248
```

Gaps: **GSK 4 and MEK 3, 4, 5, 6, 8, 11, 19 absent.** With generation this matters less —
those chapters can be generated from the DG syllabus text alone (§4, Track 1b).

---

## 2b. Public sources — what actually exists (searched 2026-08-19)

### HuggingFace: nothing. Confirmed dead end.

Queried the HF datasets API across `merchant navy`, `maritime`, `GP rating`, `seafarer`,
`IMU CET`, `nautical`, `marine engineering`, `shipping exam`, `STCW`, `COC exam`.
**Zero maritime exam-question datasets.** The only maritime hits are legal codes, a vessel
dataset, and three unrelated sub-1K CSVs. Nobody has published this domain. That is the
moat and the cost in one sentence.

### ✅ THE FIND — an OFFICIAL Synergy model paper, publicly published

**`https://www.synergyseastar.in/Images/Users/GP Rating Model Question Paper.pdf`**

Published by the exam body itself, on its own domain (`synergyseastar.in` is Synergy's SEASTAR
CET portal). **41 pages · 62 questions · 60 official keys · 60 embedded images.** Its own note:
*"you will find sample question/previous years questions below."*

Rigid, parseable format:

```
GP-A-01
Direction        Identify the equipments placed on navigation bridge indicated by the arrow
Question         <image>
Answer Options   1. …  2. …  3. …  4. …
Correct Option : (1)
Solution : Self-Explanatory
```

**This is worth more than the 612-page compilation, for three reasons — and each one changes
the plan.**

#### 1. The real exam is overwhelmingly VISUAL

60 embedded images for 62 questions. Section A is dominated by *"identify the equipment in the
picture"*, *"identify the flag"*, *"identify the markings"*. The compiled book's GSK/MEK banks
are **text recall** — a different question species.

> **Consequence:** authentic Section-A questions cannot be produced by text RAG at all, and the
> `needs_figure` serving gate would (correctly) refuse to serve them. **Figures move from
> Phase 5 "demand-gated" to a core requirement.** Without them we generate a bank that is
> plausible but does not resemble the paper — the exact failure a coaching institute will spot
> in ten seconds.

#### 2. The section LETTERING conflicts with the book — resolve before building the mock

The official paper shows **Section A – Technical** (30 Qs) and **`GP-B-xx` — numerical aptitude**
(32 Qs: fractions, ratios, averages, ages, LCM, surds). The book claims six sections at
50/50/25/25/25/25 with **Section B = Machinery**.

⚠️ **Do not over-read this.** The official paper states it is *"a sample of 30 questions [per
section] so as to give you an idea"* — it is a **sample, not a full blueprint**, and may simply
not show sections C–F. A 6-section exam is not ruled out.

What *is* a real conflict is the **lettering**: official Section B is aptitude, the book's
Section B is Machinery. At least one is wrong. Since `build_mock_papers.py` needs an exact
blueprint — and the section split is the most visible feature of the demo — **confirm the live
pattern from the actual exam notification / registration form before Phase 5.** Treat the
official paper as authoritative for *format and style*, and the book's 6-way split as
**unverified** until then.

#### 3. It is safe to use as a reference

Officially published by the exam body — unlike the Scribd/Instamojo copies (see below). It is
small (62 Qs), so it is a **format/blueprint reference and a QA yardstick**, not a bank.
Best use: the *style* exemplars in `build_prompt()`, with the compiled book supplying breadth.

### ✅ The government syllabus (grounding corpus for §4 Track 1b)

**DG Shipping Training Circular 1 of 2018 (GP Rating, revised)**
`https://www.dgshipping.gov.in/writereaddata/ShippingNotices/201801221112395971358Trg_cir1_2018_GP_revised.pdf`

A **public Government of India document** — the ideal grounding corpus, and citable.
⚠️ **Not verified:** `dgshipping.gov.in` refuses connections from this machine (likely
India-only / network-blocked). The URL is confirmed to exist via search but I could not open it.
**Deepak should fetch it from India and confirm it carries the module breakdown** — if it names
the GSK/MEK modules, it also fills the 8 chapters the book is missing.

### ❌ Everything else — do not use

Scribd, Instamojo, seatracker.ru results are **pirated or paywalled copies of the same Suman
Chakraborty compilation we already have.** No new information, and sourcing from them is worse
copyright exposure than the file on disk. One "TS Rahaman GP Rating sample paper" exists on
Scribd — a different MTI, same provenance problem.

---

## 3. Copyright-clean by default — the architecture already does this

Two mechanisms already in the codebase do the work. **Neither needs to be built.**

### (a) The serving gate makes exemplars structurally unservable

`qbank/storage.py:233`:

```python
if exam and (exam.startswith("CBSE Class") or exam.startswith("UPSC")
             or exam.startswith("BPSC") or exam.startswith("Current Affairs")):
    pass                                        # real-PYQ exams: serve everything
else:
    where.append("COALESCE(generated,0)=1")     # everyone else: serve ONLY generated
```

Because `"Synergy CET"` is **not** on that allowlist, `/pool` will serve **only `generated=1`
rows**. The 772 ingested exemplars sit at `generated=0` and are unreachable by any student
request — not by policy, by SQL. `pool_stats()` has the identical gate, so coverage numbers
count only generated rows too.

> ⚠️ **The one rule that must not be broken: never name this exam with a prefix on that
> allowlist.** The check is `startswith`. Naming it "Current Affairs — Maritime" or letting it
> inherit a `BPSC…` prefix would silently start serving raw exemplars. **Exam string is
> exactly `Synergy CET`.** Put this in the commit message.

### (b) The novelty gate rejects anything too close to the source

`qbank/generator.py` — the module docstring states the intent outright: *"a generated question
that is too similar to any exemplar / banked past-paper question is REJECTED and regenerated.
We learn the pattern; we never resell the paper."*

- `NOVELTY_MAX_SIM = 0.82` — generated stem must be **< 0.82 cosine** vs any reference
- Reference pool = the exemplars used **+ a 50-question wider slice of the same chapter**,
  both pulled with `include_generated=False` (i.e. compared against *real* questions only)
- pgvector `max_similarity()` does the same check bank-wide, with a TF-IDF fallback
- The prompt instructs: *"invent a DIFFERENT scenario with DIFFERENT numbers. It must NOT be a
  reworded exemplar. The exemplars are ONLY style/difficulty references."*

**Net: the copyright-clean requirement costs zero new code. It costs one naming discipline.**

---

## 4. Two tracks — and only one touches the PDF

### Track 1 — Sections A + B (100 of 200 Qs): RAG generation

The JEE/NEET path (`generator.py::generate_test`), unchanged:
tag-filtered exemplar retrieval → semantic diversification → LLM authors a NEW question →
novelty gate → validator → store `generated=1`.

**⚠️ The one genuinely new risk: these are FACTUAL-RECALL questions, not computational.**

For JEE physics the LLM invents a new problem with new numbers and the answer is *derivable* —
wrongness is catchable. For *"A quick closing valve is fitted on…"* there is nothing to compute.
A hallucinated key on a safety question ("what is the SWL of this shackle") is worse than no
question at all. This is the difference between this vertical and every previous one, and it is
where the effort goes.

Three controls, in order of strength:

1. **`solver.solve_consistent(q, llm, k=5)`** — already built. After generation, independently
   solve each question 5×; keep it only if the majority agrees with the stated key. Disagreement
   → `solution_mismatch` flag → not verified → never served. **This is the primary gate and it
   already exists.**
2. **Ground the generation, don't just style it** (Track 1b). Put the *DG Shipping Training
   Circular 1 of 2018 syllabus text* + the PDF's own nautical glossary and study material
   (pp. 331–360) into the prompt as a **knowledge** corpus alongside the style exemplars. The
   LLM then writes from a cited source rather than from memory. This also unlocks the 8 missing
   chapters (GSK 4, MEK 3/4/5/6/8/11/19), which have no exemplars at all.
   *This is the only real code addition in the whole plan — a knowledge-grounding block in
   `build_prompt()`. Est. half a day.*
3. **Human spot-check before first demo.** 30 questions from A + B read by someone who knows
   ships. Non-negotiable before it goes in front of an institute.

### Track 2 — Sections C, D, E, F (100 of 200 Qs): compute-the-answer, **zero PDF contact**

These are already built, already copyright-clean *by construction* (the generator computes the
answer, so it cannot be wrong and cannot be copied), and already serving SSC/Railway/Banking:

| § | Section | Engine | Status |
|---|---|---|---|
| C | Numerical reasoning (25) | `qbank/quantgen.py` | ✅ reuse as-is |
| D | Pattern recognition (25) | `qbank/figuregen.py` + `reasoninggen.py` | ✅ reuse as-is |
| E | Logical reasoning (25) | `qbank/reasoninggen.py` | ✅ reuse as-is |
| F | General knowledge (~13) | `qbank/staticgkgen.py` + `current_affairs/` | ✅ reuse, fresh CA |
| F | **Mechanical reasoning (~12)** | — none | ⚠️ **new, ~half a day** |

Mechanical reasoning (levers, gears, pulleys, inclined planes) is highly templatable —
compute-the-answer, same shape as `quantgen.py`. It is the second and last code addition.

**Half the paper never touches the PDF at all.** That halves the exposure and most of the work
is already done.

---

## 5. Integration into Acharya — exact files

Same shape as the SSC CGL / BPSC TRE rollouts. No new architecture.

**1. Exemplar loader** → `qbank/pipeline.py::ingest_synergy()` + a `run.py ingest-synergy`
subparser. **Not a standalone script** — it goes in the same slot as `ingest_grafite()` /
`ingest_datavorous()`, which are the existing precedent for *"pre-tagged + pre-solved text"*
banks. The Synergy chapter dump is exactly that shape: pre-tagged (`Exam Title : Chapter GSK 2`),
pre-keyed (`Right Answers : A`), pre-solved (`Explanation:`).

⚠️ **Do not route this through `ingest_pdf()`** — that path "requires the vision LLM" and is
built for scanned papers. Ours parses with regex at 99.8%, so the vision path would burn tokens
to do worse. Vision is only needed for the 38 scanned pages, which we're skipping.

Reuses the standard downstream exactly as the other ingests do:
`cleaner.clean()` → `cleaner.flag_duplicates(existing_hashes=...)` → `validator.validate()` →
`store.upsert()` → `_report()`.

Writes 772 rows: `exam="Synergy CET"`, `subject`, `chapter`, `stem`, `options`,
`correct_answer`, `solution`, `source="synergy_compilation_exemplar"`, `verified=1`,
**`generated=0`**. Sections C/D/E/F are **not** loaded.

**2. Taxonomy** → `qbank/syllabus.py` `TAXONOMIES`:

```python
("Synergy CET", "Ship Knowledge & Safety"):  GP_RATING_GSK,    # DG chapters GSK 1-10
("Synergy CET", "Marine Engineering"):       GP_RATING_MEK,    # DG chapters MEK 1-20
("Synergy CET", "Numerical Reasoning"):      BANKING_QUANT,    # reuse
("Synergy CET", "Logical Reasoning"):        REASONING_COMMON, # reuse
("Synergy CET", "General Knowledge"):        STATIC_GK_COMMON, # reuse
("Synergy CET", "Mechanical Reasoning"):     MECHANICAL_COMMON,# new
```

⚠️ Mandatory, not cosmetic — `get_taxonomy()` used to fall back to JEE Physics, which is how
BPSC/TRE showed "Kinematics" in the chapter picker (`feedback-chapter-picker-physics-fallback`).

**3. Subject registry** → `lms/app/examgen.py` `_SUBJECTS`, 6 entries with `match:` aliases
("gp rating", "merchant navy", "synergy", "deck rating", "engine rating", "seafarer").

**4. Goal card** → `_GOALS` + `lms/app/main.py`:
```python
"gp-rating": {"label": "Merchant Navy (GP Rating)", "tag": "Synergy CET · Sponsorship",
              "emoji": "⚓", "subjects": [...6...]},
```

**5. Difficulty ladder** → `_LADDER`: `"Synergy CET": {"easy": "2", "mix": "2-3", "hard": "3"}`.
⚠️ `/pool`'s default band is 3–4 and returns empty against a band-2 bank
(`feedback-cbse-upsc-serve-real-pool`). Set the ladder **before** testing or it will look broken.

**6. Pool fill** → `run.py batch-generate --exam "Synergy CET" --subject <s>` — the existing
`pipeline.py::batch_generate()`, which walks the taxonomy cell-by-cell and is resumable via
`pool_stats()` (skips cells already at target). Target ~1,000/section. Track 2 sections fill
instantly (no LLM); Track 1 costs LLM tokens — budget for it.

**6b. Correctness gate** → `run.py reverify --exam "Synergy CET" --k 5`.
This is `pipeline.py::reverify_solutions()` — **already a CLI command**, already doing
majority-vote self-consistency (`solver.solve_consistent`) and promoting only questions where
the majority agrees with the key; the rest stay flagged for human review. This is the existing
answer to the factual-hallucination risk in §4. Nothing to build.

**6c. Figures** → `run.py mark-figures` (`pipeline.py::mark_needs_figure()`). 55 of the 772
exemplars are figure-dependent ("Select part no.2 from the following picture"). The serving gate
in `storage.py` already refuses to serve a question that `needs_figure` without one, so this just
has to be *run* — and generated questions inherit the same protection.

**7. Embeddings** → `backfill_embeddings.py` after the exemplar load **and** after each fill.
Non-optional: exemplars written straight to SQLite never call `upsert_embedding()`, so they'd
fall out of the vector mirror and **the novelty gate would stop seeing them** — i.e. the
copyright guarantee silently degrades. This is the drift failure mode that hit TRE/BPSC
(6,212 rows, 2026-08-15). **Run it, then verify a non-zero embedding count.**

**8. Mock paper** → `build_mock_papers.py` (the LLM path, since these are generated — **not**
`build_pool_papers.py`, which is for real PYQs). Assembles the real 50/50/25/25/25/25 split,
180 min, −0.25 negative marking. **This is the demo object.**

**9. Serving** → nothing to change. `generated=1` via `/pool`, as §3(a) explains.

### What is genuinely new vs. reused

| | |
|---|---|
| **New code (≈1.5 days total)** | `ingest_synergy()` + CLI subparser · `MECHANICAL_COMMON` taxonomy + generator · knowledge-grounding block in `build_prompt()` |
| **Config only** | `TAXONOMIES` entries · `_SUBJECTS` · `_GOALS` · `_LADDER` |
| **Reused unchanged** | `cleaner` · `validator` · `solver.solve_consistent` · `generator.generate_test` + novelty gate · `batch_generate` · `reverify_solutions` · `mark_needs_figure` · `pool_stats` · `quantgen` · `reasoninggen` · `figuregen` · `staticgkgen` · `backfill_embeddings` · `/pool` serving · `build_mock_papers` |

The pipeline is not being extended — it is being **pointed at a new exam string.** Every stage
between ingest and serving already exists and already runs for JEE/NEET/SSC.

---

## 6. Phases

| Phase | Work | Command / file | Effort |
|---|---|---|---|
| **0** | **Find one named GP-Rating institute who says "if you have this, I'll use it."** Confirm the 2027 CET date. | a phone call | **—** |
| 1 | Load 772 exemplars (`generated=0`), mark figures, embed, **verify unservable** | `run.py ingest-synergy` → `run.py mark-figures` → `backfill_embeddings.py` | 3 h |
| 2 | Taxonomy + subjects + goal card + ladder | `syllabus.py`, `examgen.py`, `main.py` | 2 h |
| 3 | **Track 2 fill** — C/D/E/F, no PDF, no LLM cost | `run.py batch-generate` ×4 | 2 h |
| 4 | **Track 1 generation** — A/B RAG, then the correctness gate, then 30 read by a human | `run.py batch-generate` → `run.py reverify --k 5` | 1 day |
| 5 | Full 200-Q mock, −0.25 marking → **the demo** | `build_mock_papers.py` | 2 h |
| 6 | Knowledge grounding (DG syllabus + glossary) → unlocks the 8 missing chapters | `generator.py::build_prompt` | 0.5 day |
| 7 | Mechanical-reasoning generator | new `qbank/mechgen.py` | 0.5 day |

Phases 1–5 are almost entirely **existing commands against a new `--exam` value.**

**Demoable after Phase 5: ~2 days.** Phases 6–7 are quality/coverage, demand-gated.

Note the ordering change from the first draft: **Track 2 (Phase 3) lands before Track 1
(Phase 4)** — it is free, instant, and gets half the paper live before a single LLM token is
spent on maritime content.

---

## 7. Risks after the generation decision

| Risk | Before | Now |
|---|---|---|
| **Copyright** | High — serving a private compilation verbatim | ✅ **Resolved.** Exemplars unservable by SQL; novelty gate < 0.82; half the paper never touches the PDF. Residual risk is the naming rule in §3(a). |
| **Factual hallucination in A/B** | n/a (was verbatim) | ⚠️ **This is now the main risk.** Recall questions have no derivable answer. Mitigated by `solve_consistent(k=5)` + grounding + human spot-check — not eliminated. |
| **March date unverified** | High | Unchanged — 2026 CET was 17 May. Confirm before any calendar. |
| **Incomplete DG coverage** | 8 chapters missing | Reduced — Phase 6 generates them from syllabus text. |
| **Stale GK / eligibility** | Medium | ✅ Resolved — 2021 GK discarded entirely; GK comes from `current_affairs/`. |
| **Market is ~4,400, not 10,000** | **High — new, measured** | See §7b. Synergy's own 2024 results PDF puts GP Rating at **~4,400 registrations and 56 selected (1.3%)**. **DNS is ~23,000 — 5× bigger.** |
| **Figures required for authenticity** | **High — new** | The official paper is 60 images / 62 questions. A text-only bank will not look like the exam. |
| **New vertical = goal-wobble** | High | **Unchanged.** Merchant navy is not Patna institutes. |

---

## 7b. Market size — measured, not assumed

Synergy publishes its own results. Parsing them gives real numbers instead of the "10,000
students" estimate.

**`Synergy-GP-Rating-2024-Results.pdf`** — registration numbers run `01SYN000021` →
`01SYN004432`, and **56 candidates** are listed as advancing to interview.

**`Synergy CET - DNS Merit List.pdf`** — prefix `09SYN`, range `000113` → `023143`,
163 listed. **Different prefix per stream**, so the sequences are per-stream, not shared.

| Stream | Prefix | Approx. registrations | Selected |
|---|---|---|---|
| **GP Rating** (2024) | `01SYN` | **~4,400** | **56 (1.3%)** |
| **DNS** (2026) | `09SYN` | **~23,000** | 163 |

*(Different years, so not a clean comparison — but the order-of-magnitude gap is unambiguous.)*

**Three conclusions:**

1. **GP Rating is ~4,400, not 10,000.** The premise was roughly 2× optimistic — for Synergy.
   Other sponsors (Anglo-Eastern, Fleet, MSC) run their own tests, so the *total* GP-Rating
   coaching market is larger than 4,400; but no single exam is 10,000.
2. **A 1.3% selection rate is the strongest sales argument in this whole plan.** 4,400 people
   competing for 56 seats will pay for preparation. Scarcity, not volume, is the wedge — and it
   is a much better story to an institute owner than "big market".
3. **DNS is ~5× the market, and a better-resourced buyer** (12th-pass PCM, families already
   funding a maritime career, overlaps IMU CET). **If the goal is volume in merchant navy, DNS
   is the target, not GP Rating.** GP Rating is the cheaper *first* build because we already
   hold the content — that is an argument about cost, not about size.

---

## 7d. ✅ DISQUALIFIER ANSWERED — direct student channel + 5 committed (2026-08-19, same day)

**§7c below is superseded.** It said the blocker was *no channel to reach anyone*. Two facts
close that:

1. **The B2C student pipeline is live and running** — `acharya.trigunai.com/exam-prep`,
   self-serve signup, 14-day trial, Razorpay live (`project-acharya-student-product`).
   No institute, no teacher, no field visit required. The channel was already built.
2. **5 students ready to enroll if the subject exists.** Not n=1 speculation — 5 named people.

That satisfies आगार 3's own test — *"can I name the person who asked, and is a rupee attached?"*
Five names, five rupees. It is **not** the vow's Patna-institute विषय, and that trade is
Deepak's call to make in writing — but it is not the unnamed, unattached building the vow exists
to catch.

### ⚠️ The one condition — collect BEFORE you build, not after

`project-pmf-audit-202607`: **0/3 closed in June; watchers ≠ buyers.** "Ready to enroll" is the
exact sentence that produced those three misses. Five people saying yes to a thing that does not
exist yet costs them nothing.

**The funnel is already live, so this is testable today, at zero build cost:**
send all 5 the signup link now, on the subjects that already exist. If 5 start trials, the
demand is real and the build is justified. If 0 do, that is the single most valuable thing
you'll learn this month — and it cost one message.

> This is not a delay tactic. It is one day, it uses infrastructure that is already running,
> and it is the difference between the first 5 paying students and the fourth "they liked it."

### Scope collapses for 5 students

The plan below was sized for a market. **For 5 students it is roughly a quarter of the work.**

| Sized for a market | Sized for 5 students |
|---|---|
| ~1,000 questions per section | **~200/section is more than 5 students can exhaust** |
| Full 200-Q mock paper (Phase 5) | Defer — ship practice first, mock once they're active |
| Figures pipeline (Phase 6/7) | ⚠️ **Still required** — see risk below |
| Phases 1–7, ~2 days | **Phases 1–4, ~1.5 days** |

**Revised order — half the exam ships on day one, free:**

- **Day 1:** `ingest-synergy` → taxonomy/subject/goal card → **Track 2 fill (C/D/E/F)**.
  Track 2 is compute-the-answer: no LLM cost, no PDF, correct-by-construction, and it is
  **100 of the 200 marks.** Students have a working product at end of day 1.
- **Day 2:** Track 1 RAG for Sections A/B → `run.py reverify --k 5` → human reads 30.

### ⚠️ The risk that now matters most

With 5 real students, **the figure gap (§2b) becomes the product risk.** The official paper is
**60 images across 62 questions** — Section A is picture-identification. A text-only technical
bank will not look like the exam, and these 5 have seen the real thing.

In a community this small, 5 disappointed students is not a churn statistic — it is the whole
referral loop. **Either ship Sections A/B with figures, or ship only the aptitude half (which is
genuinely strong, free, and correct-by-construction) and say plainly that technical is coming.**
Under-promising to your first 5 payers is recoverable. Over-promising is not.

---

## 7c. ⛔ (SUPERSEDED by §7d) The disqualifier as it stood before the 5 students

**Field report:** the student who forwarded the PDF is **not enrolled in any coaching.** He
prepares from **YouTube and circulated PDFs.** (n=1 — but see below.)

Every version of this plan rested on one sentence: *"the realistic buyer is the coaching
institute, not the aspirant."* **That buyer may not exist in this vertical.**

Two independent pieces of evidence now agree:

| Evidence | Implication |
|---|---|
| ~4,400 registrations **nationally** (§7b) | Too thin to support a coaching layer — a city has a dozen candidates |
| The one real aspirant we have access to uses **free YouTube + free PDFs** | Revealed willingness to pay ≈ ₹0 |

**This is not a market-size problem. It is a channel problem.** TrigunAI's entire live GTM is
B2B2C: teacher/institute creates a test → shares a link → students take it
(`project-institute-classroom-b2b2c`, `project-direction-acharya-b2b`). **GP Rating has no
teacher in the loop.** The product would have to be sold B2C, direct, to the lowest-income
maritime segment — and the B2C funnel has never converted (`project-pmf-audit-202607`: 0 paid,
watchers ≠ buyers).

The content asset is real. The channel to reach anyone with it is not.

⚠️ **Do not over-read n=1 either.** One student is not a market — concluding "nobody pays" from
one person is the same error as "10,000 students", pointed the other way. But it is *consistent*
with the measured registration count, and two agreeing signals beat one assumption.

### If you want to test it for ₹0 instead of ₹0-and-two-days

The student named his channel: **YouTube.** TrigunAI already runs a daily content engine with
two live channels and a quiz-shorts pipeline (`project-exam-content-engine`,
`trigunai-quiz-video`) that fires at 11am without new code.

**Test: publish GP Rating quiz shorts from the 772 extracted questions. Build nothing.**
If they get traction, the demand is real and *then* the bank is worth building — demand-gated,
in the order this repo keeps getting wrong.

⚠️ Honest caveat: Block 1 marketing is already committed to Acharya exam-prep. A GP Rating
content line **dilutes it**. This is a real cost, not a free option.

---

## 8. Honest read

The generation decision was the right call and it turned out cheap: the two mechanisms that make
it copyright-clean — the `generated=1` serving gate and the 0.82 novelty gate — are already in
the code and already doing this job for JEE/NEET. The only genuinely new code in the entire plan
is a mechanical-reasoning generator and a knowledge-grounding block, one day between them.

It also *reduced* the dependency on the PDF: from 1,450 questions served, to 772 questions used
only as style references behind a gate, with half the exam paper produced by engines that never
opened the file.

**What did not change is the business question.** The asset is real; the buyer is not yet named.
And the honest risk is no longer copyright — it is that a hallucinated answer on a marine-safety
question reaches a student. That is a content-QA problem, and it is why Phase 4 has a human
reading 30 questions in it.

**Verdict, final (2026-08-19): BUILD IT — gated on the 5 students starting trials first (§7d).**

The reasoning below was written when the plan had no distribution channel. §7d closed that:
the direct student funnel is live and 5 people are named. What stands from it is the *method*
warning, not the verdict — so read the rest of this section as the trap to avoid while building,
not as a reason not to.

Watch what happened across this document. Every new fact made the case *weaker* — market 2×
smaller than assumed (§7b), the real paper needs images we don't have (§2b), the section
blueprint is unconfirmed (§2b), and finally no coaching layer exists to sell through (§7c).
**And each time, the response was to refine the plan rather than to question it.** Three
increasingly elaborate versions, all downstream of a premise that has now failed.

That is precisely `feedback-build-trap-loop`: a cheap, satisfying, technically elegant build
that produces a fast win and starves the selling action. The extraction *is* genuinely
excellent — 99.8%, zero LLM cost. **That is what makes it dangerous.** Cheap to build is an
argument for *when*, never for *whether*, and here the answer to *whether* is no.

### What survives

- **The extraction method** — regex-parseable exam PDFs are a repeatable win. Reuse it the next
  time a bank arrives in this shape.
- **§3's finding** — the `generated=1` serving gate makes any exam outside the CBSE/UPSC/BPSC
  allowlist copyright-clean *by default*. That applies to every future vertical.
- **§7b's method** — sponsors publish results PDFs; registration-number ranges give real market
  sizes. Do this **before** planning the next vertical, not after.
- **This file, as a record of the failure mode** — not as a backlog item.

### The actual next action

Not GP Rating. **One Step Patna has been unasked since 12 Aug** — a named institute, a real
teacher in the loop, a live TRE bank of 2,026 questions, and the exact B2B2C motion Acharya is
built for. That is the vow (`SANKALPA.md`), and it is still open.
