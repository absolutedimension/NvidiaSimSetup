#!/usr/bin/env python3
"""
pool_worksheets.py — the POOLING DRIVER. Runs worksheet_engine across the curriculum cells to
build a worksheet BANK. This is the turnkey tool the curriculum agent runs to fill content.

  # see what WOULD be pooled (priority order, skips draft cells):
  python3 pool_worksheets.py --dry
  # pool all MATHS cells (computed — NO endpoint needed):
  python3 pool_worksheets.py --maths-only --n 12
  # pool everything incl. knowledge subjects (needs litellm, e.g. via the EC2 tunnel):
  LITELLM_URL=http://localhost:4000/v1 python3 pool_worksheets.py --n 10

Output: kids_quiz/content/bank/<board>_class<N>_<subject>.json  +  content/bank/bank_index.json
Resumable: already-pooled cells are skipped unless --force.
Safety: cells flagged low-confidence in curriculum/index.json are SKIPPED unless --include-low.
"""
import json, os, argparse
import worksheet_engine as WE

BASE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(BASE, "content", "bank")
INDEX = os.path.join(BASE, "curriculum", "index.json")

# priority: his son's ICSE first, then the biggest markets; Bihar (mostly draft) last.
BOARD_RANK = {"ICSE": 0, "CBSE": 1, "Bihar Board": 2}
SUBJ_RANK = {"mathematics": 0, "evs": 1, "english": 2, "general knowledge": 3, "gk": 3, "hindi": 4}
def _subj_key(s): return s.lower().replace(" ", "")
def is_math(s): return _subj_key(s) in ("mathematics", "maths", "math")


def cells_from_index():
    """Yield (board, cls, subject, meta) from curriculum/index.json, priority-ordered."""
    d = json.load(open(INDEX, encoding="utf-8"))
    rows = []
    for board, classes in (d.get("cells") or {}).items():
        for cls, subs in classes.items():
            for subject, meta in subs.items():
                rows.append((board, int(cls), subject, meta or {}))
    rows.sort(key=lambda x: (BOARD_RANK.get(x[0], 9), SUBJ_RANK.get(x[2].lower(), 9), x[1]))
    return rows


def slug(board, cls, subject):
    return board.lower().replace(" ", "") + f"_class{cls}_" + subject.lower().replace(" ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--maths-only", action="store_true")
    ap.add_argument("--include-low", action="store_true", help="also pool low-confidence cells")
    ap.add_argument("--force", action="store_true", help="re-pool cells already in the bank")
    ap.add_argument("--limit", type=int, default=0, help="stop after N cells (0=all)")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    os.makedirs(BANK, exist_ok=True)
    index_path = os.path.join(BANK, "bank_index.json")
    bank_index = json.load(open(index_path)) if os.path.exists(index_path) else {}

    rows = cells_from_index()
    done = skipped = 0
    for board, cls, subject, meta in rows:
        if args.limit and done >= args.limit:
            break
        s = slug(board, cls, subject)
        conf = (meta.get("confidence") or "").lower()
        status = (meta.get("status") or "").lower()

        # filters
        if args.maths_only and not is_math(subject):
            continue
        if not is_math(subject) and conf == "low" and not args.include_low:
            print(f"  ⏭  skip {s}  (low-confidence taxonomy — pass --include-low to force)"); skipped += 1; continue
        if os.path.exists(os.path.join(BANK, s + ".json")) and not args.force:
            print(f"  ✓  have {s}"); continue

        need_llm = not is_math(subject)
        tag = "LLM" if need_llm else "computed"
        if args.dry:
            print(f"  →  would pool {s:38} [{tag}]  status={status or '?'} conf={conf or '?'}")
            done += 1; continue

        try:
            items = WE.generate(board, cls, subject, None, args.n)
        except Exception as e:
            print(f"  ⚠  {s}: {e}"); continue
        if not items:
            print(f"  ⚠  {s}: 0 items (endpoint down for knowledge?)"); continue
        json.dump({"board": board, "class": cls, "subject": subject, "count": len(items), "items": items},
                  open(os.path.join(BANK, s + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        bank_index[s] = {"board": board, "class": cls, "subject": subject, "count": len(items), "engine": tag}
        json.dump(bank_index, open(index_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  ✓  pooled {s:38} {len(items)} items [{tag}]")
        done += 1

    print(f"\n{'DRY: ' if args.dry else ''}{done} cell(s) {'to pool' if args.dry else 'pooled'} · {skipped} skipped · bank = {BANK}")


if __name__ == "__main__":
    main()
