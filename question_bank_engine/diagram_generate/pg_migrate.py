#!/usr/bin/env python3
"""Migrate the SQLite question bank -> Postgres (+ pgvector embedding column). Additive & idempotent.
SQLite stays the source of truth; this copies rows into Postgres so we can move retrieval/novelty
onto pgvector. Re-runnable (ON CONFLICT DO NOTHING).

    python3 pg_migrate.py
"""
import os, sqlite3, sys
import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qbank import config

COLS = ["id", "exam", "subject", "stem", "qtype", "options", "correct_answer", "solution",
        "figure_refs", "chapter", "concept", "difficulty", "source", "year", "verified",
        "validation_issues", "duplicate_of", "hash", "bloom_level", "generated", "needs_figure",
        "figure_url", "figure_svg"]

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS questions (
  id TEXT PRIMARY KEY, exam TEXT, subject TEXT, stem TEXT, qtype TEXT, options TEXT,
  correct_answer TEXT, solution TEXT, figure_refs TEXT, chapter TEXT, concept TEXT,
  difficulty INTEGER, source TEXT, year INTEGER, verified INTEGER, validation_issues TEXT,
  duplicate_of TEXT, hash TEXT, bloom_level TEXT, generated INTEGER, needs_figure INTEGER,
  figure_url TEXT, figure_svg TEXT, embedding vector(384)
);
-- indexes that mirror the SQL filters the app uses (exam/subject/chapter/difficulty/flags)
CREATE INDEX IF NOT EXISTS q_filter_idx ON questions (exam, subject, chapter, qtype, difficulty);
CREATE INDEX IF NOT EXISTS q_gen_idx ON questions (generated, verified);
"""


def load_env(path):
    env = {}
    for line in open(os.path.expanduser(path)):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v
    return env


def main():
    env = load_env("~/question_bank_engine/pg.env")
    sq = sqlite3.connect(config.DB_PATH)
    raw = sq.execute(f"SELECT {','.join(COLS)} FROM questions").fetchall()
    # Postgres TEXT rejects NUL (0x00) bytes that some OCR/ingest artifacts left behind — strip them.
    def clean(v):
        return v.replace("\x00", "") if isinstance(v, str) else v
    rows = [tuple(clean(v) for v in r) for r in raw]
    print(f"sqlite rows: {len(rows)}")

    pg = psycopg2.connect(host=env["PGHOST"], port=env["PGPORT"], dbname=env["PGDATABASE"],
                          user=env["PGUSER"], password=env["PGPASSWORD"])
    cur = pg.cursor()
    cur.execute(DDL)
    pg.commit()
    sql = f"INSERT INTO questions ({','.join(COLS)}) VALUES %s ON CONFLICT (id) DO NOTHING"
    execute_values(cur, sql, rows, page_size=1000)
    pg.commit()
    cur.execute("SELECT COUNT(*) FROM questions")
    print(f"postgres rows: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM questions WHERE verified=1")
    print(f"postgres verified: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM questions WHERE embedding IS NULL")
    print(f"rows needing embedding: {cur.fetchone()[0]}")
    pg.close()


if __name__ == "__main__":
    main()
