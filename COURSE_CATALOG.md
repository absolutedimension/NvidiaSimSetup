# TrigunAI Course Catalog & Monetization Plan

> **Single source of truth** for the course catalog, how it maps to the YouTube series,
> where VR fits, the infra moat, monetization tiers, and the July 18 launch plan.
> Created 2026-06-13 (CEO session). Owner: Deepak.
> Companion docs: `youtube_series/SERIES_BIBLE.md` (content), skill `trigunai-content-strategy`
> (episode catalog), `COURSE_OUTLINE.md` (the VR flagship), `project_hub/CEO_BRIEFING.md` (status).

---

## 1. The spine

**The YouTube series ("AI is the Universal Mind") is the free funnel. The courses are the paid product.**
Each episode is a faculty of mind, each faculty is a technology, each technology is a course.

| Ep | Faculty of mind | The technology | Feeds course | Infra-heavy? |
|---|---|---|---|---|
| 1 · Attention | Focus / what to ignore | Transformers · LLMs | Agentic + ML (foundation) | low |
| 2 · The Learning Loop ✅ | Learning / habit | **RL · Isaac Sim** | **Robotics / Physical AI** | 🔥 high (GPU) |
| 3 · Imagination | Dreaming form | Diffusion / generative | Machine Learning | med (GPU) |
| 4 · Meaning | Holding meaning | Embeddings · vector space | Machine Learning | low–med |
| 5 · Intuition | Knowing w/o reasoning | Neural nets · approximation | Machine Learning | med (GPU) |
| 6 · Will | Wanting / acting | **Agentic systems** | **Agentic Systems** | low |
| 7 · Getting Better | Learning from error | Gradient descent | Machine Learning | med (GPU) |

The series collapses into **four course tracks**: Machine Learning · Agentic Systems ·
Robotics/Physical AI · and the one that is *not* a faculty of mind → **VR/MR**.

---

## 2. Where VR fits — the answer

**VR is not a faculty of mind. The series teaches the *mind*; VR is the *body*.**
That's the missing half, and it's the most defensible thing TrigunAI owns. VR shows up
**three ways** — don't force it into one:

1. **Its own course** — "Build & Ship Your First VR/MR App" (`COURSE_OUTLINE.md`, 11 modules,
   Module 1 scripted). Deepak's deepest, battle-tested skill (Quest app → Meta alpha). Lowest
   competition of any course here. Standalone audience/funnel; does NOT need the series.
2. **The embodiment layer of Physical AI** — this is where VR *connects* to the series.
   Ep 2 is "a robot learns in a simulator." VR is how a human steps *inside* that simulator:
   digital twin, teleoperation, watching a trained policy run in a headset. **VR + Isaac Sim +
   a trained policy = the Physical AI course** — almost nobody has both halves. Deepak does.
3. **The delivery mechanism** — the VR classroom (Gurulok codebase) is *how the premium live
   classes get taught*. Part of what the 50k tier buys is "attend class inside VR."

**One line:** *the series teaches the Mind; VR is where the Mind gets a Body and a World.*

---

## 3. The moat (the differentiator to say out loud)

> "I don't just teach the theory — I give you the NVIDIA GPU and the Isaac Sim setup to
> actually train it, and you can attend class inside VR."

Generic Udemy ML/robotics courses **cannot** offer provided-GPU + VR delivery. TrigunAI already
runs the exact infra (EC2 A10G, Isaac Sim, NVIDIA content-agent stack). **Provided-infra +
VR-delivered = the premium tier that justifies ₹50k+.**

⚠️ **Honest warning:** student GPU provisioning is operationally heavy — multi-tenant access,
per-student idle-cost control (every hour bills TrigunAI), support, security, single-g5.2xlarge
quota in us-east-1. It is a real product to build, **not a launch-day checkbox.** Do NOT promise
provided-infra for the July 18 launch. Pilot it with course #2, after revenue + 5 real students.

---

## 4. Monetization model (LOCKED 2026-06-17 — recorded free, live = paid)

**Founder decision (2026-06-17): the recorded course is FREE and PUBLIC on YouTube — it's the
hook + reference. The ONLY chargeable product is LIVE CLASSES.** (Reversed the earlier
membership-gated plan.)

| Tier | What | Price | Platform |
|---|---|---|---|
| Free | YouTube series + shorts + **full recorded VR/MR course (9 modules, EN+HI, public)** | ₹0 | YouTube |
| **Paid — LIVE classes** | Live VR/MR cohort taught by Deepak + provided GPU/Isaac-Sim infra + hands-on build + community | **the chargeable product** (₹ TBD; cohort/seat or ₹50k premium) | VR app + EC2 + learn.trigunai.com |

**Why this works:** free recorded content is the strongest top-of-funnel (max reach, builds
trust, "I built this, here's how"); the live cohort is what people actually pay for — real-time
help, accountability, a working GPU, community. Recorded videos are the *reference* students
return to; the live class is the *transformation*.
**Watch-out (CEO):** revenue now depends entirely on actually *running* live classes (Deepak's
time, scheduling, a cohort offer). The recorded library can't be re-sold once it's free — so the
live offer + its pricing is the whole business. Stand that up next.

---

## 5. The July 18 launch plan (35 days, solo)

**Deepak's decision (2026-06-13): launch THREE courses — VR/MR, Agentic Systems, Machine
Learning — leveraging the ready video pipeline (script + render).**

**CEO-structured for truth (tiered completeness — three real listings, three buy buttons,
without pretending 30 polished videos render in 35 days):**

| # | Course | July 18 state | Why |
|---|---|---|---|
| 1 | **VR/MR App** (flagship) | **FULLY complete** — all modules recorded, listed, buy button, target ≥5 paid | Deepest skill; Module 1 already scripted; only course with a head start; least competition; doubles as the classroom |
| 2 | **Agentic Systems** | **Drip-launch** — full curriculum published + first 2–3 modules live + buy button ON, rest weekly | Hot demand, smallest scope, low infra need |
| 3 | **Machine Learning** | **Drip-launch, sequenced last** — curriculum + first modules + buy button ON | Most competitive market → give it the least-rushed curriculum |

"Drip-launch" = the **standard Udemy pattern** (the OS itself: "launch with 4–6 modules, add
the rest post-launch"). Three products selling on July 18; each completes over the following weeks.

> ⚠️ **Tradeoff on the record (Deepak's call):** three *fully-polished* courses (≈24–30 module
> videos + two curricula designed from scratch for ML & Agentic) in 35 days solo is ~50+ hrs/week
> and risks slipping the date AND burnout. The tiered model above is the de-risked version. If
> Deepak insists on three fully-complete, the date moves — that is a conscious choice, not a surprise.

### Minimum sellable unit per course (the bar for "launched")
- A title + landing description mapped to a real job/skill outcome
- A published curriculum (module list + learning outcomes)
- **First 2–3 modules recorded and watchable**
- A price + a working buy button (Udemy listing live)
- One free YouTube teaser pulled from the course → email capture

### Sequencing after July 18
Robotics / Physical AI = **course #4**, and the home of the provided-GPU premium + ₹50k live
cohort (it's where the infra moat is strongest and pairs with Ep 2). Build it once the first
three are selling and the funnel has converted at least one cohort.

---

## 6. The honest scoreboard (what "on track" means)

By **July 18**, the gate is unchanged:
- **(a)** ≥1 course fully live + public, **(b)** with a buy button, **(c)** ≥5 paying students.

Leading indicators that must move off zero *before* then:
- Episodes published publicly + email list started (this week)
- First pre-enrollments / waitlist signups by **July 10** (zero = the offer isn't landing → diagnose)

---

*Last updated 2026-06-13. Plan: 3-course tiered launch (VR complete + Agentic & ML drip),
series = funnel, infra+VR = the moat, ₹50k live-infra cohort = the real money (post-launch).*
