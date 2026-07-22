---
name: maintain-trigunai-system
description: >
  Master operational map for the ENTIRE TrigunAI production system — every site, repo, Azure
  resource, database, deploy command, secret, and safety rule. Load this BEFORE making any change
  to: lms.trigunai.com (the self-paced LMS — courses, interactive lessons, Razorpay subscriptions,
  admin/analytics, SEO), learn.trigunai.com / trigunai.com / studio.trigunai.com (the public sites +
  course catalogue + live-cohort admin), the Gurukul "Acharya" WhatsApp/web AI tutor, the billing,
  or the cross-system bridge. It tells you which repo to edit, which Azure subscription/registry/
  container to deploy to, how to verify, and what NOT to break. Triggers: "change/fix/update the
  LMS / course site / dashboard / subscriptions / Acharya / pricing / lessons / SEO", "deploy
  trigunai", "how does <X> work / where does <X> live", "maintain the trigunai system", "add a
  metric / tile / page", or any edit that touches a live trigunai.com property.
---

# Maintain the TrigunAI system

> **Read this first, then the linked memory for the subsystem you're touching.** This skill is the
> map; the memories hold the depth. Make the smallest change in the right repo, test locally, deploy
> with the right command + subscription, verify live, then **restore the default Azure subscription**
> and **update the memory**.

---

## 0. The whole system in one table

| Domain | What it is | Repo (edit here) | Azure: sub · RG · registry · app |
|---|---|---|---|
| **acharya.trigunai.com** (canonical) + **lms.trigunai.com** (301→acharya) | Self-paced LMS: 9 courses, 43 interactive lessons, Razorpay subscriptions, admin + analytics, SEO, Acharya-iframe dashboard. **`acharya.trigunai.com` is now CANONICAL** — both are custom domains on the SAME `lms` app; `lms.trigunai.com` **301-redirects** to acharya (path+query kept) via the `track_visits` middleware, EXCEPT `/webhook`, `/api/bridge`, `/healthz` (server-to-server, can't follow a 301). Env `BASE_URL=https://acharya.trigunai.com`. `main.py::root()` serves the gold landing (`templates/acharya.html`, live WebGL shader thumbnails, Founding-Learner offer) to logged-out visitors; logged-in → `/dashboard`. ⚠️ The "7-day → free year" offer is MARKETING-ONLY — no streak tracking / grant / DPDP consent built yet. | `~/Documents/01_Active/NvidiaSimSetup/lms` (FastAPI) | `cb656d95` · `trigunai-video-creator` · `trigunaicr` · app `lms` |
| **trigunai.com**, **studio.trigunai.com** (+ **learn.trigunai.com** RETIRED→301 acharya) | Public homepage (now **leads with Acharya** in the hero; episodes moved down) + the Studio web app. **`learn.trigunai.com` is retired** — its nginx server block in `deployment/frontend/nginx.conf` now `301`s everything to `acharya.trigunai.com` (the course catalogue collapsed onto Acharya). | `~/Documents/01_Active/ShaderStudio` (static `landing/` + `deployment/backend` FastAPI + Vite studio) | `7db80eaf` · `triguai-prod` · `triguaiacr` · app `triguai-frontend` (nginx host-routes the domains) |
| **gurukul.trigunai.com** | "Acharya" — the agentic WhatsApp + web AI tutor (OpenClaw + custom bridge) | on the VM; repo copies in `NvidiaSimSetup/agentic_cohort/` | VM `20.219.2.53` (`ssh -i ~/.ssh/gurukul_key dk_trigun@…`), sub `AzurePayAsgo` (`cc469e97`), RG `trigunai-gurukul-rg` |

**Two Azure subscriptions, BOTH named "Azure subscription 1" — use IDs, not names:**
- `cb656d95-2f68-469f-b2b5-aee1ac1be625` → **the default**; LMS + its Postgres live here.
- `7db80eaf-a061-45cd-b01e-09c815acbe95` → the public-sites frontend (`triguai-prod`).
- `cc469e97-…` (`AzurePayAsgo`) → the Gurukul VM.

> **RULE: after any `az account set` to a non-default sub, restore it:**
> `az account set --subscription cb656d95-2f68-469f-b2b5-aee1ac1be625`

---

## 1. Make-a-change workflow (always)

1. **Identify the subsystem** from §0 → open its section below + read its memory ([[…]] links).
2. **Edit in the correct repo** (LMS edits never go in ShaderStudio and vice-versa). Make the minimal change; match surrounding style.
3. **Test locally** before deploy. Python: `python3 -m py_compile <files>`. Templates/logic: render or smoke-test with a throwaway **python3.11 venv** (the LMS uses 3.10+ union syntax; system python3 is 3.9 — use `python3.11 -m venv /tmp/v`). The LMS DB is Postgres in prod but SQLite locally (`create_all` builds tables; the `ALTER … IF NOT EXISTS` migration lines skip on SQLite — expected).
4. **Deploy** with the subsystem's command (§2–§4). **Bump the image tag.**
5. **Verify live** (curl health + grep for your change's marker; check other co-hosted sites still 200).
6. **Restore default sub** + **update the memory** for that subsystem.

---

## 2. LMS — lms.trigunai.com  (repo: `NvidiaSimSetup/lms`)

**Stack:** FastAPI + SQLAlchemy + Jinja2, Azure Postgres, Azure Container Apps. Magic-link email auth
(no passwords). Read [[project-lms-subscriptions]], [[project-lms-lessons]].

**Key files (`lms/app/`):** `main.py` (routes + the `track_visits` middleware), `models.py`,
`config.py` (all env/secrets), `seed.py` (DB seed + idempotent `_migrate()` ALTERs, runs on startup),
`billing.py` (Razorpay), `analytics.py` (page-view tracking + admin metrics), `seo.py` (robots/sitemap/
llms.txt + JSON-LD), `legal.py` (policy pages), `course_details.py` (rich per-course detail shown on /login). Templates in `app/templates/`; lessons are **built**, not
hand-written — author `lesson_src/<course>/<slug>.json` then `python3 tools/build_lessons.py` (schema:
`tools/STEP_SCHEMA.md`). Course catalogue = `COURSES` list in `main.py`; course content/journeys in `seed.py`. **Brand:** the whole app is the Acharya dark-gold theme — token source = `:root` in `static/app.css`; see [[reference-acharya-brand]] before any UI change.

**Custom domains on this app:** `lms.trigunai.com` (default) + **`acharya.trigunai.com`** (gold tutor
landing). Both are CNAME→`lms.<env>.azurecontainerapps.io` + a `asuid.<sub>` TXT (= app
`customDomainVerificationId`), bound via `az containerapp hostname add/bind … --validation-method CNAME`
(managed TLS). To add another subdomain to this app: same two DNS records, then host-route it in
`main.py::root()`.

**Deploy (bump vN; current ≈ v46):**
```bash
cd ~/Documents/01_Active/NvidiaSimSetup/lms
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
# verify
for i in $(seq 1 15); do curl -sf https://lms.trigunai.com/healthz && break || sleep 8; done
```

**Database (read/query):** the `DATABASE_URL` is container secret `dburl` → `trigunai-lms-pg.postgres.database.azure.com`.
```bash
val=$(az containerapp secret show -n lms -g trigunai-video-creator --secret-name dburl --query value -o tsv)
# query with a python3.11 venv + psycopg2-binary; strip the "+psycopg2" from the URL
```
**Secrets** (set via `az containerapp secret set … --secrets name=val`, referenced by env `…=secretref:name`):
`dburl`, `seckey`, `acsconn` (email), `aoaikey`, `rzp-key-secret`, `rzp-webhook-secret`, `bridge-key`.
Plain env: `RZP_KEY_ID`, `RZP_PLAN_ID`, `SUBS_ENABLED`, `BRIDGE_KEY=secretref:bridge-key`, etc.

**Subscriptions / Razorpay = LIVE.** Two trial paths (card on file vs no-card "skip payment"); access gate
`has_access()` in main.py expires no-card trials at `trial_end`. Existing cohort = `grandfathered` (never
charged). To change pricing/trial: `config.py` (`PRICE_INR`, `TRIAL_DAYS`) + Razorpay plan. Webhook →
`/webhook/razorpay`. Full detail + the go-live values: [[project-lms-subscriptions]].

**Admin + analytics:** `/admin` (admin-only, at `acharya.trigunai.com/admin`) shows MRR, subs, funnel,
learning, website analytics. Metrics in `analytics.py::metrics(db)`; page views logged by the
`track_visits` middleware to the `visits` table.

**Admin WhatsApp notifications (`app/notify.py`):** pushes founder ops alerts (new signup · trial
started · new paying subscriber · cancellation) to `ADMIN_WHATSAPP`, calling the Graph API directly
(live Gurukul bridge untouched), fire-and-forget on a daemon thread. **Sends via the `admin_alert`
UTILITY template** (body `🔔 TrigunAI admin alert\n\n{{1}}\n\n…`) — transactional, delivers any time;
**falls back to plain text** if the template send fails (plain text delivers only within the admin's 24h
window). ⚠️ MARKETING templates (`gurukul_announce`) get throttled by Meta and silently don't
deliver — that's why admin alerts use a Utility template. Env: `WA_TOKEN=secretref:watoken` (from VM's
`~/.openclaw/wa_cloud.env` META_TOKEN), `WA_PHONE_ID=1226742713857457`, `WA_GRAPH_VERSION`,
`ADMIN_WHATSAPP=918454964893` (Deepak), `NOTIFY_ENABLED=1`. WABA `1017321330664208`; create/check
templates via `graph.facebook.com/<WABA>/message_templates`. To add an event: `notify.notify_admin("single-line text")`.

**Acharya WhatsApp ⇄ LMS bridge endpoints** (`main.py`, all `X-Bridge-Key` server-to-server except the
public web one). The VM bridge calls these so a WhatsApp learner becomes a real LMS account:
- `POST /api/bridge/signup` → `{email,course,phone}` → creates/links a `Student` (sets `Student.phone`),
  fires the new-signup admin alert. Called when a WhatsApp learner finishes onboarding (picks course + email).
- `POST /api/bridge/course-request` → `{topic,email,phone}` → row in **`course_requests`** table
  (`source='whatsapp'`) + admin alert. Called for custom-topic requests on WhatsApp.
- `POST /api/course-request` → **public** (no auth, light dedup) → `course_requests` (`source='web'`) +
  admin alert. Powers the "Don't see what you want to learn?" form on `/login`.
- Course requests surface on `/admin` as a "📚 Course requests" table. `Student.phone` + the optional
  WhatsApp field on the `/login` signup + request forms (carried through the magic link `&phone=`).
- The acharya landing + `/login` heroes show a **WhatsApp scan QR** + **"English or हिंदी"** multilingual line.
The bridge needs `LMS_SIGNUP_URL=https://acharya.trigunai.com/api/bridge/signup` + `LMS_BRIDGE_KEY`
(= LMS `BRIDGE_KEY`) in `~/.openclaw/wa_cloud.env`. Full flow → [[project-gurukul-vm]].

**Adding a course or lessons:** use the **`add-trigunai-course`** skill (it also deploys the tutor bank to the VM).

---

## 3. Public sites — trigunai.com / learn / studio  (repo: `ShaderStudio`)

One container (`triguai-frontend`) serves all three via nginx host-routing + an embedded FastAPI backend
(`deployment/backend/main.py`, reverse-proxied at `/api/*`) + the Vite Studio app. Read [[project-course-site-shaderstudio]].

**Edit:** static pages in `landing/` — `index.html` is **trigunai.com home, now Acharya-led**: hero =
"Meet Acharya." + gold brand panel (`landing/acharya-mark.png`) + a **WhatsApp scan card**
(`landing/acharya-wa-qr.png` → `wa.me/919135255107`) + **"English or हिंदी"** multilingual line (Noto Sans
Devanagari is loaded); the episode "series" was moved DOWN (id=`series`); the Founding-Learner offer band
sits mid-page. The course count ("Ten courses…") is hardcoded in a couple spots — bump together when the
catalogue grows. **`learn/index.html` is RETIRED** (the host 301s to acharya; the file is kept for
reference only — don't treat it as live). `pricing.html` + policy pages still live. Backend admin/API in
`deployment/backend/main.py`. (Don't edit NvidiaSimSetup `landing-page/` — stale.) See
[[project-course-site-shaderstudio]].

**Deploy (DIFFERENT sub; bump vN; current ≈ v96):**
```bash
az account set --subscription 7db80eaf-a061-45cd-b01e-09c815acbe95
cd ~/Documents/01_Active/ShaderStudio
az acr build --registry triguaiacr --resource-group triguai-prod \
  --image triguai-frontend:vN --image triguai-frontend:latest \
  --file deployment/frontend/Dockerfile \
  --build-arg VITE_TRIGUAI_API=/api --build-arg VITE_DISABLE_MUSIC_GEN=false \
  --build-arg "VITE_MUSIC_API=https://deepak-27562--triguai-musicgen-fastapi-app.modal.run" \
  --build-arg "VITE_JAMENDO_CLIENT_ID=7283080b" .
az containerapp update -n triguai-frontend -g triguai-prod --image triguaiacr.azurecr.io/triguai-frontend:vN
# verify ALL THREE survived the shared rebuild, then restore the default sub:
curl -s -m8 https://studio.trigunai.com/api/health   # → ok
curl -s -o /dev/null -w '%{http_code}' https://trigunai.com/        # 200
curl -s -o /dev/null -w '%{http_code}' https://learn.trigunai.com/  # 200
az account set --subscription cb656d95-2f68-469f-b2b5-aee1ac1be625  # RESTORE
```
The build compiles the whole Vite Studio app too (~2.5 min) — a static-page change still requires the full image.

---

## 4. Gurukul / Acharya — gurukul.trigunai.com  (on the VM)

Agentic WhatsApp + web tutor. OpenClaw + custom Node bridge `~/wa_bridge.mjs` ← Caddy TLS ← Meta
WhatsApp Cloud API. **The bridge is a systemd `--user` unit** — restart with `systemctl --user restart
wa-bridge` (NOT system-level; `systemctl wa-bridge` shows inactive). Repo copy
`agentic_cohort/whatsapp_cloud_bridge/bridge.mjs` == the live `~/wa_bridge.mjs` (edit repo → scp →
`systemctl --user restart wa-bridge` in a verified-quiet window). Web chat = `~/.openclaw/gurukul/chat.html`
served at `/chat` (embedded as the LMS dashboard hero iframe — no X-Frame-Options). Course banks:
`~/.openclaw/gurukul/courses/<id>.json`. Learner profiles = JSON in `~/.openclaw/students/<wa_id>.json`
(NOT a DB). **`/webhook` POST verifies no signature** → simulate inbound for testing:
`curl -X POST localhost:8788/webhook -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"<num>","type":"text","text":{"body":"hi"}}]}}]}]}'`.

**Acharya WhatsApp capabilities (all in `bridge.mjs::askAcharya` + the inbound handler):**
- **Cold-inbound onboarding**: new number → TrigunAI intro + 10-course menu (option 11 = "something else")
  → picks course → asks **email** → `lmsSignup()` creates a real LMS account → teaches (no silent agentic default).
- **Custom course requests**: any non-course reply / "11" → `submitCustom()` → `requestCourse()` POSTs the
  LMS course-request endpoint → "ready in ~2 working days".
- **Course switching**: an onboarded learner types "menu" / "switch" / "change course" → re-pick from the menu.
- **Teacher onboarding requests (2026-07-01)**: a prospective tutor replies **"TEACHER"** (per the teacher pamphlet) → `isTeacherIntent` → Acharya asks name/subject/#students → `submitTeacher()` logs it through the SAME course-request pipeline as `🎓 TEACHER ONBOARDING — …` (→ `course_requests` row + admin alert). **Stage-0 concierge: capture the lead, onboard the teacher OFFLINE — no teacher portal/provisioning built yet.** Student path untouched. Helpers in `bridge.mjs`: `isTeacherIntent`, `teacherPromptText`, `submitTeacher`. Deployed to live bridge 2026-07-01 (verified 200; backup `~/wa_bridge.mjs.bak.20260701_071342`).
- **Daily rate cap**: `RATE_LIMIT_PER_DAY` env (default 60) per number, counted before any LLM call (admins exempt).
- **Multilingual**: Acharya answers in English or हिंदी (the model handles it; just start chatting).
Full map: [[project-gurukul-vm]]. **This is the system Acharya runs on.**

**Business number:** `+91 91352 55107` (Phone Number ID `1226742713857457`, verified "TrigunAI Innovations").
**Scan-to-enter onboarding (lms:v38):** the acharya landing has a "Scan, and start learning in WhatsApp"
section (`#whatsapp`) — a QR (`static/brand/wa-acharya-qr.png`) + green button, both pointing at
`https://wa.me/919135255107?text=Hi%20Acharya…`. User scans/taps → sends → the bridge auto-creates their
profile (Meta-compliant: the USER initiates; a business can't message first without a template). Course
defaults on auto-create — per-course routing would need a pre-seed or course-specific wa.me links.

```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
```
> ⚠️ **NO-DISRUPT RULE — students use this live.** NEVER restart `wa-bridge` / `openclaw-gateway` while a
> student may be mid-conversation. Adding a course bank = `scp` only (no restart). Bridge code changes: only
> in a verified-quiet window. Read-only diagnostics anytime. See [[feedback-gurukul-live-no-disrupt]].

**Acharya's TEACHING BEHAVIOR (the prompt/method) lives in 3 workspace files** — edit these to change
how Acharya teaches (not the bridge): `~/.openclaw/workspace/IDENTITY.md` (who), `SOUL.md` (how — the
**8 teaching laws**), `skills/gurukul-tutor/SKILL.md` (method + concept bank + SRS + deep-work session).
- ⚠️ **The gateway CACHES these at startup** — a `scp` alone does NOT take effect; you MUST
  `systemctl --user restart openclaw-gateway.service` to load changes. (This is separate from the
  no-restart rule for course *banks*, which ARE read fresh.)
- **Safe deploy recipe:** back up on VM → `scp` → confirm quiet (`find ~/.openclaw/students -name '*.json' -mmin -8 | wc -l` == 0) → restart `openclaw-gateway.service` → verify `is-active gateway wa-bridge`.
- **Services (all systemd `--user`):** `openclaw-gateway.service` (the brain, caches workspace/skills),
  `wa-bridge.service` (WhatsApp relay), `wa-dashboard.service` (read-only admin dash at :8790 — safe to
  restart anytime, never touches students), `wa-srs.timer` (daily recall cron), `acharya-tts.service`
  (:7870 — Azure neural TTS proxy for the web-chat 🔊 read-aloud; Caddy `/chat/tts*`→7870; source in
  `agentic_cohort/gurukul_tts/`; change voice via TTS_VOICE env; safe to restart — the old browser
  `speechSynthesis` is now just the fallback).
- **Version-controlled copy** of all these live files: `agentic_cohort/gurukul_workspace/` (edit repo → scp → restart).
- **Dhyan focus/deep-understanding upgrade SHIPPED 2026-07-18** (SOUL laws 7-8: prove-it + calibration;
  mastery gate needs explain+transfer; deep-work session; dashboard exposes `confidently_wrong`). Full
  context: [[project-dhyan-focus-agent]] · `DHYAN_AGENT_SPEC.md`.
- **Goal OS SHIPPED 2026-07-19** — the tutor now SETS + CONFIRMS + HOLDS each student's goal (Deepak's own
  discipline system, productized per-student). `SOUL.md` gained section "THE GOAL YOU HOLD (Goal OS)";
  `skills/gurukul-tutor/SKILL.md` gained the "🎯 GOAL OS" section (assisted articulation — Acharya *writes*
  the goal from course+`byoa_goal`+progress, student confirms; stores `goal`/`goal_deadline`/`goal_confirmed`;
  **retrofit rule** sets it ONCE for existing students who lack it; every session's focused step points at the
  locked goal). Deployed via the safe recipe (backup `.bak.20260719_132703` → scp → gateway restart). First
  live case = Kritansh (916396844362, agentic M3); opener sent via `gurukul_announce` template (he was outside
  the 24h window). ⚠️ Only FULLY-onboarded profiles (name/email) route to the tutor — bare test numbers hit
  the bridge course-request path, so smoke-test the tutor only with a real onboarded student. Brand/measurement
  context: `ACHARYA_BRAND_SOUL.md` (discipline = the category), `LEARNING_PROGRESS_MODEL.md` (power-mean p≈0.5
  real-progress metric). Full context: [[project-dhyan-focus-agent]].
- **Goal OS v2 — silent-student watcher + demo (2026-07-20)** — retrofit now a MANDATORY first-turn gate (goal
  set before any lesson resumes). New VM cron `~/goal_os_watch.py` (daily 04:30 UTC `--send`): re-engages
  `goal_confirmed` students who go silent (goal-anchored msg via `gurukul_announce` template) + writes teacher
  report `~/.openclaw/gurukul/slipping_report.json`. Gated on `goal_confirmed` (never messages ex-team/stray
  numbers). Demo: `demo_arjun/demo_neha/demo_rahul` profiles + **viewer page `gurukul.trigunai.com/demo-goalos`**
  (Caddy static, linked from `/demo`) for Rohan's field pitch. Full context: [[project-dhyan-focus-agent]].

**Gurukul Caddy routes + web-chat VOICE + demo pages (added 2026-07-18).** `gurukul.trigunai.com` is
Caddy (`/etc/caddy/Caddyfile`, the `gurukul.trigunai.com` block). It routes per-path with a **catch-all
`handle { reverse_proxy localhost:8788 }` = the bridge** (serves `/chat`, `/chat/api`, `/webhook`). To add
a page/endpoint: insert a `handle /<path> {…}` BEFORE that catch-all → `sudo caddy validate --config
/tmp/… --adapter caddyfile` → install → **graceful `sudo systemctl reload caddy`** (never a hard restart;
backups `Caddyfile.bak.*`). **Never touch the catch-all** or you break the bridge/chat.
- **Web-chat 🔊 read-aloud = Azure NEURAL TTS** (the old browser `speechSynthesis` was "cheap"; it's now
  just the fallback). Service `acharya-tts.service` (:7870, systemd --user, reads `AZURE_SPEECH_KEY` from
  `~/voicebot_wa/wa_voice.env`) → Azure Speech REST → audio/mpeg. Caddy `handle /chat/tts*`→7870.
  `chat.html` (`~/.openclaw/gurukul/chat.html`, **read fresh per request → scp = live, no restart**)
  `speak()` fetches `/chat/tts` + plays `Audio()`. **Change the voice** = `TTS_VOICE` env (`hi-IN-SwaraNeural`
  default · Ananya · Madhur · en-IN). Source + README: `agentic_cohort/gurukul_tts/`.
- **Patna field-DEMO pages** (Rohan): `/demo` (launcher, 4 subject tap-buttons), `/demo-guide` (full guide +
  what-to-test + real-student proof), `/demo-journey` (LIVE anonymized real-student proof, regenerated by
  `~/.openclaw/gurukul/gen_journey.mjs` from a real profile). All = Caddy static → `/var/www/gurukul-demo/
  {demo,guide,journey}.html`; edit repo `teacher_gtm/demo_launcher/` → scp to that dir → **live instantly**.
- **Demo course tenants** = 4 tutor concept banks (`neet-biology`/`jee-physics`/`class10-science-math`/
  `class12-board`; repo `agentic_cohort/gurukul_pipeline/courses/`, VM `~/.openclaw/gurukul/courses/`).
  Delivery = tokened `/chat?t=<token>` links (in `DEMO_PLAYBOOK.md`); demo profiles `web_demo-*@trigunai.com`
  pre-seeded past onboarding. Built via the `add-trigunai-course` skill. See [[project-rohan-field-caller]].

---

## 4.5 Acharya ASSESSMENT system (2026-07-22) — served by the bridge/Caddy on the Gurukul VM

**The pitch pivot:** Rohan sells Acharya as an **AI assessment engine** — *"you teach; Acharya tests &
tracks"* (non-threatening; doubt-solving is commoditised). Money move = **auto-detect weak students +
one-tap suggested test**. Full context + resume notes: [[project-acharya-assessment-system]].

**Live URLs (all `gurukul.trigunai.com`, behind Caddy → bridge `~/wa_bridge.mjs`):**
| URL | What | Repo file → VM path | Deploy |
|---|---|---|---|
| `/assess?subject=…` | adaptive test, EN/हिं, 5 subjects; diagnosis from real answers + adaptive depth; honest long-answer | `teacher_gtm/assessment_demo/assess.html` → `/var/www/gurukul-demo/` | scp (Caddy `handle /assess`) |
| `/demo` `/demo-guide` | Rohan launcher + guide (assessment-framed, killer-feature card) | `teacher_gtm/demo_launcher/{demo,guide}.html` → `/var/www/gurukul-demo/` | scp |
| `/dashboard` | teacher SWOT dashboard (class-at-a-glance + per-student SWOT + trend + "Do it" suggestion). **PREVIEW — not live-wired** | `teacher_gtm/assessment_demo/dashboard.html` → `/var/www/gurukul-demo/` | scp (Caddy `handle /dashboard`) |
| `/report?t=<token>` | STUDENT "Report & Improvement": **real SWOT from profile** + self-review test that updates mastery. LIVE for Kritansh. "📊 My Report" link in chat header | `agentic_cohort/gurukul_workspace/report.html` → `~/.openclaw/gurukul/report.html` | scp (bridge `GET /report`, reads fresh) |
| WhatsApp `quiz <subj>` | native tap-button MCQ/TF → score + weak-topics. To +91 91352 55107 | in `bridge.mjs` (`WA_QUIZ` bank) | bridge redeploy |

**Bridge endpoints added to `wa_bridge.mjs`** (repo `agentic_cohort/whatsapp_cloud_bridge/bridge.mjs` ==
live): `GET /report` (page), `GET /report/api?t=` (SWOT JSON), `POST /report/grade` (single-concept
mastery update — minimal, never downgrades a solid), plus the **WhatsApp quiz engine**
(`sendWhatsAppButtons` + `maybeHandleQuiz` + `WA_QUIZ`). Token = same `email|course|exp|hmac(CHAT_SECRET)`
as `/chat`; profile resolved via `loadIdentity()[email] || sanitizeEmail(email)`. ⚠️ Bridge edits need
a **quiet-window `systemctl --user restart wa-bridge`** (§4 no-disrupt rule); test writes on a THROWAWAY
token/number first (never Kritansh's live profile — back it up).

**Honest state (hold in the pitch):** dashboard is a populated PREVIEW (real product = pipe test →
per-student mastery → class dashboard); WhatsApp = 3-opt MCQ+TF only (button limit, rich widgets
web-only); question banks are curated demo sets. **Next want:** inline "assessment mode" INSIDE the web
chat (widgets rendered in `chat.html` via structured payloads — same marker pattern the bridge uses for
image-gen). To add a subject to `/assess`: edit `SUBJECTS`+`topicMap` in `assess.html`; to a WhatsApp
quiz: edit `WA_QUIZ` in `bridge.mjs`.

---

## 5. Cross-system bridge (shared `BRIDGE_KEY`)

`BRIDGE_KEY` (LMS container secret `bridge-key`) authenticates all server-to-server calls into the LMS.
**Active uses today:** the Gurukul VM bridge → LMS `/api/bridge/signup` + `/api/bridge/course-request`
(§2). **Dormant:** `learn.trigunai.com/admin` → `/api/bridge/stats` — learn.trigunai.com is RETIRED
(301→acharya), so that unified-stats view is gone; the `/api/bridge/stats` endpoint still exists but
nothing consumes it. **Track learners now on `acharya.trigunai.com/admin`** (§2). Detail in
[[project-lms-subscriptions]] / [[project-gurukul-vm]].

---

## 6. Safety rules (every change)

1. **Restore the default sub** (`cb656d95`) after touching the public sites or Gurukul sub.
2. **Bump image tags** — never reuse a tag. Roll-back = `containerapp update` to the previous tag.
3. **Don't disrupt live Gurukul students** (§4). Don't paywall/regress existing LMS students — the
   `grandfathered` status protects the cohort; keep it.
4. **Secrets stay server-side** (container secrets / VM env). Never bake a secret into a template/bundle or
   print it. Razorpay live key secret + app secret were once pasted in chat → rotate when convenient.
5. **Verify co-hosted sites** after a `triguai-frontend` deploy (it serves 3 domains from one image).
6. **Update the relevant memory** after a change so the next session inherits the new truth.

## 7. Where the deep context lives (read before editing)
[[project-acharya-landing]] (acharya domain + landing + brand + courses) · [[reference-acharya-brand]]
(dark-gold tokens) · [[project-lms-subscriptions]] · [[project-lms-lessons]] ·
[[project-course-site-shaderstudio]] · [[project-gurukul-vm]] (WhatsApp tutor: onboarding, signup,
requests, rate cap, switching) · [[feedback-gurukul-live-no-disrupt]] · the **`add-trigunai-course`** skill.
Offline marketing assets: `NvidiaSimSetup/acharya_pamphlet/` — A4 bilingual scan-to-WhatsApp pamphlets:
`pamphlet.html` (students) + `pamphlet_teacher.html` (teachers → reply **TEACHER**), source HTML + QR + PDFs
(rendered via headless Chrome `--print-to-pdf`). The repos also have their own `CLAUDE.md`.

## 8. Current state snapshot (2026-07-01) — live versions + what exists
- **lms = v63** · **triguai-frontend = v107** (bump from these). ⚠️ tag-reuse gotcha: a stale `lms:v62`
  already existed, so `--image lms:v62` did NOT roll a new revision — ALWAYS bump to a brand-new tag.
- **Landings REPOSITIONED to assessment-only (2026-07-22, lms:v63 + triguai-frontend:v107):** both
  `acharya.trigunai.com` (`acharya.html`) and `trigunai.com` (`ShaderStudio/landing/index.html`) now sell
  Acharya as an **AI assessment engine** ("you teach, Acharya tests & tracks") — tutor/Goal-OS LEAD removed,
  Skill-Development links kept. acharya.html has a 6-card feature grid + teacher-dashboard (labeled a live
  PREVIEW) + teacher/student benefits. Positioning source of truth for landings = the assessment reposition,
  not the old discipline/Goal-OS copy. See [[project-acharya-assessment-system]].
- **SEO / AI-SEO refreshed to the Goal-OS / discipline brand 2026-07-20** (lms:v61 `app/seo.py` + `acharya.html`
  head; triguai-frontend:v106 `landing/index.html` head): llms.txt now leads with "Acharya brings discipline
  to learning" + a "what makes Acharya different (guru, not a genie)" section (Goal OS · mastery gate ·
  silent-student catch); 3 new FAQ JSON-LD entries answer the AI-assistant queries ("different from ChatGPT?",
  "what is Goal OS?", "how does Acharya keep students disciplined?"); EducationalOrganization schema gained a
  brand description; page titles + meta + OG on both acharya.trigunai.com & trigunai.com carry the new hook.
  Retired `learn.trigunai.com` refs in seo.py/sameAs → `acharya.trigunai.com`.
- **Goal-OS / "discipline in learning" branding SHIPPED to all landings 2026-07-20** (soul = `ACHARYA_BRAND_SOUL.md`):
  acharya.trigunai.com (lms:v60) gained hero badge "guru, not a genie" + a new **"Every answer is free now — the
  discipline to actually learn isn't"** section (`#goalos`: Goal OS = holds each student's goal + one focused step/day
  + won't-let-them-fake-it trio); trigunai.com (triguai-frontend:v105) gained a hero discipline line + a Goal-OS line
  in the teacher band; Rohan's field demo pages (`/demo` + `/demo-guide`, `teacher_gtm/demo_launcher/` → scp to VM
  `/var/www/gurukul-demo/`, live instantly) gained a "Goal OS — bachche COMPLETE karte हैं" money-move + flagship
  feature. Honest framing throughout (describes behavior, no results promises — Goal OS is live but unproven). SEO note (lms:v50): `seo.py` `/pricing`
  uses schema.org **`Service`, NOT `Product`** (Product snippets demand `review`/`aggregateRating` we won't
  fabricate — 0 real reviews); teacher offering has its own `Service` JSON-LD + FAQ + `llms.txt` section.
- **acharya.trigunai.com = canonical** (lms.* + learn.* → 301 acharya). Homepage leads with Acharya.
- **10 courses** (added AI Product Management `ai-pm` + 6 interactive lessons). Rich detail in `course_details.py`.
- **Whole app = Acharya dark-gold brand**; `/login` is one-card-per-row with rich course detail + gold thumbnails.
- **Admin** at acharya.trigunai.com/admin (MRR/subs/funnel/analytics + 📚 Course-requests table).
- **Founder WhatsApp alerts** (signups/trials/payments/requests) via `notify.py` + `admin_alert` utility template.
- **WhatsApp tutor**: cold-inbound menu → email signup (→ LMS account) → custom requests → daily rate cap → course switching; English/हिंदी. Scan-QR + multilingual on both heroes.
- **Founding-Learner offer** (30 min/day × 7 days → 1 yr free) is MARKETING-ONLY across web + WhatsApp +
  pamphlet — ⚠️ no streak-tracking / auto-grant / DPDP consent built yet (the big open build).
- **Teacher/tutor-entrepreneur GTM (NEW, 2026-07-01)** — teachers reply "TEACHER" on WhatsApp OR use the
  "👨‍🏫 Are you a teacher?" form on `/login` (lms:v48, reuses public `POST /api/course-request`, no backend
  change) → both log `🎓 TEACHER ONBOARDING` (`course_requests` + admin alert) → onboarded OFFLINE (Stage 0; no teacher portal yet).
  **Both landings now carry a teacher section + hero teaser** (2026-07-01): acharya.trigunai.com `#teachers`
  (`templates/acharya.html`, lms:v49) + trigunai.com `#teachers` `.teach-band` (`ShaderStudio/landing/index.html`,
  triguai-frontend:v97) — scan card, "type TEACHER" steps, WhatsApp button (`wa.me/919135255107?text=TEACHER`) + web-form link (`/login#teacherbox`).
  Teacher pamphlet `acharya_pamphlet/pamphlet_teacher.html` (+PDF). Pricing plan: P1 (has students) ₹4,999/mo
  flat · P2 (aspiring grad) guided gate → rev-share. Next build (deferred until 1 teacher pays): `Teacher`
  table + `teacher_id` on `Student` + teacher dashboard (see a planned `TEACHER_PLATFORM_PLAN.md`).
  ⚠️ WABA billing flag "Business eligibility payment issue" seen 2026-07-01 — clear the payment method in
  Meta Business Manager before mass pamphlet distribution or teacher replies won't deliver.
