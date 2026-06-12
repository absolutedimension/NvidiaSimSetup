#!/usr/bin/env python3
"""
CEO Work Scanner
================
Scans ALL Claude Code session logs under ~/.claude/projects/ and distills them
into a single human-readable digest (WORK_LOG.md) that the CEO agent reads to
know what Deepak actually worked on and shipped — across every project, every
skill, every session tied to this login.

It does NOT use an LLM. It reads the structured fields Claude Code already
records in each transcript:
  - ai-title          -> Claude's own summary of the session
  - attributionSkill  -> which agent/skill did the work
  - first user msg    -> the task that was asked
  - Write/Edit calls  -> files that were actually created/changed (= shipped)
  - Bash 'git commit' -> hard evidence something landed

Usage:
    python3 ceo_work_scan.py                 # scan everything, write WORK_LOG.md
    python3 ceo_work_scan.py --days 7        # only sessions active in last N days
    python3 ceo_work_scan.py --project Nvidia  # filter project folder by substring

Output: project_hub/WORK_LOG.md  (chronological digest + rollups)
"""

import json
import os
import re
import sys
import glob
import argparse
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "WORK_LOG.md")

# Noise we don't want to treat as "the task the user asked"
SKIP_PREFIXES = ("<command-message>", "<command-name>", "<local-command",
                 "Caveat:", "<system-reminder>")


def clean_user_text(content):
    """Pull the first real human sentence out of a user message."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
            elif isinstance(b, str):
                parts.append(b)
        text = " ".join(parts)
    else:
        return None
    text = text.strip()
    if not text:
        return None
    # strip command wrappers / reminders
    for p in SKIP_PREFIXES:
        if text.startswith(p):
            # try to salvage anything after the tag block
            text = re.sub(r"<[^>]+>", " ", text)
            break
    text = re.sub(r"<system-reminder>.*?</system-reminder>", " ", text, flags=re.S)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 4:
        return None
    return text[:240]


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def scan_file(path):
    """Return a dict summarizing one session transcript, or None if empty."""
    title = None
    skills = set()
    first_task = None
    ts_first = None
    ts_last = None
    writes, edits, bashes = 0, 0, 0
    files = []
    commits = []
    project_cwd = None
    user_msgs = 0

    with open(path, "r", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue

            t = o.get("type")
            ts = parse_ts(o.get("timestamp"))
            if ts:
                ts_first = ts if ts_first is None or ts < ts_first else ts_first
                ts_last = ts if ts_last is None or ts > ts_last else ts_last
            if o.get("cwd") and not project_cwd:
                project_cwd = o["cwd"]
            if o.get("attributionSkill"):
                skills.add(o["attributionSkill"])

            if t == "ai-title":
                title = o.get("aiTitle") or title

            elif t == "user":
                msg = o.get("message", {})
                txt = clean_user_text(msg.get("content"))
                if txt:
                    user_msgs += 1
                    if first_task is None:
                        first_task = txt

            elif t == "assistant":
                for b in o.get("message", {}).get("content", []):
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name = b.get("name")
                    inp = b.get("input", {}) or {}
                    if name == "Write":
                        writes += 1
                        if inp.get("file_path"):
                            files.append(os.path.basename(inp["file_path"]))
                    elif name in ("Edit", "NotebookEdit"):
                        edits += 1
                        if inp.get("file_path"):
                            files.append(os.path.basename(inp["file_path"]))
                    elif name == "Bash":
                        bashes += 1
                        cmd = inp.get("command", "")
                        if "git commit" in cmd:
                            m = re.search(r"-m\s+[\"']([^\"']+)", cmd)
                            commits.append(m.group(1) if m else "git commit")

    if ts_first is None and title is None and not files and first_task is None:
        return None

    return {
        "path": path,
        "title": title,
        "skills": skills,
        "task": first_task,
        "ts_first": ts_first,
        "ts_last": ts_last,
        "writes": writes,
        "edits": edits,
        "bashes": bashes,
        "files": files,
        "commits": commits,
        "cwd": project_cwd,
        "user_msgs": user_msgs,
        "is_subagent": "/subagents/" in path,
    }


def project_name(cwd, path):
    if cwd:
        return os.path.basename(cwd.rstrip("/"))
    # derive from the encoded folder name
    folder = path.split("/projects/")[-1].split("/")[0]
    return folder.split("-")[-1] or folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="only sessions active within N days")
    ap.add_argument("--project", default="", help="filter by project folder substring")
    args = ap.parse_args()

    paths = glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True)
    if args.project:
        paths = [p for p in paths if args.project.lower() in p.lower()]

    cutoff = None
    if args.days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    sessions = []
    for p in paths:
        try:
            s = scan_file(p)
        except Exception as e:
            print(f"  ! skip {p}: {e}", file=sys.stderr)
            continue
        if not s:
            continue
        if cutoff and (s["ts_last"] is None or s["ts_last"] < cutoff):
            continue
        sessions.append(s)

    # only count top-level sessions in the main chronology; subagents roll into stats
    top = [s for s in sessions if not s["is_subagent"]]
    top.sort(key=lambda s: s["ts_last"] or datetime.min.replace(tzinfo=timezone.utc))

    # ---- rollups ----
    skill_counter = Counter()
    file_counter = Counter()
    proj_counter = Counter()
    all_commits = []
    for s in sessions:
        for sk in s["skills"]:
            skill_counter[sk] += 1
        for f in s["files"]:
            file_counter[f] += 1
        all_commits += s["commits"]
    for s in top:
        proj_counter[project_name(s["cwd"], s["path"])] += 1

    # ---- write digest ----
    now = datetime.now(timezone.utc)
    lines = []
    lines.append("# Work Log — auto-scanned from Claude session history")
    lines.append("")
    lines.append(f"> Generated {now.strftime('%Y-%m-%d %H:%M UTC')} by `ceo_work_scan.py`")
    scope = f"last {args.days} days" if args.days else "all time"
    lines.append(f"> Scope: **{scope}** · {len(top)} top-level sessions · "
                 f"{len(sessions)-len(top)} subagent runs · {len(all_commits)} git commits")
    lines.append("")
    lines.append("**This file is auto-generated. Do not edit by hand — rerun the scanner.**")
    lines.append("")

    # activity by week
    lines.append("## Activity by week")
    lines.append("")
    week_counter = Counter()
    for s in top:
        if s["ts_last"]:
            iso = s["ts_last"].isocalendar()
            week_counter[f"{iso[0]}-W{iso[1]:02d}"] += 1
    for wk in sorted(week_counter):
        bar = "█" * week_counter[wk]
        lines.append(f"- `{wk}`  {bar} {week_counter[wk]} sessions")
    lines.append("")

    # skill usage
    lines.append("## Where the effort went (sessions per skill/agent)")
    lines.append("")
    for sk, n in skill_counter.most_common():
        lines.append(f"- **{sk}** — {n}")
    if not skill_counter:
        lines.append("- (no skill attribution found)")
    lines.append("")

    # project split
    lines.append("## Sessions per project")
    lines.append("")
    for pr, n in proj_counter.most_common():
        lines.append(f"- {pr} — {n}")
    lines.append("")

    # git commits = hardest evidence of shipped work
    lines.append("## Shipped (git commits across all projects)")
    lines.append("")
    if all_commits:
        for c in all_commits:
            lines.append(f"- {c}")
    else:
        lines.append("- ⚠️ **No git commits found in any session.** "
                     "Work may be living as uncommitted files only.")
    lines.append("")

    # most-touched files
    lines.append("## Most-touched files (top 25)")
    lines.append("")
    for f, n in file_counter.most_common(25):
        lines.append(f"- `{f}` ×{n}")
    lines.append("")

    # chronological session log
    lines.append("## Session-by-session (newest first)")
    lines.append("")
    for s in reversed(top):
        d = s["ts_last"].strftime("%Y-%m-%d %a") if s["ts_last"] else "????-??-??"
        dur = ""
        if s["ts_first"] and s["ts_last"]:
            mins = int((s["ts_last"] - s["ts_first"]).total_seconds() // 60)
            dur = f"{mins}m" if mins < 90 else f"{mins//60}h{mins%60:02d}m"
        proj = project_name(s["cwd"], s["path"])
        title = s["title"] or "(untitled session)"
        sk = ", ".join(sorted(s["skills"])) or "—"
        lines.append(f"### {d} · {title}")
        lines.append(f"*{proj} · {dur} · skill: {sk}*")
        if s["task"]:
            lines.append(f"- **Asked:** {s['task']}")
        shipped = []
        if s["writes"]:
            shipped.append(f"{s['writes']} files written")
        if s["edits"]:
            shipped.append(f"{s['edits']} edits")
        if s["commits"]:
            shipped.append(f"{len(s['commits'])} commits")
        if shipped:
            lines.append(f"- **Did:** {', '.join(shipped)}")
        if s["files"]:
            uniq = list(dict.fromkeys(s["files"]))[:12]
            lines.append(f"- **Files:** {', '.join('`'+f+'`' for f in uniq)}")
        lines.append("")

    out = os.path.abspath(OUT_PATH)
    with open(out, "w") as fh:
        fh.write("\n".join(lines))

    print(f"✅ Scanned {len(sessions)} transcripts ({len(top)} sessions, "
          f"{len(sessions)-len(top)} subagents)")
    print(f"   {len(all_commits)} commits · {len(skill_counter)} skills · "
          f"{len(proj_counter)} projects")
    print(f"   Digest → {out}")


if __name__ == "__main__":
    main()
