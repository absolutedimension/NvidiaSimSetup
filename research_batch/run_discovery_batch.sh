#!/bin/bash
# ============================================================================
# Maya DISCOVERY batch (scheduled, systemd-native) — flip the systemd-managed
# realtime bridge (maya-realtime.service, port 7863) into discovery mode via an
# env file, dial a small batch of FRESH *END-of-list* Patna NEET/JEE teachers
# (--reverse, so it never overlaps the front-loaded sales batch), then ALWAYS
# restore screener mode — even if dialing fails.
# Scheduled via cron at 07:30 UTC = 1:00 PM IST. Log: ~/voicebot_wa/discovery_cron.log
# ============================================================================
set -u
export PATH=/usr/local/bin:/usr/bin:/bin
LOG="$HOME/voicebot_wa/discovery_cron.log"
exec >> "$LOG" 2>&1
echo "===== $(date -u +%FT%TZ) | $(TZ=Asia/Kolkata date +%H:%M) IST | discovery START ====="
MODEENV="$HOME/voicebot_wa/maya_mode.env"
LOCK="$HOME/leads/.runner.lock"

# 0. Never run while the SALES batch (or any call_runner) is dialing — flipping the shared
#    bridge to discovery mid-sales would give sales callers the survey. The lock serialises them.
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "$(date -u +%FT%TZ) another call batch is active (lock held) — skipping discovery this cycle"
  exit 0
fi

restore_screener() {
  echo "$(date -u +%FT%TZ) restoring SCREENER mode..."
  echo "MAYA_MODE=" > "$MODEENV"
  sudo -n systemctl restart maya-realtime.service
  sleep 3
  echo "$(date -u +%FT%TZ) screener restored (maya-realtime: $(systemctl is-active maya-realtime.service))"
}
trap restore_screener EXIT

echo "$(date -u +%FT%TZ) flipping realtime bridge -> discovery (via $MODEENV)"
echo "MAYA_MODE=discovery" > "$MODEENV"
sudo -n systemctl restart maya-realtime.service
# wait until the bridge is healthy again
for i in $(seq 1 20); do sleep 2; curl -sf localhost:7863/realtime-health >/dev/null 2>&1 && break; done
if journalctl -u maya-realtime.service --since "60 sec ago" 2>/dev/null | grep -q "MODE=discovery"; then
  echo "$(date -u +%FT%TZ) discovery mode confirmed"
else
  echo "$(date -u +%FT%TZ) WARN: discovery banner not seen in journal (continuing; env is set)"
fi

set -a; source "$HOME/voicebot_wa/wa_voice.env"; source "$HOME/voicebot_wa/plivo.env"; set +a
echo "$(date -u +%FT%TZ) dialing Patna NEET/JEE from END of list, limit 12 ..."
python3 "$HOME/call_runner.py" --city Patna --segment NEET/JEE --limit 12 --reverse
echo "$(date -u +%FT%TZ) dialing DONE (rc=$?)"
# trap restore_screener runs on EXIT
