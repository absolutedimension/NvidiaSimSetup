#!/usr/bin/env python3
"""
wa_send.py — send a WhatsApp message via the Acharya (Meta Cloud API) channel to a specific
student, a list of numbers, a course cohort, or ALL real students.

Uses an APPROVED Meta template by default (gurukul_announce) so the message DELIVERS EVEN IF the
student's 24-hour WhatsApp window is closed. Free-form text (--mode freeform) only reaches students
who messaged Acharya within the last 24h — outside that window Meta rejects it ("Re-engagement message").

Env:      ~/.openclaw/wa_cloud.env   (META_TOKEN, PHONE_NUMBER_ID, GRAPH_VERSION)
Students: ~/.openclaw/students/<phone>.json  (name, course)
Log:      ~/leads/wa_announce_log.csv

Approved templates (each has one body variable {{1}}):
  gurukul_announce  (MARKETING) — default; student-facing announcements. Respects opt-outs/marketing limits.
  gurukul_recall    (MARKETING) — "Quick recall, no peeking: {{1}}"
  admin_alert       (UTILITY)   — ONLY for genuine non-promotional notifications (do NOT use for promos).

Usage:
  python3 wa_send.py --to 916396844362 --msg "..."              # one student (personalised, template)
  python3 wa_send.py --to 91... --to 91... --msg "..."          # several specific numbers
  python3 wa_send.py --course agentic --msg "New lesson is live!"
  python3 wa_send.py --all --msg "Classes resume Monday." --dry-run   # preview recipients, send nothing
  python3 wa_send.py --to 91... --msg "quick note" --mode freeform    # only if their 24h window is open
"""
import os, sys, csv, json, re, time, argparse, urllib.request, urllib.error

ENV = os.path.expanduser("~/.openclaw/wa_cloud.env")
STUDENTS = os.path.expanduser("~/.openclaw/students")
LOG = os.path.expanduser("~/leads/wa_announce_log.csv")

# synthetic / test accounts to never include in --all / --course
TEST_NUMBERS = {"911234500099", "919999888777",
                "919000000001", "919000000002", "919000000003",
                "919000000004", "919000000005", "919000000006"}

def load_env():
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.replace("export ", "").strip(), v.strip())

def real_students():
    out = []
    for fn in os.listdir(STUDENTS):
        if not fn.endswith(".json") or fn.startswith("web_") or fn.startswith("_"):
            continue
        phone = fn[:-5]
        if not phone.isdigit() or phone in TEST_NUMBERS:
            continue
        try:
            p = json.load(open(os.path.join(STUDENTS, fn)))
        except Exception:
            continue
        out.append({"phone": phone, "name": (p.get("name") or "").strip(), "course": p.get("course", "")})
    return out

def send(to, name, msg, mode, template, use_name):
    TOKEN = os.environ["META_TOKEN"]; PID = os.environ["PHONE_NUMBER_ID"]
    GV = os.environ.get("GRAPH_VERSION", "v21.0")
    body = (f"Namaste {name}! " + msg) if (use_name and name) else msg
    body = " ".join(body.split())  # collapse whitespace/newlines (Meta rejects newlines in template params)
    if mode == "freeform":
        payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body[:4096]}}
    else:
        payload = {"messaging_product": "whatsapp", "to": to, "type": "template",
                   "template": {"name": template, "language": {"code": "en_US"},
                                "components": [{"type": "body",
                                                "parameters": [{"type": "text", "text": body}]}]}}
    req = urllib.request.Request(f"https://graph.facebook.com/{GV}/{PID}/messages",
                                 data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        return True, r.get("messages", [{}])[0].get("id", "")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return False, str(e)[:200]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", action="append", default=[], help="specific number(s), repeatable")
    ap.add_argument("--all", action="store_true", help="every real student in the store")
    ap.add_argument("--course", default="", help="only students whose profile course == this slug")
    ap.add_argument("--msg", required=True, help="message body (goes into template {{1}} or free-form text)")
    ap.add_argument("--template", default="gurukul_announce", help="approved template name")
    ap.add_argument("--mode", choices=["template", "freeform"], default="template")
    ap.add_argument("--no-name", action="store_true", help="do NOT prepend 'Namaste <name>! '")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    load_env()

    if args.to:
        known = {s["phone"]: s for s in real_students()}
        recips = [known.get(t, {"phone": t, "name": "", "course": ""}) for t in args.to]
    elif args.all or args.course:
        recips = real_students()
        if args.course:
            recips = [s for s in recips if s["course"] == args.course]
    else:
        print("Pick recipients: --to <num> (repeatable), --all, or --course <slug>."); sys.exit(2)

    print(f"Recipients: {len(recips)}  | mode={args.mode} template={args.template if args.mode=='template' else '-'}")
    for s in recips:
        print(f"  · {s['phone']:14} {s.get('name','')[:24]:24} {s.get('course','')}")
    if args.dry_run:
        print("\n(dry-run — nothing sent)"); return
    if not recips:
        print("No recipients."); return

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    new = not os.path.exists(LOG)
    lf = open(LOG, "a", newline="", encoding="utf-8"); w = csv.writer(lf)
    if new: w.writerow(["ts_ist", "phone", "name", "mode", "template", "ok", "result"])
    ok = fail = 0
    for s in recips:
        good, res = send(s["phone"], s.get("name", ""), args.msg, args.mode, args.template, not args.no_name)
        ts = time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 5.5 * 3600))
        w.writerow([ts, s["phone"], s.get("name", ""), args.mode,
                    args.template if args.mode == "template" else "", good, res]); lf.flush()
        print(f"  {'✅' if good else '❌'} {s['phone']} {s.get('name','')[:18]:18} {res}")
        ok += good; fail += not good
        time.sleep(1)  # gentle pacing
    lf.close()
    print(f"\nDone: {ok} sent, {fail} failed.  Log: {LOG}")

if __name__ == "__main__":
    main()
