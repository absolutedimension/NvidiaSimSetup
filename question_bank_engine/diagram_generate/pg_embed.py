#!/usr/bin/env python3
"""Embed verified question stems into the pgvector column (local ONNX model, CPU, no torch).
Resumable: only fills rows where embedding IS NULL. Builds an HNSW cosine index at the end.

    python3 pg_embed.py
"""
import os, sys
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from pgvector.psycopg2 import register_vector
from fastembed import TextEmbedding

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL = "BAAI/bge-small-en-v1.5"   # 384-dim, strong retrieval model, ONNX
BATCH = int(os.environ.get("EMBED_BATCH", "64"))      # small batch = low memory on the 3.8G box
THREADS = int(os.environ.get("EMBED_THREADS", "2"))   # cap onnxruntime threads to bound memory


def load_env(path):
    env = {}
    for line in open(os.path.expanduser(path)):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); env[k] = v
    return env


def main():
    env = load_env("~/question_bank_engine/pg.env")
    pg = psycopg2.connect(host=env["PGHOST"], port=env["PGPORT"], dbname=env["PGDATABASE"],
                          user=env["PGUSER"], password=env["PGPASSWORD"])
    register_vector(pg)
    cur = pg.cursor()
    cur.execute("SELECT id, stem FROM questions WHERE verified=1 AND embedding IS NULL")
    rows = cur.fetchall()
    print(f"[embed] rows to embed: {len(rows)}", flush=True)
    if not rows:
        print("[embed] nothing to do"); return

    print(f"[embed] loading model {MODEL} (threads={THREADS}, batch={BATCH}) ...", flush=True)
    model = TextEmbedding(MODEL, threads=THREADS)

    done = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        texts = [(s or "")[:2000] for _, s in batch]
        embs = list(model.embed(texts))                       # list of np.float32 arrays (384,)
        args = [(np.asarray(e, dtype=np.float32), qid) for (qid, _), e in zip(batch, embs)]
        execute_batch(cur, "UPDATE questions SET embedding=%s WHERE id=%s", args, page_size=BATCH)
        pg.commit()
        done += len(batch)
        if done % (BATCH * 4) == 0 or done == len(rows):
            print(f"  embedded {done}/{len(rows)}", flush=True)

    print("[embed] building HNSW cosine index (fast at this size) ...", flush=True)
    cur.execute("CREATE INDEX IF NOT EXISTS q_emb_hnsw ON questions "
                "USING hnsw (embedding vector_cosine_ops)")
    pg.commit()
    cur.execute("SELECT COUNT(*) FROM questions WHERE embedding IS NOT NULL")
    print(f"[embed] DONE. rows with embedding: {cur.fetchone()[0]}", flush=True)
    pg.close()


if __name__ == "__main__":
    main()
