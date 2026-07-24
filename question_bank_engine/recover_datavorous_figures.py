#!/usr/bin/env python3
"""Phase 1 — figure recovery for datavorous diagram questions.

Datavorous embeds diagrams as <img src="https://cdn-question-pool.getmarks.app/...">.
Our text ingest stripped them, leaving figure-dependent questions with no image. This
re-reads the source, downloads the figure(s) from the CDN, and attaches them to the
already-banked row — the stem/key/solution are already there, only the figure was missing.

Matching: `from_datavorous_row` builds a DETERMINISTIC id from the stem, so we recompute
the same id and update that row (no fuzzy matching). Idempotent — a row whose figure is
already a local file is skipped.

    python3 recover_datavorous_figures.py --exam NEET [--limit N] [--workers 8] [--apply]

Dry-run by default (reports match rate + a few downloads, writes nothing).
"""
import argparse
import os
import re
import sqlite3
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from datasets import load_dataset

from qbank import config, extractor
from qbank.storage import Store

_IMG = re.compile(r"<img[^>]*>", re.I)
_SRC = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.I)
_UA = {"User-Agent": "Mozilla/5.0 (TrigunAI question-bank figure fetch)"}


def _img_srcs(row) -> list[str]:
    """CDN urls from the QUESTION + OPTIONS html (not the solution — we serve the question)."""
    blob = (row.get("question") or "") + " " + (row.get("options") or "")
    out, seen = [], set()
    for tag in _IMG.findall(blob):
        m = _SRC.search(tag)
        if not m:
            continue
        u = m.group(1).strip()
        if u.startswith("http") and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _ext_of(data: bytes) -> str | None:
    """Sniff image type from magic bytes — URLs are a mix of .png/.jpg and extension-less."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _download(url: str, dest_dir: str, base: str) -> str | None:
    """Download → save as <base>.<real-ext>. Returns the saved filename, or None."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=_UA)
            data = urllib.request.urlopen(req, timeout=30).read()
            ext = _ext_of(data)
            if len(data) < 100 or not ext:          # too small / not an image
                return None
            name = f"{base}.{ext}"
            with open(os.path.join(dest_dir, name), "wb") as f:
                f.write(data)
            return name
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", default="NEET", help="NEET | JEE Main | JEE Advanced")
    ap.add_argument("--dataset", default="datavorous/entrance-exam-dataset")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    os.makedirs(config.FIG_DIR, exist_ok=True)
    store = Store()
    banked = {r[0] for r in store.con.execute("SELECT id FROM questions WHERE exam=?", (args.exam,))}
    print(f"[{args.exam}] banked rows: {len(banked)}")

    ds = load_dataset(args.dataset, split="train")
    # collect (qid, [urls]) for source rows that (a) are this exam, (b) have a figure,
    # (c) map to a banked row, (d) aren't already recovered. Dedup by qid (the source
    # repeats questions across papers → same deterministic id).
    seen_qid = set()
    already_files = {f.rsplit(".", 1)[0] for f in os.listdir(config.FIG_DIR)} if os.path.isdir(config.FIG_DIR) else set()
    jobs = []
    considered = matched = already = 0
    for row in ds:
        if args.exam not in (row.get("tags") or ""):
            continue
        srcs = _img_srcs(row)
        if not srcs:
            continue
        considered += 1
        q = extractor.from_datavorous_row(row, want_exam=args.exam)
        if not q or q.id not in banked or q.id in seen_qid:
            continue
        seen_qid.add(q.id)
        matched += 1
        if q.id in already_files:                    # idempotent: figure already on disk
            already += 1
            continue
        jobs.append((q.id, srcs))
        if args.limit and len(jobs) >= args.limit:
            break

    print(f"[{args.exam}] source img-rows considered: {considered} | matched to bank: {matched} "
          f"| already recovered: {already} | to fetch: {len(jobs)}")
    if not args.apply:
        print("DRY RUN — pass --apply to download + attach. Sample jobs:")
        for qid, srcs in jobs[:5]:
            print(f"  {qid}  <- {len(srcs)} img  {srcs[0][:90]}")
        return

    # download (parallel) + attach
    ok = dead = 0

    def work(job):
        qid, srcs = job
        refs = []
        for i, url in enumerate(srcs):
            base = qid if i == 0 else f"{qid}_{i}"
            name = _download(url, config.FIG_DIR, base)
            if name:
                refs.append(name)
        return qid, refs

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for n, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if n % 250 == 0:
                print(f"  fetched {n}/{len(jobs)}")

    pub = config.PUBLIC_BASE.rstrip("/")
    for qid, refs in results:
        if not refs:
            dead += 1
            continue
        ok += 1
        url = f"{pub}/figures/{refs[0]}"
        store.con.execute(
            "UPDATE questions SET figure_url=?, figure_refs=?, needs_figure=1 WHERE id=?",
            (url, __import__("json").dumps(refs), qid))
    store.con.commit()
    print(f"[{args.exam}] DONE — figures attached: {ok} | no live image: {dead}")


if __name__ == "__main__":
    main()
