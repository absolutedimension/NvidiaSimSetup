#!/usr/bin/env python3
"""
caller_console.py — a caller's READ-ONLY window into Maya + a safe way to dial a CHOSEN list.
Deployed on the Gurukul VM at ~/caller_console.py. Touches NOTHING that serves live students:
it only reads the lead/result CSVs, fetches Plivo recording URLs, reads transcript files, and
(for `call`) shells out to the existing call_runner.py with an explicit --input list.

Usage (the caller's Claude runs these over SSH):
  python3 ~/caller_console.py leads   [--city Patna] [--segment NEET/JEE] [--limit 40]
      → uncalled candidate teachers (chains excluded), newest-first, to pick from.
  python3 ~/caller_console.py review  [--limit 25] [--interested]
      → recent CALLS with status + recording URL + a transcript snippet, to listen & decide.
  python3 ~/caller_console.py context <phone>
      → everything known about one teacher: lead row + every call + recordings + full transcript.
  python3 ~/caller_console.py call    <phone[,phone,...]>  [--dry-run]
      → dial exactly these numbers with Maya (builds a one-off --input CSV; respects the
        11am–5pm IST guard and the single-runner lock). This is the ONLY writing action.
"""
import os, sys, csv, json, argparse, base64, urllib.request, subprocess, tempfile, time

HOME = os.path.expanduser("~")

def _load_env(*paths):
    """Load KEY=VALUE lines from the VM's env files so Plivo creds are available
    however this tool is invoked (call_runner.py + Plivo recording lookups need them)."""
    for p in paths:
        p = os.path.expanduser(p)
        if not os.path.exists(p): continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            line = line[7:].strip() if line.lower().startswith("export ") else line
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env("~/voicebot_wa/plivo.env", "~/voicebot_wa/wa_voice.env")

LEADS = f"{HOME}/leads/all_leads.csv"
RESULTS = f"{HOME}/leads/call_results.csv"
TRANSCRIPTS = f"{HOME}/voicebot_wa/transcripts"
CALL_RUNNER = f"{HOME}/call_runner.py"
CHAINS = ("aakash","physics wallah","physicswallah","pw vidyapeeth","vedantu","allen",
          "sri chaitanya","narayana","bansal","resonance","fiitjee","byju","unacademy",
          "motion education","career point","chaitanya","vibrant academy","reliable institute","nucleus")

def is_chain(n): n=(n or "").lower(); return any(c in n for c in CHAINS)

def _plivo(path):
    pid = os.environ.get("PLIVO_AUTH_ID"); tok = os.environ.get("PLIVO_AUTH_TOKEN")
    if not (pid and tok): return {}
    req = urllib.request.Request(f"https://api.plivo.com/v1/Account/{pid}/{path}")
    req.add_header("Authorization","Basic "+base64.b64encode(f"{pid}:{tok}".encode()).decode())
    try: return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception: return {}

def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []

def called_phones():
    return {r.get("phone") for r in rows(RESULTS)}

def cmd_leads(a):
    done = called_phones()
    out = [l for l in rows(LEADS) if l.get("phone") and l["phone"] not in done
           and (not a.city or a.city.lower() in l.get("city","").lower())
           and (not a.segment or a.segment.lower() in l.get("segment","").lower())
           and not is_chain(l.get("name"))]
    out = out[:a.limit]
    print(f"UNCALLED CANDIDATES: {len(out)} (city={a.city or 'any'} segment={a.segment or 'any'})\n")
    for l in out:
        print(f"  {l['phone']:14} | {l.get('city','')[:10]:10} | {l.get('segment','')[:9]:9} | "
              f"⭐{l.get('rating','')}({l.get('reviews','')}) | {l.get('name','')[:46]}")

def _snippet(uuid, n=600):
    p = f"{TRANSCRIPTS}/{uuid}.txt"
    if not os.path.exists(p): return ""
    t = open(p, encoding="utf-8").read().strip()
    return t[:n] + (" …" if len(t) > n else "")

def cmd_review(a):
    rs = rows(RESULTS)
    if a.interested: rs = [r for r in rs if r.get("interested")=="yes"]
    rs = rs[-a.limit:][::-1]
    print(f"RECENT CALLS: {len(rs)}{' (interested only)' if a.interested else ''}\n")
    for r in rs:
        flag = "⭐INTERESTED" if r.get("interested")=="yes" else r.get("status","")
        print(f"• {r.get('name','')[:38]}  {r.get('phone','')}  [{flag}] dur={r.get('duration','0')}s  {r.get('city','')}")

def cmd_context(a):
    ph = a.phone.strip()
    lead = next((l for l in rows(LEADS) if l.get("phone")==ph), None)
    calls = [r for r in rows(RESULTS) if r.get("phone")==ph]
    print(f"===== CONTEXT: {ph} =====")
    if lead:
        print(f"Name : {lead.get('name','')}\nCity : {lead.get('city','')}  Segment: {lead.get('segment','')}")
        print(f"Rating: {lead.get('rating','')} ({lead.get('reviews','')} reviews)  Web: {lead.get('website','')}")
        print(f"Addr : {lead.get('address','')}")
    else:
        print("(not found in all_leads.csv)")
    print(f"\nCALL HISTORY: {len(calls)} call(s)")
    for r in calls:
        print(f"  status={r.get('status')} dur={r.get('duration')}s interested={r.get('interested')}")
    # recordings + transcript via Plivo (most recent call to this number)
    rec = _plivo(f"Recording/?to_number={ph}&limit=3")
    for o in (rec.get("objects") or []):
        print(f"  🎧 {o.get('recording_url','')}")
        u = o.get("call_uuid","")
        snip = _snippet(u, 4000)
        if snip: print(f"\n--- transcript {u} ---\n{snip}\n")

BATCH_CAP = 30  # hard ceiling per manual batch — protects against runaway dialing / Plivo cost

def cmd_batch(a):
    """Dial a fresh FILTERED batch from the pool via the existing call_runner (which handles
    dedup + the single-runner lock + the 11am-5pm IST window). Preview first, then confirm."""
    limit = min(a.limit, BATCH_CAP)
    if a.limit > BATCH_CAP:
        print(f"(capped {a.limit} -> {BATCH_CAP} per batch)\n")
    run = ["python3", CALL_RUNNER]
    if a.city: run += ["--city", a.city]
    if a.segment: run += ["--segment", a.segment]
    run += ["--limit", str(limit)]
    if a.reverse: run.append("--reverse")
    if a.dry_run: run.append("--dry-run")
    print("→ " + " ".join(run) + "\n")
    subprocess.run(run)

def cmd_call(a):
    phones = [p.strip() for p in a.phone.split(",") if p.strip()]
    lead_by = {l.get("phone"): l for l in rows(LEADS)}
    fd, path = tempfile.mkstemp(suffix=".csv", prefix="chosen_"); os.close(fd)
    with open(path,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name","phone","segment","city","rating","reviews","address","website"])
        w.writeheader()
        for ph in phones:
            l = lead_by.get(ph, {})
            w.writerow({"name":l.get("name",""),"phone":ph,"segment":l.get("segment",""),
                        "city":l.get("city",""),"rating":l.get("rating",""),"reviews":l.get("reviews",""),
                        "address":l.get("address",""),"website":l.get("website","")})
    print(f"Chosen list ({len(phones)}): {', '.join(phones)}\n")
    run = ["python3", CALL_RUNNER, "--input", path, "--limit", str(len(phones))]
    if a.dry_run: run.append("--dry-run")
    print("→ " + " ".join(run) + "\n")
    subprocess.run(run)

CALLER_LOG = f"{HOME}/leads/caller_log.csv"
LOG_COLS = ["date","teacher","phone","channel","reached","pain","objection","outcome","next_step","by"]

def cmd_log(a):
    """Append one outcome row to the SHARED log on the VM (Deepak + the field rep read it)."""
    ist = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 5.5*3600))
    new = not os.path.exists(CALLER_LOG)
    with open(CALLER_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLS)
        if new: w.writeheader()
        w.writerow({"date":ist,"teacher":a.teacher,"phone":a.phone,"channel":a.channel,
                    "reached":a.reached,"pain":a.pain,"objection":a.objection,
                    "outcome":a.outcome,"next_step":a.next,"by":a.by})
    print(f"✅ logged: {a.teacher or a.phone} · {a.outcome} ({ist})")

def cmd_history(a):
    rs = rows(CALLER_LOG)
    if a.phone: rs = [r for r in rs if r.get("phone")==a.phone]
    rs = rs[-a.limit:][::-1]
    print(f"CALL LOG: {len(rs)} row(s)\n")
    for r in rs:
        print(f"• {r.get('date','')} [{r.get('outcome','')}] {r.get('teacher','')[:34]} {r.get('phone','')} "
              f"({r.get('channel','')}, by {r.get('by','')})")
        if r.get('pain'): print(f"    pain: {r['pain'][:90]}")
        if r.get('next_step'): print(f"    next: {r['next_step'][:90]}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("leads");   p.add_argument("--city",default=""); p.add_argument("--segment",default=""); p.add_argument("--limit",type=int,default=40)
    p = sub.add_parser("review");  p.add_argument("--limit",type=int,default=25); p.add_argument("--interested",action="store_true")
    p = sub.add_parser("context"); p.add_argument("phone")
    p = sub.add_parser("call");    p.add_argument("phone"); p.add_argument("--dry-run",action="store_true")
    p = sub.add_parser("batch");   p.add_argument("--city",default=""); p.add_argument("--segment",default=""); p.add_argument("--limit",type=int,default=15); p.add_argument("--reverse",action="store_true"); p.add_argument("--dry-run",action="store_true")
    p = sub.add_parser("log")
    p.add_argument("--teacher",default=""); p.add_argument("--phone",default=""); p.add_argument("--channel",default="phone")
    p.add_argument("--reached",default=""); p.add_argument("--pain",default=""); p.add_argument("--objection",default="")
    p.add_argument("--outcome",default=""); p.add_argument("--next",default=""); p.add_argument("--by",default="")
    p = sub.add_parser("history"); p.add_argument("--phone",default=""); p.add_argument("--limit",type=int,default=25)
    a = ap.parse_args()
    {"leads":cmd_leads,"review":cmd_review,"context":cmd_context,"call":cmd_call,"batch":cmd_batch,
     "log":cmd_log,"history":cmd_history}[a.cmd](a)

if __name__ == "__main__":
    main()
