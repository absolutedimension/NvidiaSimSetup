# Acharya — Brand & Landing Content Plan

> **Status:** ✅ SHIPPED 2026-07-06 — teacher landing live at acharya.trigunai.com (`lms:v51`),
> trigunai.com teacher-led two-section reframe live (`triguai-frontend:v98`). Real demo video +
> channel-preference "Book a demo" form wired to the existing `/api/course-request` lead pipeline
> (relaxed to accept phone-only). Half the teacher surface (dashboard, pre-class brief, MCQ flow,
> report card) is still TO-BUILD (§0.6) — page sells the vision + books demos; delivery must keep pace.
> Original plan written 2026-07-06.
> **Why:** the live `acharya.trigunai.com` still sells the *old* product (a self-paced AI
> course-tutor for individual learners). The locked direction (2026-07-05) makes the **teacher /
> institution the buyer**. This plan reframes the whole brand into two clean product lines and
> rebuilds the landings around the teacher-first motion (the 50-in-50 milestone).

---

## 0. Decisions locked (2026-07-06)

| Decision | Chosen |
|---|---|
| What `acharya.trigunai.com` becomes | **Teachers flagship** (B2B "AI Assistant for Teachers"). LMS login/dashboard stays behind it. |
| `trigunai.com` main-page order | **Teacher-led** — Teachers section first, Skill Development second. |
| Teacher product primary CTA | **Book a demo** (Maya/human follow-up). ₹4,999/mo shown as an anchor. |

---

## 0.5 Sync with Avinash's one-pager (2026-07-06)

Avinash's `Acharya_for_Teachers_OnePager.md` and this plan are **aligned** on the brand split,
separate pages/pricing, teacher-led ordering, and the co-teacher frame. His additions, merged below:

| Avinash's addition | Where it lands in this plan |
|---|---|
| **Pre-class brief = the real moat** (pushed on WhatsApp before every class: what to cover, what didn't land, who's slipping) | Promoted to a **headline differentiator** — hero (S1) + the star of the intelligence layer (S6) |
| **"Three outputs from one data stream"**: pre-class brief · classroom state · report card | Restructures **Offering 3 (S6)** into these three outputs |
| **Report card → forwarded to parents = fee justification + retention** | Added to S6 + Pricing (S9) as the teacher's *business* case |
| **MCQ-first; code (not the LLM) owns mastery & scheduling** | Trust line in **Why Acharya (S7)** + How-it-works |
| **RL flywheel** — dense same-syllabus cohorts feed the calibration engine (starving at 7 students/33 misconceptions) | Strengthens **The Vision (S10)** |
| **"Co-teacher"** one-liner ("Acharya co-teaches your class") | Adopted as an alternate hero frame (see S1) |
| **Built-vs-to-build honesty** (dashboard, brief, MCQ flow, report card, syllabus→concept-graph = TO BUILD) | New honesty guardrail (§0.6) — sell the vision, book demos, don't claim unbuilt surfaces as live |
| Open Qs: pricing model, WhatsApp template recategorization, naming | Folded into §8 (decisions) + §10.5 (system dependencies) |

## 0.6 Honesty guardrail (from Avinash's built-vs-to-build table)

The landing may **sell the vision and book demos**, but must not present to-build surfaces as
shipped (CEO honesty rule). Ground truth today:

- **Live now:** student AI tutor (syllabus-agnostic pedagogy), WhatsApp channel + WABA, learner
  profiles + mastery tracking, SRS daily pings, misconception capture + repair, privacy-safe event log.
- **To build:** syllabus → concept-graph ingestion (per board), **pre-class brief generator**,
  **teacher dashboard**, structured MCQ test flow, **report-card generator**, teacher onboarding
  (currently manual, ~1 day).

Implication: **demo-first is the correct CTA** (onboarding is hand-held and half the teacher surface
is still being built). Copy describes the *product experience* truthfully as "what your class gets";
where a surface is still in build, frame as "rolling out" rather than implying a finished dashboard.

---

## 1. The brand architecture (the split)

**Acharya = one brand: "AI for how India learns and teaches."** Two product lines under it:

| | **Acharya for Teachers** (flagship · "AI assistant for teachers") | **Acharya · Skill Development** |
|---|---|---|
| Buyer | Coaching teachers + small institutes (B2B) | Individual self-learners (B2C) |
| Scope | Any subject the teacher teaches (physics, maths, NEET/JEE…) | **AI & Deep Tech topics only** — no general skills |
| Promise | Extend the teacher: hold the student 24/7, save time & money, gain control | Learn AI & deep tech by *building*, 1:1 with Acharya |
| What they get | (1) Student AI tutor synced to the teacher (2) WhatsApp channel (3) Control dashboard | Build-real **AI & deep-tech** courses, self-paced, WhatsApp + web tutor |
| Price | **From ₹4,999/mo** — base covers up to 10 students; scales as students grow · **no deposit** · 14-day free trial then pay | ₹499/mo · 30-min-daily free tier · Founding-Learner challenge |
| Primary CTA | **Book a demo** (form → team follow-up on your channel) | **Start free on WhatsApp** (scan → pick a course) |
| Lives on | **acharya.trigunai.com** (flagship) + teased on trigunai.com | **trigunai.com** (Skill Development section/page) + LMS app |
| Priority | **NOW — 50-in-50 milestone** | Steady / secondary |

**Routing summary:**
- `trigunai.com` — brand home. Hero → two doors, **Teachers first**, Skill Development second.
- `acharya.trigunai.com` — the **Teachers** landing (this plan's centerpiece) + the logged-in LMS.
- The ₹499 student self-serve product's *marketing* lives under Skill Development on trigunai.com;
  the *app* (lessons, login, subscription) still runs inside the same `lms` FastAPI at
  acharya.trigunai.com/dashboard etc. (Only the public marketing framing moves — not the plumbing.)

---

## 2. The core message (teacher product)

**One-liner:** *Acharya is the AI assistant for teachers — it gives your students a 1:1 tutor
trained on how you teach, reachable on WhatsApp, with a dashboard that puts you in control.*

**The emotional hook (per content-marketing-emotion-connect):** not "replace teachers with AI" —
that scares them. The hook is **"AI that extends you."** Your students learn for 2 hours with you,
then they're alone for 22. Acharya is *you*, available in that gap — teaching *your* material, *your*
way, so they stay in your ecosystem instead of drifting to YouTube.

**The thesis line (keep it, it's the moat):** *Most problems in education are workflow problems —
and agentic AI can solve them. We start with three. We'll build whatever you need next.*

**Tone guardrails:** confident, practical, teacher-respecting. No fear-mongering ("AI will take
your students"), no hustle-bro, no inflated claims. Outcomes teachers care about: **retention,
results, time saved, money saved, control.**

---

## 3. THE TEACHER LANDING — `acharya.trigunai.com`
### Section-by-section content plan (replaces `lms/app/templates/acharya.html`)

> Each section: **Purpose → Draft copy → CTA → Replaces**. Copy is v1 draft, usable, to be tightened.

### S1 · HERO
- **Purpose:** in 5 seconds, a teacher knows this is *for them* and what it does.
- **Eyebrow:** `TrigunAI Innovations · Acharya for Teachers`
- **Headline (option A, student-tutor frame):** **Give every student a tutor trained on how *you* teach.**
- **Headline (option B, Avinash's co-teacher frame — recommended):** **Acharya co-teaches your class.**
- **Subhead:** Acharya is an AI co-teacher for teachers and institutes. Between classes, your
  students practise, revise and clear doubts with a 1:1 tutor synced to your syllabus — on WhatsApp
  and web. And before every class, Acharya sends *you* a brief: what to cover next, what didn't land,
  who's slipping. **Your teaching keeps going in the 22 hours you're not in the room.**
- **Differentiator badge (surface the moat up top):** *The only tutor that tells you how to run your
  next class based on what your students did since the last one.*
- **Primary CTA:** `Book a demo` (opens the short form). **Secondary:** `or scan on WhatsApp →`
  (the existing teacher-register QR: scan → type "teacher"). Both just capture minimal details +
  preferred contact channel; your team reaches out on that channel. **Third:** `See how it works ↓`
- **Trust strip (placeholder):** "Built by TrigunAI · Running with real coaching classes" +
  logos/'# students learning' once you have them.
- **Replaces:** old hero "Acharya — your AI guide to building with AI" + the Founding-Learner pill +
  the "Are you a teacher?" afterthought pill.

### S2 · THE PROBLEM (the gap)
- **Purpose:** name the pain in the teacher's own words so they feel understood.
- **Kicker:** `The problem`
- **Headline:** **Your students learn for 2 hours. Then they're on their own for 22.**
- **Body:** Between classes the doubts pile up. They forget last week's concept. They don't
  practice. They drift to random YouTube videos — or another coaching class. You can't be on call
  24/7, and hiring assistants to cover the gap costs more than it returns. The result: weaker
  retention, weaker results, and students who feel unsupported the moment class ends.
- **No CTA** (this section builds tension).
- **Replaces:** "Not another video course" (that framing was for self-learners).

### S3 · WHAT ACHARYA IS (the solution, 3 offerings in one glance)
- **Purpose:** the "aha" — one assistant, three concrete things, all branded to the teacher.
- **Kicker:** `The solution`
- **Headline:** **An AI assistant that extends you — not replaces you.**
- **Intro line:** Acharya carries your teaching into the other 22 hours. Three things, live today:
- **3-card row (each links to its deep section):**
  1. **🎓 A student tutor that teaches *your* way** — synced to your syllabus and your live sessions.
  2. **💬 A WhatsApp channel** — reach your students, and let them reach Acharya, where they already are.
  3. **📊 A control dashboard** — see performance, manage students, save time and money.
- **CTA:** `Book a demo`
- **Replaces:** the "10 courses · one guide" grid (that's Skill-Dev, moves to trigunai.com).

### S4 · OFFERING 1 — Student AI Tutor (synced to you)
- **Kicker:** `Offering 1 · Student AI Tutor`
- **Headline:** **A 1:1 tutor for every student — trained on how you teach.**
- **How it works (3 steps, visual):**
  1. You give Acharya your syllabus, notes, and teaching context.
  2. It stays in sync with your live classes — what you covered, what's next.
  3. Every student gets a personal tutor that teaches *exactly* your material, your method — not a
     generic chatbot.
- **The payoff line:** So when class ends, your teaching keeps going. Students revise, clear doubts,
  and practice — inside *your* ecosystem, under *your* brand. You hold the student.
- **CTA:** `Book a demo`

### S5 · OFFERING 2 — WhatsApp Channel
- **Kicker:** `Offering 2 · WhatsApp`
- **Headline:** **Meet your students where they already are.**
- **Body:** No new app to install. Acharya lives on WhatsApp under your brand. You broadcast
  announcements, assignments and reminders to your students. They ask doubts any time — day or
  night — and get an answer in your teaching style, in English or हिंदी. (Show the WhatsApp-scan
  card / QR — reuse the existing asset.)
- **CTA:** `Book a demo`
- **Repurposes:** the existing WhatsApp-scan section, re-pointed at teachers (their students scan,
  not self-learners).

### S6 · OFFERING 3 — The teacher intelligence layer (three outputs from one data stream)
> Restructured per Avinash: every student answer feeds one learner model → three outputs. Lead with
> the **pre-class brief** (the moat), then the dashboard (depth), then the report card (student + business).
- **Kicker:** `Offering 3 · Your co-teacher intelligence`
- **Headline:** **One data stream. Three things that make you a better teacher.**
- **Output 1 — Pre-class brief (pushed on WhatsApp, before every class) ★ the differentiator:**
  Not raw data — a prescription. *"Cover Lenz's law again — 6 of 10 are shaky. Ravi and Priya are
  falling behind. Next up per your plan: electromagnetic induction."* You walk in knowing the room.
  Pushed to you, never left sitting in a dashboard.
- **Output 2 — Classroom state (dashboard, when you want depth):** per-student strengths/weaknesses,
  mastery-over-time, a concept-by-concept heatmap across the whole class.
- **Output 3 — Report card (for the student, periodic):** their strengths, progress, and streak —
  motivation for them, and **your business tool: an evidence-based report card you forward to parents
  is proof of value that justifies your fees and keeps students enrolled.** No competing tutor has this.
- **3 mini-benefits:** `⏱ Save time` · `💸 Save money` · `🎯 Walk in knowing the room`
- **CTA:** `Book a demo`

### S7 · WHY ACHARYA (the difference / the moat)
- **Kicker:** `Why Acharya`
- **Headline:** **It's your AI — branded, synced, and agentic.**
- **4 points:**
  - **Yours, not generic** — carries your brand, your syllabus, your method.
  - **Synced to your teaching** — updates with your live classes, not a static course.
  - **Agentic, not just a chatbot** — it does the workflow (doubt-solving, practice, follow-up),
    not just answer questions.
  - **Trustworthy grading** — assessment is MCQ-first and **code, not the AI, owns mastery and
    scheduling** (deterministic, no hallucinated scores; handles physics numericals fine).
  - **We build what you need next** — most education problems are workflow problems. These three are
    the start; tell us your bottleneck and we'll build the system for it.
- **No hard CTA** (credibility section).
- **Replaces:** "Teaching that compounds" (repurpose the good lines here).

### S8 · HOW YOU GO LIVE (onboarding)
- **Kicker:** `Getting started`
- **Headline:** **Live with your students in days, not months.**
- **Two ways to start (show both):**
  - **Fill the form** — name, coaching, subject, # students, and the channel you prefer we reach you on.
  - **Or scan on WhatsApp** — scan the QR, type "teacher", drop the same minimal details.
  - Either way, **our team connects with you on your preferred channel** — no calendar juggling, no self-setup.
- **Then 3 steps:** 1) We understand your class → 2) We set up your branded Acharya with your syllabus
  → 3) Your students start on WhatsApp + web; your briefs and dashboard roll out.
- **Trial line:** Start with a **14-day trial** — see real engagement before you commit.
- **CTA:** `Book a demo`

### S9 · PRICING
- **Kicker:** `Pricing`
- **Headline:** **Start almost free. Pay only after you see it work.**
- **Card:** **₹4,999 / month** — base plan, covers **up to 10 students**. Includes the student tutor,
  WhatsApp channel, the teacher intelligence layer (rolling out), your branding, and setup.
  - **No deposit. Nothing upfront.** Start with a **14-day free trial** — you only pay ₹4,999 after
    the trial, once you've seen real engagement. *Almost free to start and implement.*
  - **Scales with you:** the price grows only as your student count grows — you're never paying for
    seats you don't use.
- **Note:** Bigger institute or custom needs? Book a demo — we'll scope your slab.
- **CTA:** `Book a demo`
- **Replaces:** ₹499/mo self-paced + Founding-Learner offer (those move to Skill Development).

### S10 · THE VISION (future)
- **Kicker:** `Where this goes`
- **Headline:** **Acharya becomes your AI department.**
- **Body:** Today: a co-teacher, a WhatsApp channel, a teacher intelligence layer. Tomorrow — as you
  need it — agentic systems for admissions, fee follow-ups, attendance, parent communication, content
  creation, and more. You're not buying a tool; you're getting an AI team that grows with your
  institute.
- **Gets smarter with your class (soft flywheel line):** the more your students learn with Acharya,
  the sharper its briefs and repair get. *(Internal strategic backbone — Avinash: dense same-syllabus
  cohorts are exactly the calibration data our research engine needs; the teacher channel feeds the
  core RL loop, not just a side product. Keep this framing internal-facing / soft on the public page.)*
- **CTA:** `Book a demo`

### S11 · FINAL CTA + audience router
- **Headline:** **Give your students a teacher who never sleeps.**
- **Primary CTA:** `Book a demo`
- **Router lines (small, at the very bottom):**
  - *Are you a student?* Your teacher gives you access — ask them about Acharya.
  - *Want to build AI skills yourself?* → **Acharya Skill Development** (link to trigunai.com skill-dev).
- **Replaces:** "Meet your guide" final section (self-learner framing).

### Nav & footer (teacher landing)
- **Top nav:** `Acharya` (home) · `For Teachers` · `Skill Development ↗` (→ trigunai.com) ·
  **`Book a demo`** (button). Drop the "Start free" primary from this page.
- **Footer:** Sign in (teachers/existing) · trigunai.com · privacy · contact/WhatsApp.

---

## 4. THE MAIN LANDING — `trigunai.com` (teacher-led, two sections)
### Changes to `ShaderStudio/landing/index.html`

- **S1 · Hero (brand):** **Acharya — AI for how India learns and teaches.** One sub-line, then two
  clear doors: **`For Teachers & Institutes`** (primary) and **`For Learners (Skill Development)`**.
- **S2 · For Teachers & Institutes (FIRST):** 3-offering summary (tutor / WhatsApp / dashboard) +
  the "extend you, not replace you" line + **`Explore Acharya for Teachers →`** (→
  acharya.trigunai.com) and **`Book a demo`**.
- **S3 · Acharya Skill Development (SECOND):** **AI & Deep Tech courses only** — self-paced, ₹499/mo,
  **30-min-daily free tier**, 1:1 Acharya tutor, build-real projects. **The workflow already works
  on WhatsApp:** student scans the QR → picks from the listed courses → starts learning in chat.
  **`Start free on WhatsApp →`** (scan card) + `See the courses →`. This is where the *current*
  acharya.html student content is relocated. Keep it clearly scoped to AI/deep-tech so it never
  reads as "general skills."
- Keep the episodes/series lower on the page as brand proof.

---

## 5. What happens to the OLD student content (don't delete — relocate)

The current `acharya.html` sections that are self-learner-focused get **moved into the Skill
Development surface** (trigunai.com section, or a dedicated skill-dev page), not thrown away:

| Old section | New home |
|---|---|
| "Not another video course" | Skill Development section (its natural pitch) |
| Founding Learners (7-day → free year) | Skill Development (the B2C acquisition hook) |
| 10 courses grid | Skill Development |
| Self-paced vs cohort | Skill Development |
| "Meet your guide" | Skill Development |
| WhatsApp-scan card | **Both** — reframed per audience (students-of-a-teacher vs self-learners) |

The ₹499 subscription, the LMS lessons, login, dashboard — **unchanged in code**; only the marketing
wrapper is re-pointed.

---

## 6. Conversion mechanics — the two teacher join paths (DECIDED)

A teacher can register interest **two ways**, both ending in *your team reaching out on the
teacher's preferred channel*:

- **Path A — Web "Book a demo" form (on the landing).** A short form: name, coaching/institute name,
  subject, # students, **and the primary channel they can be reached on** (WhatsApp / call / email) +
  that contact detail. Submitting drops a lead into the teacher_gtm pipeline → your team connects on
  the channel they chose. This directly feeds 50-in-50.
- **Path B — WhatsApp scan (already live).** Teacher scans the WhatsApp QR → types "teacher" → a
  minimal in-chat form (same minimal details + preferred channel) → same lead pipeline, same
  team follow-up.

**Key principle:** we don't force a calendar or self-serve setup on the teacher — we capture the
*minimum* + their **preferred contact channel**, and the team reaches them there. The landing shows
both paths (form button + "or scan on WhatsApp" card).

- Optional secondary **`Start 14-day trial`** where it fits (S8), routing to the
  `acharya-technology-transfer` onboarding — but demo/lead-capture is primary.

---

## 7. SEO / messaging hygiene

- **Teacher landing** keywords: "AI assistant for coaching teachers", "AI tutor for my students",
  "WhatsApp tutor for coaching institute", "student retention AI". Title/meta/`llms.txt` rewritten
  from the current self-learner copy.
- **Skill-Dev** keeps the "learn AI by building" keywords — kept on trigunai.com so the two don't
  cannibalize each other's search intent.
- Don't let the two value props bleed into one page — that mix is exactly today's confusion.

---

## 8. What I need from you before building

1. ~~**Demo capture**~~ **DECIDED (2026-07-06):** two paths — web form + existing WhatsApp-scan —
   both capture minimal details **+ preferred contact channel**; team follows up on that channel.
   No calendar, no forced self-serve. (See §6.)
2. **Skill-Dev home:** a dedicated `trigunai.com/skill-development` page, or just a strong **section**
   on trigunai.com for now? (Recommend section first, page later.)
3. **Proof assets:** any real numbers/logos/testimonials I can put in the trust strip (S1) and
   pricing? If none yet, I'll use honest placeholders ("running with real coaching classes").
4. **Trial vs demo weight:** keep the 14-day trial visible on the teacher landing, or demo-only
   until you've onboarded a few manually? (Recommend keep trial in S8, demo as the button.)
5. ~~**Pricing model**~~ **DECIDED (2026-07-06):** base **₹4,999/mo covers up to 10 students**, price
   **scales as student count grows** (slabs). **No deposit / nothing upfront**; 14-day free trial then
   pay. Positioned as "almost free to start & implement." (See S9.)
6. ~~**Naming**~~ **DECIDED (2026-07-06):** the product name is **"Acharya for Teachers"** (simple &
   clear). "AI assistant for teachers" is used only as a descriptor/tagline, not the name.

## 10.5 System dependencies (not landing copy — but they gate classroom scale)

From Avinash's one-pager; these don't block writing the page but block *running* it at scale:

- **WhatsApp template recategorization (Marketing → Utility, ~6× cost difference)** before any
  classroom-scale daily pings — otherwise unit economics break at volume. Owner: maintain-trigunai-system / WABA.
- **To-build product surfaces** (§0.6): pre-class brief generator, teacher dashboard, MCQ test flow,
  report-card generator, syllabus→concept-graph ingestion. The landing can book demos against these;
  delivery must keep pace with what the page promises (don't oversell the dashboard before it exists).

---

## 9. Suggested build order (once approved)

1. Rewrite **`acharya.trigunai.com`** teacher landing (S1–S11) — the priority, matches 50-in-50.
2. Wire **`Book a demo`** capture (§6) → teacher_gtm lead + Maya.
3. Update **`trigunai.com`** hero + two sections (teacher-led) and relocate the old student content
   into Skill Development.
4. SEO/meta/`llms.txt` pass on both.
5. Verify on mobile, deploy (per `maintain-trigunai-system`: lms app for acharya, ShaderStudio for
   trigunai.com).

*Owner: Deepak. Companion skills: maintain-trigunai-system (owns the live stack + deploy),
content-marketing-emotion-connect (owns the feeling), acharya-technology-transfer (onboarding),
teacher-outreach-engine (fills the demo pipeline).*
