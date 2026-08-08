---
name: rohan-field-caller
description: Rohan's field-sales + calling cockpit for the TrigunAI Patna push. From his OWN Claude, Rohan (a) controls the Maya AI calling system on the Gurukul VM — pick Patna institutes, tweak the pitch/script for a specific institute, dial them with Maya, listen to recordings; (b) runs the in-person field motion — pick who to visit, prep the visit, demo Acharya, onboard to a free pilot; (c) logs every call AND every visit same-day to the shared VM log Deepak monitors. USE WHEN Rohan says "start my day", "who do I visit/call today", "call this institute with Maya", "change the script for X", "log my visit", "prep me for this office", "onboard this teacher". Deepak monitors all activity and corrects via the same shared logs. All knowledge (training, questions, pitch, strategy, sourcing, shortlist) is bundled in this skill's `references/` folder.
---

# Rohan — Field Caller cockpit (Patna)

> **Your job in one line:** work the Patna coaching institutes **one by one** — Maya warms them
> with a call, you **visit the office** if you can (else call to onboard), you get them onto a free
> Acharya pilot, and you **log everything the same day**. Deepak watches the logs and course-corrects.
>
> **The motion:** shortlist → Maya pre-call → **visit (preferred) or call** → discovery → demo →
> free pilot → follow-up. You control Maya from here; you don't touch anything that serves live
> students. Full strategy: `references/PATNA_FIELD_STRATEGY.md`.

---

## 0. Connect (health check — run once at the start of the day)

Everything runs on the Gurukul VM over SSH with Rohan's key. First, confirm the link is live:

```bash
ssh -i ~/.ssh/rohan_gurukul_key dk_trigun@20.219.2.53 'python3 ~/caller_console.py review --limit 5'
```

If it prints recent calls → you're connected. If it errors → message Deepak; **do not try to fix
the server yourself.** (The VM runs live student tutoring — never restart or edit services.)

---

## 1. Pick who to work today (the Patna shortlist)

The master list is `references/patna_institutes.csv` (bundled in this skill; Deepak keeps the
kit and is refreshed when Deepak updates it). Columns: `name, cluster, subject, owner, phone,
size_est, priority, maya_precall, visit_status, pilot_status, pain_notes`.

- **Cluster first.** Pick ONE area for the day (Musallahpur/Bhikhna Pahari, Boring Road,
  Kankarbagh, Rajendra Nagar, Patliputra) so you walk between 3–4 offices in one trip.
- Where to find MORE institutes to add: `references/PATNA_SOURCING_GUIDE.md` — Google Maps by
  locality, Justdial/Sulekha Patna coaching categories, plus the physical coaching bazaars.
- Ask your Claude: **"Who should I work in Kankarbagh today?"** → it reads the CSV, filters the
  cluster, ranks by priority, and hands you a visit route + the Maya pre-call list.

---

## 2. Control Maya (the AI caller) — from your Claude

Maya is our AI voice agent. You drive her through `caller_console.py` on the VM. All commands are
`ssh -i ~/.ssh/rohan_gurukul_key dk_trigun@20.219.2.53 'python3 ~/caller_console.py <cmd>'`.
Just tell your Claude what you want in plain words — it runs the right command.

| You say | What runs | What you get |
|---|---|---|
| "Who's uncalled in Patna?" | `leads --city Patna --limit 40` | pickable list of Patna institutes not yet called |
| "Maya, call these: 917992250244, 917979919133" | `call 917992250244,917979919133` | Maya dials exactly those (11am–5pm IST, max 30/batch) |
| "Run a batch of 15 Patna NEET" | `batch --city Patna --segment NEET --limit 15` | previews the list → you approve → Maya dials |
| "Let me hear today's calls" | `review --limit 25` | recent calls + status + who was interested |
| "Full context on 917992250244" | `context 917992250244` | lead details + recording link + transcript |

**Always preview before dialing** (`--dry-run` on `call`/`batch`) so you see exactly who Maya will
ring. Maya's job here is to **warm the institute and confirm they'll take a visit** — not to close.

### 2b. Tweak the pitch/script for a SPECIFIC institute (before Maya calls)

You know Patna better than the script does. Before Maya calls a particular institute, you can shape
what she leads with:

- **Per-institute angle (today):** tell your Claude, e.g. *"For MCM (IIT-JEE+NEET), have Maya open
  about after-class doubt-solving for their NEET batch, and mention we'll come to their Boring Road
  office to set it up."* Your Claude writes that into the call's context note so Maya uses it.
- **Global script edit:** the master call script lives on the VM at
  `~/teacher_gtm/02_CONVERSATION_SCRIPT.md`. To change the default pitch for everyone, ask your
  Claude to *"show me the Maya script"* then *"update the opener to …"* — it edits the file on the
  VM. **Tell Deepak when you change the global script** (he monitors it).

> ⚙️ **Note for the first setup:** the per-institute context override is wired through the call's
> lead row. If Maya isn't picking up your per-institute note yet, it means the one-line VM patch
> isn't in — flag Deepak (`ROHAN-SCRIPT` in the log) and use the global-script edit meanwhile.

---

## 3. The field visit (your main move — this is why owners buy)

Institute owners want a person in the room. That's your edge over a phone call.

**Before the visit** — ask your Claude *"prep me for <institute>"*. It pulls the CSV row + any Maya
call transcript so you walk in knowing their subject, size, and what they said on the call.

**In the room — lead with THEIR pain, not our product:**
1. **Discovery first.** "What eats most of your time after class?" Listen for: students not
   revising, doubts piling up at night, no personalised practice, making test papers, parent
   updates. *Let them name the fire.* (Full question set: `references/FIELD_RESEARCH_GUIDE.md`.)
1b. **Mirror their pain back with the match card** (`references/ACHARYA_PAINPOINT_MATCH.md`): show
   the "problems we solve today" list and ask *"inme se kaunse aapke saath hote हैं?"* — let them
   recognise their own pain — then *"aur koi jo is list mein nahi?"* (that answer is research gold).
2. **Show, don't tell — HAND THEM THE PHONE.** Don't pitch; let them *do* it. Open the ready demo
   tenant for their subject, hand them your phone, and have THEM type a real doubt → Acharya answers
   live in Hindi. Then the wow: *"ab galat jawab dijiye, confidently"* → Acharya catches it. Full
   3-minute flow (recall pain → they ask → confidently-wrong catch → teacher brief → leave it running)
   + Hindi lines + fallbacks: **`references/DEMO_PLAYBOOK.md`.** (60-sec video = fallback only, for no signal.)
3. **Map Acharya to their pain.** "Your students can ask doubts on WhatsApp at 10pm and get an
   answer in your teaching style — under your institute's name."
4. **Offer the free pilot.** Not "buy this" — "let's put it live for one of your batches free, and
   you see if your students actually use it." Low friction = yes.
5. **If they need more trust:** book a second visit or a call with Deepak. That's fine — note it.

**Carry (the field kit):** the 60-sec Acharya demo (on phone) · the Hindi one-page leave-behind
(what Acharya does + offer + QR) · WhatsApp follow-up template. If any is missing, ask Deepak before
you go — a visit with no leave-behind is half-wasted.

**Honesty rules (never break — grounds for trouble per your appointment letter):**
- Never promise marks/results — say "more practice, visible progress."
- Never say "thousands of teachers use it" — we're newly launched, looking for first partners.
- Never collect cash. Payments go **only** to the official TrigunAI link. Ever.

---

## 4. Onboard an interested teacher (free pilot)

When a teacher says yes:
- Capture: institute name, owner name, phone, **subject to go live on**, batch size, WhatsApp opt-in.
- Tell your Claude *"onboard <institute> — pilot on <subject>"*. It records the request; **Deepak
  provisions the branded Acharya tenant** (that part is Deepak's — you hand off the details).
- Get the owner to share the student WhatsApp opt-in / the join link to their batch so it goes live.
- Set the follow-up: when will you check that students are actually using it? (That's what turns a
  pilot into a paid account.)

---

## 5. Log EVERYTHING the same day (this is how you get paid + how Deepak helps you)

Your visit pay and conversion bonus are **paid only against verified logs.** No log = invisible =
unpaid. Two logs, both on the VM (Deepak reads them):

**A call outcome:**
```bash
ssh -i ~/.ssh/rohan_gurukul_key dk_trigun@20.219.2.53 \
 'python3 ~/caller_console.py log --by rohan --channel phone \
   --teacher "MCM IIT-JEE & NEET" --phone 917992250244 \
   --outcome "visit booked" --pain "after-class doubts pile up" --next "visit Thu 3pm"'
```

**A field visit** — tell your Claude *"log my visit to <institute>: <what happened>"* and it writes
the row (institute, cluster, date, outcome, pain, pilot status, next step, proof note). Same-day,
always. Attach a proof point (photo of the office / owner's card) when you can — it verifies the
visit for your ₹200.

Ask your Claude *"show my week"* anytime to see your own visits/calls/pilots so far.

---

## 6. Your daily loop (just say "start my day")

1. Health check (§0) → **"who do I work in <cluster> today?"** (§1)
2. Maya pre-calls the day's list; tweak the angle per institute if useful (§2)
3. Go visit the warm ones (§3) → demo → free pilot (§4)
4. For institutes too far/unavailable to visit → call to onboard instead
5. **Log every call + visit same-day** (§5)
6. End of day: *"show my week"* + one line to Deepak on anything blocking you.

**Minimum viable day = 3 real touches (visit or call) + 3 logs.** Quality of the conversation and
the pain you capture matters more than the count.

---

## 6b. You are also our SURVEYOR (every visit is market research — even the No's)

Deepak's real goal isn't just to install Acharya — it's to **understand how the coaching industry
actually runs and where its real pain is.** Acharya is a hypothesis; the field tells us the truth.
So **every institute teaches us something, especially the ones that say no.**

On every visit — sale or not — capture:
- **How they run today:** how many students/batches, what subjects/exams, how they handle doubts
  after class, how they make test papers, how they update parents, what tools they already pay for
  (Classplus? just WhatsApp? nothing?).
- **Their #1 time-sink / frustration** in their own words (verbatim > paraphrase).
- **If they said NO — why exactly?** ("too costly", "students won't use WhatsApp for study",
  "don't trust AI", "already have an app", "no time to set up", "parents won't like it"). The *why*
  is worth more than the sale — it tells us what to fix or build.
- **What they WISH existed** — if they could hire one assistant for one job, what would it be?

**Use the full question set:** `references/FIELD_RESEARCH_GUIDE.md` is your research script — the exact
questions to ask (their world → their day → the pain + its cost → what they already pay for → the
job they'd outsource → AI objections), each with what to listen for, plus the capture template. Ask
about their **past** ("kal kitne doubts aaye?"), never hypotheticals; **don't pitch while you dig**;
chase every pain with "kitna time/paisa isme jaata hai?". Before a visit, ask your Claude *"prep the
research questions for this visit"*.

Log it: tell your Claude *"survey note for <institute>: <what you learned>"* → it fills the capture
template and appends to the **market-intelligence log** (`teacher_gtm/08_PAIN_POINT_LOG.md`, tagged
`by=rohan`). Deepak reads these weekly to decide which agent Acharya builds next — a pain heard **3+
times with a number attached** becomes a feature (see `references/ACHARYA_FEATURES.md` §C). A "no" logged with
its reason is a **win**, not a failure.

## 7. What NOT to do
- Don't touch VM services (Acharya/Maya/WhatsApp bridge run live students on the same box).
- Don't cold-WhatsApp a teacher before they say "yes, send it" on a call/visit — protects our number.
- Don't make pricing/feature/timeline promises beyond the official offer without Deepak's OK.
- Don't share the leads/data or your key with anyone.

*Built 2026-07-16 for Rohan Kr. Saurabh (Field Sales & Onboarding, Patna). Owner: Deepak.
All docs bundled in `references/` — this skill is self-contained.
The transfer/minting of Rohan's key + kit is produced by the `transfer-caller-role` skill.*
