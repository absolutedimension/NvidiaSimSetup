#!/usr/bin/env python3
"""Parallel LLM tagger for untagged verified questions.

`run.py tag` tags one question per LLM call, single-threaded — fine for a few hundred,
too slow for the ~10k diagram questions the datavorous JEE ingest adds. The LiteLLM
proxy handles concurrency (proven on the solve pass), so this tags with a thread pool.

Scoped to UNTAGGED verified questions (chapter IS NULL), optionally by --exam, so it
only touches the freshly-ingested rows, never the established bank. Idempotent.

    python3 parallel_tag.py [--exam "JEE Main"] [--workers 12] [--limit N]
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from qbank import tagger
from qbank.llm import LLM
from qbank.storage import Store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", default=None)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    store, llm = Store(), LLM()
    if not llm.ok:
        print("LLM not reachable:", llm.last_error)
        return
    todo = store.iter_untagged(limit=args.limit)
    if args.exam:
        todo = [q for q in todo if q.exam == args.exam]
    print(f"[parallel-tag] {len(todo)} untagged | exam={args.exam or 'ALL'} | workers={args.workers}")

    done = [0]

    def tag_one(q):
        t = tagger.tag_question(q, llm=llm)
        return q.id, t

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(tag_one, q) for q in todo]
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception:
                pass
            done[0] += 1
            if done[0] % 250 == 0:
                print(f"  tagged {done[0]}/{len(todo)}")

    # write on the main thread (one sqlite connection)
    conf = {}
    for qid, t in results:
        store.update_tags(qid, t["chapter"], t["concept"], t["difficulty"], t["bloom"])
        conf[t["confidence"]] = conf.get(t["confidence"], 0) + 1
    print(f"[parallel-tag] done. wrote {len(results)} | confidence={conf}")


if __name__ == "__main__":
    main()
