#!/usr/bin/env python3
"""Backfill pgvector embeddings for banked questions that don't have one yet.

SQLite (`data/qbank.sqlite`) is the store of record; Postgres+pgvector holds a mirror whose
`questions.embedding` column powers the generator's novelty gate (`semantic.max_similarity`)
and exemplar diversification. Rows written straight into SQLite — ingested real PYQs (UPSC /
BPSC / TRE) and the compute-the-answer generator pools (SSC quant/reasoning/English/static-GK) —
never pass through `semantic.upsert_embedding()`, so they drift out of the vector mirror and
become invisible to duplicate detection.

Idempotent + resumable: it only touches ids whose embedding IS NULL / missing, in batches, so a
re-run after an interruption just continues. Read-only against SQLite.

    python3 backfill_embeddings.py --dry-run          # report the gap, embed nothing
    python3 backfill_embeddings.py --limit 200        # small verified slice first
    python3 backfill_embeddings.py                    # everything missing
"""
import argparse
import sqlite3
import sys
import time

from qbank import semantic

BATCH = 128


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/qbank.sqlite")
    ap.add_argument("--limit", type=int, default=0, help="cap rows this run (0 = all)")
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not semantic.enabled():
        print("QBANK_SEMANTIC is off — nothing to do."); return 1
    con = semantic._connect()
    if con is None:
        print("pgvector unreachable (check pg.env) — aborting."); return 1

    lite = sqlite3.connect(args.db)
    lite.row_factory = sqlite3.Row
    rows = {r["id"]: r for r in lite.execute(
        "SELECT id, exam, subject, stem, qtype, chapter, concept, difficulty, generated "
        "FROM questions WHERE verified=1 AND duplicate_of IS NULL")}
    cur = con.cursor()
    cur.execute("SELECT id FROM questions WHERE embedding IS NOT NULL")
    embedded = {r[0] for r in cur.fetchall()}
    todo = [i for i in rows if i not in embedded]
    print(f"sqlite verified={len(rows)}  pgvector embedded={len(embedded)}  MISSING={len(todo)}")
    if args.limit:
        todo = todo[:args.limit]
        print(f"--limit {args.limit} → embedding {len(todo)} this run")
    if args.dry_run or not todo:
        return 0

    done = failed = 0
    t0 = time.time()
    for i in range(0, len(todo), args.batch):
        chunk = todo[i:i + args.batch]
        stems = [(rows[q]["stem"] or "").strip() for q in chunk]
        try:
            vecs = semantic.embed(stems)
        except Exception as exc:
            print(f"  embed batch failed ({exc}) — skipping {len(chunk)}"); failed += len(chunk); continue
        payload = []
        for qid, v in zip(chunk, vecs):
            r = rows[qid]
            payload.append((qid, r["exam"], r["subject"], r["stem"], r["qtype"], r["chapter"],
                            r["concept"], r["difficulty"], 1, int(r["generated"] or 0), v))
        try:
            cur.executemany(
                "INSERT INTO questions (id, exam, subject, stem, qtype, chapter, concept, "
                "difficulty, verified, generated, embedding) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding", payload)
            con.commit()
            done += len(payload)
        except Exception as exc:
            con.rollback(); failed += len(payload)
            print(f"  upsert batch failed: {str(exc)[:120]}")
        if (i // args.batch) % 5 == 0:
            print(f"  {done}/{len(todo)} embedded ({time.time()-t0:.0f}s)", flush=True)
    print(f"\nDONE embedded={done} failed={failed} in {time.time()-t0:.0f}s")
    cur.execute("SELECT COUNT(*) FROM questions WHERE embedding IS NOT NULL")
    print("pgvector embedded now:", cur.fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
