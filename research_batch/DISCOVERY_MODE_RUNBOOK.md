# Maya Discovery Mode — Runbook

Purpose: capture **real teacher pain quotes** (skill §5). Discovery Maya asks open questions and
LISTENS instead of pitching — which also fixes the "no teacher audio in transcripts" problem, because
the bridge only transcribes the caller while Maya is *silent*.

## What was deployed (2026-07-04, Gurukul VM `dk_trigun@20.219.2.53:~/voicebot_wa/`)
- `maya_discovery_prompt.txt` — the discovery script (plain text; edit questions here, no code change).
- `maya_rt_bridge.py` — additive gate: if `MAYA_MODE=discovery`, it loads the prompt above. Default =
  screener (unchanged). Backup: `maya_rt_bridge.py.bak.discovery.<ts>`.
- `start_discovery.sh` — starts the bridge in discovery mode on the same port 7863.

## Two-batch lead management (deployed 2026-07-04)
Two Maya batches share one lead file (`~/leads/all_leads.csv`) but must never collide:
- **Sales Maya** (`batch_planner.py` 10:45 IST → approve → `maya_scheduler.py` → `call_runner.py`) draws from the **FRONT**, diversified across all cities, 25/day, needs Telegram approval.
- **Discovery Maya** (this runbook, 1 PM IST) draws from the **END** via `call_runner.py --reverse`, Patna-only, 12/day, no approval.

**How collisions are prevented (two independent guarantees):**
1. **Ends split** — sales takes the front, discovery takes the tail (`--reverse`). They stay disjoint until the whole list is consumed from both ends (~weeks away). Verified: front-12 vs end-12 share **zero** numbers.
2. **Smart dedup** (`blocked_numbers()` in call_runner + `called()` in batch_planner): a number is skipped only if it was **ANSWERED** (we reached a human — never call again) **OR** already **called TODAY** (any status). So:
   - no-answer / busy on a **prior day → retriable** (they roll back into the pool).
   - anything called today by either batch → off-limits to both for the rest of the day.

Requires a `date` column in `call_results.csv` (migrated 2026-07-04; legacy rows dated empty = treated as prior-day → retriable). Backups: `call_runner.py.bak.leadmgmt.*`, `batch_planner.py.bak.leadmgmt.*`, `call_results.csv.pre_date.*`.

To change discovery's city/size/end-draw: edit the `--city Patna --segment NEET/JEE --limit 12 --reverse` line in `~/run_discovery_batch.sh`.

## Scheduled auto-run (deployed 2026-07-04)
- **Cron on the Gurukul VM:** `30 7 * * * /bin/bash /home/dk_trigun/run_discovery_batch.sh`
  → **07:30 UTC daily = 1:00 PM IST.** First fire: **2026-07-05 1 PM IST.**
- The wrapper `~/run_discovery_batch.sh` flips the bridge to discovery, dials **12 fresh Patna NEET/JEE
  subject-specialists**, then **always restores the screener bridge** (trap on exit, even on failure).
- Log: `~/voicebot_wa/discovery_cron.log`. Repo copy: `research_batch/run_discovery_batch.sh`.
- **Make it one-time only (run just tomorrow, then stop):** after tomorrow's run,
  `crontab -l | grep -v run_discovery_batch.sh | crontab -`.
- **Change city / batch size:** edit the `--city Patna --segment NEET/JEE --limit 12` line in the wrapper.

## Channel policy — PLIVO ONLY (2026-07-05)
Maya dials over **Plivo only**. The Twilio path was disabled after the OpenClaw agent tried to use it:
- `maya-twilio.service` — stopped, disabled, **masked** (unit moved to `*.DISABLED.*`).
- `maya_twilio.py` / `start_twilio.sh` — replaced with **guard stubs** (originals kept as `*.orig`).
- Policy note for the agent: `~/voicebot_wa/CALLING_CHANNEL.md` (+ copy in `~/.openclaw/workspace/`).
- The bridge `maya-realtime.service` (port 7863) and dialer `call_runner.py` both use Plivo (`api.plivo.com`).

## How mode-switching works (systemd-native — corrected 2026-07-05)
The realtime bridge is a **systemd service** (`maya-realtime.service`, `Restart=always`), NOT a loose
`nohup` process. Do **not** `pkill`/`nohup` it — systemd will fight you. Mode is controlled by an env file:
- `~/voicebot_wa/maya_mode.env` → `MAYA_MODE=` (screener, default) or `MAYA_MODE=discovery`.
- `start_realtime.sh` sources it; flipping = edit the file + `sudo systemctl restart maya-realtime.service`.
- The discovery wrapper does exactly this, and a `trap` restores `MAYA_MODE=` on exit. It also **skips the
  cycle** if the sales batch holds `~/leads/.runner.lock` (so sales callers never hit the survey bridge).

## Run a discovery batch manually
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
/bin/bash ~/run_discovery_batch.sh   # self-contained: flips to discovery, dials 12 from END, restores screener
```
(The older stop-screener/start-discovery/`nohup` recipe below is DEPRECATED — it conflicts with systemd.)

## (deprecated) Run a discovery batch manually (~15–20 calls)
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
# 1. stop the normal screener bridge (only one can bind :7863)
pkill -f "uvicorn maya_rt_bridge"
# 2. start Maya in discovery mode (runs in foreground; leave this shell open, or use nohup/tmux)
nohup ~/voicebot_wa/start_discovery.sh > ~/voicebot_wa/discovery_bridge.log 2>&1 &
sleep 2; grep -i "MODE=discovery" ~/voicebot_wa/discovery_bridge.log   # confirm it loaded
# 3. dial a small research batch (subject-specialist Patna/Kota converts best)
set -a; source ~/voicebot_wa/wa_voice.env; source ~/voicebot_wa/plivo.env; set +a
python3 ~/call_runner.py --city Patna --segment NEET/JEE --limit 18
```

## After the batch — REVERT to screener
```bash
pkill -f "uvicorn maya_rt_bridge"
nohup ~/voicebot_wa/start_realtime.sh > ~/voicebot_wa/bridge.log 2>&1 &
```

## Where the research lands
- Transcripts: `~/voicebot_wa/transcripts/<call_uuid>.txt` — teacher lines now appear as `USER:` (they
  didn't in screener mode). Each is also pushed to Telegram.
- Recordings (best source for Hindi pain quotes): Plivo console → Logs/Recordings, or
  `call_runner.py` fetches `recording_url` per call.

## Important caveats
- `call_runner.py` marks `interested` by scanning for the screener's close phrases. Discovery mode
  doesn't say those, so **every discovery call logs `interested=no`** — that is expected. Discovery's
  value is the *transcripts/recordings*, NOT the interest flag. Do **not** mix discovery rows into the
  screener conversion funnel.
- Keep the batch small (15–20). Then feed the quotes into `USER_RESEARCH_EDU.md §1` via the daily loop.
- To change the questions, just edit `maya_discovery_prompt.txt` — no restart-code needed (re-run picks
  it up on the next bridge start).
