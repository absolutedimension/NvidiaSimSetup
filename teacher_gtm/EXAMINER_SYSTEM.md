# The Examiner System

> How to turn an official exam announcement into practice papers you can defend, for **any** exam.
> Written from the BSSC Inter Level run (Advt 02/23-A), where following it found **30 defective
> questions and 5 wrong answer keys** that every automated check had passed.

The goal is not "generate questions". It is to do what a commission's paper-setter does: start from
the notified syllabus, source real material, enforce the pattern, and refuse anything that cannot
be defended. The system below is the checklist that behaviour turns into.

---

## 0. The one idea

**Every claim on the paper must be traceable to a document, and every claim that can be checked by
solving must have been solved.**

Everything else follows. The 30 defects we removed all failed one of those two tests, and *none*
of them failed a structural test — they had four options, a valid key letter, matching numbers
across languages. Structure tells you a question is well-formed, not that it is right.

---

## STAGE 1 — Authority

**Get the official advertisement. It is the only source for pattern and syllabus.**

Not a coaching site, not a YouTube summary, not memory. For BSSC that meant pulling
`02_23A_Advt.pdf` from bssc.bihar.gov.in and reading all 17 pages.

What to extract, and it is always these things:

| | BSSC Inter Level example |
|---|---|
| Question count | 150 |
| Marks scheme | +4 correct, **−1 wrong**, 600 total |
| Duration | 2h 15m |
| Options per question | 4 (**BPSC TRE uses 5** — never mix) |
| Sections and their names | सामान्य अध्ययन · सामान्य विज्ञान एवं गणित · मानसिक क्षमता जाँच |
| Per-section counts | **not stated** — so 50/50/50 is our assumption, and must be labelled as one |
| Language rule | bilingual; **English prevails if the two differ** |
| Qualifying marks | 40% GC down to 32% SC/ST/women/PwD |
| Anything unusual | **open-book: three board textbooks allowed** |

> The last row matters more than it looks. Reading the whole advertisement is what surfaced the
> open-book rule — a fact most competitors do not lead with, and a real teaching differentiator.

**Trap:** a stale skill file said this exam was "cancelled". It had been re-advertised, applications
had closed, and 25,311 vacancies were pending. *Always re-check the live notice board.*

---

## STAGE 2 — Syllabus as a gate, not a suggestion

Write the syllabus down topic by topic, then **turn it into code that rejects**.

BSSC's maths list is arithmetic only — number system, fractions, percentage, ratio, average,
interest, profit & loss. It does **not** name algebra, trigonometry, mensuration or probability.
Our bank, sourced from a clerk exam with a wider paper, was full of them: **34% of the maths pool
had to go.**

Two things this teaches:

1. **Tags cannot do this.** `tag.type = "arithmetic"` contained a Pythagoras problem;
   `"percentage_profit_loss"` contained a circle-area question wearing a percentage costume. The
   gate must read the question text.
2. **Deny-list, not allow-list.** A wrongly-kept question is a syllabus error on a student's paper;
   a wrongly-dropped one costs nothing when the pool is large.

Implementation: `paper_common.inter_level_maths_ok()`.

---

## STAGE 3 — Section integrity

**A question belongs to the section the syllabus puts it in.** Two failures we caught:

- A **circle-geometry** question tagged "General Studies" bypassed the maths gate entirely. The
  content gate now applies to GS too — but *not* to General Science, where physics legitimately
  discusses angles, circles and volume.
- When the real Science+Maths pool ran short, the builder **topped it up from the reasoning
  generator** — putting a number analogy in the maths section. Shortfall is now carried into the
  reasoning part instead, so every question stays where it belongs.

Also: the Inter Level prelim has **no Hindi Language section**. Our first paper had 33 of them.
The syllabus, not habit, decides the parts.

---

## STAGE 4 — Provenance of the answer

**An answer is a claim. It needs a document behind it, and a human who has read that document.**

Measured on this run:

| Key type | Machine read accuracy |
|---|---|
| Handwritten grid (Advt 0111) | **39 of 100 letters WRONG** |
| Typeset grid | near-perfect — but see below |

Cropping and 3-vote majority got the handwritten key to 10 wrong / 25 skipped. Still nowhere near
what "the commission's own answer key" has to mean. **They were all transcribed by hand.**

The subtler lesson came from the typeset keys. For one paper we hand-checked Q1–50, got 50/50, and
trusted the rest. Reading pages 2 and 3 later found **five wrong letters in Q51–150**. The other
three typeset keys, read fully, had **zero** errors.

> **A key page nobody has read is an unverified claim, however typeset it looks.**

Two mechanics worth copying:
- Many keys print a **DESCRIPTION column** with the answer text. That lets you cross-check the
  letter against your own option text — free verification.
- Keep the human read in a file (`VERIFIED_KEYS.json`) that names the source page, not as an edit
  buried in the data. `apply_verified_keys.py` re-applies it after any re-extraction and refuses if
  the underlying text has changed.

---

## STAGE 5 — Answerability

**A question must be answerable from what is printed on the page.** Categories that fail, all found
here:

- points at a **table or figure** we do not have ("how many triangles are in the following figure")
- a **passage fragment** — "(32) ____ range of flora", "which of the statements above is incorrect",
  "what is being discussed in the context of boys"
- **match-the-columns with the columns missing**
- **Assertion–Reason with no assertion and no reason** — just the rubric and four generic options
- options that are **duplicates**, or a bare option letter as the text
- **a verified key pointing at a factually wrong option.** Ambedkar's birth date was keyed to
  14 मार्च; the key matched the commission page exactly and "14 अप्रैल" was option B — so the
  OPTION extraction was wrong, not the key. Nothing structural can see this; only someone who
  knows the fact can.
- stems whose **LaTeX collapsed**: `(x+2)/(x+3) > 1` printed as `x + 2 x + 3 > 1`

---

## STAGE 6 — Bilingual fidelity

Both languages must pose the **same** question.

- **Numbers must match** between the two stems, and **between paired options**. This caught a
  generated question reading "coded by **twice** its position" in English and plain "position" in
  Hindi — a different answer for a Hindi-medium student — and one real question printing English
  options `29, 9` beside Hindi `−42, −14`, where the keyed letter was right in one language and
  wrong in the other.
- **Route by script, never by field name.** Measured across 497 pairs, the extractor's own language
  labels were right only 59% of the time, swapped 12%, Hindi-in-both 27%.
- **Require a true pair** — Devanagari in one field, Latin in the other. Where the English was lost
  and Hindi sat in both, the Hindi was an unchecked machine translation; one printed a "climate
  change" stem over four 1919 dates.
- Reject **mixed scripts**: `बAREफुट` (Latin inside Devanagari), `किलो그램` (Hangul spliced in).

### The Hindi read is a SEPARATE pass, and it finds things nothing else can

20 of the 68 excluded questions were found only by reading the Hindi against the English, line by
line. Every one of them left the numbers, the option count and the key untouched, so every
automated check passed them:

| English says | Hindi said | Effect |
|---|---|---|
| from **innermost** to outermost | सबसे बाहरी परत से (from the outermost) | direction reversed — Hindi answer is the reverse of the key |
| **how many** Indian states (key: Three) | किन राज्यों (**which** states) | asks for names, key is a number |
| 5 men or 8 **women** | 5 व्यक्ति या 8 **कार्य** (8 works) | unsolvable |
| first 20 **odd** natural numbers | प्रश्न 20 **विभिन्न** (20 different) | different question |
| **dividend** is 2200 | **भागफल** (quotient) 2200 | different problem |
| A is 10th **from the left**, B 9th **from the right** | left/right dropped entirely | unsolvable |
| selling price | मूल्य मूल (original price) | key is the selling price |
| an **odd** positive integer | एक **विशेष** (special) पूर्णांक | condition changed |
| grapes | अमरूद (guava) | wrong noun |
| Non-cooperation Movement | गैर-सम **Cooperation** आंदोलन | Latin word inside the Hindi |

Read it as a CONVERGING loop, not one pass: 17 defects found, then 3 in the replacements, then 0.
Budget two or three rounds. Some of it can be gated afterwards — a Latin word standing between
Devanagari words, or प्रश्न where प्रथम/प्रति belongs — but the semantic ones (reversed direction,
changed quantifier) can only be read.

**Where OCR quality differs by subject, treat the subjects differently.** Devanagari maths came
back ~90% clean (numbers and standard terms); science ~50% corrupt (नाइट्रोजन चक्र → नैतिकता चक्र);
GS proper nouns were fatal (बैकुंठनाथ शुक्ला → बंकिमनाथ झा). We promoted maths only.

---

### Three more gates the GS sweep added

- **Out-of-syllabus TOPICS, not just out-of-syllabus words.** A spreadsheet SUMIF question and an
  NLP/tokenization question both slipped a filter that only knew software names. Gate the topic:
  computing, protocols, machine learning.
- **Questions from a section this exam does not have.** Our source papers include full English
  sections; those questions get tagged General Studies and land on a paper whose syllabus has no
  English part. An antonym question is a fine question in the wrong exam.
- **Stale current affairs.** "Who is the Vice-President of India" was correct when set in 2025 and
  is wrong now. A date-anchored version ("who became the 52nd CJI on 14 May 2025") stays true.
  **Never reuse a present-tense office-holder question.** This class does not appear as a defect in
  the source paper at all — it simply expires, and no structural check will ever flag it.

---

## STAGE 7 — Assembly

- **Blueprint from the real papers**, not from intuition. Mine the topic mix from the extracted
  papers and fill to it. Without this the shuffle alone gave 11 blood-relation questions in 50.
  Bihar-specific content measured **0–17%**, not the 30–40% that had been assumed.
- **No repeats within a paper, and none across the series.** Keep a ledger of what each set
  consumed (`InterLevel_sets_used.json`); later sets exclude what earlier ones took.
- **Dedup generated questions by concept + numbers + options**, not by stem text. The generator
  varies the actor ("A boy" / "Sita") while keeping the numbers, and the Hindi template carries no
  name at all — so two such questions are identical in Hindi.
- **Spread by concept**, but let the cap bend rather than return a short section.
- **Label provenance on the page.** Generated questions carry an asterisk in the key and a note
  under the section heading. If a paper mixes real and generated, say so.

---

## STAGE 8 — Verification, in three layers

**Layer 1 — structural, automated, exhaustive** (`test_papers.py`): count, numbering, key entries,
key letter present among options, four options everywhere, no raw LaTeX, no mixed script,
cross-language number and option agreement, no repeats within or across sets.

**Layer 2 — independent re-solve.** For anything computable, re-derive the answer from the question
text with code written *without reference to the generator*, and compare. 39 of ~89 generated
questions re-solved and agreed. This is a second derivation, not a restatement.

**Layer 3 — a human works the paper.** The only thing that catches the rest. Every one of the 30
defects came from here. Budget it; it is not optional.

**What defect rates to expect** (measured, and useful for planning):

| Where | Defect rate |
|---|---|
| Best source paper (Field Assistant 03/25) | **0.8%** |
| Office Attendant 02/22 | 8.7% |
| **8th Level 2024** | **22% — dropped wholesale** |

> When defects cluster in one source, drop the source. A 22% measured rate on defects that are only
> findable by solving implies many more not yet found. That paper contributed 32 questions; it was
> not worth a wrong answer in front of students.

Record every finding in `EXCLUSIONS.json` with the arithmetic that proves it, so it is fixed
permanently instead of rediscovered.

---

## Applying this to a new exam

1. Find the official advertisement; extract the table in Stage 1.
2. Encode the syllabus as a rejection gate (Stage 2) and the section map (Stage 3).
3. Source real papers + their official keys from the same site. **Hand-read every key page.**
4. Extract, then run Stages 5–6 as gates.
5. Assemble to a mined blueprint with a ledger (Stage 7).
6. Run all three verification layers (Stage 8) and budget the human pass.

**What is already reusable as-is:** `paper_common.py` (rendering, quality gates, bilingual checks),
`test_papers.py` (the battery), `apply_verified_keys.py`, `apply_text_corrections.py`,
`promote_maths_hindi.py`, and the set-ledger mechanism.

**What is exam-specific and must be rewritten each time:** the syllabus gate, the section map, the
blueprint, and the cover page.

---

## Honest limits of the system

- **It cannot verify a fact.** That Ambedkar was born in April, not March, is not derivable from
  the paper. A verified key pointing at a factually wrong option means the *option extraction* is
  wrong, and only a human who knows the fact will notice.
- **Current affairs go stale.** "Who is the Vice-President" was correct in the 2025 source paper
  and is wrong now. Time-sensitive questions need a freshness rule.
- **Hindi wording is machine-verified on numbers only.** No native speaker has reviewed it.
- **The human pass does not scale** — it is the binding constraint on how many sets can be
  produced, not question supply.
