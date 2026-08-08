# Acharya — Pricing Strategy & Unit Economics (teacher B2B2C)

*Researched 2026-07-05. Owner: Deepak. Companion to `01_OFFER_ONE_PAGER.md` (the ₹4,999 offer) and
`acharya-technology-transfer` skill (delivery). Anchor for any pricing decision.*

---

## TL;DR — the one thing to internalise

**Cost is NOT the constraint. Price on VALUE, not cost-plus.**

Serving a 20-student institute costs you **~₹100–150/month in real cash today** (Azure credits cover
compute for 2 years; WhatsApp doubt-replies are FREE). Even with **zero credits**, worst case is
**~₹2,000–2,700/month** on a premium model, or **~₹300–500/month** on an efficient model. Your
revenue at ₹5,000 gives you a **95%+ gross margin today** and **50–90% even after credits end**.

So the question "what does it cost me?" is nearly irrelevant. The real question is **"what is it
worth to the institute?"** — and the answer is: a lot more than ₹5,000.

---

## 1. True cost to serve ONE institute (20 active students)

| Cost line | Today (on Azure credits) | True cost (credits gone) | Why |
|---|---|---|---|
| **Compute (VM)** | ₹0 | ~₹100–300/mo | One shared `B2s` VM serves MANY institutes; per-institute slice is tiny |
| **WhatsApp Cloud API** | ~₹70–150/mo | ~₹70–150/mo | **Student doubts = "service" window = FREE & unlimited** (Meta, since Nov 2024). Only proactive SRS recall pings are billed — utility template **₹0.115/msg** (~600/mo for 20 students ≈ ₹69) |
| **Azure OpenAI tokens** | ₹0 (credits) | ₹300–500/mo (efficient model) · ₹1,500–2,500/mo (premium gpt-5.5) | ~150 doubt-turns/student/mo × ~3k in + 400 out tokens. gpt-4o-mini class is cheap; gpt-5.5 class is the ceiling |
| **TOTAL / institute / mo** | **~₹100–150 cash** | **~₹500 (efficient) → ~₹2,700 (premium)** | |

> **Margin at ₹5,000:** today ≈ **97%**. Post-credits ≈ **50% (worst) to 90% (efficient model)**.
> **Lever:** route routine doubt-solving to an efficient model, reserve the premium model for hard
> concepts — keeps post-credit cost near the ₹500 floor and margin ~90%.
>
> *Token rates for gpt-5.5 are estimated (exact Azure rate not pinned); the efficient-model floor is
> well-established from gpt-4o-mini pricing. Range shown deliberately.*

---

## 2. What the market charges (2026, India)

| Product | What it is | Price | Note |
|---|---|---|---|
| **Classplus** | Branded app + LMS + payments (NOT an AI tutor) | ₹8,000–50,000 **/year** (₹667–4,167/mo) **+ sales commission + hidden live-class credits** | Quote-based; the incumbent institutes already pay |
| **Teachmint** | Connected-classroom LMS/admin | Freemium → institute plans up to ~₹1,50,000 | Higher-end, hardware-adjacent |
| **B2C AI tutors** (PW Alakh AI, YoLearn, Super Tutor) | Per-**student** doubt apps sold to families | ~₹350–420/mo/student (≈ ₹4,200–5,000/**year**), freemium | Sold direct to students, not to institutes |
| **A human doubt-solver / TA** | Part-time subject teacher | ₹8,000–25,000/mo | The thing Acharya actually replaces/augments |
| **Acharya (us)** | White-label AI WhatsApp tutor, **under the institute's brand**, flat B2B fee | **₹4,999/mo** | **No direct competitor in this exact shape** — that's the wedge |

**Read:** Nobody else sells a *branded, WhatsApp-native, institute-owned* AI tutor on a flat B2B
fee. Classplus is an app, not a tutor; the AI tutors are B2C and un-branded. You sit in an empty lane.

---

## 3. Willingness to pay — the value anchor (why ₹5,000 is cheap)

A NEET/JEE institute charges each student **₹3,000–15,000/month** (offline typically ₹8,000+).

- 20 students × ₹3,000 (low) = **₹60,000/mo** institute revenue → ₹5,000 = **8%**
- 20 students × ₹8,000 (typical) = **₹1,60,000/mo** → ₹5,000 = **3%**
- **₹5,000 ≈ the fee of ONE student**, or less.

**The ROI line that closes it:** *"If Acharya keeps even ONE student from dropping out this month,
it has already paid for itself — often 2–3× over."* And it's cheaper than a part-time doubt teacher
(₹8k–25k/mo) that does less and can't work at 11pm.

---

## 4. RECOMMENDATION — what to charge

### For a ~20-student institute (your current case): **₹4,999/mo is correct.** Don't drop it.
It's the "fee of one student," 97% margin, and cheaper than a TA. If anything it's slightly *under*
for the value — hold it as the entry price and prove retention in the trial.

### Structure to adopt as you scale past the first 2–3 pilots: **flat, banded by active students**
Keep flat (never per-student — that punishes the institute for growing and creates churn). But add
bands so a 300-student institute doesn't pay the same as a 20-student one:

| Tier | Active students | Price/mo | ≈ % of institute revenue |
|---|---|---|---|
| **Starter** | up to 30 | **₹4,999** | 3–8% |
| **Growth** | 31–100 | **₹9,999** | 2–5% |
| **Institute** | 101–300 | **₹19,999** | 1–4% |
| **Enterprise** | 300+ / multi-branch / own number+domain+dedicated box | **Custom (₹30k+)** | negotiated |

Every band stays a small single-digit % of the institute's student revenue and undercuts a human TA.

### Two add-on levers
- **Annual prepay:** ₹49,999/year (2 months free) — locks cash upfront, cuts churn, improves your
  runway. Offer it the moment a pilot converts.
- **Premium upsell (later):** their own WhatsApp number + own domain + dedicated box = a "Pro"
  add-on (₹2,000–5,000/mo on top), which also matches exactly when *you* incur real extra cost.

### What NOT to do
- ❌ **Don't price per-student** — the offer already rejects it; it punishes growth and invites churn.
- ❌ **Don't cost-plus / discount because "it's cheap to run"** — your cost is near-zero; that's *margin*,
  not a reason to charge less. The institute pays for the *outcome* (retention, more students served).
- ❌ **Don't undercut Classplus to compete** — you're a different, higher-value product; anchor on the
  human-TA replacement, not on being the cheapest app.

---

---

## 6. SECOND PRODUCT — "Marketing Engine" (done-for-you social content) — different economics

The OpenClaw daily content engine (2 reels/day + posts across YouTube, Instagram, LinkedIn,
Facebook, Shorts) offered to institutes as a branding service. **This is NOT Acharya — the cost
structure is the opposite:** it runs on the **A10G GPU (AWS EC2, ~$1/hr) which is NOT on the free
Azure credits.** So it has real, scaling marginal cost. Price it accordingly.

### Cost to serve (per institute, per month)
| Line | Cost | Note |
|---|---|---|
| GPU render (dedicated per-institute) | ₹1,200–2,500/mo | ~2 reels/day + shorts × ~10–15 min A10G each |
| GPU render (**batched** — all institutes in one daily EC2 window, auto start/stop) | **~₹500–750/mo** | The farm is already batch/auto-stop capable — USE THIS to protect margin |
| LLM/script/image (Azure, on credits) | ~₹0 today | small even post-credits |
| **Effective floor** | **~₹500–2,500/mo** | batch → low end |

> **Margin at ₹5,000 = 50–90%** (vs Acharya's 97%). This is your only real-cost product, so ₹5,000
> is a **floor, not a target.** Batch the renders and add a quality gate before it eats margin.

### Market comparison (India SMM, 2026)
| Option | Price/mo | Volume |
|---|---|---|
| Bare tool (Buffer/Canva — teacher does the work) | ₹500–2,000 | self-serve |
| Freelancer (you give strategy, they execute) | ₹10,000–35,000 | 1–2 platforms |
| Small agency | ₹20,000–60,000 | full service |
| **A single professionally-produced reel** | **₹5,000–15,000 each** | — |
| Standard agency package | ₹20,000–40,000 | **only 12–20 posts/MONTH** |
| **Your offer** | ? | **~60 reels/month across 5 channels** |

**Read:** a standard ₹20–40k agency package delivers ~12–20 posts *per month*. You deliver ~60
reels/month across 5 channels. On raw volume you're 3–4× an agency for a fraction of the price. **BUT**
the honest caveat: **AI-generated content ≠ a custom-shot professional reel.** The realistic comp is a
**low-mid freelancer (₹10–15k)**, not a premium agency — so anchor there, not at ₹5k/reel value.

### Recommendation — what to charge
- **₹5,000/mo is a fine LAND / intro price** (easy yes, margin-positive if batched). Your instinct is OK
  **as a starting point** — but it's the *floor*.
- **Standalone list price once proven: ₹7,999–9,999/mo** — below a freelancer, above a tool, honest
  positioning as "AI content engine, cheaper than a freelancer, 3× the volume."
- **BEST play — bundle with Acharya** (raises ACV from ₹5k → ₹9k, and two hooks = far stickier):
  | | Price/mo |
  |---|---|
  | Acharya (tutor) alone | ₹4,999 |
  | Marketing engine alone | ₹4,999 (intro) → ₹7,999+ (proven) |
  | **Bundle: Acharya + Marketing** | **₹8,999** (save ₹1,000) |
- **Protect it:** (1) **batch** all institutes' renders in one daily EC2 window; (2) a **quality/approval
  gate** — the teacher approves before content posts under their brand (posting generic/off-brand content
  daily under their name is a real reputational liability you'd be taking on).

### Strategic caveat (CEO honesty)
This is a **second, different business** (an SMM service) with real GPU cost, a quality/brand-risk, and
its own ops load — bolted onto the Acharya wedge.

**GO-TO-MARKET RULE (Deepak, 2026-07-05): the lead pitch is ONE product — Acharya (₹4,999).** The
Marketing engine is **NOT** part of the outreach/lead pitch. Only bring it up:
1. **AFTER an institute has already joined** (as a retention/upsell), OR
2. **If the teacher specifically asks** about marketing / getting more students.

Never open with two products. This keeps the PMF signal clean and the pitch simple. When it does come
up, price per §6 (₹4,999 intro → ₹7,999 proven; ₹8,999 bundle). Any outreach skill / script must honor
this — Acharya only, until join or explicit request.

---

## 7. Sources
- WhatsApp API India rates (service free; utility ₹0.115; marketing ₹0.86) — Meta/aggregator pricing pages, 2026
- Social media management India (freelancer ₹10–35k, agency ₹20–60k, reel ₹5–15k each, 12–20 posts/mo) — Jigsawkraft / upGrowth / Snara, 2026
- Classplus pricing ₹8k–50k/yr + commission — Edmingle / AllCoaching / SoftwareSuggest, 2026
- Teachmint plans — SaaSworthy / Capterra, 2026
- Coaching fees ₹3k–15k/student/mo (NEET), JEE ₹1–2.5L/yr — Vedantu / Prepmed / Collegedwar, 2025–26
- B2C AI tutor pricing (PW ≤₹5k/yr, YoLearn) — MyEngineeringBuddy / YoLearn, 2025–26
