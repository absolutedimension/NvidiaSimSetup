#!/usr/bin/env python3
"""
TrigunAI Content Daily Engine — "what's due today".

Resolves today's content slot from the 30-day calendar and prints it, so the
daily run (SKILL.md §1) knows exactly what to produce.

Usage:
    python3 today.py                 # today
    python3 today.py 2026-06-24      # a specific date (plan ahead)
    python3 today.py --week          # print the whole current week

Calendar location (override with $CONTENT_CALENDAR):
    /Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/marketing_pipeline/03_CONTENT_CALENDAR_30DAY.md
"""
import os
import re
import sys
import datetime
import pathlib

DEFAULT_CALENDAR = (
    "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/"
    "marketing_pipeline/03_CONTENT_CALENDAR_30DAY.md"
)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Weekday -> (label, primary post, pillar, stage, CTA, special-day note)
RHYTHM = {
    0: ("Mon", "LinkedIn — Origin / founder story", "3 Origin", "1→3",
        "Soft (follow / series)", ""),
    1: ("Tue", "YouTube Short EN+HI — Wonder (cut from an episode)", "1 Wonder", "1→2",
        "Soft (free class in bio)", ""),
    2: ("Wed", "LinkedIn — Build / demystify", "2 Build", "2→3",
        "Soft (free class)", ""),
    3: ("Thu", "YouTube Short EN+HI — Build / curiosity", "2 Build", "2→3",
        "Soft + class teaser", ""),
    4: ("Fri", "LinkedIn — Free intro class INVITE + Email invite", "4 Offer", "3→4",
        "MEDIUM (register)", "🔑 SPECIAL: write + send the week's EMAIL invite. Fills Sat's room."),
    5: ("Sat", "FREE LIVE INTRO CLASS + a Wonder Short", "4 Proof", "4",
        "HARD (book 1:1)", "🎥 SPECIAL: RUN THE LIVE CLASS — the conversion engine. Book 1:1s after."),
    6: ("Sun", "LinkedIn — reflection / Origin-light", "3 Origin", "1→3",
        "None / soft", "📦 SPECIAL: BATCH next week — cut 3 Shorts (EN+HI), skim next week's hooks."),
}


def date_token(d: datetime.date) -> str:
    """Calendar first-cell token, e.g. 'Jun 22' (no zero-pad)."""
    return f"{MONTHS[d.month - 1]} {d.day}"


def find_calendar_row(cal_path: pathlib.Path, token: str):
    """Return the calendar table row containing the date token, or None."""
    if not cal_path.exists():
        return None
    needle = f"**{token} ·"
    for line in cal_path.read_text(encoding="utf-8").splitlines():
        if needle in line:
            return line.strip()
    return None


def parse_row(row: str):
    """Split a markdown table row into its cells (drop empty edges)."""
    cells = [c.strip() for c in row.split("|")]
    return [c for c in cells if c]


def print_day(d: datetime.date, cal_path: pathlib.Path):
    wd = d.weekday()
    label, post, pillar, stage, cta, special = RHYTHM[wd]
    token = date_token(d)
    print(f"\n📅  {d.isoformat()}  ·  {d.strftime('%A')}  ({token})")
    print("─" * 64)

    row = find_calendar_row(cal_path, token)
    if row:
        cells = parse_row(row)
        # Expected: [date, platform·format, pillar·stage, topic & hook, CTA]
        if len(cells) >= 5:
            print(f"  Platform/format : {cells[1]}")
            print(f"  Pillar · Stage  : {cells[2]}")
            print(f"  Topic & hook    : {cells[3]}")
            print(f"  CTA             : {cells[4]}")
        else:
            print("  " + row)
        print("  (source: 03_CONTENT_CALENDAR_30DAY.md)")
    else:
        # Outside the dated window — fall back to the weekday rhythm
        print("  ⚠ No dated calendar entry — using the weekday RHYTHM (roll-forward, SKILL §7):")
        print(f"  Primary post    : {post}")
        print(f"  Pillar · Stage  : {pillar} · {stage}")
        print(f"  CTA             : {cta}")

    if special:
        print(f"\n  {special}")

    print("\n  NEXT: load `content-marketing-emotion-connect` → lock feeling+hook+5 beats →")
    print("        produce → run checklist → render (Shorts) → distribute → log it.")


def main():
    args = [a for a in sys.argv[1:]]
    cal_path = pathlib.Path(os.environ.get("CONTENT_CALENDAR", DEFAULT_CALENDAR))

    week_mode = "--week" in args
    args = [a for a in args if not a.startswith("--")]

    try:
        base = datetime.date.fromisoformat(args[0]) if args else datetime.date.today()
    except ValueError:
        print(f"Bad date: {args[0]!r} — use YYYY-MM-DD")
        sys.exit(1)

    if week_mode:
        monday = base - datetime.timedelta(days=base.weekday())
        print(f"\n===== WEEK OF {monday.isoformat()} =====")
        for i in range(7):
            print_day(monday + datetime.timedelta(days=i), cal_path)
    else:
        print_day(base, cal_path)
    print()


if __name__ == "__main__":
    main()
