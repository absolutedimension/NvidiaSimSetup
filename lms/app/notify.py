"""Admin WhatsApp notifications — pushes key LMS events to the founder's number.

Uses the Meta-approved `gurukul_announce` utility template (body: "🪔 TrigunAI Gurukul\n\n{{1}}"),
so it can be sent any time (business-initiated, outside a 24h window). Calls the Graph API directly
from the LMS so the live Gurukul bridge is never touched. Fire-and-forget on a daemon thread — a
notification failure can NEVER break or slow a signup/payment request.

Config (env / container secrets): WA_TOKEN, WA_PHONE_ID, WA_GRAPH_VERSION, ADMIN_WHATSAPP, NOTIFY_ENABLED.
Stays fully inert until WA_TOKEN + WA_PHONE_ID + ADMIN_WHATSAPP are all set.
Template params must be single-line (Meta rejects newlines / tabs / 4+ spaces) — keep messages one line.
"""
import json
import threading
import urllib.request

from .config import settings

# UTILITY template (transactional admin alerts deliver reliably; MARKETING templates get throttled).
_TEMPLATE = "admin_alert"


def _post(url: str, payload: dict) -> None:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {settings.WA_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=8).read()  # raises on non-2xx


def _send(text: str) -> None:
    if not (settings.WA_TOKEN and settings.WA_PHONE_ID and settings.ADMIN_WHATSAPP):
        return
    url = f"https://graph.facebook.com/{settings.WA_GRAPH_VERSION}/{settings.WA_PHONE_ID}/messages"
    # 1) UTILITY template — delivers any time (once approved). Preferred path.
    try:
        _post(url, {
            "messaging_product": "whatsapp", "to": settings.ADMIN_WHATSAPP, "type": "template",
            "template": {"name": _TEMPLATE, "language": {"code": "en_US"},
                         "components": [{"type": "body", "parameters": [{"type": "text", "text": text[:900]}]}]},
        })
        return
    except Exception as exc:
        print(f"[notify] template send failed ({exc}); falling back to text")
    # 2) Fallback: plain text — delivers only within the admin's 24h reply window, but means alerts
    #    work immediately while the template awaits approval / if it ever gets paused.
    try:
        _post(url, {
            "messaging_product": "whatsapp", "to": settings.ADMIN_WHATSAPP,
            "type": "text", "text": {"body": f"🔔 {text}"[:4000]},
        })
    except Exception as exc:  # never propagate — best-effort telemetry
        print(f"[notify] text fallback failed: {exc}")


def notify_admin(text: str) -> None:
    """Fire-and-forget WhatsApp ping to the admin number. Safe to call from any request; never raises."""
    if not settings.NOTIFY_ENABLED:
        return
    try:
        threading.Thread(target=_send, args=(text,), daemon=True).start()
    except Exception:
        pass
