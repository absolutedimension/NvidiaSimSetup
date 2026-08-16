#!/usr/bin/env python3
"""reclean_bank.py — clean existing knowledge banks with the quality critic (in place).

Drops degenerate items (always) + LLM-fact-flagged items (WS_CRITIC=1). Then RE-FILL to the
target with fill_knowledge_pool (critic active) to restore the clean count.

  # deterministic only (no endpoint) — drop structural junk now:
  python3 reclean_bank.py --glob "content/bank/*_class3_*.json"
  # full clean (needs EC2 litellm tunnel):
  WS_CRITIC=1 LITELLM_URL=http://localhost:4000/v1 python3 reclean_bank.py --glob "content/bank/*_class3_*.json"
"""
import json, os, glob, argparse
import quality_critic as QC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="content/bank/*_class3_*.json")
    args = ap.parse_args()
    use_llm = os.environ.get("WS_CRITIC") == "1"
    total_in = total_out = 0
    for f in sorted(glob.glob(args.glob)):
        if "math" in f or "index" in f:
            continue
        d = json.load(open(f, encoding="utf-8"))
        kept, st = QC.clean(d.get("items", []), subject=d.get("subject", ""), cls=d.get("class", 3), use_llm=use_llm)
        d["items"] = kept; d["count"] = len(kept)
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        total_in += st["in"]; total_out += st["out"]
        print(f"  {os.path.basename(f)[:-5]:24} {st['in']} → {st['out']}  "
              f"(dropped {st['degenerate']} degenerate + {st['fact_flagged']} fact-flagged)")
    print(f"\nTOTAL {total_in} → {total_out}  (removed {total_in-total_out}). "
          f"Now RE-FILL to target: python3 fill_knowledge_pool.py --target 1000  (WS_CRITIC=1 for clean LLM fill)")


if __name__ == "__main__":
    main()
