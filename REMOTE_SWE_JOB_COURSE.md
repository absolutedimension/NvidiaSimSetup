# Command the Coding Agent — AI-Era Software Engineering Skills (+ Land the Remote Job)

> **Status:** DRAFT curriculum (2026-06-26, Block 3). Reframed 2026-06-26 around the agent-control
> thesis (Deepak). Designed from a YouTube roadmap script (Nansi Solanki) + TrigunAI's thesis.
> Companion: `COURSE_CATALOG.md` (where this slots in), `trigunai-content-strategy` (funnel).

**Working title:** *Command the Coding Agent* · subtitle: *The fundamentals that make you the human
in charge of AI — and get you hired, remote.*
(Alt titles: "Driver's Seat: The AI-Era Engineer" · "Control the Machine" · "Operator, Not Passenger".)

---

## 0. THE THESIS — why this course exists (read first)

> **AI didn't kill the software job. It killed the engineer who can't *direct* AI.**

The world is split into two stories. Story one: "software jobs are gone, the AI writes the code." Story
two — the true one: the AI writes code *fast and confidently wrong*. Wrong time-complexity, wrong data
model, a design that won't scale, a hallucinated API, a subtle off-by-one. **The only person who can
catch that and steer it is someone with the fundamentals — DSA, LLD, HLD.**

So the fundamentals are not obsolete. **They are the steering wheel.**

- Without them → you are a **passenger** who ships whatever the agent hands you, and can't tell good
  from broken. That engineer *is* replaceable — by a cheaper passenger.
- With them → you are the **operator.** Your judgment × the agent's speed = your output. You read its
  code, find its faults, redirect it, and ship 5× faster than the pre-AI engineer **and** safer than
  the prompt-only "vibe coder."

That is the value employers now filter for, and it is exactly what interviews now test (the script's
own Month-3 round: *"use ChatGPT — now tell me what's wrong with what it gave you"*).

**This is a TrigunAI course, fully on-spine.** It's the same thesis as the agentic work: *the human
stays in command of the machine.* DSA/HLD/LLD are how you earn that command in the coding seat.

---

## 0a. The deeper spine — system design is the grammar of mind

> This is the brand soul under the job outcome. Keep it as the *lens* (per the brand model: a lens,
> not a proof) — the job stays front and center; this is the higher octave that makes the course feel
> like a TrigunAI course and not a bootcamp.

HLD / LLD / system design don't just teach "how to pass an interview." They teach **how complexity
arranges itself into something coherent** — how independent parts coordinate, how information flows,
how a system stays *itself* under load and failure. That is the same question the whole "AI is the
Universal Mind" series asks about the mind. The mappings are structural, not poetic:

| System-design fundamental | What it really teaches | The mind / Universal-Mind echo |
|---|---|---|
| Memory hierarchy (cache → DB → cold) | hot vs cold information, speed/cost tradeoffs | working memory vs long-term memory vs the forgotten |
| Load balancing | distributing finite capacity across demand | **attention** — what gets compute *now* (Ep 1) |
| Message queues / event-driven | decoupled async signal propagation | how one thought fires the next, no central controller |
| Microservices / separation of concerns | specialized modules behind clean contracts | **faculties of mind** — the series' core premise |
| Consistency / CAP | coherence under partial, conflicting input | a single *self* from many parallel processes |
| Fault tolerance / retries / idempotency | staying alive when parts fail | resilience, recovery, habit |

**So the course is a bridge.** A student comes in scared their job is gone. They learn to command the
agent (the pragmatic win). And in learning *how complex systems are designed*, they're handed the
literal design language of mind-like systems — which is exactly what the deeper catalog (ML = learning,
Agentic = will, Robotics = embodiment) then explores. **The job is the doorway; the architecture of
intelligence is the room.** This course is where the pragmatic audience meets the Universal-Mind thesis.

---

## 0b. What this is

A **12-week, live-cohort course** that teaches the fundamentals **as the control layer for AI coding
agents**, and uses that to land a remote offer. Two outcomes, one spine:
1. **Become the operator** — the engineer who commands the agent instead of being replaced by it.
2. **Land the remote job** — because that operator is exactly who's getting hired right now.

Every technical module is taught twice over: *the fundamental itself*, and *how that fundamental lets
you command, read, and correct the agent.* We don't teach DSA to grind LeetCode — we teach the pattern
vocabulary that lets you **spec what the agent should build and catch when it didn't.**

**The one-line positioning:**
> *"Everyone says learn AI tools. We teach you the fundamentals that make the AI tools obey you — and
> get you hired in a market that's quietly desperate for engineers who can drive the agent, not just
> prompt it."*

---

## 1. Who it's for / the outcome

- **For:** engineers with 0–5 yrs who can already code, want a *remote* role, and have ~10 hrs/week.
- **Prereq honesty:** the 90-day plan assumes you've **seen DSA once before** and are *revising*. A
  true beginner needs 5–6 months — say so on the landing page; offer a "DSA from scratch" pre-track.
- **Outcome:** an interview-ready candidate with a live application pipeline, by Day 90.

---

## 2. The core design idea — TWO tracks, ONE lens

The script's biggest mistake is sequencing the job hunt last. We don't — two tracks run in parallel,
every week. And **both are taught through the agent-control lens** (§0): the fundamental, *then* how
it makes you the operator of the AI.

| Track | What it is | Runs | Through the agent-control lens |
|---|---|---|---|
| **A · The Operator's Skill** | DSA → System Design → AI-command → behavioral | the "study" half | every fundamental = a control you use to spec/read/correct the agent |
| **B · The Job Machine** | resume/LinkedIn → company list → referrals → applications → offers | **starts Week 1** | positioned as "I direct AI, I don't fear it" — the hireable story |

Pipelines convert in 6–8 weeks. If applications start in Week 1, the *first offers land while skill
prep is still finishing* — instead of starting the search the day prep ends.

**The agent-control thread (what makes Track A different from a DSA mill):**
- **DSA →** the pattern + complexity vocabulary to *spec* what the agent builds and *catch* when its
  solution is O(n²) dressed as clever. You read its code; you don't trust it.
- **LLD →** the design judgment to tell the agent *which* classes/patterns/APIs — and to reject the
  over-engineered 15-pattern soup it loves to generate.
- **HLD →** the architecture judgment the agent simply doesn't have. You design; it implements; you
  find the scaling fault it missed.
- **AI-command (capstone) →** doing all of the above *live*, under interview and on-the-job conditions.

---

## 3. The 12-week curriculum

### MONTH 1 — DSA revision + the machine starts turning

| Wk | Track A — Skill | Track B — Job Machine |
|---|---|---|
| **1** | DSA mindset: pattern-thinking, time/space complexity, optimization techniques. NeetCode 150 plan begins — arrays, hashing, two-pointers, sliding window. | **Remote-ready resume rebuild** (ATS-safe, impact bullets, remote framing) + **LinkedIn optimization** (headline, "open to work · remote", keywords). Stand up the **application tracker** (Sheet/Notion). |
| **2** | DSA — stack, binary search, linked lists, trees, tries. | **Build the company list** (15–30 remote-first cos — use ChatGPT + LeetCode Discuss lists). Extract job IDs from career portals per your experience band. Start **warm referral outreach** (1–2 LinkedIn msgs/day). |
| **3** | DSA — backtracking, graphs (BFS/DFS), DP intro. | Referral machine in motion: message + hiring-manager-ping templates. **First applications go out.** |
| **4** | DSA — advanced graphs, DP patterns, greedy, intervals. **First timed DSA mock.** | **GitHub/portfolio polish** (remote employers read your code first). Pipeline review: target *N* applications + *M* referral conversations live. |

### MONTH 2 — System Design + interviews start landing

| Wk | Track A — Skill | Track B — Job Machine |
|---|---|---|
| **5** | **LLD** — OOP, SOLID, the **top 5 design patterns** (not 15 — just enough to implement live), API request/response design, class interactions. | First recruiter screens arrive. Build the **STAR story bank** + the **"why remote"** answer. |
| **6** | **HLD foundations** — caching, SQL vs NoSQL, load balancing, CAP, back-of-envelope estimation. | **Phone-screen practice.** Remote-specific: the async/written-communication screen. |
| **7** | **HLD** — message queues (Kafka vs RabbitMQ), rate limiting, sharding, consistency. **LLD mock.** | **Take-home assignment playbook** — many remote cos test with take-homes, not live DSA. |
| **8** | **HLD practice** — design Twitter, YouTube, Uber, Swiggy, Splitwise, Google Drive. **ChatGPT-as-interviewer drill** (paste your design → "you are the interviewer, find the faults"). | **HLD/LLD mock interviews** with experienced engineers pulled from your LinkedIn network. |

### MONTH 3 — Command the agent (the capstone) + closing offers

> This month is the **payoff of the thesis** — everything built in Months 1–2 now becomes live
> command over the AI. It's the signature TrigunAI content and the strongest free-funnel material.

| Wk | Track A — Skill | Track B — Job Machine |
|---|---|---|
| **9** | 🌟 **The AI-command round (TrigunAI signature).** Interviewer says "use ChatGPT/Claude/Gemini" — and tests whether you *blindly trust it* or can **critique the AI's HLD/LLD, endpoints, and code.** Spotting AI mistakes is the whole point: this is the steering wheel from §0 in action. Nobody else teaches it well — it's your wheelhouse. | **Full-loop mock interviews** (DSA + SD + behavioral, back-to-back). |
| **10** | AI **pair-programming under interview pressure** + code review: *is the AI's code actually correct?* | Onsite/final rounds. **Interviewing the company** (remote red flags: async maturity, timezone, on-call). |
| **11** | **Targeted revision** — your weak DSA topics (the **doubt sheet** you built all along), CS fundamentals for *your* stack (FE/BE), deep-dive on your **resume projects** (they will ask). | **Offer stage** — negotiation, evaluating remote offers (comp, equity, timezone overlap, async culture). |
| **12** | **Final mocks** + revise all LLD/HLD notes + confidence. | **Close.** Multiple-offer strategy, accept, remote onboarding. Join the alumni network. |

---

## 4. What we add beyond the source script (the moat)

1. **The agent-control thesis (§0) as the spine** — not "DSA vs AI" but "DSA *to command* AI." This is
   the reframe that turns a commodity prep course into a TrigunAI course. It's the unfair advantage:
   you teach this from lived experience building agentic systems daily.
2. **Parallel job machine** (Week 1, not Month 3) — the single biggest structural improvement.
3. **The AI-command round as a full signature module** (Wk 9–10) — the capstone of the thesis.
4. **Remote-specific layer** — async/written comms, take-homes, timezone, "why remote," GitHub-first.
5. **Resume + LinkedIn + referral system** treated as a *skill*, not an afterthought (referrals are
   the script's own "golden advice" — we systematize it from Day 1), positioned as "I direct AI."
6. **Negotiation + offer evaluation** — the script stops at "you get the interview"; we close the offer.
7. **A doubt sheet + tracker** carried the whole 90 days = built-in revision + pipeline visibility.

---

## 5. Delivery + pricing (fits the LOCKED model)

Matches `COURSE_CATALOG.md §4` — **live = paid**:
- **Format:** 12-week live cohort, ~2 live sessions/week (1 skill teach + 1 mock/review), async
  doubt-clearing in between. Mocks are the product — that's what students can't get from YouTube.
- **Free funnel:** 1–2 YouTube videos pulled from the AI-interview module ("watch me catch ChatGPT
  being wrong in a system-design round") → email capture → cohort invite. This *is* shareable, novel
  content most channels don't have.
- **Price:** cohort/seat (align with the Agentic cohort's ₹ band). The AI-interview module justifies a
  premium over commodity DSA courses.

---

## 6. Catalog placement — ON-spine after the reframe

The agent-control thesis puts this course **on the TrigunAI spine**, not off it. The series teaches
"AI is the Universal Mind"; this teaches *how the human stays in command of that mind in the coding
seat.* It is the **most market-ready, most relatable** entry point in the whole catalog — everyone
feels the "is my job gone?" fear, and this answers it with a plan.

**Strategic role = the bridge course (§0a).** It's the on-ramp where the pragmatic job-seeker audience
first touches the Universal-Mind thesis: they come for the job, learn the grammar of how complex
systems (and minds) are designed, and graduate primed for the deeper catalog (ML · Agentic · Robotics).
Lowest fear-barrier in, highest pull-through to the rest of the catalog.

Add to `COURSE_CATALOG.md`:

> **Course 5 · "Command the Coding Agent"** — the AI-era engineering-skills course: DSA · System Design
> · Agent-command, taught as the control layer for AI coding agents, with a remote-job outcome. The
> broad on-ramp that *also* feeds the deeper AI catalog. Live cohort. Signature module = the AI-command
> interview round. Differentiator = taught by an engineer-founder who builds with agents daily.

---

## 7. Open decisions for Deepak (pick before build)

1. **Title** — lock the name. (Recommend: *"Command the Coding Agent"* — it carries the thesis in 3
   words. Alts in the header.) Positioning is now settled: agent-control course, not a DSA bootcamp.
2. **Who teaches the mocks** — you solo, or you + 1–2 network engineers for system-design mocks? (Scale
   constraint: mocks are the value and the time-sink.)
3. **Beginner on-ramp** — do we offer a "DSA from scratch" pre-track, or hard-gate to "revising"?
4. **Sequencing vs your launch** — this is a *5th* course. It does NOT touch today's Agentic launch.
   Slot it after the July 18 three-course launch unless you want it as the broad funnel sooner.

---

*Draft 2026-06-26. Next step: if positioning approved, turn §3 into a published curriculum + a
landing description + the one AI-interview teaser video (script via `video-script-writer-trigunai`).*
