# TrigunAI — Course Indexes (for the landing page)

> **Single source for the "what's inside each course" copy.** Full module index + a one-line
> brief per module, for every course we showcase so a visitor can register.
> Created 2026-06-13 (CEO session). Owner: Deepak.
> Companion: `COURSE_CATALOG.md` (the spine + monetization), `COURSE_OUTLINE.md` (the VR flagship in full),
> `landing-page-handoff/courses.ts` (this same data as structured code the site renders),
> `landing-page-handoff/COURSES_HANDOFF.md` (build instructions).

---

## The lineup (what the landing page offers)

| # | Course | From episodes | July 18 state | Register CTA on site | Level | Modules | ~Hours |
|---|---|---|---|---|---|---|---|
| 1 | **Build & Ship Your First VR/MR App** ⭐ flagship | (not a faculty — the *body*) | **Fully complete** | **Reserve your seat** | Beginner → Shipped | 11 | ~14 |
| 2 | **Build Agentic AI Systems** | Ep 6 · Will | Drip-launch (curriculum + first modules) | **Reserve your seat** | Beginner → Practitioner | 9 | ~10 |
| 3 | **Machine Learning & Its Math** | Eps 3·4·5·7 | Drip-launch, sequenced last | **Reserve your seat** | Beginner → Builder | 10 | ~12 |
| 4 | **Physical AI — Train a Robot in Simulation** | Ep 2 · Learning Loop | **Post-launch** (the ₹50k live+GPU tier) | **Join the waitlist** | Intermediate | 8 | ~10 |
| 5 | **Build Your AI Video Studio** *(parked — future)* | (the production craft) | **Post-launch backlog** — not on July 18 | **Join the waitlist** | Beginner → Creator | ~8 (draft) | ~10 |

**The honest line for the page:** the series is the *why* (free, on YouTube). The courses are the
*how* — where you build it for real, with provided GPU access and live classes inside VR. Taught by
someone who shipped a VR app to Meta and trains real policies on NVIDIA GPUs. No invented numbers,
no testimonials we don't have.

> ⚠️ **Truth marker for Deepak (not for the page):** index ≠ course. Showing all 4 indexes is free
> marketing copy. Only VR/MR is recorded. Agentic + ML launch July 18 with their first 2–3 modules
> live and the rest weekly (standard Udemy drip). Robotics is course #4 — waitlist only until the
> first three sell and one cohort converts. Don't let a polished index page convince anyone (including
> us) that the courses are done.

---

## Course 1 — Build & Ship Your First VR/MR App ⭐

**Full title:** Build & Ship Your First VR/MR App — AI-Powered Development with Unity & Meta Quest
**Tagline:** Use AI coding agents (Claude Code) to build a real VR/MR app from scratch — hand tracking,
passthrough MR, multiplayer — and submit it to Meta's Store. No coding experience required.
**You build:** *ZenSpace* — a VR/MR meditation room, one growing project across all 11 modules, shipped to Meta.
**For:** complete beginners, career-changers, indie creators. Coders 10x their speed; non-coders let the AI write the C#.
**Need:** a Windows PC + a Meta Quest 2/3/Pro + a USB-C cable. No prior Unity/VR experience.
**Outcome:** a real VR/MR app, running on your headset, submitted to Meta's App Lab — a thing you can hand an interviewer.

| # | Module | What's inside (brief) |
|---|---|---|
| 1 | Setup — Unity, Quest & your dev environment | Install Unity 6 + Meta XR SDK, configure for Quest, get a room running on your headset. *(This module is the free YouTube teaser.)* |
| 2 | Your AI coding partner — building VR with Claude Code | The modern workflow: describe it in English → the agent writes the C# → you test in VR → iterate. The 5-part VR prompt template. Unlocks non-coders. |
| 3 | Hands & controllers — interacting with the world | Hand tracking + controllers, grab/throw with physics, haptic feedback. Build grabbable meditation stones. |
| 4 | VR UI — menus, buttons & panels that work | World-space UI (the kind that doesn't make people sick), poke + laser interaction, a working breathing-guide timer. |
| 5 | Environment & audio — making VR feel like a place | Skyboxes, Quest-friendly lighting, particles, spatial audio, free asset sources. Turn a demo into an experience. |
| 6 | Locomotion — moving without getting sick | Teleport, smooth move, snap turn, comfort vignette — and letting the user choose their comfort mode. |
| 7 | Saving data & session logic | PlayerPrefs + JSON persistence, a Menu→Session→Summary state machine, "welcome back" memory across sessions. |
| 8 | Multiplayer basics — sharing VR with others | Photon Fusion free tier, networked head+hands avatars, spatial voice chat, a shared room. |
| 9 | Mixed reality & passthrough — VR meets your real room | Quest 3 passthrough, Scene API, spatial anchors — place virtual objects in your *real* room. The skill most senior VR devs don't have. |
| 10 | Performance & polish — making it Quest-ready | Profiler, draw-call batching, ASTC textures, holding 72fps, icon/splash/loading, the Meta VRC checklist. |
| 11 | Ship it — from build to the Meta Store | Developer account, keystore signing, release APK, store listing, privacy policy, age rating, submit for review. The module nobody else teaches. |

**Why it's the flagship:** deepest, battle-tested skill (Deepak shipped EnergyField to Meta alpha),
the *least* competitive niche here, and it covers 15/15 of the topics the top competing course covers 5.
The AI-coding-agent workflow makes it the only course of its kind.

---

## Course 2 — Build Agentic AI Systems

**Full title:** Build Agentic AI Systems — Give a Machine a Goal and the Will to Act
**Tagline:** Build real, working AI agents that do useful work — tool use, memory, planning, multi-step
autonomy — on today's APIs. From a single tool-calling agent to a multi-agent workflow for real tasks.
**Comes from:** Episode 6 — *Will* (wanting and acting).
**You build:** *Ops Agent* — an agent that automates one real small-business workflow end-to-end
(reads an inbox / documents, extracts the tasks, drafts replies, updates a sheet, reports each day).
**For:** founders, operators, developers, and anyone doing repetitive knowledge-work who wants to automate it. No ML PhD.
**Need:** a laptop + an API key (Claude / OpenAI). Light Python helps but the agent writes most of the code.
**Outcome:** a deployed agent doing a real job on a schedule — and the patterns to build the next one.

| # | Module | What's inside (brief) |
|---|---|---|
| 1 | What an agent actually is | LLM + a loop + tools + memory. The anatomy of "will" made concrete — goal in, actions out, when it stops. |
| 2 | Your first tool-calling agent | Function/tool calling, the agent loop, parsing the model's tool requests, returning results, termination. |
| 3 | Tools & integrations — giving it hands | Connect web search, files, a database, a Google Sheet, email — turning an LLM into something that *acts*. |
| 4 | Memory & context | Short-term vs long-term memory, retrieval (RAG basics), managing the context window, what to remember and forget. |
| 5 | Planning & multi-step reasoning | Task decomposition, ReAct, reflection and self-correction — how an agent handles a job that takes 12 steps, not 1. |
| 6 | Reliability & guardrails (the part tutorials skip) | Structured/JSON output, validation, retries, human-in-the-loop checkpoints, and **cost control** so it doesn't burn money. |
| 7 | Multi-agent systems | Orchestrator + worker agents, handoffs, when multiple agents genuinely help — and when they just add chaos. |
| 8 | Deploy your agent | Run it on a server/schedule, a minimal UI, logging and monitoring so you can see what it did and why. |
| 9 | Ship a real business agent | Package the Ops Agent with its playbook/prompt, hand it to a non-technical user, and measure that it actually saves time. |

**Why it's strong:** hottest demand of the four, smallest scope (shippable in the launch window), almost
no infra cost, and taught from real multi-agent systems running in production at TrigunAI — not a toy chatbot.

---

## Course 3 — Machine Learning & Its Math

**Full title:** Machine Learning & Its Math — The Faculties of Mind, Made Buildable
**Tagline:** Understand and build the core of modern ML — the math you actually need, then neural nets,
embeddings, diffusion, and training. Intuition first, code second, math demystified.
**Comes from:** Episodes 3 (Imagination), 4 (Meaning), 5 (Intuition), 7 (Getting Better).
**You build:** three small things from scratch then with PyTorch — a neural net, an embedding search, and a tiny generative demo.
**For:** developers and curious learners who want to *understand* ML, not just call an API — and were scared off by the math.
**Need:** a laptop; we provide GPU access for the training modules. Comfortable with basic Python; high-school math, refreshed in-course.
**Outcome:** you can read, build, and train a small model end-to-end — and you finally *get* what's under the hood.

| # | Module | What's inside (brief) |
|---|---|---|
| 1 | The map | What ML is, the faculties-of-mind frame, supervised / unsupervised / RL in one picture. Where everything fits. |
| 2 | The math you actually need | Vectors, matrices, dot products, and gradients — visual and intuitive, the 20% that powers everything. No fear. |
| 3 | Intuition = function approximation | A neuron, a layer, a network, the forward pass — building "knowing without reasoning" (Ep 5) by hand. |
| 4 | Getting better = gradient descent | Loss, backpropagation, the training loop — coded from scratch so you see *how* a model learns from error (Ep 7). |
| 5 | From scratch → PyTorch | The same network, now in a real framework, on a real GPU. Tensors, autograd, the modern workflow. |
| 6 | Meaning = embeddings & vector space | Word and image embeddings, similarity, and vector search — how machines hold meaning as geometry (Ep 4). |
| 7 | Imagination = generative models | Autoencoders → the intuition behind diffusion → a tiny generator that dreams new images (Ep 3). |
| 8 | Attention & transformers | Why attention won, and a minimal transformer block built up piece by piece (ties back to Ep 1). |
| 9 | Training in practice | Data, overfitting, regularization, evaluation, and the real GPU training workflow — on provided hardware. |
| 10 | A real ML project, end-to-end | Pick one — classifier, embedding search, or generator — train it, evaluate it, and show the result. |

**Why it's last in sequence:** ML is the most crowded market online, so it gets the least-rushed
curriculum. Its edge is the **mind metaphor** (1:1 with the YouTube series, so the funnel is seamless),
**from-scratch-then-framework** teaching, and **provided GPU** — generic Udemy courses can't hand you a trained model on real hardware.

---

## Course 4 — Physical AI: Train a Robot in Simulation  *(post-launch · waitlist)*

**Full title:** Physical AI — Train a Robot in Simulation and Watch It Learn
**Tagline:** The embodiment half. Train reinforcement-learning policies in NVIDIA Isaac Sim, on provided
GPU, and watch them learn inside a VR headset. Where the Mind gets a Body and a World.
**Comes from:** Episode 2 — *The Learning Loop* (RL · Isaac Sim).
**You build:** a trained control policy (a robot/drone/arm that learns to reach a goal), exported and viewable in VR.
**For:** developers and engineers ready to step from screen-AI into embodied AI / robotics.
**Need:** the premium tier — provided NVIDIA GPU + Isaac Sim setup + live cohort. (This is the ₹50k live+infra course.)
**Outcome:** a policy you trained yourself in simulation, plus the sim-to-real and teleoperation concepts behind real robots.

| # | Module | What's inside (brief) |
|---|---|---|
| 1 | Simulation & digital twins | Why we train robots in sim first; what a physics simulator does; the digital-twin idea. |
| 2 | Isaac Sim / Isaac Lab setup (provided) | Get into the NVIDIA stack on provided GPU — the environment generic courses can't give you. |
| 3 | RL basics for control | Agents, environments, rewards, episodes — reinforcement learning aimed at *movement*, not games. |
| 4 | Designing the reward | The craft that makes or breaks a policy — shaping behavior through what you reward. |
| 5 | Training your first policy | Run PPO, read the curves, get a robot that learns to reach its goal. |
| 6 | Sim-to-real concepts | Domain randomization, the reality gap, and what it takes to move a policy toward the real world. |
| 7 | Teleoperation & VR embodiment | Step inside the simulator — drive and watch the policy from a Quest headset (the VR-as-body link). |
| 8 | Deploy & view your trained policy | Export the policy, render it, and watch your trained robot run in VR. |

**Why it's the moat:** "I don't just teach the theory — I give you the GPU and the Isaac Sim setup to
actually train it, and you attend class inside VR." Almost nobody offers both halves. It's deliberately
**after** launch — student GPU provisioning is operationally heavy and shouldn't gate the July 18 date.

---

## Course 5 — Build Your AI Video Studio  *(parked · post-launch · do NOT build for July 18)*

**Full title (draft):** Build Your AI Video Studio — The Craft of AI-Assisted Storytelling
**Tagline (draft):** Build the exact pipeline TrigunAI ships its series with — AI voices, motion
graphics, contextual backgrounds, word-synced captions, compositing — and make content that *means
something*, not faceless slop.
**You build:** your own end-to-end AI video pipeline + a finished narrated episode of your own.
**For:** serious content creators / educators / founders who want studio-quality video without a studio.
**Validated by:** dogfooding — this is the real pipeline that shipped 5 bilingual episodes.
**Status:** parked course backlog. Sequences in **after** the first three courses sell. **Not** part of the July 18 launch.

**Module sketch (draft, not final):** the AI video stack overview · scripting for TTS · AI voices
(F5-TTS) · motion graphics (Manim) · contextual AI backgrounds · word-synced kinetic captions ·
music + focus-audio beds · compositing & render on GPU · bilingual / localization · publishing & channel craft.

> **Decision on record (2026-06-14):** the pipeline is the **workshop, not a product.** We teach
> people to *build* it (this course) — we do **NOT** sell B2B pipeline-setup-as-SaaS (off-brand,
> funded competitors like Synthesia/HeyGen/Descript, and a solo-founder support trap). Reactive
> done-for-you video work = opportunistic cash only, never a marketed offering. Brand guardrail:
> **craft + meaning, never hustle/faceless-channel framing** — sold crudely it cheapens the whole brand.

---

## How "Register" should behave (note for the page)

- **Courses 1–3 → "Reserve your seat."** Capture name + email + which course (+ optional "I have a Quest").
  For launch this is a free pre-enroll / waitlist that proves demand; flip to a paid Razorpay/Gumroad
  reserve link when you're ready to take money. Pre-enrollments before **July 10** are the signal that the
  offer lands — zero means diagnose, don't push.
- **Course 4 → "Join the waitlist."** Same form, tagged Robotics — no price shown, it's post-launch.
- Keep **Subscribe (Substack)** as the soft, always-present CTA; **Register** is the hard CTA per course.
- Honesty guardrails still hold: no student counts, no testimonials, no "trusted by." If there's no number, don't show one.

---

*Last updated 2026-06-13. Indexes for 4 courses; VR/MR recorded, Agentic + ML drip-launch July 18,
Robotics post-launch (waitlist). Data mirror: `landing-page-handoff/courses.ts`.*
