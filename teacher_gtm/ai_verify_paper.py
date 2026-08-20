#!/usr/bin/env python3
"""Solve a delivered paper BLIND with several models, then compare against the printed key.

What this is for, and what it is not.

Deepak's ask: don't make me check it by hand — have the AI verify the answers. That is worth doing,
but only if we are honest about what an agreement proves.

  * For the 206 OFFICIAL questions the commission's own key IS the correct answer, by definition.
    A model cannot overrule it. What a disagreement DOES mean is that something is wrong on our
    side and needs a look: our transcription changed a number or a word, we recorded the wrong
    letter, the options got reordered, or the question is genuinely stale/ambiguous and should be
    pulled. So the model is a DEFECT DETECTOR pointed at our pipeline, not an authority on the
    answer. That is exactly the check a human proof-reader cannot do 300 times without tiring.

  * For the 94 GENERATED questions the answer is computed, and test_papers.py already re-derives
    all 94 with deterministic solvers written from the question text. That is STRONGER evidence
    than a model's opinion — arithmetic does not have opinions. The model pass is a second,
    weaker check that mainly catches a stem that reads ambiguously to a fluent reader.

Three independent passes, because three tries at the same prompt is not independence:

  1. English text, model A
  2. HINDI text only, model A          <- a genuinely different route through the question. If the
                                          two languages disagree, the two halves of the question
                                          have drifted apart, and NO English-side check can see it.
  3. English text, model B             <- a different model, so a shared blind spot shows up.

Every pass is blind: the key is never in the prompt, and the model is told it may answer "X" for
"no option is correct" or "more than one is correct", which is how a defective question announces
itself instead of being forced into a guess.

Usage (on the Gurukul VM, where the LiteLLM proxy lives):
    export QBANK_LLM_BASE_URL=http://127.0.0.1:4000/v1 QBANK_LLM_API_KEY=sk-...
    python3 ai_verify_paper.py --html OneStep_BSSC_InterLevel_Set1.html --out Set1_aiverify.json
"""
import argparse
import concurrent.futures as cf
import html as htmllib
import io
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

Q_BLOCK = re.compile(r'<div class="q">(.*?)</div></div>', re.S)
KEY_ITEM = re.compile(r'<span class="k">(\d+)\.\s*<b>([A-D])</b>(<i>\*</i>)?</span>')
HI_DIV = re.compile(r'<div class="hi">(.*?)</div>', re.S)
EN_DIV = re.compile(r'<div class="en">(.*?)</div>', re.S)
OPS_DIV = re.compile(r'<div class="ops">(.*?)</div>', re.S)
OPT_LABEL = re.compile(r'^\s*<b>\(([A-D])\)</b>(.*)$', re.S)
TAGS = re.compile(r"<[^>]+>")

PROMPT = """You are sitting the Bihar Staff Selection Commission 2nd Inter Level (10+2) preliminary
examination. Answer this multiple-choice question.

{q}

Reply with JSON only: {{"answer": "<A|B|C|D|X>", "why": "<one short line>", "sure": <true|false>}}

Use "X" — do not guess a letter — if NO option is correct, if MORE THAN ONE option is correct, or
if the question cannot be answered as written. Say which in "why". A defective question is a useful
finding; a guess is not."""


FRAC = re.compile(r'<span class="fr"><span class="nu">(.*?)</span>'
                  r'<span class="de">(.*?)</span></span>', re.S)
RAD = re.compile(r'<span class="rad">(.*?)</span>', re.S)


def text(s):
    """HTML back to text a solver can read — UN-TYPESETTING the maths, not deleting it.

    Stripping tags looked fine and was quietly destroying the questions: a stacked 1/4 became the
    digits "14", so the models were asked for the L.C.M. of 14 and 25 and correctly answered that
    350 is not among the options. Four of the ten unanimous 'disagreements' in the first clean run
    were this bug, not the paper. A verifier fed a corrupted question reports a defect that is its
    own — the worst kind of false alarm, because it looks exactly like a real one.
    """
    s = s or ""
    for _ in range(3):                                    # nested fractions
        s, n = FRAC.subn(lambda m: f"({m.group(1)})/({m.group(2)})", s)
        if not n:
            break
    s = RAD.sub(lambda m: f"sqrt({m.group(1)})", s)
    s = re.sub(r"<sup>(.*?)</sup>", r"^\1", s, flags=re.S)
    s = re.sub(r"<sub>(.*?)</sub>", r"_\1", s, flags=re.S)
    return re.sub(r"\s+", " ", htmllib.unescape(TAGS.sub("", s))).strip()


def options_of(segment):
    """The options in one rendered <div class="ops">, splitting on the OPENING tag.

    A regex ending at `</span>` cannot do this: an option holding a stacked fraction contains
    nested spans, so a non-greedy match stopped at the inner one and returned "1" for 1/20 and
    "K = 1" for K = ½mv². Splitting on the opening tag is nesting-proof, and text() throws the
    stray closing tag away with everything else.

    key_from_delivered.py carries its own copy of this: that module pulls in the whole builder
    stack, and this script has to run alone on the VM where the model proxy lives.
    """
    # Cut the segment at its own closing tag first. Splitting the block on the OPENING <div
    # class="ops"> makes each segment run to the NEXT options block, so the final option of the
    # Hindi half swallowed the English stem that follows it — the Hindi route was being asked to
    # choose between an option and an option-plus-a-question. The last options block in a question
    # has no closing tag (Q_BLOCK consumed it), and split() handles that by returning it whole.
    out = []
    segment = segment.split("</div>")[0]
    for chunk in segment.split('<span class="op">')[1:]:
        m = OPT_LABEL.match(chunk)
        if m:
            out.append((m.group(1), text(m.group(2))))
    return out


def parse_blind(path):
    """The paper's questions WITHOUT its answers, plus the key held aside for the comparison."""
    doc = io.open(path, encoding="utf-8").read()
    keys = {int(n): (l, bool(star)) for n, l, star in KEY_ITEM.findall(doc)}
    items = []
    for i, block in enumerate(Q_BLOCK.findall(doc), 1):
        # Split on the OPENING tag, never match the closing one: Q_BLOCK ends at the first
        # `</div></div>`, which eats the final options div's closing tag. A regex that required
        # it therefore returned NO options for every question whose options block is last — i.e.
        # every English-only question — and the models dutifully answered "no options were
        # provided" for 21 perfectly good questions. Silent, and it looked like a paper defect.
        ops = [options_of(seg) for seg in block.split('<div class="ops">')[1:]]
        hi_stem = text(HI_DIV.search(block).group(1)) if HI_DIV.search(block) else ""
        en_stem = text(EN_DIV.search(block).group(1)) if EN_DIV.search(block) else ""
        # the Hindi half is printed first, so its option block is the first one
        hi_ops = ops[0] if ops else []
        en_ops = ops[-1] if len(ops) > 1 else hi_ops
        if len(hi_ops) != 4 or len(en_ops) != 4:
            raise SystemExit(f"Q{i}: parsed {len(hi_ops)}/{len(en_ops)} options — a solver that "
                             f"is not shown the options is not a verification of anything")
        items.append({
            "n": i,
            "hi": re.sub(r"^\d+\.\s*", "", hi_stem),
            "en": re.sub(r"^\d+\.\s*", "", en_stem),
            "hi_options": hi_ops,
            "en_options": en_ops,
            "key": keys[i][0],
            "generated": keys[i][1],
        })
    return items


def as_question(item, lang):
    stem = item[lang] or item["en"] or item["hi"]
    ops = item[f"{lang}_options"] or item["en_options"]
    return stem + "\n" + "\n".join(f"({l}) {t}" for l, t in ops)


def ask(base, key, model, question, timeout=180):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(q=question)}],
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)["choices"][0]["message"]["content"]
    try:
        d = json.loads(out)
    except Exception:
        m = re.search(r'"answer"\s*:\s*"([A-DX])"', out or "")
        d = {"answer": m.group(1) if m else "?", "why": (out or "")[:160], "sure": False}
    a = str(d.get("answer", "?")).strip().upper()[:1]
    return {"answer": a if a in "ABCDX" else "?", "why": str(d.get("why", ""))[:300],
            "sure": bool(d.get("sure"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-a", default="gpt-5.6-terra")
    ap.add_argument("--model-b", default="gpt-5.5")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="first N questions only (smoke test)")
    a = ap.parse_args()

    base = os.environ.get("QBANK_LLM_BASE_URL", "http://127.0.0.1:4000/v1")
    api = os.environ.get("QBANK_LLM_API_KEY", "")
    items = parse_blind(a.html)
    if a.limit:
        items = items[:a.limit]
    print(f"{len(items)} questions from {os.path.basename(a.html)} "
          f"({sum(1 for i in items if i['generated'])} generated)")

    # (item, pass-name, model, language) — three genuinely different routes, see the module docstring
    jobs = [(it, name, model, lang) for it in items for name, model, lang in
            (("en_a", a.model_a, "en"), ("hi_a", a.model_a, "hi"), ("en_b", a.model_b, "en"))]
    results = {}

    def run(job):
        it, name, model, lang = job
        try:
            return it["n"], name, ask(base, api, model, as_question(it, lang))
        except Exception as e:
            return it["n"], name, {"answer": "?", "why": f"error: {e}"[:200], "sure": False}

    done = 0
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, name, res in ex.map(run, jobs):
            results.setdefault(n, {})[name] = res
            done += 1
            if done % 60 == 0:
                print(f"  {done}/{len(jobs)}", flush=True)

    rows, disagree, split, flagged = [], [], [], []
    for it in items:
        r = results.get(it["n"], {})
        votes = [r.get(k, {}).get("answer", "?") for k in ("en_a", "hi_a", "en_b")]
        agree = sum(1 for v in votes if v == it["key"])
        row = dict(it, votes=votes, agree_with_key=agree, detail=r)
        row.pop("detail_hi", None)
        rows.append(row)
        if agree == 0:
            disagree.append(row)          # all three routes reject the printed key
        elif agree < 3:
            split.append(row)             # the routes do not agree with each other
        if "X" in votes:
            flagged.append(row)           # at least one route calls the question defective

    json.dump({"file": os.path.basename(a.html), "models": [a.model_a, a.model_b],
               "rows": rows}, io.open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    n = len(items)
    full = sum(1 for r in rows if r["agree_with_key"] == 3)
    print(f"\n  all three routes agree with the printed key : {full}/{n} "
          f"({100.0 * full / n:.1f}%)")
    print(f"  routes split (1 or 2 of 3)                  : {len(split)}")
    print(f"  ALL THREE disagree with the key             : {len(disagree)}  <- read these")
    print(f"  a route called the question defective ('X') : {len(flagged)}")
    for r in disagree:
        print(f"\n  Q{r['n']} key={r['key']} votes={r['votes']} "
              f"{'[generated]' if r['generated'] else ''}\n    {r['en'][:110]}"
              f"\n    {r['detail'].get('en_a', {}).get('why', '')[:160]}")
    print(f"\n  -> {a.out}")


if __name__ == "__main__":
    main()
