"""Learner-model store for Acharya University (Phase 1: JSON on disk).

Isolated from the live Acharya data — everything lives under ./data/.
Postgres swap comes in Phase 5; keep these functions as the only data access point.
"""
import json
import os
import time
import uuid

DATA_DIR = os.getenv("ACHARYA_UNI_DATA", os.path.join(os.path.dirname(__file__), "data"))
LEARNERS = os.path.join(DATA_DIR, "learners")
CURRICULA = os.path.join(DATA_DIR, "curricula")
SESSIONS = os.path.join(DATA_DIR, "sessions")

for _d in (LEARNERS, CURRICULA, SESSIONS):
    os.makedirs(_d, exist_ok=True)


def _now() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _read(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None


def _write(path: str, obj: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic


# ---- Learner --------------------------------------------------------------
def get_learner(user_id: str) -> dict:
    learner = _read(os.path.join(LEARNERS, f"{user_id}.json"))
    if not learner:
        learner = {"user_id": user_id, "name": "", "created_at": _now(), "goals": []}
        _write(os.path.join(LEARNERS, f"{user_id}.json"), learner)
    return learner


def save_learner(learner: dict) -> None:
    _write(os.path.join(LEARNERS, f"{learner['user_id']}.json"), learner)


# ---- Curriculum -----------------------------------------------------------
def get_curriculum(curriculum_id: str) -> dict | None:
    return _read(os.path.join(CURRICULA, f"{curriculum_id}.json"))


def save_curriculum(curr: dict) -> None:
    _write(os.path.join(CURRICULA, f"{curr['curriculum_id']}.json"), curr)


def list_curricula(user_id: str) -> list:
    learner = get_learner(user_id)
    out = []
    for cid in learner.get("goals", []):
        c = get_curriculum(cid)
        if c:
            out.append({"curriculum_id": cid, "title": c.get("title", ""),
                        "goal": c.get("goal", ""), "status": c.get("status", "active"),
                        "units": len(c.get("units", [])),
                        "progress": _progress(c)})
    return out


def _progress(curr: dict) -> int:
    units = curr.get("units", [])
    if not units:
        return 0
    done = sum(1 for u in units if u.get("status") == "done")
    return round(100 * done / len(units))


# ---- Tutor session --------------------------------------------------------
def _sess_path(curriculum_id: str, unit_id: str) -> str:
    return os.path.join(SESSIONS, f"{curriculum_id}__{unit_id}.json")


def get_session(curriculum_id: str, unit_id: str) -> dict:
    s = _read(_sess_path(curriculum_id, unit_id))
    if not s:
        s = {"history": [], "updated_at": _now()}
    return s


def save_session(curriculum_id: str, unit_id: str, session: dict) -> None:
    session["updated_at"] = _now()
    _write(_sess_path(curriculum_id, unit_id), session)
