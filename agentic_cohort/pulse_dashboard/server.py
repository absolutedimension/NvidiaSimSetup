#!/usr/bin/env python3
"""
pulse_dashboard server — a tiny read-only admin dashboard for the Acharya funnel.

Runs on the Gurukul VM. Holds the LMS pulse key SERVER-SIDE (never sent to the browser)
and proxies the LMS `/admin/api/pulse` to a live, auto-refreshing HTML page. Access is
gated by a secret token in the URL (?t=<DASH_TOKEN>) — treat the link like a password.

Env (from ~/pulse_dashboard/pulse_dash.env):
    LMS_PULSE_URL   e.g. https://acharya.trigunai.com/admin/api/pulse
    LMS_PULSE_KEY   the real LMS PULSE_KEY (kept here, never exposed to the browser)
    DASH_TOKEN      the secret that gates access to /admin-pulse
    PORT            default 7871

Routes (behind Caddy `handle /admin-pulse*`):
    GET /admin-pulse?t=TOKEN        -> the dashboard HTML
    GET /admin-pulse/api?t=TOKEN    -> live JSON (server fetches the LMS pulse)
    GET /admin-pulse/health         -> ok
Stdlib only. No pip installs. Never logs the tokens/keys.
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_env():
    p = os.path.join(HERE, "pulse_dash.env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
LMS_PULSE_URL = os.getenv("LMS_PULSE_URL", "https://acharya.trigunai.com/admin/api/pulse")
LMS_PULSE_KEY = os.getenv("LMS_PULSE_KEY", "")
DASH_TOKEN = os.getenv("DASH_TOKEN", "")
PORT = int(os.getenv("PORT", "7871"))

HTML = open(os.path.join(HERE, "dashboard.html"), encoding="utf-8").read()


def fetch_pulse():
    url = f"{LMS_PULSE_URL}?key={LMS_PULSE_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "pulse-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_student(sid: str):
    url = f"{LMS_PULSE_URL}/student?key={LMS_PULSE_KEY}&id={int(sid)}"
    req = urllib.request.Request(url, headers={"User-Agent": "pulse-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # never log (URLs carry the token)

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _ok_token(self, q):
        return DASH_TOKEN and q.get("t", [""])[0] == DASH_TOKEN

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/admin-pulse"
        q = parse_qs(u.query)

        if path == "/admin-pulse/health":
            return self._send(200, "ok", "text/plain")

        if path == "/admin-pulse/api":
            if not self._ok_token(q):
                return self._send(403, json.dumps({"error": "forbidden"}))
            try:
                return self._send(200, fetch_pulse())
            except Exception as e:
                return self._send(502, json.dumps({"error": f"upstream: {e}"}))

        if path == "/admin-pulse/api/student":
            if not self._ok_token(q):
                return self._send(403, json.dumps({"error": "forbidden"}))
            sid = q.get("id", [""])[0]
            if not sid.isdigit():
                return self._send(400, json.dumps({"error": "bad id"}))
            try:
                return self._send(200, fetch_student(sid))
            except urllib.error.HTTPError as e:
                return self._send(e.code, json.dumps({"error": f"upstream {e.code}"}))
            except Exception as e:
                return self._send(502, json.dumps({"error": f"upstream: {e}"}))

        if path == "/admin-pulse":
            if not self._ok_token(q):
                return self._send(403, "<h1>403 — add ?t=&lt;token&gt; to the URL</h1>", "text/html")
            return self._send(200, HTML, "text/html; charset=utf-8")

        return self._send(404, json.dumps({"error": "not found"}))


if __name__ == "__main__":
    if not LMS_PULSE_KEY or not DASH_TOKEN:
        raise SystemExit("Set LMS_PULSE_KEY and DASH_TOKEN in pulse_dash.env")
    print(f"pulse_dashboard on :{PORT}  (proxying {LMS_PULSE_URL})")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
