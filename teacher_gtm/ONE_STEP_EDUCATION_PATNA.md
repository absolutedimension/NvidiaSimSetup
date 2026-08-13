# One Step Education — Patna (FIRST institute to say YES)

> **Status:** WARM PILOT — verbally agreed to use the system (Rohan field visit, 2026-08-12).
> **NOT paid yet.** Win = committed pilot + a concrete delivery spec. Convert to paid AFTER
> their students run tests on it. Owner of channel: Rohan (Patna field). Product: Acharya assessment.

## What they teach (their exam menu — the tests they want)

**Target competitive exams:**
- **SSC** — CGL, CHSL (Bihar + Central)
- **Railway** (RRB)
- **Banking**
- **TRE** (Bihar Teacher Recruitment Exam)
- **BPSC** — incl. TRE, **Daroga** (SI)

**Subjects they want tests for:**
- Maths
- Reasoning
- **General Studies:**
  - Physics
  - Chemistry
  - Biology
  - Polity
  - Geography
  - History
  - Economics
- **Static Portion — GK**
- **Current Affairs**
- **English** (specifically for SSC CGL, Central)

## Delivery spec (what "delivered" means for this pilot)
Working test papers/practice sets, per exam × subject, that their students can take on the
Acharya assessment funnel. Coverage audit vs the live question bank → see below.

## Coverage audit — DONE 2026-08-12 (live bank = 145,056 verified)
Bank exams present: CBSE Class 10 (52.6k), NEET (34k), JEE Main (29k), CBSE Class 12 (25.5k),
JEE Advanced (1.5k), ICSE Class 3 (1.08k), UPSC Prelims (574: GS 365 + CSAT 209), Banking Prelims (568: Quant ONLY).
**NO exam entry exists for SSC / Railway / BPSC / TRE / Daroga.** This customer's whole family is unbuilt.

| Their subject | In bank? | Servable today | Gap action |
|---|---|---|---|
| Banking – Quant | ✅ 568 (Banking Prelims) | YES | serve now |
| Maths (SSC/Railway quant) | 🟡 borrow | via gen | companion-borrow CBSE/JEE-Main maths + Banking-quant |
| GS Physics | 🟡 borrow | via gen | borrow NEET/CBSE Physics |
| GS Chemistry | 🟡 borrow | via gen | borrow NEET/CBSE Chemistry |
| GS Biology | 🟡 borrow | via gen | borrow NEET Biology (14k) |
| GS Polity/Geo/History/Econ | 🟡 thin | via gen | borrow UPSC GS (365) + CBSE-12 (shallow) |
| Reasoning | 🔴 ~none | no | only UPSC CSAT 209 adjacent → BUILD |
| Static GK | 🔴 none | no | BUILD |
| Current Affairs | 🔴 none | no | BUILD (dated/fresh) |
| English (SSC CGL) | 🔴 none | no | BUILD |

**Verdict:** we can generate a *sample* SSC-CGL / Banking test THIS WEEK via the companion-exam
borrow trick (proven — CBSE-12 Maths borrowed JEE-Main). Full SRB bank = a multi-day build,
justified only if this pilot (and the SRB segment) is real.

## Build progress
- [x] **2026-08-12 — REASONING section LIVE for the whole SRB family** (SSC CGL/CHSL, Railway,
  Banking, BPSC). Compute-the-answer engine `qbank/reasoninggen.py` (7 chapters, 13 builders),
  deployed to Gurukul `/examgen`, verified live. Copyright-clean, unlimited, answer-verified.
- [x] **Quant / Maths** — already live via Banking `quantgen.py` (14 chapters), reusable for SSC/Railway.
- [x] Sample paper produced: `ONE_STEP_SAMPLE_PAPER.md` (26 Qs, reasoning + quant, key + solutions).
- [ ] Wire SSC CGL into the student LMS (examgen RAG_SUBJECTS + EXAMS) → deploy → students can TAKE it.
- [ ] GS (Physics/Chem/Bio) via companion-borrow from NEET/CBSE.
- [ ] GS Social + Static GK + English + BPSC/Daroga via official-PDF exact-question pipeline.
- [ ] Current Affairs (needs dated/fresh source).

## Next actions
1. **Rohan → One Step:** hand over `ONE_STEP_SAMPLE_PAPER.md`; qualify (# students, priority exam, timeline, will-they-pay).
2. Wire SSC CGL into the LMS so their students take the reasoning+quant tests this week.
3. Continue the SRB bank (GS borrow + PDF ingest for the remaining subjects).
4. Convert to paid once students are actively taking tests (UTR = the real gate, not "yes to use").

_Source: Rohan field visit, handwritten subject list, 2026-08-12._
