#!/usr/bin/env python3
"""
Maya scheduler / approval endpoint. The daily Telegram message links here.
  GET /maya-approve?key=..&date=YYYY-MM-DD  -> launches call_runner on that day's pending batch
  GET /maya-skip?key=..&date=YYYY-MM-DD     -> marks the day skipped (no calls)
Runs on Gurukul :7864, fronted by Caddy /maya-* . Env: MAYA_APPROVE_KEY (+ runner needs PLIVO/TELEGRAM/AZURE).
Run: uvicorn maya_scheduler:app --host 0.0.0.0 --port 7864
"""
import os, json, subprocess
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

APPROVE_KEY = os.environ.get("MAYA_APPROVE_KEY", "")
PENDING_DIR = os.path.expanduser("~/leads/pending")
RUNNER = os.path.expanduser("~/call_runner.py")
STATE = os.path.join(PENDING_DIR, "state.json")

app = FastAPI()

def _page(title, body):
    return HTMLResponse(f"<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                        f"<h2>{title}</h2><p>{body}</p></body></html>")

@app.get("/maya-health")
def health():
    return {"ok": True, "agent": "maya-scheduler"}

@app.get("/maya-approve")
def approve(key: str = "", date: str = ""):
    if key != APPROVE_KEY:
        return PlainTextResponse("bad key", status_code=403)
    path = os.path.join(PENDING_DIR, f"{date}.csv")
    if not os.path.exists(path):
        return _page("No batch found", f"No planned list for {date}.")
    json.dump({"date": date, "status": "approved"}, open(STATE, "w"))
    # launch the runner in the background; it waits for the 11am window itself
    cmd = ("set -a; source ~/voicebot_wa/wa_voice.env; source ~/voicebot_wa/plivo.env; set +a; "
           f"python3 {RUNNER} --input {path} --limit 40 >> {PENDING_DIR}/{date}.run.log 2>&1")
    subprocess.Popen(["bash", "-lc", cmd])
    return _page("✅ Approved", f"Maya will call {date}'s list during 11am–5pm IST. "
                               "You'll get a summary on Telegram when done.")

@app.get("/maya-skip")
def skip(key: str = "", date: str = ""):
    if key != APPROVE_KEY:
        return PlainTextResponse("bad key", status_code=403)
    json.dump({"date": date, "status": "skipped"}, open(STATE, "w"))
    return _page("❌ Skipped", f"No calls today ({date}). The list rolls into the next batch.")
