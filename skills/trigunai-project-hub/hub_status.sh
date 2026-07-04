#!/usr/bin/env bash
# hub_status.sh — one-screen live health board for ALL TrigunAI systems.
# Owned by the trigunai-project-hub control-tower skill (§C).
# Runs read-only checks: live sites, Gurukul VM (Acharya bridge + Maya), OpenClaw engines.
# Usage: bash hub_status.sh        (nothing to install; needs the two SSH keys)

set -uo pipefail
GK_KEY="$HOME/.ssh/gurukul_key";  GK="dk_trigun@20.219.2.53"
OC_KEY="$HOME/Downloads/hearmenow-agentic-system_key.pem"; OC="hearmenow-agentic-system@20.120.226.5"
SSH="ssh -o ConnectTimeout=12 -o StrictHostKeyChecking=no -o BatchMode=yes"
OK="✅"; BAD="❌"; WARN="⚠️ "; DASH="—"

hr(){ printf '%s\n' "────────────────────────────────────────────────────────"; }
row(){ printf '  %-3s %-26s %s\n' "$1" "$2" "$3"; }

# HTTP check → prints mark + code.
# want="200" → must equal 200. want="up" → any app response is OK; only 000/5xx = down
# (used for endpoints like /webhook that answer 403 when healthy).
http(){ local url="$1" want="${2:-200}" code
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$url" 2>/dev/null)
  if [ "$want" = up ]; then
    if [ "$code" = 000 ] || [ "${code:0:1}" = 5 ]; then echo "$BAD|$code"; else echo "$OK|$code up"; fi
  else
    if [ "$code" = "$want" ]; then echo "$OK|$code"; elif [ "$code" = 000 ]; then echo "$BAD|no-response"; else echo "$WARN|$code"; fi
  fi; }

echo; echo "  TrigunAI — SYSTEM STATUS BOARD   ($(date '+%Y-%m-%d %H:%M %Z'))"; hr

# ── 1. Live sites ──────────────────────────────────────────
echo "  LIVE SITES"
for pair in \
  "acharya.trigunai.com|https://acharya.trigunai.com/healthz|200" \
  "trigunai.com (home)|https://trigunai.com/|200" \
  "studio.trigunai.com|https://studio.trigunai.com/api/health|200" \
  "lms.trigunai.com|https://lms.trigunai.com/healthz|200" \
  "gurukul bridge (/webhook)|https://gurukul.trigunai.com/webhook|up" ; do
  IFS='|' read -r label url want <<< "$pair"
  r=$(http "$url" "$want"); row "${r%%|*}" "$label" "${r##*|}"
done
hr

# ── 2. Gurukul VM (Central India): Acharya bridge + Maya ────
echo "  GURUKUL VM  20.219.2.53  (Central India)"
if $SSH -i "$GK_KEY" "$GK" true 2>/dev/null; then
  GKOUT=$($SSH -i "$GK_KEY" "$GK" '
    echo "ACHARYA=$(curl -s -o /dev/null -m4 -w %{http_code} http://127.0.0.1:8788/ 2>/dev/null)"
    echo "MAYA=$(systemctl is-active maya-realtime 2>/dev/null)"
    echo "SCHED=$(systemctl is-active maya-scheduler 2>/dev/null)"
  ' 2>/dev/null)
  ach=$(sed -n 's/^ACHARYA=//p' <<<"$GKOUT"); maya=$(sed -n 's/^MAYA=//p' <<<"$GKOUT"); sched=$(sed -n 's/^SCHED=//p' <<<"$GKOUT")
  { [ -n "$ach" ] && [ "$ach" != 000 ]; } && row "$OK" "Acharya app (:8788)" "listening ($ach)" || row "$BAD" "Acharya app (:8788)" "${ach:-down}"
  [ "$maya" = active ] && row "$OK" "Maya realtime (systemd)" "$maya" || row "$WARN" "Maya realtime (systemd)" "${maya:-?}"
  [ "$sched" = active ] && row "$OK" "Maya scheduler (systemd)" "$sched" || row "$DASH" "Maya scheduler (systemd)" "${sched:-inactive}"
else
  row "$BAD" "SSH" "unreachable"
fi
hr

# ── 3. OpenClaw box (westus2): content + teacher engines ────
echo "  OPENCLAW BOX  20.120.226.5  (westus2)"
if $SSH -i "$OC_KEY" "$OC" true 2>/dev/null; then
  OCOUT=$($SSH -i "$OC_KEY" "$OC" '
    echo "PDAILY=$([ -f ~/.openclaw/PAUSE_DAILY ] && echo PAUSED || echo running)"
    echo "PTEACH=$([ -f ~/.openclaw/PAUSE_TEACHER ] && echo PAUSED || echo running)"
    echo "CRON=$(openclaw cron list 2>/dev/null | grep -ciE "daily-content-engine|teacher-morning|teacher-evening")"
    echo "LASTLOG=$(tail -1 ~/.openclaw/content_log.md 2>/dev/null | cut -c1-60)"
  ' 2>/dev/null)
  pd=$(sed -n 's/^PDAILY=//p' <<<"$OCOUT"); pt=$(sed -n 's/^PTEACH=//p' <<<"$OCOUT")
  cron=$(sed -n 's/^CRON=//p' <<<"$OCOUT"); last=$(sed -n 's/^LASTLOG=//p' <<<"$OCOUT")
  [ "$pd" = running ] && row "$OK" "Content engine" "$pd" || row "$WARN" "Content engine" "${pd:-?}"
  [ "$pt" = running ] && row "$OK" "Teacher engine" "$pt" || row "$WARN" "Teacher engine" "${pt:-?}"
  [ "${cron:-0}" -ge 3 ] 2>/dev/null && row "$OK" "Cron jobs registered" "$cron/3" || row "$WARN" "Cron jobs registered" "${cron:-0}/3"
  [ -n "$last" ] && row "$DASH" "Last content log" "$last"
else
  row "$BAD" "SSH" "unreachable"
fi
hr
echo "  Legend: $OK ok   $WARN check   $BAD down   $DASH info"; echo