# Acharya — Features (now) + Roadmap (next) + Landing copy

> Companion to `BRAND_POSITIONING.md`. What Acharya **actually does today** (honest — no inventing
> capability), what we **add next** (driven by real user feedback + industry), and the reframed
> landing copy for both sites. Locked 2026-07-16.
>
> Frame: **Acharya = your institute's AI Teaching Assistant.** The student tutor is **agent #1** of
> "Agentic AI for education." Each roadmap item is the next agent in the suite — and we build them
> in the order **real Patna teachers tell us they hurt** (that's Rohan's surveyor job).

---

## A. Who we assist (two buyers, one product)

| Buyer | What Acharya is to them |
|---|---|
| **Solo tuition teacher** | Their assistant — carries their teaching into the 22 hours between classes; their students get a 1:1 tutor; they get a pre-class brief + a WhatsApp broadcast channel, under their own name. |
| **Coaching institute** | Staff for the whole institute — the same, across many batches/teachers, plus owner-level visibility (who's slipping, which batch is at risk). Institute-tier depth is partly roadmap (§C). |

Neither replaces the teacher. Acharya does the **repeat, after-hours, always-on** work so the human teaches.

---

## B. What's LIVE today (what Rohan/Maya can honestly promise)

1. **1:1 Student AI Tutor — trained on how *you* teach.** Per-student tutor synced to the teacher's
   syllabus, notes and live classes. Teaches (asks a check-question, reads the answer, guides to the
   next step — not answer-dumping). On **WhatsApp + web**, **English or हिंदी**, under the teacher's brand.
2. **Per-student memory + spaced revision (the retention engine).** A Learner Model per student
   tracks concept mastery (`not_seen → shaky → solid`), misconceptions and streaks, and sends
   **spaced active-recall pings + curiosity hooks** on the forgetting-curve schedule (1d→3d→7d→16d).
   This is the "students actually revise" lever.
3. **WhatsApp channel under your brand.** Teacher broadcasts announcements / homework / reminders to
   the class; students ask doubts 24/7 and get an answer in the teacher's method. Official Meta Cloud
   API — no new app for students to install.
4. **Teacher pre-class brief + dashboard** *(live, deepening).* Before each class Acharya briefs the
   teacher: what to re-cover, who's shaky, who's slipping ("cover Lenz's law again — 6/10 shaky;
   Ravi & Priya slipping"). Plus performance visibility + student management.
5. **Interactive lessons / LMS.** Duolingo-style lessons on lms.trigunai.com (structured practice,
   not just chat).
6. **Bilingual (English / हिंदी).**
7. **Learning-loop data capture** *(built, being switched on).* Every wrong attempt / hint / latency
   is logged — the data that makes Acharya better the more it's used (the moat, not a sales feature).

> Honest caveat for the pitch: these are what we **offer**; whether real institutes adopt + get value
> is exactly what the Patna pilots test. Never claim scale ("thousands use it") — we're finding first partners.

---

## C. Roadmap — the next agents in the suite (feedback- + industry-driven)

**We do NOT build these speculatively.** Priority = whatever pain Rohan hears **3+ times** in the
field (see his surveyor log). Rough backlog, most-requested-in-coaching first:

| Next agent | Pain it kills | For |
|---|---|---|
| **Test / worksheet / mock-paper generator** | teachers burn nights making practice papers | solo + institute |
| **Homework & answer reviewer** | grading + individual feedback doesn't scale | solo + institute |
| **Parent-connect** (auto progress updates) | parents constantly ask "how's my child doing?" | solo + institute |
| **Institute owner analytics** (batch-level: at-risk, retention, attendance) | owner is blind across batches | institute |
| **Multi-teacher / batch admin console** | one Acharya, many teachers/batches, cleanly managed | institute |
| **Admin ops** (attendance, fees reminders, scheduling) | back-office eats teaching time | institute |
| **Voice doubt-solving** (Maya-style calls) | some students prefer a call to typing | both |
| **Diagnostic placement** | know each student's starting level | both |
| **More regional languages** | reach beyond Hindi/English | both |

Each shipped agent = a bigger "AI teaching team," a higher price point, and a stronger moat. The
order is set by the market, not by us guessing.

---

## D. Landing copy — the reframe (for approval before any live edit)

**Two surfaces:** `acharya.trigunai.com` (product) + `trigunai.com` (company hero). Change = swap the
descriptor to **AI Teaching Assistant**, add the **assists solo teacher AND institute** line, and add
the **"agentic AI for education"** vision altitude. `acharya.trigunai.com` already runs "extends you,
not replaces you" — keep that; it's right.

### acharya.trigunai.com — hero (proposed)
- **Pill:** `आचार्य · your AI Teaching Assistant`
- **H1:** *Acharya is your institute's* **AI Teaching Assistant.**
- **Sub:** *It carries your teaching into the 22 hours between classes — your students practise,
  revise and clear doubts with a 1:1 AI tutor on WhatsApp & web (English or हिंदी), and before every
  class Acharya briefs you on what to cover and who's slipping. For a single tuition teacher or a
  whole institute — under your brand.*
- **Badge:** *The AI teaching assistant that works while you sleep — never replaces you, always
  extends you.*
- **Section "extends you, not replaces you":** keep as-is (it's the spine).

### trigunai.com — company hero (proposed)
- **Eyebrow:** `Agentic AI for education`
- **H1:** *We build* **agentic AI for education** *— starting with Acharya.*
- **Sub:** *Acharya is an AI teaching assistant for coaching teachers and institutes: your students
  get a 1:1 tutor trained on how you teach, on WhatsApp, in your name — so you teach and Acharya
  handles the doubts, revision and busywork. The first of a team of AI agents for the classroom.*
- **CTA:** *Meet Acharya →* (to acharya.trigunai.com)

### Hero VIDEO (separate production task)
Current acharya hero uses a shader + a WhatsApp phone mockup. A true new hero *video* = a
`production-video-trigunai` render (script: teacher's day → doubts pile up at night → Acharya answers
in her style on WhatsApp → next morning the pre-class brief → "she teaches, Acharya assists"). Spec
it when the copy is locked; it's a render job, not a copy edit.

---

## E. Repo pointers (where these live)
- `acharya.trigunai.com` product landing = `lms/app/templates/acharya.html` (this repo) → deploy via
  the LMS pipeline (`maintain-trigunai-system` skill).
- `trigunai.com` company hero = the **ShaderStudio** repo (per `project-course-site-shaderstudio`),
  NOT this repo's stale `landing-page/`. Locate + confirm the exact file before editing.
- Any live edit is **draft-first → show diff → deploy on Deepak's OK** (both are production sites).

*Locked 2026-07-16. Feature truth grounded in `lms/app/templates/acharya.html` + `agentic_cohort/AI_GURUKUL_DESIGN.md` + the gurukul VM. Confirm changes in a `trigunai-ceo` / `maintain-trigunai-system` session.*
