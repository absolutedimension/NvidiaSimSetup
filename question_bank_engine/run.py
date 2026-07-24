#!/usr/bin/env python3
"""CLI for the TrigunAI Question Bank Engine.

  python run.py ingest-dataset --limit 40      # auto-collect real JEE Physics -> clean bank
  python run.py ingest-drop --exam "JEE Main" --year 2024   # ingest PDFs from drop/
  python run.py stats                          # what's in the bank
  python run.py sample -n 3                     # show clean questions
"""
import argparse
import json
import sys

from qbank import pipeline
from qbank.storage import Store


def _print_report(r):
    print("\n=== INGEST REPORT ===")
    for k in ("processed", "duplicates_flagged", "unique", "verified_clean", "rejected"):
        print(f"  {k:20s}: {r[k]}")
    if r["rejection_reasons"]:
        print("  rejection_reasons   :")
        for reason, n in r["rejection_reasons"].items():
            print(f"      - {reason}: {n}")
    print(f"  llm_used            : {r['llm_used']}"
          + (f"  ({r['llm_note']})" if r["llm_note"] else ""))


def main():
    ap = argparse.ArgumentParser(prog="qbank")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("ingest-dataset", help="auto-collect an open dataset")
    d.add_argument("--dataset", default="daman1209arora/jeebench")
    d.add_argument("--subject", default="phy", help="dataset subject code (phy/chem/math)")
    d.add_argument("--subject-name", default="Physics")
    d.add_argument("--exam", default="JEE Advanced")
    d.add_argument("--limit", type=int, default=40)
    d.add_argument("--llm-validate", action="store_true", help="also run the LLM well-formedness check (slow, over-rejects integer/numeric)")

    p = sub.add_parser("ingest-drop", help="ingest PDFs from the drop/ folder (needs LLM)")
    p.add_argument("--exam", default="JEE Main")
    p.add_argument("--subject", default="Physics")
    p.add_argument("--year", type=int, default=None)
    p.add_argument("--key", default=None, help="answer-key PDF path")

    gf = sub.add_parser("ingest-grafite", help="ingest the grafite JEE-Main bank (pre-tagged + pre-solved text)")
    gf.add_argument("--dataset", default="ruh-ai/grafite-jee-mains-qna-no-img")
    gf.add_argument("--subject", default="physics", help="dataset subject filter (physics/chemistry/maths)")
    gf.add_argument("--subject-name", default="Physics")
    gf.add_argument("--exam", default="JEE Main")
    gf.add_argument("--difficulty", type=int, default=2, help="default difficulty (integer-type gets +1)")
    gf.add_argument("--limit", type=int, default=None)
    gf.add_argument("--llm-validate", action="store_true", help="also run the LLM well-formedness check (slow)")

    dv = sub.add_parser("ingest-datavorous", help="ingest the datavorous entrance-exam bank (pre-tagged+keyed+solved HTML)")
    dv.add_argument("--dataset", default="datavorous/entrance-exam-dataset")
    dv.add_argument("--exam", default="NEET", help="exam tag to keep (NEET / JEE Main / JEE Advanced)")
    dv.add_argument("--subjects", default=None, help="comma-separated subjects to keep (default: all)")
    dv.add_argument("--difficulty", type=int, default=2)
    dv.add_argument("--limit", type=int, default=None)
    dv.add_argument("--llm-validate", action="store_true")
    dv.add_argument("--figures-only", action="store_true", help="ingest ONLY <img> diagram rows (add diagram Qs to an exam whose text bank already exists)")

    nb = sub.add_parser("ingest-neet-bio", help="ingest a text NEET Biology bank (sweatSmile schema)")
    nb.add_argument("--dataset", default="sweatSmile/neet-biology-qa")
    nb.add_argument("--subject-name", default="Biology")
    nb.add_argument("--exam", default="NEET")
    nb.add_argument("--difficulty", type=int, default=2, help="default difficulty before LLM retag")
    nb.add_argument("--limit", type=int, default=None)
    nb.add_argument("--llm-validate", action="store_true", help="also run the LLM well-formedness check (slow)")

    im = sub.add_parser("ingest-images", help="ingest an image-based dataset via the vision LLM")
    im.add_argument("--dataset", default="Reja1/jee-neet-benchmark")
    im.add_argument("--exam-prefix", default="JEE", help="filter exam_name (e.g. JEE, NEET)")
    im.add_argument("--subject", default="Physics")
    im.add_argument("--exam", default="JEE Advanced")
    im.add_argument("--limit", type=int, default=None)

    es = sub.add_parser("enrich-solutions", help="write + validate worked solutions (needs LLM)")
    es.add_argument("--chapter", default=None)
    es.add_argument("--exam", default=None, help="scope to one exam (else the WHOLE bank)")
    es.add_argument("--subject", default=None, help="scope to one subject")
    es.add_argument("--limit", type=int, default=None)

    rt = sub.add_parser("retag", help="LLM re-tag real questions (accurate concept+difficulty)")
    rt.add_argument("--chapter", default=None)
    rt.add_argument("--exam", default=None, help="scope to one exam (else the WHOLE bank)")
    rt.add_argument("--subject", default=None, help="scope to one subject")
    rt.add_argument("--limit", type=int, default=None)

    rv = sub.add_parser("reverify", help="self-consistency re-check of needs_review solutions")
    rv.add_argument("--chapter", default=None)
    rv.add_argument("--exam", default=None, help="scope to one exam (else the WHOLE bank)")
    rv.add_argument("--subject", default=None, help="scope to one subject")
    rv.add_argument("--k", type=int, default=5)
    rv.add_argument("--limit", type=int, default=None)

    sub.add_parser("mark-figures", help="flag needs_figure across the bank (text-based)")

    bf = sub.add_parser("backfill-figures", help="re-download + attach original figures for image questions")
    bf.add_argument("--dataset", default="Reja1/jee-neet-benchmark")
    bf.add_argument("--exam-prefix", default="JEE")
    bf.add_argument("--subject", default="Physics")
    bf.add_argument("--exam", default="JEE Advanced", help="bank exam name (drives the question-id prefix)")

    sub.add_parser("stats", help="show bank stats")

    t = sub.add_parser("tag", help="tag untagged verified questions (chapter/concept/difficulty/bloom)")
    t.add_argument("--limit", type=int, default=None, help="max questions to tag this run")

    q = sub.add_parser("query", help="retrieve questions by tag (the generator's read path)")
    q.add_argument("--chapter", default=None)
    q.add_argument("--subject", default=None)
    q.add_argument("--type", dest="qtype", default=None)
    q.add_argument("--difficulty", default=None, help="e.g. '3' or '3-4'")
    q.add_argument("-n", type=int, default=10)

    bg = sub.add_parser("batch-generate", help="PRE-FILL the shared question pool across a subject's taxonomy (frontend serves instantly)")
    bg.add_argument("--exam", default="JEE Advanced")
    bg.add_argument("--subject", default="Physics")
    bg.add_argument("--per-cell", type=int, default=15, help="target Qs per chapter×difficulty×type cell")
    bg.add_argument("--difficulties", default="2-3,3-4", help="comma-separated difficulty bands")
    bg.add_argument("--types", default="MCQ_single", help="comma-separated qtypes")
    bg.add_argument("--chapter", default=None, help="limit to one chapter")
    bg.add_argument("--exemplars", type=int, default=3)

    pst = sub.add_parser("pool-stats", help="coverage of the pre-generated shared pool")
    pst.add_argument("--exam", default="JEE Advanced")
    pst.add_argument("--subject", default="Physics")

    g = sub.add_parser("generate", help="RAG-generate a NEW test from tagged exemplars")
    g.add_argument("--exam", default="JEE Advanced")
    g.add_argument("--subject", default="Physics")
    g.add_argument("--chapter", required=True)
    g.add_argument("--concept", default=None)
    g.add_argument("--type", dest="qtype", default="MCQ_single")
    g.add_argument("--difficulty", default="3-4")
    g.add_argument("-n", type=int, default=5, help="questions in the test")
    g.add_argument("--exemplars", type=int, default=3)
    g.add_argument("--mock", action="store_true", help="offline plumbing demo (not real physics)")
    g.add_argument("--show-prompt", action="store_true", help="print the RAG prompt and exit (no LLM call)")
    g.add_argument("--out", default=None, help="write test JSON here")

    s = sub.add_parser("sample", help="print clean questions from the bank")
    s.add_argument("-n", type=int, default=3)
    s.add_argument("--all", action="store_true", help="include unverified")

    args = ap.parse_args()

    if args.cmd == "ingest-dataset":
        r = pipeline.ingest_open_dataset(
            dataset=args.dataset, subject=args.subject, subject_name=args.subject_name,
            exam=args.exam, limit=args.limit, llm_validate=args.llm_validate)
        _print_report(r)

    elif args.cmd == "ingest-grafite":
        r = pipeline.ingest_grafite(
            dataset=args.dataset, subject=args.subject, subject_name=args.subject_name,
            exam=args.exam, limit=args.limit, default_difficulty=args.difficulty,
            llm_validate=args.llm_validate)
        print(f"  source_rows: {r.get('source_rows')}")
        _print_report(r)

    elif args.cmd == "ingest-drop":
        from qbank import collector
        pdfs = collector.scan_drop_folder()
        if not pdfs:
            print(f"No PDFs in drop folder. Put files in {collector.config.DROP_DIR}")
            sys.exit(1)
        for pdf in pdfs:
            print(f"[ingest] {pdf}")
            r = pipeline.ingest_pdf(pdf, key_path=args.key, exam=args.exam,
                                    subject=args.subject, year=args.year)
            _print_report(r)

    elif args.cmd == "ingest-datavorous":
        subs = set(s.strip() for s in args.subjects.split(",")) if args.subjects else None
        r = pipeline.ingest_datavorous(
            dataset=args.dataset, want_exam=args.exam, subjects=subs,
            limit=args.limit, default_difficulty=args.difficulty,
            llm_validate=args.llm_validate, figures_only=args.figures_only)
        print(f"  skipped_wrong_subject: {r.get('skipped_wrong_subject')}")
        _print_report(r)

    elif args.cmd == "ingest-neet-bio":
        r = pipeline.ingest_neet_bio(
            dataset=args.dataset, subject_name=args.subject_name, exam=args.exam,
            limit=args.limit, default_difficulty=args.difficulty,
            llm_validate=args.llm_validate)
        print(f"  source_rows: {r.get('source_rows')}")
        _print_report(r)

    elif args.cmd == "ingest-images":
        r = pipeline.ingest_image_dataset(
            dataset=args.dataset, exam_prefix=args.exam_prefix, subject=args.subject,
            exam=args.exam, limit=args.limit)
        if r.get("error"):
            print("ERROR:", r["error"])
            sys.exit(1)
        print(f"  source_rows: {r.get('source_rows')}  unreadable: {r.get('unreadable')}")
        _print_report(r)

    elif args.cmd == "enrich-solutions":
        print(json.dumps(pipeline.enrich_solutions(
            chapter=args.chapter, limit=args.limit,
            exam=args.exam, subject=args.subject), indent=2))

    elif args.cmd == "retag":
        print(json.dumps(pipeline.retag(
            chapter=args.chapter, limit=args.limit,
            exam=args.exam, subject=args.subject), indent=2))

    elif args.cmd == "reverify":
        print(json.dumps(pipeline.reverify_solutions(
            chapter=args.chapter, k=args.k, limit=args.limit,
            exam=args.exam, subject=args.subject), indent=2))

    elif args.cmd == "mark-figures":
        print(json.dumps(pipeline.mark_needs_figure(), indent=2))

    elif args.cmd == "backfill-figures":
        print(json.dumps(pipeline.backfill_image_figures(
            dataset=args.dataset, exam_prefix=args.exam_prefix, subject=args.subject,
            exam=args.exam), indent=2))

    elif args.cmd == "stats":
        print(json.dumps(Store().stats(), indent=2))

    elif args.cmd == "batch-generate":
        def _prog(ch, band, qt, g, need, total):
            tag = "full, skip" if need == 0 else f"+{g}/{need} new"
            print(f"  [{ch[:34]:34s} | {band} | {qt}]  {tag}  (pool now {total})")
        r = pipeline.batch_generate(
            exam=args.exam, subject=args.subject, per_cell=args.per_cell,
            difficulties=tuple(x.strip() for x in args.difficulties.split(",")),
            qtypes=tuple(x.strip() for x in args.types.split(",")),
            chapters=[args.chapter] if args.chapter else None,
            k_exemplars=args.exemplars, on_progress=_prog)
        print(json.dumps(r, indent=2))

    elif args.cmd == "pool-stats":
        st = Store().pool_stats(args.exam, args.subject)
        by_ch = {}
        for (ch, d, qt), n in st.items():
            by_ch[ch] = by_ch.get(ch, 0) + n
        total = sum(by_ch.values())
        print(f"Pre-generated pool · {args.exam} {args.subject}: {total} questions across {len(by_ch)} chapters")
        for ch, n in sorted(by_ch.items(), key=lambda x: -x[1]):
            print(f"  {n:5d}  {ch}")

    elif args.cmd == "tag":
        from qbank import tagger
        from qbank.llm import LLM
        store, llm = Store(), LLM()
        todo = store.iter_untagged(limit=args.limit)
        print(f"[tag] {len(todo)} untagged questions | LLM={'on' if llm.ok else 'off (keyword fallback)'}")
        conf = {}
        for i, q in enumerate(todo, 1):
            tags = tagger.tag_question(q, llm=llm)
            store.update_tags(q.id, tags["chapter"], tags["concept"],
                              tags["difficulty"], tags["bloom"])
            conf[tags["confidence"]] = conf.get(tags["confidence"], 0) + 1
            if i % 25 == 0:
                print(f"    tagged {i}/{len(todo)}")
        print(f"[tag] done. confidence: {conf}")
        print(json.dumps(store.tag_distribution(), indent=2, ensure_ascii=False))

    elif args.cmd == "query":
        dmin = dmax = None
        if args.difficulty:
            parts = args.difficulty.split("-")
            dmin = int(parts[0])
            dmax = int(parts[-1])
        res = Store().retrieve(chapter=args.chapter, subject=args.subject,
                               qtype=args.qtype, dmin=dmin, dmax=dmax, limit=args.n)
        print(f"Retrieved {len(res)} question(s):")
        for q in res:
            print("=" * 72)
            print(f"[{q['id']}]  {q['chapter']} > {q['concept']}  "
                  f"| diff={q['difficulty']} | {q['qtype']} | answer={q['correct_answer']}")
            print(q["stem"][:220].replace("\n", " "))

    elif args.cmd == "generate":
        import os
        from qbank import generator
        from qbank.llm import LLM
        parts = args.difficulty.split("-")
        spec = {"exam": args.exam, "subject": args.subject, "chapter": args.chapter,
                "concept": args.concept, "qtype": args.qtype,
                "dmin": int(parts[0]), "dmax": int(parts[-1])}
        store = Store()

        if args.show_prompt:
            ex = generator.retrieve_exemplars(store, spec, k=args.exemplars)
            print(f"Retrieved {len(ex)} exemplars for {spec['chapter']} d{spec['dmin']}-{spec['dmax']}:")
            for e in ex:
                print(f"  - [{e['id']}] {e['concept']} (d{e['difficulty']})")
            system, user = generator.build_prompt(spec, ex)
            print("\n===== SYSTEM PROMPT =====\n" + system)
            print("\n===== USER PROMPT =====\n" + user)
            return

        llm = LLM()
        if not args.mock and not llm.ok:
            print("No LLM reachable. Real generation needs QBANK_LLM=on + proxy. "
                  "Try --show-prompt to see the RAG prompt, or --mock for a plumbing demo.")
            sys.exit(1)
        report = generator.generate_test(store, spec, llm=llm, count=args.n,
                                         k_exemplars=args.exemplars, mock=args.mock)
        if report.get("error"):
            print("ERROR:", report["error"])
            sys.exit(1)
        out = args.out or os.path.join(os.path.dirname(__file__), "tests_out",
                                       f"{args.chapter.replace(' ', '_')}_test.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n=== GENERATED TEST ({'MOCK' if report['mock'] else 'LLM'}) ===")
        print(f"  chapter          : {spec['chapter']}  (d{spec['dmin']}-{spec['dmax']}, {spec['qtype']})")
        print(f"  exemplars used   : {report['exemplars_used']}")
        print(f"  requested        : {report['requested']}")
        print(f"  generated (clean): {report['generated']}")
        print(f"  rejected         : {len(report['rejected'])}  {report['rejected'] if report['rejected'] else ''}")
        print(f"  written to       : {out}")
        for q in report["questions"][:2]:
            print("-" * 60)
            print(f"[{q['id']}] answer={q['correct_answer']}")
            print(q["stem"][:300])
            for o in q["options"]:
                print(f"   ({o['label']}) {o['text'][:80]}")

    elif args.cmd == "sample":
        for q in Store().sample(n=args.n, verified_only=not args.all):
            print("=" * 72)
            print(f"[{q['id']}]  {q['source']}  ({q['qtype']})  answer={q['correct_answer']}"
                  f"  verified={bool(q['verified'])}")
            print(q["stem"][:600])
            for o in q["options"]:
                print(f"   ({o['label']}) {o['text'][:120]}")
            if q["validation_issues"]:
                print("   issues:", q["validation_issues"])


if __name__ == "__main__":
    main()
