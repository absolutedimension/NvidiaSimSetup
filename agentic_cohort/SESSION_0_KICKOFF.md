# Session 0 — Kickoff (run on Google Meet, ~40 min, recorded)

**Goal of this session:** every student leaves with (a) an API key that works, (b) the starter repo
running on their machine, and (c) their use-case written down. Nothing else matters today.

Keep slides minimal — this is a working session, not a lecture. Screen-share your terminal more than slides.

---

## Slide / beat-by-beat

### 1. Welcome + the promise (3 min)
- "In 3 months, you walk out with a real agent doing a real job *you* actually do — running on a schedule, without you."
- Not a chatbot toy. A deployed Ops Agent + the patterns to build the next one.
- Introduce yourself in one line: you run multi-agent systems in production at TrigunAI.

### 2. How this cohort works (5 min)
- **Flipped:** before each weekly session you watch that module's video (≈30–60 min). The live 90 min is for *building and debugging your code*, not re-watching.
- **Same scaffold, your use-case:** everyone forks one repo; each automates their own workflow.
- **Every week starts with wins & blockers** — come having tried, bring where you're stuck.
- The rhythm: 1× / week, 90 min, [DAY + TIME], for 13 weeks. Recordings posted after each.

### 3. The map (3 min) — show the 13-week schedule
- Weeks 1–9 = the 9 modules. Week 6 & 11 = catch-up. Week 12 = **Demo Day**, you show what you built.
- One line per module (don't read them all — point at the arc: anatomy → tools → memory → planning → reliability → multi-agent → deploy → ship).

### 4. LIVE: everyone gets unblocked on setup (20 min) ← the real work
Screen-share and do it with them, slowly:
1. Fork + clone the starter repo.
2. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. **Get an API key.** Walk through creating an Anthropic (or OpenAI) key. Have a backup plan for anyone whose card fails — TrigunAI-provided key for the cohort (the moat).
4. `cp .env.example .env`, paste key.
5. `python run.py "hello"` → **everyone should see the loop tick once.** Celebrate this — it's their agent working.
- Don't move on until all 3 are green. This is the whole point of Session 0.

### 5. Name your use-case (5 min)
- Round-robin: each student says, out loud, the one repetitive workflow they want their agent to do.
- Write each into the shared progress sheet live. Push gently for *real and small* (one inbox, one sheet) over *big and vague*.

### 6. Logistics (4 min)
- Discord: `#announcements` `#help` `#show-your-work` `#resources`. Post blockers in `#help`.
- Office hours: you reply in `#help` daily by [TIME]; optional mid-week open call [DAY/TIME].
- This week's pre-work: watch **Module 1 — What an agent actually is**. Link in `#announcements`.
- Recording of today goes up tonight.

---

## Pre-session checklist (you, before Session 0)
- [ ] Starter repo pushed to GitHub as a **template** (settings → Template repository ✓)
- [ ] Progress sheet created, 3 student rows
- [ ] Discord server up with the 4 channels + students invited
- [ ] TrigunAI fallback API key ready (in case a student can't make one)
- [ ] Meet link + auto-record on, in the calendar invite
