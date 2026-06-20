#!/usr/bin/env python3
"""
TrigunAI multi-channel marketing publisher.

One CLI to push content to the channels an agent can SAFELY automate:
  - email     (Azure Communication Services — connection string OR `az login`)
  - telegram  (Bot API)
  - discord   (webhook)
  - youtube   (delegates to ../youtube_series/yt_upload.py)
  - post      (fan-out: one content item -> many channels, from a manifest)
  - campaign  (run a list of posts / an email send, from a manifest)

DESIGN RULES (read the skill SKILL.md for the why):
  * SAFETY DEFAULT = DRY RUN. Nothing is sent unless you pass --send.
  * This tool does PUBLISHING (broadcast) only. It does NOT do 1:1 cold DMs on
    LinkedIn / Instagram / WhatsApp — that violates their ToS and is also your
    human conversion edge. Keep the close human.
  * Every send is logged to publish_state.json so re-runs are visible.

Config: copy config.example.env -> .env (or export the vars). Keys:
  ACS_CONNECTION_STRING   (preferred)   OR   ACS_ENDPOINT (+ `az login`)
  ACS_SENDER              e.g. DoNotReply@trigunai.com  (a verified ACS sender)
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (channel @handle or numeric id)
  DISCORD_WEBHOOK_URL

Usage:
  python3 publish.py email --to lists/waitlist.csv --subject "Free VR class Fri" \\
        --html emails/free_class_invite.html --send
  python3 publish.py telegram --text "New: build a VR app live with AI. Free class Fri." --send
  python3 publish.py discord  --text "..." --file teaser.mp4 --send
  python3 publish.py post     --manifest campaigns/wk0_short_proof.json --send
  python3 publish.py campaign --manifest campaigns/free_class_invite.json --send
  python3 publish.py youtube  -- run yt_manifest.json --only ep08      # passthrough
"""
import os, sys, csv, json, time, argparse, subprocess, datetime, mimetypes

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "publish_state.json")

# --- env loading (simple .env, no dependency) ---------------------------------
def _load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env()

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_state(channel, ident, detail):
    s = json.load(open(STATE)) if os.path.exists(STATE) else []
    s.append({"ts": now(), "channel": channel, "id": ident, "detail": detail})
    json.dump(s, open(STATE, "w"), indent=2)

def need(var):
    v = os.environ.get(var)
    if not v:
        sys.exit(f"!! missing env var {var} — set it in marketing/.env (see config.example.env)")
    return v

# --- recipient parsing --------------------------------------------------------
def _resolve(path):
    """Resolve a manifest-referenced path: as given, else relative to marketing/ root."""
    if not path:
        return path
    if os.path.exists(path):
        return path
    cand = os.path.join(HERE, path)
    return cand if os.path.exists(cand) else path

def parse_recipients(spec):
    """spec can be: a .csv path (col 'email'), a .json list, or comma-separated addrs."""
    spec = _resolve(spec)
    if os.path.exists(spec):
        if spec.endswith(".csv"):
            rows = list(csv.DictReader(open(spec)))
            col = next((c for c in (rows[0].keys() if rows else []) if c.lower() in ("email", "e-mail", "address")), None)
            if not col:
                sys.exit(f"!! {spec} has no 'email' column")
            return [r[col].strip() for r in rows
                    if r.get(col, "").strip() and "@" in r[col] and not r[col].strip().startswith("#")]
        if spec.endswith(".json"):
            data = json.load(open(spec))
            return [d if isinstance(d, str) else d.get("email") for d in data]
    return [a.strip() for a in spec.split(",") if a.strip()]

def read_body(path_or_text):
    p = _resolve(path_or_text)
    if p and os.path.exists(p):
        return open(p, encoding="utf-8").read()
    return path_or_text or ""

# --- EMAIL: Azure Communication Services --------------------------------------
def send_email(to_spec, subject, html=None, text=None, send=False):
    recips = parse_recipients(to_spec)
    html = read_body(html) if html else None
    text = read_body(text) if text else (None if html else "")
    print(f"[email] recipients={len(recips)}  subject={subject!r}")
    if not send:
        print(f"[email] DRY RUN — would send to: {', '.join(recips[:5])}{' ...' if len(recips) > 5 else ''}")
        print("[email] add --send to actually send.")
        return
    sender = need("ACS_SENDER")
    try:
        from azure.communication.email import EmailClient
    except ImportError:
        sys.exit("!! pip install azure-communication-email  (and azure-identity if using az login)")
    conn = os.environ.get("ACS_CONNECTION_STRING")
    if conn:
        client = EmailClient.from_connection_string(conn)
    else:
        endpoint = need("ACS_ENDPOINT")
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError:
            sys.exit("!! pip install azure-identity  (needed for the `az login` auth path)")
        client = EmailClient(endpoint, DefaultAzureCredential())
    sent = 0
    for addr in recips:
        content = {"subject": subject}
        if text is not None: content["plainText"] = text
        if html is not None: content["html"] = html
        msg = {"senderAddress": sender, "recipients": {"to": [{"address": addr}]}, "content": content}
        try:
            poller = client.begin_send(msg)
            res = poller.result()
            sent += 1
            print(f"  -> {addr}  ({getattr(res, 'get', lambda *_: '')('status') or 'queued'})")
            time.sleep(0.3)  # gentle throttle
        except Exception as e:
            print(f"  !! {addr}  FAILED: {e}")
    log_state("email", subject, f"{sent}/{len(recips)} sent")
    print(f"[email] sent {sent}/{len(recips)}")

# --- TELEGRAM -----------------------------------------------------------------
def send_telegram(text, photo=None, video=None, send=False):
    print(f"[telegram] media={'video' if video else 'photo' if photo else 'none'}")
    if not send:
        print(f"[telegram] DRY RUN — text:\n  {text[:200]}")
        print("[telegram] add --send to actually post.")
        return
    import requests
    token = need("TELEGRAM_BOT_TOKEN"); chat = need("TELEGRAM_CHAT_ID")
    base = f"https://api.telegram.org/bot{token}"
    if video:
        r = requests.post(f"{base}/sendVideo", data={"chat_id": chat, "caption": text, "parse_mode": "HTML"},
                          files={"video": open(video, "rb")}, timeout=300)
    elif photo:
        r = requests.post(f"{base}/sendPhoto", data={"chat_id": chat, "caption": text, "parse_mode": "HTML"},
                          files={"photo": open(photo, "rb")}, timeout=120)
    else:
        r = requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": text, "parse_mode": "HTML"}, timeout=30)
    ok = r.ok and r.json().get("ok")
    print(f"[telegram] {'OK' if ok else 'FAILED: ' + r.text[:300]}")
    log_state("telegram", text[:40], "ok" if ok else r.text[:120])

# --- DISCORD (webhook) --------------------------------------------------------
def send_discord(text, file=None, send=False):
    print(f"[discord] file={'yes' if file else 'no'}")
    if not send:
        print(f"[discord] DRY RUN — text:\n  {text[:200]}")
        print("[discord] add --send to actually post.")
        return
    import requests
    url = need("DISCORD_WEBHOOK_URL")
    if file:
        r = requests.post(url, data={"payload_json": json.dumps({"content": text})},
                          files={"file": (os.path.basename(file), open(file, "rb"))}, timeout=120)
    else:
        r = requests.post(url, json={"content": text}, timeout=30)
    ok = r.status_code in (200, 204)
    print(f"[discord] {'OK' if ok else 'FAILED: ' + r.text[:300]}")
    log_state("discord", text[:40], "ok" if ok else r.text[:120])

# --- YOUTUBE (delegate to the existing uploader) ------------------------------
def youtube_passthrough(rest):
    up = os.path.join(HERE, "..", "youtube_series", "yt_upload.py")
    if not os.path.exists(up):
        sys.exit(f"!! uploader not found at {up}")
    subprocess.run([sys.executable, up] + rest, cwd=os.path.dirname(up))

# --- POST: fan one item to many channels --------------------------------------
def run_post(manifest, send=False):
    m = json.load(open(manifest))
    text = m.get("text", "")
    if m.get("cta"):
        text = f"{text}\n\n{m['cta']}"
    media = m.get("media")
    for ch in m.get("channels", []):
        print(f"--- {ch} ---")
        if ch == "telegram":
            send_telegram(text, video=media if media and media.endswith((".mp4", ".mov")) else None,
                          photo=media if media and media.endswith((".png", ".jpg", ".jpeg")) else None, send=send)
        elif ch == "discord":
            send_discord(text, file=media, send=send)
        elif ch == "email":
            send_email(m["audience"], m.get("subject", m.get("id", "TrigunAI")),
                       html=m.get("html"), text=text, send=send)
        else:
            print(f"  (skip — channel {ch!r} is human-only or unsupported here)")

# --- CAMPAIGN: a list of posts or a single email send -------------------------
def run_campaign(manifest, send=False):
    m = json.load(open(manifest))
    if m.get("channel") == "email":
        send_email(m["audience"], m["subject"], html=m.get("html"), text=m.get("text"), send=send)
        return
    for step in m.get("posts", []):
        path = step if os.path.isabs(step) else os.path.join(HERE, step)
        print(f"\n=== post: {path} ===")
        run_post(path, send=send)

# --- CLI ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="TrigunAI multi-channel marketing publisher")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("email"); e.add_argument("--to", required=True); e.add_argument("--subject", required=True)
    e.add_argument("--html"); e.add_argument("--text"); e.add_argument("--send", action="store_true")

    t = sub.add_parser("telegram"); t.add_argument("--text", required=True)
    t.add_argument("--photo"); t.add_argument("--video"); t.add_argument("--send", action="store_true")

    d = sub.add_parser("discord"); d.add_argument("--text", required=True)
    d.add_argument("--file"); d.add_argument("--send", action="store_true")

    p = sub.add_parser("post"); p.add_argument("--manifest", required=True); p.add_argument("--send", action="store_true")
    c = sub.add_parser("campaign"); c.add_argument("--manifest", required=True); c.add_argument("--send", action="store_true")
    sub.add_parser("youtube")  # everything after is passthrough

    if len(sys.argv) >= 2 and sys.argv[1] == "youtube":
        return youtube_passthrough(sys.argv[2:])

    a = ap.parse_args()
    if a.cmd == "email":    send_email(a.to, a.subject, html=a.html, text=a.text, send=a.send)
    elif a.cmd == "telegram": send_telegram(a.text, photo=a.photo, video=a.video, send=a.send)
    elif a.cmd == "discord":  send_discord(a.text, file=a.file, send=a.send)
    elif a.cmd == "post":     run_post(a.manifest, send=a.send)
    elif a.cmd == "campaign": run_campaign(a.manifest, send=a.send)

if __name__ == "__main__":
    main()
