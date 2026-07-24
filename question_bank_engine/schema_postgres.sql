-- Production schema for the Question Bank (Postgres + pgvector).
-- SQLite (data/qbank.sqlite) mirrors these columns for local/demo; swap Store's
-- backend to this for production + retrieval (RAG generation reads from here).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS questions (
    id                TEXT PRIMARY KEY,
    exam              TEXT NOT NULL,
    subject           TEXT NOT NULL,
    stem              TEXT NOT NULL,
    qtype             TEXT NOT NULL,           -- MCQ_single | MCQ_multi | integer | numeric
    options           JSONB NOT NULL DEFAULT '[]',
    correct_answer    TEXT NOT NULL DEFAULT '',
    solution          TEXT NOT NULL DEFAULT '',
    figure_refs       JSONB NOT NULL DEFAULT '[]',

    -- tagging (Phase 2 — the tagging agent fills these)
    chapter           TEXT,
    concept           TEXT,
    difficulty        SMALLINT,                -- 1..5
    bloom_level       TEXT,

    -- provenance
    source            TEXT,
    year              SMALLINT,

    -- pipeline state
    verified          BOOLEAN NOT NULL DEFAULT FALSE,
    validation_issues JSONB NOT NULL DEFAULT '[]',
    duplicate_of      TEXT REFERENCES questions(id),
    hash              TEXT NOT NULL,

    -- retrieval (Phase 2+: generation retrieves exemplars by similarity)
    embedding         vector(1536),

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_q_subject     ON questions (exam, subject);
CREATE INDEX IF NOT EXISTS idx_q_topic       ON questions (subject, chapter, concept);
CREATE INDEX IF NOT EXISTS idx_q_verified    ON questions (verified) WHERE duplicate_of IS NULL;
CREATE INDEX IF NOT EXISTS idx_q_hash        ON questions (hash);
-- vector index for retrieval (build after embeddings are populated):
-- CREATE INDEX ON questions USING hnsw (embedding vector_cosine_ops);
