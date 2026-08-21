#!/usr/bin/env python3
"""संकल्प daily gate — 5-second status read of the one live vow.

Reads NvidiaSimSetup/SANKALPA.md. Writes nothing. Prints: vow, days left,
streak, last 7 verdicts, and the frozen (सीमा) list.

    python3 skills/sankalp-daily-gate/scripts/gate.py
    python3 skills/sankalp-daily-gate/scripts/gate.py --frozen   # just the सीमा list
"""
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
VOW = ROOT / "SANKALPA.md"

ROW = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(\S+)\s*(.*)$")


def main() -> int:
    if not VOW.exists():
        print(f"no vow file at {VOW} — nothing is committed.")
        return 1
    text = VOW.read_text(encoding="utf-8")
    today = dt.date.today()

    m = re.search(r"\*\*काल \(expires\):\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    expiry = dt.date.fromisoformat(m.group(1)) if m else None

    m = re.search(r"### विषय.*?\n\n> \*\*(.+?)\*\*", text, re.S)
    vow_line = " ".join(m.group(1).split()) if m else "(विषय not found)"

    # log rows live after the पुनरावृत्ति heading
    tail = text.split("## पुनरावृत्ति", 1)[-1]
    rows = []
    for line in tail.splitlines():
        hit = ROW.match(line.strip())
        if hit:
            rows.append((hit.group(1), hit.group(2), hit.group(3).strip()))

    verdicts = [(d, v) for d, v, _ in rows if v.upper() in ("ON", "OFF", "अतिचार")]
    on = sum(1 for _, v in verdicts if v.upper() == "ON")
    off = sum(1 for _, v in verdicts if v.upper() == "OFF")
    streak = 0
    for _, v in reversed(verdicts):
        if v.upper() == "ON":
            streak += 1
        elif v.upper() == "OFF":
            break

    print("\n  संकल्प — the one live vow")
    print("  " + "-" * 58)
    print(f"  {vow_line}\n")

    if expiry:
        left = (expiry - today).days
        if left < 0:
            print(f"  ⚠️  EXPIRED {-left}d ago ({expiry}). Do NOT roll over.")
            print("      Re-take or drop it in writing before anything else.\n")
        else:
            print(f"  काल: {expiry}  ({left} days left)")

    print(f"  scored: {on} ON / {off} OFF        current streak: {streak}")

    if verdicts:
        print("  last 7: " + "  ".join(f"{d[5:]} {v}" for d, v in verdicts[-7:]))

    logged_today = any(d == today.isoformat() for d, _, _ in rows)
    open_today = [r for r in rows if r[0] == today.isoformat() and r[1].upper() not in ("ON", "OFF", "अतिचार")]
    print()
    if not logged_today:
        print("  ▸ TODAY IS UNNAMED. Name the ONE selling action before any build work.")
    elif open_today:
        print(f"  ▸ today declared: {open_today[0][2] or '(no action written)'}")
        print("    → still (pending). Close it tonight: ON / OFF / अतिचार.")
    else:
        print("  ▸ today is closed. Nothing further.")

    if "--frozen" in sys.argv or "-f" in sys.argv:
        block = re.search(r"\*\*Tier A.*?```\n(.*?)```", text, re.S)
        if block:
            print("\n  सीमा — frozen until the काल date:")
            for line in block.group(1).rstrip().splitlines():
                print("    " + line)
    else:
        print("\n  (--frozen to print the सीमा list)")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
