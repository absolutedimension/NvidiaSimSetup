# LMS route patch — teacher onboarding page

**File to edit:** `lms/app/main.py` (production LMS)
**Deploy target:** `acharya.trigunai.com` (Azure Container App, per `maintain-trigunai-system` skill)
**Risk:** LOW — adds one new template + one new GET route. No existing route touched. Behind an env flag so it can ship dark.
**Prereq:** template `onboard.html` already dropped at `lms/app/templates/onboard.html`.

---

## 1. Add near the top of `main.py` (with other env vars)

```python
# --- teacher onboarding (Gurukul VM bot bridge) ---
ONBOARDING_BOT_BASE = os.environ.get(
    "ONBOARDING_BOT_BASE",
    "https://gurukul.trigunai.com",   # or "http://127.0.0.1:7864" for local
)
TEACHER_ONBOARDING_ENABLED = os.environ.get("TEACHER_ONBOARDING", "off") == "on"
```

## 2. Add ONE new route (put near other public `@app.get` routes, e.g. after `/pricing`)

```python
@app.get("/onboard/{token}", response_class=HTMLResponse)
async def teacher_onboard(request: Request, token: str):
    """Teacher-facing onboarding page.
    The web token is minted by onboarding_bot.py on the Gurukul VM and sent to the
    teacher on WhatsApp after they answer the 5 in-chat questions. This page:
      - JS fetches ONBOARDING_BOT_BASE/lookup_token/{token} to preload teacher context
      - Teacher fills the form (students CSV + logo + colour preview)
      - Form POSTs to ONBOARDING_BOT_BASE/onboard_submit/{token}
      - The bot marks stage=provisioning, cron fires acharya-technology-transfer
    """
    if not TEACHER_ONBOARDING_ENABLED:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "onboard.html",
        {"request": request, "token": token, "bot_base_url": ONBOARDING_BOT_BASE},
    )
```

That's it. No auth needed on the page itself — the token is the auth (16-char UUID, single-use, only issued to a teacher who's already answered 5 WhatsApp questions).

## 3. Deploy

Per `maintain-trigunai-system`:
```bash
# from lms/ dir
docker build -t <registry>/lms:<vNN> .
docker push <registry>/lms:<vNN>
# then set env on the Azure Container App: TEACHER_ONBOARDING=on
```

Flip the flag ON only after step 4 below.

## 4. End-to-end test before flipping flag

1. On Gurukul VM: `DRY_RUN=0 uvicorn onboarding_bot:app --host 127.0.0.1 --port 7864` in tmux
2. Expose the bot via Caddy at `https://gurukul.trigunai.com` (path prefix `/onboard*` and `/lookup_token/*`)
3. Push LMS with `TEACHER_ONBOARDING=off` (route returns 404 — safe deploy)
4. Locally set `TEACHER_ONBOARDING=on` and hit `http://localhost:8000/onboard/testtoken123` — should render the form
5. Manually add a fake token to the queue for testing, walk through the flow

## 5. Caddy config for the bot (add to existing Caddyfile on Gurukul VM)

```caddy
gurukul.trigunai.com {
    handle_path /lookup_token/* { reverse_proxy 127.0.0.1:7864 }
    handle_path /onboard_submit/* { reverse_proxy 127.0.0.1:7864 }
    handle_path /wa_incoming { reverse_proxy 127.0.0.1:7864 }
    # existing rules preserved below
    ...
}
```

Only the LOOKUP + SUBMIT endpoints are public. `/wa_incoming` is called by `wa_bridge.mjs` on the SAME box — restrict it to loopback via a `@allow_local` matcher if you want extra hardening.
