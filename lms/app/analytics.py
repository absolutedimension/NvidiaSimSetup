"""Website analytics (privacy-friendly page views) + the admin system-metrics aggregation.

Page views are logged to the `visits` table by a middleware in main.py. We never store raw IPs —
only a daily-salted hash (`anon`) so we can count unique visitors per day without tracking people.
"""
import hashlib
from datetime import datetime, timedelta

from sqlalchemy import func

from .models import Visit, Student, Lesson, LessonProgress, Event, now

PRICE = 499

# Paths we don't count as "page views"
_SKIP = ("/static", "/api", "/admin", "/healthz", "/robots", "/sitemap", "/llms",
         "/google", "/webhook", "/billing", "/auth", "/favicon")
_BOTS = ("bot", "crawl", "spider", "slurp", "bingpreview", "facebookexternal",
         "headless", "lighthouse", "pingdom", "uptime")


def should_track(path: str, ua: str) -> bool:
    if any(path.startswith(p) for p in _SKIP):
        return False
    ua = (ua or "").lower()
    return not any(b in ua for b in _BOTS)


def _anon(ip: str, ua: str) -> str:
    day = datetime.utcnow().strftime("%Y%m%d")
    return hashlib.sha256(f"{ip}|{ua}|{day}".encode()).hexdigest()[:32]


def make_visit(path: str, ref: str, ip: str, ua: str, student_id):
    return Visit(path=path[:200], ref=(ref or "")[:200], anon=_anon(ip or "", ua or ""),
                 student_id=student_id)


# ---------- admin metrics ----------
def _since(h=0, d=0):
    return datetime.utcnow() - timedelta(hours=h, days=d)


def metrics(db) -> dict:
    now_ = datetime.utcnow()
    d1, d7, d30 = _since(d=1), _since(d=7), _since(d=30)

    # --- subscriptions / revenue ---
    def sub_count(**f):
        q = db.query(Student)
        for k, v in f.items():
            q = q.filter(getattr(Student, k) == v)
        return q.count()

    students = db.query(Student).all()
    active = sum(1 for s in students if s.sub_status == "active")
    trial_card = sum(1 for s in students if s.sub_status == "trialing" and s.rzp_subscription_id)
    trial_nocard = sum(1 for s in students if s.sub_status == "trialing" and not s.rzp_subscription_id
                       and s.trial_end and s.trial_end > now_)
    trial_expired = sum(1 for s in students if s.sub_status == "trialing" and not s.rzp_subscription_id
                        and (not s.trial_end or s.trial_end <= now_))
    past_due = sum(1 for s in students if s.sub_status == "past_due")
    cancelled = sum(1 for s in students if s.sub_status == "cancelled")
    grandfathered = sum(1 for s in students if s.sub_status == "grandfathered")
    none_ = sum(1 for s in students if (s.sub_status or "none") == "none")
    paying = active + past_due  # billed (or should be)
    mrr = active * PRICE

    # --- growth ---
    total = len(students)
    new_24h = db.query(Student).filter(Student.enrolled_at >= d1).count()
    new_7d = db.query(Student).filter(Student.enrolled_at >= d7).count()
    by_course = dict(db.query(Student.course, func.count(Student.id)).group_by(Student.course).all())

    # --- learning ---
    lessons_done = db.query(LessonProgress).filter_by(status="done").count()
    lessons_inprog = db.query(LessonProgress).filter_by(status="in_progress").count()
    done_7d = db.query(LessonProgress).filter(LessonProgress.status == "done",
                                              LessonProgress.completed_at >= d7).count()
    # top courses by completions (join lesson->module not needed; use Event ref or LessonProgress)
    top_lessons = (db.query(Lesson.title, func.count(LessonProgress.id))
                   .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
                   .filter(LessonProgress.status == "done")
                   .group_by(Lesson.title).order_by(func.count(LessonProgress.id).desc()).limit(8).all())

    # --- website analytics ---
    def views(since):
        return db.query(Visit).filter(Visit.created_at >= since).count()

    def uniques(since):
        return db.query(func.count(func.distinct(Visit.anon))).filter(Visit.created_at >= since).scalar() or 0

    pv_24h, pv_7d, pv_30d = views(d1), views(d7), views(d30)
    uv_24h, uv_7d = uniques(d1), uniques(d7)
    top_pages = (db.query(Visit.path, func.count(Visit.id)).filter(Visit.created_at >= d7)
                 .group_by(Visit.path).order_by(func.count(Visit.id).desc()).limit(10).all())
    top_refs = (db.query(Visit.ref, func.count(Visit.id))
                .filter(Visit.created_at >= d7, Visit.ref != "")
                .group_by(Visit.ref).order_by(func.count(Visit.id).desc()).limit(8).all())
    active_users_24h = (db.query(func.count(func.distinct(Visit.student_id)))
                        .filter(Visit.created_at >= d1, Visit.student_id.isnot(None)).scalar() or 0)

    # --- funnel (last 7d): visitors -> pricing views -> trials started -> paying ---
    pricing_views = db.query(func.count(func.distinct(Visit.anon))).filter(
        Visit.created_at >= d7, Visit.path.like("/pricing%")).scalar() or 0
    trials_started_7d = db.query(Student).filter(Student.trial_end.isnot(None),
                                                 Student.enrolled_at >= d7).count()

    # --- recent activity feed ---
    recent = (db.query(Event).order_by(Event.created_at.desc()).limit(12).all())
    recent_feed = [{"type": e.type, "when": e.created_at.strftime("%d %b %H:%M")} for e in recent]

    return {
        "subs": {"total": total, "active": active, "trial_card": trial_card,
                 "trial_nocard": trial_nocard, "trial_expired": trial_expired,
                 "past_due": past_due, "cancelled": cancelled, "grandfathered": grandfathered,
                 "none": none_, "paying": paying, "mrr": mrr, "arr": mrr * 12},
        "growth": {"total": total, "new_24h": new_24h, "new_7d": new_7d,
                   "by_course": sorted(by_course.items(), key=lambda x: -x[1])},
        "learning": {"done": lessons_done, "in_progress": lessons_inprog, "done_7d": done_7d,
                     "top_lessons": [(t, n) for t, n in top_lessons]},
        "web": {"pv_24h": pv_24h, "pv_7d": pv_7d, "pv_30d": pv_30d, "uv_24h": uv_24h, "uv_7d": uv_7d,
                "active_users_24h": active_users_24h,
                "top_pages": [(p, n) for p, n in top_pages],
                "top_refs": [(r, n) for r, n in top_refs]},
        "funnel": {"visitors_7d": uv_7d, "pricing_views_7d": pricing_views,
                   "trials_7d": trials_started_7d, "paying": paying},
        "recent": recent_feed,
    }
