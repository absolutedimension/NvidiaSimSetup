#!/usr/bin/env python3
"""Assemble curriculum cell JSONs from a research-agent result file.
Usage: python3 make_cells.py <agent_result.json>
Accepts either {board, subject, cells:[{class,...}]} or {board, cells:[{subject,class,...}]}.
Writes kids_quiz/curriculum/<board>_class<N>_<subject>.json per cell. Won't overwrite a
status:'complete' cell (protects the real-book ICSE Class-3 Maths)."""
import json, sys, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
SUBJ_SLUG = {"Mathematics": "mathematics", "EVS": "evs", "English": "english",
             "General Knowledge": "gk", "Hindi": "hindi", "Science": "science"}

def clean(x):
    if isinstance(x, str): return html.unescape(x).strip()
    if isinstance(x, list): return [clean(i) for i in x]
    if isinstance(x, dict): return {k: clean(v) for k, v in x.items()}
    return x

def cid(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')[:40]

def write_cell(board, subject, cell):
    cell = clean(cell)
    cls = int(cell["class"])
    conf = cell.get("confidence", "low")
    verified = bool(cell.get("verified", False))
    status = "complete" if (conf == "high" and verified) else "draft"
    chapters = []
    for ch in cell.get("chapters", []):
        if isinstance(ch, str):                      # agent returned bare chapter names
            chapters.append({"id": cid(ch), "name": ch, "subtopics": []})
        else:
            chapters.append({"id": cid(ch["name"]), "name": ch["name"],
                             "subtopics": ch.get("subtopics", [])})
    out = {
        "board": board, "class": cls, "subject": subject,
        "source": {"name": cell.get("source_name", ""), "url": cell.get("source_url", ""),
                   "verified_on": "2026-08-02"},
        "confidence": conf, "verified": verified, "status": status,
        "notes": cell.get("notes", ""), "chapters": chapters,
    }
    fn = f"{board.lower().replace(' ','')}_class{cls}_{SUBJ_SLUG.get(subject, cid(subject))}.json"
    fp = os.path.join(HERE, fn)
    if os.path.exists(fp):
        try:
            if json.load(open(fp)).get("status") == "complete":
                print("  SKIP (complete, protected):", fn); return
        except Exception: pass
    json.dump(out, open(fp, "w"), indent=2, ensure_ascii=False)
    print(f"  wrote {fn}  [{status}/{conf}, {len(chapters)} ch]")

def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    board = data["board"]
    top_subject = data.get("subject")
    for cell in data["cells"]:
        subject = cell.get("subject", top_subject)
        if not cell.get("chapters"):    # e.g. CBSE EVS 1-2 = integrated, no chapters
            print(f"  (Class {cell.get('class')} {subject}: no chapters — {cell.get('notes','')[:60]})")
        write_cell(board, subject, cell)

if __name__ == "__main__":
    main()
