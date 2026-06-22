#!/usr/bin/env bash
# send_brief.sh "<subject>" <body-file>
# Emails Deepak's daily accountability brief to deepak@trigunai.com via Azure Communication
# Services, reusing marketing/publish.py. Loads ACS creds from marketing/.env (gitignored).
#
# Exit codes:
#   0  = sent
#   3  = NO_ACS (creds missing) -> caller should fall back to a Gmail draft + push
#   other = publish.py error
set -uo pipefail
cd "$(dirname "$0")/.."   # repo root

SUBJECT="${1:?usage: send_brief.sh \"<subject>\" <body-file>}"
BODY="${2:?usage: send_brief.sh \"<subject>\" <body-file>}"
TO="${BRIEF_TO:-deepak@trigunai.com}"

# load ACS creds (never committed)
set -a; [ -f marketing/.env ] && . marketing/.env; set +a

if { [ -z "${ACS_CONNECTION_STRING:-}" ] && [ -z "${ACS_ENDPOINT:-}" ]; } || [ -z "${ACS_SENDER:-}" ]; then
  echo "NO_ACS: ACS creds not found in marketing/.env (need ACS_CONNECTION_STRING + ACS_SENDER)."
  echo "        Falling back to draft. To enable real email: see daily_routine/EMAIL_SETUP.md"
  exit 3
fi

python3 marketing/publish.py email --to "$TO" --subject "$SUBJECT" --text "$BODY" --send
