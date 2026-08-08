# TrigunAI — Patna Field GTM + Marketing Strategy

> **The one-month bet (2026-07-16 → 2026-08-16):** stop guessing on the phone, go meet real
> coaching-institute owners face-to-face in Patna, and let those meetings tell us what education
> actually needs an agentic-AI solution for. Acharya is our first hypothesis; the field is the
> test. First hire (Rohan) starts today.
>
> Supersedes the pure-calling 50-in-50 phone test. Owner: Deepak. Reviewed weekly.

---

## 0. Why we pivoted (the ground-truth that earned this)

Deepak personally sat on the **first 5 Maya-accepted demo calls**. The signal was loud and
consistent: **institute owners don't buy a tutor over the phone. They expect a person to come to
the office and explain it.** Coaching in Patna is a relationship-and-trust business. A voice call
gets you a "haan bhejiye kisi ko" — send someone — not a "yes."

That single insight rewrites the motion:

| Old model (phone-first, national) | New model (field-first, Patna) |
|---|---|
| Maya cold-calls → book a *phone demo* → remote onboard | Maya warms/confirms → **Rohan visits the office** → onboard in person |
| Sell "Acharya, our AI tutor product" | **Solve the institute's real pain** with agentic AI; Acharya is the spearhead |
| Spread across 10 cities of accepted leads | **Patna only** — density so one rep can walk between offices |
| Product-led ("buy this") | **Discovery-led** ("what's breaking in your workday?") |

**This is not a small tweak — it's the first time TrigunAI touches real users with a human hand.
That is exactly what the PMF audit begged for. Good instinct. Now the discipline is to run it
narrow and honest.**

---

## 1. The new operating model

```
   Deepak shortlists Patna institutes (by area cluster)
        │
        ▼
   Maya (AI voice) pre-calls  ──►  warms + confirms interest + books a visit window
        │                              (or: Rohan walks in cold — no call needed)
        ▼
   Rohan VISITS the office  ──►  discovery ("what's your biggest daily pain?")
        │                         + live Acharya demo on his phone
        ▼
   Interested?  ──►  onboard to a FREE PILOT (branded Acharya on their real subject)
        │              Deepak provisions the tenant (acharya-technology-transfer)
        ▼
   Pilot used by real students  ──►  refine from real feedback  ──►  first PAID
```

**Roles (who owns what):**
- **Deepak (CEO):** shortlist institutes, own strategy, **ride along on the first / key visits**
  (trust + you learn fastest in the room), provision Acharya tenants, review Rohan's daily log.
- **Rohan (Field Sales & Onboarding, Patna):** in-person visits, discovery, demo, onboarding,
  **same-day logging**, pain-point capture. ₹10k fixed + ₹200/visit (cap 25/mo) + ₹500/converted
  visit + ₹1,100/first-payment. No cash handling — payments go to the official link only.
- **Maya (AI voice):** pre-call to warm and book the visit; still the top-of-funnel dialer.
  Rohan controls Maya himself from his Claude (see `rohan-field-caller` skill), so there's no
  separate phone-caller role — one rep owns Patna end-to-end (call + visit + onboard).

---

## 2. Positioning: solution to education, not "buy my product"

> "We are trying to give solutions to the education industry — not sell a product. On that pain
> point, Acharya and our other systems will grow. **Acharya is a hypothesis; it gets clarity when
> it meets real users.**" — Deepak, 2026-07-16

Hold this line, but with one guardrail so it doesn't drift into unpaid consulting:

- **Lead with the pain, not the product.** Open every visit with discovery: doubt-solving after
  class hours? revision that doesn't happen? parents asking for updates? test/paper generation
  eating the teacher's nights? attendance/fees chaos? Let *them* name the fire.
- **Acharya is the default spearhead.** When the pain is "students don't revise / ask doubts at
  night / no personalised practice" — that's Acharya, live, today. Demo it in the room.
- **Guardrail against becoming a custom-agency:** if a totally different pain shows up, *log it*
  as a pattern — don't promise a bespoke build on the spot. We productise pains we hear **3+
  times**, not one-offs. Discovery refines the product; it doesn't replace it with 10 custom jobs.
- **The real deliverable of month one is a ranked pain-point map of Patna coaching institutes** —
  that's worth as much as the first ₹, because it tells us what to actually build.

---

## 3. Geographic focus — Patna, by cluster

Patna is a genuine coaching hub (BSEB boards + NEET/JEE + banking/SSC + spoken-English). Density
is the whole point: cluster the shortlist so Rohan does **3–4 visits in one trip**, not one visit
across town.

**Candidate clusters to shortlist (Deepak fills the actual names):**
- **Musallahpur Hat / Bhikhna Pahari** — the classic Patna coaching bazaar, highest density
- **Boring Road / Rajapul** — mid-premium tuition + spoken English
- **Kankarbagh** — huge residential + coaching belt
- **Rajendra Nagar / Kadamkuan** — established tuition names
- **Patliputra / Bailey Road** — newer/premium centres

> **Action for Deepak:** build the shortlist as `teacher_gtm/patna_institutes.csv` — columns:
> `name, area/cluster, subject, owner, phone, size(est students), source, priority, maya_precall,
> visit_status, pilot_status, pain_notes`. Start with ~40–50 names; that's a month of field work
> at Rohan's 25-visit cap plus repeats.

---

## 4. The one-month plan (4 weeks, realistic field metrics)

The old "30 phone conversations / 3 pilots / 1 paid by 07-23" test is **retired** — you can't run
30 field visits in 7 days from a standing start, and pretending otherwise is the dishonesty the OS
forbids. Replacing it with a field-honest test:

| Week | Dates | Theme | Target (leading) | Target (gate) |
|---|---|---|---|---|
| **W1** | 07-16→07-22 | Stand up the engine | Rohan equipped + trained; shortlist ≥40; Maya pre-calls cluster 1; **8–10 first visits** | 2–3 pilots *agreed* |
| **W2** | 07-23→07-29 | Density push | **20+ visits**; first pilots go **live** on their subject; first proof clip | 3–5 pilots live |
| **W3** | 07-30→08-05 | Convert | deepen the winners; refine offer from real objections | **1st cleared payment** |
| **W4** | 08-06→08-16 | Systematise | hit Rohan's 25-visit cap; write the repeatable "Patna field motion" playbook | 2–3 paid; go/no-go on rep #2 |

**Continue / kill (decide 08-16):**
- ✅ **Double down** if: ≥1 paying institute **and** a pain-point that repeats 3+ times that Acharya
  (or an obvious adjacent) solves. → hire field rep #2, add the next cluster/city.
- ❌ **Rethink** if: <2 pilots ever went *live* (real students using it) and no repeated solvable
  pain surfaced. Then the problem is the product or the market, not the effort — go back to CEO OS.

---

## 5. The NEW marketing strategy — marketing now serves the field

Under field-first, "post a reel → click a CTA link" is low-leverage. Marketing's job for the next
month = **make Rohan's knock land warm and turn every pilot into the reason the next one says
yes.** Four pillars:

### Pillar 1 — Local "heard-of-them" layer (so the name isn't cold)
When Rohan says "TrigunAI / Acharya," the owner should half-recognise it.
- Google Business Profile: **TrigunAI Innovations, Patna** (real local presence, reviews later).
- Patna-tagged Instagram/FB posts in **Hindi + Bihar exam context** (BSEB, NEET/JEE, Patna
  coaching). Not brand-abstract — local and specific.
- 2–3 posts/week, geo-relevant. Goal is familiarity, not clicks.

### Pillar 2 — The field kit (highest-leverage marketing right now — it *converts*)
The assets Rohan carries into the room:
- **60-sec Acharya demo** on his phone (already have `acharya_teacher_demo_v3.mp4` — verify it's
  the field cut).
- **One-page leave-behind in Hindi:** what Acharya does for *their* students + the offer + a QR to
  a live demo tenant. (Build this — it's the single most important asset this week.)
- **WhatsApp follow-up template** (owner shares to their teacher group).
- **A "how a teacher uses it" story card** once we have the first pilot.

### Pillar 3 — "Agentic AI for education" thought-leadership (makes the meeting worth taking)
Short, credible content that an institute owner respects — position TrigunAI as *the people
solving education's workflow pains with AI agents*, not a tutor vendor:
- 60–90s clips: "how an AI agent handles after-class doubts / nightly revision / auto-generated
  practice papers / parent updates for a coaching institute." One pain per clip.
- Post to the channels + reuse as Rohan's talking points. This is where the reel-machine
  (`content-daily-engine`) redeploys — same engine, new target: **local credibility, not national
  reach.**

### Pillar 4 — The proof flywheel (the compounding engine)
Every pilot becomes marketing:
- Short clip / quote / before-after from each live institute (with permission).
- One happy Musallahpur teacher is why the next 5 in that lane say yes. **This is how field sales
  compounds** — social proof is local and specific in this market.

> **Marketing's success metric this month is NOT views.** It's: (a) did the field kit exist and
> get used, (b) did local familiarity rise (owners saying "haan, suna hai"), (c) did we turn ≥1
> pilot into a proof asset. Reach is vanity here.

---

## 6. What Deepak must DROP for the month (the focus tax — non-negotiable)

A solo founder can't add a field operation *and* keep five creative blocks alive. The Witness
question is: **what are you killing to make room?** For the next month, the honest answer:

- ⏸️ **Drone / Robotics AI** — already parked. Stays parked.
- ⏸️ **Flow Art VR "to Live"** — pause the build push. (Channel content only if it doubles as
  Pillar-3 marketing.)
- ⏸️ **New course scripting** — pause *unless* it directly makes a pilot sellable to a real
  institute's subject.
- ✅ **Keep, aimed at Patna:** field ops (Rohan) · Acharya provisioning · field-supporting
  marketing (the 4 pillars) · daily log discipline.

The 5-block routine compresses to **3 blocks, all pointing at Patna** (see the updated
`daily_routine/PLAN.md`). Fewer blocks done well > five half-done. This is gate-first, literally.

---

## 7. Metrics that matter (track weekly, honestly)

- **Activity:** visits/week (target ~6, cap 25/mo) · Maya pre-calls made
- **Leading:** in-person demos given · pilots *agreed* · pilots *live* (real students using it)
- **Gate (lagging):** first cleared payment (UTR, not invoice) · # paying institutes
- **Learning (the sleeper metric):** distinct pain-points logged + which repeat 3+ times

Log home: `teacher_gtm/` — Rohan's visits in `leads/rohan_field_log.csv` (same-day), pains in
`teacher_gtm/08_PAIN_POINT_LOG.md`, milestone in `MILESTONE_50_IN_50.md` (reframe its targets to
field, or supersede it with this doc's W1–W4 table).

---

## 8. Honest risks (the Witness flags)

1. **Focus is the whole game.** This works only if the drops in §6 actually happen. If drone/VR/
   courses creep back in, the field engine starves. Guard it.
2. **Solution-led can drift into unpaid consulting.** Keep Acharya as the default sell; productise
   pains heard 3+ times; don't hand-build one-offs. (§2 guardrail.)
3. **New field rep, real money, real customers.** The appointment letter handles it well (no cash
   handling, honest-claims clause). Enforce same-day logging from Day 1 — an unlogged field week is
   invisible and unpayable.
4. **Retiring the old test honestly.** The 07-23 phone test had pre-committed kill criteria. We are
   not quietly abandoning it — we are **explicitly replacing** it with the W1–W4 field test because
   the motion changed. Recorded here so the OS stays honest.
5. **Patna-only is right for density, but it's one market.** A win here must be *documented as a
   repeatable motion* (W4) so it ports to the next city — otherwise it's a local fluke, not PMF.

---

*Created 2026-07-16 on Deepak's field-first pivot. First hire: Rohan Kr. Saurabh (field, Patna).
Companion: `trigunai-ceo` (gate + weekly review), `teacher-outreach-engine` (the daily loop),
`acharya-technology-transfer` (provision a pilot), `content-daily-engine` (the 4 marketing pillars).*
