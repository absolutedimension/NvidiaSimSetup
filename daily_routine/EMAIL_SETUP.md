# Real daily accountability emails — one-time setup (~5 min)

The morning (7am) + evening (9pm) accountability tasks send a REAL email to deepak@trigunai.com
via Azure Communication Services (the same ACS your LMS uses for magic-link emails), through
`marketing/publish.py`. Two things to set up on the machine that runs the tasks (the Mac):

## 1. Put the ACS credentials in `marketing/.env` (gitignored — safe)

Create `marketing/.env` with:

```
ACS_CONNECTION_STRING=<your Azure Communication Services connection string>
ACS_SENDER=DoNotReply@trigunai.com     # a VERIFIED sender on your ACS domain
```

Where to get them:
- **Azure Portal → your Communication Services resource → Keys** → "Connection string".
- Or copy from wherever the LMS already keeps it (the LMS emailer uses the same ACS — see
  `lms/app/config.py` / `lms/app/emailer.py`; the value lives in the LMS's deployed env, not in git).
- `ACS_SENDER` must be a sender address verified on your ACS Email Communication domain.

> `marketing/.env` is already in `.gitignore` — the secret never gets committed.

## 2. Install the ACS email SDK (once, on the Mac)

```
pip3 install azure-communication-email
```

## 3. Test it

```
echo "test brief from send_brief" > /tmp/brief.txt
daily_routine/send_brief.sh "Test — daily brief" /tmp/brief.txt
```
- Prints `sent 1/1` → real email works. Check deepak@trigunai.com inbox.
- Prints `NO_ACS …` → creds not found; re-check `marketing/.env`.

Until this is done, the tasks **fall back automatically** to creating a Gmail **draft** (in your
Drafts) — so you still get the brief, you just have to open Drafts to read it.
