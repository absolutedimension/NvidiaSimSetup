---
name: trigunai-marketing
description: Agentic multi-channel marketing publisher for TrigunAI — drives the publish.py CLI to broadcast course/episode/free-class content to email (Azure Communication Services), Telegram, Discord, and YouTube from one command, with Deepak's periodic input (API keys + content approval) and the human close kept manual. Use when the user wants to MARKET, PROMOTE, or DISTRIBUTE the courses / free class / episodes; "send the email", "post the teaser", "announce the class", "blast the waitlist", "publish to channels", "drive signups", "run the campaign", "market the cohort", "promote the course", "email the list", "post to telegram/discord", or any marketing-distribution task. Also trigger when the CEO agent decides marketing action is the week's move. Reads MARKETING_PLAN_JULY18.md for strategy and the admin dashboard for metrics (CLASS REQUESTS, PAID).
---

# TrigunAI Marketing — agentic publishing, human close

This skill turns marketing distribution into one-command, agent-drivable actions. It is the
execution arm of `MARKETING_PLAN_JULY18.md`. The strategy lives there; the *doing* lives here.

## The one rule that governs everything

**Automate the broadcast. Keep the close human.**

- ✅ AUTOMATE (this skill): email broadcasts/sequences, Telegram/Discord posts, YouTube uploads,
  multi-channel fan-out. Owned + ToS-safe channels.
- ❌ DO NOT automate: 1:1 cold DMs on WhatsApp / LinkedIn / Instagram. It violates their ToS
  (account-ban risk) **and** the personal conversation is Deepak's conversion edge. The skill can
  *draft* DM text for Deepak to send by hand — it must never send 1:1 outreach itself.

## What the agent does vs. what Deepak does

| Step | Owner |
|---|---|
| Draft content (copy, captions, email HTML, post text) | **Agent** (use the video/audio pipeline skills for media) |
| Pick channels + assemble the campaign manifest | **Agent** |
| Dry-run + show Deepak the preview for approval | **Agent → Deepak** |
| Provide API keys / approve the send | **Deepak** (periodic input) |
| Fire the broadcast with `--send` | **Agent** (after approval) |
| Warm 1:1 DMs + the free class + the payment close | **Deepak** (human, always) |
| Read metrics back (CLASS REQUESTS, attendance, PAID) | **Agent** from the admin dashboard |

## The engine: `marketing/publish.py`

Safety default = **DRY RUN**. Nothing transmits without `--send`. Always dry-run first, show
Deepak, then add `--send`.

```bash
cd marketing

# Email broadcast (Azure Communication Services)
python3 publish.py email --to lists/waitlist.csv --subject "Free VR class Fri" \
      --html emails/free_class_invite.html            # dry run
python3 publish.py email --to lists/waitlist.csv --subject "Free VR class Fri" \
      --html emails/free_class_invite.html --send      # real send

# Telegram / Discord single post
python3 publish.py telegram --text "VR app live on Quest. Free class Fri. <link>" --video teaser.mp4 --send
python3 publish.py discord  --text "..." --file teaser.mp4 --send

# Fan one item to many channels (manifest in campaigns/)
python3 publish.py post     --manifest campaigns/wk0_short_proof.json          # dry run
python3 publish.py post     --manifest campaigns/wk0_short_proof.json --send

# Email campaign manifest
python3 publish.py campaign --manifest campaigns/free_class_invite.json --send

# YouTube (delegates to the proven youtube_series/yt_upload.py)
python3 publish.py youtube run yt_manifest.json --only ep08 --privacy public
```

Every send is logged to `marketing/publish_state.json`.

## Setup (one-time, Deepak provides the secrets)

1. `cp marketing/config.example.env marketing/.env` (it's gitignored — never commit it).
2. **Email (Azure Communication Services):** Deepak already uses ACS for magic-link auth.
   - Easiest: paste `ACS_CONNECTION_STRING` (Azure portal → the Communication Service → Keys).
   - Or `az login` path: set `ACS_ENDPOINT` + `pip install azure-identity` (uses his logged-in CLI).
   - Set `ACS_SENDER` to the verified sender on his ACS Email domain.
   - `pip install azure-communication-email`
3. **Telegram (optional):** @BotFather → token → add bot as channel admin → set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`.
4. **Discord (optional):** Server → Integrations → Webhooks → copy URL → `DISCORD_WEBHOOK_URL`.
5. **Audience list:** export the admin dashboard CSV (`learn.trigunai.com/dashboard/admin` → Download CSV)
   into `marketing/lists/waitlist.csv` (needs an `email` column; test accounts auto-skipped if they lack `@`).

## Content rules (from the plan + CEO OS)

- **Lead with the live product:** "I have a VR app **live on the Meta Quest store** (+ more in testing)."
  Never call the alpha apps "live." This proof point IS the course promise — use it as the headline.
- **Aim CTAs at buyers (B/C/D), reach via A.** Every asset ends with ONE CTA → the free-class request.
- **No inflated claims, no "industry-recognized cert," no healing/hype framing.** (CEO OS anti-patterns.)
- **Bilingual where free** (EN+HI) widens reach at near-zero cost — reuse the video pipeline's HI path.

## The metric loop

After any campaign, read the admin dashboard and report back to Deepak:
- **CLASS REQUESTS** (leading #1 — must move off 0)
- free-class **attendance**
- **PAID (LIVE COHORT)** (THE GATE)
If CLASS REQUESTS stays 0 after a push, the fix is a **sharper CTA / better free-class hook**, not more volume. Say so.

## Guardrails

- Dry-run first, every time. Show Deepak the preview before `--send`.
- Don't let building/posting eat the launch run-up. Email + the free-class invite are the highest-ROI
  actions before July 18; exotic multi-channel automation is post-launch polish.
- Throttle email (the script already does). Keep lists clean (export fresh from the dashboard).
- Stop-condition (from the plan): zero CLASS REQUESTS by Jul 6 = topic/CTA not landing — diagnose, don't spend more.

## Extending later (post-launch, only if it pays)
- Meta Graph adapter (IG/FB Reels auto-publish) — needs a Business account + app review.
- X/Twitter adapter — paid API tier.
- Self-host Postiz on EC2 as a LinkedIn/X/IG fan-out hub (avoids per-API pain).
Add these as new functions in `publish.py` mirroring the Telegram/Discord adapters.
