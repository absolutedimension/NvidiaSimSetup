---
name: bssc-test-prep
description: >
  Control tower for the BIHAR govt-exam test-paper line — BSSC CGL, BSSC Inter Level and
  BPSC CCE — built for One Step Education (Patna) and every Bihar institute after them.
  Owns the end-to-end pipeline that turns OFFICIAL commission PDFs into real, BILINGUAL
  (Hindi+English), officially-keyed questions, mines the exam's pattern from those papers,
  and assembles authentic full-length practice papers. Load this for ANY work on: BSSC or
  BPSC question sourcing, the vision-extraction pipeline, answer-key matching, exam pattern
  or blueprint mining, Hindi/bilingual question generation, or building a BSSC/BPSC paper
  for an institute. Triggers on "BSSC", "Bihar SSC", "Inter Level", "BSSC CGL", "BPSC CCE",
  "Bihar exam paper", "bilingual question paper", "extract question paper", "exam pattern",
  "blueprint", "One Step paper". Companion to trigunai-assessment-backend-data (the general
  qbank engine) and acharya-student-frontend (which serves the papers).
---

# BSSC / BPSC test-paper line

> **Why this exists.** One Step Education (Patna) — our first institute to say yes — asked for
> full-length practice papers for **BSSC CGL**, **BSSC Inter Level** and **BPSC CCE**, in **Hindi**,
> for their students. Everything here serves that.
>
> **Status 2026-08-20 (evening).** §10 is DONE. **16 official papers, 1,744 real questions**, of
> which **1,588 carry an answer key transcribed BY HAND from the commission's own Model Answer
> pages** (the machine read of those keys was 40% wrong — gotcha #16).
>
> **The number that matters: real General Studies usable for a CGL / Inter-Level / clerk paper went
> from 259 to 631.** That is **12 papers** with a fresh 50-question REAL GS section, up from 4.
> Also new: **295 real Mathematics** questions (there were none before).
>
> ⚠️ **The 11 new papers are ENGLISH-ONLY in practice.** Their Hindi is extracted but QUARANTINED in
> `stem_hi_unverified`, because vision cannot read Devanagari on these 2016-18 scans well enough to
> put in front of a Bihar student (gotcha #15). The five 2022-25 papers are unaffected and remain
> bilingual. **A bilingual full-length paper must still be built from those five.**
>
> **▶ NEXT JOB: get the Hindi for the new papers** — either a stronger Indic OCR (Qwen2.5-VL on the
> T4, already proven for Indic PDFs in `exact-question-making-pipeline-from-pdf`) or Azure Document
> Intelligence. Everything else is in place; `page_hi` is recorded on every question, so it is a
> re-read of known pages, not a re-extraction.

---

## 1. The three exams — get these right, an owner will know

| | **BSSC Inter Level** | **BSSC CGL** | **BPSC CCE** |
|---|---|---|---|
| Body | Bihar Staff Selection Commission | BSSC | Bihar **Public Service** Commission |
| Level | Class 12 (10+2) | Graduate | Graduate — **officer cadre** |
| Posts | Clerk, Steno, DEO | ASO, Planning Asst, Auditor | SDM, DSP, BDO |
| Vacancies | ~26,000 | 1,883 | ~1,250 |
| Prelims Q | 150 | 150 | 150 |
| **Marks** | **600 (4 each)** | **600 (4 each)** | **150 (1 each)** |
| **Negative** | **−1** | **−1** | **−0.33** ⚠️ *confirm — sources disagree* |
| Duration | 2h 15m | 2h 15m | **2h** |
| Structure | 3 parts × 50 | 3 parts × 50 | **single GS paper, no sections** |
| Options | **4**, `(a)(b)(c)(d)` | 4 | 4 |

**BSSC three parts (official order):** भाग-I सामान्य अध्ययन (1-50) · भाग-II सामान्य विज्ञान एवं गणित
(51-100) · भाग-III सामान्य बुद्धि परीक्षण (101-150).

**BPSC prelims is screening only** — marks do not count toward final merit. Say so on the paper.

**BPSC TRE uses 5 options (A–E)** including "More than one of the above" / "None of the above".
BSSC uses 4. **Never mix the two in one paper.**

---

## 2. ⚠️ There is NO Inter Level question paper — but the exam is LIVE and pending

**Verified against the commission's notice board on 2026-08-20.** Full sourced write-up:
**`teacher_gtm/BSSC_INTER_LEVEL_FACTSHEET.md`**; official PDFs in
`question_bank_engine/drop/bssc_official/`.

- **1st Inter Level** (Advt 06060114) — exam ~2016-17, paper never posted.
- **2nd Inter Level** (Advt 02/23 → **02/23(A)**) — **NOT cancelled.** It was re-advertised in
  revised form on 27.09.2025. Applications ran 15.10.2025 → **16.02.2026**, and vacancies grew
  23,175 → 24,492 → **25,311**. **The prelim has still not been held and no date has been announced**
  — the last notice on this advertisement is 13.02.2026, six months before this check.

So there is still no past paper to sell, but the reason has changed: the exam is *upcoming*, not
dead. That is why institutes are asking for Inter Level material right now.

**Never say "Inter Level previous year questions".** The closest real substitutes are **Advt 02/25
Welfare Organiser & LDC**, **Advt 0111 Clerk (Group D→C)**, **Office Attendant 02/22** and the
**10th/8th Level 2024** papers — same or adjacent level, same format. The source advertisement
number is printed on our paper, so the claim stays checkable.

### The official prelim scheme (from `02_23A_Advt.pdf`) — our paper matches it
150 questions · **+4 / −1** · **600 marks** · **2h 15m** · 4 options · bilingual, and **if the Hindi
and English versions differ the ENGLISH question prevails**. Three sections: सामान्य अध्ययन ·
सामान्य विज्ञान एवं गणित (**मैट्रिक level**) · मानसिक क्षमता जाँच. The advertisement does **not**
fix a per-section count — 50/50/50 is our assumption, not an official rule.

⭐ **The prelim is an OPEN-BOOK exam** (Rules 2010 clause 12): candidates carry **three textbooks**,
one per section, NCERT/BSEB/ICSE board textbooks only — no guides, photocopies, notes or devices.
Name and roll number must be written on each book and nothing else. This should shape how the
material is taught, and most competitors do not lead with it.

⚠️ **Two syllabus facts that contradict our current bank:** the official maths list is
**arithmetic only** (number system, fractions, percentage, ratio, average, interest, profit & loss)
— **no algebra, trigonometry or mensuration** — yet our maths stock from Advt 0111 contains AP,
polynomials and circle geometry, which are ABOVE this syllabus. And **भूगोल sits under General
Science**, not GS. Filter accordingly before building an Inter-Level paper.

---

## 3. What we have (2026-08-19)

Local: `question_bank_engine/drop/bssc/` (22 PDFs, 141 MB) · VM: `~/bssc_in/` on Gurukul.

| Paper | Q | Hindi | Officially keyed |
|---|---|---|---|
| LDC / Welfare Organiser 02/25 *(inter-level equivalent)* | 50 | 50 | 50 |
| BSSC 10th Level 2024 | 97 | 97 | 97 |
| BSSC 8th Level 2024 | 100 | 100 | 99 |
| Office Attendant 02/22 | 100 | 100 | 100 |
| Field Assistant 03/25 | 150 | 150 | 148 |
| **TOTAL** | **497** | **497** | **494** |

Each `<paper>_KEYED.json` holds: `stem`, `stem_hi`, `options`, `options_hi`, `correct_answer`
(official), `number`, `page`, `tag{section,type,topic,difficulty,bihar_specific}`.

**Not yet in the live bank.** Storing needs: `BSSC` in `examgen.RAG_SUBJECTS` + `GOALS`, the
`real-serve` allowlist in `storage.pool_questions`, and the `stem_hi`/`options_hi` columns
(added to `models.py`/`storage.py` on 2026-08-19) deployed to the VM.

---

## 4. The pipeline

```
bssc.bihar.gov.in/NoticeBoard.htm   (905 PDFs; grep for प्रश्न पत्र / आदर्श उत्तर)
   └─ curl download            ⚠️ SSL chain fails in urllib — USE CURL
        └─ extract_bssc.py     vision, BILINGUAL, hosted gpt-4o (NO GPU NEEDED)
             └─ official key   vision-read आदर्श उत्तर grid → {q_no: letter}
                  └─ match     <paper>_KEYED.json
                       └─ tag_bssc.py   classify → mine per-exam blueprint
                            └─ build_*_paper.py   assemble the PDF
```

**Scripts** (repo root `question_bank_engine/`):

| Script | Does |
|---|---|
| `extract_bssc.py` | One paper → bilingual questions. `--dpi 220`, retries thin pages |
| `bssc_batch.py` | All paper+key pairs, one at a time, writes `BATCH_SUMMARY.json` |
| `tag_bssc.py` | Tag every question, then mine a blueprint **per exam** |
| `teacher_gtm/build_bssc_paper.py` | 150-Q BSSC paper PDF (3 parts, 600 marks, −1) |
| `teacher_gtm/build_bpsc_paper.py` | 150-Q BPSC paper PDF (single GS, 150 marks) |

**Runbook** (Gurukul VM — the vision model is hosted, so no GPU):

```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
cd ~/question_bank_engine
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://127.0.0.1:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 QBANK_VISION_MODEL=gpt-4o
setsid nohup ~/run_bssc_batch.sh > ~/bssc_in/batch.log 2>&1 < /dev/null &
```

⏱ ~25 s/page. A 150-Q paper ≈ 5 min, ~$1 of vision calls.

---

## 5. 🔴 GOTCHAS — every one cost real time

1. **The commission's SSL chain fails in Python.** `urllib` throws `CERTIFICATE_VERIFY_FAILED`
   on all 24 PDFs. **Use `curl`.**
2. **Every paper is a SCAN.** Zero text layer; the few with one carry garbage OCR
   (`"Roll No. (ktL) II II n II"`). Vision is the only route.
3. **The papers are BILINGUAL and the generic prompt mis-reads that.** `extractor.from_pdf`
   returned **2 questions from a page holding 5**, treating the Hindi and English halves as
   ambiguous. `extract_bssc.py`'s prompt states the layout explicitly → **5/page**, and it is
   also what gives us `stem_hi`/`options_hi` for free. **Never fall back to the generic prompt.**
4. **LaTeX gets eaten by JSON.** The model writes `\frac` unescaped, `json.loads` turns `\f` into
   a form feed, and the option becomes `\x0crac{...}`. Run every string through
   `models.repair_latex`.
5. **Hindi options get silently replaced by the English ones.** Require them in the prompt AND
   **drop `options_hi` unless it is the same length as `options`** — a mismatched pair desyncs a
   bilingual paper without any error.
6. **Never average blueprints across exam types.** Pooling 5 structurally different papers produced
   "Reasoning 3.8%", which describes no real exam. **One blueprint per exam.**
7. **A GK-only topic taxonomy buries half a paper in "Other."** These papers are ~30% Hindi
   language, ~25-30% maths. The taxonomy must carry language and maths topics.
8. **`SET_A` in a filename is the booklet series, not the exam.** Identify the exam from the
   surrounding notice text on the notice board, not the filename.
9. **🔴 `content_hash` collapsed EVERY Hindi question into one.** `normalize_for_hash` stripped all
   non-ASCII, so every Devanagari stem normalised to `""` and hashed to the SHA-1 of nothing — the
   dedup layer would have silently discarded the entire Hindi bank as duplicates. FIXED
   (`models.py` keeps `\u0900-\u097f`); English hashes unchanged. **Re-check this if hashing is
   ever touched.**
10. **The extraction's language FIELDS are unreliable — route by SCRIPT.** Measured across 497
    pairs: only **59% correct, 12% swapped, 27% Hindi in BOTH fields**. Rendering by field name
    printed some questions twice and others back-to-front. `build_onestep_paper.split_lang()` decides
    by Devanagari detection and prints each language once. **Any new renderer must do the same.**
11. **Test a generator with a real store.** `quantgen.generate_test` calls `store.upsert` and dies on
    `None`; pass a null-object store when measuring capacity.
12. **Render every paper to an image and LOOK at it.** The duplicate-language bug was invisible in the
    JSON and obvious on the page.
13. **🔴 The vision API DOWNSCALES the image, so `--dpi` is not the lever — CROPPING is.** Measured on
    a 2016 scan: a whole page at 220 dpi and the *same page at 450 dpi* produced equally hallucinated
    Devanagari, because both get resized to the same budget before the model sees them. Cropping the
    page into 3 overlapping horizontal bands fixed the stems outright. Any time transcription quality
    is the problem, cut the image up; do not just raise dpi.
14. **🔴 The 2016-18 booklets are FACING-PAGE bilingual, not side-by-side.** Even PDF page = English,
    odd = Hindi, with the SAME question numbers (p24 = English Q72-78, p25 = Hindi Q72-78). Feeding
    those to `extract_bssc.py`'s side-by-side prompt is actively harmful: it is told each question
    appears twice on the page and to merge, so on a one-language page it invents a translation or
    fuses two consecutive questions. Use `extract_bssc_paired.py`, which reads each page
    monolingually and merges by question number, routing by SCRIPT (gotcha #10 again).
15. **🔴 Hindi from the 2016-18 scans is NOT shippable, and is quarantined on purpose.** Bands fix the
    stems but proper nouns and technical vocabulary still come back wrong — बैकुंठनाथ शुक्ला →
    बंकिमनाथ झा, बादलों की तड़ित झंझा → बालों की ताजगी. All four hosted models (gpt-4o, gpt-5.5,
    gpt-5.6-terra, gpt-5.6-sol) fail identically, so this is not a prompt or model-choice problem.
    `extract_bssc_paired.py` therefore writes `stem_hi_unverified` / `options_hi_unverified` and
    leaves `stem_hi` / `options_hi` EMPTY, so no builder can print it by accident. The ENGLISH from
    the same pages is verbatim and safe. Promote with `--hindi-verified` only after a real review.
16. **🔴 Handwritten answer keys: vision got 39 of 100 letters WRONG. Transcribe them by eye.**
    The keys for Advertisement 0111 (GK, Maths, Hindi) are handwritten. Measured against a hand
    transcription of GK1 page 29: whole page = 39 wrong; 2x2 tiles = 9 wrong but 19 rows skipped;
    tiles + 3-vote majority = 10 wrong, 25 skipped. Nothing came close to what "the commission's own
    answer key" has to mean. Every key is now transcribed by hand into
    `question_bank_engine/drop/bssc/VERIFIED_KEYS.json` and applied by `apply_verified_keys.py`.
    **Typeset keys are fine** — a 50-answer check of the LIVE One Step paper (Field Assistant 03/25,
    typeset) matched 50/50, so the five 2022-25 papers were never affected.
17. **The commission's notice board links to files that 404, and its filenames are case-sensitive.**
    `01010116-MA-GK.pdf` and `01010116-QB-Hindi.pdf` are linked but genuinely absent — which is why
    the 01010116 GK paper has no key. There is no `JE-0411-MA-*` key file at all; the JE keys live in
    the 2018 re-publications `Advertisement/gk.PDF`, `civil.PDF`, `mechanical.PDF` — **uppercase
    `.PDF`; the lowercase spelling returns 404.**

18. **🔴 `--pin` did NOT reproduce a delivered paper, and said nothing.** `gen_sig` deliberately
    ignores the actor name so that "Neha is the daughter of Sunil" and "Priya is the mother of Amit"
    count as one question — which makes it a signature of the question's SHAPE, not of the question.
    `load_generated` shuffles then keeps the first clone per signature, so which concrete question a
    signature resolves to depends on the seed: **measured 31 of 307 signatures resolved differently
    across two draws.** A pinned rebuild of Set 2 therefore came back with the same 150 shapes,
    different names and letters — still 150 correct questions, no longer the file the institute was
    holding, and no warning. FIXED: the manifest now stores `gen_full` (the generated questions in
    full) and `--pin` restores those; both delivered sets now rebuild **byte-identical**. If a pin
    ever prints "BY SIGNATURE — not exact", the paper it produces is not the paper you verified.

19. **A verification sheet must be read OUT of the delivered file, never rebuilt alongside it.**
    `key_from_delivered.py` parses the paper's own printed key and question blocks, so row 47 of the
    sheet is question 47 of the PDF in the reader's hand by construction. Two things this caught:
    a re-derived ordering drifts silently past the renderer's skip-an-unrenderable-question branch,
    and a loose option-subset fallback **mis-attributed ten questions to a Hindi paper they had
    nothing to do with**. A wrong citation is the one defect that destroys the sheet's purpose, so
    the matcher refuses to guess: it reports an untraced row instead. Cross-check it against
    `build_onestep_paper.py --key-json` — the two paths agree on all 150 rows of Set 1.

---

## 6. Measured findings — two of these OVERTURNED my own earlier claims

**Per-exam blueprint** (`drop/bssc/BSSC_BLUEPRINT.json`, and on the VM at `~/bssc_in/`):

| Paper | n | Bihar | Avg diff | GS | Maths | Hindi | English | Reasoning |
|---|---|---|---|---|---|---|---|---|
| LDC/Welfare 02/25 | 50 | **0%** | 1.78 | 36% | 16% | 2% | **32%** | — |
| Field Assistant 03/25 | 150 | 15% | 1.89 | **51%** | 20% | — | — | 11% |
| 10th Level 2024 | 97 | 12% | 1.44 | 37% | 28% | **31%** | — | — |
| 8th Level 2024 | 100 | **17%** | 1.47 | 39% | **31%** | 27% | — | — |
| Office Attendant 02/22 | 100 | 5% | 1.53 | 44% | 30% | 19% | — | — |

- ❌ **"BSSC needs 30-40% Bihar content" was WRONG.** Measured **0-17%, ~11% overall**. That is BPSC's
  emphasis, not BSSC's. A generated paper at 14% was already ABOVE the real exam. Do not chase this.
- ❌ **"We generate harder than the real exam" was WRONG.** I compared a pool *label* ("2-3") against a
  measured difficulty. Measuring our generated questions on the SAME 1-5 scale: reasoning **1.45**,
  quant **1.90**, GK **1.05** vs real papers **1.44-1.89**. They already match. The only outlier is GK,
  which is EASIER than the real papers.
- ⚠️ **The generators IGNORE the difficulty argument** — `diff=1` and `diff=3` return byte-identical
  questions. The band is a label stamped at storage time, nothing more. Changing a ladder value
  changes nothing real.
- ⚠️ **SSC pools are EMPTY below band 2-3.** Requesting "1-2" returns zero questions and silently
  produces an empty paper. Check pool depth before changing any band.
- **Language sections are the real content hole:** Hindi 19-31% of three papers, English 32% of the
  LDC paper. Bigger than Bihar ever was. `hindigen` now covers Hindi; English has `englishgen`.
- **Arithmetic is the single largest topic in every paper** (12-16%) — more than any GK topic.
- **High-yield topics (in every paper):** Current Affairs (National) · Indian Polity · Static GK ·
  Science & Technology · Sports · Environment.

### Taxonomy lesson (cost a full re-tag)
Listing the same concept on BOTH the `type` and `topic` axes made the model put the real answer in
`type` and fall back to `"Other"` for `topic` — 46% unclassified. Fixed by DERIVING topic from type
in `tag_bssc.effective_topic()` (no re-tagging needed; the data was already right) → **2-8%**.
Blueprints must be **per exam**: pooling five structurally different papers produced "Reasoning 3.8%",
an artifact describing no real exam.

## 6b. What is LIVE (2026-08-20)

| Piece | State |
|---|---|
| `qbank/hindigen.py` — 9 builders (तत्सम-तद्भव · समास · संज्ञा · विलोम · पर्यायवाची · मुहावरे · उपसर्ग · प्रत्यय) | **live**, routed in `generator.generate_test`, ~155 distinct |
| `bssc-hindi` → **हिंदी (BSSC)** in `RAG_SUBJECTS` + **BSSC goal** + `_TEACHER_GOALS` | **live `lms:v154`** |
| `BSSC` difficulty ladder `1 / 1-2 / 2` | live (label only — see §6) |
| `models.py` + `storage.py` `stem_hi`/`options_hi`/`solution_hi` columns | **live on Gurukul** |
| `reasoninggen` — all 13 builders emit Hindi | live |
| `teacher_gtm/OneStep_BSSC_150.pdf` + `build_onestep_paper.py` + `onestep_logo.png` | built |

### How many unique papers we can actually make — UPDATED 2026-08-20

| Section | Source | Papers |
|---|---|---|
| Reasoning | `reasoninggen`, computed answers | **unlimited** |
| Maths | `quantgen` computed + **295 REAL** | **unlimited** (Hindi NOT done) |
| Hindi | `hindigen`, 155 distinct | 4 |
| **General Studies** | **REAL only — 631 questions** (was 259) | **12** ← still binding, but 3× |

**English-only vs bilingual is now the binding distinction, not GS volume.** All 372 of the new GS
questions are English-only until the Hindi is recovered. So:

- **Bilingual papers: still limited by the five 2022-25 papers** (259 GS) → ~5 papers.
- **English-only papers: 12.**

⚠️ The old "212" figure was a stale count; measuring the same five papers with the current servable
filter (English stem + 4 options + official answer) gives **259**. The 631 is on that same basis.

- **100% real, zero repeats: 1 paper** (Reasoning+English real stock is only 33).
- **4 papers** with a fresh REAL 50-question GS section + generated Reasoning/Maths/Hindi.
- Beyond 4, GS repeats or must be RAG-generated — **and GS is the one section we should NOT
  generate freely**, because its answer is a model's factual claim, not a computed result.
- **⇒ More real GS is the only thing that raises the ceiling. That is why §10 matters.**

---

## 7. Copyright posture — this is the moat, do not trade it

**Use:** official commission PDFs (government works, published free) · our own compute-the-answer
generators · RAG generation over our own bank.

**Do NOT use:** publisher books (Chakshu, EduGorilla, YCT), competitor PDFs (Prepp, Testbook,
Adda247), or YouTube transcripts as question sources. Their compilations are their copyright, they
are our competitors, and the whole pitch is *"asli, verified, copyright-clean."* One breach makes
Rohan's line false.

**Narrow exception, already precedent:** an answer **letter** is a fact, not expression — the TRE
keying used third-party sites for the letter only, never their explanation text. That is for keying
a question we hold from an official source, not for acquiring questions.

**Legitimate research:** reading a book or a competitor's material to learn format, question types
and Hindi phrasing. Buy the paperback (₹192) for that; Kindle is DRM'd and blocks nothing useful.

---

## 8. Bilingual generation (the other half)

Real papers give bilingual questions. **Generated** questions need Hindi templates:

- `qbank/reasoning_hi.py` — Hindi vocab + `possessive()` (**का/की/के must agree with the
  RELATION's gender**: विकास **की** माता, विकास **के** पिता — getting this wrong is the first thing
  a Hindi reader notices).
- `qbank/reasoninggen.py` — **all 13 builders emit `stem_hi`/`solution_hi`** ✅ DONE 2026-08-19.
  Word options map via `hi_opts` AFTER `_mcq` shuffles, so Hindi and English option order match.
- `qbank/quantgen.py` — 23 builders, **Hindi NOT done** (~1.5 days, same mechanical pattern).
- `models.Question` + `storage` carry `stem_hi` / `options_hi` / `solution_hi` ✅.

**This is not translation.** The generators COMPUTE the answer, so the Hindi is a second template
over the same computation — a number or option cannot drift between languages. **Never
machine-translate the bank.**

---

## 9. NEXT (highest value first)

1. **Hand-verify ~15 answers** against the official key PDFs. Vision read both; a systematic misread
   would be silent, and "official key" is a claim you cannot walk back.
2. **Store the 497 into the live bank** — RAG_SUBJECTS/GOALS/real-serve + push the `*_hi` columns.
3. **Lower BSSC generation difficulty to band 1-2** (finding §6).
4. **Blueprint-driven assembly** — generate to the measured per-exam mix, capped at 2 per template.
5. **Quantgen Hindi** (~1.5 days) → fully bilingual BSSC paper.
6. **Missing reasoning builders** the real papers use and we cannot generate: calendar, coded
   inequality, dice, seating arrangement, syllogism, figure series.
7. **Get a real Inter Level paper** — only from One Step's own material or a student's copy.

**Related:** `trigunai-assessment-backend-data` (qbank engine) · `acharya-student-frontend`
(`/teacher/mock` serves these) · memory `[[project-srb-govtjob-bank]]`,
`[[project-hindi-question-content]]`, `[[project-one-step-education]]`.

---

## 10. ✅ DONE — the remaining papers are extracted (2026-08-20)

**Result.** 11 more papers extracted, keyed and tagged. Bank is now 16 papers / 1,744 questions.

| Paper (advertisement identified from the KEY page, not the filename) | Q | EN servable | Officially keyed |
|---|---|---|---|
| GK Booklet — **Advt 0111** Clerk, Rajkiyakrit High School | 100 | 100 | 99 |
| GK Kara Mishrak — **Advt 12010116** | 100 | 100 | 99 |
| GK & Numerical Ability — **Advt 18010116** Utpad Rasayan Parikshak | 150 | 149 | 150 |
| Asst Teacher GK — **Advt 01010116** | 147 | 138 | **0 — key is a dead 404** |
| JE GK/GS — **Advt 0411** | 100 | 100 | 100 |
| Maths — **Advt 0111** | 100 | 100 | 100 |
| Hindi — **Advt 0111** | 100 | **4** | 100 |
| JE Civil / JE Mechanical — **Advt 0411** | 100 + 100 | 100 + 100 | 99 + 99 |
| Chemistry — **Advt 18010116** | 150 | 137 | 146 |
| Pharmacy — **Advt 12010116** | 100 | 100 | 100 |

**Three papers did not deliver what the old §10 table assumed:**

1. **`01010116-QB-GK` has no answer key and cannot be served.** The commission links
   `01010116-MA-GK.pdf` but the file 404s. 147 good English questions, zero answers. Usable for
   blueprint mining only. (`01010116-QB-Hindi.pdf` is 404 too, which strands `01010116-MA-Hindi.pdf`
   — a key with no booklet.)
2. **`hindi1.PDF` is a HINDI-ONLY booklet** — the Hindi *subject* paper, so its questions are printed
   only in Devanagari. With Hindi quarantined, 96 of its 100 questions have no readable stem, so it
   contributes nothing servable and must be EXCLUDED from the blueprint (it otherwise reports
   nonsense like "96% Bihar-specific", because the tagger was handed empty strings).
3. **Chemistry, Pharmacy, JE Civil, JE Mechanical are post-specific technical subjects.** They tag as
   "General Studies" only because the taxonomy has no better bucket. **Do not count their 414
   questions toward the GS pool** for a CGL/Inter-Level paper — that would inflate the headline
   number four-fold with chemistry and civil-engineering content no clerk candidate will ever see.

### The scripts this produced (all in `question_bank_engine/`)

| Script | Does |
|---|---|
| `extract_bssc_paired.py` | FACING-PAGE booklets → monolingual page reads merged by question number, in overlapping bands. Hindi quarantined unless `--hindi-verified` |
| `bssc_batch2.py` | Drives the 11 papers; supports a key living in the SAME pdf (`"self"` + page) and a question-page range per paper |
| `apply_verified_keys.py` | Overwrites `correct_answer` from the hand-transcribed `drop/bssc/VERIFIED_KEYS.json` and stamps provenance |
| `verify_bssc_paper.py` | Per-paper gate: gaps, duplicates, servable, keyed, key-letter-matches-an-option + renders a source page to LOOK at |
| `drop/bssc/VERIFIED_KEYS.json` | **1,050 answers transcribed by eye** from 10 Model Answer pages |
| `drop/bssc/PDF_STRUCTURE_FULL.json` | Every page of all 15 PDFs classified: question pages, key pages, cover, OMR, rough work |

---

## 10b. Historical — what the job looked like before it was done

All 22 official PDFs are already downloaded to `question_bank_engine/drop/bssc/`. Five papers are
done; **12 files / 325 pages remain**. This is the single highest-value task: it is the only thing
that raises the number of genuinely-real papers (§6b).

| File | Pages | Note |
|---|---|---|
| `CHEMISTRY_M.A.PDF` | 71 | booklet **+ model answer in the same PDF** |
| `G.K_and_N.A_M.A.PDF` | 49 | GK + Numerical Ability, **+ model answer** |
| `GK(3649).PDF` | 32 | Kara Mishrak GK, **+ model answer** |
| `GK1.PDF` | 30 | GK booklet **+ model answer** |
| `maths.PDF` | 29 | Maths booklet **+ model answer** |
| `01010116-QB-GK.pdf` | 24 | GK; key `01010116-MA-GK.pdf` **failed to download — retry** |
| `PHARMACY.PDF` | 24 | **+ model answer** |
| `JE-0411-QB-Mechanical.pdf` | 20 | JE; **no key downloaded** |
| `JE-0411-QB-Civil.pdf` | 16 | JE; **no key downloaded** |
| `JE-0411-QB-GK-GS.pdf` | 16 | JE GK/GS; **no key downloaded** |
| `hindi1.PDF` | 13 | Hindi booklet **+ model answer** — feeds the Hindi section |
| `01010116-MA-Hindi.pdf` | 1 | key for the Hindi booklet |

**Priority order** (by value to the GS bottleneck and the Hindi section):
`GK1` → `GK(3649)` → `G.K_and_N.A_M.A` → `01010116-QB-GK` → `hindi1` → `maths` → `JE-*` →
`CHEMISTRY` / `PHARMACY` (technical posts, least reusable).

### ⚠️ These differ from the five already done
Several are **"test booklet AND model answer in ONE PDF"** — the key is not a separate file. So the
key-reading step must locate the आदर्श उत्तर pages *inside* the same document (usually at the end)
rather than opening a second file. `bssc_batch.py`'s `PAIRS` list assumes separate files; it needs a
same-file mode, or split the PDF first.

### Runbook
```bash
# 1. upload whatever is not already on the VM
scp -i ~/.ssh/gurukul_key question_bank_engine/drop/bssc/<file> \
    dk_trigun@20.219.2.53:~/bssc_in/

# 2. extract (hosted vision — NO GPU; the T4 is NOT needed, keep it deallocated)
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
cd ~/question_bank_engine
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://127.0.0.1:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 QBANK_VISION_MODEL=gpt-4o
setsid nohup .venv/bin/python extract_bssc.py ~/bssc_in/<file> --exam BSSC \
    --subject "General Studies" --year 2024 --out ~/bssc_in/<stem>_EXTRACT.json \
    > ~/bssc_in/<stem>.log 2>&1 < /dev/null &

# 3. key + tag + re-mine
.venv/bin/python bssc_batch.py          # after adding the new pairs to PAIRS
setsid nohup ~/run_tag.sh > ~/bssc_in/tag.log 2>&1 < /dev/null &
.venv/bin/python tag_bssc.py --mine-only
```
⏱ ~25 s/page ⇒ 325 pages ≈ **2¼ hours unattended**, a few dollars of vision calls.

**Sanity checks after each paper:** numbering continuous with no gaps · `hindi == total` ·
`keyed == total` · then RENDER a page and look at it (gotcha 12).

---

## 11. STILL OPEN

1. **Hand-verify ~15 answers** against the official key PDFs before any student sits these. Vision
   read both the questions and the keys; a systematic misread would be silent, and "official answer
   key" is not a claim you can walk back.
2. **A Hindi reader must check `hindigen`'s tables** (first ~20 questions) before an institute sees
   them. Standard textbook content, but unreviewed by a native speaker.
3. **Store the 497 into the live bank** — `real-serve` allowlist + push `*_hi` columns.
4. **Hindi for `quantgen`** (~1.5 days, same mechanical pattern as `reasoninggen`) — until then the
   maths section of a generated paper is English-only in a bilingual paper.
5. **Expand `hindigen` tables** — pure data entry; a few hundred entries takes Hindi past 1,000.
6. **Missing reasoning builders** the real papers use and we cannot generate: calendar, coded
   inequality, dice, seating arrangement, syllogism, figure series.
7. **Get a real Inter Level paper** — only from One Step's own material or a student's copy (§2).

---

## 12. ▶ STATE AS OF 2026-08-20 — the paper is now 100% GENERATED. Read this before anything.

**Two review copies are with One Step** (via Rohan, 2026-08-20). Deepak has checked the Hindi
renders correctly on the page. **We are waiting on the owner's answer to ONE question: is 70% hard
the right level?** Do not rebuild the sets or change difficulty until that comes back — the whole
point of the badges is to get his calibration, and changing the paper first wastes the ask.

### What the papers are now

`OneStep_BSSC_InterLevel_Set1_REVIEW.pdf` / `Set2_REVIEW.pdf` — 150 questions each, **zero official
past-paper questions**, 15/15/70 easy/medium/hard in every section, no question shared between
sets, every one independently re-solved before the paper is allowed to build.

```bash
python3 build_onestep_paper.py --set 1 --sets 2 --inter-level --all-generated \
    --difficulty-mix 15:15:70 --show-difficulty --logo onestep_logo.png --out <file>.pdf
python3 test_papers.py <file>.html          # must print ALL CHECKS PASSED and N of N re-solved
```

`--show-difficulty` prints a सरल/मध्यम/कठिन badge per question — REVIEW copies only, never a
student copy. A student who sees "Hard" before answering has been primed.

### 🔴 WHAT ROHAN CAN AND CANNOT SAY

The old line — *"asli, verified past-year questions with the commission's own answer key"* — is
**no longer true of these papers**. Nothing on them is a past-paper question. The honest
replacement, which is arguably stronger:

> "Every answer is either computed in Python or traceable to the official Constitution text.
> Nothing is copied from anyone, and nothing rests on a scan we might have misread."

### Why we went fully generated

The owner read the first two sets and said *"ye basic ka bhi basic hai"*. He was right, and the
cause was measurable: 28 of Set 1's 106 official questions were tagged difficulty 1, and a third
came from Office Attendant and 10th Level papers — exams for posts BELOW Inter Level. The draw
never considered difficulty at all; it picked by hash order.

The deeper constraint: **the real BSSC papers are basic.** Across 1,744 extracted questions only 50
are difficulty 3 and none higher. "Authentic to the exam" and "what this owner wants" are different
targets, and only generation can serve the second.

### The four generators, and what varies with difficulty

| engine | covers | difficulty | bilingual |
|---|---|---|---|
| `quantgen` | maths, 23 builders | **10 of 23** respond to `diff` (d1-d4) | 6 builders |
| `reasoninggen` | reasoning, 13 builders | **all 13** | all |
| `sciencegen` | physics numericals, 3 builders | all, d1-d4 | all |
| `staticgkgen` + `staticgk_forms` | GS | recall = d1; statement/match forms = d2/d3 | via `staticgk_hi` gate |

Pools: **500** distinct hard GS, **3,206** maths, **3,871** reasoning, **296** science.

### The rule that keeps generated GS honest

A false statement is made by pairing a key with a **different value from the same table**. That is
only false if the table is a **function** (one value per key) AND its **values are mutually
exclusive**. Both halves are load-bearing:

- Chandigarh is the capital of Punjab AND Haryana → the reverse direction is unsafe, so the forms
  only ever run key → value.
- The 73rd and 74th Amendments were both enacted in **1992** → a year swap is accidentally TRUE.
  `_false_value` refuses any value owned by more than one key. **I reasoned about this hazard twice
  and both times checked only the key side; it took a real collision to show the check was half a
  check.**

### GS content: what worked and what did not

- **`polity_tables.py` — 31 articles + 8 amendments, VERIFIED against the official Constitution PDF**
  (`cdnbbsr.s3waas.gov.in`; legislative.gov.in serves only a landing page). One real error found
  and fixed: the 61st Amendment is **1988** (the Act), not 1989 (commencement). On an OPEN-BOOK
  exam that would have marked a correct candidate wrong while they held the proof.
- **`CONSTITUTION_ARTICLES.json` — 462 headings** parsed from the official ToC by
  `parse_constitution_toc.py`. 430 unused; extending is now mechanical.
- **NCERT is a DEAD END for the statement forms.** 849 cited paragraphs → 1,537 support-verified
  facts → **two** pattern matches → **zero** usable tables. Prose has no closed value domains.
  `GS_SOURCED_FACTS.jsonl` and `GS_FACTS_VERIFIED.jsonl` are saved but feed nothing. **Do not
  extract more NCERT chapters expecting a different answer.**

### 🔴 THE LESSON OF THIS ENTIRE EFFORT: check the checker

**Sixteen times** a checker was wrong rather than the thing it checked. Flattened fractions made the
models answer "the L.C.M. of 14 and 25"; `\bNN\b` cannot match in "Equality14."; a solver read a
3-statement question as 2-statement and failed 22 correct ones; a parser reported Article 15 as
"The United Provinces Land Acquisition Act, 1948".

Two habits came out of it, and they are the transferable part of this work:

1. **Sabotage every new check before trusting it.** Flip a key, feed a false claim. A check that
   cannot fail is not a check. `test_papers.py` catching a deliberately corrupted answer is the
   only reason its green run means anything.
2. **Gate on already-verified data before writing.** The ToC parser had to reproduce the 19
   hand-verified rows before a single new one was accepted. It caught two broken parsers that
   produced clean-looking output.

And the asymmetry that decides close calls: **a false alarm costs an hour; a false pass ships.**

### 🔴 OWNER FEEDBACK #2 (2026-08-20, on the generated papers): Part III is basic AND one-topic

His words: the reasoning section *"has very basic questions and it contains only one topic, it's
not distributed across the syllabus."* Measured against the delivered sets — he is right, and
"one topic" understates it:

    SET 1 Part III: Blood Relations 16 of 50 (32%), then 10 other concepts at 1-4 each
    SET 2 Part III: Blood Relations 11, Letter Series 10, then 8 others

Two separate defects, and the second is the real one:

1. **Clustering.** One concept taking a third of a section is indefensible and is a one-line fix —
   a per-concept cap of ~4 in Part III.

2. **All eleven concepts are ONE FAMILY.** Trace a relationship, or shift letters/numbers along a
   sequence. To a reader that IS one topic, because it is one skill asked eleven ways. Against
   खंड (ग), which names सादृश्य · समानता एवं भिन्नता · **स्थान कल्पना** · **समस्या समाधान** ·
   **विश्लेषण** · **दृश्य स्मृति** · **अवलोकन** · संबंध अवधारणा · अंक गणितीय तर्कशक्ति · श्रृंखला ·
   कूट लेखन — we generate the last four and have NOTHING for spatial visualisation, problem
   solving, analysis, visual memory or observation. No syllogism, seating arrangement, coded
   inequality, calendar, dice, figure series or statement-conclusion.

**Note what our own metric said: 32 of those 50 questions are tagged difficulty 4.** The owner
still called them basic, and he is right — he is judging the TOPIC, not the step count. A four-step
blood-relation chain is still blood relations. This is the second time his read has beaten our
measurement; the first was "ye basic ka bhi basic hai" on the official questions. **When the
difficulty tag and the customer disagree, the customer is describing something the tag does not
measure.**

Do NOT respond by generating more of what we have — the missing families are the fix, and more
volume makes the imbalance worse.

### ▶ NEXT SESSION, in order

1. **FIX PART III — this is now the top item, the owner has told us twice.**
   a. Per-concept cap of ~4 in Part III (one line, immediate).
   b. New reasoninggen builders, in this order: **syllogism · seating arrangement · coded
      inequality · calendar · dice**. All are algorithmic, so they fit the compute-the-answer
      pattern exactly, and they are what a candidate actually finds hard. Follow the proven recipe:
      disjoint difficulty bands, mistake-derived distractors, Hindi from the start, and an
      independent solver in `test_papers.py` BEFORE the pool is regenerated.
   c. **Non-verbal / figure series is the real hole** — खंड (ग) explicitly names गैर-शाब्दिक and we
      cannot draw. Needs SVG generation; bigger piece, do it last.
2. **Act on the owner's difficulty answer** when it comes.
2. **A native Hindi reader over the generated Hindi.** Deepak has checked the FONT renders; nobody
   has checked the LANGUAGE. This session alone produced `73वाँ` for `73वें`, `पोती` for `नातिन`,
   `भतीजी` for `भांजी` and a literal `मेरा/मेरी` on the page. 12 polity renderings from 2026-08-20
   are entirely unverified.
3. **13 quantgen builders still ignore `diff`** — profit/loss, CI, ratio and boats are done; DI,
   partnership, alligation, mensuration and the rest are not.
4. **Select more of the 430 parsed articles**, with Hindi. A parsed row still needs judgement:
   "243. Definitions" is a faithful heading and a useless question.
5. **BSEB textbooks** — Bihar is 20% of the GS section and `biharboardonline.bihar.gov.in` does not
   resolve. Those PDFs must come from Rohan into `drop/gs_sources/`.

**Measured error rate on hand-written data here: about 1 in 27.** That is why every table gets
checked against a source, and why "I wrote it carefully" is not a verification.
