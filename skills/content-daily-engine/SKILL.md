---
name: content-daily-engine
description: >
  The DAILY execution engine for TrigunAI's marketing content. Run this every day to deliver
  the day's posts on schedule. It resolves what's due today from the 30-day calendar
  (marketing_pipeline/03_CONTENT_CALENDAR_30DAY.md), produces the actual asset(s) through the
  emotion OS (content-marketing-emotion-connect), gates them on the pre-publish checklist, hands
  off to the render skill (production-video-trigunai / faceless-explainer) and the distribution
  skill (trigunai-marketing), and logs what shipped in marketing_pipeline/CONTENT_LOG.md. It is
  the operating arm that turns the calendar into daily delivery. USE WHEN Deepak wants to run,
  ship, or produce the day's content. Triggers on: "today's content", "what do I post today",
  "run the daily content", "deliver today", "daily post", "ship today's content", "content
  engine", "make today's posts", "daily marketing run", "what's due today", "run the calendar",
  "do today's marketing", "let's post", "/content-today", "daily delivery", "this week's content",
  "batch this week". Companion to the calendar (the plan), the emotion OS (the feeling), and the
  marketing skill (the pipes). This skill OWNS daily execution + the shipped log.
---

# Content Daily Engine — the operating arm

> **Job:** every day, turn the plan into a shipped post. Read the calendar → know today's slot →
> produce it in the right emotion → check it → render → distribute → log it. Repeat tomorrow.
>
> **The chain:** `content-daily-engine` (what + when, today) → `content-marketing-emotion-connect`
> (the feeling) → `production-video-trigunai` / `faceless-explainer-trigunai` (render) →
> `trigunai-marketing` (distribute). This skill drives the loop; the others are called by it.
>
> Plan: `marketing_pipeline/03_CONTENT_CALENDAR_30DAY.md` · Strategy: `02_CONTENT_STRATEGY.md` ·
> Log: `marketing_pipeline/CONTENT_LOG.md` (this skill writes it). Owner: Deepak.

---

## 0. THE GOLDEN RULE

> **Ship something every day, but never skip the engine.** The weekly engine is the **Saturday
> free live intro class** + the **Friday invite**. If a day collapses, protect those two and the
> **Tuesday Wonder Short**; everything else is upside. (CEO discipline: protect the gate, not the to-do list.)

The only scoreboard that matters: **intro-class registrations → 1:1 calls → cleared payments.**
Optimize daily output for those, not likes.

---

## 1. THE DAILY RUN (do these 7 steps, in order, every time)

When invoked (or each morning), run this loop:

1. **Resolve today's slot.** Run the helper:
   ```bash
   python3 ~/.claude/skills/content-daily-engine/scripts/today.py
   ```
   It prints today's date, weekday, and the calendar row (pillar · stage · topic · hook · CTA).
   Pass a date to plan ahead: `today.py 2026-06-24`. If today is outside the calendar window,
   it falls back to the weekday rhythm (§3) — roll the plan forward (§7).

2. **Load the emotion.** Open `content-marketing-emotion-connect`. Confirm for this slot:
   **pillar · arc-stage · the feeling (wonder + agency both present?) · the hook · the 5 beats.**
   *Never produce before the feeling is defined.*

3. **Produce the asset** in the right format (use the §4 per-format recipe):
   - LinkedIn post → write it (line-1 hook, short lines, one story, one CTA).
   - Short → write the script (hook, 5 beats, captions) → hand to the render skill (§5).
   - Email → subject = hook, one idea, one CTA.

4. **Gate it — run the pre-publish checklist** (§6). If any box fails, fix before shipping.
   This is the quality wall. A piece that fails the emotion test fails the metrics test.

5. **Render** (Shorts only): call `production-video-trigunai` (or `faceless-explainer-trigunai`).
   Produce **EN + HI**. LinkedIn/email need no render.

6. **Distribute / schedule:** call `trigunai-marketing` (`publish.py`) for email + multi-channel
   fan-out; schedule LinkedIn/YouTube natively. **Keep the 1:1 close human** — never auto-DM.

7. **Log it.** Append a line to `marketing_pipeline/CONTENT_LOG.md` (§8). The log is how the engine
   (and the CEO skill) knows what actually shipped vs. what the plan claims.

---

## 2. SPECIAL DAYS (the rhythm has 3 non-standard days each week)

| Day | Beyond the normal post, also… |
|---|---|
| **Friday** | Write + send **the week's email** (Sat-class invite) via `trigunai-marketing`. Post the LinkedIn invite. This fills Saturday's room — highest-leverage post of the week. |
| **Saturday** | **Run the free live intro class** (the conversion engine — the one "live" task). Prep: confirm registrants, the build demo, the GPU, the 1:1 booking link. Post a Wonder Short same day. After: book 1:1s from the room. |
| **Sunday** | **Batch next week** (§9): cut next week's 3 Shorts from existing episodes (EN+HI); skim the calendar for next week's hooks. ~1.5 hr that makes the rest of the week cheap. |

---

## 3. THE WEEKDAY RHYTHM (fallback when the dated calendar runs out / for quick reference)

| Weekday | Primary post | Pillar · Stage | CTA |
|---|---|---|---|
| Mon | LinkedIn — Origin / founder story | 3 · 1→3 | Soft |
| Tue | Short EN+HI — Wonder (from an episode) | 1 · 1→2 | Soft (class in bio) |
| Wed | LinkedIn — Build / demystify | 2 · 2→3 | Soft |
| Thu | Short EN+HI — Build / curiosity | 2 · 2→3 | Soft + teaser |
| Fri | LinkedIn + **Email** — class INVITE | 4 · 3→4 | **Medium (register)** |
| Sat | **LIVE CLASS** + Wonder Short | 4 · 4 | **Hard (book 1:1)** |
| Sun | LinkedIn — reflection · batch next week | 3 · 1→3 | None / soft |

Mix target: ~40% Wonder · 25% Build · 25% Origin · 10% Proof. Every Short ships EN + HI.

---

## 4. PER-FORMAT PRODUCTION RECIPE (apply the 5-beat skeleton)

**LinkedIn post (Origin/Build/Offer):**
- Line 1 = the hook (a feeling/tension — it's all that shows before "…see more"). Pull from the
  calendar row's hook or the emotion-OS hook bank.
- 5 beats compressed: hook → name the gap → the turn/insight → "and you can…" (agency) → one CTA.
- Short lines, white space, written like Deepak talks. Link in first comment, not line 1.

**Short / Reel (Wonder/Build):**
- 0–1s: strongest visual + spoken/text hook (feeling first, no logo intro).
- 5 beats in 15–45s; re-hook at ~50%; big word-synced captions; readable muted.
- Cut from the 14 existing episodes first. Logo at the END. EN + HI.
- CTA soft: "free class — link in bio."

**Email (Friday invite):**
- Subject = the hook (curiosity/wonder). One idea, one feeling, one CTA = register for Saturday.
- Plain + personal > designed + corporate.

---

## 5. RENDER HANDOFF (Shorts)

Give the render skill a tight brief from the resolved slot:
`{ pillar, stage, feeling, hook (line 1), 5 beats, source episode to cut from, captions, EN+HI, CTA }`
→ `production-video-trigunai` (kinetic-caption pipeline) or `faceless-explainer-trigunai`.
Do not render before beats + feeling are locked (§1 step 2).

---

## 6. THE PRE-PUBLISH CHECKLIST (the gate — run on every asset)

```
[ ] FEELING in the first 1–3 seconds? (not a topic announcement)
[ ] Which PILLAR? (1 Wonder / 2 Build / 3 Origin / 4 Proof — matches today's slot?)
[ ] STAGE + CTA matched? (no "buy" to Stage-1; hard CTA only Stage 3–4)
[ ] BOTH wonder AND agency present?
[ ] VIEWER is the hero?
[ ] ONE clear CTA?
[ ] On-brand emotion? (no fear / hustle / healing / fake-proof)
[ ] EN + HI? (Shorts)
[ ] Drives to the engine (Saturday class / the list)?
[ ] Honest? (nothing inflated — true today)
```

---

## 7. ROLL-FORWARD (when the dated calendar window ends, e.g. after Jul 19)

The 30-day calendar is a window, not a wall. When it runs out, keep the machine turning:
1. Use the **weekday rhythm** (§3) as the default skeleton.
2. **Themes shift with the gate:** pre-launch → "warm + wonder"; in-cohort → **Proof becomes the
   lead pillar** (student wins out-convert everything — bump Proof to ~30%).
3. Regenerate a fresh 30-day grid by re-running the calendar build with the new month's gate/goal
   (ask the CEO skill for the current gate first). Don't post blind — re-anchor to the live objective.

---

## 8. THE SHIPPED LOG (`marketing_pipeline/CONTENT_LOG.md`)

Create it if absent. Append one line per shipped asset. This is **evidence**, the calendar is a
**claim** — the CEO work-scanner can't see posts that touch no file, so this log is how shipped
marketing becomes visible across sessions.

Format:
```
| Date | Slot | Pillar | Format | Link/where | Status | Notes (registrations etc.) |
|------|------|--------|--------|-----------|--------|----------------------------|
| 2026-06-22 | Mon Origin | 3 | LinkedIn | <url> | shipped | 4 comments, 1 DM |
```

At week's end, total the **registrations / 1:1s / paid** into the calendar's §5 metrics grid and
tell Deepak the honest scoreboard (not views — registrations→paid).

---

## 9. WEEKLY BATCH (Sunday — makes the week cheap)

| ~Time | Task | Output |
|---|---|---|
| 1.5 hr | Cut next week's **3 Shorts** from existing episodes (EN+HI) via the render skill | 6 uploads queued |
| 1 hr (Mon) | Write the week's **5 LinkedIn posts** in one sitting (calendar gives each hook) | 5 scheduled |
| 30 min (Fri) | Write + send the **email** invite | room filled |
| 1 hr (Sat) | **Run the live class** | leads → 1:1s |

No new footage needed while episodes remain unmined. Record a fresh "build an agent in 40 min" only
if Saturday classes need a replay asset.

---

## 10. RECOVERY (missed days happen — don't spiral)

- **Missed a normal post (Mon/Wed/Tue/Thu):** let it go or fold its angle into tomorrow. Do NOT
  double-post to "catch up" — it reads as spam.
- **Missed Friday invite or Saturday class:** this is the engine — recover immediately. Send the
  invite late same day; if the class slips, reschedule within 48h and tell the list honestly.
- **Whole week slipped:** run the §3 minimum (Sat class + Fri invite + Tue Short) and reset Sunday.
- The engine survives missed *content*; it does not survive a missed *class*. Guard the class.

---

## 11. THE 30-SECOND INVOCATION (what to say when Deepak says "run today's content")

1. `python3 ~/.claude/skills/content-daily-engine/scripts/today.py` → today's slot
2. State: **today is [pillar] · [stage] · feeling = [x] · hook = "[line 1]" · CTA = [y]**
3. Produce the asset (§4) → run the checklist (§6) → render if Short (§5) → distribute (§1.6)
4. Append to the log (§8); if Fri/Sat/Sun, do the special-day task (§2)
5. One honest line on where the week's registrations/paid stand vs. target

---

*Content Daily Engine v1.0 · created 2026-06-21 · Trigunaï Innovations.*
*Drives `03_CONTENT_CALENDAR_30DAY.md` through `content-marketing-emotion-connect`. Logs to CONTENT_LOG.md.*
*Ship daily. Guard the class. Count registrations, not likes. Built honestly.*
