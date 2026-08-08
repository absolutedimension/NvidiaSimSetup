#!/usr/bin/env python3
"""
onboarding_bot.py — 6-question WhatsApp state machine that onboards a teacher to Acharya.

Flow:
  Meta webhook → wa_bridge.mjs → (if teacher in queue) → POST /wa_incoming here
  This returns the next question (or a done signal). wa_bridge.mjs sends the reply.

Also exposes:
  POST /send_template/{phone}   → send acharya_teacher_onboarding template to one queued teacher
  POST /send_all_pending        → send template to every teacher with stage=queued
  GET  /status                  → live dashboard of the queue
  POST /wa_incoming             → main state-machine driver (called by wa_bridge.mjs)

State is persisted in ~/teacher_gtm/onboarding_queue.json (single source of truth).
Env: reads ~/.openclaw/wa_cloud.env for META_TOKEN + PHONE_NUMBER_ID.

Run:
  DRY_RUN=1 python3 onboarding_bot.py --test-flow                # simulate a teacher end-to-end
  uvicorn onboarding_bot:app --host 127.0.0.1 --port 7864         # serve for wa_bridge.mjs
"""
from __future__ import annotations
import os, json, time, uuid, argparse, urllib.request, urllib.error, sys, re
from pathlib import Path
from typing import Any
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse
    _FASTAPI = True
except ImportError:
    _FASTAPI = False

# ── config ────────────────────────────────────────────────────────────────────
HOME = Path(os.path.expanduser("~"))
QUEUE_PATH = HOME / "teacher_gtm" / "onboarding_queue.json"
ENV_PATH   = HOME / ".openclaw" / "wa_cloud.env"
LOG_PATH   = HOME / "teacher_gtm" / "onboarding_events.jsonl"
CALL_RESULTS_PATH = Path(os.environ.get("CALL_RESULTS_PATH", str(HOME / "leads" / "call_results.csv")))
WEB_ONBOARD_BASE = os.environ.get("WEB_ONBOARD_BASE", "https://gurukul.trigunai.com/onboard")
ONBOARD_HTML_PATH = Path(os.environ.get("ONBOARD_HTML_PATH", str(HOME / "teacher_gtm" / "onboard_standalone.html")))
SELFSERVE_HTML_PATH = Path(os.environ.get("SELFSERVE_HTML_PATH", str(HOME / "teacher_gtm" / "onboard_selfserve.html")))
ONBOARD_BOT_BASE_FOR_BROWSER = os.environ.get("ONBOARD_BOT_BASE_FOR_BROWSER", "https://gurukul.trigunai.com")
TEMPLATE_NAME = "acharya_teacher_onboarding"
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# ── env loading (matches wa_send.py convention) ───────────────────────────────
def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.replace("export ", "").strip(), v.strip())

# ── queue I/O ─────────────────────────────────────────────────────────────────
def load_queue() -> dict:
    return json.loads(QUEUE_PATH.read_text())

def save_queue(q: dict) -> None:
    tmp = QUEUE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(q, indent=2, ensure_ascii=False))
    tmp.replace(QUEUE_PATH)

def find_teacher(q: dict, wa_number: str) -> dict | None:
    for t in q.get("teachers", []):
        if t.get("wa_number") == wa_number:
            return t
    return None

def log_event(event: dict) -> None:
    event["ts"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5.5 * 3600))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

# ── Meta send helpers ─────────────────────────────────────────────────────────
def _meta_post(payload: dict) -> tuple[bool, str]:
    if DRY_RUN:
        print(f"[DRY_RUN] would send → {json.dumps(payload, ensure_ascii=False)}")
        return True, f"dryrun-msg-{uuid.uuid4().hex[:8]}"
    token = os.environ["META_TOKEN"]
    pid   = os.environ["PHONE_NUMBER_ID"]
    gv    = os.environ.get("GRAPH_VERSION", "v21.0")
    req = urllib.request.Request(
        f"https://graph.facebook.com/{gv}/{pid}/messages",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        return True, r.get("messages", [{}])[0].get("id", "")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return False, str(e)[:300]

def send_template(to: str, name_param: str) -> tuple[bool, str]:
    """Send the approved acharya_teacher_onboarding template to a teacher."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": "en_US"},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": name_param}],
            }],
        },
    }
    return _meta_post(payload)

def send_text(to: str, body: str) -> tuple[bool, str]:
    """Free-form text (only works inside the 24h window opened by teacher's reply)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body[:4096]},
    }
    return _meta_post(payload)

def send_buttons(to: str, body: str, buttons: list[str]) -> tuple[bool, str]:
    """Interactive quick-reply buttons (max 3 buttons, 20 char titles)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b.lower(), "title": b[:20]}}
                    for b in buttons[:3]
                ]
            },
        },
    }
    return _meta_post(payload)

# ── state machine ─────────────────────────────────────────────────────────────
#
# stage transitions:
#   queued
#     → send_template → template_sent
#   template_sent + teacher taps START (or replies any text)
#     → started + collecting_q1
#   collecting_q1..q6
#     → each answer advances to the next
#   collecting_q6_web_link  (we send the URL, wait for form submit)
#     → web_upload_pending
#   external webhook from web form
#     → provisioning → live
#
#   also: any stage + teacher replies STOP → opted_out (final)
#
QUESTIONS = [
    {
        "key": "coaching_name_confirmed",
        "prompt": (
            "Namaste ji 🙏\n\n"
            "Aapke coaching ka pura naam confirm kar dijiye — yahi naam Acharya par "
            "aur students ke messages mein dikhega.\n\n"
            "Reply karein aap ka coaching / institute name."
        ),
    },
    {
        "key": "subject_class",
        "prompt": (
            "Bahut accha ji ✅\n\n"
            "Aap kaunsa subject padhaate hain? Aur konsi class / exam ke liye?\n"
            "*Example:* Physics — Class 11-12 JEE\n"
            "*Example:* Full package — NEET dropper batch\n\n"
            "Reply karein."
        ),
    },
    {
        "key": "student_count",
        "prompt": (
            "Aapke lagbhag kitne students hain? (approximate theek hai)\n\n"
            "*Example:* 40\n*Example:* 120"
        ),
    },
    {
        "key": "brand_color",
        "prompt": (
            "Aapka pasandeeda brand color? — students ke dashboard aur Acharya messages "
            "mein yahi dikhega.\n\n"
            "Reply karein ek option:\n"
            "🔴 red   🟢 green   🔵 blue   🟡 yellow   ⚫ black\n"
            "ya reply karein `default` (TrigunAI gold)"
        ),
    },
    {
        "key": "logo_choice",
        "prompt": (
            "Aapka logo? Reply karein:\n\n"
            "*LOGO* — apna logo bhejna hai (mein aage image maangungi)\n"
            "*SKIP* — default Acharya branding chalega abhi ke liye"
        ),
    },
    {
        "key": "web_form_sent",  # sentinel — this "question" is the web link
        "prompt": None,  # constructed dynamically per teacher (has token)
    },
]

def _next_question_index(teacher: dict) -> int:
    """Which question is this teacher currently on (0-indexed)? Returns len(QUESTIONS) if done."""
    for i, q in enumerate(QUESTIONS):
        if q["key"] not in teacher.get("answers", {}):
            return i
    return len(QUESTIONS)

def _mint_web_token(teacher: dict) -> str:
    tok = teacher.get("web_token")
    if not tok:
        tok = uuid.uuid4().hex[:16]
    return tok

def build_web_link(teacher: dict) -> str:
    tok = _mint_web_token(teacher)
    teacher["web_token"] = tok
    return f"{WEB_ONBOARD_BASE}/{tok}"

def _push_history(teacher: dict, direction: str, body: str) -> None:
    teacher.setdefault("history", []).append({
        "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5.5 * 3600)),
        "dir": direction,  # "in" or "out"
        "body": body[:500],
    })

_AUTO_REPLY_PATTERNS = [
    r"thank you for contact",
    r"will contact you soon",
    r"representatives will contact",
    r"one of our representatives",
    r"auto[- ]?reply",
    r"drop your message",
    r"our team will get back",
    r"we will get back to you",
    r"outside (?:our |the )?business hours",
    r"reach out on our number",
]

def _looks_like_auto_reply(text: str) -> bool:
    """Detect WhatsApp Business auto-reply messages so we don't advance the state machine on them.
    Real teacher answers are short + human; auto-replies are long + marketing-y + multi-pattern."""
    if not text or len(text) < 40:
        return False
    t = text.lower()
    hits = sum(1 for p in _AUTO_REPLY_PATTERNS if re.search(p, t))
    return hits >= 1

def handle_incoming(wa_number: str, incoming_text: str, button_id: str | None = None) -> dict:
    """
    Core state-machine driver. Called for every teacher-side message.
    Returns {"reply": <text or None>, "buttons": [...], "stage": <new_stage>, "provisioned": bool}
    Persists the queue.
    """
    incoming_text = (incoming_text or "").strip()
    q = load_queue()
    teacher = find_teacher(q, wa_number)
    if not teacher:
        return {"reply": None, "buttons": [], "stage": "not_in_queue", "provisioned": False}

    # Auto-reply guard: WhatsApp Business accounts send auto-replies that look like real answers.
    # If we detect one, log + freeze the state (do NOT advance). Button clicks bypass this check
    # since a real human tap is always intentional.
    if not button_id and _looks_like_auto_reply(incoming_text):
        _push_history(teacher, "in", f"[AUTO-REPLY IGNORED] {incoming_text[:120]}")
        teacher.setdefault("auto_reply_count", 0)
        teacher["auto_reply_count"] = teacher["auto_reply_count"] + 1
        save_queue(q)
        log_event({"wa": wa_number, "event": "auto_reply_ignored",
                   "count": teacher["auto_reply_count"], "text_preview": incoming_text[:120]})
        return {"reply": None, "buttons": [], "stage": teacher["stage"], "provisioned": False}

    _push_history(teacher, "in", button_id or incoming_text)

    # global opt-out
    if incoming_text.upper() == "STOP" or (button_id and button_id.lower() == "stop"):
        teacher["stage"] = "opted_out"
        _push_history(teacher, "out", "opted out — no further messages")
        save_queue(q)
        log_event({"wa": wa_number, "event": "opted_out"})
        return {"reply": None, "buttons": [], "stage": "opted_out", "provisioned": False}

    # first inbound after template = teacher tapped START (or any text) → begin questions
    if teacher["stage"] in ("template_sent", "template_delivered", "template_read"):
        teacher["stage"] = "collecting_details"
        teacher["answers"] = {}
        first_q = QUESTIONS[0]["prompt"]
        _push_history(teacher, "out", first_q)
        save_queue(q)
        log_event({"wa": wa_number, "event": "started"})
        return {"reply": first_q, "buttons": [], "stage": teacher["stage"], "provisioned": False}

    # if we're mid-flow, record the answer for the CURRENT question
    if teacher["stage"] == "collecting_details":
        idx = _next_question_index(teacher)
        if idx >= len(QUESTIONS):
            # all answered — shouldn't reach here without provision fire, but handle gracefully
            return {"reply": None, "buttons": [], "stage": teacher["stage"], "provisioned": False}
        current = QUESTIONS[idx]
        teacher.setdefault("answers", {})[current["key"]] = button_id or incoming_text
        # advance
        next_idx = idx + 1
        if next_idx < len(QUESTIONS) - 1:
            # normal next question
            reply = QUESTIONS[next_idx]["prompt"]
            _push_history(teacher, "out", reply)
            save_queue(q)
            return {"reply": reply, "buttons": [], "stage": teacher["stage"], "provisioned": False}
        elif next_idx == len(QUESTIONS) - 1:
            # last "question" is the web link
            link = build_web_link(teacher)
            reply = (
                "Bahut accha ji 🙏\n\n"
                "Aakhri step — apne students ki list (naam + WhatsApp number) yahan upload karein, "
                "logo/colour ka preview dekhein, aur confirm karein:\n\n"
                f"👉 {link}\n\n"
                "5-10 minute lagega. Confirm hote hi aapka Acharya LIVE ho jaayega."
            )
            teacher["stage"] = "web_upload_pending"
            teacher["answers"]["web_form_sent"] = link
            _push_history(teacher, "out", reply)
            save_queue(q)
            log_event({"wa": wa_number, "event": "web_link_sent", "token": teacher["web_token"]})
            return {"reply": reply, "buttons": [], "stage": teacher["stage"], "provisioned": False}

    if teacher["stage"] == "web_upload_pending":
        # teacher pinged us but hasn't submitted the form yet — nudge
        link = teacher.get("answers", {}).get("web_form_sent", "")
        reply = (
            "Bas ek step baaki hai ji 🙏\n\n"
            "Web form pe apne students + logo upload kar dijiye:\n"
            f"👉 {link}\n\n"
            "Koi problem ho to yahin reply karein — mein help karungi."
        )
        _push_history(teacher, "out", reply)
        save_queue(q)
        return {"reply": reply, "buttons": [], "stage": teacher["stage"], "provisioned": False}

    if teacher["stage"] == "live":
        # teacher already provisioned — pass through to Acharya as a normal user
        return {"reply": None, "buttons": [], "stage": "live", "provisioned": True}

    # default: unhandled state
    return {"reply": None, "buttons": [], "stage": teacher["stage"], "provisioned": False}

def mark_web_form_submitted(wa_number: str, form_data: dict) -> dict:
    """Called by the web form's POST /submit handler. Fires provisioning."""
    q = load_queue()
    teacher = find_teacher(q, wa_number)
    if not teacher:
        return {"ok": False, "error": "teacher not in queue"}
    teacher["stage"] = "provisioning"
    teacher["form_data"] = form_data
    save_queue(q)
    log_event({"wa": wa_number, "event": "web_form_submitted", "form": form_data})
    # TODO: actual acharya-technology-transfer invocation here.
    # For now we mark ready; a companion cron / hook fires the skill.
    return {"ok": True, "stage": "provisioning"}

def _notify_gtm(text: str) -> None:
    """Fire-and-forget Telegram ping to the GTM group. Never breaks the caller."""
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            vp = HOME / "voicebot_wa" / "wa_voice.env"
            if vp.exists():
                for ln in vp.read_text().splitlines():
                    ln = ln.strip()
                    if ln.startswith(("export TELEGRAM_BOT_TOKEN=", "TELEGRAM_BOT_TOKEN=")):
                        token = ln.split("=", 1)[1].strip()
                        break
        if not token:
            return
        chat = os.environ.get("TELEGRAM_GTM_CHAT", "-1004424694241")
        data = json.dumps({"chat_id": chat, "text": text[:3900]}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, method="POST", headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

def create_self_signup(form: dict) -> dict:
    """Public self-serve intake (no token). Creates/updates a teacher record + alerts the team."""
    wa = _normalise_phone(form.get("whatsapp", ""))
    if not wa or len(wa) < 11:
        return {"ok": False, "error": "A valid WhatsApp number with country code is required."}
    coaching = (form.get("coaching_name") or "").strip()
    teacher_name = (form.get("teacher_name") or "").strip()
    if not coaching:
        return {"ok": False, "error": "Coaching / institute name is required."}
    q = load_queue()
    if "self_signup" not in q.get("_stages", []):
        q.setdefault("_stages", []).append("self_signup")
    t = find_teacher(q, wa)
    if not t:
        t = {"wa_number": wa, "history": [], "answers": {}}
        q.setdefault("teachers", []).append(t)
    t["coaching_name"] = coaching
    t["teacher_name"] = teacher_name
    t["stage"] = "self_signup"
    t["source"] = "self_serve_web"
    t["form_data"] = form
    save_queue(q)
    log_event({"wa": wa, "event": "self_signup", "coaching": coaching,
               "teacher": teacher_name, "subject": form.get("subject_class", ""), "form": form})
    _notify_gtm(
        "🟢 NEW SELF-SERVE ONBOARDING\n"
        f"🏫 {coaching}\n"
        f"👤 {teacher_name} · 📱 {wa}\n"
        f"📚 {form.get('subject_class','')}\n"
        f"🗓 Timeline: {form.get('timeline','')}\n"
        f"👥 Students: {'provided' if form.get('students') else 'to follow'} · Lang: {form.get('language','')}\n"
        "→ Review in onboarding_queue (stage=self_signup), then provision."
    )
    return {"ok": True}

def mark_provisioned(wa_number: str, tenant_url: str) -> dict:
    """Called by acharya-technology-transfer when the branded instance is live."""
    q = load_queue()
    teacher = find_teacher(q, wa_number)
    if not teacher:
        return {"ok": False, "error": "teacher not in queue"}
    teacher["stage"] = "live"
    teacher["tenant_url"] = tenant_url
    save_queue(q)
    final_msg = (
        "🎉 Aapka Acharya LIVE hai ji!\n\n"
        f"Students ko yeh link forward karein — woh sidha WhatsApp par tutor se baat kar payenge:\n\n"
        f"👉 {tenant_url}\n\n"
        "Kuchh bhi problem ho to yahin reply karein — mein help karungi. Shubhkaamnaayein! 🙏"
    )
    send_text(wa_number, final_msg)
    _push_history(teacher, "out", final_msg)
    save_queue(q)
    log_event({"wa": wa_number, "event": "live", "tenant_url": tenant_url})
    return {"ok": True, "stage": "live"}

# ── ingest: sync interested=yes rows from Maya's call_results.csv into queue ─
def _normalise_phone(raw: str) -> str:
    d = "".join(ch for ch in raw if ch.isdigit())
    if len(d) == 10:
        return "91" + d
    if len(d) == 12 and d.startswith("91"):
        return d
    return d  # let caller decide

def _guess_contact_name_for_template(coaching_name: str) -> str:
    """{{1}} for the template. Empty coaching_name → return '' so caller marks stage=needs_name."""
    n = (coaching_name or "").strip()
    if not n:
        return ""
    # take up to the first pipe / dash / comma, then trim to a short human phrase
    head = n.split("|")[0].split("—")[0].split(",")[0].strip()
    if len(head) > 40:
        head = head[:37] + "..."
    return head + " sir" if not head.lower().endswith(("sir", "ji")) else head

def sync_from_call_results() -> dict:
    """Ingest rows from ~/leads/call_results.csv where interested=yes into the onboarding queue.
    Idempotent: teachers already in the queue (any stage) are skipped.
    Rows with an empty name go in with stage='needs_name' — so they surface for review
    without accidentally sending a blank-name template. Returns a summary dict."""
    import csv
    q = load_queue()
    existing = {t.get("wa_number") for t in q.get("teachers", [])}
    added, needs_name, skipped_dup = 0, 0, 0
    try:
        rows = list(csv.DictReader(open(CALL_RESULTS_PATH, encoding="utf-8")))
    except Exception as e:
        return {"error": f"could not read {CALL_RESULTS_PATH}: {e}"}
    for r in rows:
        if (r.get("interested") or "").strip().lower() != "yes":
            continue
        wa = _normalise_phone(r.get("phone", ""))
        if not wa or len(wa) != 12:
            continue
        if wa in existing:
            skipped_dup += 1
            continue
        coaching = (r.get("name") or "").strip()
        contact = _guess_contact_name_for_template(coaching)
        stage = "queued" if contact else "needs_name"
        q["teachers"].append({
            "wa_number": wa,
            "called_phone": wa,
            "coaching_name": coaching or "(unnamed — from call_results.csv)",
            "contact_name_for_template": contact,
            "city": (r.get("city") or "").strip(),
            "segment": (r.get("segment") or "").strip(),
            "call_duration_s": int(r.get("duration") or 0) if (r.get("duration") or "").isdigit() else 0,
            "consent_source": "auto_sync_call_results_interested_yes",
            "stage": stage,
            "notes": "auto-synced from call_results.csv. wa_number = called_phone (heuristic). Verify against transcript when possible.",
            "history": [],
        })
        existing.add(wa)
        if stage == "needs_name":
            needs_name += 1
        else:
            added += 1
    save_queue(q)
    log_event({"event": "sync_from_call_results", "added": added, "needs_name": needs_name, "skipped_dup": skipped_dup})
    return {"added": added, "needs_name": needs_name, "skipped_dup": skipped_dup, "total_in_queue": len(q["teachers"])}

def list_queue() -> None:
    """Pretty-print the current queue grouped by stage."""
    q = load_queue()
    by_stage: dict[str, list] = {}
    for t in q.get("teachers", []):
        by_stage.setdefault(t.get("stage", "?"), []).append(t)
    stage_order = ["queued", "needs_name", "template_sent", "template_delivered",
                   "started", "collecting_details", "web_upload_pending",
                   "provisioning", "live", "opted_out", "failed"]
    for s in stage_order:
        if s not in by_stage:
            continue
        rows = by_stage[s]
        print(f"\n== {s.upper()} ({len(rows)}) ==")
        for t in rows:
            city = (t.get("city") or "").ljust(20)
            print(f"  · {t['wa_number']:14} {city} {t.get('coaching_name','')[:60]}")
    print(f"\nTotal: {len(q.get('teachers', []))} teachers")

# ── operator commands (send template to queue) ────────────────────────────────
def send_template_to(wa_number: str) -> dict:
    q = load_queue()
    teacher = find_teacher(q, wa_number)
    if not teacher:
        return {"ok": False, "error": "teacher not in queue"}
    if teacher["stage"] != "queued":
        return {"ok": False, "error": f"stage is {teacher['stage']}, not queued"}
    ok, msg_id = send_template(wa_number, teacher["contact_name_for_template"])
    if ok:
        teacher["stage"] = "template_sent"
        teacher["template_msg_id"] = msg_id
        _push_history(teacher, "out", f"[template {TEMPLATE_NAME}] sent (id={msg_id})")
        save_queue(q)
        log_event({"wa": wa_number, "event": "template_sent", "msg_id": msg_id})
    else:
        log_event({"wa": wa_number, "event": "template_failed", "error": msg_id})
    return {"ok": ok, "msg_id_or_error": msg_id, "stage": teacher["stage"]}

def send_all_pending() -> list[dict]:
    q = load_queue()
    results = []
    for t in q.get("teachers", []):
        if t.get("stage") == "queued":
            r = send_template_to(t["wa_number"])
            r["wa_number"] = t["wa_number"]
            r["coaching_name"] = t.get("coaching_name")
            results.append(r)
            time.sleep(1)
    return results

# ── FastAPI (only built if fastapi is available) ─────────────────────────────
def _build_app():
    if not _FASTAPI:
        return None
    app = FastAPI()

    @app.post("/wa_incoming")
    async def wa_incoming(req: Request):
        payload = await req.json()
        wa = payload.get("wa_number", "")
        text = payload.get("text", "")
        btn  = payload.get("button_id")
        return handle_incoming(wa, text, btn)

    @app.post("/send_template/{phone}")
    def _st(phone: str):
        return send_template_to(phone)

    @app.post("/send_all_pending")
    def _sap():
        return {"results": send_all_pending()}

    @app.post("/web_form_submitted")
    async def _wfs(req: Request):
        payload = await req.json()
        return mark_web_form_submitted(payload["wa_number"], payload.get("form", {}))

    @app.post("/mark_provisioned")
    async def _mp(req: Request):
        payload = await req.json()
        return mark_provisioned(payload["wa_number"], payload["tenant_url"])

    @app.get("/onboard/{token}", response_class=HTMLResponse)
    def _onboard_page(token: str):
        """Serve the teacher-facing onboarding form. Substitutes __TOKEN__ + __BOT_BASE__ into the standalone HTML."""
        try:
            html = ONBOARD_HTML_PATH.read_text()
        except Exception:
            return HTMLResponse(status_code=500, content="<h1>Setup unavailable</h1><p>Please reply on WhatsApp for help.</p>")
        html = html.replace("__TOKEN__", token).replace("__BOT_BASE__", ONBOARD_BOT_BASE_FOR_BROWSER)
        return HTMLResponse(content=html)

    @app.get("/lookup_token/{token}")
    def _lookup(token: str):
        """LMS web page calls this to get teacher context for the /onboard/{token} page."""
        q = load_queue()
        for t in q.get("teachers", []):
            if t.get("web_token") == token and t.get("stage") == "web_upload_pending":
                return {
                    "ok": True,
                    "wa_number": t["wa_number"],
                    "coaching_name": t.get("answers", {}).get("coaching_name_confirmed") or t.get("coaching_name"),
                    "subject_class": t.get("answers", {}).get("subject_class", ""),
                    "student_count": t.get("answers", {}).get("student_count", ""),
                    "brand_color": t.get("answers", {}).get("brand_color", "default"),
                    "logo_choice": t.get("answers", {}).get("logo_choice", "skip"),
                    "city": t.get("city", ""),
                }
        return {"ok": False, "error": "token not found or already used"}

    @app.post("/onboard_submit/{token}")
    async def _onboard_submit(token: str, req: Request):
        """LMS web page POSTs here with parsed student list + confirmed settings."""
        q = load_queue()
        for t in q.get("teachers", []):
            if t.get("web_token") == token and t.get("stage") == "web_upload_pending":
                form = await req.json()
                return mark_web_form_submitted(t["wa_number"], form)
        return {"ok": False, "error": "token not found or expired"}

    @app.get("/start", response_class=HTMLResponse)
    def _selfserve_page():
        """Public, no-token self-serve onboarding form (shareable link for the video / marketing)."""
        try:
            html = SELFSERVE_HTML_PATH.read_text()
        except Exception:
            return HTMLResponse(status_code=500, content="<h1>Setup unavailable</h1><p>Please message us on WhatsApp.</p>")
        html = html.replace("__BOT_BASE__", ONBOARD_BOT_BASE_FOR_BROWSER)
        return HTMLResponse(content=html)

    @app.post("/self_onboard")
    async def _self_onboard(req: Request):
        form = await req.json()
        return create_self_signup(form)

    @app.get("/status")
    def _status():
        q = load_queue()
        return {
            "total": len(q.get("teachers", [])),
            "by_stage": {
                s: sum(1 for t in q["teachers"] if t.get("stage") == s)
                for s in q.get("_stages", [])
            },
            "teachers": [
                {k: t.get(k) for k in ("wa_number", "coaching_name", "stage")}
                for t in q.get("teachers", [])
            ],
        }

    return app

# module-level app (for `uvicorn onboarding_bot:app`)
try:
    load_env()
    app = _build_app()
except Exception:
    app = None  # fastapi not installed on this system yet

# ── CLI: local simulation ─────────────────────────────────────────────────────
def _simulate() -> None:
    """End-to-end dry-run for one teacher (uses first queued teacher)."""
    load_env()
    q = load_queue()
    t0 = next((t for t in q["teachers"] if t["stage"] == "queued"), None)
    if not t0:
        print("no queued teacher to simulate")
        return
    wa = t0["wa_number"]
    print(f"\n=== SIMULATING FLOW for {wa} ({t0['coaching_name']}) ===\n")

    print(">>> operator: send_template_to")
    print(send_template_to(wa), "\n")

    scripted = [
        ("HI aapki call aayi thi mujhe interest hai", None),  # trigger start
        ("Catalyzers Institute, Kota", None),                  # Q1
        ("Physics + Chemistry — Class 11-12 JEE dropper batch", None),  # Q2
        ("85", None),                                          # Q3
        ("blue", "blue"),                                      # Q4
        ("SKIP", "skip"),                                      # Q5
    ]
    for text, btn in scripted:
        print(f">>> teacher says: {text!r}  button={btn}")
        out = handle_incoming(wa, text, btn)
        print(f"    bot replies:  stage={out['stage']}")
        if out["reply"]:
            print(f"    ---\n{out['reply']}\n    ---\n")

    # simulate web form submit
    print(">>> operator: mark_web_form_submitted")
    print(mark_web_form_submitted(wa, {"students_csv": "5 rows", "logo": "default", "color": "blue"}), "\n")

    # simulate provision completion
    print(">>> operator: mark_provisioned")
    print(mark_provisioned(wa, "https://acharya.trigunai.com/t/catalyzers"), "\n")

    # show final state
    q2 = load_queue()
    t2 = find_teacher(q2, wa)
    print(f"=== final teacher state ===")
    print(f"  stage:        {t2['stage']}")
    print(f"  answers:      {json.dumps(t2.get('answers', {}), ensure_ascii=False)}")
    print(f"  web_token:    {t2.get('web_token')}")
    print(f"  tenant_url:   {t2.get('tenant_url')}")
    print(f"  history len:  {len(t2.get('history', []))}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-flow", action="store_true", help="Dry-run one teacher end-to-end")
    ap.add_argument("--reset", action="store_true", help="DANGER: reset all teachers to stage=queued (test only)")
    ap.add_argument("--sync", action="store_true", help="Ingest new interested=yes rows from call_results.csv into the queue")
    ap.add_argument("--list", action="store_true", help="Pretty-print the current queue grouped by stage")
    ap.add_argument("--send-batch", action="store_true", help="Fire template to every teacher with stage=queued (via bot API)")
    ap.add_argument("--fix-name", nargs=2, metavar=("PHONE", "COACHING_NAME"),
                    help="Add coaching name to a needs_name teacher; auto-moves them to stage=queued")
    args = ap.parse_args()
    load_env()
    if args.sync:
        r = sync_from_call_results()
        print(json.dumps(r, indent=2))
        return
    if args.list:
        list_queue()
        return
    if args.send_batch:
        r = send_all_pending()
        print(json.dumps(r, indent=2))
        return
    if args.fix_name:
        phone, name = args.fix_name
        phone = _normalise_phone(phone)
        q = load_queue()
        for t in q.get("teachers", []):
            if t.get("wa_number") == phone:
                if t.get("stage") != "needs_name":
                    print(f"⚠️  {phone} stage is {t['stage']!r}, not needs_name — refusing to overwrite")
                    return
                t["coaching_name"] = name.strip()
                t["contact_name_for_template"] = _guess_contact_name_for_template(name)
                t["stage"] = "queued"
                save_queue(q)
                log_event({"event": "fix_name", "wa": phone, "new_name": name})
                print(f"✅ {phone} fixed: coaching_name={name!r}, stage=queued")
                return
        print(f"❌ {phone} not found in queue")
        return
    if args.reset:
        q = load_queue()
        for t in q["teachers"]:
            t["stage"] = "queued"
            t.pop("answers", None); t.pop("history", None); t.pop("web_token", None)
            t.pop("template_msg_id", None); t.pop("form_data", None); t.pop("tenant_url", None)
        save_queue(q)
        print("queue reset — all teachers back to stage=queued")
        return
    if args.test_flow:
        _simulate()
        return
    print(__doc__)

if __name__ == "__main__":
    main()
