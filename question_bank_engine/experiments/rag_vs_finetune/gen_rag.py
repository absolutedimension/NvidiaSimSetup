#!/usr/bin/env python3
"""Arm A — RAG + prompting. Authors questions against specs.json using the EXISTING
generator (retrieve real exemplars -> prompt the base model -> validate -> novelty gate).

Needs the LLM proxy:  QBANK_LLM=on QBANK_LLM_BASE_URL=... QBANK_LLM_API_KEY=...
Output: artifacts/out_rag.json  ({"arm":"rag","questions":[...with _novelty...]})
"""
import json
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)

from qbank import generator          # noqa: E402
from qbank.storage import Store      # noqa: E402
from qbank.llm import LLM            # noqa: E402

ART = os.path.join(HERE, "artifacts")


def main():
    specs = json.load(open(os.path.join(ART, "specs.json")))
    bank = json.load(open(os.path.join(ART, "bank_stems.json")))
    store, llm = Store(), LLM()
    if not llm.ok:
        sys.exit(f"LLM proxy not reachable: {llm.last_error}")

    out = []
    for s in specs:
        rep = generator.generate_test(store, dict(s), llm=llm,
                                      count=s.get("count", 4), k_exemplars=3)
        for q in rep.get("questions", []):
            q["_novelty"] = round(generator.novelty(
                SimpleNamespace(stem=q["stem"]), bank), 3)
            out.append(q)
        print(f"  {s['chapter']:<32} requested={s.get('count')} "
              f"clean={rep.get('generated')} rejected={len(rep.get('rejected', []))}")

    json.dump({"arm": "rag", "model": os.environ.get('QBANK_CHAT_MODEL', 'default'),
               "questions": out}, open(os.path.join(ART, "out_rag.json"), "w"),
              indent=2, ensure_ascii=False)
    print(f"\nArm A (RAG): {len(out)} clean questions -> artifacts/out_rag.json")


if __name__ == "__main__":
    main()
