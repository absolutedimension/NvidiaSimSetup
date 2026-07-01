# "Command the Coding Agent" — Detailed Course Index

> The full topic → subtopic breakdown for the 12-week course. Built 2026-06-26 (Block 3).
> Parent doc (thesis + positioning): `REMOTE_SWE_JOB_COURSE.md`. Owner: Deepak.
>
> **Reading key:** every technical topic is taught on two levels — **(F)** the fundamental itself, and
> **(⌘)** *the command layer* — how that fundamental lets you spec, read, and correct the AI coding
> agent. The ⌘ line is what makes this a TrigunAI course and not a DSA mill (see thesis §0).
>
> **Two parallel tracks run every week:** **A · The Operator's Skill** (study) and **B · The Job
> Machine** (search — starts Week 1, never waits for Month 3).

---

## Prerequisites & on-ramp

- **Assumed:** can already write code in one language; has *seen* DSA once (this is revision-paced).
- **Pre-track (optional, self-paced) — "DSA from Zero":** for true beginners — language basics,
  recursion, the first data structures. Gate the main cohort to "revising," offer this as the ramp.
- **Tools used throughout:** an AI coding agent (Claude / ChatGPT / Cursor), LeetCode/NeetCode,
  a System-Design notebook, GitHub, and a personal **Doubt Sheet** + **Application Tracker** (built Wk1).

---

# MONTH 1 — Fundamentals as the agent's control vocabulary (DSA) + the machine starts

### Week 1 — Complexity thinking + array/hash patterns · Job Machine ignition
**Track A · Skill**
1. **Complexity & the operator's eye**
   - Big-O, Big-Θ, Big-Ω; time vs space; amortized analysis
   - Best/avg/worst case; how to *derive* complexity from code you didn't write
   - ⌘ Reading AI-generated code and naming its complexity — catching "O(n²) dressed as clever"
2. **Arrays & strings** — traversal, in-place ops, prefix sums, sorting-as-a-tool
3. **Hashing** — hash maps, sets, frequency counting, collision intuition
4. **Two pointers** — opposite ends, fast/slow, partitioning
5. **Sliding window** — fixed & variable window, the template
   - ⌘ Prompting the agent to solve with a *named* pattern, then verifying it used it

**Track B · Job Machine**
- **Remote-ready résumé rebuild** — ATS-safe formatting, impact-bullet formula (action + metric +
  tech), tailoring to a target role, the "AI-fluent engineer" framing
- **LinkedIn optimization** — headline, About, "Open to work · Remote," skills/keywords, featured work
- **Set up the Application Tracker** (company · role · job-id · referral · status · next action)

### Week 2 — Linear structures, search & trees · build the target list
**Track A · Skill**
1. **Stack & queue** — monotonic stack, queue/deque patterns
2. **Binary search** — on sorted arrays, on rotated arrays, **binary search on the answer**
3. **Linked lists** — reversal, cycle detection (Floyd), merge, fast/slow pointers
4. **Trees** — binary tree vs BST, DFS (pre/in/post), BFS/level-order, recursion on trees
5. **Tries** — prefix trees, when to reach for them
   - ⌘ Asking the agent for a tree/graph solution and stepping its recursion to find the off-by-one

**Track B · Job Machine**
- **Build the company list** — 15–30 remote-first companies (ChatGPT + LeetCode Discuss "remote" lists)
- **Career-portal pass** — extract real job-IDs per your YoE band; log each into the tracker
- **Referral outreach v1** — start 1–2 warm LinkedIn messages/day (template provided)

### Week 3 — Recursion, backtracking, graphs · referrals + first applications
**Track A · Skill**
1. **Recursion & backtracking** — subsets, permutations, combinations, N-Queens, pruning
2. **Graphs I** — adjacency list/matrix, BFS, DFS, connected components
3. **Graphs II** — topological sort, Union-Find (DSU), cycle detection in directed/undirected
4. **Dynamic programming — intro** — memoization vs tabulation, state design, the "what's the subproblem" habit
   - ⌘ Designing the DP *state* yourself, letting the agent fill the transition, and checking it

**Track B · Job Machine**
- **The referral system** — message templates, hiring-manager ping, "refer me + ping your recruiter"
- **First applications go out** — apply + request referral the same day; track conversion
- **Interview-pipeline hygiene** — follow-up cadence, never let a thread go cold

### Week 4 — Advanced DP, greedy, heaps + first mock · portfolio polish
**Track A · Skill**
1. **DP patterns** — 0/1 & unbounded knapsack, LIS, grid/path DP, interval DP, DP-on-trees
2. **Greedy** — exchange argument, when greedy is correct vs a trap
3. **Heaps / priority queues** — top-K, merge-K, running median
4. **Intervals** — merge, insert, sweep line
5. **Bit manipulation** — masks, tricks, when it matters
6. **First timed DSA mock** (45 min, recorded) → faults go to the **Doubt Sheet**

**Track B · Job Machine**
- **GitHub/portfolio polish** — pinned repos, READMEs, a clean commit story (remote employers read code)
- **Month-1 pipeline review** — applications sent, referrals live, screens booked (numbers, not vibes)

---

# MONTH 2 — System design = the architecture judgment the agent lacks + interviews land

### Week 5 — Low-Level Design (LLD) · screens begin
**Track A · Skill**
1. **OOP, properly** — encapsulation, abstraction, inheritance, polymorphism; composition over inheritance
2. **SOLID principles** — each one with a before/after
3. **The top 5 design patterns** (enough to implement live, not 15): **Strategy, Factory, Observer,
   Singleton, Decorator** (+ Adapter as bonus) — problem each solves, code, smell when misapplied
4. **API / class design** — responsibilities, interfaces, request/response contracts, REST verbs & status codes
5. **Worked LLD** — Parking Lot / Elevator / Splitwise-core: requirements → classes → interactions → APIs
   - ⌘ Making the agent generate an LLD, then **rejecting its over-engineered pattern-soup** down to what's needed

**Track B · Job Machine**
- **STAR story bank** — 6–8 stories mapped to common behavioral prompts
- **The "why remote / why this company" answer** — crisp, honest, non-generic
- First **recruiter screens** — what they actually score, salary-expectation handling

### Week 6 — High-Level Design (HLD) foundations I · phone screens
**Track A · Skill**
1. **The HLD frame** — functional vs non-functional requirements, the interview's 5-step method
2. **Back-of-the-envelope estimation** — QPS, storage, bandwidth, the numbers every engineer should know
3. **Caching** — cache-aside/write-through/write-back, eviction (LRU/LFU), Redis, CDN
   - ⌘ *(mind echo: cache = working memory; see REMOTE_SWE_JOB_COURSE §0a)*
4. **Databases** — SQL vs NoSQL, indexing, normalization vs denormalization, transactions/ACID
5. **Load balancing** — L4 vs L7, round-robin/least-conn, health checks
   - ⌘ *(mind echo: load balancing = attention allocation)*
6. **CAP theorem & consistency models** — strong/eventual, the real-world tradeoffs

**Track B · Job Machine**
- **Phone-screen practice** — talking through code out loud, thinking aloud under time
- **Remote-specific: the async/written round** — clear written communication as a tested skill

### Week 7 — High-Level Design foundations II · take-homes · LLD mock
**Track A · Skill**
1. **Message queues & streaming** — pub/sub, **Kafka vs RabbitMQ** (when each), delivery guarantees
   - ⌘ *(mind echo: queues = how one thought fires the next, no central controller)*
2. **Sharding & partitioning** — strategies, hotspots, **consistent hashing**
3. **Replication** — leader/follower, quorum, failover
4. **Rate limiting** — token bucket, leaky bucket, sliding-window counters
5. **Microservices vs monolith** — API gateway, service discovery, when NOT to do microservices
6. **Reliability & observability** — idempotency, retries, dead-letter queues, logs/metrics/traces
7. **LLD mock** (recorded) → Doubt Sheet

**Track B · Job Machine**
- **Take-home assignment playbook** — scoping, what graders look for, README/tests, time-boxing
- **Standing out** — turning a take-home into a portfolio piece

### Week 8 — HLD case studies (the canon) · mocks with your network
**Track A · Skill** — design, end to end, with tradeoffs spoken aloud:
1. **News feed** — Twitter/X / Instagram (fan-out on write vs read)
2. **Video platform** — YouTube / Netflix (upload, transcode, CDN, recommendations)
3. **Geo & matching** — Uber / Swiggy (geohashing, driver matching, surge)
4. **Ledger** — Splitwise (balances, settle-up, consistency)
5. **File storage & sync** — Google Drive / Dropbox (chunking, dedup, conflict)
6. **Classics** — URL shortener, distributed rate limiter, WhatsApp/chat, Google Docs (collab)
7. **ChatGPT-as-interviewer drill** — paste your design → "you are the interviewer, find the faults"
   - ⌘ The drill *is* the skill: can you defend a design against an adversarial AI?

**Track B · Job Machine**
- **Mock interviews with experienced engineers** pulled from your LinkedIn network (how to ask, how to use feedback)
- **On-site loop prep** — the full-day structure, energy management

---

# MONTH 3 — Command the agent (the capstone) + close the offer

### Week 9 — 🌟 The AI-command interview round (TrigunAI signature) · full-loop mocks
**Track A · Skill**
1. **How interviews changed** — "use ChatGPT/Claude/Gemini" rounds; what they're *really* testing (judgment, not recall)
2. **Driving the agent for HLD/LLD** — prompting for a scaffold, then steering it
3. **Finding the faults** — critiquing an AI-generated design: missing components, wrong DB, no rate limit, hand-waved scale
4. **Spotting hallucinations** — fake APIs, wrong endpoints, plausible-but-wrong libraries
5. **Code review of AI output** — correctness, complexity, edge cases, security, readability
6. **Trust calibration** — when to accept, when to override, how to *say* it in an interview
   - ⌘ This whole week is the thesis made physical: the fundamentals are the steering wheel

**Track B · Job Machine**
- **Full-loop mock** — DSA + System Design + behavioral back-to-back, recorded, debriefed

### Week 10 — AI pair-programming under pressure · final rounds
**Track A · Skill**
1. **The operator loop** — spec → generate → review → test → iterate (and how to keep it tight)
2. **Test-driven AI coding** — writing the tests that catch the agent
3. **Refactoring & debugging AI code** — finding the bug the agent introduced; reading unfamiliar generated code fast
4. **Security review** — injection, secrets in code, broken auth, unsafe deps in AI output
5. **Live build** — ship a small feature with an agent and **defend every line** (the on-the-job reality)

**Track B · Job Machine**
- **Final / onsite rounds** — managing a panel, whiteboard-with-AI variants
- **Interview the company** — remote red flags: async maturity, on-call, timezone overlap, doc culture

### Week 11 — Targeted revision + your-stack fundamentals · the offer stage
**Track A · Skill**
1. **Doubt-Sheet sweep** — re-attempt every question you flagged across 10 weeks
2. **CS fundamentals** — OS, networking (HTTP, TCP/IP, DNS, TLS), DBMS, concurrency basics
3. **Your specialty, deep** — frontend *or* backend per your profile (the stack on your résumé)
4. **Résumé-project deep dive** — be ready to defend every line; the architecture, the why, the tradeoffs
5. **Behavioral mastery** — leadership principles / values rounds, conflict & failure stories

**Track B · Job Machine**
- **Negotiation** — anchoring, competing offers, the "I have another process" play, what's negotiable in remote (base/equity/timezone/equipment)
- **Offer evaluation** — comp structure, equity reality, remote culture, growth, manager

### Week 12 — Final mocks + close + capstone
**Track A · Skill**
1. **Final mock loops** — DSA + HLD + LLD + AI-command, polished
2. **Notes consolidation** — your own one-page cheat-sheets for each pillar
3. **Capstone demo** — the agent-assisted project you built through the cohort (portfolio + talking point)

**Track B · Job Machine**
- **Closing** — multiple-offer strategy, accepting gracefully, backing out kindly
- **Remote onboarding** — first-30-days playbook, setting up to succeed async
- **Alumni network** — staying connected, paying referrals forward

---

## Cross-cutting threads (run the whole 12 weeks)

| Thread | What it is |
|---|---|
| **Doubt Sheet** | every missed question/concept, re-attempted in Wk 11 |
| **Application Tracker** | the live pipeline — built Wk1, reviewed monthly |
| **Capstone project** | one real agent-assisted build, demoed Wk12 |
| **The ⌘ command lens** | every technical topic revisited as "how do I make the agent get this right?" |
| **Weekly mock** | from Wk4 on — the recorded mock is the product YouTube can't give |

---

## Free-funnel content pulled from this index (for `trigunai-content-strategy`)

The highest-share videos live in Month 3: *"Watch me catch ChatGPT being wrong in a system-design
interview,"* *"The AI wrote this code — here are the 4 bugs a real engineer spots,"* *"Why DSA is how
you control the AI, not what AI replaces."* Each → email capture → cohort invite.

---

*Index v1, 2026-06-26. Next: convert any one week into a full lesson script via
`video-script-writer-trigunai`; publish the index as the course's public curriculum page.*
