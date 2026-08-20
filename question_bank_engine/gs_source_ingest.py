#!/usr/bin/env python3
"""Ingest OFFICIAL government sources into a citable General Studies fact store.

Why this exists. Our generated GS questions are correct but UNSOURCED: they look facts up in tables
hand-written inside staticgkgen.py. That was fine while the paper also carried real commission
questions — those carried their own provenance. On a fully generated paper it is the weak link,
because the verification sheet can only say "our table says Bhubaneswar" where it used to say
"Advt 03/25 question 67, open the PDF and read row 67".

So every fact ingested here keeps the citation that makes it checkable by someone who does not
already know the answer:

    {"text": "...", "source": "PIB", "title": "...", "url": "...", "date": "2026-05-14",
     "para": 3, "ingested": "..."}

A question generated from a row can then print "PIB release 14.05.2026, para 3" — a document the
student can open, which is exactly the standard the official questions met.

Two paths in, because that is how these sources actually arrive:

  --url    PIB press releases and any other government page. Government works are free to reuse;
           we take the FACTS and write our own questions, never the page's wording.
  --drop   Any official PDF or text file placed in drop/gs_sources/ — NCERT chapters, the Economic
           Survey, the Bihar Economic Survey. ncert.nic.in does not resolve from this machine, and
           the big survey documents are PDFs anyway, so the drop folder is the primary path and
           the fetcher is the convenience.

NOT copied: a source's SELECTION of facts. Taking one channel's curated "Top 50 current affairs"
list would be taking their editorial judgement, which is theirs. Facts scattered across primary
government documents are nobody's.

Dating matters. Current affairs expire, and EXCLUSIONS.json already carries "stale current affairs"
as a standing rule — every row here is dated so a generator can refuse anything older than it wants.

Usage:
    python3 gs_source_ingest.py --url https://www.pib.gov.in/PressReleasePage.aspx?PRID=...
    python3 gs_source_ingest.py --drop            # everything in drop/gs_sources/
"""
import argparse
import datetime as _dt
import glob
import io
import json
import os
import re
import ssl
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DROP = os.path.join(HERE, "drop", "gs_sources")
STORE = os.path.join(HERE, "drop", "bssc", "GS_SOURCED_FACTS.jsonl")

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
DATE = re.compile(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})")
_MON = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def _clean(t):
    return WS.sub(" ", t).strip()


def _paragraphs(text, min_words=12):
    """Paragraphs worth keeping. A one-line fragment cannot support a question, and a wall of
    boilerplate ('Ministry of ...') is not a fact — both are dropped rather than stored and
    filtered later, so the store stays something a human can read end to end."""
    out = []
    for p in re.split(r"\n\s*\n|(?<=[.।])\s{2,}", text):
        p = _clean(p)
        if len(p.split()) >= min_words and not p.lower().startswith("posted on"):
            out.append(p)
    return out


def _date_in(text, fallback=None):
    m = DATE.search(text or "")
    if m:
        d, mon, y = int(m.group(1)), _MON[m.group(2)], int(m.group(3))
        try:
            return _dt.date(y, mon, d).isoformat()
        except ValueError:
            pass
    return fallback


def from_url(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE          # the commission's SSL chain fails in urllib; PIB's too
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
        html = r.read().decode("utf-8", "ignore")
    title = _clean(TAG.sub(" ", (re.search(r"<title>(.*?)</title>", html, re.S) or
                                 re.match("", "")).group(1) if "<title>" in html else "")) or url
    body = re.sub(r"(?is)<(script|style|nav|footer|header).*?</\1>", " ", html)
    text = TAG.sub("\n", body)
    date = _date_in(text)
    return [{"text": p, "source": "PIB" if "pib.gov.in" in url else "web",
             "title": title[:160], "url": url, "date": date, "para": i + 1}
            for i, p in enumerate(_paragraphs(text))]


def from_file(path):
    if path.lower().endswith(".pdf"):
        try:
            import pypdf
        except ImportError:
            print(f"  {os.path.basename(path)}: pypdf not installed, skipped")
            return []
        pages = pypdf.PdfReader(path).pages
        text = "\n\n".join((pg.extract_text() or "") for pg in pages)
    else:
        text = io.open(path, encoding="utf-8", errors="ignore").read()
    name = os.path.basename(path)
    return [{"text": p, "source": "drop", "title": name, "url": f"file://{name}",
             "date": _date_in(text), "para": i + 1}
            for i, p in enumerate(_paragraphs(text))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--drop", action="store_true")
    ap.add_argument("--store", default=STORE)
    a = ap.parse_args()

    rows = []
    for u in a.url:
        try:
            got = from_url(u)
            print(f"  {len(got):4d} paragraphs from {u[:70]}")
            rows += got
        except Exception as e:
            print(f"  FAILED {u[:60]}: {type(e).__name__} {e}")
    if a.drop:
        os.makedirs(DROP, exist_ok=True)
        files = sorted(glob.glob(os.path.join(DROP, "*")))
        if not files:
            print(f"  drop/gs_sources/ is empty — put official PDFs or text there "
                  f"(NCERT chapters, Economic Survey, Bihar Economic Survey)")
        for f in files:
            got = from_file(f)
            print(f"  {len(got):4d} paragraphs from {os.path.basename(f)}")
            rows += got

    # append, de-duplicating on the text itself so re-running a source is harmless
    seen = set()
    if os.path.exists(a.store):
        for line in io.open(a.store, encoding="utf-8"):
            try:
                seen.add(json.loads(line)["text"])
            except Exception:
                pass
    stamp = _dt.date.today().isoformat()
    added = 0
    with io.open(a.store, "a", encoding="utf-8") as fh:
        for r in rows:
            if r["text"] in seen:
                continue
            seen.add(r["text"])
            r["ingested"] = stamp
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            added += 1
    dated = sum(1 for r in rows if r.get("date"))
    print(f"\n  {added} new facts stored, {len(rows) - added} already present")
    print(f"  {dated} of {len(rows)} carry a date — undated rows cannot be expired, so a "
          f"current-affairs generator must skip them")
    print(f"  -> {a.store}")


if __name__ == "__main__":
    main()
