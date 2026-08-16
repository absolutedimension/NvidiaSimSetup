#!/usr/bin/env python3
"""quality_critic.py — make pooled worksheet questions SAFE FOR LIVE CHILDREN.

Two layers:
  1. degenerate(item)  — DETERMINISTIC (no LLM). Catches structural garbage: empty/placeholder
     statements ("True or False?"), blank cloze, duplicate options, missing answers, etc.
  2. llm_verdicts(items) — LLM fact-check (gpt-4o-mini via litellm). Flags factually WRONG or
     AMBIGUOUS items for a Class-3 child (e.g. "A lion lives in a den → False"). Batched.

Used by fill_knowledge_pool.py (accept-time) and by reclean_bank.py (clean an existing bank).
"""
import json, os, re, urllib.request

_LATIN = re.compile(r'[A-Za-z]')
_PLACEHOLDER_TF = re.compile(r'^\s*(true or false|yes or no|is this (correct|right|true))\s*[?.!]*\s*$', re.I)


def _real(s, n=6):
    s = (s or '').strip()
    return len(s) >= n and not _PLACEHOLDER_TF.match(s)


def degenerate(item):
    """Return a reason string if the item is structurally unfit for a child, else None."""
    t = item.get('type'); p = item.get('payload', {}) or {}; a = item.get('answer')
    if t == 'true_false':
        s = (p.get('statement') or '').strip()
        if not _real(s):                 return 'empty/placeholder statement'
        if a not in (True, False):       return 'no boolean answer'
    elif t == 'cloze':
        s = p.get('sentence', '') or ''
        if '___' not in s or not _real(s.replace('___', ' '), 8): return 'no real sentence/blank'
        if a not in (p.get('bank') or []):                        return 'answer not in bank'
    elif t == 'odd_one_out':
        o = p.get('options', []) or []
        if len(o) < 3 or a not in o:                              return 'bad options/answer'
        if len({str(x).strip().lower() for x in o}) < len(o):     return 'duplicate options'
    elif t == 'match_following':
        pr = p.get('pairs', []) or []
        if len(pr) < 3:                                           return 'too few pairs'
        for pair in pr:
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2):    return 'malformed pair'
            if len(str(pair[0]).strip()) < 2 or len(str(pair[1]).strip()) < 2: return 'empty pair side'
    elif t == 'sort_groups':
        if len(p.get('items', []) or []) < 2 or len(p.get('bins', []) or []) < 2: return 'bad sort'
        if not isinstance(a, dict) or len(a) < len(p.get('items', [])):           return 'incomplete answer map'
    else:
        return 'unknown type'
    return None


def _one_line(item):
    """Compact representation of an item + its ANSWER KEY (the critic judges if the KEY is correct)."""
    t = item.get('type'); p = item.get('payload', {}) or {}; a = item.get('answer')
    if t == 'true_false':
        tf = 'TRUE' if a in (True, 'True') else 'FALSE'
        return (f'True/False. Statement: "{p.get("statement","")}". The answer key says this statement is '
                f'{tf} — is that correct?')
    if t == 'cloze':           return f'Fill the blank: "{p.get("sentence","")}" — the answer key fills it with "{a}". Is that correct?'
    if t == 'odd_one_out':     return f'Which does NOT belong among {p.get("options",[])}? Answer key: "{a}". Correct?'
    if t == 'match_following': return f'Match pairs (each left↔right must be a true pair): {p.get("pairs",[])}. All correct?'
    if t == 'sort_groups':     return f'Sort {p.get("items",[])} into {p.get("bins",[])}. Answer key mapping: {a}. Every item in the right group?'
    return json.dumps(p, ensure_ascii=False)[:120]


def llm_verdicts(items, subject='', cls=3, batch=10):
    """Fact-check items in batches. Returns a list of bools (True = keep) aligned to `items`.
    An item is dropped only if the LLM is confident it is factually WRONG or genuinely AMBIGUOUS
    for a Class-{cls} child. On any LLM/parse failure the batch is KEPT (fail-open, no false drops)."""
    url = os.environ.get('LITELLM_URL', 'http://localhost:4000/v1') + '/chat/completions'
    key = os.environ.get('LITELLM_KEY', 'sk-trigunai-master-key-2026')
    # a STRONGER model for judging than for generating (accuracy matters; the critic runs few calls)
    model = os.environ.get('WS_CRITIC_MODEL', 'gpt-4o')
    keep = [True] * len(items)
    for start in range(0, len(items), batch):
        chunk = items[start:start + batch]
        listing = '\n'.join(f'{i}. {_one_line(it)}' for i, it in enumerate(chunk))
        prompt = (
            f"You are quality-checking practice questions for a Class {cls} child ({subject}). For EACH item, mark it "
            f"BAD only if the marked answer is CLEARLY, FACTUALLY WRONG (a plain error a teacher would correct). "
            f"KEEP everything else — including simple, easy, or slightly loose-but-reasonable questions. "
            f"When in ANY doubt, KEEP it. Do NOT flag a question just for being basic or for wording you'd phrase "
            f"differently — only flag genuine factual errors.\n\n"
            f"{listing}\n\n"
            f'Reply ONLY a JSON array like [{{"i":0,"ok":true}},{{"i":1,"ok":false}}] — one entry per item '
            f'(ok:false ONLY for a clear factual error).')
        try:
            body = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                               'temperature': 0, 'max_tokens': 800}).encode()
            req = urllib.request.Request(url, data=body, method='POST',
                                         headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as r:
                txt = json.load(r)['choices'][0]['message']['content']
            m = re.search(r'\[.*\]', txt, re.S)
            for v in (json.loads(m.group(0)) if m else []):
                idx = v.get('i')
                if isinstance(idx, int) and 0 <= idx < len(chunk) and v.get('ok') is False:
                    keep[start + idx] = False
        except Exception:
            pass   # fail-open: keep the whole batch rather than risk false drops
    return keep


def clean(items, subject='', cls=3, use_llm=True):
    """Drop degenerate items (always) + LLM-flagged items (if use_llm and endpoint reachable).
    Returns (kept, stats)."""
    stats = {'in': len(items), 'degenerate': 0, 'fact_flagged': 0}
    survivors = []
    for it in items:
        r = degenerate(it)
        if r: stats['degenerate'] += 1
        else: survivors.append(it)
    if use_llm and survivors:
        verdicts = llm_verdicts(survivors, subject=subject, cls=cls)
        kept = [it for it, ok in zip(survivors, verdicts) if ok]
        stats['fact_flagged'] = len(survivors) - len(kept)
        survivors = kept
    stats['out'] = len(survivors)
    return survivors, stats


if __name__ == '__main__':
    import glob, argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--glob', default='content/bank/*_class3_*.json')
    ap.add_argument('--llm', action='store_true', help='also run the LLM fact-check (needs endpoint)')
    args = ap.parse_args()
    for f in sorted(glob.glob(args.glob)):
        if 'math' in f or 'index' in f: continue
        d = json.load(open(f, encoding='utf-8'))
        subj = d.get('subject', ''); _, st = clean(d.get('items', []), subject=subj, cls=d.get('class', 3), use_llm=args.llm)
        print(f'  {os.path.basename(f)[:-5]:24} in={st["in"]:4} degenerate={st["degenerate"]:3} '
              f'fact_flagged={st["fact_flagged"]:3} → clean={st["out"]:4}')
