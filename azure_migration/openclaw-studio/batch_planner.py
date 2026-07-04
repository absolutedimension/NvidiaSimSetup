#!/usr/bin/env python3
"""
Daily batch planner for Maya's outreach — picks today's call list (diversified across cities,
skips chains + already-called), writes a pending CSV, and Telegrams Deepak the list with
one-tap Approve / Skip links. Calls only start after approval (handled by maya_scheduler.py).
Run daily ~10:45 IST via cron.
Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAYA_APPROVE_KEY, MAYA_BASE, MAYA_DAILY
"""
import os, csv, json, time, urllib.request
from urllib.parse import urlencode
from collections import defaultdict, deque

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN"); TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")
APPROVE_KEY = os.environ.get("MAYA_APPROVE_KEY", "")
BASE = os.environ.get("MAYA_BASE", "https://gurukul.trigunai.com")
DAILY = int(os.environ.get("MAYA_DAILY", "25"))
INPUT = os.path.expanduser("~/leads/all_leads.csv")
RESULTS = os.path.expanduser("~/leads/call_results.csv")
PENDING_DIR = os.path.expanduser("~/leads/pending")
CHAINS = ("aakash", "physics wallah", "pw vidyapeeth", "physicswallah", "vedantu", "allen",
          "sri chaitanya", "narayana", "bansal classes", "resonance", "fiitjee", "byju",
          "unacademy", "motion education", "career point", "chaitanya", "vibrant academy",
          "reliable institute", "nucleus education")

def is_chain(n): n = (n or "").lower(); return any(c in n for c in CHAINS)
def called():
    if not os.path.exists(RESULTS): return set()
    return {r["phone"] for r in csv.DictReader(open(RESULTS, encoding="utf-8"))}
def today_ist(): return time.strftime("%Y-%m-%d", time.gmtime(time.time() + 5.5 * 3600))
def telegram(text):
    if not (TG_TOKEN and TG_CHAT): return
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
              data=json.dumps({"chat_id": TG_CHAT, "text": text[:4000], "disable_web_page_preview": True}).encode(),
              method="POST"); req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("telegram err", e)

def main():
    os.makedirs(PENDING_DIR, exist_ok=True)
    date = today_ist()
    done = called()
    leads = [l for l in csv.DictReader(open(INPUT, encoding="utf-8"))
             if l.get("phone") and l["phone"] not in done and not is_chain(l["name"])]
    if not leads:
        telegram("📞 Maya: no more uncalled leads — the list is exhausted. Add more via lead_extractor.py."); return

    # diversify: round-robin across cities so a day mixes locations/segments
    bycity = defaultdict(deque)
    for l in leads: bycity[l["city"]].append(l)
    cities = list(bycity); batch = []; i = 0
    while len(batch) < DAILY and any(bycity[c] for c in cities):
        c = cities[i % len(cities)]
        if bycity[c]: batch.append(bycity[c].popleft())
        i += 1

    path = os.path.join(PENDING_DIR, f"{date}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        cols = ["name", "phone", "segment", "city", "rating", "reviews", "address", "website"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for l in batch: w.writerow({k: l.get(k, "") for k in cols})
    json.dump({"date": date, "status": "awaiting_approval", "count": len(batch)},
              open(os.path.join(PENDING_DIR, "state.json"), "w"))

    q = urlencode({"key": APPROVE_KEY, "date": date})
    approve = f"{BASE}/maya-approve?{q}"; skip = f"{BASE}/maya-skip?{q}"
    lines = "\n".join(f"{n+1}. {l['name'][:34]} · {l['city']} · {l['phone']}" for n, l in enumerate(batch))
    telegram(f"📞 Maya — today's call list ({date}), {len(batch)} teachers:\n\n{lines}\n\n"
             f"✅ APPROVE & start (Maya calls 11am–5pm):\n{approve}\n\n❌ Skip today:\n{skip}")
    print(f"planned {len(batch)} for {date}, awaiting approval -> {path}")

if __name__ == "__main__":
    main()
