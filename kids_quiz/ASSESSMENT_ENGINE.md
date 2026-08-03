# The Common Assessment Engine — one core for kids AND seniors

*2026-08-02. `assessment_core.py` is the SHARED, science-backed core both products import. Kids get
worksheets, seniors get MCQ — but the difficulty model, misconception library, and feedback are the
SAME engine. Grounded in the Science-of-Assessment map (rung 1). Companions:
`worksheet_engine.py`, `assessment_styles.json`, `ASSESSMENT_STYLE_SYSTEM.md`.*

## The one idea
> **Concept · style · difficulty · student are separate dials; MCQ vs worksheet is just one dial (format).**
> So ONE engine enriches every item — a Class-2 kid's count sheet and a JEE aspirant's diagnostic MCQ —
> with the three things all learning-science needs: predicted **difficulty**, misconception-tagged
> **distractors**, and process **feedback**.

## The shared contract (any item, any level)
```json
{ "type": "arith", "instruction": "...", "payload": {"op":"×","a":8,"b":7}, "answer": 56,
  "style": {"representation":"abstract","dok":2} }
```
Call `assessment_core.enrich(item)` → the item gains:
```json
{ "difficulty": 0.9, "band": 2,
  "radicals": {"digits":1,"op":"×","representation":"abstract","dok":2},
  "distractors": [{"value":15,"misconception_id":"mul_added","why":"'Times' means multiply, not add."},
                  {"value":49,"misconception_id":"mul_one_group_short","why":"You used one group too few."}],
  "hints": [{"level":"strategy"},{"level":"step"},{"level":"worked"}] }
```

## The three enrichments (rung 1 of the science stack)
| | What | Science | Function |
|---|---|---|---|
| **Difficulty** | `b` computed from **radicals** (digit count, carry/borrow, operation, representation, DOK) — *predict difficulty before serving* | Item models: radicals set difficulty, incidentals are cosmetic (Gierl & Lai) | `difficulty(item)` → `(b, radicals)` ; `difficulty_band(b)` → 1–4 |
| **Distractors** | wrong options computed by running a **named buggy procedure** on the item's own numbers → a wrong answer is a *diagnosis* | Misconception distractors / Force Concept Inventory | `distractors(item)` ; `MISCONCEPTIONS` library |
| **Feedback** | tiered **hint ladder** (strategy → step → worked → answer-last) | Hattie process-level feedback | `hints(item)` |

## How each product uses the SAME engine
- **Kids (worksheets):** `worksheet_engine.generate()` already calls `enrich()` on every item → the
  worksheet UI shows the tiered hints, the print sheet stays clean, and the difficulty/band drives serving.
- **Seniors (MCQ courses):** call `assessment_core.to_mcq(item)` → returns a diagnostic MCQ: the correct
  option + 3 **misconception-tagged distractors**, each carrying `misconception_id` + `why`. When a student
  picks a wrong option, log the `misconception_id` straight to the weak-topic dashboard. This is the upgrade
  from "MCQ-only, scored" → "MCQ, diagnostic."
```python
import assessment_core as ac
ac.enrich(item)              # difficulty + distractors + hints (both products)
mcq = ac.to_mcq(item)        # seniors: {stem, options[correct + misconception distractors]}
```

## Why it's genuinely common (not kid-specific)
`assessment_core.py` has **zero kid-specific / zero worksheet-specific code** — it operates on the generic
item contract above. The misconception library and difficulty radicals are keyed by **concept + operation**,
not by grade. Point it at a Class-2 addition item or a JEE multiplication item and it does the right thing;
harder inputs simply produce a higher `b`. It has no dependencies, so the senior qbank engine
(`question_bank_engine/`) can import it directly (or the file can be copied to that repo).

## Extend it (this is why it's an engine)
- **New misconceptions** → add `{id, name, fn(a,b)→wrong, why}` to `MISCONCEPTIONS[concept]`. For non-numeric
  subjects (EVS/GK/physics/chemistry), add a per-concept catalog of common errors (published lists exist for
  physics/maths; boards/UPSC need curating).
- **New difficulty radicals** → add a branch to `difficulty()` for a new item type (steps, transfer distance,
  distractor plausibility all raise `b`).
- **New concepts** → the arithmetic library covers add/sub/mul/div; add fractions, algebra, etc. the same way.

## Where this sits on the roadmap
This is **rung 1** (the rich item schema) — the foundation. It unlocks the rest of the Science-of-Assessment
build ladder:
- **rung 2** — per-skill mastery state (BKT + Elo) — the difficulty `b` here is what the ability estimate compares against.
- **rung 3** — the 85% controller — requests `b ≈ θ`; this engine makes `b` predictable so that request is answerable.
- **rungs 4-8** — spacing, blueprint, calibration, motivation, self-improving pool — all read the fields this engine writes.

— assessment engine (common core)
