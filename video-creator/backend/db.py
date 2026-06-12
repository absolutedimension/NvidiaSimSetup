"""
Job Queue Database — SQLite backed.
Zero infrastructure. Swap to Redis/Azure Queue for scale.
"""

import sqlite3
import json
import os
import time
import uuid
from contextlib import contextmanager
from typing import Optional

DB_PATH = os.environ.get("VIDEO_CREATOR_DB", "/home/ubuntu/video-creator-data/jobs.db")


def _ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            config TEXT,
            status TEXT DEFAULT 'created',
            created_at REAL,
            updated_at REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            type TEXT,
            status TEXT DEFAULT 'queued',
            priority INTEGER DEFAULT 5,
            depends_on TEXT DEFAULT '[]',
            config TEXT,
            result TEXT,
            progress INTEGER DEFAULT 0,
            step TEXT DEFAULT '',
            error TEXT,
            worker_id TEXT,
            created_at REAL,
            started_at REAL,
            completed_at REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id)")
    conn.commit()
    conn.close()


_ensure_db()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ============================================================
# Project CRUD
# ============================================================

def create_project(name: str, config: dict) -> str:
    pid = f"proj_{uuid.uuid4().hex[:8]}"
    now = time.time()
    with get_db() as db:
        db.execute(
            "INSERT INTO projects (id, name, config, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (pid, name, json.dumps(config), "created", now, now)
        )
    return pid


def get_project(pid: str) -> Optional[dict]:
    with get_db() as db:
        row = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        if row:
            d = dict(row)
            d["config"] = json.loads(d["config"])
            return d
    return None


def update_project_status(pid: str, status: str):
    with get_db() as db:
        db.execute("UPDATE projects SET status=?, updated_at=? WHERE id=?", (status, time.time(), pid))


def list_projects(limit=20) -> list:
    with get_db() as db:
        rows = db.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


# ============================================================
# Job CRUD
# ============================================================

def create_job(project_id: str, job_type: str, config: dict, priority: int = 5, depends_on: list = None) -> str:
    jid = f"job_{uuid.uuid4().hex[:8]}"
    now = time.time()
    with get_db() as db:
        db.execute(
            "INSERT INTO jobs (id, project_id, type, config, priority, depends_on, created_at) VALUES (?,?,?,?,?,?,?)",
            (jid, project_id, job_type, json.dumps(config), priority, json.dumps(depends_on or []), now)
        )
    return jid


def get_job(jid: str) -> Optional[dict]:
    with get_db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if row:
            d = dict(row)
            d["config"] = json.loads(d["config"])
            d["depends_on"] = json.loads(d["depends_on"])
            d["result"] = json.loads(d["result"]) if d["result"] else None
            return d
    return None


def get_project_jobs(pid: str) -> list:
    with get_db() as db:
        rows = db.execute("SELECT * FROM jobs WHERE project_id=? ORDER BY priority, created_at", (pid,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["config"] = json.loads(d["config"])
            d["depends_on"] = json.loads(d["depends_on"])
            d["result"] = json.loads(d["result"]) if d["result"] else None
            result.append(d)
        return result


def claim_next_job(worker_id: str, job_types: list) -> Optional[dict]:
    """
    Atomically claim the next available job for this worker.
    Only returns jobs whose dependencies are all completed.
    """
    with get_db() as db:
        placeholders = ",".join("?" * len(job_types))
        rows = db.execute(
            f"SELECT * FROM jobs WHERE status='queued' AND type IN ({placeholders}) ORDER BY priority, created_at",
            job_types
        ).fetchall()

        for row in rows:
            job = dict(row)
            job["depends_on"] = json.loads(job["depends_on"])

            # Check dependencies
            deps_met = True
            for dep_id in job["depends_on"]:
                dep = db.execute("SELECT status FROM jobs WHERE id=?", (dep_id,)).fetchone()
                if not dep or dep["status"] != "completed":
                    deps_met = False
                    break

            if deps_met:
                # Claim it
                db.execute(
                    "UPDATE jobs SET status='processing', worker_id=?, started_at=? WHERE id=? AND status='queued'",
                    (worker_id, time.time(), job["id"])
                )
                job["config"] = json.loads(job["config"])
                job["result"] = json.loads(job["result"]) if job["result"] else None
                job["status"] = "processing"
                return job

    return None


def update_job_progress(jid: str, progress: int, step: str = ""):
    with get_db() as db:
        db.execute("UPDATE jobs SET progress=?, step=? WHERE id=?", (progress, step, jid))


def complete_job(jid: str, result: dict):
    with get_db() as db:
        db.execute(
            "UPDATE jobs SET status='completed', result=?, progress=100, completed_at=? WHERE id=?",
            (json.dumps(result), time.time(), jid)
        )


def fail_job(jid: str, error: str):
    with get_db() as db:
        db.execute(
            "UPDATE jobs SET status='failed', error=?, completed_at=? WHERE id=?",
            (error, time.time(), jid)
        )


def get_queue_stats() -> dict:
    with get_db() as db:
        stats = {}
        for status in ["queued", "processing", "completed", "failed"]:
            count = db.execute("SELECT COUNT(*) FROM jobs WHERE status=?", (status,)).fetchone()[0]
            stats[status] = count
        return stats
