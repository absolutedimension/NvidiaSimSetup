#!/usr/bin/env python3
"""
pulse.py — the TrigunAI campaign + funnel command center.

Pulls the LIVE signup/login truth from the Acharya LMS (`/admin/api/pulse`, read-only,
key-gated) and prints one clean scoreboard: who is joining, from where, and whether
anyone is paying — regardless of source (Google Ads, LinkedIn, WhatsApp, manual, direct).

Google Ads numbers are entered by hand for now (the Ads API needs an OAuth setup) — keep
them in ~/.claude/skills/trigunai-campaign-tracker/ads.json and this script folds them in.

Usage:
    python3 pulse.py                 # fetch live + print scoreboard
    python3 pulse.py --file x.json   # format a saved payload (offline/testing)
    python3 pulse.py --raw           # dump the raw JSON

Env:
    PULSE_URL   default https://acharya.trigunai.com/admin/api/pulse
    PULSE_KEY   default trigunai-pulse-2026   (must match the LMS container's PULSE_KEY)
"""
import json
import os
import sys
import urllib.request

PULSE_URL = os.getenv("PULSE_URL", "https://acharya.trigunai.com/admin/api/pulse")
_KEY_FILE = os.path.expanduser("~/.claude/skills/trigunai-campaign-tracker/.pulse_key")


def _resolve_key():
    """Key resolution order: env PULSE_KEY > local .pulse_key file > default.
    The real prod key lives ONLY in .pulse_key (git-ignored) — never in this committed file."""
    if os.getenv("PULSE_KEY"):
        return os.getenv("PULSE_KEY").strip()
    try:
        with open(_KEY_FILE) as f:
            return f.read().strip()
    except Exception:
        return "trigunai-pulse-2026"


PULSE_KEY = _resolve_key()
ADS_FILE = os.path.expanduser("~/.claude/skills/trigunai-campaign-tracker/ads.json")

C = {"g": "\033[92m", "y": "\033[93m", "r": "\033[91m", "b": "\033[94m",
     "d": "\033[2m", "B": "\033[1m", "x": "\033[0m"}


def col(s, c):
    return f"{C[c]}{s}{C['x']}"


def fetch():
    url = f"{PULSE_URL}?key={PULSE_KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def load_ads():
    """Manual Google Ads numbers. Edit ads.json after reading the Ads dashboard.
    Shape: {"spend": 0, "impressions": 0, "clicks": 0, "avg_cpc": 0, "campaign": "patna-students"}"""
    try:
        with open(ADS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def bar(label, val, note=""):
    return f"  {label:<22} {col(str(val), 'B'):<18} {col(note, 'd')}"


def render(p):
    ep = p.get("exam_prep", {})
    cc = p.get("course_cohort", {})
    web = p.get("web", {})
    ads = load_ads()

    print()
    print(col("═" * 66, "b"))
    print(col("  ACHARYA — EXAM-PREP CAMPAIGN & FUNNEL PULSE", "B") + col(f"   ({p.get('as_of','')})", "d"))
    print(col("  (assessment funnel only — the old course cohort is kept separate below)", "d"))
    print(col("═" * 66, "b"))

    # ---------- THE GATE (what actually matters right now) ----------
    paid = ep.get("assess_active", 0)
    trialing = ep.get("assess_trialing", 0)
    gate = col("0 — GATE NOT MOVED", "r") if paid == 0 else col(f"{paid} PAYING", "g")
    print()
    print(col("  ⭐ THE GATE", "B") + f"   exam-prep paid (₹249 student / ₹999+ teacher): {gate}   ·   trials: {trialing}")

    # ---------- ACQUISITION: who is joining (EXAM-PREP ONLY) ----------
    print()
    print(col("  WHO IS JOINING", "B") + col("  (exam-prep / assessment only)", "d"))
    print(bar("New signups 24h", ep.get("new_24h", 0)))
    print(bar("New signups 7d", ep.get("new_7d", 0)))
    print(bar("Exam-prep users total", ep.get("total", 0)))
    print(bar("Teachers / institutes", f"{ep.get('teachers',0)} / {len(ep.get('institutes',[]))}",
              ", ".join(ep.get("institutes", [])[:4])))
    print(bar("Logins 24h / 7d", f"{ep.get('logins_24h',0)} / {ep.get('logins_7d',0)}"))
    print(bar("Started a topic", ep.get("with_topics", 0), "took at least one test"))
    print(col(f"  {C['d']}· separate: {cc.get('total',0)} old course-cohort students "
              f"({cc.get('grandfathered',0)} grandfathered) — NOT the ad funnel{C['x']}", "d"))

    # ---------- SOURCE: where they came from ----------
    print()
    print(col("  WHERE FROM (7d traffic sources)", "B"))
    refs = web.get("top_refs", []) or []
    if refs:
        for r, n in refs[:6]:
            print(f"  {str(r)[:44]:<46} {col(n, 'B')}")
    else:
        print(col("  (no referrer data yet — direct/ad clicks land with no ref)", "d"))
    print(bar("Page views 24h / 7d", f"{web.get('pv_24h',0)} / {web.get('pv_7d',0)}"))
    print(bar("Unique visitors 24h/7d", f"{web.get('uv_24h',0)} / {web.get('uv_7d',0)}"))

    # ---------- GOOGLE ADS (manual) ----------
    print()
    print(col("  GOOGLE ADS", "B") + col(f"  ({ads.get('campaign','—')}, manual entry)", "d"))
    if ads:
        spend = ads.get("spend", 0)
        clicks = ads.get("clicks", 0)
        print(bar("Spend", f"₹{spend}"))
        print(bar("Impressions / clicks", f"{ads.get('impressions',0)} / {clicks}"))
        print(bar("Avg CPC", f"₹{ads.get('avg_cpc',0)}"))
        # cost per signup (attribution is loose at this stage, but directionally useful)
        if clicks and ep.get("new_7d"):
            print(bar("~Cost / signup", f"₹{round(spend / max(ep['new_7d'],1))}",
                      "spend ÷ 7d exam-prep signups (rough)"))
    else:
        print(col(f"  (no ads.json — create {ADS_FILE} with today's Ads numbers)", "d"))

    # ---------- RECENT SIGNUP FEED ----------
    print()
    print(col("  RECENT SIGNUPS (latest 10)", "B"))
    feed = p.get("recent_signups", [])[:10]
    if feed:
        for s in feed:
            role = col("T", "y") if s["role"] == "teacher" else col("S", "b")
            pay = col("₹PAID", "g") if s["assess"] == "active" else (
                  col("trial", "y") if s["assess"] == "trialing" else col("free", "d"))
            extra = f" · {s['institute']}" if s.get("institute") else ""
            topic = f" · {s['topic']}" if s.get("topic") else ""
            print(f"  [{role}] {s['name'][:16]:<16} {s['email']:<26} {pay:<14} "
                  f"{col(s['joined'], 'd')}{col(topic + extra, 'd')}")
    else:
        print(col("  (nobody yet)", "d"))

    # ---------- THE VERDICT (what to do) ----------
    print()
    print(col("─" * 66, "b"))
    print(col("  WHAT TO WATCH NOW", "B"))
    verdicts = []
    if ads and ads.get("clicks", 0) >= 20 and ep.get("new_7d", 0) == 0:
        verdicts.append(col("✗ Ad clicks but ZERO exam-prep signups → the landing/funnel is leaking. Fix the page, not the ad.", "r"))
    if ep.get("new_7d", 0) > 0 and ep.get("with_topics", 0) == 0:
        verdicts.append(col("⚠ Signups but nobody took a test → activation is the leak. Push straight into a test.", "y"))
    if paid == 0 and trialing > 0:
        verdicts.append(col("⚠ Trials but no paid → the ₹249 ask isn't converting. The leak is trial→paid, not traffic.", "y"))
    if paid == 0 and trialing == 0 and ep.get("new_7d", 0) == 0:
        verdicts.append(col("• Cold start. The ONLY number that matters this week: does a click become an exam-prep signup?", "d"))
    if paid > 0:
        verdicts.append(col(f"✓ {paid} paying. Now find WHICH source/keyword produced them and pour budget there.", "g"))
    for v in verdicts:
        print("  " + v)
    print(col("═" * 66, "b"))
    print()


def main():
    args = sys.argv[1:]
    if "--file" in args:
        p = json.load(open(args[args.index("--file") + 1]))
    else:
        try:
            p = fetch()
        except Exception as e:
            print(col(f"\n  ✗ Could not reach {PULSE_URL}", "r"))
            print(col(f"    {e}", "d"))
            print(col("    Is the pulse endpoint deployed + is PULSE_KEY correct?\n", "d"))
            sys.exit(1)
    if "--raw" in args:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return
    render(p)


if __name__ == "__main__":
    main()
