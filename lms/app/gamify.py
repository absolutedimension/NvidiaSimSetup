"""Points ledger, levels, streaks, and badges. The ledger is the source of truth;
totals and levels are computed on read."""
import math
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Achievement, Event, PointsLedger, Streak, Student

# canonical reward map (mirrors LEARNING_DESIGN.md)
POINTS = {
    "step_correct": 10,
    "lesson_complete": 25,
    "lesson_perfect": 15,
    "workbook_task": 10,
    "bring_item": 30,
    "module_watched": 15,
    "week_complete": 100,
    "capstone": 500,
}
STREAK_MILESTONES = {3: 20, 7: 50, 14: 120, 30: 300}
BADGES = {
    "first_steps": "First steps",
    "loop_master": "Loop master",
    "streak_3": "3-day streak",
    "streak_7": "7-day streak",
    "streak_14": "14-day streak",
    "streak_30": "30-day streak",
    "week_done": "Week complete",
    "shipped_it": "Shipped it",
    "demo_day": "Demo Day",
}


def total_points(db: Session, student_id: int) -> int:
    return db.query(func.coalesce(func.sum(PointsLedger.points), 0)).filter_by(
        student_id=student_id
    ).scalar() or 0


def level_for(total: int) -> int:
    return int(math.floor(math.sqrt(max(total, 0) / 50)))


def level_progress(total: int) -> dict:
    lvl = level_for(total)
    floor_pts = 50 * (lvl ** 2)
    next_pts = 50 * ((lvl + 1) ** 2)
    span = next_pts - floor_pts
    pct = int(round(100 * (total - floor_pts) / span)) if span else 100
    return {"level": lvl, "total": total, "to_next": next_pts - total, "pct": min(max(pct, 0), 100)}


def award(db: Session, student_id: int, reason: str, ref: str = "", points: int | None = None) -> int:
    pts = POINTS.get(reason, 0) if points is None else points
    if pts:
        db.add(PointsLedger(student_id=student_id, points=pts, reason=reason, ref=ref))
    db.add(Event(student_id=student_id, type=reason, payload={"ref": ref, "points": pts}))
    db.commit()
    return pts


def grant_badge(db: Session, student_id: int, code: str) -> bool:
    if db.query(Achievement).filter_by(student_id=student_id, badge_code=code).first():
        return False
    db.add(Achievement(student_id=student_id, badge_code=code))
    db.commit()
    return True


def touch_streak(db: Session, student_id: int) -> dict:
    """Call on any points-earning action. Returns streak info + any milestone fired."""
    today = date.today()
    s = db.get(Streak, student_id)
    if not s:
        s = Streak(student_id=student_id, current=0, longest=0)
        db.add(s)
    milestone = None
    if s.last_active_date == today:
        pass  # already counted today
    else:
        if s.last_active_date == today - timedelta(days=1):
            s.current += 1
        else:
            s.current = 1
        s.last_active_date = today
        s.longest = max(s.longest, s.current)
        if s.current in STREAK_MILESTONES:
            milestone = s.current
            award(db, student_id, f"streak_{s.current}", points=STREAK_MILESTONES[s.current])
            grant_badge(db, student_id, f"streak_{s.current}")
    db.commit()
    # keep last_active_at on the student fresh too
    st = db.get(Student, student_id)
    if st:
        from .models import now as _now
        st.last_active_at = _now()
        db.commit()
    return {"current": s.current, "longest": s.longest, "milestone": milestone}


def stats(db: Session, student_id: int) -> dict:
    total = total_points(db, student_id)
    s = db.get(Streak, student_id)
    badges = [a.badge_code for a in db.query(Achievement).filter_by(student_id=student_id).all()]
    return {
        **level_progress(total),
        "streak": (s.current if s else 0),
        "longest": (s.longest if s else 0),
        "badges": badges,
        "gems": total,
    }
