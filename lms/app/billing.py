"""Razorpay subscription billing for the public LMS.

Model: ₹499/month, 7-day free trial with the mandate captured upfront (UPI Autopay or
card e-mandate), auto-charge at trial end, cancel anytime.

How the trial works on Razorpay: a Subscription is created with `start_at` set TRIAL_DAYS
in the future. The customer authorises the recurring mandate now (via Razorpay's hosted
auth page / `short_url`); the FIRST debit only happens at `start_at`. Cancelling before
then = never charged. Everything is driven by webhooks (the source of truth for state).

All functions are safe no-ops / raise clean errors when keys aren't configured, so the
app boots fine in test/unconfigured mode.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from .config import settings

try:
    import razorpay  # type: ignore
except Exception:  # SDK not installed in some envs — keep import soft
    razorpay = None


def _keys_ok() -> bool:
    return bool(razorpay and settings.RZP_KEY_ID and settings.RZP_KEY_SECRET)


def configured() -> bool:
    """The ₹499 course plan is fully configured (keys + course plan id)."""
    return _keys_ok() and bool(settings.RZP_PLAN_ID)


def configured_assess() -> bool:
    """The ₹199 student-assessment plan is fully configured (keys + assess plan id)."""
    return _keys_ok() and bool(settings.RZP_ASSESS_PLAN_ID)


def _client():
    if not _keys_ok():
        raise RuntimeError("Razorpay keys not configured (RZP_KEY_ID / RZP_KEY_SECRET).")
    c = razorpay.Client(auth=(settings.RZP_KEY_ID, settings.RZP_KEY_SECRET))
    c.set_app_details({"title": "TrigunAI-LMS", "version": "1.0"})
    return c


def ensure_customer(client, name: str, email: str, contact: str = "") -> str:
    """Create (or fetch existing) Razorpay customer; returns customer id."""
    data = {"name": name or email.split("@")[0], "email": email, "fail_existing": 0}
    if contact:
        data["contact"] = contact
    cust = client.customer.create(data)
    return cust["id"]


def create_subscription(name: str, email: str, course: str, contact: str = "",
                        customer_id: str = "", trial_days: int | None = None,
                        plan_id: str | None = None, total_count: int | None = None,
                        notes: dict | None = None) -> dict:
    """Create a subscription. Returns the Razorpay subscription dict (has `id` and
    `short_url` — redirect the user to short_url to authorise the mandate).

    `trial_days`: None -> the default free trial (settings.TRIAL_DAYS, first charge in N days).
    0 -> no trial, first charge happens immediately on authorisation (used when the student
    already consumed their one free trial, e.g. a no-card trial that expired).

    NOTE: we deliberately do NOT pass `customer_id`. Razorpay's hosted authorisation page
    (`short_url`) collects the customer's details itself; pre-attaching a customer_id makes
    that hosted page return "Hosted page is not available". The customer is linked back to
    us via `notes.email` + the subscription id (stored on the Student)."""
    client = _client()
    td = settings.TRIAL_DAYS if trial_days is None else int(trial_days)
    payload = {
        "plan_id": plan_id or settings.RZP_PLAN_ID,
        "total_count": total_count or settings.SUB_TOTAL_COUNT,
        "quantity": 1,
        "customer_notify": 1,
        "notes": notes or {"email": email, "course": course},
    }
    start_at = 0
    if td > 0:
        start_at = int(time.time()) + td * 86400
        payload["start_at"] = start_at              # <-- delay first charge = the free trial
    if email or contact:
        payload["notify_info"] = {k: v for k, v in
                                  (("notify_email", email), ("notify_phone", contact)) if v}
    sub = client.subscription.create(payload)
    return {"id": sub["id"], "short_url": sub.get("short_url", ""),
            "customer_id": sub.get("customer_id", ""), "start_at": start_at,
            "status": sub.get("status")}


def cancel_subscription(sub_id: str, at_cycle_end: bool = True) -> dict:
    """Cancel. at_cycle_end=True keeps access until the paid period ends; during the trial
    Razorpay cancels immediately (nothing has been charged)."""
    client = _client()
    return client.subscription.cancel(sub_id, {"cancel_at_cycle_end": 1 if at_cycle_end else 0})


def fetch_subscription(sub_id: str) -> dict:
    return _client().subscription.fetch(sub_id)


def verify_webhook(body: bytes, signature: str) -> bool:
    """Verify the X-Razorpay-Signature header against the raw body."""
    if not (razorpay and settings.RZP_WEBHOOK_SECRET):
        return False
    try:
        razorpay.Utility().verify_webhook_signature(
            body.decode("utf-8"), signature, settings.RZP_WEBHOOK_SECRET
        )
        return True
    except Exception:
        return False


def ts_to_dt(ts: Optional[int]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.utcfromtimestamp(int(ts))
    except Exception:
        return None


# Map a Razorpay subscription entity -> our internal sub_status.
# Razorpay statuses: created, authenticated, active, pending, halted, cancelled, completed, expired
_STATUS_MAP = {
    "created": "created",
    "authenticated": "trialing",   # mandate done, first charge scheduled at start_at (= trial end)
    "active": "active",
    "pending": "past_due",         # a charge failed; Razorpay is retrying
    "halted": "past_due",          # retries exhausted — prompt the user to update payment
    "cancelled": "cancelled",
    "completed": "cancelled",
    "expired": "cancelled",
}


def map_status(rzp_status: str) -> str:
    return _STATUS_MAP.get(rzp_status, "none")
