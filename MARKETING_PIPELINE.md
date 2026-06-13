# TrigunAI Marketing Pipeline — Setup Playbook

> Created 2026-06-13 (CEO session). The funnel that turns YouTube viewers into email
> subscribers into paying students. Companion: `COURSE_CATALOG.md` (what we sell),
> `youtube_series/` (the content). Owner: Deepak.
>
> **Stack (locked 2026-06-13):** Traffic = YouTube (long + Shorts). List/nurture = Substack.
> Front door = rebuilt React landing page (`landing-page/`) → button points at Substack.
> Convert = Udemy (recorded) + cohort waitlist (₹50k, post-launch).

Legend: **[YOU]** = only Deepak can do (accounts, publish). **[CLAUDE]** = I produce the asset.

---

## The funnel

```
 YouTube episode / Short ──┐
 Instagram? (later)        ├──►  Landing page (trigunai.com)  ──►  Substack subscribe
 Network / WhatsApp        │         every CTA = "Get Ep2 +            │
 LinkedIn post (later)  ───┘          early-bird waitlist"             ▼
                                                            Welcome email (auto) ──► drip
                                                                                       │
                                                              Udemy course + ₹50k cohort waitlist
```

**The one rule:** every video, Short, and page ends with the SAME call —
*"Drop your email to get Episode 2 + the early-bird course waitlist."* One funnel, one CTA.

---

## Stage 1 — Substack (the list) · do this FIRST, live in ~1 hour

This is the backbone. It works before the landing page exists.

**[YOU] Steps:**
1. Create a Substack at substack.com → publication name + custom URL.
2. Paste the About + Welcome copy below.
3. Turn ON the automatic welcome email (Settings → Emails → Welcome email).
4. Publish the Ep1 post (copy below) → this becomes the first thing new subscribers see.
5. Grab your subscribe URL (e.g. `trigunai.substack.com/subscribe`) — every CTA points here.

### [CLAUDE] Publication name + tagline (ready to paste)
- **Name:** `AI is the Universal Mind`
- **Tagline:** `Every AI breakthrough is humanity rebuilding one faculty of its own mind. Watch the mirror.`
- **By:** Deepak Kumar · TrigunAI

### [CLAUDE] About page (ready to paste)
> Every few months, AI crosses a line we thought was ours alone — it pays attention, it learns,
> it imagines. This series argues something stranger: each breakthrough is humanity *accidentally
> rebuilding one faculty of its own mind*. AI is a mirror, not a copy — and looking into it shows
> you how your own attention, memory, and intuition actually work.
>
> Free episodes (animated, ~7 min) drop here and on YouTube. Subscribers get each new episode first,
> plus early-bird access to the hands-on courses where we *build* these systems — with real GPUs and
> a VR classroom. Look closely at one, and you understand the other.
>
> — Deepak (founder, TrigunAI · shipped a VR app to the Meta Quest store)

### [CLAUDE] Welcome email (auto-sends on subscribe — ready to paste)
> **Subject:** You're in — here's Episode 2 🧠
>
> Welcome. You just joined people who want to understand the machinery of mind — theirs and the machine's.
>
> Here's what happens next:
> - **Watch Episode 1 — Attention** (if you haven't): [YouTube link]
> - **Episode 2 — The Learning Loop** is yours early, right here: [Ep2 YouTube/unlisted link]
> - New episodes land first in your inbox, ~every 1–2 weeks.
>
> And the reason this exists: these episodes are the *why*. The **courses** are the *how* — where we
> actually build it (VR/MR apps, agentic systems, machine learning) with real GPU access and live
> classes inside VR. I'm opening an **early-bird waitlist** now — reply "WAITLIST" and I'll make sure
> you get the founding-cohort price.
>
> Look closely at one, and you understand the other.
> — Deepak

### [CLAUDE] Episode 1 launch post (ready to paste)
> **Title:** Attention — how a machine learned to read your mind (Ep.1)
> **Body:**
> When you read "The animal didn't cross the street because it was too tired" — you knew "it" meant
> the animal. Nobody taught you that. And now a machine knows it too. That one idea — figuring out
> which words should pay attention to which — is the breakthrough behind ChatGPT, Claude, all of it.
>
> [embed Ep1 YouTube video]
>
> This is Episode 1 of *AI is the Universal Mind*. Episode 2 (The Learning Loop) is already out for
> subscribers — you'll find it in your welcome email. New episodes land here first.
>
> *If this made the invisible visible for you, the courses are where we build it for real → reply "WAITLIST".*

---

## Stage 2 — YouTube (the traffic) · [YOU] create channel, upload

**[YOU] Steps:**
1. Create/brand the YouTube channel (logo from `Blender-Antigravity/trigun-logo-output/`).
2. Upload `youtube_series/ep01_FINAL_focus.mp4` as PUBLIC, then `ep02_FINAL_focus.mp4` (unlisted → share via Substack, or public after a few days).
3. Pin a comment with the Substack subscribe link.
4. Upload 2–3 Shorts cut from Ep1 (see cut plan below).

### [CLAUDE] Ep1 upload kit (ready to paste)
- **Title (pick one):**
  - `How a machine learned to pay attention — and what it reveals about your mind`
  - `Attention Is All You Need — explained as a faculty of YOUR mind | AI is the Universal Mind Ep.1`
- **Description:**
  > When you read a sentence, how do you know which words matter? You do it instantly — and nobody
  > taught you the rule. In 2017 a paper called "Attention Is All You Need" gave machines the same
  > ability, and it became the breakthrough behind ChatGPT and Claude.
  >
  > This is Episode 1 of *AI is the Universal Mind* — a series arguing that every AI breakthrough is
  > humanity rebuilding one faculty of its own mind. AI is a mirror, not a copy.
  >
  > 🧠 Get Episode 2 + early-bird course access: [Substack link]
  >
  > Chapters:
  > 0:00 The question · 0:30 Attention Is All You Need · 1:00 The cocktail party · ...
  >
  > #AI #attention #transformers #machinelearning #neuroscience
- **Thumbnail brief:** dark background; the sentence with the word **"it"** glowing gold, a line
  drawn from "it" → "animal"; bold 3-word overlay **"WHICH WORD MATTERS?"**; TrigunAI mark bottom-right.
- **Shorts cut plan (3× 30–50s, vertical):**
  1. The cocktail-party hook (scene_03) — "across a crowded room, someone says your name…"
  2. The "it" sentence puzzle (scene_01) — pure curiosity hook.
  3. "Your mind is a spotlight that chooses what to ignore" (scene_04) — the anchor line.
  - Each ends: *"Full episode + Episode 2 → link in bio / pinned comment."*

> Hindi track: `ep01_hi_FINAL_focus.mp4` exists — upload as a second public video (or a separate
> Hindi playlist) once the English funnel is live. Doubles your reach for zero new production.

---

## Stage 3 — Landing page (the front door) · [CLAUDE] build, [YOU] deploy

**Realign `landing-page/` from the OLD direction (Creator/Student SaaS) to the new spine.**
Its only job: one scroll, one CTA (Substack subscribe). Sections:
1. **Hero** — thesis line + "Watch Episode 1" + email/subscribe button (→ Substack).
2. **The series** — Ep1 + Ep2 embedded; "new episodes first by email."
3. **The courses** — catalog teaser (VR/MR · Agentic · ML) + "Join the early-bird waitlist."
4. **Why me** — Deepak's credibility: shipped a Quest app to Meta alpha; real GPU/Isaac-Sim infra.
5. **Footer CTA** — subscribe again + socials.

Deploy: trigunai.com (Azure Static Web Apps or Squarespace redirect). The subscribe button can
simply link to the Substack subscribe URL — no backend needed.

---

## Stage 4 — Convert · [YOU] Udemy listing, [CLAUDE] copy

1. **[CLAUDE]** Udemy listing copy (title, subtitle, what-you'll-learn, description) for the VR flagship.
2. **[YOU]** Create the Udemy course shell + upload first 2–3 modules + set price + buy button ON.
3. **[YOU]** Add the Udemy link to the welcome-email drip + landing page once live.
4. Cohort waitlist (₹50k) = a reply-"WAITLIST" tag in Substack for now; formalize post-launch.

---

## The drip (after welcome) · [CLAUDE] ready when list has subs
- **Email 2 (day 3):** the story behind the series + "what we're building" (course teaser).
- **Email 3 (day 7):** Episode-topic deep cut + soft waitlist CTA.
- **Email 4 (launch):** "The first course is live — founding-cohort price for you."

---

## This week's order of operations (don't reorder — distribution before polish)
1. **[YOU]** Substack live (Stage 1) — list capturing. ← the single most important step
2. **[YOU]** YouTube channel + Ep1 public + Shorts (Stage 2).
3. **[YOU]** Post Ep1 to your network/LinkedIn with the Substack link.
4. **[CLAUDE]** Build the landing page (Stage 3) in parallel — does NOT block 1–3.
5. **[CLAUDE]** Udemy + drip copy (Stage 4) as recording progresses.

**Scoreboard (must move off zero this week):** episodes published ✓ · Substack subs > 0 · first "WAITLIST" replies.
