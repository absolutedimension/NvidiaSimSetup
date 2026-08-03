#!/usr/bin/env python3
"""
batch_all.py — ONE-TIME batch: render EVERY video in the plan on EC2 with parallelism,
pull them, STOP EC2, then upload them all UNLISTED to the kids channel for review.

  python3 batch_all.py                      # all 60, 6-way parallel, upload unlisted
  python3 batch_all.py --parallel 6 --privacy unlisted
  python3 batch_all.py --no-upload          # render + pull only

Renders run detached on EC2 (nohup + xargs -P N) so a dropped ssh doesn't matter; this
script polls for completion. Meant to run from the Mac (engine present) — it rsyncs the
whole engine so EC2 is current.
"""
import os, sys, json, time, subprocess, argparse, shutil, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(BASE, "plan_maths_15day.json")
OUTD = os.path.join(BASE, "out", "batch")
LOG = os.path.join(BASE, "out", "batch_log.txt")

IID = "i-047ebf759f2386e71"; REGION = "us-east-1"
HOST = "ubuntu@34.192.145.204"; KEY = os.path.expanduser("~/.ssh/trigunai_key.pem")
REMOTE = "~/kids_quiz"
SSH = ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=20",
       "-o", "ServerAliveInterval=30"]
AWS = shutil.which("aws") or "aws"

def log(m):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')}  [batch] {m}"
    print(line, flush=True); open(LOG, "a").write(line + "\n")

def sh(cmd, **kw): return subprocess.run(cmd, check=True, **kw)
def aws(*a): return subprocess.run([AWS] + list(a) + ["--region", REGION], check=True,
                                   capture_output=True, text=True).stdout.strip()

def ec2_state(): return aws("ec2", "describe-instances", "--instance-ids", IID,
                            "--query", "Reservations[0].Instances[0].State.Name", "--output", "text")
def ec2_start():
    if ec2_state() != "running":
        log("starting EC2…"); aws("ec2", "start-instances", "--instance-ids", IID)
        aws("ec2", "wait", "instance-running", "--instance-ids", IID)
    for _ in range(40):
        try: sh(SSH + [HOST, "true"], capture_output=True, timeout=20); log("EC2 SSH ready."); return
        except Exception: time.sleep(6)
    raise SystemExit("EC2 SSH never came up")
def ec2_stop():
    log("stopping EC2 (batch done)…"); aws("ec2", "stop-instances", "--instance-ids", IID)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--keep-ec2", action="store_true", help="do not stop EC2 at the end")
    a = ap.parse_args()
    os.makedirs(OUTD, exist_ok=True)
    plan = json.load(open(PLAN))

    # 1) generate ALL content
    jobs = []
    for day in plan["days"]:
        N = day["day"]
        for s in day["slots"]:
            base = f"batch_d{N:02d}_s{s['slot']}_{s['topic']}"
            cj = os.path.join(BASE, "content", base + ".json")
            sh(["python3", os.path.join(BASE, "gen_content.py"), "--topic", s["topic"],
                "--adventure", s["adventure"], "--out", cj, "--seed", str(N*100+s["slot"])])
            jobs.append({"day": N, "slot": s["slot"], "topic": s["topic"], "adventure": s["adventure"],
                         "cj": cj, "base": base, "mp4": os.path.join(OUTD, base + ".mp4")})
    log(f"generated {len(jobs)} content sets")

    # 2) render on EC2, {parallel} at a time (detached; we poll)
    ec2_start()
    sh(["rsync", "-az", "--delete", "-e", f"ssh -i {KEY} -o StrictHostKeyChecking=no",
        "--exclude", "out/", "--exclude", "__pycache__", "--exclude", "*.pyc",
        "--exclude", "preview_*.png", "--exclude", ".venv", BASE + "/", f"{HOST}:{REMOTE}/"])
    # launch the clean render script detached (survives ssh drop); we poll for BATCH_DONE
    sh(SSH + [HOST, f"cd {REMOTE} && chmod +x render_batch.sh && "
                    f"nohup bash render_batch.sh {a.parallel} >/dev/null 2>&1 & echo LAUNCHED"])
    log(f"rendering {len(jobs)} on EC2, {a.parallel}-way parallel…")
    total = len(jobs)
    while True:
        time.sleep(45)
        try:
            done = int(sh(SSH + [HOST, f"ls {REMOTE}/out/batch_*.mp4 2>/dev/null | wc -l"],
                          capture_output=True, text=True).stdout.strip() or "0")
            fin = sh(SSH + [HOST, f"test -f {REMOTE}/out/BATCH_DONE && echo yes || echo no"],
                     capture_output=True, text=True).stdout.strip()
        except Exception as e:
            log(f"poll hiccup ({e}); retrying"); continue
        log(f"  rendered {done}/{total}")
        if fin == "yes":
            log(f"render complete ({done}/{total})"); break

    # 3) pull all
    for j in jobs:
        try:
            sh(["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no",
                f"{HOST}:{REMOTE}/out/{j['base']}.mp4", j["mp4"]], capture_output=True)
        except Exception:
            log(f"  !! pull failed for {j['base']}")
    got = [j for j in jobs if os.path.exists(j["mp4"]) and os.path.getsize(j["mp4"]) > 0]
    log(f"pulled {len(got)}/{total} videos")

    # 4) stop EC2
    if not a.keep_ec2: ec2_stop()

    # 5) upload unlisted
    items = [{"mp4": j["mp4"], "adventure": j["adventure"], "topic": j["topic"],
              "day": j["day"], "slot": j["slot"]} for j in got]
    ipath = os.path.join(OUTD, "items_all.json"); json.dump(items, open(ipath, "w"), indent=1)
    if a.no_upload:
        log(f"--no-upload: {len(got)} rendered. items={ipath}"); return
    log(f"uploading {len(got)} videos {a.privacy} to kids channel…")
    sh(["python3", os.path.join(BASE, "publish_kids.py"), "--items", ipath, "--privacy", a.privacy])
    log("=== BATCH COMPLETE ===")

if __name__ == "__main__":
    main()
