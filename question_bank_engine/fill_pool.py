#!/usr/bin/env python3
"""Batch-fill the generated pool for govt-job skill subjects to a target depth.

The quant/reasoning/english/static-GK generators COMPUTE the answer (no LLM, no key risk) and upsert
as verified=1, generated=1. We loop generator.generate_test until each (exam, subject) pool reaches
--target. Resumable: counts the live pool each round and stops at target. See POOL_FILL_PLAN.md.

DEFAULT DB is a local test db; pass --db data/qbank.sqlite (on Gurukul) to fill the live pool.
"""
import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank import storage, generator

# (exam, subject) that the SSC serving already uses + the generators' accepted subject strings.
SUBJECTS = {
    "maths":     ("SSC CGL", "Quantitative Aptitude"),
    "reasoning": ("SSC CGL", "Reasoning"),
    "english":   ("SSC CGL", "English"),
    "gk":        ("SSC CGL", "General Knowledge"),
}


def pool_count(store, exam, subject):
    return store.con.execute(
        "SELECT COUNT(*) FROM questions WHERE exam=? AND subject=? "
        "AND verified=1 AND COALESCE(generated,0)=1 AND duplicate_of IS NULL",
        (exam, subject)).fetchone()[0]


def fill(store, exam, subject, target, difficulty, batch, max_rounds):
    have = pool_count(store, exam, subject)
    print(f"  [{subject}] start={have} target={target}")
    rounds = stalls = 0
    while have < target and rounds < max_rounds:
        rounds += 1
        generator.generate_test(store, {"exam": exam, "subject": subject,
                                        "difficulty": difficulty, "dmin": 2, "dmax": 3},
                                count=batch)
        now = pool_count(store, exam, subject)
        if now <= have:
            stalls += 1
            if stalls >= 8:
                print(f"  [{subject}] STALLED at {now} (generator exhausted unique) — stopping")
                break
        else:
            stalls = 0
        have = now
        if rounds % 10 == 0:
            print(f"  [{subject}] {have}/{target} (round {rounds})", flush=True)
    print(f"  [{subject}] DONE at {have}")
    return have


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/tmp/fill_test.sqlite")
    ap.add_argument("--target", type=int, default=1000)
    ap.add_argument("--subjects", default="maths,reasoning,english,gk")
    ap.add_argument("--difficulty", default="2-3")
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--max-rounds", type=int, default=200)
    args = ap.parse_args()
    store = storage.Store(args.db)
    print(f"DB: {args.db}")
    for key in args.subjects.split(","):
        key = key.strip()
        if key not in SUBJECTS:
            print(f"  skip unknown subject '{key}'"); continue
        exam, subject = SUBJECTS[key]
        fill(store, exam, subject, args.target, args.difficulty, args.batch, args.max_rounds)
    print("\nfinal stats:", store.stats().get("verified_unique"))


if __name__ == "__main__":
    main()
