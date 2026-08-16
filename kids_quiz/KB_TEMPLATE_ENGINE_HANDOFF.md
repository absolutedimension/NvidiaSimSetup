# KB + Templates Worksheet Engine — HANDOFF

> Self-contained brief for the session building the new knowledge/maths generator. Read this top-to-bottom.
> Control tower for the whole kids product = skill **`trigunai-kids-education`** + memory
> **[[project-kids-worksheet-allsubjects]]**. This doc is ONLY the engine-rebuild.

---

## 0. STATUS — BUILT & LIVE (2026-08-03, `lms-kids:v50`)
The engine is built and serving. **ALL grades 1–5 × ALL subjects are on the clean engine (CBSE+ICSE):** GK/EVS/English/Hindi =
KB+templates (20 KBs in `kb/`), Maths = computed. Grades 1/2/4/5 knowledge KBs were authored via the `author-grade-kbs`
multi-agent workflow (32 agents, grade-distinct + verified), then materialized + deterministically validated + deployed.
`_validate` now also checks template placeholders, pair shape, and cloze `___`. Remaining: Bihar grades 1/2/4/5 (deprioritized),
maths pictograph renderer, per-chapter depth.
- **Engine:** `kids_quiz/kb_engine.py` — `generate(kb, n, seed)` + CLI. `_validate()` guard fails loud on any KB shape that
  could emit a wrong question; computes articles via `{art}`; grouping FALSE-explain shows the corrected true statement;
  **language-aware via `_S(kb,key,default,**fmt)` + an optional `kb['strings']` block** (Hindi supplies Devanagari
  instructions/explanations — see `kb/hindi_class3.json`; English KBs use the defaults).
- **KBs authored (verified):** `gk_class3.json`, `evs_class3.json` (+10 OpenBookQA-mined facts), `english_class3.json`,
  `hindi_class3.json` (pure Devanagari, 0 Latin leaks by construction).
- **Banks generated + deployed:** `content/bank/{cbse,icse}_class3_{gk,evs}.json` (1000 each), copied into
  `lms/app/kidsengine/content/bank/`. Old LLM banks backed up to `*.llm.bak`.
- **Proof met:** 1000 distinct · degenerate=0 · article-glitches=0 · 0 factual errors (hand-checked) · instant · no LLM.
- **Implementation vs the §6 proposal:** the actual KB schema is `categories` / `groupings` / `relations` (a→b `pairs`) /
  `facts` (NOT the "entity table" shape §6 sketched — same idea, simpler to author + validate). Serving reuses the existing
  **pre-pooled bank path** (`serve()` already prefers the bank for knowledge subjects) — so **no `serve()` code change was
  needed**; we just replaced the bank files. RAG-over-textbook (§7b) was NOT used — facts were hand-authored + verified; add
  RAG grounding later if a subject's facts get large/contested.
- **NEXT (agreed priority):** English G3 → Hindi G3 (Devanagari KB) → class-scale KBs to grades 1/2/4/5. Recipe below (§8) +
  the concise version in the skill's NEXT TASKS. The MATHS gap (§4) is still open and independent of this.

---

## 1. The goal
A worksheet generator that produces **UNLIMITED × CLEAN (factually correct) × STANDARD (curriculum-aligned)**
questions for kids — **Class 1–5, boards ICSE/CBSE/Bihar, 5 subjects (Maths, EVS, English, GK, Hindi)** — for both
**on-screen (interactive)** and **print**. This REPLACES the current LLM-pool approach for knowledge and FILLS the
maths coverage gap. Serving live children, so correctness is non-negotiable.

## 2. The core thesis — SEPARATE FACTS FROM FORM
The bottleneck is **fact correctness, not volume**. Maths already makes infinite *correct* questions with **no LLM**
because facts are **computed, not guessed** (`234+158` is always `392`). Do the same for everything:
- **FACTS** = a small, **verified** Knowledge Base per curriculum subtopic (cow→shed, lotus=national flower, big↔small,
  triangle→3 sides…).
- **FORM** = question **templates** (odd-one-out / match / true-false / cloze / sort / and maths archetypes) that COMBINE
  facts into questions.
- Verify the FACTS **once** → every templated question is **correct by construction**. Distractors (wrong options) are
  **other real KB values**, never invented. Unlimited combinations, ~free, ~100% clean.

**Who builds the KB:** the Claude/Opus session authors the verified KB **directly as data files** (grounded in each
curriculum subtopic), verifies it (optionally cross-check), commits it. **No LLM calls at question-generation time.**
Use Opus for the ONE-TIME work: build the KB + author templates + the few creative types (comprehension/word-problems).

## 3. Why we pivoted (findings from the LLM-pool attempt — do not repeat these)
- **gpt-4o-mini pool** (the current live `content/bank/*.json`, 1000/cell Grade-3 knowledge): **~10% factual/degenerate
  errors** (e.g. `Cat → "Air Animals"`, empty `"True or False?"`, `fruits good for → eyes`).
- **LLM auto-critic is a DEAD END** — `quality_critic.llm_verdicts()` has **~50% false positives, CONSISTENT even on
  2 votes** (gpt-4o keeps flagging CORRECT items: `"national flower is Rose → False"`, `"bones help us move → True"`).
  Do NOT hard-drop on it.
- **gpt-4o GENERATION** is much cleaner (sampled 10/10 correct) — but per-question LLM is still costly + not truly
  unlimited, and still not verifiable at scale. Not the answer.
- **Only the DETERMINISTIC critic** (`quality_critic.degenerate()`) is reliable → keep it for well-formedness checks.
**Conclusion:** KB+templates is the durable engine. Keep the current 1000-item pools LIVE as a stopgap; replace per-subject as the KB engine is proven.

## 4. The MATHS coverage gap — ✅ FIXED (v46, 2026-08-03)
**Done.** `worksheet_engine.py` now has computed generators `g_division` / `g_shape` / `g_fraction` / `g_measure` (chapter-aware)
/ `g_data`, a `DIRECT_MATHS` map that bypasses the style layer, and `chapter_concepts()` routes the new strands FIRST (matching
ICSE clean names + CBSE playful NCERT titles). 0 logic errors over 3000+ items; all reuse existing renderers. **Only remainder:**
a real data-handling **pictograph/bar-graph renderer** (currently `g_data` = a contextual count word-problem stopgap). Original diagnosis kept below.

"Maths is computed/perfect" is TRUE **only for the number/arithmetic strand**. `worksheet_engine.py` has generators for:
`count, add, sub, mul, compare, neighbour(before/after), sequence, money, word-problem, error-spot` — **and NO division
generator** (divi maps to mul). `chapter_concepts()` keyword-maps a chapter → concept and **falls back to
`["add","number"]` for anything unmatched**. So picking **Shapes & Geometry / Fractions / Measurement / Division / Data**
silently generates NUMBER questions under that label (user hit this: a "Shapes & Geometry" sheet returned place-value/addition).
**These are all perfectly COMPUTABLE templates (no LLM):** shapes (name/sides/corners/2D-3D/faces), fractions (colour-½,
of-a-shape, compare), measurement (longer/heavier/time), division, data (read a picture-graph). Add them as maths generators.

## 5. THE OUTPUT CONTRACT — every generated item MUST match this schema
The KB engine plugs into the existing renderers/serving unchanged, so items MUST look exactly like today's
(`worksheet_engine._item()` output):
```json
{ "type": "odd_one_out", "subject": "gk", "class": 3, "chapter": "Animals", "band": "3-5",
  "instruction": "इनमें से कौन सा अलग है?", "voice": "…", "payload": { … per type … },
  "answer": <type-specific>, "explain": "…" }
```
**Renderable types + payload/answer shapes** (see `WORKSHEET_GRAMMAR.md`; renderers in
`lms/app/static/kids/worksheet.js` + `worksheet_print.js`):
- `odd_one_out`  payload `{options:[a,b,c,d]}`  answer=the-odd-one (must be in options)
- `match_following` payload `{pairs:[[L,R],…]}`  answer=null (pairs ARE the key)
- `true_false`  payload `{statement:"…"}`  answer=bool
- `cloze`  payload `{sentence:"… ___ …", bank:[…]}`  answer=the-correct-bank-word
- `sort_groups`  payload `{items:[…], bins:[…]}`  answer={item:bin,…} (map EVERY item)
- Maths (computed): `count_write`, `arith`, `fill_sequence`, `compare_symbol`, `neighbour_number`, `count_money`,
  `pattern_next`, `true_false`, `match_following`, `sort_groups`, `odd_one_out`. **Add: shape/fraction/measurement/division/data.**
Every item is then enriched by `assessment_core.enrich()` (adds `difficulty`, hints) — the KB engine does NOT need to;
`serve()`/`generate()` already enrich. Entity-art auto-attaches if an option word matches an asset (assets.js `wordIndex`).

## 6. KB structure (proposed — per curriculum subtopic)
Store a KB as JSON keyed by curriculum subtopic. Two shapes cover most:
- **Entity table** (attributes per entity) — powers match / true-false / sort / cloze / odd-one-out:
  ```json
  {"animals":{
     "cow":  {"home":"shed","sound":"moo","young":"calf","legs":4,"group":"mammal","habitat":"land","domestic":true},
     "sparrow":{"home":"nest","sound":"chirp","young":"chick","legs":2,"group":"bird","habitat":"air","domestic":false}}}
  ```
- **Pair/relation lists** — powers match / cloze / odd-one-out:
  ```json
  {"opposites":[["big","small"],["hot","cold"]], "national_symbols":{"flower":"lotus","bird":"peacock"}}
  ```
- **Maths shapes KB:** `{"triangle":{"sides":3,"corners":3,"dim":"2D"},"cube":{"faces":6,"corners":8,"dim":"3D"}}`.
Grounding: build one KB per curriculum subtopic in `kids_quiz/curriculum/*` (each cell has `chapters[].subtopics`).
Language: build a HINDI KB for the Hindi subject (Devanagari values), and English-medium KBs for EVS/English/GK/Maths.

## 7. Templates (FORM) — turn KB → items, correct by construction
- **odd_one_out:** pick N entities sharing an attribute value + 1 with a different value → the different one is the answer.
- **match_following:** pick K (entity, attribute-value) pairs (e.g. animal→home).
- **true_false:** state a real KB fact (answer True) OR swap in a WRONG-but-real value (answer False).
- **cloze:** sentence template with a blank filled by a KB value; bank = correct + 2 other real KB values.
- **sort_groups:** pick items spanning ≥2 groups by an attribute (e.g. habitat land/water/air).
- **maths shapes:** "How many sides does a {shape}? → sides"; match shape→sides; sort 2D/3D; odd-one-out by dim.
Distractors ALWAYS come from the KB (real values), so nothing is invented. Randomise selection for unlimited variety;
dedup by a signature (reuse `fill_knowledge_pool.sig`). Optionally still pool to `content/bank/` OR generate live in `serve()`.

## 7b. RAG + embeddings — WHERE they fit (optional, but recommended for AUTHORITATIVE facts)
**Current kids pipeline uses NO embeddings and NO RAG** — it's Python (computed maths + SQL/JSON serving + BKT/Elo) +
direct-LLM prompting (the chapter/subtopics are pasted into the prompt string; `gen_qbank_g3.py`: *"no embeddings needed
to serve"*). The **senior** Acharya side DOES use RAG (`lms/app/examgen.py` = client for the `/examgen` RAG generator over
real past-paper exemplars) — but kids deliberately uses the simpler path. Reference infra that already exists in the
company: the `/examgen` RAG service, and **pgvector** (used by the Swakritii PMC VM — see [[project-swakritii-pmc-vm]]).

**The KB engine itself does NOT need embeddings** — the KB is small, structured, keyed by subtopic → direct lookup;
templates consume it by key. Correctness comes from the KB being verified, not from retrieval. BUT embeddings/RAG add
real value in 3 specific spots:

1. **⭐ RAG-over-textbook to GROUND & VERIFY the KB (the best use — do this).** Don't let Opus recall facts from memory
   (risk: a wrong "national flower"). Instead ingest the **real curriculum source** (NCERT "Looking Around" EVS, the
   board textbooks — the curriculum cells already cite sources+URLs, e.g. `cbse_class3_evs.json.source`), chunk +
   embed them, and per subtopic **retrieve the authoritative passage → Opus builds the KB FROM that passage.** This makes
   the facts genuinely *standard* and *verifiable* (KB entry can even store a `source` snippet). RAG grounds the FACTS;
   templates guarantee the CORRECTNESS. This is a ONE-TIME build step, not per-question.
2. **Semantic dedup.** Exact-signature dedup (`fill_knowledge_pool.sig`) misses near-duplicates ("A cow says moo" vs
   "The sound a cow makes is moo"). Embed each generated question and drop items with cosine-sim > ~0.9 to an existing
   one → truly non-repeating. (Only needed if templates over a small KB start colliding; large KBs + randomisation
   mostly avoid it.)
3. **Creative / comprehension types.** For reading-comprehension or word-problem-in-context items (which templates can't
   author), RAG a real passage and generate questions grounded in it.

**Practical:** embeddings via the litellm proxy if it exposes an embed model, else a local `sentence-transformers`
(e.g. `all-MiniLM-L6-v2`) — no GPU needed for a few thousand facts/questions. Store in a plain FAISS/Chroma index or
pgvector (reuse the pattern from the senior side). Keep it OFFLINE (build-time), never in the question-serving path.
**Net recommended architecture:** *RAG-over-textbook → Opus authors verified KB → templates emit unlimited correct
questions → optional embedding dedup.* Facts are retrieved+verified once; form is deterministic.

## 8. First concrete steps (prove it on ONE cell before scaling)
1. Pick **EVS or GK, Grade 3, CBSE** (rich, English). Read its curriculum cell `kids_quiz/curriculum/cbse_class3_{evs|gk}.json` (chapters + subtopics).
2. **Author the verified KB** for ~5–10 of its subtopics (you = Opus, write the JSON, double-check every fact).
3. Write a small **`kb_engine.py`** with the ~6 template functions (§7) that read the KB and emit items in the §5 schema.
4. Generate 20–30, **eyeball for 100% correctness + variety**, and confirm they render (drop into `print.html` via
   `localStorage.kidsPrintSheet`, or the worksheet page).
5. **Wire into serving:** in `worksheet_engine.generate()` (or a branch in `lms/app/kids_worksheet.py serve()`), route the
   KB-covered subject/subtopic to `kb_engine` instead of `llm_knowledge`. Keep the pool as fallback for uncovered cells.
6. **Re-copy** `kids_quiz/` engine files into `lms/app/kidsengine/`, deploy `lms-kids:vNEXT` (recipe in the skill).
7. Scale: add KBs subtopic-by-subtopic, add the missing MATHS templates (§4). Boards differ → separate KBs per board where the curriculum differs.

## 9. Key files / reuse
| Path | What |
|---|---|
| `kids_quiz/worksheet_engine.py` | **THE reference** — the COMPUTED Maths path = the template pattern to copy; `_item()` = the schema; `chapter_concepts()` = where the maths gap lives; `llm_knowledge()` = the OLD approach (being replaced) |
| `kids_quiz/curriculum/` | 75 cells (3 boards × 5 classes × 5 subjects), each with `chapters[].subtopics` — the coverage skeleton to ground KBs |
| `kids_quiz/quality_critic.py` | `degenerate()` = reliable well-formedness check (KEEP); `llm_verdicts()` = unreliable (DON'T use to drop) |
| `kids_quiz/fill_knowledge_pool.py` | current LLM-pool driver (stopgap); has `sig()` dedup + `BROAD` topics — reuse the dedup |
| `lms/app/kids_worksheet.py` | serving brain — `serve()` calls `WE.generate(board,cls,subject,chapter,n)`; the KB engine plugs in here; also `_bank_items()` (pool fallback) |
| `lms/app/kidsengine/` | the APP COPY of the engine + banks — **RE-COPY from `kids_quiz/` after any change** (source of truth = `kids_quiz/`) |
| `lms/app/kidsengine/content/bank/` | current 1000-item LLM pools (Grade 3) — LIVE stopgap, keep serving until KB replaces per-cell |
| `lms/app/static/kids/{worksheet.js,worksheet_print.js}` | the renderers — item schema (§5) MUST match these; entity-art via `assets.js wordIndex` |
| docs | `WORKSHEET_GRAMMAR.md` (archetypes), `ASSESSMENT_ENGINE.md`, `ASSESSMENT_STYLE_SYSTEM.md` |

## 10. Guardrails / gotchas
- **Item schema is the contract** (§5) — match it exactly or renderers/serve/enrich/art break.
- **Source of truth = `kids_quiz/`**; re-copy into `lms/app/kidsengine/` before deploy.
- **Hindi = pure Devanagari** in KB values (the pool needed a purity gate; a Hindi KB avoids the problem at source).
- **Deterministic critic yes, LLM auto-critic no** (§3).
- **Don't disrupt live** — kids app is an isolated Azure Container App (`kids`), currently `lms-kids:v44`; deploy rollback-safe.
- Boards genuinely differ (CBSE vs ICSE curricula differ) — don't share a KB blindly across boards where the syllabus differs.
- **Everything v33→v44 is UNCOMMITTED to git** (only v26→v37 committed at `c11e8c7`) — commit early.

## 11. Definition of done (per subject)
For a subject/grade/board cell: a verified KB covering its curriculum subtopics + templates that emit the 5 archetypes,
producing **unlimited, deduped, 100%-correct** items in the §5 schema, wired into `serve()`, rendering on screen + print,
Hindi where relevant, replacing that cell's LLM pool. Then move to the next cell.
