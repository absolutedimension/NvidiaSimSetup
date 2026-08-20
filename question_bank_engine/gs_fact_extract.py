#!/usr/bin/env python3
"""Turn sourced paragraphs into VERIFIED atomic facts, gated by a blind verifier.

The step this closes. gs_source_ingest gives paragraphs with citations; the statement forms need
atomic claims. Going from one to the other is extraction, and extraction is exactly where a model
asserts something its source does not say — "the 73rd Amendment gave Panchayati Raj constitutional
status" is right, but a model summarising the same paragraph could as easily produce "the 73rd
Amendment created Panchayati Raj", which is not what the book says and is wrong.

So nothing is trusted on the extractor's word. Each candidate claim goes to TWO other model calls
that never see the extractor's reasoning and are shown only the paragraph and the claim, asked one
question: does this paragraph support this claim exactly as written? Only unanimous YES survives.
The verifier is told to answer NO when the claim is merely plausible or generally true but not
stated here — plausible-but-unsourced is the failure this gate exists to catch, and it is the same
gate that found six wrong questions in the commission's own papers.

A surviving row keeps its citation, so the verification sheet can print "NCERT Class 10,
jess304.pdf, para 35 — open it and read" exactly as it prints a commission Model Answer page.

Usage (on the Gurukul VM, where the LiteLLM proxy lives):
    export QBANK_LLM_BASE_URL=http://127.0.0.1:4000/v1 QBANK_LLM_API_KEY=sk-...
    python3 gs_fact_extract.py --limit 40
"""
import argparse
import concurrent.futures as cf
import io
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "drop", "bssc", "GS_SOURCED_FACTS.jsonl")
OUT = os.path.join(HERE, "drop", "bssc", "GS_FACTS_VERIFIED.jsonl")

EXTRACT = """From the textbook passage below, extract up to {k} ATOMIC factual claims that a
General Studies exam could test. Each claim must be a single complete sentence that stands on its
own, states one fact, and is FULLY supported by this passage.

Do not infer, generalise, or add anything the passage does not state. Prefer claims with a
definite subject and a definite value — a year, an article, a name, a place, a definition.
Skip the passage entirely if it is narrative, an exercise, a caption, or has no testable fact.

DO NOT extract figures that come from a table, chart, graph or survey reported in the text —
percentages, growth rates, sample results. Every claim that failed verification in testing was of
that kind: a number read out of a table and then attached to a broader subject than the table
covers, such as turning one row into "ALL dictatorial regimes had a growth rate of 4.42". A number
is only safe here when the sentence itself states what it belongs to.

PASSAGE:
{para}

Reply with JSON only: {{"claims": ["...", "..."]}}  (an empty list is a fine answer)"""

VERIFY = """Below is a textbook passage and a claim. Answer ONE question: is the claim supported by
THIS passage, exactly as written?

Answer "no" if the claim is merely plausible, generally true, or something you know independently
but the passage does not state. Answer "no" if the claim changes, strengthens or generalises what
the passage says. Only "yes" if a careful reader would agree the passage states it.

PASSAGE:
{para}

CLAIM: {claim}

Reply with JSON only: {{"supported": true|false, "why": "<one short line>"}}"""


def ask(base, key, model, prompt, timeout=120):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40, help="paragraphs to process")
    ap.add_argument("--per-para", type=int, default=3)
    ap.add_argument("--extractor", default="gpt-5.6-terra")
    ap.add_argument("--verifiers", default="gpt-5.5,gpt-4o,gpt-5.6-sol",
                    help="Three, not two. With two, every single rejection in testing came from "
                         "ONE of them — gpt-4o dissenting while gpt-5.5 passed everything — so "
                         "unanimity was doing the work of agreement and the gate was effectively "
                         "single-verifier. A third makes a lone conservative model visible in the "
                         "vote rather than invisible behind the unanimity rule.")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    base = os.environ.get("QBANK_LLM_BASE_URL", "http://127.0.0.1:4000/v1")
    key = os.environ.get("QBANK_LLM_API_KEY", "")
    verifiers = [v.strip() for v in a.verifiers.split(",") if v.strip()]

    paras = [json.loads(l) for l in io.open(SRC, encoding="utf-8")][:a.limit]
    # RESUME. Each row records the paragraph it came from, so a run that died — or was stopped —
    # can pick up where it left off instead of paying for five thousand model calls again. This is
    # only possible because rows are written as they are verified; the first version held
    # everything in memory and wrote once at the end, so a crash at paragraph 800 lost all 800.
    done = set()
    if os.path.exists(OUT):
        for line in io.open(OUT, encoding="utf-8"):
            try:
                r = json.loads(line)
                done.add((r.get("title"), r.get("para")))
            except Exception:
                pass
    todo = [p for p in paras if (p.get("title"), p.get("para")) not in done]
    print(f"{len(paras)} paragraphs, {len(paras) - len(todo)} already done, {len(todo)} to do",
          flush=True)
    print(f"extractor {a.extractor}, verifiers {verifiers}", flush=True)
    paras = todo

    def handle(p):
        text = re.sub(r"\s+", " ", p["text"])[:1800]
        try:
            claims = ask(base, key, a.extractor,
                         EXTRACT.format(k=a.per_para, para=text)).get("claims", [])
        except Exception as e:
            return p, [], f"extract failed: {type(e).__name__}"
        kept = []
        for c in claims[:a.per_para]:
            if not isinstance(c, str) or len(c.split()) < 5:
                continue
            votes = []
            for m in verifiers:
                try:
                    votes.append(bool(ask(base, key, m,
                                          VERIFY.format(para=text, claim=c)).get("supported")))
                except Exception:
                    votes.append(False)
            kept.append((c, all(votes), votes))
        return p, kept, None

    stats = {"claims": 0, "kept": 0, "rejected": 0, "split": 0}
    dissent = {}
    seen_n = 0
    # Append and FLUSH as each paragraph finishes. A long unattended job that only writes at the
    # end is one crash away from having produced nothing.
    with io.open(OUT, "a", encoding="utf-8") as fh, \
            cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for p, kept, err in ex.map(handle, paras):
            seen_n += 1
            if err:
                print("  " + err, flush=True)
                continue
            for claim, ok, votes in kept:
                stats["claims"] += 1
                if ok:
                    stats["kept"] += 1
                    fh.write(json.dumps(
                        {"claim": claim, "source": p.get("source"), "title": p.get("title"),
                         "url": p.get("url"), "date": p.get("date"), "para": p.get("para"),
                         # the SAME text the verifier judged, not a shortened copy — a 600-char
                         # excerpt dropped the supporting sentence, so a stored fact could not be
                         # re-checked against its own citation
                         "passage": re.sub(r"\s+", " ", p["text"])[:1800]},
                        ensure_ascii=False) + "\n")
                    fh.flush()
                else:
                    stats["rejected"] += 1
                    if any(votes):
                        stats["split"] += 1
                        # a split is the interesting case: one verifier saw support and the other
                        # did not, which is where a miscalibrated gate shows itself
                        nos = [m for m, v in zip(verifiers, votes) if not v]
                        print(f"  SPLIT rejected-by={nos} {claim[:80]}", flush=True)
                        for m in nos:
                            dissent[m] = dissent.get(m, 0) + 1
            if seen_n % 25 == 0:
                print(f"  {seen_n}/{len(paras)} paragraphs | {stats['kept']} kept "
                      f"| {stats['rejected']} rejected", flush=True)
    c = stats["claims"] or 1
    print(f"\n  {stats['claims']} claims extracted")
    print(f"  {stats['kept']} survived BOTH verifiers ({100 * stats['kept'] / c:.0f}%)")
    print(f"  {stats['rejected']} rejected, of which {stats['split']} split the verifiers "
          f"— those are the ones worth reading")
    if dissent:
        print(f"  dissents by verifier: {dissent}")
        if len(dissent) == 1:
            print(f"  WARNING: every rejection came from ONE verifier. Unanimity is doing the "
                  f"work of agreement, and the gate is effectively single-verifier.")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
