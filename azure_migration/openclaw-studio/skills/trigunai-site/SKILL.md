---
name: trigunai-site
description: "The PUBLIC-SITES agent — trigunai.com (the marketing homepage), studio.trigunai.com (the Studio web app), and learn.trigunai.com (retired → 301). All three are served by ONE container app (`triguai-frontend`) in a SEPARATE Azure subscription from the Acharya app. Use whenever Deepak wants to change/deploy the public homepage (hero, pricing, policy pages, teacher band, episodes), the Studio site, or ship a landing change LIVE. Triggers: 'trigunai.com', 'the homepage', 'the public site', 'the landing page' (the marketing one, NOT the acharya app landing), 'the studio site', 'pricing page', 'deploy trigunai.com'. CODE changes → edit via `trigun-coding` (Codex) on the Gurukul box, then deploy with the helper. Siblings: `acharya-frontend` (the acharya.trigunai.com APP + its own landing) and `qbank-data` (the question bank). NOT for the acharya app itself, audio/video (studio-*), or the WhatsApp tutor."
metadata: { "openclaw": { "emoji": "🌐", "requires": { "bins": ["ssh","scp"] } } }
---

# trigunai-site — the public marketing sites

You maintain **trigunai.com + studio.trigunai.com + learn.trigunai.com**, all served by ONE container
app (`triguai-frontend`) in Azure sub `7db80eaf` / RG `triguai-prod` / registry `triguaiacr`. You EDIT
via Codex on Gurukul and DEPLOY with a helper. **⚠️ One image serves all three domains — always verify
all three after a deploy.**

## Where the code lives + how to reach it
`source ~/.openclaw/qbank.env` (GURUKUL, GKEY). It's a **git repo on the Gurukul box**: `~/triguai_site`
(static `landing/` pages + `deployment/backend` FastAPI + a Vite Studio app). Run via `ssh -i $GKEY $GURUKUL '<cmd>'`.

## What's here (and what's NOT)
- `landing/index.html` = **trigunai.com homepage** (Acharya-led hero, WhatsApp scan card, teacher band, episodes).
- `landing/pricing.html` + policy pages (`privacy-policy`, `terms-of-service`, `refund-policy`, …).
- `deployment/backend/main.py` = the small FastAPI backend (reverse-proxied at `/api/*`, powers studio).
- The Vite **Studio** app (compiled into the image — a static-page change STILL triggers the full build).
- `learn/index.html` is **RETIRED** (host 301s to acharya) — don't treat it as live.
- **NOT here:** the acharya.trigunai.com app + its `acharya.html` landing — that's the **`acharya-frontend`** skill.

## To CHANGE → Codex on Gurukul, then deploy
1. Edit via **`trigun-coding`** (Codex) pointed at `~/triguai_site` ON Gurukul. Smallest change; match style. `git commit`.
2. Deploy: `ssh -i $GKEY $GURUKUL 'cd ~/triguai_site && ./triguai_deploy.sh'`
   — uses Gurukul's default az (already in the `triguai-prod` subscription), builds `triguai-frontend:vN`
   (auto-bumped) with the correct VITE build-args, rolls the container, **verifies all 3 domains**.
   (Pass a tag to override: `./triguai_deploy.sh v120`.) The Vite build is ~2.5 min.
3. **VERIFY in a browser** — the helper checks `trigunai.com`=200, `studio/api`=ok, `learn`=301. Eyeball the change too.

## 🔴 GOTCHAS
- **ONE image = 3 live domains.** A bad change breaks all three — the helper verifies all three; if any isn't
  200/ok/301, roll back (`./triguai_deploy.sh <previous vN>`).
- **Different Azure subscription** (`7db80eaf`) from the Acharya app — the helper handles it via Gurukul's
  default az identity (NOT the service principal that `acharya-frontend`/`qbank-data` use).
- **Bump the tag every deploy** (helper does). The build recompiles the whole Studio app even for a text change.
- **The course count** ("Ten courses…") is hardcoded in a couple of spots — bump together if the catalogue grows.

## State (2026-07-25)
Live ≈ `triguai-frontend:v109` (deployed from the Gurukul repo via the helper; all 3 domains verified).
Homepage leads with Acharya + a WhatsApp scan card + teacher band; episodes moved down; learn.* is 301'd.
