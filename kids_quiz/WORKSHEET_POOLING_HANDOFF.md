# 🤝 HANDOFF — pool the worksheet bank (for the curriculum agent)

*From the worksheet-engine session, 2026-08-02. You built the taxonomy (75 cells ✅). Next: run the
generator across your cells to fill the worksheet BANK. The engine + driver are built and tested —
this is turnkey. Companions: `worksheet_engine.py`, `pool_worksheets.py`, `WORKSHEET_GRAMMAR.md`.*

## Division of labour
- **Worksheet session (me):** owns the ENGINE (`worksheet_engine.py`) + driver (`pool_worksheets.py`) + the render/print/pool components. Built + hardened.
- **You (curriculum):** own the DATA — run the pooling across your cells, since you know which are verified vs draft. This is your "curriculum → content" step.

## What's already done
- ✅ **Engine** — any `board/class/subject/chapter` → proper worksheet. Maths = computed (class-scaled ranges); knowledge (EVS/English/GK/Hindi) = LLM-generated, grounded on the chapter, **hardened** (validation + retry drops degenerate items).
- ✅ **All MATHS pooled already** — 15 cells × 12 items = **180 items** in `content/bank/` (ICSE/CBSE/Bihar × Class 1–5, computed, offline). Class-scaled and verified (Class 1 `10+10` → Class 5 `33965+48193`).

## YOUR job — pool the knowledge subjects (EVS / English / Hindi)
These need the LLM (litellm). Bring up the endpoint (EC2 tunnel), then run the driver:
```bash
# 1. tunnel litellm from the EC2 box (34.192.145.204) to localhost:4000
ssh -i ~/.ssh/trigunai_key.pem -N -L 4000:localhost:4000 ubuntu@34.192.145.204 &

# 2. pool everything not yet done (skips Maths [have], skips low-confidence cells, resumable)
cd kids_quiz
LITELLM_URL=http://localhost:4000/v1 python3 pool_worksheets.py --n 10

# preview first if you like:
python3 pool_worksheets.py --dry
```
- **Resumable** — already-pooled cells are skipped (re-run safely; `--force` to redo one).
- **Safety filter** — cells flagged `low-confidence` in `curriculum/index.json` are **skipped** (e.g. GK, and shaky Bihar branches). Only `--include-low` overrides — don't, unless you've verified that branch.
- **Output** — `content/bank/<board>_class<N>_<subject>.json` + `content/bank/bank_index.json`.

## Priority order (the driver already sorts this way)
ICSE first (his son) → CBSE → Bihar; within a board: Mathematics → EVS → English → GK → Hindi.
Suggested first run: `--n 10` for ICSE + CBSE EVS/English Class 1–5 (skip Bihar/GK until verified).

## Quality bar (already enforced, but eyeball a few)
The hardener rejects: match pairs with placeholder/1-char values or duplicates, cloze whose answer isn't in the bank, true/false without a bool answer, etc. Still, **spot-check 3–4 knowledge cells** — the LLM is ~90% clean; if a chapter reads oddly, its taxonomy branch may be weak (fix the cell, re-pool with `--force`).

## What NOT to do
- Don't pool the `draft`/`low-confidence` cells (Bihar, GK) until their taxonomy is verified.
- Don't touch the ENGINE files (`worksheet_engine.py`, `pool_worksheets.py`) — ping me if a generator needs changing.
- Don't wire serving into `main.py` — that's the shared collision point; coordinate (it's the last step, done with the avatar session).

## After pooling → serving (separate step, cross-session)
The bank JSON feeds the kids `/exam-prep` flow per (board, class, subject). That wiring lives in `main.py` (our collision point) — leave it; we'll do it together once the bank is filled.

— worksheet-engine session
