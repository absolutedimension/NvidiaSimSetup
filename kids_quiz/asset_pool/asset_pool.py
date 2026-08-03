#!/usr/bin/env python3
"""
asset_pool.py — the BRAIN of the kids asset-pooling system (runs locally, no GPU).

The pool = lms/app/static/kids/asset_manifest.json. Each asset is `ready` (a web asset exists) or
`needed` (queued for offline generation; worksheets show its emoji until then). This tool keeps the
pool honest and decides what to generate:

  status                     → ready vs needed counts + the needed list
  scan   <dir-or-file>...     → find asset ids referenced by worksheet items; flag any UNKNOWN ones
  request <id>[,<id>...]      → add new `needed` assets (--type/--emoji/--source)
  plan   [--type prop]        → write to_generate.json = the batch the offline generator consumes

Flow:  worksheets reference assets  →  scan finds gaps  →  request adds them  →  plan emits the batch
       →  gen_assets.py (on EC2) generates + marks them `ready`  →  worksheets auto-fill the art.

Usage:
  python3 asset_pool.py status
  python3 asset_pool.py scan ../../lms/app/static/kids/alive_worksheet.html ../content/
  python3 asset_pool.py request penguin,rocket --type prop --emoji 🐧
  python3 asset_pool.py plan --out to_generate.json
"""
import json, os, sys, argparse, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MANIFEST = os.path.normpath(os.path.join(HERE, "..", "..", "lms", "app", "static", "kids", "asset_manifest.json"))


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, m):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print(f"✓ wrote {path}")


def cmd_status(m, args):
    a = m["assets"]
    ready = [k for k, v in a.items() if v.get("status") == "ready"]
    needed = [k for k, v in a.items() if v.get("status") != "ready"]
    by_type = {}
    for k, v in a.items():
        by_type.setdefault(v.get("type", "?"), [0, 0])
        by_type[v.get("type", "?")][0 if v.get("status") == "ready" else 1] += 1
    print(f"POOL: {len(ready)} ready · {len(needed)} needed · {len(a)} total")
    for t, (r, n) in sorted(by_type.items()):
        print(f"  {t:12} ready {r:3}  needed {n:3}")
    if needed:
        print("\nNEEDED (emoji fallback in use):")
        for k in sorted(needed):
            print(f"  {a[k].get('emoji','?')}  {k:14} [{a[k].get('type','?')}] via {a[k].get('source','?')}")


def _iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for f in glob.glob(os.path.join(p, "**", "*.*"), recursive=True):
                if f.rsplit(".", 1)[-1].lower() in ("json", "html", "js"):
                    yield f
        elif os.path.isfile(p):
            yield p


def cmd_scan(m, args):
    a = m["assets"]
    ref = re.compile(r'["\']asset["\']\s*:\s*["\']([a-z0-9_]+)["\']')
    emoji_to_id = {v.get("emoji"): k for k, v in a.items() if v.get("emoji")}
    used = {}                       # id -> count
    unknown = {}                    # id -> count (referenced but not in pool)
    for f in _iter_files(args.paths):
        txt = open(f, "r", encoding="utf-8", errors="ignore").read()
        for mid in ref.findall(txt):
            (used if mid in a else unknown)[mid] = (used if mid in a else unknown).get(mid, 0) + 1
        for em, mid in emoji_to_id.items():   # emojis that map to a pool id also count as usage
            c = txt.count(em)
            if c:
                used[mid] = used.get(mid, 0) + c
    print(f"scanned {len(list(_iter_files(args.paths)))} file(s)")
    if used:
        print("\nreferenced pool assets:")
        for k in sorted(used, key=lambda x: -used[x]):
            st = a[k].get("status")
            flag = "✓ready" if st == "ready" else "… needed"
            print(f"  {used[k]:3}×  {k:14} {flag}")
    if unknown:
        print("\n⚠ referenced but NOT in the pool (run `request` to add):")
        for k in sorted(unknown):
            print(f"  {unknown[k]:3}×  {k}")


def cmd_request(m, args):
    a = m["assets"]
    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    for i in ids:
        if i in a:
            print(f"  · {i} already in pool ({a[i]['status']}) — skipped")
            continue
        a[i] = {"type": args.type, "label": i, "status": "needed",
                "emoji": args.emoji or "❓", "source": args.source, "web": None, "tags": []}
        print(f"  + added {i} [{args.type}] via {args.source}")
    save(args.manifest, m)


# ---- context → character (keyword-driven now; an LLM call can replace this map later) ----
SUBJECT_HELPER = {"math": "nova_owl", "maths": "nova_owl", "mathematics": "nova_owl",
                  "english": "lexi_fox", "evs": "gaia_deer", "science": "gaia_deer",
                  "gk": "quizzy_parrot", "hindi": "nova_owl"}
HELPER_LABEL = {"nova_owl": "wise friendly owl teacher mascot with tiny round glasses",
                "lexi_fox": "friendly orange fox mascot holding a little book",
                "gaia_deer": "gentle friendly deer mascot with a green leaf",
                "quizzy_parrot": "cheerful colorful parrot mascot"}
ANIMAL_WORDS = ["lion", "elephant", "monkey", "tiger", "bear", "cow", "dog", "cat", "rabbit", "owl",
                "fox", "deer", "parrot", "frog", "penguin", "zebra", "giraffe", "duck", "horse"]


def cmd_suggest(m, args):
    """Given a worksheet's subject + topic, propose the characters it needs and add them as `needed`."""
    a = m["assets"]
    subj = (args.subject or "").lower().strip()
    topic = (args.topic or "").lower()
    picks = {}   # id -> label
    helper = SUBJECT_HELPER.get(subj)
    if helper:
        picks[helper] = HELPER_LABEL.get(helper, helper.replace("_", " ") + " mascot")
    for w in ANIMAL_WORDS:
        if w in topic:
            picks[w + "_char"] = f"friendly {w} mascot"
    if not picks:
        print("no character suggestions for that context — pass --subject and/or a richer --topic")
        return
    print(f"context: subject='{subj}' topic='{topic[:60]}' → suggested characters:")
    added = 0
    for cid, label in picks.items():
        if cid in a:
            print(f"  · {cid} already in pool ({a[cid]['status']})")
            continue
        a[cid] = {"type": "character", "label": label, "status": "needed", "emoji": "🧸",
                  "source": "gpt-image", "web": None, "prompt": None, "tags": ["mascot", subj]}
        print(f"  + {cid}  ({label})")
        added += 1
    if added and args.add:
        save(args.manifest, m)
    elif added:
        print("  (dry — pass --add to write these into the pool)")


def cmd_plan(m, args):
    a = m["assets"]
    batch = []
    for k, v in a.items():
        if v.get("status") == "ready":
            continue
        if args.type and v.get("type") != args.type:
            continue
        batch.append({"id": k, "type": v.get("type"), "source": v.get("source"),
                      "label": v.get("label", k), "emoji": v.get("emoji"),
                      "prompt": v.get("prompt")})   # prompt optional; gen_assets fills a default
    out = os.path.join(HERE, args.out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"count": len(batch), "items": batch}, f, ensure_ascii=False, indent=2)
    print(f"✓ {len(batch)} asset(s) → {out}")
    print("  next: run gen_assets.py on the GPU box (litellm/factory) to generate + mark ready.")


def main():
    ap = argparse.ArgumentParser(description="Kids asset pool manager")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    s = sub.add_parser("scan"); s.add_argument("paths", nargs="+")
    r = sub.add_parser("request"); r.add_argument("ids")
    r.add_argument("--type", default="prop"); r.add_argument("--emoji", default="")
    r.add_argument("--source", default="gpt-image")
    sg = sub.add_parser("suggest"); sg.add_argument("--subject", default=""); sg.add_argument("--topic", default="")
    sg.add_argument("--add", action="store_true")
    p = sub.add_parser("plan"); p.add_argument("--type", default=""); p.add_argument("--out", default="to_generate.json")
    args = ap.parse_args()

    m = load(args.manifest)
    {"status": cmd_status, "scan": cmd_scan, "request": cmd_request,
     "suggest": cmd_suggest, "plan": cmd_plan}[args.cmd](m, args)


if __name__ == "__main__":
    main()
