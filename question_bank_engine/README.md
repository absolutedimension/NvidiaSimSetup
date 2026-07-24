# TrigunAI Question Bank Engine — Phase 1

An **agentic pipeline** that turns raw exam sources into a **clean, de-duplicated,
validated internal question bank**. The bank is the foundation the exam-generation
engine (RAG + generation + validation) is built on. This phase builds and proves
the *ingestion → clean bank* half.

```
collector → extractor → keymatch → cleaner → validator → store
```

| Agent | File | Job |
|---|---|---|
| **Collector** | `qbank/collector.py` | HYBRID sourcing: auto-pull open datasets (HuggingFace API) + scan a manual `drop/` folder for PDFs. (Official NTA/CBSE auto-download plugs in here with the same contract.) **No coaching/aggregator scraping.** |
| **Extractor** | `qbank/extractor.py` | Raw source → structured `Question`. Dataset rows: rule-based split of inline `(A)/[A]/[\mathrm{A}]` options. PDFs: gpt-4o vision → structured questions. |
| **Keymatch** | `qbank/keymatch.py` | Attach official answer keys (separate PDF) by question number. Never guesses answers. |
| **Cleaner** | `qbank/cleaner.py` | Normalize LaTeX/whitespace; flag duplicates (exact hash + TF-IDF near-dup). Dupes are flagged, never deleted. |
| **Validator** | `qbank/validator.py` | Quality gate: rule checks (1 correct answer, answer∈options, non-empty…) + optional LLM semantic check. Only clean questions get `verified=True`. |
| **Store** | `qbank/storage.py` | SQLite (local/demo) → Postgres+pgvector (prod, `schema_postgres.sql`). |

## Run it (offline, rule-based — no setup)

```bash
cd question_bank_engine
QBANK_LLM=off python3 run.py ingest-dataset --limit 80   # real JEE Advanced Physics
python3 run.py stats
python3 run.py sample -n 3
```

Proven on real data (`daman1209arora/jeebench`, JEE Advanced 2016–2021 Physics):
120 questions ingested → 120 clean & verified, 4 question types, idempotent re-runs
(re-ingesting does **not** double the bank).

## Turn on the LLM (semantic validation + PDF extraction)

The pipeline degrades gracefully without an LLM. To enable it, install the client
and point at the TrigunAI LiteLLM/Azure proxy:

```bash
pip install openai pymupdf scikit-learn requests
# SSH-tunnel the EC2 proxy locally (or point at the Gurukul VM):
#   ssh -i ~/.ssh/trigunai_key.pem -L 4000:localhost:4000 ubuntu@$EC2_IP
export QBANK_LLM=on
export QBANK_LLM_BASE_URL=http://localhost:4000/v1
export QBANK_LLM_API_KEY=sk-trigunai-master-key-2026
python3 run.py ingest-dataset --limit 40
```

## Ingest your own papers (manual-drop path)

```bash
cp jee_main_2024_physics.pdf question_bank_engine/drop/
export QBANK_LLM=on   # PDF extraction needs the vision model
python3 run.py ingest-drop --exam "JEE Main" --subject Physics --year 2024 \
    --key jee_main_2024_key.pdf
```

## Phase 2 — Tagging agent (DONE)

Tags every clean question with `chapter / concept / difficulty(1-5) / bloom_level`,
constrained to a syllabus taxonomy (`qbank/syllabus.py` — the knowledge-graph seed).
LLM-first (syllabus-constrained classification + calibrated difficulty); keyword
fallback so it runs offline. This is what makes retrieval possible.

```bash
python3 run.py tag                       # tag untagged verified questions
python3 run.py query --chapter "Modern Physics" --difficulty 3-4 --type MCQ_single -n 5
python3 run.py query --chapter "Thermodynamics & Kinetic Theory" -n 3
```

Proven: 120 real JEE questions tagged into 16 chapters + concept level (offline
keyword mode), difficulty 2–5. `query` retrieves by tag — the exam-generator's read
path. Turn on `QBANK_LLM=on` for concept-level accuracy + calibrated difficulty +
Bloom, and to classify the ~5% the keyword pass leaves `Unclassified`.

## Phase 3 — Generator (DONE)

The RAG exam-generation loop (`qbank/generator.py`):

```
retrieve tagged exemplars → author a NEW question (LLM) → validate (well-formed +
answer-correct) → NOVELTY-check vs the bank → store (generated=True) → assemble test
```

The **novelty gate** (`NOVELTY_MAX_SIM=0.82`, TF-IDF cosine) is the copyright-clean
guarantee: any generated question too similar to a real banked question is rejected
and regenerated. The engine learns the pattern; it never resells the paper.

```bash
# See the RAG prompt built from real exemplars (offline, no LLM call):
python3 run.py generate --chapter "Modern Physics" --difficulty 3-4 --type MCQ_single --show-prompt

# Real generation (needs the LLM):
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 QBANK_LLM_API_KEY=sk-trigunai-master-key-2026
python3 run.py generate --chapter "Modern Physics" --difficulty 3-4 -n 5 --out tests_out/mp.json

# Offline plumbing demo (NOT real physics — proves retrieve→validate→novelty→store→assemble):
python3 run.py generate --chapter "Modern Physics" -n 3 --mock
```

Output is a self-contained test JSON: `spec`, `questions` (fully tagged), `answer_key`,
`exemplars_used`, and a `rejected` log. Generated questions are flagged `generated=True`
and excluded from the exemplar pool so the engine never trains on its own output.

## What's NEXT

- **Turn on the LLM** (`QBANK_LLM=on` + SSH tunnel to the proxy) for real generated questions + concept-accurate tagging.
- **Embeddings** — populate `embedding` (pgvector) so exemplar retrieval is semantic, not just tag-filtered.
- **Test-series orchestrator** — compose many tests across a blueprint (topic weighting, difficulty curve, full mock papers).
- Scale to Chemistry/Maths, then NEET/boards (one taxonomy each in `syllabus.py`).

## Legal posture

Collected questions are an **internal reference corpus** to learn patterns/difficulty.
The *sold* product generates fresh, validated questions — it does not resell past
papers. Sources are official bodies + open datasets + what you legally hold. We do
not scrape copyrighted coaching platforms.
