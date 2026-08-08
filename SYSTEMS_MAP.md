# TrigunAI — Systems Map (the living overview)

> **What this is.** The one file that shows the whole business as a *system of feedback loops*,
> not a list of projects. Read it to answer "what affects what" and "why is effort not turning
> into revenue." Built 2026-07-29 from a systems-thinking pass (MIT / John Sterman, *Business
> Dynamics* — policy resistance, the iceberg, reinforcing vs balancing loops, delays).
>
> **Keep it alive.** When a loop opens or closes, update the STATUS BOARD (§5). This doc is the
> control panel; the skills are the hands.

---

## 0. The two laws of this system (read first)

1. **Only R1 makes money — and R1 is a loop, not a funnel.** Content → Traffic → Signup →
   Activated → Paying → revenue → *funds more Content*. A funnel you fill once; a loop must
   **circulate**. It circulates only when it is closed at BOTH ends.
2. **A reinforcing "build trap" keeps R1 cut.** Under pressure of 0-paid, attention flows to
   building (fast, certain reward) and starves marketing (slow, uncertain reward). This is
   *policy resistance*: the fix that feels right (build the product deeper) feeds the thing
   keeping revenue at zero. Breaking it needs an **external constraint** (the daily gate), because
   internal motivation loses to delay.

---

## 1. Loop 1 — R1, the money flywheel (the hero loop)

```
        ┌─────────────────── R1 · revenue funds content ───────────────────┐
        │                                                                   │
   ▼ (OPEN: starved)                                              ▼ (OPEN: billing off)
 [ Content ] → [ Traffic ] → [ Signup ] → [ Activated ] → [ Paying ₹ ] ──► revenue ──┐
   marketing     visitors      account      took a test     ₹199 / ₹249               │
       ▲                          │                                                   │
       │                          ▼                                                   │
       └──── steer ◄──── [ Pulse dashboard ] (control loop B1 — reads funnel)         │
             (under-used)                                                             │
                                                                                      ▼
                                                                            (funds Content) ──► back to Content
```

- **Reinforcing (R).** Each turn should make the next turn bigger.
- **Cut in two places right now:** Content (marketing ships ~1 day in 7) and Paying (billing
  inert). A flywheel cut in two places does not spin slowly — **it does not spin at all.** This is
  the entire "0 paid" situation in one sentence.
- Traffic / Signup / Activated are **already built and waiting.** The middle of the loop is healthy.

---

## 2. Loop 2 — the build trap (the vicious loop that keeps R1 cut)

```
 [ 0 paid ] → [ Build more ] → [ Fast win ] → [ Attention gone ] → [ Marketing ] ──┐
  pressure     feels like fix   commits ship    to building          starved        │
      ▲            (reinforces "build = progress")                                   │
      └──────────────────────── R · still 0 paid, more pressure ◄────────────────────┘
                                   delay: marketing reward is slow + uncertain
```

- **Reinforcing (R), vicious.** Named after Sterman's healthcare "iceberg": above the waterline
  you see "build more → product better"; below it is this cycle.
- **Why it's sticky:** building pays *immediately* (a commit today); marketing pays *slowly and
  uncertainly* (a post now → maybe a signup in weeks → maybe a payment, through billing that's
  off). A well-calibrated controller optimizes the fast, certain signal — so the trap wins the
  hands without any lapse in discipline. **The problem is delay, not willpower.**

---

## 3. All the loops (the full set)

| Loop | Type | What it does | State |
|---|---|---|---|
| **R1 · growth flywheel** | reinforcing | Content→Traffic→Signup→Activated→Paying→funds Content | ⛔ **OPEN** at Content + Paying |
| **build trap** | reinforcing (vicious) | 0-paid → build → fast win → attention gone → marketing starved → 0-paid | 🔴 **ACTIVE** |
| **R2 · quality** | reinforcing (virtuous) | usage → research + LearningEvent → product fixes → better activation → more usage | 🟡 running (but can't start R1) |
| **R3 · bank enrichment** | reinforcing | attempts → which Qs fail → tag/verify → better bank → more value | 🟢 mostly automated |
| **B1 · control (Pulse)** | balancing | dashboard reads funnel → decide → adjust Content | 🟡 built, read-but-not-acted-on |
| **B2 · operator allocation** | balancing | founder attention split across build vs distribute | 🔴 ~90% to build (upstream of all) |

**Key insight:** R2 and R3 are healthy and were fed hard all week — but a virtuous quality loop
**cannot start a stalled flywheel.** It only makes each turn better *once the wheel already spins.*

---

## 4. Leverage points — "change what affects what" (highest first)

1. **Operator attention split (B2)** — controls which loops get fed. Highest leverage, lowest cost.
   This is exactly what the daily gate governs.
2. **Content node (R1 inlet)** — nothing downstream moves without it; Traffic→Paying are built and
   waiting. Feed this one node and the whole right side of R1 lights up.
3. **Billing (R1 outlet)** — until a UTR can clear, "Paying" never registers, so R1 never closes and
   marketing never gets reinforced. **Even a perfect marketing week dead-ends here.**
4. **Pulse acted-on (B1)** — turns guesswork into steering.
5. **Product depth (group A systems)** — improves conversion *per turn*, but multiplies a wheel that
   isn't turning. High effort, ~zero leverage until 1–3 are fixed.

---

## 5. STATUS BOARD — update when a loop opens/closes  *(as of 2026-07-29)*

| Item | Status | Note |
|---|---|---|
| R1 inlet — AUTO channel (YouTube) | 🟢 FED | automated exam-content engine (launchd 11am IST) ships ~4 exam-prep shorts/day → /exam-prep CTA; 16 videos Jul 25–28 (days 2–5). Corrected 07-29 — this was invisible before. |
| R1 inlet — HUMAN channel (LinkedIn/founder) | 🟡 THIN | only 1 founder post (07-25, URL still unlogged); 07-29 post drafted+ready. This is the genuinely starved inlet, not "marketing" wholesale. |
| R1 outlet — ₹249/mo subscription | 🟢 LIVE + VERIFIED | 07-29 traced end-to-end (code + live): subscribe→Razorpay→return→`trialing`→access granted on trialing+card (no "paid-but-locked-out" bug); webhook live on both hosts, rejects unsigned (400), not redirected. Blocker for this path = traffic/conversion, not code. **Open (Deepak-only):** confirm Razorpay dashboard webhook (URL/events/secret) for the "💰 paid" alert + cancellation sync; run the free 14-day-trial smoke test (₹0). |
| R1 outlet — ₹1,299 Exam Pass (LEAD offer) | ⛔ OPEN | the CEO-designated lead offer is only a WhatsApp manual-close link, NOT self-serve. `billing.py` = subscriptions only, no one-time Razorpay Order. This is the real billing build gap. |
| R1 middle (Traffic→Activated) | 🟢 built | dashboard, test-gen, 5-topic model live (lms:v127); SEO pivoted to test-paper angle 07-29 (/exam-prep + /teacher indexable). |
| Build trap | 🟡 PARTIAL | build-heavy weeks, but the "0 marketing" read was WRONG — auto-engine fed YouTube daily. Real trap = attention to build over the *outlet* (billing) + the *human* channel. |
| Pulse (B1) | 🔴 BLIND SPOT | CONTENT_LOG/routine-log didn't see the automated YouTube channel for a week → false "0 marketing" verdict. Measurement loop must cover ALL channels, incl. yt_uploaded.json. |
| Paid students | **0** | the gate; the number the whole system exists to move |

**Corrected diagnosis (07-29):** R1's inlet is *partly* fed (automated YouTube), the middle is built,
so the two truly open nodes are the **billing OUTLET** (no payment can register) and the **human/founder
inlet** (LinkedIn) — plus a **Pulse blind spot** that hid the auto-channel and produced a false zero.
**Close condition for R1:** billing able to clear one real payment (outlet) + a steady founder-voice
channel (human inlet) + a Pulse that counts every channel. The auto-YouTube inlet already turns daily.

---

## 6. The Sterman lens (the mental-model corrections to keep applying)

- **Policy resistance** — the fix that feels right (build deeper) feeds the problem (0 paid). Always
  ask: *does my fix touch the loop that's actually broken, or a healthy one?*
- **No side effects, only effects** — 0-paid is the *direct effect* of the attention split, not bad
  luck from "out there." Own it as endogenous and it becomes controllable.
- **Short-run wins reinforce the wrong model, via delay** — fast/certain (build) out-competes
  slow/uncertain (market) for the hands. Fix = *shorten the marketing feedback delay* (log + score a
  post same-day so it feels like it paid off today).
- **Challenge the boundary** — anything treated as "external and fixed" (billing keys, "I build when
  I sit down") is usually endogenous and feeds back. Pull it inside the model.
- **You can't tell people — they learn by doing in a safe space (the flight simulator)** —
  (a) *for the founder:* the daily log IS the simulator — experience the streak reset cheaply, today.
  (b) *for the product:* Acharya's adaptive test engine literally is a flight simulator for exams.
  Positioning hook: **"fail here, safely, again and again, so you don't fail there"** — not "46k
  questions." Route to `content-marketing-emotion-connect`.

---

## 7. How to use this doc

- **Glance daily** (it's the overview). "What's happening?" = read §5 STATUS BOARD.
- **Before any big effort,** check §4: am I feeding a high-leverage node (1–3) or polishing a wheel
  that isn't turning (5)?
- **When a loop changes,** edit §5 — this is the single source of truth for loop health.
- Companion skills: `trigunai-project-hub` (control tower / topology), `trigunai-ceo` (the gate +
  Witness), `trigunai-daily-discipline` (the daily constraint that breaks the build trap).

*Owner: Deepak. Living doc — keep §5 current.*
