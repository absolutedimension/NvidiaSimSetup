"""Collector agent — the HYBRID sourcing layer.

  fetch_open_dataset()  -> auto-collect from open datasets (HuggingFace datasets API).
  scan_drop_folder()    -> manual drop: any PDFs you place in drop/.

Official-exam auto-download (NTA/CBSE) plugs in here as another fetch_* function
using the same output contract (list of raw dict rows). We deliberately do NOT
scrape copyrighted coaching/aggregator platforms."""
import glob
import json
import os
import urllib.parse
import urllib.request

from . import config

_HF_API = "https://datasets-server.huggingface.co/rows"


def fetch_open_dataset(dataset: str = "daman1209arora/jeebench",
                       subject: str = "phy", limit: int = 40,
                       split: str = "test") -> list[dict]:
    """Pull real rows from an open HuggingFace dataset (public JSON API)."""
    rows: list[dict] = []
    offset = 0
    total = 10 ** 9
    while len(rows) < limit and offset < total:
        url = (f"{_HF_API}?dataset={urllib.parse.quote(dataset)}"
               f"&config=default&split={split}&offset={offset}&length=100")
        with urllib.request.urlopen(url, timeout=45) as r:
            d = json.loads(r.read())
        total = d.get("num_rows_total", 0)
        batch = [x["row"] for x in d.get("rows", [])]
        if not batch:
            break
        rows += [b for b in batch if subject is None or b.get("subject") == subject]
        offset += 100
    return rows[:limit]


# Some papers split a bank subject across several dataset labels — NEET 2024 files
# Biology as "Botany" + "Zoology" (2025/26 use "Biology"). Retrieval is by bank
# subject, so they all land in one place.
SUBJECT_ALIASES = {
    "Biology": ("Biology", "Botany", "Zoology"),
    "Mathematics": ("Mathematics", "Maths", "Math"),
}


def fetch_image_dataset(dataset: str = "Reja1/jee-neet-benchmark",
                        exam_prefix: str | None = "JEE", subject: str = "Physics",
                        limit: int | None = None, split: str = "test") -> list[dict]:
    """Image-based dataset (questions as PNGs + answers in metadata). Returns rows with
    the image URL + metadata; the vision extractor turns each image into a Question."""
    import time
    wanted = {s.lower() for s in SUBJECT_ALIASES.get(subject, (subject,))}
    rows: list[dict] = []
    offset = 0
    total = 10 ** 9
    while offset < total:
        if limit and len(rows) >= limit:
            break
        url = (f"{_HF_API}?dataset={urllib.parse.quote(dataset)}"
               f"&config=default&split={split}&offset={offset}&length=100")
        d = None
        for attempt in range(4):                 # datasets-server 500s transiently
            try:
                with urllib.request.urlopen(url, timeout=45) as r:
                    d = json.loads(r.read())
                break
            except Exception:
                time.sleep(2 * (attempt + 1))
        if d is None:                            # give up on this page, keep going
            offset += 100
            continue
        total = d.get("num_rows_total", 0)
        batch = [x["row"] for x in d.get("rows", [])]
        if not batch:
            break
        for b in batch:
            if str(b.get("subject", "")).lower() not in wanted:
                continue
            if exam_prefix and not str(b.get("exam_name", "")).startswith(exam_prefix):
                continue
            rows.append({"image_url": b["image"]["src"], "question_type": b["question_type"],
                         "correct_answer": b["correct_answer"], "exam_name": b["exam_name"],
                         "exam_year": b["exam_year"], "question_id": b["question_id"],
                         "dataset_subject": b.get("subject")})
        offset += 100
    return rows[:limit] if limit else rows


def scan_drop_folder(path: str | None = None) -> list[str]:
    """Manual-drop source: PDFs the user placed for ingestion."""
    path = path or config.DROP_DIR
    os.makedirs(path, exist_ok=True)
    return sorted(glob.glob(os.path.join(path, "*.pdf")))
