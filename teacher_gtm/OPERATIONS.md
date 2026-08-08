# Teacher Onboarding — Operations (canonical, read by both Deepak AND the field rep's Claude sessions)

**Owner responsibilities:**
- **The field rep** (via maya-caller skill in Claude Desktop): source leads · run Maya calls · listen +
  qualify · call hot leads directly · **approve + fire onboarding batches** · fix `needs_name` teachers.
- **Deepak** (via any Claude session): final `acharya-technology-transfer` for teachers at
  `stage=provisioning` · edit templates / bot / bridge / Caddy · debug systemd services.

## The daily rhythm (both callers use this)

```
morning:                     evening:
  1. --list                     4. --list (again — see who moved)
  2. fix any needs_name         5. any provisioning → tell Deepak
  3. --send-batch on queued     6. log calls in caller_log.csv
```

## Commands both can run (SSH as dk_trigun)

| Purpose | Command |
|---|---|
| See pipeline state | `python3 ~/teacher_gtm/onboarding_bot.py --list` |
| Send today's approved batch | `python3 ~/teacher_gtm/onboarding_bot.py --send-batch` |
| Sync fresh interested=yes from CSV into queue (usually automatic every 15min) | `python3 ~/teacher_gtm/onboarding_bot.py --sync` |
| One-off template to a queued phone | `curl -sS -X POST http://127.0.0.1:7865/send_template/<phone>` |
| Bot health check | `curl -sS http://127.0.0.1:7865/status \| python3 -m json.tool` |
| Watch delivery/read receipts live | `journalctl --user -u wa-bridge -f \| grep -E "917[0-9]+"` |
| Event log for one teacher | `grep "<phone>" ~/teacher_gtm/onboarding_events.jsonl` |

## Commands ONLY Deepak runs

| Purpose | Command |
|---|---|
| Mark a teacher LIVE (after acharya-technology-transfer finishes) | `curl -X POST http://127.0.0.1:7865/mark_provisioned -H "Content-Type: application/json" -d '{"wa_number":"<phone>","tenant_url":"<url>"}'` |
| Restart bot | `systemctl --user restart teacher-onboarding-bot` |
| Restart bridge (CAREFUL — live students) | `systemctl --user restart wa-bridge` |
| Reload Caddy | `sudo systemctl reload caddy` |

## The stages (single source of truth)

`queued` → `template_sent` → `template_delivered` → `template_read` → `started` →
`collecting_details` → `web_upload_pending` → `provisioning` → `live`

Off-happy-path: `needs_name` (fix + re-queue), `failed` (Meta block — tell Deepak), `opted_out` (STOP).

## Key files on this VM

| Path | What |
|---|---|
| `~/teacher_gtm/onboarding_queue.json` | Single source of truth for who's in the pipeline |
| `~/teacher_gtm/onboarding_bot.py` | The state machine + CLI |
| `~/teacher_gtm/onboard_standalone.html` | Web form served at gurukul.trigunai.com/onboard/{token} |
| `~/teacher_gtm/onboarding_events.jsonl` | Append-only event log |
| `~/leads/call_results.csv` | Maya's call outcomes — the `interested=yes` → auto-sync source |
| `~/wa_bridge.mjs` | WhatsApp Cloud API bridge (patched to route teacher numbers to bot) |
| `~/.config/systemd/user/teacher-onboarding-bot.service` | Bot systemd unit |
| `~/.config/systemd/user/sync-onboarding-queue.timer` | Every-15-min sync |
| `/etc/caddy/Caddyfile` | Public routing (/onboard, /lookup_token, /onboard_submit → bot) |

## DO NOT
- Add a teacher to `~/.openclaw/students/` — that folder is LIVE students, triggers daily marketing
  templates, will get their number Meta-blocked. Teachers belong ONLY in the onboarding_queue.json.
- Restart wa-bridge without confirming with Deepak — it also serves the live Acharya student tutor.
- Retry a `failed` teacher — Meta blocks are engagement-score-based and last days.

Last updated: 2026-07-08 by Deepak's Claude session — the day the pipeline shipped end-to-end.
