"""SQLite store for local/demo. Production target is Postgres+pgvector
(same columns; see schema_postgres.sql). Interface is intentionally tiny so the
backend can be swapped without touching the agents."""
import json
import os
import sqlite3

from . import config
from .models import Question, unescape_newlines

_SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
  id TEXT PRIMARY KEY,
  exam TEXT, subject TEXT, stem TEXT, qtype TEXT,
  options TEXT, correct_answer TEXT, solution TEXT, figure_refs TEXT,
  needs_figure INTEGER DEFAULT 0, figure_url TEXT, figure_svg TEXT,
  chapter TEXT, concept TEXT, difficulty INTEGER, bloom_level TEXT,
  source TEXT, year INTEGER,
  verified INTEGER, generated INTEGER DEFAULT 0, validation_issues TEXT, duplicate_of TEXT, hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_hash ON questions(hash);
CREATE INDEX IF NOT EXISTS idx_subject ON questions(subject);
CREATE INDEX IF NOT EXISTS idx_verified ON questions(verified);
CREATE INDEX IF NOT EXISTS idx_topic ON questions(subject, chapter, difficulty);
"""

_COLS = ["id", "exam", "subject", "stem", "qtype", "options", "correct_answer",
         "solution", "figure_refs", "needs_figure", "figure_url", "figure_svg",
         "chapter", "concept", "difficulty", "bloom_level",
         "source", "year", "verified", "generated", "validation_issues", "duplicate_of", "hash"]


class Store:
    def __init__(self, path: str | None = None):
        self.path = path or config.DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # timeout + WAL so a long ingest/tag job and the live API can share the DB:
        # readers no longer block on the writer, and a writer waits instead of raising
        # "database is locked" the moment two jobs overlap.
        self.con = sqlite3.connect(self.path, timeout=30.0)
        try:
            self.con.execute("PRAGMA journal_mode=WAL")
            self.con.execute("PRAGMA busy_timeout=30000")
        except sqlite3.OperationalError:
            pass                      # read-only mount or locked mid-switch; keep going
        self.con.executescript(_SCHEMA)
        # migrate older DBs that predate later columns
        for ddl in ("ALTER TABLE questions ADD COLUMN bloom_level TEXT",
                    "ALTER TABLE questions ADD COLUMN generated INTEGER DEFAULT 0",
                    "ALTER TABLE questions ADD COLUMN needs_figure INTEGER DEFAULT 0",
                    "ALTER TABLE questions ADD COLUMN figure_url TEXT",
                    "ALTER TABLE questions ADD COLUMN figure_svg TEXT"):
            try:
                self.con.execute(ddl)
                self.con.commit()
            except sqlite3.OperationalError:
                pass  # column already exists

    def upsert(self, q: Question):
        row = (q.id, q.exam, q.subject, q.stem, q.qtype,
               json.dumps(q.options, ensure_ascii=False), q.correct_answer, q.solution,
               json.dumps(q.figure_refs), int(q.needs_figure), q.figure_url, q.figure_svg,
               q.chapter, q.concept, q.difficulty, q.bloom_level,
               q.source, q.year, int(q.verified), int(q.generated),
               json.dumps(q.validation_issues, ensure_ascii=False), q.duplicate_of, q.hash)
        self.con.execute(
            f"INSERT OR REPLACE INTO questions ({','.join(_COLS)}) "
            f"VALUES ({','.join('?' * len(_COLS))})", row)
        self.con.commit()

    def existing_hashes(self) -> dict:
        """hash -> id, for cross-batch dedup against what's already banked."""
        return {h: i for h, i in self.con.execute(
            "SELECT hash, id FROM questions WHERE duplicate_of IS NULL")}

    def stats(self) -> dict:
        c = self.con
        total = c.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        verified = c.execute("SELECT COUNT(*) FROM questions WHERE verified=1 AND duplicate_of IS NULL").fetchone()[0]
        dupes = c.execute("SELECT COUNT(*) FROM questions WHERE duplicate_of IS NOT NULL").fetchone()[0]
        by_type = dict(c.execute(
            "SELECT qtype, COUNT(*) FROM questions WHERE duplicate_of IS NULL GROUP BY qtype").fetchall())
        by_year = dict(c.execute(
            "SELECT year, COUNT(*) FROM questions WHERE duplicate_of IS NULL GROUP BY year").fetchall())
        return {"total": total, "verified_unique": verified, "duplicates": dupes,
                "by_type": by_type, "by_year": by_year}

    # --- tagging (Phase 2) ---

    def _row_to_q(self, cur, row) -> Question:
        d = dict(zip([c[0] for c in cur.description], row))
        d["options"] = json.loads(d.get("options") or "[]")
        d["figure_refs"] = json.loads(d.get("figure_refs") or "[]")
        d["validation_issues"] = json.loads(d.get("validation_issues") or "[]")
        d["verified"] = bool(d.get("verified"))
        d["generated"] = bool(d.get("generated"))
        d["needs_figure"] = bool(d.get("needs_figure"))
        return Question(**{k: d[k] for k in d if k in Question.__dataclass_fields__})

    def rows_id_stem(self):
        return self.con.execute("SELECT id, stem, figure_url FROM questions").fetchall()

    def iter_real(self, chapter=None, missing_solution=False, exclude_needs_figure=False,
                  limit=None, exam=None, subject=None) -> list[Question]:
        sql = "SELECT * FROM questions WHERE generated=0 AND verified=1 AND duplicate_of IS NULL"
        args = []
        if chapter:
            sql += " AND chapter=?"
            args.append(chapter)
        # exam/subject scoping matters once the bank holds several exams: an unscoped
        # retag/enrich would sweep all ~12k banked questions instead of the new subject.
        if exam:
            sql += " AND exam=?"
            args.append(exam)
        if subject:
            sql += " AND subject=?"
            args.append(subject)
        if missing_solution:
            sql += " AND (solution IS NULL OR solution='')"
        if exclude_needs_figure:
            sql += " AND COALESCE(needs_figure,0)=0"
        if limit:
            sql += f" LIMIT {int(limit)}"
        cur = self.con.execute(sql, args)
        return [self._row_to_q(cur, r) for r in cur.fetchall()]

    def set_solution(self, qid, solution, extra_issue=None):
        # central choke point for LLM-authored solutions -> normalise escaped newlines
        # here rather than in each caller (see models.unescape_newlines)
        solution = unescape_newlines(solution)
        row = self.con.execute("SELECT validation_issues FROM questions WHERE id=?", (qid,)).fetchone()
        issues = json.loads(row[0] or "[]") if row and row[0] else []
        if extra_issue and extra_issue not in issues:
            issues.append(extra_issue)
        self.con.execute("UPDATE questions SET solution=?, validation_issues=? WHERE id=?",
                         (solution, json.dumps(issues, ensure_ascii=False), qid))
        self.con.commit()

    def set_needs_figure(self, qid, val):
        self.con.execute("UPDATE questions SET needs_figure=? WHERE id=?", (int(val), qid))
        self.con.commit()

    def update_figure(self, qid, figure_url, needs_figure):
        self.con.execute("UPDATE questions SET figure_url=?, needs_figure=? WHERE id=?",
                         (figure_url, int(needs_figure), qid))
        self.con.commit()

    def iter_untagged(self, limit: int | None = None) -> list[Question]:
        q = ("SELECT * FROM questions WHERE verified=1 AND duplicate_of IS NULL "
             "AND (chapter IS NULL OR chapter='')")
        if limit:
            q += f" LIMIT {int(limit)}"
        cur = self.con.execute(q)
        rows = cur.fetchall()
        return [self._row_to_q(cur, r) for r in rows]

    def update_tags(self, qid, chapter, concept, difficulty, bloom_level):
        self.con.execute(
            "UPDATE questions SET chapter=?, concept=?, difficulty=?, bloom_level=? WHERE id=?",
            (chapter, concept, difficulty, bloom_level, qid))
        self.con.commit()

    def tag_distribution(self) -> dict:
        c = self.con
        by_chapter = dict(c.execute(
            "SELECT chapter, COUNT(*) FROM questions WHERE duplicate_of IS NULL AND chapter IS NOT NULL "
            "GROUP BY chapter ORDER BY COUNT(*) DESC").fetchall())
        by_difficulty = dict(c.execute(
            "SELECT difficulty, COUNT(*) FROM questions WHERE duplicate_of IS NULL AND difficulty IS NOT NULL "
            "GROUP BY difficulty ORDER BY difficulty").fetchall())
        return {"by_chapter": by_chapter, "by_difficulty": by_difficulty}

    def chapter_counts(self, exam=None, subject=None) -> dict:
        """Verified-exemplar count per chapter, scoped to exam+subject so the topic
        picker doesn't merge same-named chapters across exams (JEE Main vs Advanced
        share chapter names). Powers /chapters `exemplars_banked`."""
        where = ["verified=1", "duplicate_of IS NULL", "chapter IS NOT NULL"]
        args = []
        for col, val in (("exam", exam), ("subject", subject)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        sql = ("SELECT chapter, COUNT(*) FROM questions WHERE " + " AND ".join(where) +
               " GROUP BY chapter")
        return dict(self.con.execute(sql, args).fetchall())

    def retrieve(self, chapter=None, subject=None, qtype=None, exam=None,
                 dmin=None, dmax=None, limit=10, include_generated=True) -> list[dict]:
        """The payoff: pull questions by tag — the exam-generator's read path."""
        where = ["verified=1", "duplicate_of IS NULL"]
        args = []
        if not include_generated:
            where.append("COALESCE(generated,0)=0")
        for col, val in (("subject", subject), ("chapter", chapter), ("qtype", qtype), ("exam", exam)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        if dmin is not None:
            where.append("difficulty>=?")
            args.append(dmin)
        if dmax is not None:
            where.append("difficulty<=?")
            args.append(dmax)
        sql = f"SELECT * FROM questions WHERE {' AND '.join(where)} LIMIT {int(limit)}"
        cur = self.con.execute(sql, args)
        cols = [d[0] for d in cur.description]
        out = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["options"] = json.loads(d["options"] or "[]")
            out.append(d)
        return out

    def pool_questions(self, exam=None, subject=None, chapter=None, qtype=None,
                       dmin=None, dmax=None, exclude_ids=None, limit=10) -> list[dict]:
        """Serve PRE-GENERATED pool questions (generated=1, verified=1) INSTANTLY — no LLM.
        This is the frontend's hot path: draw from the shared pool, passing exclude_ids
        (already-seen) so a student never repeats. Randomised so the shared pool spreads
        evenly across students. Live /generate is only for power users who drain a cell."""
        where = ["verified=1", "COALESCE(generated,0)=1", "duplicate_of IS NULL"]
        args = []
        for col, val in (("exam", exam), ("subject", subject), ("chapter", chapter), ("qtype", qtype)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        if dmin is not None:
            where.append("difficulty>=?")
            args.append(dmin)
        if dmax is not None:
            where.append("difficulty<=?")
            args.append(dmax)
        if exclude_ids:
            where.append("id NOT IN (%s)" % ",".join("?" * len(exclude_ids)))
            args.extend(exclude_ids)
        sql = ("SELECT * FROM questions WHERE " + " AND ".join(where) +
               " ORDER BY RANDOM() LIMIT %d" % int(limit))
        cur = self.con.execute(sql, args)
        cols = [d[0] for d in cur.description]
        out = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["options"] = json.loads(d["options"] or "[]")
            out.append(d)
        return out

    def pool_stats(self, exam=None, subject=None) -> dict:
        """Coverage of the pre-generated pool keyed by (chapter, difficulty, qtype).
        Powers batch-fill (skip cells already at target — makes the fill RESUMABLE) and
        an ops view of pool depth per topic."""
        where = ["verified=1", "COALESCE(generated,0)=1", "duplicate_of IS NULL", "chapter IS NOT NULL"]
        args = []
        for col, val in (("exam", exam), ("subject", subject)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        sql = ("SELECT chapter, difficulty, qtype, COUNT(*) FROM questions WHERE " +
               " AND ".join(where) + " GROUP BY chapter, difficulty, qtype")
        return {(ch, d, qt): n for ch, d, qt, n in self.con.execute(sql, args).fetchall()}

    def sample(self, n: int = 3, verified_only: bool = True) -> list[dict]:
        q = "SELECT * FROM questions WHERE duplicate_of IS NULL"
        if verified_only:
            q += " AND verified=1"
        q += f" LIMIT {int(n)}"
        cur = self.con.execute(q)
        cols = [d[0] for d in cur.description]
        out = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["options"] = json.loads(d["options"] or "[]")
            d["validation_issues"] = json.loads(d["validation_issues"] or "[]")
            out.append(d)
        return out
