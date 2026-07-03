import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print("(maps search failed)"); sys.exit(0)
results = d.get("results", [])
if not results:
    print("(no results)"); sys.exit(0)
for r in results:
    p = r.get("poi", {}); a = r.get("address", {})
    name = p.get("name", "?")
    phone = (p.get("phone") or "").strip() or "(verify on Justdial)"
    addr = a.get("freeformAddress", "")
    print(f"{name} | {phone} | {addr}")
