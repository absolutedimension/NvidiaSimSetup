# RAG vs Fine-tune — which authors better JEE Physics questions?

A fair, reproducible A/B on the **live bank** (120 verified JEE Advanced Physics Qs).
Both arms author NEW questions against the **same 8-chapter specs** and pass the
**same validator + novelty gate**; an **independent strong judge** (gpt-4o) grades them
blind. The only variable is the *method*.

```
                       specs.json  (8 chapters x 4 = 32 target Qs)
                      /                                    \
   Arm A: RAG + prompting                        Arm B: fine-tuned model
   retrieve 3 real exemplars ->                  LoRA-SFT'd on the 120 Qs ->
   prompt base model -> validate                 prompt (NO exemplars) -> validate
   -> novelty gate                               -> novelty gate
                      \                                    /
                       judge.py  (gpt-4o, blind, solves-then-grades)
                       physics_correct | jee_authentic | difficulty_match
                       | distractor_quality | key_correct_rate | novelty
```

## Files
| File | Role |
|---|---|
| `prepare_data.py` | bank -> `ft_train.jsonl` (SFT pairs) + `specs.json` + `bank_stems.json`. **Offline, already run.** |
| `train_lora.py` | QLoRA SFT of a Qwen base on the 120 Qs (A10G, ~mins) -> `artifacts/lora-qwen/` |
| `gen_rag.py` | Arm A — RAG generation (needs LLM proxy) -> `out_rag.json` |
| `gen_ft.py` | Arm B — fine-tuned generation (A10G) -> `out_ft.json` |
| `judge.py` | blind gpt-4o scoring + `--report` comparison table |
| `run_on_ec2.sh` | orchestrates the whole thing on the box |

## Run (on the A10G box, proxy up)
```bash
cd question_bank_engine/experiments/rag_vs_finetune
python3 prepare_data.py
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 QBANK_LLM_API_KEY=sk-trigunai-master-key-2026
python3 gen_rag.py                       # Arm A
BASE_MODEL=Qwen/Qwen2.5-7B-Instruct python3 train_lora.py   # ~5-10 min
FT_MODEL_DIR=artifacts/lora-qwen python3 gen_ft.py          # Arm B
python3 judge.py out_rag.json artifacts/scored_rag.json
python3 judge.py out_ft.json  artifacts/scored_ft.json
python3 judge.py --report artifacts/scored_rag.json artifacts/scored_ft.json
```

## How to read the result — and the honest caveat

**Data-size reality:** 120 examples is a *style/format* LoRA, not knowledge transfer.
It teaches the model the house JSON+LaTeX shape and JEE phrasing; it cannot teach new
physics. Standard SFT needs ~500–1000+ clean pairs before a fine-tune reliably beats a
strong base + RAG. So on THIS data the expected outcome is **RAG ≥ fine-tune**, and the
real value of running it is (a) a credible baseline number and (b) a harness that
re-runs automatically as the bank grows.

The decisive columns:
- **key_correct_rate** — the correctness gate. If a method's marked answers are wrong,
  nothing else matters. RAG usually wins here (exemplars anchor the physics).
- **jee_authentic** — the one place fine-tune can surprise, if the 120 Qs have a strong
  house style the base model lacks.
- **novelty** — LOWER is better (more original). Watch the fine-tune arm: with little
  data it tends to regurgitate; the novelty gate rejects those, so a high rejection
  count on Arm B *is* the overfitting signal.

**Decision rule:** fine-tune is only worth shipping if it beats RAG on `jee_authentic`
AND ties on `key_correct_rate` AND its novelty is not worse. Otherwise keep RAG and
re-run this after scaling the bank to ~1k Qs (Chemistry+Maths+more years).
