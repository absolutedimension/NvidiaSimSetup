# Operations Runbook — TrigunAI Gurukul

> How to run, change, and upgrade the system. All paths are on this box. PATH must include
> `$HOME/.npm-global/bin` for `openclaw` (login shells already do).

## File & service map
| What | Where |
|---|---|
| Tutor persona (Acharya) | `~/.openclaw/workspace/{IDENTITY,SOUL,USER}.md` |
| Tutor skill (sequence + mastery + concept bank + LMS links) | `~/.openclaw/workspace/skills/gurukul-tutor/SKILL.md` |
| Coding skill | `~/.openclaw/workspace/skills/trigun-ai-coding/SKILL.md` |
| Admin persona (Sutradhaar) | `~/.openclaw/admin-workspace/{IDENTITY,SOUL}.md` |
| Admin skill (ops) | `~/.openclaw/admin-workspace/skills/gurukul-admin/SKILL.md` |
| Machine-readable concept bank + LMS assessment links | `~/.openclaw/gurukul/concepts.json` |
| Per-student Learner Profiles (= the roster) | `~/.openclaw/students/<wa_id>.json` |
| WhatsApp bridge | `~/wa_bridge.mjs` |
| Pipeline scripts | `~/.openclaw/gurukul/{broadcast,srs_cron,add_student,gurukul_lib}.mjs` |
| WhatsApp/Meta + admin config | `~/.openclaw/wa_cloud.env` (SECRET — never print) |
| Docs (this set) | `~/.openclaw/docs/*.md` |

## Services (user systemd; survive reboot via linger)
```
systemctl --user status wa-bridge openclaw-gateway wa-srs.timer
systemctl --user restart wa-bridge            # after editing the bridge
systemctl --user restart openclaw-gateway     # after a model/config change
curl -s localhost:8788/health                 # bridge health (expect: ok)
openclaw daemon status                         # gateway health
journalctl --user -u wa-bridge -n 40 --no-pager        # bridge logs (inbound/reply/profile/admin)
systemctl --user list-timers wa-srs.timer --no-pager   # next SRS run
```

## Common operations
**Inspect a student**  ·  `cat ~/.openclaw/students/<wa_id>.json`
**List the roster**  ·  `ls ~/.openclaw/students/*.json | wc -l` (count) / `ls ~/.openclaw/students/`
**Add students to roster**  ·  `node ~/.openclaw/gurukul/add_student.mjs "Name:9198..." "9199..."`
**Broadcast (active students, free-form)**  ·  `node ~/.openclaw/gurukul/broadcast.mjs "your message"`
**Broadcast (everyone, needs approved template)**  ·  `node ~/.openclaw/gurukul/broadcast.mjs --template gurukul_announce --param "your message"`
**Run the SRS engine now (debug)**  ·  `node ~/.openclaw/gurukul/srs_cron.mjs`

**Add or edit a concept** (the curriculum):
1. Edit `~/.openclaw/gurukul/concepts.json` — add the key to `order` + `concepts` (recall + answer).
2. Mirror its hook/recall into `~/.openclaw/workspace/skills/gurukul-tutor/SKILL.md` (the bank table).
3. No restart needed (read live). Verify: `openclaw agent --session-key smoke --message "teach me <x>" --json`.

**Change how Acharya teaches** (tone / rules / sequence):
- Edit `gurukul-tutor/SKILL.md` or `workspace/SOUL.md` → hot-reloads. Smoke-test with a fresh `--session-key`.

**Change a module's LMS assessment link**:
- Edit the `assessments` map in `concepts.json` AND the MODULE CHECKPOINT table in `gurukul-tutor/SKILL.md`.

**Edit the bridge / pipeline code**:
- Back up first: `cp ~/wa_bridge.mjs ~/wa_bridge.mjs.bak`. Edit. `systemctl --user restart wa-bridge` + health check.
- Use the `trigun-ai-coding` skill (codex) for non-trivial changes.

**Add a new admin number** (route to Sutradhaar): append to `ADMIN_NUMBERS=` (comma-sep) in `wa_cloud.env`,
then `systemctl --user restart wa-bridge`.

**Test a model**  ·  `openclaw infer model run --model microsoft-foundry/gpt-5.5 --prompt "ping"`
**List skills loaded**  ·  `openclaw skills list`
**List agents**  ·  `openclaw agents list`

## Safety rules
- Verify every change (health check / load check / smoke message) before declaring done.
- Heads-up before anything destructive; back up the file first (`cp x x.bak`).
- Never run experiments against a real student's profile — use a scratch `--session-key` or throwaway wa_id.
- Never print secrets from `wa_cloud.env` or auth profiles.
- Minimal, focused changes — this is production with paying students.
