# Acharya — Pricing Model & SaaS Finance (Founder's Reference)

*The final pricing model + the finance concepts behind it. Owner: Deepak. Written 2026-08-01.
Companion to `STUDY_HUB_SUNDAY_BRIEF.md` (the deal), `INSTITUTE_POLICIES.md` (terms),
`ACHARYA_PARTNER_PROGRAM.md` (channel), and the banners.*

---

## 1. THE FINAL PRICING MODEL

**Model type:** *Land-and-expand hybrid* — one-time setup + value-based per-student (with a floor) +
a founding discount to break the cold start. This is what the best B2B SaaS startups run.

| Component | Number | Why it's here |
|---|---|---|
| **One-time setup** | **₹55,000** (₹25k Brand Activation + ₹30k go-live) | Cash upfront funds the build; filters tire-kickers (skin in the game → serious buyers → low churn) |
| **Recurring — per student, by exam** | **₹120 Board/Foundation · ₹250 JEE/NEET/Senior** | Value-based; scales automatically as the institute grows |
| **Monthly floor** | **minimum ₹15,000/mo** | Never serve at a loss, even a tiny institute |
| **Founding discount** | **₹100/student** (first cohort, temporary) | Breaks the 0-paid cold start without wrecking the price anchor |
| **Annual prepay (option)** | 2 months free | Cash + lock-in — huge for runway |
| **Partner channel (Phase 2)** | 60/40 split, ₹50/student floor to us | Others sell for you; open only after a partner is a proven, live customer |

**Go-live SLA:** live within 2 working days of the start payment.
**Setup breakdown (internal / on request):** ₹25k brand activation (custom mobile + web app: logo &
brand colours only, not features) · ₹30k go-live = ₹15k server & hosting + ₹15k DevOps & setup.

### The one-line pitch
> *"₹55,000 to build your own branded app, then ₹250 per student a month — and as a founding institute
> you launch at ₹100. That's a day's fee of one student, to run your whole assessment."*

### Two discipline rules
1. **The founding discount is temporary** — raise to list (₹250) once you have 3–5 institutes.
2. **Don't hire a maintenance engineer until ~5 institutes** — else early deals turn unprofitable.

---

## 2. WHY THIS MODEL IS STARTUP-OPTIMAL

- **It pays you upfront** (setup + annual prepay) — cash is oxygen when pre-revenue.
- **It's profitable per deal at list**, and only a deliberate temporary loss at the founding rate — an
  *investment* in first logos, not a leak.
- **It's explainable in one breath** — critical when pitching in a noisy institute office.
- **It captures value and expands** — per-student grows your revenue as the customer grows, no renegotiation.

**Beats the alternatives:** flat fee leaves money on big institutes; pure per-student (no floor) loses
on small ones; no-setup-fee makes you fund every build with zero revenue; full-price-day-one can't
break a cold start.

---

## 3. THE PRICING MODELS ON THE MARKET (the menu)

| Model | What it is | Acharya fit |
|---|---|---|
| Flat subscription | one price, all-you-can-use | too rigid alone |
| Per-seat / per-user | price × users (**per student**) | ✅ core |
| Usage-based / metered | pay per unit consumed | possible add-on |
| Tiered (Good/Better/Best) | feature bundles at rising prices | later (Basic vs Pro) |
| Freemium | free base, pay to unlock | B2C only |
| **Hybrid (base + usage)** | floor fee + per-unit | ✅ what we use |
| **One-time + recurring** | setup + subscription | ✅ what we use |
| Revenue-share / wholesale | partner sells, you take a cut | ✅ partner program |

---

## 4. HOW COSTING IS CALCULATED PROFESSIONALLY

Split costs into **two layers** — the key mental shift:

- **Layer 1 — COGS (cost to *deliver*):** infra/hosting, AI tokens, per-instance engineering, support.
  → **Gross Margin = (Revenue − COGS) ÷ Revenue.** SaaS target **70–85%.**
- **Layer 2 — Operating costs (run the *company*):** R&D (features), Sales & Marketing (= CAC), G&A.

Judge the **product** by gross margin; judge the **company** by profit/burn. A healthy SaaS has high
gross margin even while the company runs at a loss to fund growth. Never mix the two layers.

---

## 5. UNIT ECONOMICS — the 10 metrics to know cold

| Term | Plain meaning | Formula | Healthy |
|---|---|---|---|
| **MRR / ARR** | monthly / annual recurring revenue | Σ subs (×12) | grows |
| **ARPA** | avg revenue per account (institute) | MRR ÷ accounts | — |
| **COGS** | cost to deliver | infra+tokens+support+per-unit eng | — |
| **Gross Margin** | % left after COGS | (Rev − COGS) ÷ Rev | 70–85% |
| **CAC** | cost to acquire a customer | sales+mktg ÷ new customers | — |
| **Churn** | % lost per month | lost ÷ total | <2%/mo |
| **LTV** | lifetime value | (ARPA × GM) ÷ churn | — |
| **LTV : CAC** | return on acquisition | LTV ÷ CAC | ≥ 3:1 |
| **CAC Payback** | months to earn CAC back | CAC ÷ (ARPA × GM) | < 12 mo |
| **NRR** | net revenue retention (expansion) | (start+upsell−churn) ÷ start | >100% |

Survival pair: **Burn** (₹ lost/mo) and **Runway** (cash ÷ burn = months left).

### The one mental model (the engine)
> Spend **CAC** → win a customer → they pay **ARPA/mo** → you keep **gross-margin %** → they stay
> **1 ÷ churn** months → total = **LTV**. If **LTV ≥ 3× CAC and payback < 12 mo**, every rupee into
> sales returns 3×+ → pour fuel and scale. That's the whole game.

---

## 6. UNIT ECONOMICS — Acharya cost model INCLUDING engineering (by scale)

Engineering/maintenance is a **fixed salary spread across all institutes** → per-institute cost
collapses as you scale. (Engineer ≈ ₹60,000/mo, maintains ~30 standardized instances.)

**Cost per institute (400 students):**

| Cost line | 1 institute | 5 | 30 |
|---|---|---|---|
| Infra / hosting | ₹12k | ₹12k | ₹8k |
| AI tokens | ₹2k | ₹2k | ₹2k |
| Engineering / maintenance | ₹60k | ₹12k | ₹2k |
| Support, payments, overhead | ₹3k | ₹3k | ₹3k |
| **Total cost / institute** | **~₹77k** | **~₹29k** | **~₹15k** |

**Profit vs revenue (400 students):**

| Scenario | Founding ₹100/stu = ₹40k/mo | List ₹250/stu = ₹1,00,000/mo |
|---|---|---|
| 1 institute (₹77k cost) | –₹37k (deliberate acquisition cost) | +₹23k |
| 5 institutes (₹29k cost) | +₹11k | +₹71k |
| 30 institutes (₹15k cost) | +₹25k | +₹85k |

**Takeaways:** (a) at institute #1, founding-price + a dedicated engineer = a loss → *you* maintain
early, don't hire; (b) list price is profitable even at #1; (c) by ~5 institutes the model is 50%+
margin; by 30 it's a machine.

---

## 7. ALL THE FACTORS THAT AFFECT PRICING (checklist)

**Cost-side (raise the floor):** engineering/maintenance · support & training · onboarding time ·
content/pool upkeep · GST 18% · payment fees & late payment/bad debt.

**Value-side (raise the ceiling):** segment willingness-to-pay (NEET/JEE > board; metro > tier-2) ·
competition (Classplus/Teachmint/human TA) · churn→LTV (embedded = sticky) · CAC · positioning
(underpricing signals "toy").

**Strategic:** scale economies · contract length (annual prepay) · switching cost (data lock-in lets
you raise price) · concentration risk (no customer >30% of revenue).

---

## 8. WHAT MATTERS FOR US RIGHT NOW (stage = 0 paid)

Ignore most metrics until ~10 customers. Obsess over three:
1. **Gross margin per institute** — does each deal make money after *true* cost (incl. eng)? (Yes at list.)
2. **First paid + repeatability** — selling the same thing twice beats any spreadsheet.
3. **The engineering scale curve** — cost/institute drops fast with volume; land 5 before optimizing.

Later (10+ institutes): CAC, LTV:CAC, churn, payback, NRR become the dashboard.
