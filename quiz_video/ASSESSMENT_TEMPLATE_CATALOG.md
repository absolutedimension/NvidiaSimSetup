# Acharya Quiz-Video — Assessment Template Catalog

> For the **daily scheduled posting** engine. Each template is a reusable video format the
> pipeline can render from a content JSON. Mix them so the feed never feels repetitive —
> the format itself becomes the hook. All share: alive voice, light soothing animated
> Acharya background, isochronic focus bed, crystal-clear typography, celebration on correct.

---

## A. STANDARD (the assessments you already use — reliable, exam-authentic)

| # | Template | Format | How it holds attention | Signature animation |
|---|----------|--------|------------------------|---------------------|
| 1 | **MCQ** (single) | 1 Q, 4 options, timer | Countdown pressure + "did I get it?" | Ticking ring, green reveal + confetti |
| 2 | **True / False** rapid | Statement → T/F, short timer | Fast, bingeable, low friction | Card flip to reveal ✓ / ✗ |
| 3 | **Fill in the Blank** | Sentence with a gap, type/guess | Curiosity gap literally on screen | Word slides into the blank on reveal |
| 4 | **Assertion–Reason** | Statement + reason, pick relation | Feels like the real JEE/NEET item | Two panels connect with a verdict badge |
| 5 | **Numerical / Solve-it** | Problem, compute the value in N sec | "Can you do it in your head?" | Working steps unfold on reveal |
| 6 | **Diagram / Image-based** | Label or read a figure | Visual, stops the scroll | Callout arrows animate to the answer |

## B. INNOVATIVE (scroll-stoppers — the "hold the student" formats)

| # | Template | Format | The hook | Signature animation |
|---|----------|--------|----------|---------------------|
| 7 | **Match the Following** ⭐ | Column A ↔ Column B, connect pairs | Brain wants to pair things; satisfying | Glowing lines draw between correct pairs one-by-one on reveal |
| 8 | **Reveal the Secret** ⭐ | Answer hidden behind tiles/blur, un-covers as timer runs | The mystery box — you MUST see what's under | Tiles dissolve / scratch-off / blur-clears to reveal |
| 9 | **Odd One Out** | 4 items, 3 share a property | "Which one doesn't belong?" is irresistible | The odd item shakes, others dim; odd one glows |
| 10 | **Sequence / Order It** | Shuffle steps, put in right order | Ranking = engagement, feels like a game | Cards slide/snap into the correct order |
| 11 | **Spot the Error** | A worked solution with 1 mistake | "Find the bug" — teacher's favourite | Red pulse locks onto the wrong step |
| 12 | **This or That** | Two options head-to-head, pick faster | Binary = instant participation | Split-screen, winner side swells + glows |
| 13 | **Rapid Fire (5-in-1)** | 5 micro-Qs, ~4 sec each, running score | Streak mechanic, "keep watching for your score" | Score counter ticks; combo flames on streak |
| 14 | **Elimination** | Start with 4, each tick removes a wrong one | Tension builds as options vanish | Options burn away until the answer stands alone |
| 15 | **Guess Before Reveal** | Progressive clues drop, answer at 0 | Sunk-cost curiosity — must see if right | Clue cards stack in; final flourish reveal |
| 16 | **Memory / Flash** | Show info 3 sec → hide → ask about it | Tests attention, dares the viewer | Content flashes then flips to the question |
| 17 | **Two Truths & a Lie** | 3 statements, spot the false one | Social-media-native format, very shareable | The lie cracks/shatters on reveal |
| 18 | **Category Sort** | Drag items into 2–3 buckets | Satisfying tidy-up, visual | Items fly into their correct bucket |

## C. SERIES WRAPPERS (structure across days, not single-video formats)

- **"Chapter in 60 seconds"** — one hard concept, 3 escalating Qs (easy → exam-level).
- **"Beat Yesterday"** — same topic, harder version; callback to prior day's post.
- **"Weak-spot Wednesday"** — the question most students get wrong (uses real Acharya miss-data).
- **"Full mock, 1 question a day"** — a 30-Q mock dripped across a month; CTA = take the full test on Acharya.

---

## Suggested weekly posting rhythm (keeps variety high)

| Day | Format | Why here |
|-----|--------|----------|
| Mon | Match the Following (#7) | Strong, elegant open to the week |
| Tue | MCQ single (#1) | Exam-authentic anchor |
| Wed | Reveal the Secret (#8) — "Weak-spot Wednesday" | Mystery + real miss-data |
| Thu | Spot the Error (#11) or Assertion–Reason (#4) | Deeper, teacher-style |
| Fri | Rapid Fire 5-in-1 (#13) | High-energy, shareable, streak |
| Sat | Odd One Out (#9) / This-or-That (#12) | Light, playful weekend |
| Sun | Numerical Solve-it (#5) | Reflective challenge |

**Every video ends the same way:** correct-answer celebration → one-line "Why" → CTA
"Get your full adaptive test on Acharya." The format rotates; the brand + CTA are constant.

---

## Build order (recommendation)

1. ✅ Engine v2 core: alive voice, light animated bg, isochronic bed, celebration, clear type.
2. ⭐ **Match the Following** (#7) — flagship innovative, elegant line-draw. *(building now)*
3. ⭐ **Reveal the Secret** (#8) — the mystery format.
4. **Rapid Fire** (#13) — streak/score mechanic for shareability.
5. Then fill out the rest from a shared template spec, one JSON per video.

Each template = one renderer function in `make_quiz_video.py` keyed by `"type"` in the
content JSON, so a day's post is just: pick type → fill content → render → schedule.
