---
name: user-research-education-trigunai
description: >
  Deep, CONTINUOUS user-research + execution engine for TrigunAI's education product (Acharya AI
  tutor for coaching teachers & their students). Turns the live outreach pipeline — Maya voice calls
  (Plivo) + the Acharya WhatsApp tutor + the LMS — into a daily research instrument that surfaces the
  REAL, practical pain points of Indian teachers and students, then converts those pains into (a)
  agentic-system solution hypotheses, (b) sharper Maya call scripts, and (c) marketing messaging.
  The thesis it exists to prove: most education problems are workflow problems that agentic systems can
  solve — so we must learn the actual workflows/pains from real users, every day. Use to run the daily
  user-research loop, mine call transcripts/recordings + WhatsApp doubts for pain points, build/maintain
  the user-research knowledge base, spot emerging patterns, design agentic solutions, and feed
  marketing + product. Triggers: "user research", "study my users", "what are teachers' pain points",
  "analyze the calls", "mine the transcripts", "what are students struggling with", "research report",
  "customer insight", "why aren't teachers interested", "objections", "discovery mode", "what should we
  build", "pain points", "understand my users", "daily research".
metadata: { "trigunai": { "emoji": "🔬", "kind": "research+execution" } }
---

# user-research-education-trigunai — Deep User Research → Agentic Execution

**Mission.** Understand India's coaching teachers and their students *better every single day* — their
real, practical workflows and pain points — and convert that understanding into agentic systems that
solve them, plus the marketing that sells them. This is not a survey deck; it's a living research loop
powered by the **real conversations TrigunAI is already having** through Maya and Acharya.

**Core thesis (what we're testing).** Most education pain is *workflow* pain (a teacher can't answer
40 doubts at 9pm; a student is stuck and no one's awake; admissions/follow-up eats the teacher's day).
Agentic systems + workflows can absorb that load. To build the right ones, we must learn the actual
workflow from the people living it — not guess. Every insight must trace to a real user's words.

---

## 1. The instruments (real data sources — this is our unfair advantage)

We are not doing cold surveys — we already talk to hundreds of real teachers/students. Mine that.

| Instrument | What it reveals | Where the data lives |
|---|---|---|
| **Maya voice calls** (Plivo, gpt-realtime) | Teachers' own words: objections, needs, how they run their coaching, what they wish existed | Transcripts `dk_trigun@20.219.2.53:~/voicebot_wa/transcripts/<call_uuid>.txt` · recordings via Plivo `/Recording/` · outcomes `~/leads/call_results.csv` |
| **Acharya WhatsApp tutor** | STUDENTS' real doubts + where they get stuck, when they study, what they can't understand | Gurukul VM (`20.219.2.53`) — Acharya message logs / Learner Profiles (see `project-gurukul-vm`) |
| **LMS LearningEvent data** | Web learners' wrong attempts, hints used, latency (quantified struggle) | LMS `LearningEvent` table (see `project-learning-loop`) |
| **Lead outcomes** | Which segments/cities/pitches convert — demand signal | `~/leads/call_results.csv` (status + interested) |

Connect from a Claude session: `ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53`. Maya/pipeline ops
live in the **content-marketing-bot** skill §6; Acharya/LMS in **maintain-trigunai-system**.

---

## 2. The daily research loop (run this each day)

1. **Pull the day's raw material**
   - New call transcripts: `ssh … 'ls -t ~/voicebot_wa/transcripts/*.txt | head -30'` + read them.
   - Interested + objection calls: recordings for the *answered-but-not-interested* ones are gold (that's where the real objections are — not just the yeses).
   - New Acharya student doubts from the WhatsApp logs.
2. **Extract** — for each conversation, pull structured items:
   `{ speaker: teacher|student, segment, city, pain, objection, need/feature_wish, quote (verbatim), emotion }`.
   Verbatim quotes only — never paraphrase into an insight that wasn't said.
3. **Tag** into the taxonomy (§3). New recurring theme → add a tag.
4. **Update the knowledge base** (`USER_RESEARCH_EDU.md`) — append evidence under each pain; bump counts.
5. **Surface** — today's new signals, this week's top 5 pains (by frequency × intensity), any *emerging*
   pattern, and any objection that recurred (that's a script fix or a positioning fix).
6. **Convert** (§4) — for each top pain, write/refresh: the agentic-solution hypothesis, the Maya-script
   tweak, and the marketing hook (a real quote → a line of copy).
7. **Report** — a tight daily note to Deepak (Telegram/CEO brief): "heard today, top pains, 1 thing to
   build, 1 script change, 1 marketing hook." Weekly: a synthesis.

---

## 3. Pain-point taxonomy (living — grow it, don't force-fit)

Seed categories (teacher side): **after-hours doubts** · **too many students / can't scale attention**
· **admissions & follow-up load** · **cost/ROI sensitivity** · **tech-shyness / setup fear** ·
**student engagement & retention** · **content/notes prep time** · **doubt quality & consistency** ·
**parent communication** · **competition from big chains/apps**.
Student side: **stuck at night, no one to ask** · **shy to ask in class** · **doubt not resolved fast**
· **weak-concept loops** · **language (Hindi vs English)** · **motivation/consistency**.
Each tag holds: count, top verbatim quotes (with source call/segment/city), intensity notes.

---

## 4. From insight → agentic solution → execution (the whole point)

For every validated top pain, produce a one-liner in three columns and route it:

| Column | Goes to |
|---|---|
| **Agentic solution hypothesis** (what workflow/agent could absorb this pain) | product roadmap · `project-tutor-rl` / `project-learning-loop` when it's a tutor/learning workflow |
| **Maya script tweak** (address the objection earlier / sharpen the hook) | update `INSTRUCTIONS` in `maya_rt_bridge.py` (content-marketing-bot §6.4) |
| **Marketing hook** (real quote → emotional line) | `content-marketing-emotion-connect` + `content-daily-engine` (the day's reel/post) |

Example: pain "students ask doubts at 9pm and I can't reply to all" →
solution *Acharya auto-answers after-hours under the teacher's brand*; Maya hook *"9 बजे रात को doubt
आए तो study रुकनी नहीं चाहिए"*; marketing hook = same, as a reel opener. (Real, because teachers said it.)

---

## 5. Maya "discovery mode" (research variant of the call)

The default Maya call is a screener (content-marketing-bot §6). For a research push, run a **discovery
variant**: after qualifying, Maya asks **1–2 open pain questions** ("आपकी सबसे बड़ी परेशानी क्या है जब
students के doubts बहुत ज़्यादा आते हैं?" / "अगर एक चीज़ automatic हो जाए तो क्या चाहेंगे?"), keeps it
short, and lets them talk. Implement by swapping `INSTRUCTIONS` to a discovery prompt for a batch, or
tagging a small "research batch" of leads. The transcripts from these are the richest pain data.
(Keep it honest: it's still a real call from TrigunAI; don't fake a persona.)

---

## 6. Outputs (where the knowledge accumulates)

| Artifact | Purpose |
|---|---|
| `USER_RESEARCH_EDU.md` (repo root) | The living knowledge base — pains, evidence, quotes, counts, by segment |
| Weekly synthesis note | Top pains, what moved, solution/roadmap implications |
| `research_batch/` transcripts | Raw discovery-call material |
| Marketing-hook bank | Real-quote-derived lines feeding the content engine |

Everything is **evidence-linked** — each claim points to a call/segment/quote. Numbers are counts of
real conversations, never invented.

---

## 7. Honesty guardrails (non-negotiable — this is research)

- **Every insight traces to a real user quote.** No fabricated pains, personas, or "users say…" without a source.
- **Objections are data, not failures.** The *no*s teach more than the *yes*es — mine them hardest.
- **Small N is small N.** Say "3 of 27 teachers mentioned X," not "teachers want X." Report confidence honestly.
- **Don't lead the witness.** Discovery questions stay open; don't script the answer we want.
- **Consent/compliance.** Calls are to published business numbers; research use of transcripts is internal.
  Follow the same DLT/DND rules as content-marketing-bot §6.8.

---

## 8. Related skills / context
- **content-marketing-bot** — owns Maya calling, the lead pipeline, transcripts/recordings, content engine (this skill *consumes* Maya's output and *feeds* the content engine).
- **maintain-trigunai-system** — Acharya/LMS (the student-side data source).
- **teacher-outreach-engine** — the teacher GTM sprint (this skill supplies the "why they buy / why they don't").
- **project-tutor-rl · project-learning-loop** — where student-struggle insights become better teaching agents.
- **trigunai-ceo** — strategy; this skill hands it evidence-based user truth for direction calls.

*This skill exists so TrigunAI never guesses about its users. Every day: listen to real teachers and
students, extract their real pains, and turn those pains into agentic systems that actually help — and
into marketing that speaks their exact words back to them.*
