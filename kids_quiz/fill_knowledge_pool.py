#!/usr/bin/env python3
"""fill_knowledge_pool.py — grow the knowledge worksheet banks (EVS/English/GK/Hindi) to a target
size via the LLM, deduped across the WHOLE cell, round-robining across every chapter for variety.

  LITELLM_URL=http://localhost:4000/v1 WS_LLM_TEMP=0.9 \
  python3 fill_knowledge_pool.py --target 300 --workers 8

Resumable: starts from whatever is already in content/bank/<slug>.json and only adds NEW items.
Writes incrementally (every round) so a kill mid-run keeps progress.
"""
import json, os, re, argparse, threading
from concurrent.futures import ThreadPoolExecutor
import worksheet_engine as WE

_LATIN = re.compile(r'[A-Za-z]')


def hindi_pure(it):
    """A Hindi item is 'pure' only if its CONTENT (not the instruction, which we localise) has no
    Latin letters — rejects the Hindi↔English translation items the LLM sometimes emits."""
    p = it.get("payload", {}) or {}
    blobs = [str(it.get("answer", "")), p.get("statement", ""), p.get("sentence", "")]
    blobs += [str(x) for x in p.get("options", [])] + [str(x) for x in p.get("bank", [])]
    blobs += [str(x) for x in p.get("items", [])] + [str(x) for x in p.get("bins", [])]
    for pr in p.get("pairs", []):
        blobs += [str(x) for x in (pr if isinstance(pr, (list, tuple)) else [pr])]
    return not any(_LATIN.search(b or "") for b in blobs)

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "content", "bank")
_print_lock = threading.Lock()

# Broad, age-appropriate Class-3 topic areas per subject — added to the curriculum chapters so
# low-breadth subjects (GK 3 ch, English 4, Hindi 5) have enough distinct ground to reach 1000.
BROAD = {
    "GK": ["Animals and birds", "Wild and domestic animals", "Plants and trees", "Fruits and vegetables",
           "Our country India", "National symbols of India", "Festivals of India", "Means of transport",
           "Community helpers", "The human body", "Good habits and safety", "Seasons and weather",
           "Sports and games", "Food and nutrition", "The solar system and space", "Water and its uses",
           "Colours and shapes", "Days months and time", "Famous places in India", "Insects and small creatures",
           "Birds and their sounds", "Trees and their fruits", "Our helpers and their tools", "Air land and water animals"],
    "English": ["Opposite words", "Rhyming words", "Naming words (nouns)", "Action words (verbs)",
                "Articles a an the", "Plurals one and many", "This that these those", "Describing words",
                "Simple sentences", "Punctuation full stop and capital letter", "Common sight words",
                "Vowels and consonants", "Prepositions in on under", "Question words who what where",
                "Days and months spelling", "Genders he she", "Was were is am are", "Naming animals and their young",
                "Naming animals and their homes", "Sounds animals make"],
    "Hindi": ["विलोम शब्द", "पर्यायवाची शब्द", "वचन एक और अनेक", "गिनती एक से बीस", "फल और सब्ज़ियाँ",
              "जानवर और पक्षी", "रंग", "शरीर के अंग", "त्योहार", "दिन और महीने", "मात्राएँ आ की मात्रा",
              "संज्ञा शब्द", "क्रिया शब्द", "परिवार के सदस्य", "आकार और दिशाएँ", "पशु और उनके बच्चे",
              "पशु और उनके घर", "फूल और पेड़", "यातायात के साधन", "हमारे सहायक"],
    "EVS": ["Living and non-living things", "Plants around us", "Animals around us", "Our body and senses",
            "Food we eat", "Water and air", "Our family and home", "Safety and good habits",
            "Weather and seasons", "Means of transport", "Festivals and celebrations", "Keeping clean"],
}


def sig(it):
    """A dedup signature that ignores incidental formatting — catches near-duplicate items."""
    p = it.get("payload", {}) or {}
    t = it.get("type")
    if t == "match_following":
        return "m|" + "|".join(sorted(str(a).strip().lower() for a, _ in p.get("pairs", []) if isinstance(a, str)))
    if t == "odd_one_out":
        return "o|" + "|".join(sorted(str(x).strip().lower() for x in p.get("options", [])))
    if t == "true_false":
        return "t|" + str(p.get("statement", "")).strip().lower()
    if t == "cloze":
        return "c|" + str(p.get("sentence", "")).strip().lower()
    if t == "sort_groups":
        return "s|" + "|".join(sorted(str(x).strip().lower() for x in p.get("items", [])))
    return "x|" + json.dumps(p, sort_keys=True, ensure_ascii=False)


def fill(board, cls, subject, target, dry_limit):
    slug = board.lower().replace(" ", "") + f"_class{cls}_" + subject.lower().replace(" ", "")
    path = os.path.join(BANK, slug + ".json")
    items, seen = [], set()
    if os.path.exists(path):
        for it in (json.load(open(path, encoding="utf-8")).get("items", [])):
            s = sig(it)
            if s not in seen:
                seen.add(s); items.append(it)
    start = len(items)
    cell = WE.load_cell(board, cls, subject)
    chapters = WE.chapters_of(cell) if cell else [(subject, [])]
    if not chapters:
        chapters = [(subject, [])]
    # widen the ground with broad Class-3 topic areas so narrow subjects can still reach the target
    chapters = chapters + [(t, []) for t in BROAD.get(subject, [])]

    def flush():
        json.dump({"board": board, "class": cls, "subject": subject, "count": len(items), "items": items},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    dry = ci = 0
    while len(items) < target and dry < dry_limit:
        chname, subs = chapters[ci % len(chapters)]; ci += 1
        try:
            batch = WE.llm_knowledge(subject, cls, chname, subs, n=12, _attempts=1)
        except Exception:
            batch = []
        added = 0
        hindi = subject.strip().lower() == "hindi"
        for it in batch:
            if hindi and not hindi_pure(it):     # keep Hindi worksheets fully in Devanagari
                continue
            s = sig(it)
            if s in seen:
                continue
            seen.add(s); items.append(it); added += 1
            if len(items) >= target:
                break
        dry = 0 if added else dry + 1
        if added:
            flush()
        with _print_lock:
            print(f"  {slug:32} +{added:2}  ->  {len(items):3}/{target}  (dry={dry})", flush=True)
    flush()
    return slug, start, len(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=300)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-limit", type=int, default=40)
    ap.add_argument("--boards", default="CBSE,ICSE")
    ap.add_argument("--subjects", default="EVS,English,GK,Hindi")
    ap.add_argument("--cls", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(BANK, exist_ok=True)
    cells = [(b.strip(), args.cls, s.strip())
             for b in args.boards.split(",") for s in args.subjects.split(",")]
    print(f"Filling {len(cells)} cells to {args.target} each (workers={args.workers}, "
          f"temp={os.environ.get('WS_LLM_TEMP','0.6')})\n")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(fill, b, c, s, args.target, args.dry_limit) for (b, c, s) in cells]
        for f in futs:
            results.append(f.result())
    print("\n=== DONE ===")
    for slug, start, end in sorted(results):
        print(f"  {slug:32} {start:3} -> {end:3}  (+{end-start})")
    # refresh bank_index
    idx_path = os.path.join(BANK, "bank_index.json")
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    for slug, _, end in results:
        idx[slug] = {**idx.get(slug, {}), "count": end, "engine": "LLM"}
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nTotal items now: {sum(e for _,_,e in results)} across {len(results)} knowledge cells.")


if __name__ == "__main__":
    main()
