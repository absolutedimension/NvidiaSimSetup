# Assessment Style System — concept ⟂ style (worksheet engine)

*Added 2026-08-02. Encodes the assessment-design method: a **concept** and a **style** are separate
layers. One concept × the style dials = the whole item bank; a **student type** is just a *weighting*
of the same styles (a mixing board, not separate machines). Files: `assessment_styles.json`,
`student_profiles.json`, realized in `worksheet_engine.py`.*

## The model
```
   concept (from curriculum chapter)          e.g. "addition"
              │
              ├── STYLE = 4 dials ────────────────────────────────────────────────
              │     cognitive (Bloom)  ·  DOK (Webb)  ·  representation (CPA)  ·  context
              │     one concept × these dials = dozens of legitimately different items
              ▼
   STUDENT PROFILE = weighting over styles     kids_1_2 = pictorial-heavy · board = +error_spot
              ▼
   worksheet item, tagged with its style dials → rendered by worksheet.js / printed
```

## The dials (assessment_styles.json)
| Dial | Framework | Values |
|---|---|---|
| **cognitive** | Bloom | remember → understand → apply → analyze → evaluate → create |
| **dok** | Webb DOK | 1 recall · 2 skill · 3 strategic · 4 extended |
| **representation** | CPA / Bruner | abstract · pictorial · words · story · object · table |
| **context** | — | abstract · real_object · real_life · game · exam |

## Styles shipped (one concept, many lenses)
`abstract_fact` (4×3=?) · `pictorial_count` (count objects) · `story_reallife` ("Riya has 4, gets 3…")
· `sequence_pattern` (skip-count) · `money_context` · `relational_match` · **`error_spot`** ("X wrote
4×3=7 — correct?" = misconception diagnosis). **Planned** (need new render): `reverse_relation`
(12 = 4 × ?), `assertion_reason` (board/JEE/UPSC DNA).

Each generated item carries its dials:
```json
"style": {"id":"story_reallife","cognitive":"apply","dok":2,"representation":"story","context":"real_life","concept":"add"}
```

## Student profiles (student_profiles.json) — the mixing board
A profile weights the styles; out-of-grade or non-`live` styles drop and weights renormalise.
```
kids_1_2 : pictorial 0.45 · story 0.20 · abstract 0.25 · sequence 0.10      (CPA-concrete, no abstraction yet)
kids_3_5 : abstract 0.28 · story 0.30 · pictorial 0.12 · sequence 0.13 · money 0.10 · error 0.07
board    : abstract 0.30 · story 0.25 · error 0.20 · sequence 0.15 · money 0.10   (exam-authentic + diagnosis)
jee_neet : abstract 0.30 · reverse 0.30 · error 0.20 · assertion 0.20              (higher DOK — planned styles)
upsc     : assertion 0.40 · match 0.30 · error 0.30
```
`class_to_profile` maps Class 1–2 → kids_1_2, Class 3–5 → kids_3_5 automatically. Override with `--profile`.

## Use
```bash
python3 worksheet_engine.py --board CBSE --class 2 --subject Mathematics --chapter Addition --n 8            # auto kids_1_2
python3 worksheet_engine.py --board CBSE --class 4 --subject Mathematics --chapter Multiplication --profile board --n 12
```
Verified: same "addition" concept came out as pictorial + abstract + story + compare + sequence for Class 2;
`--profile board` surfaced error-spotting ("Rohan wrote 2948+3579=6526 — correct?" → False).

## Extend (this is why it's a system, not a script)
- **New style** → add an entry to `assessment_styles.json` (dials + concepts + grade_band + `status:"live"`)
  and a realizer branch in `worksheet_engine._realize`. For `planned` styles (reverse_relation,
  assertion_reason) also add a render archetype to `worksheet.js`.
- **New student type** → add a weighting to `student_profiles.json` (e.g. `neet`, `banking`). No engine change.
- **Same layer works for the qbank/MCQ generator too** — the styles are format-agnostic; the RAG generator
  can take a style as a constraint, and `/pool` real-PYQs already give the `exam-authentic` style for free.

## Why it matters
A child who answers `2 × 3 = ?` but not "6 candies shared by 2 friends" memorised a fact, didn't own the
concept. Varying the style is how a worksheet *measures understanding* rather than recall — and doing it as
data (dials + profiles) means every concept is automatically renderable in N styles, per who's learning.
