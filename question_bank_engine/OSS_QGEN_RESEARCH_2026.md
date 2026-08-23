# Open-source question generation — what actually exists (research, 2026-08-22)

Question asked: *"Is there an open-source LLM or system already in the market that can generate
section-wise questions (Reasoning / Maths / General Science) for Indian competitive exams —
BSSC, BPSC and the rest? What's the best scalable pipeline today?"*

Short answer, up front:

1. **No open-source system generates Indian commission-exam papers.** Nothing exists that does
   blueprint-conformant, bilingual, officially-keyed BSSC/BPSC paper assembly. Don't go looking —
   that gap is the product.
2. **But the per-category generators do exist as open source, and they are NOT LLMs.** The
   RL-training community independently built exactly the architecture this repo already uses
   (compute-the-answer, correct-by-construction) and open-sourced ~170 generators under
   Apache-2.0 / MIT. That is free inventory we should borrow from.
3. **The 2026 consensus is: the LLM never authors the answer.** A solver does. The LLM only
   renders prose, ranks distractors, and judges. Our `qbank/` already works this way — which
   means the strategic finding of this research is *"you are on the right architecture, now
   harvest the OSS generator inventory and adopt their interface."*

---

## 1. What we already have (the baseline this research is measured against)

| Layer | File | Size |
|---|---|---|
| Reasoning builders | `qbank/reasoninggen.py` (+ `reasoning_common`, `reasoning_hi`) | **20 item builders / 16 chapters** (62 top-level defs incl. helpers), 2,704 lines |
| Maths builders | `qbank/quantgen.py` (+ `banking_quant`) | 52 functions, 1,765 lines |
| Static GK / GS | `qbank/staticgkgen.py` + fact tables (`polity_*`, `history_*`, `science_*`, `bihar_tables`) | ~2,000 lines |
| Blueprint | `drop/bssc/SYLLABUS_MAP.json` — syllabus topic → share → generator |
| RAG path | `qbank/generator.py` (JEE/NEET only) |
| Real PYQs | UPSC / BPSC / TRE, `generated=0`, served from `/pool` |

Three production paths, documented in `HOW_GENERATION_WORKS.md`. The govt-job pool is almost
entirely path 1 (compute-the-answer). **This is the same design the papers below converged on.**

---

## 2. The open-source inventory that matters

### 2.1 Reasoning — `reasoning-gym` (Apache-2.0) ★ the big one

[open-thought/reasoning-gym](https://github.com/open-thought/reasoning-gym) — NeurIPS 2025
Datasets & Benchmarks **spotlight**. A Python library of **105 procedural dataset generators**
with algorithmic answer verification, built for RL-with-verifiable-rewards.

```python
import reasoning_gym
data = reasoning_gym.create_dataset('zebra_puzzles', size=10, seed=42, num_people=5)
for x in data:
    print(x['question'], x['answer'])
assert data.score_answer(answer=x['answer'], entry=x) == 1.0
```

Three things in it we should take even if we take nothing else:

- **Parameterized difficulty as a first-class kwarg** (`max_animals=20`, `num_people=5`). Our
  builders mostly hard-code difficulty. Theirs is a dial.
- **A seed.** Same seed → same item. Reproducible papers, diffable regressions.
- **A "cascade scorer"** — progressively lenient string → numeric → symbolic matchers, so a
  correct answer written `1/2` vs `0.5` vs `.5` isn't marked wrong. We hand-roll this per builder.

**Mapping their 105 tasks onto the BSSC/BPSC reasoning syllabus:**

| BSSC reasoning topic | reasoning-gym task | Verdict |
|---|---|---|
| Seating arrangement / puzzle | `zebra_puzzles` | Direct — this IS the seating-arrangement family |
| Blood relations | `family_relationships` | Direct |
| Syllogism | `syllogism` | Direct |
| Number / letter series | `number_sequence`, `letter_jumble` | Direct |
| Calendar | `calendar_arithmetic` | Direct |
| Coding–decoding | `caesar_cipher`, `string_manipulation` | Partial — Indian coding-decoding is its own grammar |
| Arithmetic reasoning | `gsm_symbolic`, `chain_sum`, `simple_equations` | Direct |
| Matrix / figure counting | `rectangle_count`, `manipulate_matrix`, `rotate_matrix` | Partial |
| Direction sense | — | **Ours to build** |
| Clocks | — | **Ours to build** |
| Ranking / order | — | **Ours to build** (trivially, from `number_sorting`) |
| Statement–assumption, course of action, data sufficiency | — | **Ours to build — Indian-exam specific** |

> ⚠️ **SUPERSEDED — this table was name-matching. See `REASONING_GYM_AUDIT.md` (2026-08-22),
> which generated real samples from every candidate.** Actual result: **0 of 106 RG tasks emit MCQ
> options**, `dice`/`caesar_cipher`/`number_sorting` are false friends, and **0 of our 20 builders
> should be deleted.** RG's real value is as a differential-test oracle plus 4 new chapters.

### 2.2 Reasoning — `reasoning-core` (MIT)

[sileod/reasoning-core](https://github.com/sileod/reasoning-core) — 65+ procedural tasks with
**formal verification** (Lean 4 compilation, TPTP/Metamath entailment, first-order logic, NLI,
CSP, planning). Interoperates bidirectionally with reasoning-gym ("mix tasks through either
library's interface"). Overkill for BSSC difficulty, but its **first-order-logic and NLI
generators are the honest way to build syllogism and statement–conclusion items** at controlled
hardness rather than by template.

### 2.3 Reasoning, multilingual — Apple's `ml-multilingual-reasoning-gym`

[apple/ml-multilingual-reasoning-gym](https://github.com/apple/ml-multilingual-reasoning-gym) —
90+ tasks, **perfectly parallel across 10+ languages using identical seeds**, so the same seed
yields structurally identical problems with translated text and identical numeric answers.

That is *exactly* the bilingual-paper problem we solve by hand today. **Caveat: Hindi is not
confirmed in the supported list** (English, French, Spanish, Japanese, Chinese are named). Worth
30 minutes to check — if Hindi is in there, it's a free bilingual reasoning pipeline; if not, its
architecture (localize the *template*, not the *rendered sentence*) is the pattern to copy, which
is what `reasoning_hi.py` already gropes toward.

### 2.4 Maths — symbolic templating, not LLM authoring

The literature has hard-converged here, and it validates `quantgen.py`:

- **GSM-Symbolic** (Apple): convert word problems into **templates with perturbable variables**.
- **MathCAMPS**: encode each maths skill as a **formal grammar**, sample symbolic problems from
  it, then realize them as natural language.
- **[Adaptive Problem Generation via Symbolic Representations](https://arxiv.org/html/2602.19187)**
  (2026): the most directly copyable pipeline —
  1. parse a seed problem into **SymPy**;
  2. have an LLM modify the *symbolic code* (not the prose);
  3. **solve with SymPy or Z3** to get ground truth;
  4. render back to a word problem;
  5. optimize the modification prompt against student performance (TextGrad closed loop).

  Reported: 0.37 average cosine distance between generated variants vs 0.07 for
  natural-language paraphrase — i.e. **symbolic mutation produces genuinely different questions;
  LLM paraphrase produces the same question wearing a hat.** That single number is the argument
  for keeping quantgen symbolic and refusing "just ask GPT for 50 maths questions".

- **[NVIDIA NeMo-Skills](https://github.com/NVIDIA-NeMo/Skills)** + OpenMathInstruct-1/2 (1.8M /
  14M problem–solution pairs, generated with text+code-execution reasoning). Use it for
  **solution traces and step-by-step explanations**, not for question stems.

### 2.5 General Science / GK — `knight-mcq` (KG-driven)

[KNIGHT](https://arxiv.org/html/2602.20135) — the one system in this survey purpose-built for
**factual MCQ generation with controllable difficulty**. Available on PyPI (`knight-mcq`) and
GitHub. Pipeline:

1. build a topic knowledge graph (dense retrieval → entity descriptions → relation triples →
   depth-controlled expansion + pruning);
2. **enumerate multi-hop paths** through the KG; each path is a question;
3. generate stem + key + three semantically-proximate distractors conditioned on the path;
4. validate on five criteria — *fluency, single-key correctness, option uniqueness, answer
   derivability from evidence, topic relevance*.

**Difficulty is graph depth** (`dmax`): longer path = more hops = harder, and human studies
confirmed Level-3 accuracy is consistently below Level-1. That is a real, defensible difficulty
model — better than our current "we label it hard because it feels hard".

Practical read for us: KNIGHT is instantiated on Wikipedia/Wikidata. **Bihar-specific GK is thin
in Wikidata**, so our hand-verified `bihar_tables.py` / `polity_tables.py` stay. But KNIGHT's
*path-enumeration + sibling-entity distractor* mechanism is directly portable onto our own fact
tables, and its 5-criterion validator is a ready-made gate.

Supporting technique worth stealing: **NLI filtering of distractors** (Dutulescu et al., AIED
2024) — run entailment between stem and each distractor and drop options that are actually
entailed (i.e. accidentally correct). Cheap, catches a real class of bug.

### 2.6 Orchestration frameworks (if/when we scale LLM calls)

| Tool | What it is | Fit for us |
|---|---|---|
| **[NeMo Data Designer](https://nvidia-nemo.github.io/DataDesigner/)** | Schema-driven synthetic data: statistical samplers + LLM columns + validation, handles batching/parallelism | Best fit — its "sampler column feeds LLM column" model is literally blueprint → item |
| **distilabel** (Argilla) | Chains LLM generators and judges into typed pipelines | Good for the judge/filter layer |
| **NeMo Curator** | Ray-based curation/dedup at scale | Only if the bank goes to millions |

We do not need any of these today — 145k questions is a laptop-scale problem. Note them for when
the realization layer becomes the bottleneck.

### 2.7 Datasets

**[169Pi/exambench](https://huggingface.co/datasets/169Pi/exambench)** — 405,906 examples,
~600M tokens, Apache-2.0, covering 25+ exams **including SSC CGL/CHSL, IBPS PO/Clerk, SBI, RBI
Grade B, RRB NTPC, UPSC CSE**. Schema: `prompt` / `complex_cot` / `response`.

⚠️ **It is entirely synthetic** (distilled), not real past papers. Which means:
- ✅ Legitimate use: **style exemplars for the RAG path** and a corpus for measuring what SSC-style
  question phrasing looks like.
- ❌ Illegitimate use: serving it. Its keys are model-asserted, not officially verified. Ingesting
  it into the pool would repeat exactly the failure mode this repo has spent months eliminating.

---

## 3. The models (the boring layer)

Open-weight leaders as of Aug 2026 — for the *realization and judging* roles only:

| Role | Model | Note |
|---|---|---|
| Hindi / bilingual rendering | **Sarvam-105B** (also 30B) | Open weights, all 22 scheduled languages, native + romanized + Hinglish; wins ~90% of pairwise comparisons vs GPT-4o/Gemini 3/Llama-70B on Indian-language tasks |
| Cheap Indic fallback | **BharatGen Param2 17B MoE** (IIT-B consortium) | Small, open, HF-released |
| EN→HI translation | **[IndicTrans3-beta](https://huggingface.co/ai4bharat/IndicTrans3-beta)** (AI4Bharat) | Use with a locked exam-terminology glossary; never free-translate a maths stem |
| Maths/reasoning workhorse | **Qwen3.6-27B** dense | Runs on one GPU — fits the existing qbank-worker VM |
| Top-end judge | **Kimi K3** (57 AA Intelligence Index, top open-weight) / **GLM-5.2** (99.2 AIME 2026) / **DeepSeek-V4** | Only where quality justifies cost |

**Important caution from the evaluation literature:** larger, more accurate models have *more
highly correlated errors* than smaller ones, even across different architectures and providers.
So "three models agreed" is much weaker evidence than it feels. **Consensus is a fallback;
symbolic verification is the real gate.** Use consensus only where nothing can be computed —
i.e. General Science facts — and even there prefer a cited source over a vote.

---

## 4. The recommended pipeline (5 layers)

```
  ┌─ 1. BLUEPRINT ────────────────────────────────────────────────┐
  │  SYLLABUS_MAP.json: section → topic → share → difficulty mix  │
  │  (mined from real BSSC/BPSC papers — we already have this)     │
  └───────────────────────────┬───────────────────────────────────┘
                              ▼
  ┌─ 2. ITEM MODEL ───────────────────────────────────────────────┐
  │  A seeded, parameterized symbolic spec — never prose.          │
  │  Maths → SymPy expression   Reasoning → CSP constraint set     │
  │  GS → knowledge-graph path over a VERIFIED fact table          │
  └───────────────────────────┬───────────────────────────────────┘
                              ▼
  ┌─ 3. SOLVER  (the answer is DERIVED, never asserted) ──────────┐
  │  SymPy / Z3 · python-constraint / OR-Tools / pycosat · lookup  │
  │  ★ AND: assert the solution is UNIQUE (count models == 1)      │
  └───────────────────────────┬───────────────────────────────────┘
                              ▼
  ┌─ 4. REALIZATION  (the ONLY place an LLM is allowed) ──────────┐
  │  spec → exam-authentic English + Hindi prose                   │
  │  + distractor plausibility ranking                             │
  │  Deterministic template fallback when the LLM is unavailable   │
  └───────────────────────────┬───────────────────────────────────┘
                              ▼
  ┌─ 5. GATE ─────────────────────────────────────────────────────┐
  │  uniqueness · pgvector novelty/dedup · NLI distractor filter   │
  │  · KNIGHT 5-criterion judge · human spot-check on new builders │
  └───────────────────────────┬───────────────────────────────────┘
                              ▼
  ┌─ 6. TELEMETRY (the moat nobody open-source has) ──────────────┐
  │  live student attempts → per-item p-value + discrimination     │
  │  → recalibrate the difficulty dial in layer 2                  │
  └────────────────────────────────────────────────────────────────┘
```

Layers 1–3 are ~free (CPU, no API cost, unlimited volume). Layer 4 is one batched LLM call per
item. Layer 5 is cheap. **Cost scales with prose, not with question count** — which is why the
symbolic core matters commercially, not just for correctness.

Layer 6 is the part that no open-source project can give us and no competitor has: **real Bihar
students answering these items.** Item response statistics from actual attempts turn "we think
this is hard" into a calibrated difficulty parameter. That is the thing to protect.

---

## 5. Where an LLM genuinely earns its place

Allowed: (1) rendering a solved symbolic spec into bilingual exam prose; (2) ranking/generating
distractors *given* the correct answer; (3) style-matching real commission phrasing;
(4) extracting questions from official PDFs (already done — Qwen2.5-VL, `qwen_extract_bpsc.py`);
(5) judging and filtering.

Forbidden: authoring the answer key. Every category of failure this bank has hit traces back to
a model asserting a key nobody derived.

---

## 6. Concrete next steps, cheapest first

1. **`pip install reasoning-gym reasoning-core`, run a 1-hour audit.** Score each of our 62
   reasoning builders against their 105 tasks: which are duplicated (delete ours), which of
   theirs fill a BSSC gap (adopt), which BSSC families neither has (build). Expected outcome:
   we keep the Indian-specific 6, adopt ~5, and inherit difficulty dials for the rest.
2. ~~**Add a uniqueness verifier to every puzzle-type builder.**~~ **Already done** — `_b_seating`
   enforces `len(_seat_solutions(...)) == 1` and trims implied clues; `_syl_sat` does the same for
   syllogism. Corrected by the audit.
3. **Refactor our builders onto the reasoning-gym interface** —
   `create_dataset(name, size, seed, **cfg)` + `score_answer(answer, entry)`. One weekend of
   mechanical work that buys: reproducible papers, regression tests, difficulty as a parameter,
   and the option to RL-train on our own bank later.
4. **Port KNIGHT's path-enumeration + 5-criterion validator onto our fact tables** for General
   Science / Polity. Keep the tables (Bihar GK isn't in Wikidata); take the mechanism.
5. **Add NLI distractor filtering** to `item_forms.py` — cheap, catches accidentally-correct
   options.
6. **Pull exambench as style exemplars only**, into the RAG exemplar store, tagged
   `source=synthetic, servable=0`. Never into `/pool`.
7. **Evaluate Sarvam-105B vs current Azure path** for Hindi rendering on 100 items, blind-scored
   by a Patna teacher. If Sarvam wins, the Hindi half of the bank gets cheaper and better.

---

## Sources

- [open-thought/reasoning-gym](https://github.com/open-thought/reasoning-gym) · [paper](https://openreview.net/forum?id=GqYSunGmp7) · [PyPI](https://pypi.org/project/reasoning-gym/)
- [sileod/reasoning-core](https://github.com/sileod/reasoning-core) · [paper](https://arxiv.org/html/2603.02208v1)
- [apple/ml-multilingual-reasoning-gym](https://github.com/apple/ml-multilingual-reasoning-gym)
- [KNIGHT: KG-driven MCQ generation](https://arxiv.org/html/2602.20135)
- [Adaptive Problem Generation via Symbolic Representations](https://arxiv.org/html/2602.19187)
- [NVIDIA NeMo-Skills](https://github.com/NVIDIA-NeMo/Skills) · [OpenMathInstruct-1](https://arxiv.org/pdf/2402.10176) · [NeMo Data Designer](https://nvidia-nemo.github.io/DataDesigner/latest/) · [NeMo Curator](https://github.com/NVIDIA-NeMo/Curator)
- [Distractor Generation survey](https://arxiv.org/pdf/2402.01512) · [DG_Survey repo](https://github.com/Distractor-Generation/DG_Survey) · [NLI-filtered DG toolkit](https://link.springer.com/chapter/10.1007/978-3-031-64299-9_18)
- [LLM-based Automated Item Generation in STEM: scoping review](https://aquila.usm.edu/jetde/vol19/iss2/7/) · [AI-assisted exam variant generation (HITL)](https://doi.org/10.3390/educsci15081029) · [Automated item evaluation via LLM critiques](https://arxiv.org/html/2608.06609)
- [169Pi/exambench](https://huggingface.co/datasets/169Pi/exambench)
- [Sarvam-105B](https://www.buildfastwithai.com/blogs/sarvam-105b-india-s-open-source-llm-for-22-indian-languages-2026) · [AI4Bharat IndicTrans3-beta](https://huggingface.co/ai4bharat/IndicTrans3-beta) · [AI4Bharat](https://github.com/AI4Bharat)
- [Best open-weight LLMs 2026](https://wavect.io/blog/open-weight-llm-comparison-2026/) · [Cross-model consensus is weaker than it looks](https://www.digitalapplied.com/blog/cross-model-review-consensus-verification-2026)
- [tuchandra/zebra (puzzle generator + SAT solver)](https://github.com/tuchandra/zebra) · [quint-t/Puzzle-Generator-and-Solver](https://github.com/quint-t/Puzzle-Generator-and-Solver)
