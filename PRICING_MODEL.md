# Acharya — Pricing Model (canon)

> **What we charge, to whom, and why.** Covers both live funnels: **B2C** (`acharya.trigunai.com/exam-prep`)
> and **B2B** (`acharya.trigunai.com/teacher`). Companion to `COMPETITIVE_ANALYSIS_EXAM_PREP.md` (the market
> read) and `BRAND_POSITIONING.md` (how we talk). **Locked 2026-07-24.**
>
> **Product = an authentic exam-paper generator** — unlimited practice tests in the exact pattern of the
> real exam (real-pattern diagrams included), from a curated ~46k RAG bank. Lead with the machine + the
> exam-authenticity, never "tutor."

---

## 0. The honest frame (read first)

- **0 customers have paid on either funnel.** Every price here is a **hypothesis to test**, not a fact.
- **The job of pricing right now is NOT to maximize ARPU — it is to get the first cleared payment (0→1).**
  Land low, prove the value, then expand. A first paid ₹999 institute is worth more than ₹4,999 of ARPU
  we can't close.
- **Never compete on mock-count or price** — govt all-access (Testbook/Adda247) anchors ₹300–400/yr for
  150k+ mocks; we lose both. Sell on the one thing they fake or skip: *AI that finds YOUR weak spots and
  generates YOUR next test, with real exam-pattern diagrams.*
- **The wall to respect = Embibe** (Reliance/Jio) — ships our student feature set for *free*, bundled with
  content. Our edge must be **focus + distribution + diagram-authentic UX**, not raw features.

---

## 0.5 The pricing UNIT — per exam, never per subject (how it scales)

**A plan always covers ALL subjects of an exam — never one subject.** Nobody preps for a single
subject (a NEET student needs Physics + Chemistry + **Biology**; JEE = PCM). "NEET Biology only" is
not a product.

**Student plans are per-EXAM-GOAL, not all-access** (in the entrance segment). The ₹1,299 Exam Pass =
**one exam, all its subjects, for that exam cycle** (JEE = PCM · NEET = PCB). Matches how PW/Allen sell.

**As competitive-exam data is built, pricing FORKS by segment** (the market splits — see
`COMPETITIVE_ANALYSIS_EXAM_PREP.md` §1):

| Segment | Exams | Pricing unit | Why | Market anchor |
|---|---|---|---|---|
| **Entrance** | JEE, NEET (later: state CETs) | **per-exam Pass ~₹1,299** | Aspirant preps for ONE exam | PW ₹5–8k/yr — we're cheap |
| **Govt / competitive** | Banking, SSC, Railways, UPSC | **ALL-ACCESS sub (many exams, one price)** | Aspirants attempt *several* together | Testbook/Adda247 ₹300–400/yr → price **₹599–999/yr** |

Do **not** cross the models: per-exam pricing loses to Testbook's all-access in govt; cheap all-access
leaves money on the table in entrance.

**Teacher plans = exam-agnostic, priced by SCALE** (already so). A coaching teacher generates for
*whatever their institute teaches* (often JEE **and** NEET), so B2B tiers grant **all exams the bank
covers**, priced by **student count** (₹999 / ₹2,999 / ₹7,999) — never per exam.

**Optional later:** an **"All Entrance" bundle** (JEE + NEET) for droppers/dual-preppers; a **mega
all-access** tier once many exams exist.

**Gate discipline (anti-pattern #25):** this is the *design* for expansion — **validate ONE exam
paid** (a NEET/JEE ₹1,299, or a teacher ₹999) **before building the banking/UPSC pricing fork.**

---

## 1. Student (B2C) — `/exam-prep`

**The trap we're fixing:** ₹199/**mo** (~₹2,400/yr) reads *premium* against an ₹800–1,200/**yr** test-series
habit. Exam prep is **goal-bound and seasonal**, not a monthly habit — so lead with an exam-cycle plan, not
a monthly sub.

| Tier | Price | What's included | Purpose |
|---|---|---|---|
| **Free** | ₹0 | 3–5 tests/mo · basic report · limited chapters | Funnel + let the AI/diagram quality be *felt* before the paywall |
| **Exam Pass** ⭐ (lead) | **₹1,299 "till your exam"** | Unlimited tests · full mock papers · weak-topic SWOT report · all chapters · real-pattern diagrams | The primary buy — matches the habit, anchors *below* PW's ₹5–8k, ~= Embibe's ₹1,100 |
| Monthly | ₹249/mo | Same as Exam Pass, month-to-month | Flexibility only — priced *up* so the annual Pass is the obvious choice |

**Positioning line:** *"Unlimited real-pattern JEE/NEET tests that find your weak spots — practise till your exam."*
**Do NOT** sell on "10,000 questions" or "cheapest" (both are losing games).

**Competitive anchors (from `COMPETITIVE_ANALYSIS_EXAM_PREP.md`, vendor-advertised, spot-check before quoting):**
PW Real Test Pass ₹5,000–8,000/yr · standalone test-series ₹650–1,200/yr (CL/Testbook/Vedantu/Allen/Aakash/Embibe)
· Embibe free/bundled · govt all-access ₹300–400/yr. **₹1,299 sits deliberately between the ₹800 habit and Embibe.**

---

## 2. Teacher / Institute (B2B) — `/teacher`

**The wedge:** there is *no* dominant "authentic AI paper generator for coaching institutes." The real
competition is a junior teacher + Word + copy-paste from PDFs/getmarks, plus generic paper-generator
software. Less contested than B2C — but willingness-to-pay is **unproven** (the ₹35k close failed 0/3, and
a ₹499 attempt was tried). Fix = **land-and-expand**, entry price low enough to say yes after one demo.

| Tier | Price | Cap / who | Includes |
|---|---|---|---|
| **Solo Teacher** ⭐ (land here) | **₹999/mo** | 1 teacher · ≤20 students | Unlimited real-pattern papers · share link (no student signup) · printable + answer key · weak-topic dashboard |
| Coaching | **₹2,999/mo** | ≤50 students | + white-label (institute brand) · class analytics · priority generation |
| Institute | **₹7,999/mo** | ≤200 students | + multi-teacher · full branding · usage analytics · priority support |
| **Custom** | Contact business | 200+ students / multi-branch | negotiated — the biggest fish never self-serve a price |

> **Caps tightened 2026-07-30 (Deepak):** was Solo ≤60 / Coaching ≤300 / Institute unlimited. Now
> ≤20 / ≤50 / ≤200 + Custom-above-200. Deliberate premium-per-student call (Solo ~₹50, Coaching ~₹60,
> Institute ~₹40/student) — sell on brand + hours-saved + dashboard, NOT the per-student math. Live on
> `/teacher` + `config.py` comments + Rohan's `teacher_gtm/ROHAN_QUOTE_CARD.md`. Still 0 paid — anchor
> high in the field, fall back to ₹999 only to break 0→1.

- **14 days free**, then the tier. (Supersedes the flat ₹4,999/≤50 in `teacher_gtm/01_OFFER_ONE_PAGER.md`
  — that model was fine, but land lower to break 0→1, then move institutes up.)
- **Alternative institutes understand:** per-student ₹15–30/student/mo. Flat is easier to close; offer
  per-student only if a big institute pushes back on the flat cap.
- **The sticky value (→ switching cost → moat seed):** once their assessments + weak-topic dashboards run
  on Acharya, ripping it out hurts. Sell the *dashboard + time-saved*, not the generator alone.

**Sell line:** *"Generate real-pattern papers for your batches in seconds, under your name — and see exactly
which student is weak in which topic."* Teacher is the hero; Acharya is their staff, never their replacement.

---

## 3. Do we have a moat? (honest — from the analysis)

**Not yet. Today it's a *service* with one real technical edge.**
- **Not a moat:** the RAG bank (competitors scraped the same sources; Embibe/PW are bigger) · "unlimited AI
  generation" (LLM-commoditized, model is rented) · price/features (instantly matchable).
- **The one real edge now:** **authentic, complete, diagram-correct generated papers** — most AI-test tools
  skip diagrams or serve broken "as shown in figure" questions. This is a **feature lead, not a moat** (a
  funded team could close it in a quarter).
- **What would *become* a moat — each needs paying customers first:** (1) **data flywheel** (every wrong
  answer → what to serve next; compounding, uncopyable); (2) **B2B switching cost** (institute runs its
  assessments on us); (3) **breadth into neglected exams** (banking/UPSC/state/boards before the giants
  care); (4) **distribution the giants don't own** (WhatsApp-native + teacher-brand channel).

**Bottom line:** the moat and the gate are the same conversation — nothing is defensible until someone pays
and starts generating the usage data that compounds. **Don't let "the bank is bigger / the pipeline is
better" stand in for either revenue or a moat.**

---

## 4. What to test (in priority order)

1. **Break 0→1 on either funnel** — put the **₹999 teacher tier** or the **₹1,299 student Pass** in front of
   ONE real buyer this week and close it. That single payment validates more than this whole doc.
2. **Student:** does the **annual Pass out-convert monthly?** (the framing bet). Free→Pass conversion rate.
3. **Teacher:** does **₹999 close where ₹4,999 didn't?** Log every objection (price / trust / diagram quality / time-saved).
4. **Boards segment** (Class 9–12) — competitive white space, under-verified; scan before betting the funnel there.
5. **Embibe watch** — if they launch a cheap paid standalone adaptive sub, the student ₹1,299 slot narrows; re-check quarterly.

---

*Locked 2026-07-24 · supersedes scattered prior numbers (student ₹199/mo; teacher flat ₹4,999/≤50).*
*Grounds: `COMPETITIVE_ANALYSIS_EXAM_PREP.md` (deep-research 2026-07-23) + Master Founding OS v7.0 (gate = first cleared payment).*
