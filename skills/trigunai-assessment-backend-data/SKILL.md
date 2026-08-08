---
name: trigunai-assessment-backend-data
description: >
  Control tower + operator guide for the TrigunAI Question Bank Engine — the backend
  DATA layer behind Acharya's exam/test-paper generation. It turns raw exam sources
  (HuggingFace datasets + dropped PDFs) into a CLEAN, TAGGED, SOLVED, VERIFIED question
  bank, then generates NEW copyright-clean test papers from it via RAG. Load this skill
  for ANY work on: building/expanding the question bank, adding a NEW subject or exam
  (JEE Main/Chemistry/Maths/NEET/boards), ingesting exam data, tagging/solving/verifying
  questions, generating test papers or practice questions, the live generation API
  (rtx.trigunai.com/examgen), or resuming this project in a fresh session. Triggers on:
  "question bank", "assessment data", "test paper generation", "generate questions",
  "add a subject / exam to the bank", "ingest JEE/NEET data", "solve the questions",
  "tag questions", "exam generator API", "qbank", "trigunai-assessment", or continuing
  the JEE-Advanced-Physics work. Companion to [[project-acharya-assessment-system]] and
  [[project-acharya-student-product]] (the student funnel this feeds) and
  maintain-trigunai-system (owns the live LMS/Acharya stack).
---

# TrigunAI Assessment Backend Data — Question Bank Engine

The DATA + GENERATION brain for exam/test-paper generation. Strategy is settled: **RAG
over a tagged/solved question bank on a strong model — NOT fine-tuning** (see §9). The
bank is the moat; the model is rented.

Full pipeline:
```
collect → extract → keymatch → clean → validate → store → TAG → SOLVE+VERIFY → GENERATE
```

---

## 1. Where everything lives

| Item | Value |
|---|---|
| **Code (local)** | `NvidiaSimSetup/question_bank_engine/` |
| **Code (EC2, live)** | `/home/ubuntu/question_bank_engine/` |
| **DB (demo/live)** | `data/qbank.sqlite` (SQLite) — STILL the live store the API reads. |
| **Postgres+pgvector (NEW 2026-07-24, Gurukul)** | Native (apt, NOT Docker — box has no Docker) PostgreSQL 16.14 + `postgresql-16-pgvector` (pgvector 0.6.0). systemd `postgresql`, **127.0.0.1:5432 only** (not public), tuned small (shared_buffers 192MB, max_connections 50) for the 3.8G box. Role/db `qbank`, extension `vector` enabled. Creds in `~/question_bank_engine/pg.env` (chmod 600, `DATABASE_URL=postgresql://qbank:…@127.0.0.1:5432/qbank`). **MIGRATED + EMBEDDED (2026-07-24), but retrieve/novelty NOT yet rewired** — all 57,607 SQLite rows copied to PG (`diagram_generate/pg_migrate.py`), and the **46,396 verified rows embedded** with a LOCAL ONNX model **`BAAI/bge-small-en-v1.5` (384-dim, fastembed — NOT text-embedding-3-small; no Azure embeddings deployment exists)** + **HNSW cosine index `q_emb_hnsw`** (`diagram_generate/pg_embed.py`; ~60min on the box w/ swap). Semantic NN verified working. **SQLite is STILL the live store** — `storage.retrieve`/`generator.novelty` still use tag-SQL + TF-IDF; the pgvector rewire is the NEXT step (make generation actually use semantic retrieval + semantic novelty). Box needed a 2G swapfile (was 0) — kept. Prod target later = Azure DB for PostgreSQL Flexible Server (centralindia, DPDP) — same code, swap connstring. |
| **Figures** | `figures/<id>.png`, served at `/examgen/figures/<id>.png` |
| **Batch-worker VM (NEW 2026-07-25)** | **`qbank-worker`** — Azure E4as_v5 (4 vCPU / **31 GB** / 122 GB disk), **centralindia**, `ssh -i ~/.ssh/qbank_worker_key azureuser@40.80.84.87`, RG `trigunai-video-creator`. The HEAVY box: runs `batch-generate` pool fills + pgvector embeddings OFF the tiny 3.8 GB Gurukul box. Has its own PG16+pgvector, venv (prod-pinned), `litellm.service` (gpt-5.6-terra/sol, auto-starts on boot), DB replica. **DEALLOCATE when idle** (~$0.25/hr running). Managed identity can self-stop. Full detail = [[project-qbank-worker-vm]]. **Two-VM split: Gurukul = always-on light serving; qbank-worker = on-demand batch.** |
| **EC2 host** | `34.192.145.204` (STABLE Elastic IP), instance `i-047ebf759f2386e71`, us-east-1 |
| **SSH** | `ssh -i ~/.ssh/trigunai_key.pem ubuntu@34.192.145.204` |
| **LLM** | LiteLLM proxy on `localhost:4000` → Azure `gpt-4o` / `gpt-4o-mini`. Master key `sk-trigunai-master-key-2026` |
| **Generation API (PRIMARY, always-on)** | **Gurukul VM** `20.219.2.53` (`ssh -i ~/.ssh/gurukul_key dk_trigun@…`). systemd `qbank-api` (venv uvicorn `127.0.0.1:8020`) + `litellm-proxy` (venv, `127.0.0.1:4000`→Azure gpt-4o-mini). Public `https://gurukul.trigunai.com/examgen` (Caddy `handle_path /examgen/*`). Code at `/home/dk_trigun/question_bank_engine/` (venv `.venv/`). **Migrated off the EC2 GPU box 2026-07-23** so examgen survives EC2 stop. |
| **Generation API (FALLBACK)** | **EC2** `34.192.145.204`: systemd `qbank-api` `127.0.0.1:8020`, public `https://rtx.trigunai.com/examgen` — still runs but needs the GPU box ON. Not the LMS target anymore. |
| **LMS wiring** | `lms` container-app env `EXAMGEN_URL=https://gurukul.trigunai.com/examgen` + secret `examgen-key` (= `QBANK_API_KEY`). LMS module `lms/app/examgen.py` calls `{EXAMGEN_URL}/chapters` + `/generate`. Flip URL via `az containerapp update -n lms -g trigunai-video-creator --set-env-vars EXAMGEN_URL=…` (config-only). |
| **API key** | in `/home/ubuntu/question_bank_engine/api.env` → `QBANK_API_KEY` (Bearer; protects Azure spend) |

**LLM env (export before any LLM command):**
```bash
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 \
       QBANK_CHAT_MODEL=gpt-4o QBANK_VISION_MODEL=gpt-4o
```
Without these (or with `QBANK_LLM=off`) the engine runs offline with rule-based fallbacks
(keyword tagging, no solving/generation). The LiteLLM proxy runs on the EC2 box only, so
LLM commands must run ON the box (or SSH-tunnel `-L 4000:localhost:4000`).

---

## 2. Module map (`qbank/`)

| File | Role |
|---|---|
| `config.py` | All env-driven config (LLM endpoint, DB path, FIG_DIR, PUBLIC_BASE) |
| `models.py` | `Question` dataclass; `content_hash`, `normalize_for_hash`, `repair_latex`, `references_figure` |
| `llm.py` | OpenAI-compatible client → LiteLLM proxy; `chat_json`, `vision_json`; graceful degrade |
| `storage.py` | SQLite store; `upsert/retrieve/iter_real/set_solution/update_tags/…` (pgvector = prod) |
| `collector.py` | Sourcing: `fetch_open_dataset` (HF text), `fetch_image_dataset` (HF images), `scan_drop_folder` (PDFs) |
| `extractor.py` | Raw→Question: `from_dataset_row` (text), `from_image_row` (vision), `from_pdf` (vision) |
| `keymatch.py` | Attach official answer keys from a separate key PDF (PDF path only) |
| `cleaner.py` | Normalize LaTeX; dedup (hash + TF-IDF) |
| `validator.py` | Quality gate: rule checks + optional LLM well-formedness check |
| `tagger.py` | Assign chapter/concept/difficulty/bloom (LLM-first, keyword fallback) |
| `solver.py` | Solve + validate answers: `solve`, `solve_consistent` (self-consistency), `explain`, `answers_match`, `canon` |
| `generator.py` | RAG generation loop: retrieve exemplars → author NEW question (±SVG figure) → validate → novelty gate |
| `syllabus.py` | **Knowledge-graph taxonomy** (JEE Physics chapters+concepts+keywords). `TAXONOMIES` registry — extend per subject |
| `pipeline.py` | Orchestrators: `ingest_open_dataset`, `ingest_image_dataset`, `enrich_solutions`, `retag`, `reverify`, `mark_needs_figure`, `backfill_image_figures` |
| `run.py` | CLI (see §3) |
| `api.py` | FastAPI service (see §5) |
| `apply_solutions.py` | Apply Claude-authored solutions; compares to official key (range-aware); flags `solved_by_claude` / `answer_disputed_claude` |

---

## 3. CLI reference (`python3 run.py <cmd>`)

```bash
# INGEST
run.py ingest-dataset --dataset daman1209arora/jeebench --subject phy --subject-name Physics --exam "JEE Advanced" --limit 120
run.py ingest-images  --dataset Reja1/jee-neet-benchmark --exam-prefix JEE --subject Physics   # vision (needs LLM)
run.py ingest-images  --dataset Reja1/jee-neet-benchmark --exam-prefix NEET --exam "NEET" --subject Biology   # NEET path (next exam to build)
run.py ingest-grafite --subject physics --subject-name Physics --exam "JEE Main"              # grafite bank: pre-tagged + pre-solved TEXT, no LLM. --subject chemistry|maths for the others
run.py ingest-datavorous --exam NEET [--subjects Biology,Physics]                             # datavorous bank: pre-tagged+keyed+solved HTML, no LLM. --exam "JEE Main"|"JEE Advanced" also available (~35k JEE Main un-ingested)
run.py ingest-neet-bio                                                                        # sweatSmile NEET-Biology text (choices[]+letter/index answer), no LLM
run.py ingest-drop    --exam "JEE Main" --subject Physics --year 2024 --key key.pdf            # PDFs in drop/ (needs LLM)

# TAG
run.py tag                      # tag untagged (keyword if QBANK_LLM=off, LLM if on)
run.py retag --chapter X        # re-tag ALL (LLM) — accurate concept + calibrated difficulty

# SOLVE / VERIFY (needs LLM)
run.py enrich-solutions --chapter X   # solve independently; agree→verified, else explain-toward-key + flag needs_review
run.py reverify --chapter X --k 5     # self-consistency majority vote on needs_review → promote if matches key

# FIGURES
run.py mark-figures             # flag needs_figure across bank (text-based)
run.py backfill-figures         # re-download + attach original figure PNGs for image questions

# INSPECT / RETRIEVE
run.py stats
run.py sample -n 3
run.py query --chapter "Modern Physics" --difficulty 3-4 --type MCQ_single -n 10   # generator's read path

# GENERATE (needs LLM)
run.py generate --chapter "Modern Physics" --difficulty 3-4 --type MCQ_single -n 5 --out tests_out/mp.json
run.py generate --chapter "Ray Optics" --require-figure ... # (via API flag) forces an SVG diagram

# BATCH PRE-GENERATION → shared pool (needs LLM; see §5.5) — fills the pool the frontend serves instantly
run.py batch-generate --exam "JEE Advanced" --subject Chemistry --per-cell 15 --difficulties "2-3,3-4" --types MCQ_single
run.py batch-generate --subject Physics --chapter "Modern Physics" --per-cell 20   # limit to one chapter
run.py pool-stats --exam "JEE Advanced" --subject Chemistry                        # pool depth per chapter
```

---

## 4. Data sources (checked, HuggingFace)

| Dataset | Coverage | Format | Notes |
|---|---|---|---|
| **daman1209arora/jeebench** | JEE Advanced 2016–2023, Phy/Chem/Math | TEXT (options inline) | `--subject phy/chem/math`. Benchmark SUBSET, not full papers |
| **Reja1/jee-neet-benchmark** ⭐ | JEE Adv + NEET **2024/2025/2026**, Phy/Chem/Math/Bio | IMAGES + answer keys in metadata | THE latest-years source; needs vision ingest. 860 rows total, of which **560 are NEET** (Bio 280 incl. Botany+Zoology, Phy 140, Chem 140). ⚠️ NEET keys are option INDEXES — see the letterize gotcha in §10 |
| **sweatSmile/neet-biology-qa** ⭐ | NEET Biology, 793 rows | TEXT `{question, subject, choices[], answer}` | The Biology text bank — `run.py ingest-neet-bio`. NCERT-style recall Qs (not verbatim past papers); 25/25 keys hand-audited correct. 169 of the 793 are internal duplicates |
| ~~roshansk23/NEET_2021~~, ~~dalmeow/NEET_2020~~ | NEET 2020/21 | TEXT | **UNUSABLE — checked 2026-07-23**: ZERO English rows (12 regional languages only) and `category_en` is per-PAPER not per-question, so rows labelled "biology" are physics questions |
| ~~devNaam/examguru-neet-jee-dataset~~ | medmcqa (medical PG) | — | AVOID — PG medicine, not NEET-UG syllabus |
| **ruh-ai/grafite-jee-mains-qna-no-img** ⭐⭐ | **JEE Main** AIEEE→2024, Phy(3522)/Chem(3372)/Maths(4498) | TEXT: stem+options+**answer**+**chapter/topic**+**solution/explanation** | BEST JEE-Main source — PRE-TAGGED + PRE-SOLVED, no LLM/vision needed. `ingest-grafite`. HTML sub/sup + `<img>` in some solutions (adapter strips them). `correct_option` is a JSON-string. Physics DONE (see §10). |
| **datavorous/entrance-exam-dataset** ⭐⭐⭐ | **97k rows: NEET ~49.7k + JEE Main ~35k + JEE Advanced ~1k**, all subjects incl. Biology | TEXT/HTML: `tags`="[Subject,Chapter,Exam]", `options` HTML w/ `<li class="correct">`, `correct_option` value, `answer`=worked solution | THE big multi-exam bank — pre-tagged + pre-keyed + pre-solved, no LLM. `ingest-datavorous --exam <NEET\|JEE Main\|JEE Advanced>`. Key marked TWO ways (li.correct + value text) → adapter cross-checks + drops disagreements (0/49,771 for NEET). **NEET DONE; ~35k JEE Main NOT yet ingested** (JEE Main already has 11k from grafite — optional top-up). |
| ~~BruthaCool/neetjee~~ | NEET 122k rows | TEXT (no key) | **AVOID — checked 2026-07-23**: 122k rows but NO answer keys (2/500 sampled had any answer marker) + OCR noise + non-MCQ rows |
| ~~catchshubham/neet-dataset~~ | NEET 5.6k, chat format | messages+metadata | **AVOID**: corrupted — mojibake, mangled options, keys CONTRADICT their own explanations ("Correct is (A)" while explanation says (C)) |
| PhysicsWallahAI/JEE-Main-2025-Math | JEE Main 2025 | TEXT | **Math only** (no physics) |
| CK0607/2025-Jee-Mains-Question | JEE Main 2025 | TEXT | **Math only** (misnamed) |
| Kaggle: damerajee/jee-question-json-format | JEE+NEET | JSON | needs Kaggle creds; check manually |

**No parsed JEE MAIN physics on HF** → get NTA PDFs manually (`ingest-drop`).
Legal posture: collected Qs = internal reference corpus; sold output = GENERATED + validated (copyright-clean). No coaching-site scraping.

---

## 5. Live generation API (frontend contract)

Base `https://rtx.trigunai.com/examgen` · handoff doc = `question_bank_engine/FRONTEND_HANDOFF.md` · test page = `test_client.html`.

- `GET /health` — status + `llm_reachable` + bank size
- `GET /chapters?exam=JEE%20Advanced&subject=Physics` — topic picker (chapters + concepts + exemplar counts)
- `POST /generate` (Bearer key) — body: `{exam,subject,chapter,concept?,difficulty:"3-4",type:"MCQ_single",count,exemplars,require_figure}` → returns questions (LaTeX), options, `correct_answer`, `solution`, `figure_svg` (generated diagram) / `figure_url` (real PNG), `answer_key`.
- Manage: `sudo systemctl restart qbank-api`; logs `journalctl -u qbank-api -f`.

---

## 5.5 BATCH PRE-GENERATION → shared question pool (the volume engine) ⭐

**Why:** live `/generate` is 15–60 s/pack — too slow for a student to do many questions, and it burns Azure tokens per request per student. So we **pre-generate a large SHARED pool once**, the frontend serves from it **instantly (no LLM in the hot path)**, and live generation only fires when a *power user drains a cell*. This is the single biggest lever for "questions per active user."

**✅ NOW LIVE (2026-07-25):** `/pool` + `/pool/stats` are **deployed on Gurukul and serving** (~1,400 pool
Qs across all 9 subjects). Batch fills run on the **`qbank-worker` VM** (§1), not the tiny Gurukul box, then
sync to Gurukul additively. **Runbook (worker):** `ssh -i ~/.ssh/qbank_worker_key azureuser@40.80.84.87`;
`cd ~/question_bank_engine`; `set -a; . ./api.env; . ./pg.env; set +a; export QBANK_SEMANTIC=off QBANK_CHAT_MODEL=gpt-5.6-terra QBANK_LLM_HARD_TIMEOUT=300`
(⚠️ **semantic OFF for concurrent fills** — onnxruntime deadlocks under parallelism); then
`python run.py batch-generate --exam X --subject Y --per-cell N --difficulties BAND --types MCQ_single`
(multi-subject driver = `/tmp/fill_all.sh`). **Then sync to Gurukul:** `dump_gen_all.py` → scp `gen_all.json`
→ `apply_gen_all.py` (INSERT OR IGNORE by id) → `sudo systemctl restart qbank-api` on Gurukul. The nightly
cron (`auto_refill.sh` via Azure Automation) does all this automatically — see §10 SESSION 2026-07-25.
**Deallocate the worker when done** (`az vm deallocate -g trigunai-video-creator -n qbank-worker`).

**How it works (built, pending deploy):**
- Generated questions already persist (`generator.generate_test` upserts them `generated=1, verified=1`). The "pool" = those rows.
- `pipeline.batch_generate(exam, subject, per_cell, difficulties, qtypes, chapters, ...)` walks the taxonomy and, for each **(chapter × difficulty-band × qtype) cell**, tops up to `per_cell` verified questions — **SKIPPING cells already at target ⇒ resumable & idempotent** (re-run any time to refill drained cells). Reads `store.pool_stats()` to know coverage.
- `storage.pool_questions(...)` serves the pool (randomised, `exclude_ids` = already-seen). `storage.pool_stats()` = coverage per cell.
- API (frontend hot path): **`GET /pool`** (instant, NO auth/LLM) + **`GET /pool/stats`** (ops). Live **`POST /generate`** stays the fallback when `/pool` returns `exhausted:true`.

**Runbook — start a batch fill (fresh session):**
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53   # or EC2 for heavy runs, then sync DB to Gurukul
cd ~/question_bank_engine
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 QBANK_CHAT_MODEL=gpt-5.5   # gpt-5.5 = higher-quality pool
# one subject at a time; nohup because it's long. per-cell 15, both difficulty bands, MCQ_single:
PYTHONUNBUFFERED=1 nohup python3 run.py batch-generate --exam "JEE Advanced" --subject Chemistry \
   --per-cell 15 --difficulties "2-3,3-4" --types MCQ_single > /tmp/batch_chem.log 2>&1 &
# monitor:  tail -f /tmp/batch_chem.log   ·   coverage:  python3 run.py pool-stats --subject Chemistry
```
**Scale math:** JEE Advanced Chemistry = 25 chapters × 2 bands × 1 type × 15 = ~750 questions; each ~10–40 s on gpt-5.5 + verify gate → a few hours/subject, ~$1–3 Azure/subject. JEE Main (28–32 chapters) is bigger — run per subject, in background, over several sessions. **For real scale, a Workflow** (fan out over cells, verify each) is the natural orchestrator — user must opt in ("use a workflow").

**Gotchas:**
- Pool quality = generation quality. Use `QBANK_CHAT_MODEL=gpt-5.5`; the novelty gate (`NOVELTY_MAX_SIM=0.82`) blocks near-copies of real Qs; the verify loop drops implausible answers. **Generated answers are still less trustworthy than real past-paper keys** (§8) — served as PRACTICE, and the frontend's "report" button feeds review.
- After a batch run on EC2, **sync the DB to Gurukul** (the live one) — `scp data/qbank.sqlite` + restart `qbank-api`. Or run batch-generate directly on Gurukul (litellm is there too).
- Re-running batch-generate is safe (skips full cells). Increase `--per-cell` later to deepen the pool.
- To add types beyond MCQ_single (integer/numeric/MCQ_multi), pass `--types "MCQ_single,integer"`.

**Full frontend contract for the pool model:** `question_bank_engine/FRONTEND_HANDOFF_POOL.md`.

---

## 6. ADD A NEW SUBJECT OR EXAM (the reusable workflow)

Example: JEE Advanced **Chemistry** (or Maths / NEET / boards). Depth-first — finish one subject before the next (see [[feedback-qbank-depth-first]]).

1. **Taxonomy** — add to `qbank/syllabus.py`: define the chapters+concepts+keywords dict and register it:
   ```python
   JEE_CHEMISTRY = { "Chapter": {"keywords":[...], "concepts":{"Concept":[kw...]}}, ... }
   TAXONOMIES[("JEE Advanced","Chemistry")] = JEE_CHEMISTRY
   ```
2. **Ingest** —
   - text years (2016–23): `run.py ingest-dataset --subject chem --subject-name Chemistry`
   - latest years (2024–26): `run.py ingest-images --exam-prefix JEE --subject Chemistry` (vision, in background — ~15-20 min/100)
3. **Tag**: `run.py retag --chapter <none = all new>` (LLM) — concept-accurate.
4. **Solve + verify**: `run.py enrich-solutions` then `run.py reverify --k 5`. For DIAGRAM questions the LLM can't text-solve, solve them yourself (see §7).
5. **Figures**: image ingest auto-saves diagrams; run `run.py mark-figures` for text-dataset figure refs.
6. **Verify**: `run.py stats`, spot-check `run.py sample`, test `run.py query`.
7. **Generate**: `run.py generate --subject Chemistry --chapter ...`. Frontend `/chapters` picks it up automatically.

**Deploy to the LIVE box = Gurukul VM** (not EC2 — the DB there is a fallback copy):
`scp -i ~/.ssh/gurukul_key question_bank_engine/qbank/*.py dk_trigun@20.219.2.53:/home/dk_trigun/question_bank_engine/qbank/` then `ssh … 'sudo systemctl restart qbank-api'`. The engine + LIVE DB live at `/home/dk_trigun/question_bank_engine/` (venv `.venv/`). **Back up `data/qbank.sqlite` to `backups/` before any bulk ingest** (it's the live bank). Run heavy LLM jobs with the §1 env exported (or `. ./api.env`).

---

## 6.5 REUSABLE EXTRACTION PLAYBOOK (start here for a NEW subject/exam — boards, Commerce, JEE-Main top-up)

Proven on NEET (2026-07-23: ~1k → ~33k). **Prefer a PRE-TAGGED + PRE-SOLVED text source** (datavorous / grafite / sweatSmile) — it needs no LLM for tags/keys/solutions, so tens of thousands of Qs cost ~$0 and finish in minutes.

**Step 1 — Find sources on HuggingFace (script, not guessing).** Query the API, then filter to datasets that actually carry an answer key:
```python
# search many terms → dedup ids
"https://huggingface.co/api/datasets?search=<term>&limit=50"   # terms: "<exam> mcq","cbse mcq","<subject> pyq","board exam india",...
# for each candidate, keep only if a feature name looks like an answer AND rows>=300:
"https://datasets-server.huggingface.co/info?dataset=<id>"     # features + row counts
# ANS keywords to require in features: answer/correct/key/gold/label/solution/option
"https://datasets-server.huggingface.co/first-rows?dataset=<id>&config=default&split=train"   # eyeball 3 rows
```
Then **audit before trusting**: sample ~25 rows, verify keys against your own knowledge. Two real datasets FAILED this (BruthaCool = no keys; catchshubham = keys contradict their own explanations). A big row count means nothing without correct keys.

**Step 2 — Pick the adapter by row SHAPE** (no new parser unless the shape is genuinely new):

| Row shape | Adapter / CLI | LLM? |
|---|---|---|
| `tags`=[Subj,Chapter,Exam] + HTML `<li class="correct">` + `answer` solution | `from_datavorous_row` / `ingest-datavorous --exam X` | none |
| subject/chapter/topic + options[{identifier,content}] + correct_option + solution | `from_grafite_row` / `ingest-grafite` | none |
| `{question, choices[], answer}` (letter or index) | `from_neet_bio_row` / `ingest-neet-bio` | none |
| inline `(A)…(B)…` stem + `gold` | `from_dataset_row` / `ingest-dataset` | none (tag/solve later) |
| question is a PNG, answer in metadata | `from_image_row` / `ingest-images` | vision |
| PDF papers + key PDF | `from_pdf` / `ingest-drop` | vision |

If the shape is new, write a small `from_<name>_row` mirroring the closest one (they all return a `Question`; the validator owns `verified`).

**Step 3 — Taxonomy: DERIVE from the ingested chapters, don't hand-author.** When the source is pre-tagged, ingest FIRST with the source's own chapter names, then generate the taxonomy from the DB (`derive_neet_taxonomy.py` is the template — query `SELECT chapter,COUNT(*) … GROUP BY chapter`, emit a `{chapter:{keywords,concepts:{}}}` module, register in `syllabus.py TAXONOMIES`). This guarantees `/chapters` matches the data exactly. Hand-authoring first (as NEET Biology was) causes name-mismatch churn — only do it when there's no dominant pre-tagged source.

**Step 4 — Solve (only if the source lacks solutions).** `enrich-solutions --exam X --subject Y` (gpt-4o for boards/NEET-easy; gpt-5.5 for JEE-hard; Claude-in-session for the hardest — §7). SHARD long jobs: the LiteLLM proxy doesn't serialize, so `xargs -P 8` over `--chapter` is ~10× faster.

**Step 5 — Deploy + verify**: back up DB → sync code+DB to Gurukul → `restart qbank-api` → `curl /chapters?exam=X&subject=Y` → one `/generate`.

**THE GOTCHAS (each cost real time — check them up front):**
1. **Option-index answer keys.** Papers labelling options `(1)(2)(3)(4)` with the key given as an INDEX get rejected `no_answer_key` (bank wants A–D). `extractor.letterize_options` handles numeric labels + positional keys; `repair_numeric_options.py` fixes already-ingested rows. **Check label-vs-key format FIRST on any image/new source.**
2. **Two independent key markers → cross-check, drop disagreements.** Free key validator (datavorous had 0/49,771 disagree). If a source marks the answer two ways, verify they agree in the adapter.
3. **Cross-subject mis-tags.** Sources mis-file rows (datavorous had 1,118 physics Qs tagged `subject=Chemistry`). Rule: **the chapter name is truth** (dominant-subject voting is unreliable — Capacitance is physics but Chem-dominant; Biomolecules is legit in both Bio+Chem). Reassign by an unambiguous chapter set.
4. **Dedup is automatic** (content-hash + TF-IDF) — expect 15–20% flagged on aggregated PYQ banks; that's correct.
5. **Difficulty band per exam**: NEET/boards ~2–3, JEE Main ~2–3, JEE Advanced 3–4. Set `--difficulty`.
6. **Ops:** `storage` uses WAL+busy_timeout so jobs+API share the DB; `retag/enrich/reverify` need `--exam/--subject` or they sweep the whole ~44k bank; figure URLs follow `QBANK_PUBLIC_BASE` (must be the Gurukul examgen URL, set in `api.env`).
7. **Stripped diagrams = silent incomplete questions.** HTML/PDF sources embed diagrams as `<img>`; a text adapter strips them, leaving a question that says "as shown in the figure" with NO figure and NO `needs_figure` flag. datavorous did this to ~1,055 rows (mostly NEET Physics). **Any text adapter must set `needs_figure` from the raw `<img>` OR `references_figure(stem)`** (from_datavorous_row/from_grafite_row now do). Backfill existing rows with `flag_figure_refs.py --apply` (additive: flags fig-referenced + no-image, never unflags). Real figure PNGs only exist for image-sourced Qs (Reja1 vision ingest → `figure_url`); the text bulk is diagram-less, so figure questions there are *excluded*, not rendered. Generation can still emit its OWN SVG diagrams via `require_figure`.

**NEXT candidates (no bank yet — the LMS `EXAMS` already lists them):** **Class 10** (Sci+Math boards), **Class 12** (PCM boards), **Commerce** (Class 11–12). Search HF per Step 1 (`cbse class 10 mcq`, `ncert exemplar`, `cbse pyq`, `class 12 board mcq`, `accountancy/economics/business studies mcq`); the KadamParth/NCERT_* set (Biology/Chemistry/Physics/Accounting/Economics/Business-Studies 11th+12th) is a candidate to check. Also: **datavorous has ~35k JEE Main rows un-ingested** (`ingest-datavorous --exam "JEE Main"`) — a quick depth top-up over the existing 11k grafite bank.

---

## 7. Solving questions well (Claude-as-solver, the quality lever)

gpt-4o agrees with official JEE-Advanced keys only ~50%; a stronger reasoner (Opus in-session) hits ~99%. So for a subject's hardest questions:
- **Text questions**: read them (`sample`/DB export), solve in-context, write `[{id,answer,solution}]` JSON, `python3 apply_solutions.py <json>` (compares to official key; range-aware for tolerance answers).
- **Diagram questions**: `scp` the `figures/<id>.png` locally, **Read the images**, solve from the figure, then `apply_solutions.py`.
- Mismatches auto-flag `answer_disputed_claude` (a free bad-key detector — 2 official 2026 keys were caught wrong: #42, #95). Never fabricate an answer just to match; flag/skip un-solvable ones.

---

## 8. Generation: similar vs innovative

- **Similar** (same concept, new numbers/scenario) → reliable, at scale. Novelty gate (`NOVELTY_MAX_SIM=0.82`) blocks copies. Your practice-drill engine.
- **Innovative** (concept crossover across two chapters, difficulty escalation, scenario transfer, inversion) → possible but the generated ANSWER is less trustworthy (the model often can't solve its own hard creation). **Gate every generated question through the verify loop** (`solve_consistent`); expect lower yield; human-review the hardest.
- Grade the PRODUCT on **real verified questions**; use generation for practice/variety.

---

## 9. Settled strategy (don't relitigate)

- **RAG over fine-tuning.** ~200-2000 examples is far too few to fine-tune reasoning into an LLM; SFT teaches format not reasoning; JEE Adv is a reasoning task where small open models are weak. This data's real uses: RAG exemplars, eval set, few-shot, and a FUTURE fine-tune/RLVR seed once there are 10k+ verified Qs.
- **Graded tests = real past-paper questions (correct keys); generation = practice.**
- **Depth-first**: perfect one subject (tags+solutions+diagrams) before breadth.

---

## 10. Current state + resume

### ⭐ SESSION 2026-07-29 — mock-paper series (all 8 exams) + UPSC/CBSE practice pools + CBSE Maths

Driven from the LMS side (drove `/generate` + `/pool` remotely; no worker-VM needed — every `/generate`
persists to the live DB, so a chapter-loop fill = pool fill). All on the Gurukul box; DB backed up each time.

1. **Mock-paper "test series" = PER-EXAM.** Two generators in `lms/tools/`: `build_mock_papers.py --goal <id>`
   (LLM, per-exam blueprints in `lms/app/mockpaper.py::BLUEPRINTS`) + `build_pool_papers.py --goal <id>`
   (assembles REAL PYQs from `/pool`, for UPSC + CBSE boards). All 8 exams now have 3 papers (JEE-Adv 5).
   Boards are MCQ-only (bank has no subjective board Qs) → labeled "MCQ Practice", not "Mock".
2. **UPSC was chapter-UNTAGGED** (518 real PYQs, `chapter=NULL`) → ran `parallel_tag.py --exam "UPSC Civil
   Services (Preliminary)"` (494 high-conf) so per-chapter generation + practice pools work.
3. **Practice pools filled** for UPSC + CBSE (10/12/Commerce): the fix was to generate against the ACTUAL
   stored chapter names (not taxonomy names — CBSE stored "Electric Charges and Fields", the taxonomy said
   "Electrostatics" → 0 exemplars). Loop DISTINCT DB chapters, `/generate` count=4 grounded in 3 exemplars.
4. **⭐ CBSE Class 12 Maths via companion-exam borrow (the reusable trick):** only 34 real (untagged, narrow).
   Patched `qbank/syllabus.py`: `TAXONOMIES[("CBSE Class 12","Mathematics")] = JEE_MAIN_MATHS` (same syllabus
   + chapter names) + `EXEMPLAR_FALLBACK[("CBSE Class 12","Mathematics")] = ("JEE Main","Mathematics")` →
   restart `qbank-api` → generate at BOARD difficulty (2-3) grounded in JEE Main Maths' 10.8k real Qs →
   116 Qs/32 chapters. CBSE Class 10 Maths was ALREADY in the bank (49k, UltraData NCERT) — just wired in the LMS.
   Backup `qbank/syllabus.py.bak_cbse12maths_*`. **Pattern: a board/thin subject can borrow a syllabus-matched
   exam's exemplars + author at the easier difficulty** (this is how NEET Phy/Chem already work).
5. Wired into LMS `examgen.RAG_SUBJECTS` + `GOALS`: `cbse10-maths`, `cbse12-maths` (lms v132/v133). NEXT
   (real, not generated) = CBSE Class 12 Maths via the exact-question PDF pipeline on official papers.

### ⭐⭐ SESSION 2026-07-25 — POOL IS LIVE + BATCH WORKER + AUTO-REFILL CRON (read this FIRST)

The volume engine is now production. Detail in [[project-qbank-worker-vm]]; this is the index.

1. **`/pool` IS LIVE on Gurukul** (was 404 all along). Deployed the repo `api.py` (a superset — adds
   `/pool` + `/pool/stats`, storage.py already had `pool_questions`/`pool_stats`) + restarted `qbank-api`.
   `GET /pool?exam&subject&chapter&difficulty&type&count` serves real complete questions **instantly**
   (no LLM, no auth); `/pool/stats` = coverage. Frontend is pool-first → **serves instant with NO code
   change**. `POST /generate` stays the fallback on `exhausted:true`.
2. **New batch-worker VM `qbank-worker`** (see §1 + [[project-qbank-worker-vm]]) — the heavy box.
   Provisioned via `az`, full env stood up: PG16+pgvector 0.6, prod-pinned venv, LiteLLM (gpt-5.6-terra),
   live DB replica. SQLite→PG migrated (57,608 rows) + **46,397 verified embedded (bge-small-384) + HNSW**.
3. **Pool FILLED** — ~**1,400 generated pool questions across all 9 subjects** (primary band per exam:
   JEE-Adv `3-4` · JEE-Main `3` · NEET `2-3`; MCQ_single; per-cell 5) on gpt-5.6-terra, then **synced to
   Gurukul additively** (`dump_gen_all.py` → scp → `apply_gen_all.py` INSERT OR IGNORE by id → restart
   qbank-api). Driver = `/tmp/fill_all.sh` on worker (4 concurrent, `wait -n` gate). Deepen later by
   re-running (idempotent, skips full cells) or raising `--per-cell`.
4. **Nightly auto-refill CRON (cost-smart)** — Azure Automation `qbank-scheduler` (managed identity,
   VM Contributor) → runbook `nightly-refill` (Start-AzVM → `Invoke-AzVMRunCommand` launches
   `~/auto_refill.sh`) → schedule `nightly-2100utc` daily 21:00 UTC. `auto_refill.sh`: top-up
   below-threshold cells (semantic OFF, per-cell 10, 3 concurrent) → sync to Gurukul → **self-deallocate**
   via `az login --identity`. `litellm.service` auto-starts on boot. Worker bills only during the window
   (~$10-15/mo). **CAVEAT: runbook not yet test-run** (would collide with the initial fill) — validate on
   first scheduled run or a manual `az automation runbook start` when idle. Pause = disable the schedule.
5. **TWO fixes made (both real debugging):**
   - **LLM hang** — a gpt-5.6 call stalled 34 min (SDK `timeout=240` defeated by proxy keepalives).
     `qbank/llm.py` now wraps `.create()` in a **ThreadPoolExecutor hard deadline** (`QBANK_LLM_HARD_TIMEOUT`,
     default **300s**); a timeout **returns None (skips the Q), does NOT raise** → one stuck call can't abort
     a batch. **Applied on the worker; NOT yet deployed to Gurukul** (live `/generate` could hang too — deploy `llm.py` there later).
   - **fastembed/onnxruntime DEADLOCKS under concurrency** — 4 parallel batch procs all `futex_do_wait`,
     0% CPU, PG "idle in transaction". Single-process semantic is fine. → **bulk fill runs `QBANK_SEMANTIC=off`**
     (TF-IDF novelty still blocks copies); run a single-process pgvector semantic-dedup pass separately if wanted.
6. **Frontend pricing wired same session** (see the `acharya-student-frontend` skill): student `/exam-prep/upgrade`
   = Exam Pass ₹1,299 + ₹249/mo; teacher `/teacher` = ₹999/₹2,999/₹7,999 tiers. `lms:v102`. Canon = `PRICING_MODEL.md`.

---

### ⭐ SESSION 2026-07-24 — WHAT'S NOW LIVE & WORKING

All live on the always-on Gurukul VM (`gurukul.trigunai.com/examgen`). Detail in the dated sub-sections above; this is the index.

1. **Generation model = `gpt-5.6-terra`** (LIVE — `api.env` `QBANK_CHAT_MODEL=gpt-5.6-terra`). Newer/cheaper-than-gpt-5.5 reasoning model, deployed on Azure `trigunai-lms-aoai` (RG `trigunai-video-creator`, eastus, GlobalStandard) + wired into LiteLLM. **`gpt-5.6-sol`** also deployed (hard solve/verify tier — `QBANK_CHAT_MODEL=gpt-5.6-sol`). gpt-5.5 still available. All reasoning models → proxy drops `temperature` via `additional_drop_params`. Verified authoring live.
2. **Figure-first DIAGRAM questions = LIVE** (`qbank/figuregen.py` + router in `generator.generate_test`). `/generate` with `require_figure=true` on a Chemistry organic chapter → deterministic engine: WE draw the structure (55 verified compounds → RDKit) + RDKit COMPUTES the answer (formula/stereo/DoU/rings/-OH). Served glycerol PNG verified. Correct-by-construction, copyright-clean. Maths/Physics = next plug-ins.
3. **Incomplete-question guard = LIVE** (`models.is_figure_dependent` qtype-aware + serving gate in `storage.pool_questions`/`retrieve(servable_only)` + 1,344 backfilled `needs_figure`). Sampled 246 served → 0 incomplete. Never serves a figure-less "as shown below" Q.
4. **79 clean chem figures** attached to real diagram rows (`<id>.gen.png`, OPSIN→RDKit, watermark-free) via `diagram_generate/generate_chem_figures.py` + PubChem fallback (`resolve.py`).
5. **Postgres+pgvector = UP** on Gurukul (native apt PG16, `pg.env`, 46,396 verified rows embedded bge-small-384 + HNSW). **Semantic rewire deployed but GATED TO BATCH** — `api.env` `QBANK_SEMANTIC=off` (live API light, ~9s text-gen); export `QBANK_SEMANTIC=on` for batch pool-fill (semantic novelty + diverse exemplars). SQLite is still the store of record.
6. **New code (all in `question_bank_engine/`, UNCOMMITTED to git):** `qbank/semantic.py`, `qbank/figuregen.py`; `diagram_generate/` (resolve, triage_chem, triage_v2, generate_chem_figures, generate_rxn_table, generate_diagram_questions, generate_math_physics_demo, audit_backfill_figures, pg_migrate, pg_embed, calibrate_semantic); edits to `qbank/models.py` + `storage.py` + `generator.py`. Backups: `data/qbank.sqlite.pre_*`, `qbank/*.py.bak_*`, `api.env.bak_*`, `~/litellm/config.yaml.bak_*`.
7. **Portable Temurin-17 JRE at `~/jre`** on Gurukul (no-sudo, for OPSIN) + a **2G swapfile** added (box was 0-swap, needed for embed jobs). **NEXT:** batch-fill the diagram pool (figure-first across organic chapters); Maths/Physics figure-first plug-ins; PubChem-fallback widen chem figures; formal SEM_MAX_SIM calibration + enable semantic in live API once on a bigger box/Azure PG.

---

**JEE Advanced — ALL 3 subjects complete:**
- **Physics: 238 verified** — 213 real Qs, 205 (96%) worked solutions, 156 Claude-verified, 54 diagram Qs w/ figures. 2 disputed keys flagged (#42, #95).
- **Chemistry: 149 verified (100% solved)** + **Mathematics: 226 verified (100% solved)** (2026-07-23) — from `daman1209arora/jeebench` (`--subject chem/math`, TEXT, 2016–23). LLM-tagged into 25/27 chapters (reusing the JEE Main Chem/Maths taxonomies — same syllabus), difficulty 3–4. Answers = jeebench `gold`.
  - **Worked solutions to Physics-level parity, done 2026-07-23:** **Maths = all 226 Claude-solved in-session** (16 batches via `apply_solutions.py`; **225 match official key, 1 genuine disputed key** flagged `answer_disputed_claude` = the 2018 f_n telescoping problem where options A & B are also provably true — a known controversy). **Chemistry = all 149 solved** (114 by gpt-5.5, **35 Claude-solved in-session**, all 35 match). Physics 231/238 (7 un-figurable/truncated remain).
  - **gpt-5.5 now wired into LiteLLM** (both boxes): Azure resource `trigunai-lms-aoai` (deployment `gpt-5.5`, api-version 2025-04-01-preview, same one OpenClaw uses); added to `~/litellm/config.yaml`. **gpt-5.5 is a REASONING model — reject custom `temperature`** (only default), so `qbank/llm.py` now OMITS temperature for gpt-5.x (helper `_is_reasoning_model`) and uses a **240s client timeout** (was 45s — reasoning takes >60s on hard Qs). Solve with gpt-5.5 via `QBANK_CHAT_MODEL=gpt-5.5`; agreement on JEE Adv ~88% vs gpt-4o's ~50% — but for the hardest (esp. Maths) **Claude-in-session solving is the gold standard (~99%+)** via export-unsolved→batch-solve→`apply_solutions.py`.
  - **2 ingest bugs fixed:** (a) `ingest-dataset` LLM well-formedness check spuriously rejected ALL integer/numeric Qs — `ingest_open_dataset` now defaults **rule-based** (`llm_validate=False`, opt-in `--llm-validate`); (b) `/chapters` merged same-named chapters across exams — added `storage.chapter_counts(exam,subject)`. Generation retrieval was already exam+subject-scoped (no cross-exam bleed). Optional next: adjudicate the 3 disputed keys (2 Physics + 1 Maths); Reja1 2024–26 image Qs.

**JEE MAIN — ALL 3 subjects complete (2026-07-23)** — from `ruh-ai/grafite-jee-mains-qna-no-img` (pre-tagged + pre-solved TEXT, grafite keys TRUSTED = verified via rule_check since these are RAG *exemplars*, not a graded set — key-audit LLM flag-pass still optional):
- **Physics: 3,444 verified**, 28 chapters/127 concepts, taxonomy `qbank/jee_main_physics.py`
- **Chemistry: 3,212 verified**, 31 chapters/156 concepts, taxonomy `qbank/jee_main_chemistry.py`
- **Mathematics: 4,062 verified**, 32 chapters/186 concepts, taxonomy `qbank/jee_main_maths.py`
All registered in `syllabus.py TAXONOMIES` under `("JEE Main", <subject>)`; live on the Gurukul host — **`bank_verified` now ~10,957** (incl. the 238 JEE-Adv Physics). Built via `ingest-grafite` + `extractor.from_grafite_row` + `pipeline.ingest_grafite`. **NOT yet wired into the student LMS** — needs `RAG_SUBJECTS` (`jee-main-physics/chemistry/maths`) entries in `lms/app/examgen.py` + `EXAMS` in `lms/app/main.py`, then deploy `lms:vN`.

**Resume checklist (fresh session):**
1. **Live API now on the Gurukul VM** (always-on): `curl https://gurukul.trigunai.com/examgen/health` → expect `{status:ok, llm_reachable:true, bank_verified:…}`. Box: `ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53`; code `cd ~/question_bank_engine`; `.venv/bin/python run.py stats`. Services: `systemctl status qbank-api litellm-proxy` (both `--now`+enabled). Caddy route in `/etc/caddy/Caddyfile` (`handle_path /examgen/*`→8020); reload not restart.
2. For heavy INGEST/RETAG/SOLVE work you may still prefer the EC2 box (`ssh -i ~/.ssh/trigunai_key.pem ubuntu@34.192.145.204`) — but it needs the GPU box ON, and its DB is now a FALLBACK copy (the LIVE DB is on Gurukul). Keep the two DBs in sync if you ingest on EC2 (scp `data/qbank.sqlite` + `figures/` Gurukul↔EC2).
3. LLM env (§1): on Gurukul the LiteLLM proxy is `litellm-proxy.service` at `127.0.0.1:4000` (config `~/litellm/config.yaml`, master key `sk-trigunai-master-key-2026`). Export the §1 vars (or use `api.env`) for any tag/solve/generate work. **Models available via the proxy: `gpt-4o-mini`/`gpt-4o` (weak, ~50% on JEE Adv), `gpt-5.5` (reasoning, ~88% JEE Adv), AND the newer `gpt-5.6-terra`/`gpt-5.6-sol`** (deployed 2026-07-24 on Azure `trigunai-lms-aoai`, GlobalStandard, api-version 2025-04-01-preview; both wired into `~/litellm/config.yaml` with `additional_drop_params:[temperature,top_p]`). **GPT-5.6 tiering (recommended go-forward):** `gpt-5.6-terra` = bulk generation workhorse (≈gpt-5.5 quality at ~½ the cost: $2.50/$15 per 1M) → **swap the pool/batch-generate default from gpt-5.5 → gpt-5.6-terra**; `gpt-5.6-sol` = hardest solve/verify/disputed-key adjudication ($5/$30). All are reasoning models → `qbank/llm.py` `_is_reasoning_model` must skip `temperature` (currently keys on gpt-5.x — the proxy already drops it via `additional_drop_params`, so calls won't 400 even if the code sends it). 240s timeout still applies. **✅ LIVE default switched 2026-07-24: `api.env` on Gurukul now `QBANK_CHAT_MODEL=gpt-5.6-terra`** (was gpt-5.5) — qbank-api restarted, live `/generate` verified authoring valid questions on it. `api.env.bak_*` kept. Escalate to `gpt-5.6-sol` for the hardest solve/verify by exporting `QBANK_CHAT_MODEL=gpt-5.6-sol` for that job.
4. **Best-quality solving = Claude-in-session** (~99% match, esp. Maths): `export` unsolved Qs to JSON (id, stem, options, gold), solve in batches of ~12–15, write `[{id,answer,solution}]`, `python3 apply_solutions.py <json>` (compares to official key; flags `answer_disputed_claude` on mismatch — NEVER fabricate to match, flag it). This is how all 226 Adv-Maths + 35 hardest Adv-Chem were done. gpt-5.5 handles the bulk; Claude handles the hardest / adjudicates disputes.
5. **✅ IIT JEE (Advanced + Main) + NEET all DONE** — 9 exam×subject banks, ~44k verified, tagged + solved, live on Gurukul. Handoffs: `FRONTEND_HANDOFF_IIT.md`, `FRONTEND_HANDOFF_NEET.md`.
6. **▶ NEXT SUBJECT to build = boards (Class 10 / Class 12 / Commerce)** — no bank yet, but the LMS `EXAMS` already lists them. Follow **§6.5 REUSABLE EXTRACTION PLAYBOOK** (find a pre-tagged HF source → pick adapter by shape → ingest → derive taxonomy from DB → deploy). Quick win also available: `ingest-datavorous --exam "JEE Main"` (~35k rows to top up JEE Main).

### 🖼️ DIAGRAM QUESTIONS — figures recovered 2026-07-24 (~4,437 with real images)

The bank is text-first, but diagram questions now carry their ACTUAL figure. Key insight: **datavorous embeds diagrams as `<img>` pointing at a live CDN** (`cdn-question-pool.getmarks.app`), which our text ingest stripped — the figures aren't lost, they're re-downloadable. So "solving the diagram bank" is mostly FIGURE RECOVERY (the keys+solutions were already ingested), not re-solving.

- **`recover_datavorous_figures.py --exam X --apply`** (run with `. ./api.env` sourced so figure_url uses the Gurukul PUBLIC_BASE): re-reads the source, downloads the figure(s), attaches `figure_url`/`figure_refs` + `needs_figure=1` to the already-banked row (matched by the deterministic `from_datavorous_row` id). Magic-byte ext sniffing (png/jpg/extension-less mix), dedup by qid, idempotent, dry-run default.
- **Result (verified diagram Qs WITH a real figure):** NEET 2,371 (Bio 418 / Phys 1030 / Chem 923) · JEE Advanced 199 · JEE Main 1,867 = **4,437**. Bank ~46,294.
- **IIT path (diagram-focused):** `ingest-datavorous --exam "JEE Main" --figures-only` ingests ONLY `<img>` rows and CLEARS the chapter (datavorous JEE chapter names only ~25-45% match our taxonomy) → `parallel_tag.py --exam "JEE Main"` LLM-tags them into the EXISTING JEE taxonomy → recover figures. This adds diagram Qs without touching the grafite JEE text banks.
- **`parallel_tag.py`** — thread-pool LLM tagger for untagged verified Qs (~15/sec vs single-thread ~1/sec). Use for any big tag job; scoped to `chapter IS NULL` so it never re-tags the established bank.
- **⚠️ figures carry a getmarks "MARKS" watermark** → kept to INTERNAL/exemplar use pending the serve-real-vs-generate-clean decision (§ the diagram strategy). Figure recovery is valuable under every posture (serve / redraw-clean / verify), so it was done regardless.
- **Open — Phase 2:** multi-image "which graph" questions (options ARE images) are rejected `empty_option` at ingest (~1,500 across exams) — need a figure-SET render + adapter that keeps image-options. **Phase 3:** VLM-verify figure↔key consistency at scale (3 hand-checks passed: NEET black-body, NEET age-pyramid, JEE polaroid).

### 🎨 CLEAN-REDRAW research (2026-07-24) — remove the getmarks watermark by re-authoring figures

The recovered figures carry a getmarks watermark → can't serve raw. Investigated auto-redrawing them clean. Harnesses in `question_bank_engine/diagram_redraw/` (+ README). Findings:
- **General VLM (gpt-4o) → spec → render = FAILS.** Lossy extraction; the VLM verifier gives FALSE-passes (scored a clearly-wrong graph 10/10). Don't auto-ship it. `redraw_graphs.py`/`redraw_chem.py`.
- **Specialist OSR beats general VLM decisively for chemistry.** `DECIMER` (open-source, image→SMILES, on the EC2 A10G) read a single skeletal chiral molecule — stereochemistry + tritium isotope — PERFECTLY, where gpt-4o got ~0. RDKit renders it clean. Research: MolScribe/DECIMER ~90%. **MolScribe unusable on our boxes (pins Python≤3.10; ours is 3.12) — use DECIMER.** Env: EC2 `~/molscribe_pilot/decimer_env`.
- **The universal blocker = MCQ OPTION PANELS** (4 candidate molecules/graphs in ONE image) — cuts across EVERY diagram type. A single-item OSR reads a panel as one C300 garbage blob.
- **Segmentation solves it.** `segment_osr_render.py` splits a panel into per-option crops (dilate + connected-components; tailored to exam panels — NO Mask R-CNN, which is dep-hell on modern TF) → DECIMER + RDKit per crop. Proven: alcohols panel → 4 clean option crops.
- **Remaining gap = depiction style, a domain-shift.** DECIMER excels on SKELETAL line drawings, ~50% on the CONDENSED notation Indian exams use (`CH3-CH-CH2OH` with explicit labels) — tert-butanol read perfectly, isobutanol misread on the SAME panel. **Fix = fine-tune DECIMER on exam-style condensed structures** (we have thousands in the bank), not more pipeline.
- **Net:** the segment→OSR→render pipeline is BUILT and works end-to-end; chemistry single/skeletal is near-shippable; condensed-notation + freehand physics (mechanics/circuits) are not yet. **Interim posture stands: recovered figures INTERNAL only; student-facing diagrams = GENERATE new questions with our own simple figures.** Newest tool to try next: **DeepSeek-OCR 2** (3B, one model for structures+charts+geometry).

### 🎯 DIAGRAMS — GO-FORWARD APPROACH (text→generate→verify). ⭐ CHEM PIPELINE BUILT + 79 LIVE; NEXT = PubChem fallback + PHYSICS

**The redraw/OSR approach is a dead end** (perception bottleneck — see above). **New, better approach chosen 2026-07-24: don't reproduce their figure at all — GENERATE our own correct figure from the TEXT we already have, then VERIFY.** ✅ **Chemistry pipeline BUILT + 79 clean figures LIVE — see the "CHEMISTRY PIPELINE BUILT" box below for results, code, lessons, and the runbook.**

**Why it's stronger:** (1) skips PERCEPTION entirely (the exact thing that failed — reading messy watermarked images); (2) we already have the reliable inputs as text: stem + options + **correct answer** + **worked solution**; (3) verification is against the KNOWN ANSWER, not visual similarity → **no false-pass problem** (the thing that made the redraw-verifier untrustworthy); (4) copyright-clean by construction — our own figure, never touches the getmarks image.

**The loop:**
```
question + solution (text) → generate a figure → SOLVE the question using our figure
   → does it match the KNOWN correct answer?   yes: keep   |   no: regenerate
```
This is a VERIFIABLE-reward loop (we own the answers), far more robust than the visual-match verify that false-passed.

**By type:**
- **CHEMISTRY = start here, cleanest, near-deterministic.** The solution usually NAMES the compounds ("tertiary alcohols react fastest → tert-butanol"). name→structure is a SOLVED problem: **OPSIN** (name→SMILES) → **RDKit** → perfect clean structure. No OSR, no image reading. Pipeline: LLM extracts compound name(s) from stem+solution → OPSIN → RDKit render → attach as clean `figure_url`. Measure yield.
- **PHYSICS setups** (incline/block/force, circuit whose values the solution restates): LLM generates a schematic (schemdraw / SVG) from the described config → verify by RE-SOLVING to the known answer (reuse `solver.py` / the generate-verify pattern).
- **Limit:** when the figure's data is in NEITHER stem NOR solution → the generate-and-solve loop simply won't reach the known answer → **detect + flag, keep internal.** A good worked solution usually restates the figure's data, so this is the minority.

#### ✅ CHEMISTRY PIPELINE BUILT + 79 CLEAN FIGURES LIVE (2026-07-24)

The chemistry `extract → OPSIN → render → gate → attach` pipeline is built, validated, and has
attached **79 clean, watermark-free, copyright-clean structure figures to the LIVE bank** (NEET +
JEE Chemistry). Code: **`question_bank_engine/diagram_generate/`** (`triage_chem.py`,
`generate_chem_figures.py`). Runs on Gurukul (CPU only). **NOT wired to EC2 GPU box.**

- **Env now on Gurukul:** portable **Temurin-17 JRE at `~/jre`** (no-sudo, no service — OPSIN's
  Java) + **`py2opsin`** in the qbank venv + RDKit already there. Run with `export PATH=$HOME/jre/bin:$PATH`.
- **Deterministic core is 100%.** `compound name → OPSIN(name→SMILES) → RDKit render` — zero
  perception. 24/24 representative exam names → correct clean structures (IUPAC, common, stereo).
- **Pipeline (`generate_chem_figures.py`):** (1) **extract** — gpt-4o reads stem+options+**answer**+solution,
  names the compound(s) to draw, tags each `source: stated|inferred`, sets `drawable=false` for
  the limit case AND for non-structure figures (graphs / Ellingham / energy diagrams / apparatus /
  tables / lattices / Assertion-Reason); (2) **OPSIN batch** — ALL names in ONE call; (3) **render**
  — RDKit clean PNG (single or option grid); (4) **match-gate** (the attach gate) — a VLM check
  *"does our figure show the compound(s) the question is actually about, or an incidental
  reagent / a wrong figure-type?"* — NOT solve-the-MCQ. `--attach` writes `<id>.gen.png` to
  `figures/` + `figure_url` onto the row.
- **Honest yield (full 916-Q chem-diagram pool, `solution>40`):** drawable **40%** · renders clean
  **34%** · Tier-A (all compounds *stated verbatim*) **17%** · **ATTACHABLE (Tier-A + match-gate) ≈ 12% → 79 rows.**
- **Cost** ≈ $0.005–0.015/question (1 gpt-4o extract + 1 vision match; OPSIN/RDKit free).
- **KEY LESSONS (each cost real debugging):**
  1. **py2opsin has a temp-file RACE** (`py2opsin_temp_input.txt` in CWD) → concurrent threads
     read each other's molecules → renders the WRONG compound silently. **Fix: batch all names in
     ONE `py2opsin([...])` call**, never per-thread. (Was the cause of a bogus 6/14 verify run.)
  2. **VERIFY-BY-SOLVING is the WRONG acceptance gate.** gpt-4o mis-ranks chemistry (amine
     basicity, dehydration/nitration order), so it FALSE-FAILS *correct* figures (a perfect
     4-alcohol panel "failed" only because the VLM mis-ordered dehydration). Use a **figure-subject
     MATCH check** instead — it targets the real failure mode (wrong/incidental compound) without
     needing the VLM to solve.
  3. **Tier-A (stated verbatim) is NOT auto-safe** — gpt-4o can extract a verbatim-mentioned
     *catalyst* (`AlCl3` for an "aromatic compound P/Q/R/S" Q) → wrong figure. The match-gate catches it.
  4. **Graph/diagram questions that MENTION compounds** (Ellingham Assertion-Reason names CO/C/O₂)
     were the worst false-positive — a molecule got drawn for a *graph* figure. Both the extract
     prompt AND the match-gate now explicitly reject non-structure figure-types even when compounds
     are named. **This was found AFTER a first attach of 115; reverted from backup + re-attached 79.**
  5. **OPSIN vocabulary boundaries** (legit yield ceiling): generic classes ("alkyl halide"),
     polymers ("polystyrene"), organometallics ("manganese decacarbonyl"), drug trade names
     ("chlordiazepoxide"). **A PubChem name→structure fallback would lift yield** — the #1 next lever.
  6. **Attach safety:** always `cp data/qbank.sqlite backups/…pre_chemfig_<ts>` first; `figure_url`
     MUST use `QBANK_PUBLIC_BASE=https://gurukul.trigunai.com/examgen` (export it) or figures 404
     when EC2 is off; generated figures saved as **`<id>.gen.png`** (distinct from recovered
     getmarks `<id>.png`) so provenance is queryable (`figure_url LIKE '%.gen.png'`) and revertible.

**Runbook (attach more / re-run):**
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 ; cd ~/question_bank_engine
export PATH=$HOME/jre/bin:$PATH
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 \
       QBANK_CHAT_MODEL=gpt-4o QBANK_VISION_MODEL=gpt-4o QBANK_PUBLIC_BASE=https://gurukul.trigunai.com/examgen
cp data/qbank.sqlite backups/qbank.sqlite.pre_chemfig_$(date +%Y%m%d_%H%M%S)
.venv/bin/python diagram_generate/generate_chem_figures.py --full --attach --workers 8   # chem pool
# triage-only (no attach): diagram_generate/triage_chem.py --limit 90
```

**Next-session start:** (1) **PubChem name→structure fallback** to lift chem yield above 12% (catches
polymers / organometallics / drug names OPSIN can't); (2) widen the `solution>40` filter + re-run
for more chem coverage; (3) **PHYSICS generate-and-verify loop** (schemdraw/SVG schematic from the
described incline/circuit config → RE-SOLVE to the known answer — this one CAN use verify-by-solving
since physics answers are numeric/deterministic, unlike chem ranking). Failed-redraw harnesses kept
in `question_bank_engine/diagram_redraw/`.

### 🛡️ INCOMPLETE-QUESTION GUARD (2026-07-24) — never serve a figure-less "as shown below" question

A banked question that references a figure it doesn't have = an unanswerable half-question →
business-critical. Defense-in-depth now enforces "never serve a question that needs a figure it
lacks", verified live (pool sampled 246 → **0 incomplete served**). Layers:
- **Detector** — `qbank/models.py`: `references_figure()` (expanded regex: figure/graph/circuit/
  "the following compound|structure|reaction|…"/Column-I-II/List-I-II) + `options_are_bare()`
  (empty, or options that are just labels `(i)(ii)`/orderings `a>b>c`) + **`is_figure_dependent(stem,
  options, qtype)`** — **qtype-aware**: integer/numeric Qs legitimately have empty options, so only
  the stem is checked (this fix cut a 5,251 false-count down to the true **1,509**). High precision.
- **Serving gate** (the guarantee) — `storage.pool_questions` + `retrieve(servable_only=True)` add
  `(COALESCE(needs_figure,0)=0 OR figure_url IS NOT NULL OR figure_svg IS NOT NULL)`: a question is
  servable only if it needs no figure OR actually carries one. Applied to the student hot path.
- **Backfill** — `diagram_generate/audit_backfill_figures.py [--apply]`: ran the detector over the
  bank, set `needs_figure=1` on **1,344 silent** figure-dependent Qs the old flag missed (so the gate
  catches them). Re-run after any big ingest.
- **Exemplars** — `generator.retrieve_exemplars` now passes `servable_only=True` so generation never
  imitates "as shown below" phrasing from figure-dependent exemplars.
- **Generation validator** — rejects any generated Q where `needs_figure or is_figure_dependent(...)`
  and no figure (`figure_svg`/`figure_url`).
- **True exposure (46,396 bank):** 1,509 incomplete, only **15 were in the servable pool** (now
  excluded); 1,344 silent (backfilled). Deployed live on Gurukul (code + `needs_figure` backfill);
  backups `qbank.sqlite.pre_figguard_*` + `qbank/*.py.bak_*`.

### ✅ FIGURE-FIRST DIAGRAM GENERATION — WIRED LIVE (2026-07-24)

The figure-first engine is now the LIVE diagram path (not just a prototype). Module **`qbank/figuregen.py`**
+ router in `generator.generate_test`: when `/generate` is called with **`require_figure=true`** and
`figuregen.can_generate(exam, subject, chapter)` (Chemistry + an organic-structure chapter), it routes to
figure-first INSTEAD of LLM-SVG. Mechanism: **55 verified exam compounds** embedded as canonical SMILES
(pre-resolved via OPSIN so the live path needs only RDKit — no Java) → RDKit renders the structure to
`figures/<id>.gen.png` + sets `figure_url` → **RDKit COMPUTES the answer** (molecular formula / stereocentres /
DoU / rings / -OH count = ground truth) → templated MCQ w/ deterministic distractors, spread answer positions.
Chapter→topic map picks relevant compounds; non-organic chapters → `can_generate=False` → falls through to
LLM. **Live-verified:** `require_figure=true` NEET-Chem-Alcohols returned `generator:"figure-first-chem"` with a
served glycerol PNG. Correct-by-construction (figure drawn by us, answer computed), copyright-clean. Batch-fill
the diagram pool by calling with `require_figure=true` across organic chapters. **NEXT plug-ins:** Maths (SymPy)
+ Physics (matplotlib/schemdraw) generators — add a builder + widen `figuregen.can_generate`. Frontend: a
"diagram practice" toggle sets `require_figure=true`; general practice lets the LLM path decide per-concept.

### 🔎 pgvector SEMANTIC REWIRE — DEPLOYED, GATED TO BATCH (2026-07-24)

`qbank/semantic.py` (fastembed bge-small-384 + connect-per-call PG) is wired into `generator.py`:
**semantic novelty** (`max_similarity` — catches reworded near-dupes TF-IDF misses; reject ≥ `SEM_MAX_SIM`,
default **0.90** via `QBANK_SEM_MAX_SIM`), **diverse exemplars** (`diversify_indices` — farthest-point sampling
over a wider candidate set), and **`upsert_embedding`** (keeps the PG novelty pool current on each accept).
All degrade gracefully to the SQLite+TF-IDF path. **KEY OPS DECISION: gated to BATCH, OFF in the live API.**
Loading fastembed inside the uvicorn worker on the 3.8G box added ~30s to the FIRST live `/generate` (stacked on
gpt-5.6 reasoning → >100s timeouts). So **`api.env` has `QBANK_SEMANTIC=off`** — live `/generate` stays light
(TF-IDF, ~9s) since it's only the power-user fallback. **For batch pool-fill, export `QBANK_SEMANTIC=on`** (a
one-time model load amortizes over thousands of Qs — where semantic novelty actually matters). Enable in the live
API only after moving to a bigger box / Azure PG (or pre-warm fastembed at startup, accepting the ~400MB resident
cost). Formal SEM_MAX_SIM calibration deferred (box too slow to run the embed job) — 0.90 is a safe conservative default.

### 🎨 FIGURE-FIRST DIAGRAM-QUESTION GENERATION (2026-07-24 prototype) — the origin of the live engine above

Rather than reproduce copyrighted exam figures, GENERATE new questions with our OWN correct figures:
draw a parametric figure → a deterministic engine COMPUTES the answer → phrase an MCQ. Figure correct
because we drew it; answer correct because computed (not LLM-guessed); copyright-clean; unlimited.
Proven across 3 subjects (`diagram_generate/`):
- **Chemistry** `generate_diagram_questions.py` — name→OPSIN/PubChem→RDKit structure; RDKit computes
  formula / stereocentres / DoU / rings / –OH. 68 correct Qs from 16 seeds.
- **Maths** `generate_math_physics_demo.py` — matplotlib graphs/geometry; **SymPy** exact answers
  (roots, area). Best-fit subject.
- **Physics** — matplotlib motion-graphs (slope=accel, area=displacement) + **schemdraw** circuits
  (series/parallel R). Per-figure-type render+solve module; graphs & circuits proven.
Also: **PubChem/LLM-SMILES fallback** (`resolve.py`: OPSIN→PubChem→LLM) recovers drug/organometallic
names OPSIN can't (chlordiazepoxide etc.), wired into `generate_chem_figures.py`. Reaction/table
rendering (`generate_rxn_table.py`) BUILT but LOW YIELD (exam reactions are multi-step/ionic; matching
tables leak the answer) — not attached broadly. **Not yet productionised into the live pool** — next
step is to seed the figure-first generator from the bank's named compounds into `/exam-prep`.

### 🩺 NEET — BUILT 2026-07-23 (all 3 subjects live)

NEET (medical entrance, NTA) = **Physics, Chemistry, BIOLOGY**. Built in one session; live on the Gurukul examgen API alongside JEE.

| `exam` | `subject` | Verified | Chapters | Worked solutions | Source |
|---|---|---|---|---|---|
| `NEET` | `Biology` | **13,961** | 38 | 100% of non-diagram | datavorous bank + `sweatSmile/neet-biology-qa` + Reja1 NEET 2024–26 images |
| `NEET` | `Physics` | **5,343** | 32 | 100% of non-diagram | datavorous bank + Reja1 NEET 2024–26 images |
| `NEET` | `Chemistry` | **13,507** | 35 | ~99% of non-diagram | datavorous bank + Reja1 NEET 2024–26 images |

**Scale-up 2026-07-23 (~1k → ~33k):** `datavorous/entrance-exam-dataset` (97k rows, ~49.7k NEET) is the grafite-equivalent for NEET — pre-tagged (subject/chapter), pre-keyed, pre-solved HTML. Ingest with `run.py ingest-datavorous --exam NEET` (no LLM: tags + keys + solutions all present; 39,054 verified after dedup). Adapter `extractor.from_datavorous_row` cross-checks the two independent key markers (`li.correct` class vs `correct_option` value text) and drops disagreements — **0 disagreements across 49,771 rows**. **Rejected alternatives:** `BruthaCool/neetjee` (122k rows but NO answer keys) and `catchshubham/neet-dataset` (corrupted — mojibake, keys contradict their own explanations).

**Taxonomies are now datavorous-derived** (`qbank/neet_physics.py`, `qbank/neet_chemistry.py` via `derive_neet_taxonomy.py --write`), replacing the JEE-Main reuse — datavorous uses NEET-specific chapter names that don't match JEE Main. This also killed the old "NEET inherits non-NEET chapters (Communication Systems)" rough edge AND the NEET→JEE-Main exemplar fallback (now self-sufficient; `EXEMPLAR_FALLBACK = {}`). Biology's 7 chapter-name variants (e.g. "Human Health and Diseases" → "…Disease") are normalised to the clean hand-authored taxonomy.

**Cross-tag cleanup:** datavorous mis-tagged 1,118 rows `subject=Chemistry` whose chapter is unambiguously Physics ("Electrostatics", "Ray Optics"…). Rule used: **the physics chapter name is truth** (dominant-subject is unreliable — Capacitance is physics but Chemistry-dominant; Biomolecules is legit in both Bio and Chem). Reassigned to Physics.

Solved with **gpt-4o**; the ~90 `solution_needs_review` flags (independent solve ≠ official key) also catch vision mis-transcriptions — adjudicating them is a quality pass, not a blocker.

- Taxonomy: `qbank/neet_biology.py` (38 NCERT chapters / 145 concepts, hand-authored — keeps the chapters rationalised out of the 2024 syllabus since older Qs still test them). Phy/Chem reuse `JEE_MAIN_PHYSICS`/`JEE_MAIN_CHEMISTRY` via `TAXONOMIES[("NEET", …)]`.
- New CLI: `run.py ingest-neet-bio` (text). Images: `run.py ingest-images --exam-prefix NEET --exam NEET --subject Biology|Physics|Chemistry`.
- `collector.SUBJECT_ALIASES` folds NEET 2024's **Botany + Zoology into `Biology`** (one subject is how students pick).
- **Companion-exam exemplar fallback** (`syllabus.EXEMPLAR_FALLBACK`): NEET Phy/Chem have only ~130/~104 real Qs over ~25 chapters — too thin to retrieve 3 same-chapter exemplars — so `generator.retrieve_exemplars` borrows **JEE Main** exemplars for empty chapters (same syllabus) and still authors at the requested NEET difficulty. `/chapters` now returns `exemplars_banked` (own + borrowed, so existing `>0` filters still work), `exemplars_own`, and `exemplar_fallback_exam`.
- **Difficulty band for NEET is 2–3** (JEE Advanced is 3–4).
- Handoff doc: `question_bank_engine/FRONTEND_HANDOFF_NEET.md`.

**⚠️ THE BUG THAT WILL BITE ANY NEW IMAGE SOURCE — option-index answer keys.** NEET papers print options as **(1)(2)(3)(4)** and Reja1 gives the key as an option **INDEX**, while JEE Advanced uses (A)(B)(C)(D) and the validator requires A–D. The first NEET image ingest therefore rejected **all 540 extracted questions** with `no_answer_key` — extraction was perfect, only the labelling differed. Fixed by `extractor.letterize_options()` (numeric labels → A–D by value; letter labels + numeric key → mapped POSITIONALLY, capped at 4 options since a 5+-option extraction is a vision mis-parse). `repair_numeric_options.py` applies the same normalisation to already-extracted rows (idempotent, dry-run by default) — it recovered 465 questions instead of repeating ~2h of vision calls. **Check labels vs key format FIRST on any new image dataset.**

**Quality (hand-audited, honest):** 25/25 sweatSmile Biology keys correct; 11/12 repaired NEET-2024 image keys correct — the 12th was a mis-transcribed *option text* from the vision model, not a bad key. ~74 diagram questions carry `needs_figure` and are excluded from auto-solving. Questions where an independent solve disagreed with the official key are flagged `solution_needs_review` (this is also what surfaces vision mis-transcriptions).

**Known rough edge:** NEET Phy/Chem inherit the JEE Main chapter LIST, which includes a few chapters no longer in the NEET syllabus (e.g. Communication Systems). A NEET-specific chapter filter is a follow-up.

**Other backlog:** (a) wire NEET **and** JEE Chem/Maths (+ JEE Main) into the student LMS `RAG_SUBJECTS`+`EXAMS` (§4 of FRONTEND_HANDOFF_NEET.md / §6 of the IIT one) + deploy `lms:vN` — **~13.3k questions are built but students can still only reach JEE Advanced Physics**; (b) adjudicate the **3 disputed keys** (Physics #42/#95, Maths 2018 f_n); (c) key-audit flag-pass over the grafite JEE-Main bank; (d) **`/pool` + `batch-generate` exist in the local repo but are NOT deployed to Gurukul** (api.py is untracked in git) — decide whether to ship them.

**Reusable grafite → new-subject recipe (proven on JEE Main Physics):** (1) `run.py ingest-grafite --subject <phys/chem/maths> --subject-name <Name> --exam "JEE Main"` (rule-based validate, verified from grafite keys); (2) derive a taxonomy: query `SELECT chapter, concept FROM questions WHERE exam=? GROUP BY chapter,concept`, build `{chapter:{keywords:[],concepts:{concept:[]}}}`, write `qbank/jee_main_<subject>.py`, register `("JEE Main","<Name>")` in `syllabus.py TAXONOMIES`; (3) push code + synced DB to BOTH EC2 and the live Gurukul host, `systemctl restart qbank-api` on Gurukul; (4) verify `/chapters` + a `/generate`. The DB is now the LIVE one on Gurukul — build on a copy, then sync back (back up Gurukul's DB first).

## 11. Gotchas

- Public IP is now a stable EIP (34.192.145.204) — no more IP chasing.
- Port 8010 is the RTX studio; qbank-api uses **8020**.
- `/tmp` on EC2 is ephemeral (wiped on stop); engine + DB live on EBS at `/home/ubuntu/` (persist).
- Background LLM jobs: nohup + `PYTHONUNBUFFERED=1`; INGEST jobs store at the END (no incremental DB update), so a crash loses the batch — `enrich-solutions`/`tag` commit per question. Never `pkill -f enrich` (matches its own shell — kill by PID).
- **Throughput**: the LiteLLM proxy does NOT serialize (6 concurrent calls ≈ same latency as 1) — the limit is per-question latency, so SHARD long jobs. Solving 800 Biology Qs went from ~2/min to ~25/min by running 8 workers via `xargs -P 8` over `--chapter`. Ingest can likewise run one process per subject.
- `retag`/`enrich-solutions`/`reverify` take `--exam`/`--subject`; **without them they sweep the WHOLE ~13k bank**.
- `storage.Store` now opens SQLite in **WAL with a 30s busy_timeout**, so a long job and the live API can share the DB instead of racing to "database is locked".
- **Figure URLs follow `QBANK_PUBLIC_BASE`** — it defaults to `rtx.trigunai.com` (the EC2 box). On Gurukul it must be `https://gurukul.trigunai.com/examgen` (now set in `api.env`), else diagrams 404 whenever EC2 is off. 60 pre-existing rows were repointed on 2026-07-23.
- LLM JSON+LaTeX corruption (`\text`→TAB) — `models.repair_latex` fixes it; apply to any LLM-authored text.
- Dataset `index` resets per paper → IDs must include content hash (already handled).
