---
name: studio-daily
description: "The DAILY content engine orchestrator. Reads today's row from the content plan, starts the render farm, generates the day's content (reels, FlowArt music, carousels), AUTO-POSTS reels to Instagram+Facebook+YouTube Short, DELIVERS the manual pieces (LinkedIn posts, carousels, Stories) to Deepak on Telegram, then stops the farm and logs everything. Runs unattended from an 11am cron, or on demand ('run today's content', 'what's today', 'do the daily post', 'run the content engine'). Honors the kill-switch and the honesty guardrail."
metadata: { "openclaw": { "emoji": "🗓️", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-daily — Autonomous Daily Content Engine

Turns the 15-day plan into daily posts. Reads `~/.openclaw/content_plan.json`, produces the day's assets on the render farm, routes each to its platform, then shuts the farm down.

## Kill switch (check FIRST)
```bash
[ -f ~/.openclaw/PAUSE_DAILY ] && { echo "DAILY PAUSED (remove ~/.openclaw/PAUSE_DAILY to resume)"; exit 0; }
```
To pause the whole engine: `touch ~/.openclaw/PAUSE_DAILY`. To resume: delete it.

## 1. Find today's row
```bash
TODAY=$(TZ=Asia/Kolkata date +%F)
DAY=$(python3 -c "import json,sys;d=json.load(open('$HOME/.openclaw/content_plan.json'));r=[x for x in d['days'] if x['date']=='$TODAY'];print(json.dumps(r[0]) if r else '')")
[ -z "$DAY" ] && { echo "no plan row for $TODAY — nothing to do"; exit 0; }
```

## 2. ensure_farm() — start EC2 if down (fixed IP 34.192.145.204)
IG/FB posting + FlowArt NVENC are **EC2-only**, so the daily run needs **EC2**, not the T4.
```bash
source ~/.openclaw/farm.sh
if [ "$FARM_NAME" != ec2 ]; then
  # needs AWS creds on this box (~/.aws/credentials, scoped ec2:Start/Stop/Describe on i-047ebf759f2386e71)
  aws ec2 start-instances --instance-ids i-047ebf759f2386e71 --region us-east-1 || \
    { echo "cannot start EC2 (no AWS creds on box) — tell Deepak to start it"; exit 1; }
  for i in $(seq 1 20); do ssh -i ~/.ssh/trigunai_key.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o BatchMode=yes ubuntu@34.192.145.204 'echo UP' 2>/dev/null | grep -q UP && break; sleep 15; done
  source ~/.openclaw/farm.sh   # re-resolve → now ec2
fi
```

## 3. Produce + route each item in today's row
Read the JSON fields and act:

- **`hero_reel`** → `studio-script` (write a punchy 9:16 reel_script.json from `brief`+`cta`, honesty guardrail) → `studio-reel` (render 1080×1920) → then **auto-post**:
  - `studio-social` → Instagram + Facebook (caption = hook + CTA[`cta`] + 3–5 niche hashtags + `?utm_source=ig/fb`)
  - `studio-youtube` → YouTube Short (title from brief; **public** per "fully autonomous")
- **`flowart_music`** (days 8, 15) → `studio-track`/`studio-music` (make the track) → `studio-flowart` (visualizer) → `studio-youtube` **FlowArt channel**.
- **`carousel`** (days 2, 7, 12) → generate card copy (per `brief`+`cta`) + images (slide/gpt-image) → **deliver to Deepak on Telegram** (carousels aren't auto-posted). 
- **`linkedin`** → compose the post text from `brief`+`cta` + attach the day's reel/asset → **deliver to Deepak on Telegram** (LinkedIn API pending → manual).
- **`stories`** → deliver the Story idea(s)/asset to Deepak on Telegram.

## 4. release_farm() — stop EC2 (save cost)
```bash
aws ec2 stop-instances --instance-ids i-047ebf759f2386e71 --region us-east-1 2>/dev/null || \
  ssh -i ~/.ssh/trigunai_key.pem -o StrictHostKeyChecking=no ubuntu@34.192.145.204 'sudo poweroff' 2>/dev/null
```
(SSH `poweroff` also stops an EBS instance — works even without AWS creds. Skip stopping only if a long job — e.g. a 1-hr FlowArt render or table-read — is still running.)

## 5. Log + report
- Append to `~/.openclaw/content_log.md`: date, what was generated, what auto-posted (with IG/FB media ids + YT link), what was delivered-for-manual.
- Send Deepak a Telegram summary: ✅ posted (IG/FB/YT links) · ✋ waiting on you (LinkedIn text + carousel/stories assets attached).

## Guardrails
- **Honesty:** no fabricated testimonials/metrics; the Day-11 teacher "case" must be real or framed as "how it would work" (carried in the plan).
- **Autonomous posting is live** — content goes public without human review. The kill switch (`~/.openclaw/PAUSE_DAILY`) stops it instantly; the content log is the audit trail.
- **Never** double-post (studio-social state files are idempotent).
- If a render fails, **do not** post a broken asset — log the failure, deliver a note to Deepak, skip that item.

## On-demand
"run today's content" / "run the daily" → execute steps 1–5 now. "what's today" → just read + report today's row without producing.
