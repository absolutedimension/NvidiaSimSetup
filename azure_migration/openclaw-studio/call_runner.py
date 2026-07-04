#!/usr/bin/env python3
"""
Maya batch call-runner — dials a chosen batch of leads through the realtime bot, one at a time
(gpt-realtime deployment is capacity-1, so calls are sequential), logs every outcome, and
Telegrams a summary. Runs on the Gurukul VM.

Env (~/voicebot_wa/wa_voice.env + plivo.env): PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Usage:
  python3 call_runner.py --city Patna --segment NEET/JEE --limit 25          # a batch
  python3 call_runner.py --city Kota --limit 10 --dry-run                     # preview only, no calls
  python3 call_runner.py --limit 30                                           # mixed 30
Outcome per lead appended to ~/leads/call_results.csv; already-called numbers are skipped on re-run.
"""
import os, sys, csv, json, time, argparse, urllib.request, base64, re
from urllib.parse import urlencode

# National chains / big brands — NOT our buyer (they're the competition). Exclude from calling.
CHAINS = ("aakash", "physics wallah", "pw vidyapeeth", "physicswallah", "vedantu", "allen",
          "sri chaitanya", "narayana", "bansal classes", "resonance", "fiitjee", "byju",
          "unacademy", "motion education", "career point", "aakash byju", "chaitanya",
          "vibrant academy", "reliable institute", "nucleus education")

def is_chain(name):
    n = (name or "").lower()
    return any(c in n for c in CHAINS)

PLIVO_ID = os.environ["PLIVO_AUTH_ID"]; PLIVO_TOKEN = os.environ["PLIVO_AUTH_TOKEN"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN"); TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")
FROM = os.environ.get("MAYA_FROM", "912264230921")
ANSWER_URL = os.environ.get("MAYA_ANSWER_URL", "https://gurukul.trigunai.com/realtime-answer")
TRANSCRIPT_DIR = os.path.expanduser("~/voicebot_wa/transcripts")
INPUT = os.path.expanduser("~/leads/all_leads.csv")
RESULTS = os.path.expanduser("~/leads/call_results.csv")
INTEREST_MARKERS = ("संपर्क कर", "registration", "पूरी जानकारी")   # Maya says these ONLY when interested

def _api(path, method, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"https://api.plivo.com/v1/Account/{PLIVO_ID}/{path}", data=data, method=method)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{PLIVO_ID}:{PLIVO_TOKEN}".encode()).decode())
    if data is not None: req.add_header("Content-Type", "application/json")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=20).read())
    except Exception as e:
        return {"error": str(e)[:80]}

def place(to, name="", city="", segment=""):
    qs = urlencode({"name": name, "city": city, "segment": segment})
    url = f"{ANSWER_URL}?{qs}" if qs else ANSWER_URL
    r = _api("Call/", "POST", {"from": FROM, "to": to, "answer_url": url, "answer_method": "POST"})
    return r.get("request_uuid")

def cdr(uuid):
    return _api(f"Call/{uuid}/", "GET")

def get_recording(uuid):
    r = _api(f"Recording/?call_uuid={uuid}", "GET")
    objs = r.get("objects", []) if isinstance(r, dict) else []
    return objs[0].get("recording_url", "") if objs else ""

def transcript(uuid):
    p = os.path.join(TRANSCRIPT_DIR, f"{uuid}.txt")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

def telegram(text):
    if not (TG_TOKEN and TG_CHAT): return
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
              data=json.dumps({"chat_id": TG_CHAT, "text": text[:4000]}).encode(), method="POST")
        req.add_header("Content-Type", "application/json"); urllib.request.urlopen(req, timeout=10)
    except Exception: pass

def already_called():
    if not os.path.exists(RESULTS): return set()
    return {r["phone"] for r in csv.DictReader(open(RESULTS, encoding="utf-8"))}

def ist_hour():
    return ((time.time() + 5.5 * 3600) % 86400) / 3600.0   # 0..24 IST

def office_ok(start=11.0, end=17.0):
    return start <= ist_hour() < end

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default=""); ap.add_argument("--segment", default="")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--gap", type=int, default=8, help="seconds between calls")
    ap.add_argument("--max-wait", type=int, default=150, help="max seconds to wait per call")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--input", default=INPUT, help="leads CSV to call from")
    ap.add_argument("--ignore-hours", action="store_true", help="skip the 11am-5pm IST guard (testing)")
    args = ap.parse_args()

    leads = list(csv.DictReader(open(args.input, encoding="utf-8")))
    done = already_called()
    # if a pre-planned batch file is passed, it's already filtered — take it as-is (still skip already-called)
    preplanned = args.input != INPUT
    batch = [l for l in leads
             if l.get("phone") and l["phone"] not in done
             and (preplanned or (
                 (not args.city or args.city.lower() in l["city"].lower())
                 and (not args.segment or args.segment.lower() in l["segment"].lower())
                 and not is_chain(l["name"])))][:args.limit]

    print(f"Batch: {len(batch)} leads  (city={args.city or 'any'} segment={args.segment or 'any'})")
    for l in batch:
        print(f"  · {l['city'][:12]:12} {l['segment'][:10]:10} {l['phone']}  {l['name'][:40]}")
    if args.dry_run:
        print("\n(dry-run — no calls placed)"); return
    if not batch:
        print("Nothing to call."); return

    # if approved before the office window, wait until 11am IST; if after 5pm, defer
    if not args.ignore_hours:
        while ist_hour() < 11.0:
            time.sleep(120)
        if ist_hour() >= 17.0:
            print("Past 5pm IST — deferring.")
            telegram("Maya: approved after 5pm — today's list will roll into the next window.")
            return

    # single-runner lock — never let two batches dial at once (realtime is capacity-1)
    LOCK = os.path.expanduser("~/leads/.runner.lock")
    if os.path.exists(LOCK):
        try:
            os.kill(int((open(LOCK).read().strip() or "0")), 0)
            print("Another call_runner is already active — exiting."); return
        except Exception:
            pass  # stale lock
    open(LOCK, "w").write(str(os.getpid()))

    new = not os.path.exists(RESULTS)
    rf = open(RESULTS, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(rf, fieldnames=["phone", "name", "segment", "city", "status", "duration", "interested"])
    if new: w.writeheader()

    tally = {"answered": 0, "interested": 0, "busy": 0, "no_answer": 0, "failed": 0}
    interested_leads = []
    for i, l in enumerate(batch, 1):
        if not args.ignore_hours and not office_ok():
            left = len(batch) - i + 1
            print(f"\n⏸ Outside 11am–5pm IST — stopping. {left} leads deferred to next batch.")
            telegram(f"⏸ Maya paused (outside 11am–5pm IST). {left} of today's leads not called — they'll roll into the next batch.")
            break
        uuid = place(l["phone"], l["name"], l["city"], l["segment"])
        print(f"[{i}/{len(batch)}] calling {l['phone']} {l['name'][:30]} ... ", end="", flush=True)
        if not uuid:
            w.writerow({**pick(l), "status": "failed", "duration": 0, "interested": ""}); rf.flush()
            tally["failed"] += 1; print("FAILED"); continue
        # wait for completion
        dur = None; cause = None; waited = 0
        while waited < args.max_wait:
            time.sleep(6); waited += 6
            d = cdr(uuid)
            if d.get("hangup_cause_name"):
                cause = d.get("hangup_cause_name"); dur = int(d.get("bill_duration") or 0); break
        interested = ""
        if dur and dur > 0:
            status = "answered"; tally["answered"] += 1
            t = transcript(uuid)
            if any(m in t for m in INTEREST_MARKERS):
                interested = "yes"; tally["interested"] += 1; interested_leads.append((l, uuid))
            else:
                interested = "no"
        elif cause == "Busy Line":
            status = "busy"; tally["busy"] += 1
        else:
            status = "no_answer"; tally["no_answer"] += 1
        w.writerow({**pick(l), "status": status, "duration": dur or 0, "interested": interested}); rf.flush()
        print(f"{status}" + (f" / interested={interested}" if interested else ""))
        time.sleep(args.gap)

    rf.close()
    try: os.remove(LOCK)
    except Exception: pass
    summary = (f"📞 Maya batch done ({args.city or 'mixed'} {args.segment}):\n"
               f"called {len(batch)} · answered {tally['answered']} · INTERESTED {tally['interested']} · "
               f"busy {tally['busy']} · no-answer {tally['no_answer']} · failed {tally['failed']}\n")
    if interested_leads:
        summary += "\n⭐ Interested (tap to hear the call):\n"
        for l, u in interested_leads:
            rec = get_recording(u)
            summary += f"• {l['name'][:35]} {l['phone']} ({l['city']})" + (f"\n  🎧 {rec}" if rec else "") + "\n"
    print("\n" + summary); telegram(summary)

def pick(l):
    return {"phone": l["phone"], "name": l["name"], "segment": l["segment"], "city": l["city"]}

if __name__ == "__main__":
    main()
