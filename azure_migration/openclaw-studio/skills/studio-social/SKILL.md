---
name: studio-social
description: "Auto-POST a finished vertical MP4 reel + caption to Instagram AND Facebook (as Reels) via the Meta Graph API publisher on the render box. Use when a reel is ready to go live on socials, or the daily engine needs to publish. Hosts the MP4 on the box's public URL (rtx.trigunai.com/reels), writes the manifest, then posts to @trigunaiinnovations + the Trigunai Innovations FB Page. Tracks posted state so it never double-posts. NOT for YouTube (studio-youtube) or making the video (studio-reel/studio-video)."
metadata: { "openclaw": { "emoji": "📣", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-social — Post Reels to Instagram + Facebook

Drives the `marketing_pipeline/ig_publish/` Meta Graph API publisher **on the EC2 render box** (the IG/FB token + Caddy public host live there). Instagram fetches the video live from a public URL, so **EC2 must be running** and the file must be hosted.

## When to Use
✅ A finished 1080×1920 reel MP4 is ready → publish to IG + FB.

## When NOT to Use
❌ YouTube → `studio-youtube`. ❌ Making the video → `studio-reel`/`studio-video`. ❌ LinkedIn → not automated; deliver to Deepak for manual posting.

## Requires (on the render box, already set up)
- `~/marketing_pipeline/ig_publish/.env` → `IG_ACCESS_TOKEN` (permanent page token; underlying user token expires ~2026-08-31 — re-mint then).
- Caddy serves `/var/www/reels/` at `https://rtx.trigunai.com/reels/`.
- Meta app "Gurukul": IG user `17841480511571246`, FB page `1235364529650979`.

## Step 0 — EC2 must be up (IG fetches the video live)
Social posting is **EC2-only** (token + host are there — NOT on the T4). Ensure EC2:
```bash
source ~/.openclaw/farm.sh          # if FARM_NAME != ec2, start EC2 first (see studio-daily ensure_farm)
[ "$FARM_NAME" != ec2 ] && echo "IG/FB posting needs EC2 up — start it before posting" && exit 1
SSH(){ ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"; }
```

## Post a reel (IG + FB)
```bash
# 1. host the MP4 on the box's public webroot
scp -i "$EC2_KEY" /tmp/reel.mp4 "$EC2_USER@$EC2_IP:/tmp/reel.mp4"
SSH 'sudo cp /tmp/reel.mp4 /var/www/reels/ && sudo chmod 644 /var/www/reels/*.mp4'

# 2. add it to the manifest (filename + caption). Append, don't overwrite prior entries.
SSH 'cd ~/marketing_pipeline/ig_publish && python3 - <<PY
import json,os
m="reels_manifest.json"; a=json.load(open(m)) if os.path.exists(m) else []
a.append({"filename":"reel.mp4","caption":"<CAPTION incl CTA + 3-5 niche hashtags>"})
json.dump(a,open(m,"w"),indent=2)
PY'

# 3. publish to IG then FB (post-all only posts unposted items)
SSH 'cd ~/marketing_pipeline/ig_publish && set -a; source .env; set +a && \
  python3 ig_reels_publish.py check && python3 ig_reels_publish.py post-all && \
  python3 fb_reels_publish.py check && python3 fb_reels_publish.py post-all'

# 4. confirm what went live
SSH 'cd ~/marketing_pipeline/ig_publish && cat posted_state.json fb_posted_state.json'
```

## Caption rules (from the 15-day plan)
- Lead with the hook, end with the CTA (A=Acharya wa.me/919135255107 · C=acharya.trigunai.com · T=reply TEACHER).
- 3–5 niche hashtags (see the plan's hashtag sets). Put `?utm_source=ig` / `utm_source=fb` on any acharya.trigunai.com link.
- **Honesty guardrail:** no fabricated testimonials / student counts.

## Gotchas
- **EC2 must stay up during publish** — Meta pulls the video from the URL; if the box stops mid-post it fails.
- `post-all` is idempotent (state files) — safe to re-run; only unposted items go.
- Verify the file is 1080×1920 (Reels spec) before posting.
- IG account must stay a Business account linked to the FB Page (already configured).
