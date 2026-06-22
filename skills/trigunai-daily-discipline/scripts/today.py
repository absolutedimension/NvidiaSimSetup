#!/usr/bin/env python3
"""
TrigunAI Daily Discipline — "what are my blocks today + how's my streak".

Prints the 5 daily work blocks, today's gate reminder (Fri invite / Sat class),
the current discipline STREAK and GATE-DAYS, and per-block 7-day adherence —
all read from daily_routine/ROUTINE_LOG.md.

Usage:
    python3 today.py                 # today's plan + scoreboard
    python3 today.py 2026-06-24      # a specific date (plan ahead)
    python3 today.py --new           # append today's blank row to the log
    python3 today.py --week          # the whole current week's gate reminders

Log location (override with $ROUTINE_LOG):
    <repo>/daily_routine/ROUTINE_LOG.md   (repo resolved from cwd, else default)
"""
import os
import re
import sys
import datetime
import pathlib

DEFAULT_REPO = pathlib.Path(
    "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup"
)

# block-key -> (number, label, hours, owning skill, done-criterion)
BLOCKS = [
    ("1 Marketing", 2, "content-daily-engine → emotion-connect → marketing",
     "≥1 asset POSTED publicly w/ intro-class CTA"),
    ("2 Robotics", 2, "trigunai-training",
     "a train run / checkpoint / trajectory / eval — path logged"),
    ("3 Course", 4, "trigunai-content-strategy + video-script-writer",
     "a WRITTEN module outline / script scene / flow design"),
    ("4 FlowArt/VR", 2, "trigunai-vr + production-video/music + trigunai-youtube",
     "a VR-to-Live build step OR a piece of channel content shipped"),
    ("5 TechScan", 1, "WebSearch / deep-research",
     "3 items + 1 'so-what for TrigunAI' line"),
]
GATE_BLOCKS = {"1 Marketing", "3 Course"}  # the two that move revenue

# Default Claude model per block when PLAN.md gives no @model tag.
# Cheapest-that-works: haiku=mechanical, sonnet=the middle, opus=hard reasoning only.
DEFAULT_MODEL = {
    "1 Marketing": "sonnet",
    "2 Robotics": "sonnet",   # running training is mechanical; escalate to opus for reward design/debug
    "3 Course": "sonnet",     # escalate to opus for curriculum/flow design or hard concepts
    "4 FlowArt/VR": "sonnet",
    "5 TechScan": "haiku",
}

# weekday -> special gate note
SPECIAL = {
    4: "🔑 FRIDAY — Block 1 IS the free-intro-class INVITE (LinkedIn + email). Fills Saturday's room.",
    5: "🎥 SATURDAY — Block 1 IS running the FREE LIVE INTRO CLASS (the conversion event). Book 1:1s after.",
    6: "📦 SUNDAY — weekly check: how many gate-days this week? Rebalance toward Blocks 1+3 if <4.",
}


def repo_root() -> pathlib.Path:
    cwd = pathlib.Path.cwd()
    for p in [cwd, *cwd.parents]:
        if (p / "daily_routine").exists() or (p / "project_hub").exists():
            return p
    return DEFAULT_REPO


def log_path() -> pathlib.Path:
    env = os.environ.get("ROUTINE_LOG")
    if env:
        return pathlib.Path(env)
    return repo_root() / "daily_routine" / "ROUTINE_LOG.md"


def plan_path() -> pathlib.Path:
    env = os.environ.get("ROUTINE_PLAN")
    if env:
        return pathlib.Path(env)
    return repo_root() / "daily_routine" / "PLAN.md"


PLAN_SECTION = re.compile(r"^##\s+(\d)\b")
TASK_LINE = re.compile(r"^\s*-\s*\[ \]\s*(.+)$")
MODEL_TAG = re.compile(r"@model:(haiku|sonnet|opus)", re.I)


def parse_plan(path: pathlib.Path):
    """Return {block-digit: (task_text, model_or_None)} = first unchecked task per block."""
    out = {}
    if not path.exists():
        return out
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = PLAN_SECTION.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur and cur not in out:
            t = TASK_LINE.match(line)
            if t:
                text = t.group(1).strip()
                mm = MODEL_TAG.search(text)
                model = mm.group(1).lower() if mm else None
                text = MODEL_TAG.sub("", text).strip()
                out[cur] = (text, model)
    return out


DAY_HDR = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")
DONE_LINE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(\d\s+\w[\w/]*)")


def parse_log(path: pathlib.Path):
    """Return {date(iso): set(of done block-keys)}."""
    days = {}
    if not path.exists():
        return days
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = DAY_HDR.match(line)
        if m:
            cur = m.group(1)
            days.setdefault(cur, set())
            continue
        if cur:
            d = DONE_LINE.match(line)
            if d and d.group(1).lower() == "x":
                # normalise key to "<n> <Name>"
                key = " ".join(d.group(2).split())
                days[cur].add(key)
    return days


def streak_and_gatedays(days, today):
    """Streak = consecutive logged-with-any-done days ending today/yesterday.
       Gate-days(7) = days in last 7 with BOTH gate blocks done."""
    # streak
    streak = 0
    d = today
    if today.isoformat() not in days or not days.get(today.isoformat()):
        d = today - datetime.timedelta(days=1)  # allow today not-yet-done
    while d.isoformat() in days and days[d.isoformat()]:
        streak += 1
        d -= datetime.timedelta(days=1)
    # gate-days in last 7
    gate = 0
    per_block = {b[0]: 0 for b in BLOCKS}
    for i in range(7):
        di = (today - datetime.timedelta(days=i)).isoformat()
        done = days.get(di, set())
        for b in BLOCKS:
            if b[0] in done:
                per_block[b[0]] += 1
        if GATE_BLOCKS.issubset(done):
            gate += 1
    return streak, gate, per_block


def skeleton(d: datetime.date) -> str:
    lines = [f"## {d.isoformat()} {d.strftime('%a')}  (gate: 0 paid)"]
    for key, hrs, _skill, _done in BLOCKS:
        pad = key.ljust(13)
        lines.append(f"- [ ] {pad}({hrs}h)   — target: …            → artifact:")
    lines.append("Reflection:")
    lines.append("Tomorrow's lead domino:")
    return "\n".join(lines) + "\n"


def cmd_audit(today: datetime.date, n: int, days):
    """Hard accountability scan of the last n days: flag MISSING / EMPTY / partial."""
    path = log_path()
    print(f"\n🔎  ACCOUNTABILITY AUDIT — last {n} days  (log: {path})")
    print("═" * 70)
    n_blocks = len(BLOCKS)
    misses = 0
    for i in range(n - 1, -1, -1):
        d = today - datetime.timedelta(days=i)
        iso = d.isoformat()
        done = days.get(iso)
        tag = f"{iso} {d.strftime('%a')}"
        if iso not in days:
            print(f"  ❌ {tag}   MISSING — no row was ever stamped")
            if i > 0:
                misses += 1
        elif not done:
            print(f"  ⚠️  {tag}   EMPTY — row stamped, 0 blocks shipped")
            if i > 0:
                misses += 1
        else:
            gate = "⭐both" if GATE_BLOCKS.issubset(done) else "✗gate"
            donekeys = " ".join(sorted(k.split()[0] for k in done))
            label = "FULL" if len(done) == n_blocks else f"partial {len(done)}/{n_blocks}"
            print(f"  ✅ {tag}   {label}  [{gate}]  blocks: {donekeys}")
    print("─" * 70)
    streak, gate, _ = streak_and_gatedays(days, today)
    print(f"  🔥 Streak: {streak}   ·   🎯 Gate-days (last 7): {gate}/7   ·   misses (excl. today): {misses}")
    if misses >= 3:
        print("  🚨 3+ misses — this is a commitment problem, not a scheduling one. Name it. Route to trigunai-ceo §7.")
    elif misses >= 1:
        print("  ⚠ Streak is broken. Make Deepak account for each gap IN WRITING before planning today (SKILL §A).")
    print("\n  Now: confront each gap (§A step 2) → verify ticks vs evidence (§A step 3) →")
    print("       close yesterday's row → THEN plan today.\n")


def cmd_new(d: datetime.date):
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if f"## {d.isoformat()}" in existing:
        print(f"Row for {d.isoformat()} already exists in {path} — not duplicating.")
        return
    header = "" if existing else "# TrigunAI — Daily Routine Log\n\n> Output > hours · gate-first (Blocks 1+3 are revenue). One row per day.\n\n"
    with path.open("a", encoding="utf-8") as f:
        if header:
            f.write(header)
        f.write(skeleton(d))
        f.write("\n")
    print(f"✅ Stamped {d.isoformat()} into {path}")


def print_day(d: datetime.date, days):
    wd = d.weekday()
    print(f"\n📅  {d.isoformat()}  ·  {d.strftime('%A')}")
    print("═" * 70)
    total = 0
    done_today = days.get(d.isoformat(), set())
    plan = parse_plan(plan_path())
    for key, hrs, skill, crit in BLOCKS:
        total += hrs
        mark = "✅" if key in done_today else "▢"
        gate = " ⭐" if key in GATE_BLOCKS else "  "
        digit = key.split()[0]
        task, model = plan.get(digit, (None, None))
        model = model or DEFAULT_MODEL.get(key, "sonnet")
        print(f"  {mark}{gate} {key.ljust(13)} {hrs}h  → {skill}")
        if task:
            print(f"         TODAY: {task}   [model: {model}]")
        else:
            print(f"         TODAY: (set one in daily_routine/PLAN.md)   [model: {model}]")
        print(f"         done = {crit}")
    print("─" * 70)
    print(f"  Total: {total}h   (⭐ = revenue gate block — protect first)")

    if wd in SPECIAL:
        print(f"\n  {SPECIAL[wd]}")

    streak, gate, per_block = streak_and_gatedays(days, d)
    print(f"\n  🔥 Streak: {streak} day(s) logged in a row"
          f"   ·   🎯 Gate-days (last 7, both 1+3): {gate}/7")
    adh = "  ".join(f"{k.split()[0]}:{per_block[k]}" for k, *_ in BLOCKS)
    print(f"  7-day adherence per block →  {adh}")
    if gate < 4:
        print("  ⚠ Gate-days < 4/7 — routine is drifting off revenue. Lean into Blocks 1 + 3.")

    print("\n  NEXT: `--new` to stamp today's row → run each block via its owning skill →")
    print("        fill the row tonight (artifact per block) → streak holds on OUTPUT, not hours.")


def main():
    args = sys.argv[1:]
    new_mode = "--new" in args
    week_mode = "--week" in args
    audit_mode = "--audit" in args
    # --audit may take an integer count (default 7)
    audit_n = 7
    if audit_mode:
        idx = args.index("--audit")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            audit_n = int(args[idx + 1])
            args.pop(idx + 1)
    pos = [a for a in args if not a.startswith("--") and not a.isdigit()]
    try:
        base = datetime.date.fromisoformat(pos[0]) if pos else datetime.date.today()
    except ValueError:
        print(f"Bad date: {pos[0]!r} — use YYYY-MM-DD")
        sys.exit(1)

    if new_mode:
        cmd_new(base)
        return

    days = parse_log(log_path())
    if audit_mode:
        cmd_audit(base, audit_n, days)
        return
    if week_mode:
        monday = base - datetime.timedelta(days=base.weekday())
        for i in range(7):
            print_day(monday + datetime.timedelta(days=i), days)
    else:
        print_day(base, days)
    print()


if __name__ == "__main__":
    main()
