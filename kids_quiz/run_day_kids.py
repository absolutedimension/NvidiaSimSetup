#!/usr/bin/env python3
"""
run_day_kids.py — DAILY DRIVER for the Grade-3 Maths kids pipeline.

For plan day N (from ANCHOR):
  generate 4 content JSONs -> START EC2 (if off) -> render the 4 on EC2 in parallel ->
  pull mp4s -> STOP EC2 (only if we started it) -> publish to TrigunAI-KidsEducation -> log.

The plan loops every 15 days but the SEED is the absolute day number, so every cycle
produces FRESH questions (endless deep practice). Honors a PAUSE file.

  run_day_kids.py                      # today's day, render + publish public
  run_day_kids.py --day 3              # force plan day 3
  run_day_kids.py --no-upload          # render only (dry run)
  run_day_kids.py --privacy unlisted   # publish unlisted (safe test)
"""
import os, sys, json, time, subprocess, datetime, argparse, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
# aws binary: env override, else PATH, else the conductor venv (VM has no system aws)
AWS_BIN = os.environ.get("KIDS_AWS") or shutil.which("aws") \
    or (os.path.join(BASE, ".venv", "bin", "aws") if os.path.exists(os.path.join(BASE, ".venv", "bin", "aws")) else "aws")
PLAN = os.path.join(BASE, "plan_maths_15day.json")
PAUSE = os.path.join(BASE, "PAUSE")
LOG = os.path.join(BASE, "run_log.txt")
OUTD = os.path.join(BASE, "out", "daily")
ANCHOR = datetime.date(2026, 7, 31)                 # plan day 1

# EC2 render box (TrigunAI-Omniverse, stable Elastic IP)
IID = "i-047ebf759f2386e71"
REGION = "us-east-1"
HOST = "ubuntu@34.192.145.204"
KEY = os.path.expanduser("~/.ssh/trigunai_key.pem")
REMOTE = "~/kids_quiz"
SSH = ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15"]

def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')}  [kids] {msg}"
    print(line, flush=True); open(LOG, "a").write(line + "\n")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

def aws(*args):
    return subprocess.run([AWS_BIN] + list(args) + ["--region", REGION],
                          check=True, capture_output=True, text=True).stdout

def ec2_state():
    out = aws("ec2", "describe-instances", "--instance-ids", IID,
              "--query", "Reservations[0].Instances[0].State.Name", "--output", "text")
    return out.strip()

def ec2_start():
    st = ec2_state()
    if st == "running":
        log("EC2 already running — using it, will NOT stop it after (in use).")
        return False                        # we did not start it
    log(f"EC2 is {st}; starting…")
    aws("ec2", "start-instances", "--instance-ids", IID)
    aws("ec2", "wait", "instance-running", "--instance-ids", IID)
    for _ in range(40):                     # wait for SSH
        try:
            sh(SSH + [HOST, "true"], capture_output=True, timeout=20); log("EC2 SSH ready."); return True
        except Exception:
            time.sleep(6)
    raise SystemExit("EC2 started but SSH never came up")

def ec2_stop(we_started):
    if not we_started:
        log("Leaving EC2 running (it was already up before this run)."); return
    log("Stopping EC2 (we started it)…")
    aws("ec2", "stop-instances", "--instance-ids", IID)

HAS_ENGINE = os.path.exists(os.path.join(BASE, "make_kids_quiz_video.py"))

def sync_up(jobs):
    """From the Mac (engine present): rsync the whole engine+assets so EC2 stays current.
       From the VM (conductor, no engine): scp ONLY the day's content JSONs (never --delete
       the engine that lives on EC2)."""
    if HAS_ENGINE:
        sh(["rsync", "-az", "--delete",
            "-e", f"ssh -i {KEY} -o StrictHostKeyChecking=no",
            "--exclude", "out/", "--exclude", "__pycache__", "--exclude", "*.pyc",
            "--exclude", "preview_*.png",
            BASE + "/", f"{HOST}:{REMOTE}/"])
    else:
        sh(SSH + [HOST, f"mkdir -p {REMOTE}/content"])
        for j in jobs:
            sh(["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no",
                j["cj"], f"{HOST}:{REMOTE}/content/{j['cj_name']}"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=None)
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    a = ap.parse_args()

    if os.path.exists(PAUSE):
        log("PAUSE file present — doing nothing."); return
    os.makedirs(OUTD, exist_ok=True)
    plan = json.load(open(PLAN)); days = plan["days"]

    N = a.day if a.day else (datetime.date.today() - ANCHOR).days + 1
    if N < 1:
        log(f"Day {N} is before ANCHOR {ANCHOR} — nothing to do."); return
    plan_idx = (N - 1) % len(days)                  # loop the 15-day plan forever
    slots = days[plan_idx]["slots"]
    log(f"=== DAY {N} (plan day {plan_idx+1}) — {len(slots)} videos ===")

    # 1) generate content locally (seed = absolute day -> fresh questions each cycle)
    jobs = []
    for s in slots:
        cj = os.path.join(BASE, "content", f"auto_d{N:03d}_s{s['slot']}.json")
        seed = N * 100 + s["slot"]
        sh(["python3", os.path.join(BASE, "gen_content.py"), "--topic", s["topic"],
            "--adventure", s["adventure"], "--out", cj, "--seed", str(seed)])
        mp4 = os.path.join(OUTD, f"d{N:03d}_s{s['slot']}_{s['topic']}.mp4")
        jobs.append({"slot": s["slot"], "topic": s["topic"], "adventure": s["adventure"],
                     "cj": cj, "cj_name": os.path.basename(cj), "mp4": mp4,
                     "mp4_name": os.path.basename(mp4)})

    # 2) render on EC2
    started = ec2_start()
    try:
        sync_up(jobs)
        # render the 4 SEQUENTIALLY on the box (reliable for unattended cron — a parallel
        # `& … wait` can hang the ssh channel if an orphaned render from a prior run lingers).
        # EC2 renders each in ~1.5 min, so 4 ≈ 6 min with the box up only that long.
        cmd = "cd %s; mkdir -p out; " % REMOTE
        cmd += " ; ".join(
            f'echo ">> {j["mp4_name"]}"; python3 make_kids_quiz_video.py '
            f'content/{j["cj_name"]} out/{j["mp4_name"]} > out/{j["mp4_name"]}.log 2>&1' for j in jobs)
        cmd += " ; echo ALL_DONE"
        log("Rendering 4 videos on EC2 (sequential)…")
        sh(SSH + [HOST, cmd])
        for j in jobs:                              # pull each mp4
            sh(["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no",
                f"{HOST}:{REMOTE}/out/{j['mp4_name']}", j["mp4"]])
            sz = os.path.getsize(j["mp4"]) if os.path.exists(j["mp4"]) else 0
            log(f"  pulled {j['mp4_name']} ({sz//1024} KB)")
    finally:
        ec2_stop(started)

    # 3) publish
    items = [{"mp4": j["mp4"], "adventure": j["adventure"], "topic": j["topic"],
              "day": N, "slot": j["slot"]} for j in jobs if os.path.exists(j["mp4"])]
    ipath = os.path.join(OUTD, f"items_d{N:03d}.json")
    json.dump(items, open(ipath, "w"), indent=1)
    if a.no_upload:
        log(f"--no-upload: rendered {len(items)} videos, skipped publish. items={ipath}"); return
    log(f"Publishing {len(items)} videos to TrigunAI-KidsEducation ({a.privacy})…")
    sh(["python3", os.path.join(BASE, "publish_kids.py"), "--items", ipath, "--privacy", a.privacy])
    log(f"=== DAY {N} complete ===")

if __name__ == "__main__":
    main()
