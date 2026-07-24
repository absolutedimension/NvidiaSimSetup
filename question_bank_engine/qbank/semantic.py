"""Semantic layer over pgvector — the RAG upgrade.

Replaces lexical TF-IDF novelty with EMBEDDING novelty (catches reworded near-duplicates
TF-IDF misses) and adds embedding-based exemplar diversification. Everything degrades
gracefully: if Postgres/pgvector or the embed model is unavailable, callers fall back to
the SQLite + TF-IDF path.

Store of record stays SQLite. This module only reaches into the pgvector copy for
similarity queries, and keeps that copy in sync by embedding each newly-accepted
generated question (upsert_embedding).

Model: BAAI/bge-small-en-v1.5 (384-dim, local ONNX via fastembed) — same one used to
backfill the bank, so query and index vectors are comparable.
"""
import os
import threading

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_emb = None
_lock = threading.Lock()


def enabled() -> bool:
    return os.environ.get("QBANK_SEMANTIC", "on").lower() not in ("off", "0", "false", "no")


def _env() -> dict:
    """Read PG connection settings from pg.env (next to the package or in the home dir)."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in (os.path.join(here, "pg.env"), os.path.expanduser("~/question_bank_engine/pg.env")):
        if os.path.exists(path):
            env = {}
            for line in open(path):
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k] = v
            return env
    return {}


def _model():
    global _emb
    if _emb is None:
        with _lock:
            if _emb is None:
                from fastembed import TextEmbedding
                _emb = TextEmbedding(MODEL_NAME, threads=int(os.environ.get("EMBED_THREADS", "2")))
    return _emb


def embed(texts):
    """Return a list of float32 numpy arrays (384-dim). Serialized for thread-safety."""
    import numpy as np
    if isinstance(texts, str):
        texts = [texts]
    texts = [(t or "")[:2000] for t in texts]
    with _lock:
        return [np.asarray(e, dtype=np.float32) for e in _model().embed(texts)]


def _connect():
    """Fresh PG connection per call (thread-safe under concurrent generation). None on failure."""
    try:
        import psycopg2
        from pgvector.psycopg2 import register_vector
        env = _env()
        if not env:
            return None
        con = psycopg2.connect(host=env["PGHOST"], port=env["PGPORT"], dbname=env["PGDATABASE"],
                               user=env["PGUSER"], password=env["PGPASSWORD"], connect_timeout=5)
        register_vector(con)
        return con
    except Exception:
        return None


def max_similarity(stem: str, exam=None, subject=None, chapter=None) -> float:
    """Max cosine similarity of `stem` vs verified banked questions in scope (HNSW-indexed).
    Returns 0.0 when semantic is off/unavailable (so the caller's TF-IDF gate still runs)."""
    if not enabled() or not (stem or "").strip():
        return 0.0
    con = _connect()
    if con is None:
        return 0.0
    try:
        v = embed(stem)[0]
        where = ["verified=1", "embedding IS NOT NULL"]
        args = []
        for col, val in (("exam", exam), ("subject", subject), ("chapter", chapter)):
            if val:
                where.append(f"{col}=%s")
                args.append(val)
        cur = con.cursor()
        cur.execute(
            f"SELECT 1 - (embedding <=> %s) FROM questions WHERE {' AND '.join(where)} "
            f"ORDER BY embedding <=> %s LIMIT 1", [v] + args + [v])
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
    except Exception:
        return 0.0
    finally:
        try:
            con.close()
        except Exception:
            pass


def upsert_embedding(q) -> None:
    """Embed a newly-accepted generated question into pgvector so it joins the novelty pool.
    Best-effort — a failure never blocks generation."""
    if not enabled():
        return
    con = _connect()
    if con is None:
        return
    try:
        v = embed(q.stem)[0]
        cur = con.cursor()
        cur.execute(
            "INSERT INTO questions (id, exam, subject, stem, qtype, chapter, concept, "
            "difficulty, verified, generated, embedding) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,1,%s) "
            "ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding",
            (q.id, q.exam, q.subject, q.stem, q.qtype, getattr(q, "chapter", None),
             getattr(q, "concept", None), getattr(q, "difficulty", None), v))
        con.commit()
    except Exception:
        try:
            con.rollback()
        except Exception:
            pass
    finally:
        try:
            con.close()
        except Exception:
            pass


def diversify_indices(stems, k: int):
    """Pick k indices whose embeddings are maximally spread (farthest-point sampling), so the
    exemplars shown to the generator are varied rather than near-duplicates of each other.
    Falls back to the first k when semantic is off/unavailable or there's nothing to diversify."""
    n = len(stems)
    if not enabled() or n <= k:
        return list(range(min(k, n)))
    try:
        import numpy as np
        E = np.vstack(embed(list(stems)))
        E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
        chosen = [0]
        while len(chosen) < k:
            sims = E @ E[chosen].T            # (n, |chosen|) cosine sims
            maxsim = sims.max(axis=1)         # each candidate's closest match among chosen
            maxsim[chosen] = 2.0              # exclude already-chosen
            chosen.append(int(np.argmin(maxsim)))   # most-dissimilar-to-all-chosen
        return chosen
    except Exception:
        return list(range(min(k, n)))
