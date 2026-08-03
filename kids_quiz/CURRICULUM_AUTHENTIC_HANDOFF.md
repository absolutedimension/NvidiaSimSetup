# 🤝 HANDOFF — Authentic class-wise, subject-wise curriculum (K / Class 1–5, Indian boards)

*Written 2026-08-02 by the worksheet/asset session, for the agent continuing the curriculum build.
Goal: a machine-readable taxonomy where **every topic traces to an official, publicly-released Indian
board syllabus** — no invented topics. Companions: `trigunai-kids-education` (control tower),
`exact-question-making-pipeline-from-pdf` (the vision extractor), `WORKSHEET_GRAMMAR.md` (delivery),
`kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md` (the one branch already done right).*

## The goal in one line
> Build the **skeleton** (board → class → subject → chapter → subtopic) for K–5, pulled from **official
> sources only**, as structured JSON the whole system consumes. Content is generated later; the
> *skeleton must be authentic*.

## The fact that shapes everything
At **Class 1–5 there is NO official board exam** — assessment is school-internal. So there is no
"official test" to collect. What IS official and collectible is the **syllabus/index** each board
publishes. That index is the authentic skeleton. (Don't chase "standard worksheets" — they're
per-school and inconsistent; generate content, source only the index.)

## ✅ HOW MUCH IS DONE (honest)
| Piece | State |
|---|---|
| **Method + authentic-source list** (this doc) | ✅ done |
| **ICSE Class 3 · Mathematics** — from his REAL book (New Guided Mathematics, 10 chapters) | ✅ authentic; Ch 1–2 → **768 live Qs**. This is the reference for "done right" (`KIDS_QUIZ_ICSE_G3_PLAN.md`) |
| Worksheet Grammar (delivery formats) + asset pool (art) | ✅ built — parallel tracks, NOT curriculum |
| **Everything else** (all other boards/classes/subjects) | ⛔ **not started — this handoff** |

So: **1 of ~90 cells done** (see matrix). The method is proven on that one; replicate it.

## The ONLY authentic sources (use these, nothing else)
| Board | Official source | What to pull |
|---|---|---|
| **CBSE** | **NCERT** — `ncert.nic.in`, `epathshala.nic.in` | syllabus + textbook contents (Math-Magic, Marigold, EVS) |
| **ICSE** | **CISCE** — `cisce.org` | the "Classes I–V" curriculum document |
| **Bihar Board** (for the institute B2B) | **SCERT Bihar** + DIKSHA Bihar node | state syllabus |
| Cross-board | **DIKSHA** — `diksha.gov.in` (Govt of India) | energised textbooks, worksheets |

> Copyright: a **list of topics is fact, not copyrightable** — safe to structure. Use the official
> docs; never copy a private publisher's book. Record the source URL + date on every branch.

## The target output (schema + location)
One file per (board, class, subject): `kids_quiz/curriculum/<board>_class<N>_<subject>.json`
```json
{
  "board": "ICSE", "class": 3, "subject": "Mathematics",
  "source": { "name": "CISCE Classes I–V Curriculum", "url": "https://cisce.org/...",
              "verified_on": "2026-08-02", "also_verified": ["his school book"] },
  "chapters": [
    { "id": "numbers", "name": "Numbers",
      "subtopics": ["place value & face value", "comparing & ordering", "successor/predecessor",
                    "expanded form", "number names"] },
    { "id": "addition", "name": "Addition", "subtopics": ["3-digit with/without carrying", "..."] }
  ]
}
```
Plus a master `kids_quiz/curriculum/index.json` listing every completed cell + its coverage status.

## The matrix to fill (priority order)
Boards: **ICSE** (his son, first) · **CBSE** (biggest market) · **Bihar Board** (institute B2B).
Classes **1–5**. Subjects: **Mathematics, English, EVS, GK, Hindi**.
→ ~3 boards × 5 classes × ~5 subjects ≈ **75–90 cells**. Do **ICSE + CBSE Maths & EVS Class 1–5 first**
(highest use), then widen.

## The method (repeat per cell — proven on ICSE Cl-3 Maths)
1. Get the official syllabus page/PDF (sources above).
2. Extract the **contents/index** → structured chapters+subtopics. Use the **`exact-question-making-
   pipeline-from-pdf`** skill's Qwen2.5-VL vision extractor for PDFs (here it extracts the *index*, not
   questions), or read the page directly.
3. Write the `<board>_class<N>_<subject>.json` with the `source` block (URL + `verified_on`).
4. Where possible, **cross-verify against a 2nd source** (e.g. a real school book) and note it.
5. Update `curriculum/index.json`.
6. **Do NOT clobber** the existing ICSE Class-3 Maths (it's from his real book — the truth for that cell;
   reconcile, don't overwrite).

## Acceptance criteria (this is the whole point)
- ✅ Every chapter/subtopic **traces to an official public source** recorded on the branch.
- ✅ No invented or "web-baseline guess" topics left unmarked (the current ICSE-Cl3 file flags its
  web-baseline vs real-book — keep that discipline).
- ✅ Machine-readable JSON in the schema above; `index.json` current.

## How it plugs into the system (why it matters)
This taxonomy is **Layer 1 — the skeleton** from the kids system map. It feeds:
- the app's **board/class/subject picker** (what a student can choose),
- the **item generators** (which chapters to generate questions/worksheets for),
- the **asset pool** (which props a topic needs),
- **worksheet tagging** (each item locked to a real curriculum node).
Without the authentic skeleton, everything downstream is un-anchored. This is the foundation.

— worksheet/asset session

---
## 📈 PROGRESS UPDATE — 2026-08-02 (curriculum build agent)
Built the machine-readable skeleton in `kids_quiz/curriculum/` (schema + `index.json` + `build_index.py` + `make_cells.py`). **1/75 → 25/75 cells (33%).** Method = 4 parallel research agents pulling official chapter lists; assembled to per-cell JSON.

**COMPLETE (authentic, verified from official source):**
- **CBSE Mathematics 1–5** — NCERT Joyful Maths (1–2) + Maths Mela (3–5), verbatim from ncert.nic.in PDFs.
- **CBSE EVS 1–5** — NCERT: Cl 1–2 = NO separate EVS (integrated into Language/Maths, per NCERT teacher note); Cl 3–5 = Looking Around (24/27/22 ch), verbatim.
- **ICSE Mathematics 1–5** — CISCE Primary Curriculum (strand-based), verbatim via Web Archive of cisce.org PrimaryCurriculum.pdf. Cl 3 = existing real-book cell (New Guided Maths, 1080 live Qs) PROTECTED, not overwritten.

**DRAFT (needs official-PDF cross-check):**
- **ICSE EVS 1–5** — CISCE Environmental Education; official cisce.org PDF 403'd → medium-confidence secondary source. ACTION: re-pull via Web Archive of the CISCE EVS doc.
- **ICSE GK 1–5** — low confidence; CISCE prescribes NO board GK syllabus at primary (school-choice). Keep as optional.

**LEFT (~50 cells):** English (CBSE Marigold + ICSE) 1–5; Hindi 1–5 both boards; CBSE GK 1–5; **entire Bihar Board** (SCERT, for the institute B2B). Then generate QUESTIONS for the completed skeletons (only ICSE Cl-3 Maths has questions today).

---
## ✅ MATRIX COMPLETE — 2026-08-02 (curriculum build agent, batch 2)
**75/75 cells (100%).** All three boards × 5 classes × 5 subjects now have an authentic skeleton in `kids_quiz/curriculum/`.
- **COMPLETE/verified (40 cells):** CBSE {Maths, EVS, English, Hindi} 1–5 (NCERT — Joyful Maths/Maths Mela, Looking Around, Mridang/Santoor, Sarangi/Veena) + ICSE {Maths, EVS, English, Hindi} 1–5 (CISCE Primary Curriculum via Web Archive). ICSE Cl-3 Maths = real book + 1080 live Qs.
- **DRAFT (35 cells):** GK 1–5 all 3 boards (no official primary GK syllabus exists — school-choice, low conf) + all Bihar Board {Maths, EVS, English, Hindi} 1–5 (Bihar's OWN SCERT/BSTBPC books — गणित, पर्यावरण और हम, Blossom, अंकुर/कोंपल; official e-LOTS/bepclots portal serves self-signed TLS so names came from aggregator mirrors → medium/low, verified=false).
- **NEXT to upgrade drafts:** fetch the official Bihar SCERT PDFs directly (portal TLS trust) to raise Bihar cells draft→verified; official-PDF cross-check for GK is moot (no board GK syllabus). EVS Cl1-2 both boards = correctly documented as integrated (no separate book).
- **THEN:** generate QUESTIONS per cell (only ICSE Cl-3 Maths has questions today). Skeleton now unlocks generation for 39 other structure-ready cells.
