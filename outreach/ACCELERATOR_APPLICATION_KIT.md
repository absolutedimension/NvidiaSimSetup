# TrigunAI — Accelerator / Grant Application Kit

> Reusable answer set for **Google for Startups Accelerator: India (AI-First)**, **Microsoft for Startups
> Founders Hub**, **Startup India Seed Fund Scheme (SISFS)**, and any similar AI/edtech program.
> **Ground-truth rule (do not violate):** we are **pre-revenue, 0 paid**. Every claim here is true today.
> Numbers in `[FILL: …]` are placeholders — put the REAL current figure before you submit. Never invent
> revenue, student counts, or "thousands of users." "None yet" is an acceptable, honest answer.

_Last updated: 2026-07-01. Owner: Deepak. Source of truth: `trigunai-ceo` OS._

---

## 0. Fill-these-first (real numbers, before any submission)
- [ ] `[FILL: # of people who have chatted with Acharya on WhatsApp]` (from the VM `~/.openclaw/students/`)
- [ ] `[FILL: # of LMS signups]` (from `/admin`)
- [ ] `[FILL: # of interactive-lesson completions / learning events]`
- [ ] `[FILL: # teacher-onboarding requests received]` (once the pamphlet is out)
- [ ] DPIIT recognition status (in progress → needed for SISFS)
- [ ] Paid customers: **0** (state honestly; warm pipeline = 1 teacher at ₹5k, verbal)

---

## 1. One-liner (elevator pitch)
**TrigunAI builds Acharya — an autonomous AI tutor on WhatsApp that teaches anyone to *build* with AI,
one-on-one, in English & हिंदी — and lets teachers run their own tutoring business on top of it.**

Alt (agentic-AI framing, for Google AI-First): *"An agentic AI teaching system: a fully autonomous
multi-agent tutor (LLM reasoning + spaced-repetition + per-learner memory) delivered over WhatsApp and web,
now opening as rails for micro-educators."*

## 2. The problem
Hundreds of millions of Indians want to be part of the AI economy but are stuck: courses are passive video,
1:1 tutoring doesn't scale, and quality teaching is locked to expensive urban coaching. Meanwhile millions of
capable graduates and local tutors want to run a teaching business but have no tech, no AI, and no rails.

## 3. The solution / product (what exists TODAY)
- **Acharya** — an autonomous agentic tutor live on **WhatsApp** (official Meta Cloud API) + web, teaching
  1:1 with **persistent per-learner memory + spaced-repetition recall grading** (Bloom 2-sigma target).
  Multi-course, course-switching, bilingual (EN/हिंदी). Built on an agent framework (OpenClaw) over Azure OpenAI.
- **LMS** (acharya.trigunai.com) — 10 courses, 40+ interactive Duolingo-style lessons, progress tracking,
  admin + analytics, subscription billing (Razorpay) wired.
- **Teacher rails (new)** — teachers onboard via WhatsApp/web; their students learn with Acharya; a teacher
  dashboard is the next build. B2B2C: the teacher does acquisition, we provide the AI + tech.
- **Physical AI engine (deep-tech, secondary)** — an autonomous drone cinematographer RL policy
  (Isaac Sim PPO → ONNX ~80KB, 50Hz on-device) + ModusXR AR focus modes. This is the genuinely deep-tech
  track for deep-tech-specific programs.

## 4. Why now / why us (the unfakeable edge)
Founder Deepak Kumar is a self-taught builder — flow dancer who taught himself to ship a Meta Quest VR app,
train RL drone policies, and build production AI systems, using AI as his tools. TrigunAI teaches *that* path:
not "use AI," but "build with it." The teaching method is proven on the founder's own shipped work, and the
tutor itself is a working autonomous agent — the product is a demonstration of the capability it teaches.

## 5. Technology (honest stack)
- Agentic layer: OpenClaw multi-agent (student tutor + admin agent) on **Azure OpenAI** (gpt-5.5 / 4o-mini),
  WhatsApp Cloud API bridge, per-learner JSON profiles, deterministic SRS recall grading, event-log dataset
  for a future knowledge-tracing / RL teaching model.
- App: FastAPI + Postgres on **Azure Container Apps**; static + Studio on a second container.
- Physical AI: NVIDIA Isaac Sim / Isaac Lab (PPO), ONNX export, OVRTX render, VLM quality gate. **NVIDIA
  Inception member.**

## 6. Traction (STATE HONESTLY — pre-revenue)
- **Live & in-market:** Acharya answering real learners on WhatsApp + web; `[FILL: N]` people have chatted;
  `[FILL: N]` LMS signups; `[FILL: N]` lesson completions.
- **Paying customers: 0** (pre-revenue). **Warm pipeline:** 1 tuition teacher verbally committed to ₹5,000/mo
  × 6 months (B2B2C), not yet cleared.
- **Built, not hype:** company registered (Pvt Ltd), 5 live domains, NVIDIA Inception, bilingual course library.
> Do NOT write "thousands of learners" or any revenue figure. If a form demands revenue, answer **pre-revenue**.

## 7. Business model
- **B2C:** Acharya subscription ₹499/mo (7-day free trial).
- **B2B2C (the wedge):** teachers pay **₹4,999/mo** to run their class on our rails (P1, has students);
  aspiring-tutor grads get a guided qualification gate → **revenue-share** (P2, no cash upfront).
- Compounding assets: the learner email list + the learning-event dataset (trains the teaching model).

## 8. Market
India edtech + AI-upskilling; the "AI economy access" wedge (individual learners) plus the micro-educator/
tutor-entrepreneur market (P1/P2). Bilingual (EN/हिंदी) unlocks the non-metro majority.

## 9. Team
- **Deepak Kumar** — Co-Founder, **CEO & CTO** (engineer-founder; runs the Learning Engine + owns the build).
- **Avinash** — Co-Founder, **Chief Research Officer** (Physical AI Engine / ModusXR research).

## 10. Company facts
- Trigunaï Innovations Pvt Ltd · CIN **U86909BR2025PTC078945** · registered Patna, operational Patna + Mumbai.
- NVIDIA Inception member. DPIIT recognition: **in progress** `[FILL: status]`.
- Sites: trigunai.com · acharya.trigunai.com · studio.trigunai.com · physical-ai.trigunai.com.

---

## 11. The ASK — tailored per program
- **Microsoft for Startups Founders Hub** → Azure + Azure OpenAI credits (we run entirely on Azure — direct
  cost offset). No accelerator narrative needed; software-product eligibility. **Lowest effort — do first.**
- **Google for Startups Accelerator: India (AI-First)** → equity-free seat + up to $350k GCP credits +
  DeepMind/Cloud mentorship. Lead with the **agentic-AI + education** angle (§1 alt, §3, §5). Show the live
  Acharya + `[FILL: N]` users as validation. Risk: they favor Seed–Series A with traction — foreground the
  working autonomous agent + real users.
- **SISFS (Startup India Seed Fund Scheme)** → ₹20L PoC grant + ₹50L convertible (non-dilutive-ish).
  **Blocked on DPIIT recognition — finish that first.** Apply via incubators; emphasize pre-revenue,
  tech-driven, commercial potential, Indian-owned (all true).
- **Deep-tech programs (e.g. Accenture-type)** → lead with the **Physical AI / drone RL** engine, NOT Acharya.

## 12. Standard-question crib (paste + trim)
- *What does your startup do?* → §1
- *Problem?* → §2  ·  *Solution?* → §3  ·  *Why you?* → §4  ·  *Tech / IP?* → §5
- *Traction / customers?* → §6 (pre-revenue; live users; 1 warm teacher)
- *Revenue stage?* → **Pre-revenue**  ·  *GTM?* → **B2C + B2B2C (teachers)** (§7)
- *Business/revenue model?* → §7  ·  *Market?* → §8  ·  *Team?* → §9  ·  *Ask?* → §11
