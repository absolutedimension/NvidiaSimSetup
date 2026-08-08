---
name: qbank-data
description: "The DATA-BACKEND agent for Acharya's exam question bank — the whole pipeline that turns raw exam sources into a clean, tagged, solved, verified question bank and serves it to the student LMS. Use whenever Deepak wants to: search HuggingFace for exam data, ingest a dataset, build/convert questions (JEE / NEET / CBSE boards), embed into pgvector, push data LIVE, wire a new exam into the student app, check bank stats, start/stop the worker VM, or fix/extend the pipeline code. Triggers: 'question bank', 'exam data', 'ingest', 'search for a dataset', 'add a subject/exam', 'build boards', 'generate questions', 'embed', 'go live / push live', 'wire X to the LMS', 'bank stats', 'the backend', 'the qbank pipeline', 'CBSE / class 10 / class 12 data', 'the worker VM'. For CODE changes to the pipeline, this skill hands off to `trigun-coding` (Codex on the Gurukul box). NOT for audio/video (studio-*) or voice calls (Maya)."
metadata: { "openclaw": { "emoji": "📚", "requires": { "bins": ["ssh","scp","az"] } } }
---

# qbank-data — Acharya's Exam Question-Bank backend

You operate the DATA layer behind Acharya's exam-paper generation. You **direct** two Azure boxes
over SSH and **report** back. You never invent a pipeline — you run the real scripts. For code
changes, you delegate to **`trigun-coding`** (Codex), already on the Gurukul box.

## Connection — `source ~/.openclaw/qbank.env` first
```bash
source ~/.openclaw/qbank.env   # sets GURUKUL, GKEY, WORKER, WKEY
# GURUKUL = dk_trigun@20.219.2.53   GKEY = ~/.ssh/gurukul_key       (LIVE serving box + Codex + the git repo)
# WORKER  = azureuser@40.80.84.87   WKEY = ~/.ssh/qbank_worker_key  (heavy batch box; DEALLOCATE when idle)
# Example: ssh -i $GKEY $GURUKUL '<cmd>'   ·   ssh -i $WKEY $WORKER '<cmd>'
```
**Worker power** goes through Gurukul (it holds the service principal — this box's az is a different tenant):
`ssh -i $GKEY $GURUKUL '~/question_bank_engine/data_prep/worker_power.sh start|stop|status'`.
Always retry ssh 3× (sshd can be slow). Heavy jobs run DETACHED (`nohup … &`) — launch, then poll the log.

## The two-box + LMS architecture (do not confuse them)
- **Gurukul VM** (`20.219.2.53`) = **LIVE serving**: `qbank-api` :8020 (public `gurukul.trigunai.com/examgen`),
  the litellm proxy :4000 (Azure: gpt-5.6-terra/sol, gpt-5.5, gpt-4o[-mini]), the **store-of-record SQLite**
  `~/question_bank_engine/data/qbank.sqlite`, Postgres+pgvector, **Codex**, and the git repo
  `~/question_bank_engine` (AGENTS.md inside). This is what students hit — treat writes as production.
- **qbank-worker VM** (`40.80.84.87`, RG `trigunai-video-creator`, sub in `WORKER_SUB`) = heavy batch:
  HF ingest, LLM Q&A→MCQ conversion, pgvector embed. Own copy of `qbank/`+`diagram_generate/`+`~/data_prep`.
  **Deallocated by default** — start it before batch work, deallocate after (it bills ~$0.25/hr).
- **LMS** (Azure Container App `lms`, repo on Deepak's Mac `NvidiaSimSetup/lms`) = the student/teacher app
  (`acharya.trigunai.com`). Wiring a new exam here is a Mac-side code + `az containerapp` deploy (see below).

## The pipeline (search → ingest → convert → embed → LIVE)
Each step is a real command. Report progress; back up before live writes.

1. **Search** a source: `ssh $GKEY $GURUKUL 'python3 ~/question_bank_engine/data_prep/hf_search.py <keywords>'`
   → HF datasets that carry an answer key + ≥200 rows. Audit keys before trusting (bad datasets exist).
2. **Start the worker** (needed for 3–5): `ssh -i $GKEY $GURUKUL '~/question_bank_engine/data_prep/worker_power.sh start'`
   (and `… stop` to deallocate, `… status` to check). This uses the service principal on Gurukul.
3. **Ingest** (on worker, no LLM for pre-keyed sources): `run.py ingest-datavorous --exam <NEET|JEE Main|JEE Advanced>`
   (datavorous) / `ingest-grafite` / `ingest-neet-bio`. For CBSE boards, **convert** NCERT Q&A→MCQ:
   `diagram_generate/ncert_qa_to_mcq.py --dataset KadamParth/NCERT_… --exam "CBSE Class 12" --subject Physics`
   (or `~/data_prep/run_boards.sh` for all 4 board subjects). gpt-4o-mini is fine for board conversion (~$3 total).
4. **Embed**: on worker `diagram_generate/pg_migrate.py && diagram_generate/pg_embed.py` (additive, resumable).
5. **Go LIVE** (worker → student bank): export the exam's rows on the worker
   (`data_prep/export_exam.py "<exam prefix>"`), scp to Gurukul, then on Gurukul `data_prep/sync_live.py`
   (backs up first) + `sudo systemctl restart qbank-api`. Verify `curl …/examgen/chapters?exam=…&subject=…`.
6. **Deallocate** the worker when done.

## Wire a new exam into the student LMS (so students can PICK it)
On Deepak's Mac repo `NvidiaSimSetup/lms`: add the subject(s) to `app/examgen.py` **RAG_SUBJECTS** (exam+subject
must EXACTLY match the bank, e.g. `"CBSE Class 12"/"Physics"`), add a **GOALS** entry, add a **DIFFICULTY_LADDER**
band (boards = `2/2-3/3`), and in `app/main.py` flip the exam to `available: True` in **STUDENT_EXAMS** + point
its **EXAMS** `subject` at a real RAG id. `python3 -m py_compile app/*.py`, then
`az acr build --registry trigunaicr --image lms:vN . && az containerapp update -n lms -g trigunai-video-creator
--image trigunaicr.azurecr.io/lms:vN` (bump N). **Verify in a real browser** — a green API is not proof. New
DB columns need an ALTER in `seed._migrate`. (Full detail: the `acharya-student-frontend` skill on the Mac.)

## Code changes → hand to `trigun-coding` (Codex)
The pipeline is a git repo on the Gurukul box (`~/question_bank_engine`, AGENTS.md inside). To change/extend it
(new adapter, fix a bug, add a bot command), invoke **`trigun-coding`** pointed at that repo ON the Gurukul box
(Codex there is wired to gpt-5.6-terra via the litellm proxy). After a code change: restart `qbank-api`
(engine) or `qbank-bot` (bot), and `./sync_to_worker.sh` for anything the worker runs. Commit with git.

## Current state (2026-07-25)
- **Banks LIVE (~78k verified):** JEE Advanced + JEE Main + NEET (Phys/Chem/Maths|Bio) · **CBSE Class 10 Science
  + Class 12 Physics/Chemistry/Biology (15,195, wired into the LMS).**
- **Board Maths: NOT built** — HF has no CBSE-aligned maths (only generic word-problem sets). Do it by
  GENERATION (SymPy-verified), not ingest.
- **CBSE has no pre-generated pool** → student tests fall to slow live `/generate` (~40s/Q). Next win:
  batch-generate a CBSE pool on the worker for instant serving.
- A Telegram command-bot (`qbank-bot` on Gurukul) also drives this pipeline; you are the agentic version of it.

## Safety (non-negotiable)
- The Gurukul SQLite is the LIVE student bank — **always `cp data/qbank.sqlite backups/…` before bulk writes.**
- **≤4 concurrent requests to `/examgen`** (it shares the 3.9 GB Gurukul box with the live WhatsApp tutor).
- Never commit `*.sqlite`, `data/`, `figures/`, `backups/`, or `*.env` (secrets).
- Audit answer keys before trusting a new source. Deallocate the worker when idle.
