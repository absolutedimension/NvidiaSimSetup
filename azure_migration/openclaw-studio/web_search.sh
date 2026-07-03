#!/bin/bash
# Web search via DuckDuckGo (no API key). Usage: web_search.sh "query" [N]
# Prints:  <title> | <url>   (one per line)
Q="$1"; N="${2:-8}"
ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$Q")
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
fetch() { curl -s -m 15 -A "$UA" "$1" ; }
# try html endpoint, then lite endpoint
HTML=$(fetch "https://html.duckduckgo.com/html/?q=${ENC}")
echo "$HTML" | python3 - "$N" <<'PY'
import sys, re, html, urllib.parse
n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
t = sys.stdin.read()
out, seen = [], set()
# match any anchor whose href carries a DDG redirect (uddg=), robust to attribute order
for m in re.finditer(r'href="[^"]*?uddg=([^&"]+)[^"]*"[^>]*>(.*?)</a>', t, re.S):
    real = urllib.parse.unquote(m.group(1))
    title = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
    if title and real.startswith("http") and real not in seen:
        seen.add(real); out.append(f"{title} | {real}")
print("\n".join(out[:n]))
PY
