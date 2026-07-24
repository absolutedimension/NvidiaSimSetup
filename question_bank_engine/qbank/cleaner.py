"""Cleaner agent — normalize text + flag duplicates.

Dedup is two-stage:
  1. exact  : content hash (aggressively normalized) — catches copies across years/sources.
  2. near   : TF-IDF cosine within the fresh batch — catches reworded repeats.
Duplicates are FLAGGED (duplicate_of set), never deleted — repeat frequency is
useful signal ('this concept is asked every year')."""
import re

from . import config
from .models import normalize_for_hash


def normalize(text: str) -> str:
    text = (text or "").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean(questions):
    for q in questions:
        q.stem = normalize(q.stem)
        for o in q.options:
            o["text"] = normalize(o.get("text", ""))
    return questions


def flag_duplicates(questions, existing_hashes: dict | None = None,
                    threshold: float | None = None):
    existing_hashes = existing_hashes or {}
    threshold = threshold if threshold is not None else config.NEAR_DUP_THRESHOLD

    # stage 1: exact hash (against bank + within batch)
    seen = {}
    for q in questions:
        if q.hash in existing_hashes and existing_hashes[q.hash] != q.id:
            q.duplicate_of = existing_hashes[q.hash]
        elif q.hash in seen:
            q.duplicate_of = seen[q.hash]
        else:
            seen[q.hash] = q.id

    # stage 2: near-dup within the still-fresh batch
    fresh = [q for q in questions if not q.duplicate_of]
    if len(fresh) > 2:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            texts = [normalize_for_hash(q.stem) for q in fresh]
            X = TfidfVectorizer(min_df=1).fit_transform(texts)
            S = cosine_similarity(X)
            for i in range(len(fresh)):
                if fresh[i].duplicate_of:
                    continue
                for j in range(i + 1, len(fresh)):
                    if not fresh[j].duplicate_of and S[i, j] >= threshold:
                        fresh[j].duplicate_of = fresh[i].id
        except Exception:
            pass  # sklearn missing -> exact dedup only
    return questions
