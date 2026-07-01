#!/usr/bin/env bash
# Flywheel refresh — pull de-identified real-data aggregate from the Gurukul VM and
# recalibrate the student simulator. Read-only on the VM; only aggregate stats (no
# names/transcripts) come back. Safe to run anytime; no Acharya disruption.
#
# Usage:  bash tutor_rl/calibration/refresh.sh
# Cron (weekly, propose — do NOT add without `crontab -l` review first):
#   0 6 * * 1  cd /path/to/NvidiaSimSetup && bash tutor_rl/calibration/refresh.sh >> /tmp/tutor_calib.log 2>&1
set -euo pipefail
KEY="$HOME/.ssh/gurukul_key"
VM="dk_trigun@20.219.2.53"
HERE="$(cd "$(dirname "$0")" && pwd)"

scp -i "$KEY" -o ConnectTimeout=12 -o BatchMode=yes "$HERE/aggregate_profiles.mjs" "$VM:/tmp/agg_profiles.mjs" >/dev/null
ssh -i "$KEY" -o ConnectTimeout=12 -o BatchMode=yes "$VM" 'node /tmp/agg_profiles.mjs' > "$HERE/real_aggregate.json"
echo "aggregate refreshed -> $HERE/real_aggregate.json"
python3 "$HERE/../calibrate.py"
