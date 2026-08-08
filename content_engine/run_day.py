#!/usr/bin/env python3
"""
content_engine/run_day.py  —  the DAILY DRIVER.
For plan day N: generate 4 content JSONs on the Gurukul VM (bank + gpt-5.5),
pull them, render locally (solution + quiz engines), and upload to YouTube.

Day is derived from an anchor date (day 1 = ANCHOR). Override with --day.
Honors a PAUSE file (content_engine/PAUSE) — if present, does nothing.

Usage:
  run_day.py                 # today's day per anchor, render + upload public
  run_day.py --day 2         # force day 2
  run_day.py --no-upload     # render only (dry run of content)
"""
import os, sys, json, subprocess, datetime, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
PLAN = os.path.join(BASE, "plan_15day.json")
PAUSE = os.path.join(BASE, "PAUSE")
LOG = os.path.join(BASE, "run_log.txt")
ANCHOR = datetime.date(2026, 7, 24)                 # plan day 1 = today

VM = "dk_trigun@20.219.2.53"
VM_KEY = os.path.expanduser("~/.ssh/gurukul_key")
VM_PY = "~/question_bank_engine/.venv/bin/python"
VM_SEL = "~/content_engine/bank_to_video.py"

SOL_DIR = os.path.join(REPO, "solution_video")
QUIZ_DIR = os.path.join(REPO, "quiz_video")

def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

def vm_generate(slot, out_vm):
    """Run bank_to_video.py on the VM, return the remote path."""
    q = slot
    args = [f'--format {q["format"]}', f'--exam "{q["exam"]}"', f'--subject "{q["subject"]}"',
            f'--chapter "{q["chapter"]}"', f'--out {out_vm}']
    if q["format"] == "quiz":
        args.append(f'--n {q.get("n_questions",3)}')
    cmd = f'cd ~/content_engine && {VM_PY} {VM_SEL} ' + " ".join(args)
    sh(["ssh", "-i", VM_KEY, "-o", "StrictHostKeyChecking=no", VM, cmd])

def pull(remote, local):
    sh(["scp", "-i", VM_KEY, "-o", "StrictHostKeyChecking=no", f"{VM}:{remote}", local])

def render_solution(cj, mp4):
    sh(["python3", "make_solution_video.py", cj, mp4], cwd=SOL_DIR)

def render_quiz(cj, mp4):
    sh(["python3", "make_quiz_video.py", cj, mp4], cwd=QUIZ_DIR)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=None)
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--privacy", default="public")
    a = ap.parse_args()

    if os.path.exists(PAUSE):
        log("PAUSE file present — skipping."); return
    day = a.day or ((datetime.date.today() - ANCHOR).days + 1)
    if not (1 <= day <= 15):
        log(f"day {day} outside 1..15 — nothing to do."); return
    plan = json.load(open(PLAN))
    slots = next(p["videos"] for p in plan if p["day"] == day)
    log(f"=== DAY {day} — {len(slots)} videos ===")

    items = []
    for i, slot in enumerate(slots):
        tag = f"day{day}_{slot['slot']}{i+1}"
        out_vm = f"/tmp/{tag}.json"
        try:
            log(f"[{tag}] generate {slot['format']} {slot['exam']}/{slot['subject']}/{slot['chapter']}")
            vm_generate(slot, out_vm)
            if slot["format"] == "solution":
                cj = os.path.join(SOL_DIR, "content", f"{tag}.json")
                pull(out_vm, cj)
                mp4 = os.path.join(SOL_DIR, "out", f"{tag}.mp4")
                log(f"[{tag}] render solution"); render_solution(f"content/{tag}.json", f"out/{tag}.mp4")
            else:
                cj = os.path.join(QUIZ_DIR, "content", f"{tag}.json")
                pull(out_vm, cj)
                mp4 = os.path.join(QUIZ_DIR, "out", f"{tag}.mp4")
                log(f"[{tag}] render quiz"); render_quiz(f"content/{tag}.json", f"out/{tag}.mp4")
            items.append({"mp4": mp4, "content_json": cj, "format": slot["format"],
                          "exam": slot["exam"], "subject": slot["subject"],
                          "chapter": slot["chapter"], "lang": "en"})
            log(f"[{tag}] OK")
        except Exception as e:
            log(f"[{tag}] FAILED: {e}")

    if not items:
        log("no videos produced — abort."); return
    items_path = os.path.join(BASE, f"items_day{day}.json")
    json.dump(items, open(items_path, "w"), indent=1)
    if a.no_upload:
        log(f"--no-upload: {len(items)} rendered, manifest {items_path}"); return
    log(f"uploading {len(items)} videos ({a.privacy})")
    sh(["python3", os.path.join(BASE, "publish.py"), "--items", items_path, "--privacy", a.privacy])
    log(f"=== DAY {day} DONE ===")

if __name__ == "__main__":
    main()
