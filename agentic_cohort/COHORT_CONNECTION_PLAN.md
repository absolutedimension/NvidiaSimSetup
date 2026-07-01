# Cohort Connection Plan — how Acharya reaches students

> Two needs: (1) a **common/cohort channel** for broadcast + shared learning, and (2) a **personal
> 1:1 tutor** per student with tight, saved context. Built on the robust WhatsApp Cloud API + OpenClaw
> Acharya (gpt-5.5) on VM 20.219.2.53.

## The hard constraint (decides the design)
**WhatsApp Cloud API = 1:1 only. It cannot be in a WhatsApp group.** Groups need the unofficial Web
path (logs out). So the AI cannot live *inside* a WhatsApp group robustly. Channel 2 is designed around this.

---

## CHANNEL 1 — Personal Tutor (1:1) ✅ BUILT, robust
WhatsApp Cloud API → bridge → Acharya, one thread per student. This is the core (Bloom 2-sigma).

### Technique: tight context + saved info (the personalization engine)
Two layers per student, keyed by their WhatsApp number (`wa_id`):
1. **Conversation continuity** — OpenClaw already keeps a per-student *session* (the bridge passes
   `--to +<wa_id>`, deriving a stable session key). The full back-and-forth persists in that session,
   so Acharya naturally remembers the running thread.
2. **Structured Learner Profile** — a persistent JSON per student: `~/.openclaw/students/<wa_id>.json`
   ```json
   { "name":"", "byoa_goal":"", "level":"", "current_module":2,
     "concepts": {"agent_loop":"solid","tool_boundary":"shaky"},
     "misconceptions":["model runs the tool itself"],
     "srs": [{"concept":"agent_loop","due":"2026-06-29","interval_days":3}],
     "streak":4, "last_win":"first tool call fired", "notes":[] }
   ```
   **Flow per message (bridge):**
   - load `<wa_id>.json` → inject as a `STUDENT PROFILE:` preamble into the agent message
   - Acharya teaches with that context (gurukul-tutor skill)
   - a lightweight background call extracts "what changed" (mastery↑, new fact, misconception) → merge → save
   This is what "holds his context tight + saves his important information" — durable across days/restarts.

---

## CHANNEL 2 — Common / Cohort (pick one; AI-in-WhatsApp-group is NOT possible)

| Option | The AI experience | Robust? | Students need |
|---|---|---|---|
| **A. WhatsApp 1:1 broadcast fan-out** (Recommended) | Acharya sends the same lesson/announcement/daily-question to *every* student individually; each reply is personal. No shared thread, but everyone gets common content + a *personalized* answer (better than group spam). | ✅ Cloud API | nothing new |
| **B. Human-run WhatsApp group + AI 1:1** | A normal WhatsApp group for peer/community (Deepak posts, students chat). AI is NOT in it; it tutors 1:1. Best of both: social space + private tutor. | ✅ (group is human-run) | nothing new |
| **C. Telegram cohort group with Acharya in it** | A real group where Acharya replies in-thread on @mention/context — the "AI TA in the room" you pictured. | ✅ Telegram bots work in groups | join Telegram |

**Recommended: A + B together** — a human-run WhatsApp community group (peer energy) + Acharya's 1:1
broadcast fan-out for common content + personal tutoring. Pure WhatsApp, robust, no new app.
Choose **C** only if you specifically want the AI replying inside a shared group thread.

### Broadcast technique (Option A)
- Maintain a cohort roster (list of student `wa_id`s) — a simple `~/.openclaw/students/roster.json`.
- `openclaw message broadcast` (or loop `message send`) fans a message to all.
- **WhatsApp rule:** a business-initiated message outside a student's 24h window needs an approved
  *template*. So: register a few **utility templates** (daily_lesson, recall_ping, announcement) with a
  `{{1}}` variable that carries any content. Once a student replies, you're in their free 24h window.

---

## IMPLEMENTATION PHASES — STATUS
1. ✅ **Learner Profile store** — bridge loads `students/<wa_id>.json`, injects it into every turn,
   background-extracts updates (gpt-4o-mini), and GRADES recall replies (pending_recall). Verified.
2. ✅ **Roster + broadcast** — `~/.openclaw/gurukul/broadcast.mjs` (free-form to active students works;
   `--template gurukul_announce` for out-of-window). Roster = the student profiles on disk.
3. ✅ **Daily SRS cron** — `~/.openclaw/gurukul/srs_cron.mjs` + systemd timer `wa-srs.timer`
   (daily 03:30 UTC / 9:00 IST). Engine verified firing; needs the `gurukul_recall` template approved to deliver.
   Concept bank: `~/.openclaw/gurukul/concepts.json`.
4. ⏸ **(Option C Telegram)** — not chosen.
5. ⏳ **Community group (Option B)** — Deepak creates a normal WhatsApp group (human task).

### ⚠️ ONE remaining user action to make proactive pings deliver
Create + approve 2 utility templates in Meta — see `gurukul_pipeline/TEMPLATES.md`:
`gurukul_recall` (daily SRS, body `{{1}}`) + `gurukul_announce` (broadcasts, body `{{1}}`).
Free-form replies/broadcasts to ACTIVE students (within 24h) already work without templates.

## Onboarding flow (both channels)
On enrolment: student messages Acharya's number "JOIN" (opens 24h window + consent) → Acharya greets,
captures `byoa_goal` + `level` → profile created → added to roster + (B) invited to the community group.

*Owner: Deepak. Companion to AI_GURUKUL_DESIGN.md + WHATSAPP_GURUKUL_SETUP.md.*
