# pulse_dashboard — Acharya funnel live admin dashboard

Read-only, auto-refreshing browser dashboard for the Acharya exam-prep funnel. Hosted on the
**Gurukul VM**, fed by the LMS `/admin/api/pulse` endpoint. Owned + maintained by the
`trigunai-campaign-tracker` skill (see its `SKILL.md §5` for the full maintain/evolve recipe).

## What's here
- `server.py` — tiny stdlib HTTP proxy. Holds the LMS pulse key **server-side**; serves the page +
  a JSON proxy, gated by a token in the URL (`?t=<DASH_TOKEN>`). Runs on VM port 7871.
- `dashboard.html` — the live page (inline CSS/JS, auto-refresh every 30s, token read from its own URL).
- `pulse_dash.env` — **VM-only, not committed.** `LMS_PULSE_URL`, `LMS_PULSE_KEY`, `DASH_TOKEN`, `PORT`.

## Live URL
`https://gurukul.trigunai.com/admin-pulse?t=<DASH_TOKEN>` — treat like a password.

## Architecture
```
browser ──(?t=DASH_TOKEN)──▶ Caddy handle /admin-pulse* ──▶ localhost:7871 (server.py)
                                                                  │ holds LMS key server-side
                                                                  ▼
                                          https://acharya.trigunai.com/admin/api/pulse?key=PULSE_KEY
                                                                  │ (lms/app/analytics.py:pulse())
                                                                  ▼  JSON: exam_prep + course_cohort + web + recent_signups
```
The **CLI** (`trigunai-campaign-tracker/scripts/pulse.py`) and **this page** read the SAME payload —
one source of truth, two faces.

## Deploy / update (from the Mac)
```bash
PEM=~/.ssh/gurukul_key; VM=dk_trigun@20.219.2.53
scp -i $PEM server.py dashboard.html $VM:~/pulse_dashboard/
ssh -i $PEM $VM 'systemctl --user restart pulse-dashboard.service'   # only needed for server.py; html is read fresh
```
- systemd `--user` unit: `pulse-dashboard.service` (safe to restart anytime — NOT student-facing).
- ⚠️ Never restart `wa-bridge` / `openclaw-gateway` (live students).
- Caddy route `handle /admin-pulse*` sits BEFORE `handle /admin*`; changes → `sudo caddy validate` →
  `sudo systemctl reload caddy` (graceful).

## Rotate the access token
Edit `DASH_TOKEN` in the VM's `~/pulse_dashboard/pulse_dash.env` → restart the service → update the
skill's `~/.claude/skills/trigunai-campaign-tracker/.dash_token` + `DASHBOARD_URL.txt`.
