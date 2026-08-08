---
name: trigunai-campaign-tracker
description: >-
  Deepak's daily command center for the Acharya growth engine — one glance at who is joining,
  from where, whether they activate, and whether anyone is PAYING, across EVERY source (Google
  Ads, LinkedIn, WhatsApp, manual, direct), plus the Google Ads campaign parameters. It pulls the
  live signup/login truth from the LMS (`/admin/api/pulse`, read-only) and folds in the manually-read
  Google Ads numbers, then prints a single scoreboard AND tells Deepak the few metrics that actually
  matter at THIS stage (cold start, 0 paid) — not vanity reach. USE WHEN Deepak wants to check the
  campaign, see who signed up / logged in, check funnel/traffic, ask "is anyone joining / paying",
  "how are the ads doing", "who registered today", "what's happening with Acharya", "check my numbers",
  "growth", "conversions", "did the LinkedIn post work", "campaign status", "pulse", "/pulse",
  "/campaign", "dashboard", "how many signups". ALSO hosts + MAINTAINS a live auto-refreshing browser
  dashboard on the Gurukul VM (gurukul.trigunai.com/admin-pulse) — and it is this skill's standing job to
  keep that dashboard in sync whenever a metric / price / track / funnel step is ADDED or REMOVED (change
  the LMS pulse() producer + the web + CLI faces together; never let it show a stale or killed number).
  Companion to content-daily-engine (makes the content), maintain-trigunai-system (owns the LMS the pulse
  endpoint lives in), and trigunai-daily-discipline (Block 1 marketing). This skill OWNS reading the
  scoreboard, keeping the live dashboard truthful, + deciding what to fix next.
---

# TrigunAI — Campaign & Funnel Command Center

> **Job:** in 30 seconds, answer four questions honestly — **who is joining, from where, are they
> activating, and is anyone paying?** — across every acquisition source, and name the ONE thing to
> fix next. It is the *reading* half of growth; `content-daily-engine` is the *making* half.
>
> **The one law (from the CEO OS):** reach is vanity, **signups → activation → paid is the game.**
> Impressions and clicks feel good and pay nothing. This skill always leads with the gate number
> (paid), never with the pretty number (views).

---

## 0. THE 30-SECOND RUN

```bash
python3 ~/.claude/skills/trigunai-campaign-tracker/scripts/pulse.py
```

That's it. It fetches the live funnel truth + your saved Google Ads numbers and prints the
scoreboard with a **"WHAT TO WATCH NOW"** verdict at the bottom. Run it whenever Deepak asks
about signups / ads / conversions / "who joined" / "is it working."

- Update the Google Ads numbers first (they're manual — see §3): edit `ads.json`, then run.
- `--raw` dumps the JSON · `--file x.json` formats a saved payload offline.

### The hosted LIVE dashboard (browser, auto-refreshing)
Same data, as a live web page — open on any device, refreshes itself every 30s:

```
https://gurukul.trigunai.com/admin-pulse?t=<DASH_TOKEN>
```
The full URL (with token) is saved locally at `~/.claude/skills/trigunai-campaign-tracker/DASHBOARD_URL.txt`
(git-ignored). **Treat the link like a password** — the token is the only gate. It shows THE GATE, who's
joining (exam-prep scoped), traffic sources, recent signups, and the live verdict.

- **Hosting:** a tiny read-only proxy on the **Gurukul VM** (`~/pulse_dashboard/server.py`, systemd
  `--user` service `pulse-dashboard.service`, port 7871) behind Caddy `handle /admin-pulse*`. The proxy
  holds the LMS pulse key **server-side** — the browser only ever sees the `DASH_TOKEN`, never the LMS key.
- **The CLI (`pulse.py`) and the web dashboard read the SAME `/admin/api/pulse` payload** — so they never
  disagree. That's the design: one source of truth, two faces (terminal + browser).

---

## 1. WHAT TO TRACK **RIGHT NOW** (stage: cold start, 0 paid, ~₹350/day ad + 1 LinkedIn post)

You are at the very bottom of the funnel's life — the campaign just went live and no one has paid.
At this stage **most metrics are noise.** Track this short list, in this order. Each row is a
question; the metric is only there to answer it.

| # | The question that matters | Metric to read | Healthy signal (this week) |
|---|---|---|---|
| **1** | Is anyone **paying**? (the gate) | `assess_active` (₹249 paid) | Even **1** ends the "0 paid" era. That's the week's win. |
| **2** | Does a **click become a signup**? | 7d signups vs ad clicks + LinkedIn | Any signups attributable to the push at all |
| **3** | What does a signup **cost**? | spend ÷ 7d signups (`~Cost/signup`) | < ₹150/signup is fine to start; > ₹400 = fix funnel or keywords |
| **4** | Do signups **activate** (take a test)? | `with_topics` vs total signups | Most signups should take ≥1 test. If not, the leak is *after* signup. |
| **5** | **Which source** converts? | `top_refs` + the recent-signup feed | Find the channel that produces real signups → double down |
| **6** | Are **teachers/institutes** biting? (B2B) | `teachers`, `institutes` | Any teacher signup is a strong B2B signal — follow up personally |

**Deliberately IGNORE for now** (they'll matter later, not this week): impressions, CTR, followers,
page-view totals, "ad strength," optimization score, MRR projections. They move before the gate does
and tempt you into vanity. If the scoreboard tempts Deepak toward a pretty number, name it and pull
him back to rows 1–4.

> **The single sentence to repeat this week:** *"Clicks are not the score. The score is: did a click
> become a signup, and did a signup become ₹249?"*

---

## 2. THE FUNNEL (what each stage is, and where it leaks)

```
   IMPRESSION → CLICK → LANDING (/exam-prep) → SIGNUP/LOGIN → TOOK A TEST → ₹249 PAID
     (Ads)      (Ads)     (web pv/uv)         (new_24h/7d)   (with_topics)  (assess_active)
        └─ vanity ─┘         └──────────── this is where the money is ────────────┘
```

Diagnose by finding the **biggest drop** between two adjacent stages — that's the one thing to fix:

| Drop between… | Means | Fix (owner skill) |
|---|---|---|
| Click → Landing | ad clicks but no matching page views | tracking/redirect broken, or slow page → `maintain-trigunai-system` |
| Landing → Signup | people arrive, don't sign up | the page doesn't deliver the ad's promise ("start free") → walk it as a cold visitor, fix the CTA |
| Signup → Test | they sign up, never practice | activation leak — push straight into a test on first login → `acharya-student-frontend` |
| Test → Paid | they use it free, don't pay | the ₹249 ask / value moment is wrong → pricing & upgrade flow |

**The rule:** never fix a stage that isn't the biggest leak. One fix per read.

---

## 3. DATA SOURCES (what's live vs manual)

| Source | How it's read | Live? |
|---|---|---|
| **Signups / logins / activation / paid / teachers / traffic source** | `GET /admin/api/pulse?key=…` on the LMS (read-only, key-gated). Aggregated by `app/analytics.py:pulse()`. Tracks **every** source. | ✅ live once deployed (§5) |
| **Google Ads** (spend, impressions, clicks, CPC) | **Manual** — read the Ads dashboard, write into `ads.json`. The Ads API needs an OAuth setup we haven't done. | ⚠ manual |

**Source attribution note:** the funnel captures the HTTP referrer (`top_refs`) — so LinkedIn/WhatsApp/
organic clicks are attributed automatically. **Google Ads clicks often land with no referrer**, so
attribute those by correlating a signup *spike* with ad *clicks* on the same day, and by watching the
`patna-students` geography (Patna signups ≈ the ad). When you want clean per-source numbers, add UTM
tags to each link (e.g. `?utm_source=linkedin`, `?utm_source=googleads`) — then `top_refs`/landing
paths separate them cleanly. That's the next upgrade.

### Updating Google Ads numbers (10 seconds)
Read these off the Ads dashboard and put them in `~/.claude/skills/trigunai-campaign-tracker/ads.json`:
```json
{ "campaign": "patna-students", "spend": 210, "impressions": 1840, "clicks": 47, "avg_cpc": 3.15 }
```

---

## 4. HOW TO READ THE SCOREBOARD (the coaching layer)

When you print the pulse for Deepak, don't just show numbers — **interpret** them against §1:

1. **Lead with THE GATE.** If `assess_active = 0`, say so plainly: "still 0 paid." If ≥1, that's the
   headline — celebrate it and immediately ask *which source produced it.*
2. **Then acquisition + source.** "N signed up in 7d, mostly from <source>." If 0, the push isn't
   converting yet — that's the whole story, don't bury it.
3. **Then the biggest leak** (§2) and the ONE fix. Route it to the owning skill.
4. **Then the honesty check.** If ad clicks are climbing but signups are flat, say: *"we're buying
   clicks, not students — fix the funnel before adding budget."* Never let rising spend read as progress.
5. **Log it.** A meaningful read (esp. the first signup, first paid, or a funnel fix) is a
   `trigunai-daily-discipline` Block-1 artifact — note it in `daily_routine/ROUTINE_LOG.md` / `CONTENT_LOG.md`.

**Decision rules the verdict encodes:**
- Clicks ≥ 20 and 0 signups → **stop tuning the ad; fix the landing page.**
- Signups > 0 but 0 activation → **push signups straight into a test.**
- Trials > 0, paid 0 → **watch the trial→paid step; the ₹249 moment needs work.**
- Cost/signup > ₹400 → **cut the worst keywords** (the ones with clicks and no conversions) before raising budget.
- First paid appears → **find its source/keyword and pour budget there; cut the rest.**

---

## 5. MAINTAIN & EVOLVE THE DASHBOARD (this skill's STANDING JOB)

> **The dashboard is not a one-off — it must stay true as the product changes.** When a new track,
> price, metric, or funnel step is ADDED or REMOVED, or a report should surface something new, this
> skill's job is to reflect it everywhere. A stale dashboard that shows a metric we killed (or hides
> one we added) is worse than no dashboard — it lies. Keep it honest.

### 5.1 The three layers — change them TOGETHER (the contract)
There is ONE source of truth (`pulse()`), rendered in two faces. A new/removed field must move through all three:

| Layer | File | Role | Deploy to make it live |
|---|---|---|---|
| **1. Producer** | `lms/app/analytics.py :: pulse()` | computes every number (the payload) | **LMS deploy** (§5.3) |
| **2. Web face** | `agentic_cohort/pulse_dashboard/dashboard.html` | renders the payload in the browser | **VM push** (§5.4) — instant |
| **3. CLI face** | `~/.claude/skills/trigunai-campaign-tracker/scripts/pulse.py` | renders the payload in the terminal | none — local file |

**Rule:** if you add a key to `pulse()`, add it to BOTH faces. If you remove a metric, remove it from
both faces (don't leave a dead card). If a face reads a key the producer no longer sends, it must
degrade gracefully (`.get(key, default)`), never crash.

### 5.2 Recipes for the common changes
- **Add a metric** (e.g. "tests taken today", "trial→paid rate"): compute it in `pulse()` → add a card in
  `dashboard.html` (`cards[]` array or a new section) → add a `bar(...)` line in `pulse.py :: render()`
  → deploy LMS (§5.3) + push VM (§5.4).
- **Add a new track / product** (e.g. a new paid tier, a new exam vertical): decide if it belongs to the
  exam-prep scope or is separate (like the course cohort) — update the `is_exam_prep()` classifier and the
  `exam_prep` / `course_cohort` split in `pulse()` accordingly, then surface it in both faces.
- **Remove something** (a killed feature/price): delete its computation in `pulse()` and its render in both
  faces. Update the price/label strings (there are ₹ labels in all three layers — grep and change together).
- **Change a price** (like ₹199→₹249): grep `₹` across `analytics.py`, `dashboard.html`, `pulse.py`, and
  the SKILL — change all at once so nothing shows a stale number.
- **Change what "who's joining" means** (attribution/source): the funnel captures HTTP referrer in
  `web.top_refs`; for clean per-source splits, add UTM tags to links and read landing-path/`utm_source` in `pulse()`.

### 5.3 Deploy the LMS producer (via `maintain-trigunai-system`)
```bash
cd ~/Documents/01_Active/NvidiaSimSetup/lms
python3 -m py_compile app/analytics.py app/main.py        # test first
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .   # bump N (last: v128)
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
for i in $(seq 1 20); do curl -sf https://acharya.trigunai.com/healthz && break || sleep 8; done
# verify the new field is live:
curl -s "https://acharya.trigunai.com/admin/api/pulse?key=$(cat ~/.claude/skills/trigunai-campaign-tracker/.pulse_key)" | python3 -m json.tool | head
```
- Endpoint: `GET /admin/api/pulse?key=…` (route in `lms/app/main.py`), key = `config.py:PULSE_KEY`.
- **Key** = Azure container secret `pulsekey` (env `PULSE_KEY=secretref:pulsekey`). Rotate via
  `az containerapp secret set … --secrets pulsekey=<new>` + restart; then update the skill's `.pulse_key`
  and the VM's `~/pulse_dashboard/pulse_dash.env`.
- **Security:** read-only, returns only aggregates + masked emails (`de***@dom`). Never commit the real key.
- After deploy: **restore the default Azure sub** (`az account set --subscription cb656d95-2f68-469f-b2b5-aee1ac1be625`) — the LMS is already in it, but keep the habit.

### 5.4 Push the VM web dashboard (no restart of anything student-facing)
```bash
PEM=~/.ssh/gurukul_key; VM=dk_trigun@20.219.2.53
scp -i $PEM ~/Documents/01_Active/NvidiaSimSetup/agentic_cohort/pulse_dashboard/{server.py,dashboard.html} $VM:~/pulse_dashboard/
ssh -i $PEM $VM 'systemctl --user restart pulse-dashboard.service && sleep 1 && systemctl --user is-active pulse-dashboard.service'
curl -s -o /dev/null -w '%{http_code}\n' "https://gurukul.trigunai.com/admin-pulse?t=$(cat ~/.claude/skills/trigunai-campaign-tracker/.dash_token)"
```
- `dashboard.html` is read fresh by the browser → an `.html`-only change is live on next page refresh
  (restart only needed if you change `server.py`).
- ⚠️ **NEVER restart `wa-bridge` / `openclaw-gateway`** (live students) — `pulse-dashboard.service` is a
  separate `--user` unit, safe to restart anytime; it touches nothing student-facing.
- **Caddy**: route is `handle /admin-pulse*` (before `handle /admin*`) in `/etc/caddy/Caddyfile`. If you
  ever re-add it: backup → insert before `/admin*` → `sudo caddy validate` → **`sudo systemctl reload caddy`**
  (graceful, never restart) → verify `/admin` (8790) + `/chat` (8788) still 200.

### 5.5 Health checks
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 'systemctl --user is-active pulse-dashboard.service; curl -s localhost:7871/admin-pulse/health'
```
If the page shows a red dot / "upstream" error: the LMS pulse endpoint is down or the key rotated —
re-sync `pulse_dash.env` on the VM with the current `PULSE_KEY`.

---

## 6. WIRING (where this sits)

```
trigunai-campaign-tracker  (READ: who's joining, from where, are they paying — + what to fix)
   │  pulls
   ├─ LMS /admin/api/pulse        ← app/analytics.py:pulse()   (maintain-trigunai-system owns deploy)
   ├─ ads.json                    ← manual Google Ads numbers
   │  feeds back into
   ├─ content-daily-engine        → make the next asset for the source that converts
   ├─ acharya-student-frontend    → fix the funnel stage that leaks
   └─ trigunai-daily-discipline   → log the read as a Block-1 artifact
```

Companion, not overlap: `content-daily-engine` MAKES marketing; this skill READS whether it worked
and says what to change. `maintain-trigunai-system` owns the LMS + the deploy of the pulse endpoint.

---

*Built 2026-07-28 — the day the Patna student campaign + first LinkedIn post went live at 0 paid.
The whole point: never again build/spend for six days without looking at whether anyone joined.
Owner: Deepak. One law: signups → activation → paid, not reach.*
