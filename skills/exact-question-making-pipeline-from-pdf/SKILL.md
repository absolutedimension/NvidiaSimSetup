---
name: exact-question-making-pipeline-from-pdf
description: >
  Turn an OFFICIAL exam-paper PDF into REAL, verbatim, answer-keyed questions in the TrigunAI
  question bank — NO generative AI, NO paraphrase, NO invented questions. A vision-LLM
  (Qwen2.5-VL) transcribes each printed question exactly, the correct answer comes from the
  OFFICIAL key, and the rows are stored as verified REAL questions (generated=0, verified=1)
  that serve directly to students. This is how Acharya offers "practise the ACTUAL past-paper
  questions" — distinct from the RAG generator (which authors NEW copyright-clean questions).
  PROVEN on UPSC Civil Services Prelims (517 real PYQs live). Load this skill for: adding a new
  exam/board from PDFs as REAL questions, "make real questions from this PDF", "extract past
  papers", "no generation, use the real questions", CBSE Class 10 / Class 12 (PCM + Commerce)
  board question ingestion, vision PDF extraction, answer-key matching, or serving a
  generated=0 bank. Triggers on: "real questions from pdf", "exact question pipeline", "extract
  the paper", "past paper ingest", "vision extract questions", "board questions real", "class 10
  questions", "class 12 questions", "PCM board", "commerce board", "official PYQ", "qwen extract".
  Companion to trigunai-assessment-backend-data (the qbank engine + RAG generator this feeds)
  and acharya-student-frontend (which wires the exam into the student picker).
---

# Exact Question-Making Pipeline — from PDF (REAL questions, no generation)

**Purpose.** Give students the ability to solve the **actual official questions** of an exam —
transcribed verbatim from the paper, keyed from the official answer key. **Nothing is generated
or paraphrased.** This is the opposite posture to the RAG generator in
`trigunai-assessment-backend-data` (which authors NEW copyright-clean questions). Both live in
the same bank; this pipeline produces rows tagged `generated=0, verified=1` and marked as real.

> **Proven:** UPSC Civil Services (Prelims) — 517 real PYQs (324 GS + 193 CSAT, 2023–2025) live.
> **Next:** CBSE Class 10, Class 12 PCM (Physics/Chem/Maths) + Commerce (Accountancy/BST/Econ).

---

## The 6 stages

```
① SOURCE      official PDFs only (paper + answer key)     -> ~/drop/<exam>/
② EXTRACT     Qwen2.5-VL vision -> per-question JSON       -> scripts/qwen_extract.py   (GPU box)
③ KEY         transcribe/collect the OFFICIAL answer key   -> keys.json  { TAG: {qnum: "A"} }
④ STORE       real rows, keyed, verified                   -> scripts/store_real_questions.py
⑤ CLEAN       strip duplicated option block from stems     -> scripts/clean_option_blocks.py
⑥ SERVE       let generated=0 rows serve from /pool        -> scripts/enable_pool_serving.py
                                                               + hand off wiring to frontend
```

Everything after ② runs **on the serving VM** (Gurukul `dk_trigun@20.219.2.53`,
`~/question_bank_engine`, store-of-record `data/qbank.sqlite`, API = systemd `qbank-api` on
:8020 → public `https://gurukul.trigunai.com/examgen`). ② runs on a **GPU box** (EC2 A10G).

---

## ① SOURCE — official only

Use only the exam body's own PDFs (upsc.gov.in, cbse.gov.in / cbseacademic.nic.in). You need
**two** things per paper: the **question paper** and the **official answer key / marking scheme**.
Drop them in `~/drop/<exam>/` on the box with a clear TAG per file, e.g. `2025_QP1.pdf`,
`2025_PHY_SETA.pdf`. Gotcha: `upsc.gov.in` (no www) 307-redirects and drops the path — use
`www.upsc.gov.in` + a browser user-agent when fetching.

## ② EXTRACT — vision, verbatim (`scripts/qwen_extract.py`)

Runs on the GPU box. **Use Qwen2.5-VL-7B, not gpt-4o** — general gpt-4o paraphrases
multi-statement questions and silently drops the numbered statements; Qwen keeps them intact and
renders tables as markdown. The prompt SKIPS Hindi/non-English pages (bilingual papers repeat
every question), and the script keeps the first non-empty English version per question number.

```bash
# on the GPU box (start the EC2 A10G; export HF_HOME to the big NVMe if root disk is small)
export HF_HOME=/mnt/nvme/hf
pip install --break-system-packages transformers accelerate qwen-vl-utils pymupdf pillow torch
for f in ~/drop/upsc/*_QP*.pdf; do
  python3 qwen_extract.py --pdf "$f" --out "~/drop/upsc/qwen/$(basename ${f%.pdf}).json"
done
# STOP the EC2 when done — it bills ~$1/hr.
```

Output per file: `{ "1": {number, stem, raw_options[], options{A..D}}, ... }`.

## ③ KEY — the official answer key

The answer must come from the **official key**, never from an LLM solving the question. Build
`keys.json`: `{ "<TAG>": { "<qnum>": "A|B|C|D", ... }, ... }`. Mark officially
**dropped/bonus** questions as `"X"` (the store step skips them). If the newest paper's key
isn't released yet, omit that TAG and use `--no-key-verified` (rows land `verified=0` awaiting
the key). Keys are small — transcribe them by hand from the PDF into JSON; that hand-transcription
IS the trust anchor of the whole pipeline.

## ④ STORE — as REAL verified rows (`scripts/store_real_questions.py`)

```bash
cd ~/question_bank_engine && PYTHONPATH=$PWD python3 <skill>/scripts/store_real_questions.py \
  --qdir ~/drop/upsc/qwen --keys ~/drop/upsc/keys.json \
  --exam "UPSC Civil Services (Preliminary)" --map ~/drop/upsc/tagmap.json --id-prefix upsc
```
`tagmap.json` maps each TAG → `{"subject": "...", "paper": "...", "year": 2025}`. Rows get
`generated=0`; `verified=1` only when an official key exists AND it's an auto-checkable MCQ
(the validator rule-checks). Descriptive/board long-answer rows store as `qtype=descriptive`
with the model answer as `correct_answer` (see boards note).

## ⑤ CLEAN — de-duplicate the option block (`scripts/clean_option_blocks.py`)

**The #1 display bug.** Vision models leave the full `(a)-(d)` options *inside* the stem, so the
UI shows them twice. Always run this after storing. Back up the DB first.
```bash
cd ~/question_bank_engine
cp data/qbank.sqlite data/qbank.sqlite.bak_clean
PYTHONPATH=$PWD python3 <skill>/scripts/clean_option_blocks.py --exam-like "UPSC%"
# expect: "still contain option markers after clean: 0"
```
It preserves the numbered STATEMENT lists (1./2./3., I./II./III.) — those are part of the
question — and strips a stray leading question number ("1. ").

## ⑥ SERVE — let real rows reach students (`scripts/enable_pool_serving.py`)

The frontend hot path `/pool` serves only `generated=1` by default. Two edits to
`qbank/storage.py` make a real bank serve (idempotent, mirrors the UPSC/CBSE fix):
1. **Bypass the `generated=1` gate** for your exam-name prefix.
2. **Skip the chapter filter** for your prefix IF rows are chapter-NULL (else topic-named
   frontend requests match 0 rows and fall to slow LLM generation). Drop this once you tag by chapter.
```bash
cd ~/question_bank_engine
cp qbank/storage.py qbank/storage.py.bak_serving
python3 <skill>/scripts/enable_pool_serving.py --prefix "UPSC" --skip-chapter
python3 -m py_compile qbank/storage.py && sudo systemctl restart qbank-api
```
Then verify + hand off the frontend wiring (§ Frontend handoff).

---

## Serving model & figures

- **Serving = the real PYQs, not generated.** Because you bypass the `generated=1` gate, the
  517 (or N) authentic rows serve directly. The RAG generator stays as the drain-fallback only.
- **Figure gate.** The store keeps the existing HARD serving gate: a row with `needs_figure=1`
  and no `figure_url`/`figure_svg` is NEVER served (protects against figure-less questions). For
  text/statement/table exams (UPSC) this is a no-op (0 figure questions). For **PCM boards** many
  questions reference a diagram → the extractor sets `needs_figure=1`; those rows are held back
  until a real figure is attached (recover from the source PDF page, or generate a clean own
  figure per the qbank engine's diagram-generate pipeline). **Do not solve-and-serve a
  figure-dependent question without its figure.**

## Frontend handoff (do NOT deploy the frontend from here)

This pipeline stops at "real rows serve from the API". Turning the exam ON in the student UI is
the **frontend agent's** job (skill `acharya-student-frontend`, owns the real `lms` source +
deploy). Never deploy the LMS from a stale repo. Give the frontend agent: the exam label, the
subjects, and the 6 wiring blocks (RAG_SUBJECTS, GOALS, DIFFICULTY_LADDER, EXAMS, STUDENT_EXAMS,
`_student_goal`). Template: `UPSC_FRONTEND_HANDOFF.md` in the repo root — copy its structure per exam.

## Verify (end to end)

```bash
# real rows serve from the public API (swap exam/subject)
curl -s "https://gurukul.trigunai.com/examgen/pool?exam=UPSC+Civil+Services+%28Preliminary%29&subject=General+Studies&difficulty=3&type=MCQ_single&count=3"
# -> count>0, clean stems, 4 options, correct_answer present
```
In the UI (after the frontend agent wires it): take a test, confirm each question renders once
(no double options) and grades against the official key.

---

## Gotchas (hard-won on UPSC — they WILL recur on boards)

1. **gpt-4o paraphrases → use Qwen2.5-VL.** General VLMs drop numbered statements. Non-negotiable.
2. **Option block duplicated in the stem** (64% of UPSC rows) → always run ⑤. Two layouts:
   multi-line and single-line `(a)..(d)`. The cleaner handles both.
3. **Answer key is the trust anchor** — transcribe the OFFICIAL key by hand; never let an LLM
   "solve" for the key on a real-question bank. (UPSC 2026 had no key yet → stored `verified=0`.)
4. **chapter=NULL vs topic-named requests.** Real rows often have no chapter; the frontend still
   sends topic chips → without the chapter-skip (⑥.2) every request falls to slow generation.
5. **`generated=1` gate** silently hides a real bank from `/pool`. Symptom: API returns 0, UI
   shows nothing or generates. Fix = ⑥.1.
6. **Bilingual PDFs** repeat every question in Hindi → prompt skips non-English pages + keep-first.
7. **EC2 disk / HF cache** — mount the NVMe and `export HF_HOME` before pulling the 7B model.
8. **`/tmp` is ephemeral on EC2** (wiped on stop) — keep source PDFs + JSON on EBS/home, not /tmp.
9. **STOP the EC2 GPU box** when extraction is done (~$1/hr).
10. **`sys.path[0]` gotcha** — a script file run from `/tmp` doesn't see `qbank`; run with
    `PYTHONPATH=~/question_bank_engine` (only `python3 -c` gets cwd on the path for free).

---

## CLASS 10 / 12 (PCM + Commerce) — what's different from UPSC

The pipeline is the same; boards add three wrinkles:

- **Mixed question types.** CBSE papers are not all MCQ (Sections A–E: MCQ, assertion-reason,
  1/2/3/5-mark short & long answers, case studies). The extractor captures a `qtype` and makes
  options optional; descriptive rows store with the **marking-scheme model answer** as
  `correct_answer` and `qtype=descriptive`. Auto-grading only applies to MCQ; descriptive rows
  are "solve & self/AI-check against the official model answer".
- **Figures everywhere (PCM).** Circuits, ray diagrams, graphs, geometry. Extractor flags
  `needs_figure=1`; those rows are held by the serving gate until a real figure is attached —
  recover the figure from the PDF page crop, or generate a clean own figure. Never serve a
  figure-dependent question blind.
- **Answer source = official marking scheme** (cbseacademic.nic.in publishes them per year/set).
  Transcribe MCQ keys to `keys.json`; for descriptive, store the model answer text.

Suggested first targets (highest reuse, cleanest keys): **Class 12 Physics, Chemistry, Maths**
(official marking schemes are well structured), then **Commerce (Accountancy, Business Studies,
Economics)**. One `--exam` per subject, e.g. `"CBSE Class 12 Physics"`, `--id-prefix cbse12phy`.

---

## Files

```
exact-question-making-pipeline-from-pdf/
├── SKILL.md                        # this file
└── scripts/
    ├── qwen_extract.py             # ② PDF -> per-question JSON (Qwen2.5-VL, GPU box)
    ├── store_real_questions.py     # ④ store as REAL verified rows, keyed
    ├── clean_option_blocks.py      # ⑤ strip duplicated option block from stems
    └── enable_pool_serving.py      # ⑥ patch storage.py so generated=0 rows serve
```

Ties to [[project-question-bank-engine]] (the bank + RAG generator this feeds),
[[project-acharya-student-product]] (the student funnel), and `acharya-student-frontend`
(wires the exam into the UI). Real-questions posture is the counterpart to the engine's
copyright-clean GENERATE posture — keep the two clearly separated in any bank you build.
