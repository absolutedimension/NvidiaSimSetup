#!/usr/bin/env python3
"""Column-aware verbatim extractor for BPSC TRE question booklets.

BPSC TRE papers (bpsc.bihar.gov.in -> Teacher Recruitment Examinations) are
digitally-generated, TEXT-LAYER PDFs (unlike the scanned BPSC Prelims papers that
need Qwen vision OCR). They are 2-column, column-major, and BILINGUAL — each
question appears in English then Hindi (legacy non-Unicode font). We serve the
ENGLISH text.

Layout facts (verified 2026-08-14):
  * 2 columns; split near page-width/2; read left column top->bottom, then right.
  * 5 options (A-E); D is almost always "More than one of the above", E "None of
    the above" — we anchor on this cluster (robust vs. numbered instruction lines).
  * English option cluster precedes the Hindi one for the same question.

OUTPUT = verbatim questions with NO answer key. TRE official answer keys live only
on bpsc.bih.nic.in, which is firewalled from all our egress paths, so these are
STAGED (generated=0, verified=0) and MUST NOT be served until an official key is
matched. See SRB_PYQ_SOURCING_GUIDE.md.

Note: math/quant questions contain fractions/superscripts that reflow imperfectly
in any text layer — those stems/options may need manual cleanup or vision OCR for
perfect fidelity. GS / Science / Polity / English extract cleanly.
"""
import pymupdf, re, sys, json, os, glob

ENG_D = "More than one of the above"
ENG_E = "None of the above"


def page_reading_order(pg):
    W = pg.rect.width
    mid = W / 2.0
    words = pg.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    if not words:
        return ""
    left = [w for w in words if (w[0] + w[2]) / 2 < mid]
    right = [w for w in words if (w[0] + w[2]) / 2 >= mid]

    def col_text(ws):
        ws = sorted(ws, key=lambda w: (round(w[1] / 4.0), w[0]))
        lines, cur, cur_y = [], [], None
        for w in ws:
            y = w[1]
            if cur_y is None or abs(y - cur_y) <= 5:
                cur.append(w)
                cur_y = y if cur_y is None else cur_y
            else:
                lines.append(cur); cur = [w]; cur_y = y
        if cur:
            lines.append(cur)
        return "\n".join(" ".join(w[4] for w in sorted(ln, key=lambda w: w[0])) for ln in lines)

    return col_text(left) + "\n" + col_text(right)


def flatten(path):
    d = pymupdf.open(path)
    txt = "\n".join(page_reading_order(d[i]) for i in range(d.page_count))
    txt = re.sub(r'\s*\n\s*', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


# One option cluster: (A)...(B)...(C)...(D)...(E)...  The (E) value stops at the
# next option-A, the next question number ("12. "), a PART header, or a P.T.O — so
# it does NOT swallow the following question's stem.
CLUSTER = re.compile(
    r'\(A\)\s*(?P<A>.*?)\s*\(B\)\s*(?P<B>.*?)\s*\(C\)\s*(?P<C>.*?)\s*'
    r'\(D\)\s*(?P<D>.*?)\s*\(E\)\s*(?P<E>.*?)'
    r'(?=\s*\(A\)|\s+\d{1,3}\.\s|\s*PART\s*[—–-]|\s*\[\s*P\.T\.O|\Z)',
    re.S)

FOOTER = re.compile(r'\d+\s*/\s*[A-Z]+\s*/\s*[A-Z]?\s*[-–]?\s*\d{2,4}[^ ]*(?:/\S+)?\s*\d*')


def clean(s):
    s = FOOTER.sub(' ', s)
    s = re.sub(r'\[\s*P\.T\.O[^\]]*\]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def is_english(m):
    d, e = m.group('D'), m.group('E')
    # English cluster: D/E carry the standard English boilerplate
    return (ENG_D.lower() in d.lower()) or (ENG_E.lower() in e.lower())


def extract(path):
    flat = flatten(path)
    out = []
    last_end = 0
    prev_qno = 0
    for m in CLUSTER.finditer(flat):
        if not is_english(m):
            last_end = m.end()
            continue
        # stem = text between previous cluster end and this (A)
        pre = flat[last_end:m.start()]
        last_end = m.end()
        # Locate this question's number marker. Decimals/ratios inside a math stem
        # ("1 : 3. 5 years") look like "N." markers, so DON'T take the last one — take the
        # marker whose number CONTINUES the sequence (prev_qno+1..+3); that is the real
        # question number and sits at the stem's start, so nothing gets truncated.
        markers = [(mo.end(), int(mo.group(1)))
                   for mo in re.finditer(r'(?:^|\s)(\d{1,3})\.\s', pre)]
        qno, stem = None, pre
        for target in (prev_qno + 1, prev_qno + 2, prev_qno + 3):
            hit = [mk for mk in markers if mk[1] == target]
            if hit:
                qno, stem = hit[0][1], pre[hit[0][0]:]
                break
        if qno is None:                       # sequence broke — fall back to last marker
            if markers:
                qno, stem = markers[-1][1], pre[markers[-1][0]:]
            else:
                qno = prev_qno + 1
        stem = clean(stem)
        # strip leading structural noise: "[ P.T.O.", "PART—II ( ... )", "P-26." labels
        stem = re.sub(r'^\s*\[\s*P\.T\.O\.?\s*\]?\.?', '', stem)
        stem = re.sub(r'^\s*PART\s*[—–-]\s*[IVX]+\s*\([^)]*\)?', '', stem)
        stem = re.sub(r'^\s*\(?\s*[A-Z ]{3,}\s*\)', '', stem)  # dangling "( GENERAL STUDIES )"
        stem = re.sub(r'^\s*P\s*[-–]\s*\d{1,3}\s*\.?\s*', '', stem)  # Part-II "P-26."
        stem = re.sub(r'^\s*[—–-]\s*', '', stem)
        stem = stem.strip()
        opts = {k: clean(m.group(k)) for k in ['A', 'B', 'C', 'D', 'E']}
        # normalize the two boilerplate options
        opts['D'] = ENG_D if ENG_D.lower() in opts['D'].lower() else opts['D']
        opts['E'] = ENG_E if ENG_E.lower() in opts['E'].lower() else opts['E']
        if len(stem) < 4:
            continue
        # sanity: qno should be increasing & plausible
        if not (0 < qno <= 250):
            qno = prev_qno + 1
        prev_qno = qno
        out.append({"q_no": qno, "stem": stem, "options": opts})
    return out


def main():
    args = sys.argv[1:]
    to_json = None
    if '--out' in args:
        i = args.index('--out'); to_json = args[i + 1]; args = args[:i] + args[i + 2:]
    paths = []
    for a in args:
        paths.extend(sorted(glob.glob(a)) if any(c in a for c in '*?[') else [a])
    allq = {}
    for p in paths:
        qs = extract(p)
        allq[os.path.basename(p)] = qs
        print(f"{len(qs):4d} Q  {os.path.basename(p)}")
        if len(paths) == 1:
            for q in qs[:4] + qs[-2:]:
                print("-" * 50)
                print(f"Q{q['q_no']}. {q['stem'][:200]}")
                for lab in 'ABCDE':
                    print(f"   ({lab}) {q['options'][lab][:90]}")
    if to_json:
        json.dump(allq, open(to_json, 'w'), ensure_ascii=False, indent=1)
        total = sum(len(v) for v in allq.values())
        print(f"\nwrote {to_json}  ({len(allq)} papers, {total} questions)")


if __name__ == "__main__":
    main()
