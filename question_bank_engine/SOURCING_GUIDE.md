# Manual Sourcing Guide — JEE Physics question bank

## What's already in the bank (as of 2026-07-23)

- **Exam:** JEE Advanced only  ·  **Subject:** Physics only
- **Years:** 2016–2023 (Paper 1 + Paper 2)
- **Depth:** 120 questions — a *subset* from the open `jeebench` benchmark dataset,
  NOT the full papers (~15 Qs/year vs ~36 actually asked).

**So collect from here, in priority order.**

## Priority collection list

| # | Target | Why | Rough size |
|---|---|---|---|
| 1 | JEE Advanced Physics **2024 + 2025** | latest years, totally missing | ~72 Qs |
| 2 | **Complete** JEE Advanced Physics 2016–2023 | fill the gaps jeebench skipped | ~170 Qs |
| 3 | JEE Advanced Physics **pre-2016** (2010–2015) | depth for pattern learning | ~200 Qs |
| 4 | **JEE Main** Physics (all recent years/shifts) | different, higher-volume exam | thousands |
| 5 | Chemistry, Maths (both exams) | expand subjects | large |

## Where to get them (legitimate, free, authoritative)

- **JEE Advanced** → **jeeadv.ac.in** → "Archive" section → past **Question Papers**
  AND **Answer Keys** (both papers, per year). Official, clean PDFs.
- **JEE Main** → **jeemain.nta.nic.in** / **nta.ac.in** → "Question Paper" +
  "Final Answer Key" per session/shift.
- **NCERT** (ncert.nic.in) → exemplar problems, for foundational/board-aligned items.
- Also check **HuggingFace / Kaggle** for already-parsed sets before OCR-ing PDFs
  (search "JEE Advanced 2024", "JEE Main physics") — saves the extraction step.

> Avoid coaching-site PDFs (Allen/Aakash/PW/etc.) for the *sold* product — copyright.
> Official bodies + NCERT + open datasets only.

## What to download for each paper

For every year/paper collect **TWO** PDFs:
1. the **question paper** (e.g. `jee_adv_2024_paper1_physics.pdf`)
2. the **answer key** (e.g. `jee_adv_2024_paper1_key.pdf`)

The answer key is separate — the engine joins answers to questions by number.

## How to ingest what you find (engine is live on EC2)

```bash
# on the EC2 box: /home/ubuntu/question_bank_engine
# 1. drop the PDFs
cp jee_adv_2024_paper1_physics.pdf drop/

# 2. ingest (uses gpt-4o vision to extract; needs the LLM, already on)
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 QBANK_CHAT_MODEL=gpt-4o
python3 run.py ingest-drop --exam "JEE Advanced" --subject Physics --year 2024 \
        --key jee_adv_2024_paper1_key.pdf

# 3. tag the new questions, then they're generatable
python3 run.py tag
python3 run.py stats
```

That's it — extract → keymatch → clean → validate → store → tag, all automatic.
New questions immediately become exemplars the generator API can draw from.

## Just hand me the PDFs

Easiest path: drop the PDFs in `question_bank_engine/drop/` (or send them) and I'll
run the ingest + tag + verify and report how many clean questions landed.
