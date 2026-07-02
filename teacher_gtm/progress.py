#!/usr/bin/env python3
"""
Teacher GTM progress engine.
State lives in teacher_gtm/progress.json (structured, machine-updated).
Renders teacher_gtm/PROGRESS.md (human dashboard) + prints a daily summary.

Usage:
  python3 progress.py show                      # render + print dashboard
  python3 progress.py log --date YYYY-MM-DD \\
        --queued N --conversations N --qualified N \\
        --pilots-booked N --pilots-live N \\
        --paid N --revenue N --note "..."       # add/overwrite a day's entry
  python3 progress.py interview --who aditya --note "verbatim reason"
The 'log' fields are the DAY's counts (not cumulative); totals are summed.
"""
import json, sys, os, argparse
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "progress.json")
DASH  = os.path.join(HERE, "PROGRESS.md")

DEFAULT = {
    "test_name": "Teacher B2B2C PMF test",
    "start": "2026-07-03",
    "end":   "2026-07-23",
    "targets": {"conversations": 30, "pilots_booked": 3, "pilots_live": 2, "paid": 1},
    "days": [],          # [{date, queued, conversations, qualified, pilots_booked, pilots_live, paid, revenue, note}]
    "interviews": {      # the 3 cohort non-payer interviews
        "aditya":   {"done": False, "note": ""},
        "kritansh": {"done": False, "note": ""},
        "gauri":    {"done": False, "note": ""},
    },
}

def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return json.loads(json.dumps(DEFAULT))

def save(s):
    with open(STATE, "w") as f:
        json.dump(s, f, indent=2)

def totals(s):
    keys = ["queued","conversations","qualified","pilots_booked","pilots_live","paid","revenue"]
    t = {k: 0 for k in keys}
    for d in s["days"]:
        for k in keys:
            t[k] += d.get(k, 0)
    return t

def bar(done, target, width=20):
    if target <= 0: return ""
    frac = min(1.0, done / target)
    filled = int(round(frac * width))
    return "█"*filled + "░"*(width-filled)

def render(s, today=None):
    today = today or date.today().isoformat()
    t = totals(s)
    start = datetime.fromisoformat(s["start"]).date()
    end   = datetime.fromisoformat(s["end"]).date()
    tod   = datetime.fromisoformat(today).date()
    total_days = (end - start).days + 1
    elapsed = max(0, (tod - start).days + 1)
    elapsed = min(elapsed, total_days)
    remaining = max(0, (end - tod).days)
    tgt = s["targets"]

    # pace: conversations expected by now (linear over the window)
    expected_conv = round(tgt["conversations"] * (elapsed/total_days)) if total_days else 0
    conv = t["conversations"]
    pace = "ON TRACK" if conv >= expected_conv else f"BEHIND by {expected_conv-conv}"
    if conv >= tgt["conversations"]: pace = "TARGET HIT"

    iv = s["interviews"]
    iv_done = sum(1 for v in iv.values() if v["done"])

    lines = []
    lines.append(f"# Teacher GTM — Progress Dashboard")
    lines.append("")
    lines.append(f"> Auto-rendered by `progress.py`. Do not hand-edit — edit via the CLI. "
                 f"Rendered for **{today}**.")
    lines.append("")
    lines.append(f"**Test:** {s['test_name']}  ·  **Window:** {s['start']} → {s['end']} "
                 f"({total_days} days)")
    lines.append(f"**Day {elapsed} of {total_days}**  ·  **{remaining} days left**  ·  "
                 f"Pace: **{pace}** (expected ~{expected_conv} conversations by now)")
    lines.append("")
    lines.append("## The gate")
    lines.append("")
    lines.append(f"| Metric | Done | Target | Progress | Left |")
    lines.append(f"|---|---|---|---|---|")
    def row(label, done, target, money=False):
        d = f"₹{done:,}" if money else str(done)
        tg = f"₹{target:,}" if money else str(target)
        left = max(0, target-done)
        return f"| {label} | **{d}** | {tg} | `{bar(done,target)}` | {left} |"
    lines.append(row("Conversations held", conv, tgt["conversations"]))
    lines.append(row("Qualified teachers", t["qualified"], round(tgt["conversations"]/2)))
    lines.append(row("Pilots booked", t["pilots_booked"], tgt["pilots_booked"]))
    lines.append(row("Pilots live (≥5 students)", t["pilots_live"], tgt["pilots_live"]))
    lines.append(f"| **PAID (cleared)** | **{t['paid']}** | {tgt['paid']} | "
                 f"`{bar(t['paid'],tgt['paid'])}` | {max(0,tgt['paid']-t['paid'])} |")
    lines.append(f"| Revenue cleared | **₹{t['revenue']:,}** | ₹{4999*tgt['paid']:,} | "
                 f"`{bar(t['revenue'],4999*tgt['paid'])}` | — |")
    lines.append("")
    lines.append(f"**Non-payer interviews (do first):** {iv_done}/3  "
                 + " · ".join(f"{k.title()}={'✅' if v['done'] else '⬜'}" for k,v in iv.items()))
    lines.append("")

    # what to do today
    per_workday = 10/5  # 10 conversations across ~5 working days a week
    lines.append("## What today needs")
    if t["paid"] >= tgt["paid"]:
        lines.append("- 🎉 **First payment cleared — PMF signal.** Move to Test v2 (see 00_TEST_SPEC.md).")
    elif remaining == 0:
        lines.append("- ⏰ **Test window closed — run the verdict** against 00_TEST_SPEC.md table. No silent extension.")
    else:
        need = max(0, expected_conv - conv)
        if iv_done < 3:
            lines.append(f"- ☎️ Book the remaining {3-iv_done} non-payer interview(s) — highest-value data.")
        lines.append(f"- 📞 Hold ~2 conversations today (pull 6 fresh numbers, dial). "
                     + (f"You're {need} behind pace — add a catch-up block." if need>0 else "You're on/ahead of pace."))
        lines.append("- 📝 Log every call SAME DAY (`python3 progress.py log ...` + verbatim objection in 03_CONVERSATION_LOG.md).")
    lines.append("")

    # daily history
    lines.append("## Daily history")
    lines.append("")
    lines.append("| Date | Queued | Conversations | Qualified | Pilots booked | Paid | Note |")
    lines.append("|---|---|---|---|---|---|---|")
    for d in sorted(s["days"], key=lambda x: x["date"]):
        lines.append(f"| {d['date']} | {d.get('queued',0)} | {d.get('conversations',0)} | "
                     f"{d.get('qualified',0)} | {d.get('pilots_booked',0)} | {d.get('paid',0)} | "
                     f"{d.get('note','')[:60]} |")
    if not s["days"]:
        lines.append("| _(no days logged yet)_ | | | | | | |")
    lines.append("")

    txt = "\n".join(lines)
    with open(DASH, "w") as f:
        f.write(txt+"\n")
    return txt

def cmd_log(s, a):
    d = a.date or date.today().isoformat()
    entry = {"date": d, "queued": a.queued, "conversations": a.conversations,
             "qualified": a.qualified, "pilots_booked": a.pilots_booked,
             "pilots_live": a.pilots_live, "paid": a.paid, "revenue": a.revenue,
             "note": a.note or ""}
    s["days"] = [x for x in s["days"] if x["date"] != d] + [entry]
    save(s)
    print(f"Logged {d}: {a.conversations} conversations, {a.paid} paid.")

def cmd_interview(s, a):
    who = a.who.lower()
    if who not in s["interviews"]:
        print(f"Unknown: {who}. Use aditya|kritansh|gauri."); return
    s["interviews"][who] = {"done": True, "note": a.note or ""}
    save(s)
    print(f"Interview logged: {who}.")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("show")
    lg = sub.add_parser("log")
    for k in ["queued","conversations","qualified","pilots_booked","pilots_live","paid","revenue"]:
        lg.add_argument(f"--{k.replace('_','-')}", dest=k, type=int, default=0)
    lg.add_argument("--date"); lg.add_argument("--note")
    iv = sub.add_parser("interview")
    iv.add_argument("--who", required=True); iv.add_argument("--note")
    a = p.parse_args()
    s = load()
    if a.cmd == "log": cmd_log(s, a)
    elif a.cmd == "interview": cmd_interview(s, a)
    # always re-render + print
    print(render(s))

if __name__ == "__main__":
    main()
