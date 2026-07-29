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


def _mask_email(e: str) -> str:
    """Privacy-light masking for the ops feed: 'deepak@trigunai.com' -> 'de***@trigunai.com'."""
    e = (e or "").strip()
    if "@" not in e:
        return e[:2] + "***" if e else ""
    user, dom = e.split("@", 1)
    return (user[:2] + "***") + "@" + dom


def pulse(db) -> dict:
    """The campaign/funnel command-center payload — read-only. Consumed by the
    `trigunai-campaign-tracker` skill. Tracks EVERY signup/login regardless of source.

    IMPORTANT: the `students` table is ONE shared DB holding TWO different products:
      1. the OLD course cohort (agentic/remote-swe/… — the grandfathered ₹499 track), and
      2. the NEW exam-prep ASSESSMENT users (the ₹199 track the ads point at).
    The campaign is about (2). So the acquisition numbers here are SCOPED to exam-prep
    students only; the course cohort is reported separately for context, never mixed in.
    An exam-prep student = has an exam-prep topic OR is on the ₹199 assess track OR is a
    teacher/institute (the new B2B assessment side)."""
    from .models import StudentTopic
    m = metrics(db)
    now_ = datetime.utcnow()
    d1, d7 = _since(d=1), _since(d=7)

    students = db.query(Student).all()
    topic_ids = {sid for (sid,) in db.query(StudentTopic.student_id).distinct().all()}

    def is_exam_prep(s):
        return ((getattr(s, "assess_status", "none") or "none") != "none"
                or s.id in topic_ids
                or getattr(s, "is_teacher", False))

    ep_students = [s for s in students if is_exam_prep(s)]
    ep_ids = {s.id for s in ep_students}

    def acount(status):
        return sum(1 for s in ep_students if (getattr(s, "assess_status", "none") or "none") == status)

    # --- exam-prep (₹199 assessment track) — SCOPED to the funnel these ads point at ---
    exam_prep = {
        "total": len(ep_students),                  # exam-prep students only (NOT the 27 course rows)
        "new_24h": sum(1 for s in ep_students if s.enrolled_at and s.enrolled_at >= d1),
        "new_7d": sum(1 for s in ep_students if s.enrolled_at and s.enrolled_at >= d7),
        "assess_trialing": acount("trialing"),
        "assess_active": acount("active"),          # ← the PAID number that ends the gate
        "assess_past_due": acount("past_due"),
        "assess_cancelled": acount("cancelled"),
        "assess_comped": acount("comped"),
        "teachers": sum(1 for s in ep_students if getattr(s, "is_teacher", False)),
        "institutes": sorted({s.institute for s in ep_students if getattr(s, "institute", "")})[:30],
        "with_topics": len(topic_ids & ep_ids),
        "logins_24h": sum(1 for s in ep_students if s.last_active_at and s.last_active_at >= d1),
        "logins_7d": sum(1 for s in ep_students if s.last_active_at and s.last_active_at >= d7),
    }

    # --- course cohort (the OTHER, older product) — for context only, kept separate ---
    course_cohort = {
        "total": len(students) - len(ep_students),
        "grandfathered": sum(1 for s in students if s.id not in ep_ids and s.sub_status == "grandfathered"),
        "note": "old course track (₹499) — NOT the assessment funnel the ads target",
    }

    # --- who is joining (exam-prep only, last 25), first topic + whether they've paid ---
    first_topic = {}
    for st in db.query(StudentTopic).order_by(StudentTopic.created_at.asc()).all():
        first_topic.setdefault(st.student_id, st.title or st.topic_key)
    recent_signups = []
    for s in sorted(ep_students, key=lambda x: x.enrolled_at or now_, reverse=True)[:25]:
        recent_signups.append({
            "id": s.id,
            "name": s.name or "—",
            "email": _mask_email(s.email),
            "role": "teacher" if getattr(s, "is_teacher", False) else "student",
            "institute": getattr(s, "institute", "") or "",
            "course": s.course,
            "topic": first_topic.get(s.id, ""),
            "assess": getattr(s, "assess_status", "none") or "none",
            "sub": s.sub_status or "none",
            "joined": (s.enrolled_at or now_).strftime("%d %b %H:%M"),
            "last_active": (s.last_active_at or now_).strftime("%d %b %H:%M"),
        })

    return {
        "as_of": now_.strftime("%Y-%m-%d %H:%M UTC"),
        "web": m["web"],            # includes top_refs = traffic SOURCE attribution
        "exam_prep": exam_prep,     # SCOPED — the campaign funnel
        "course_cohort": course_cohort,   # separate, for context
        "recent_signups": recent_signups,
    }


def _classify_source(texts) -> str:
    """Best-guess acquisition source from a student's visit refs/paths."""
    blob = " ".join(t for t in texts if t).lower()
    if "gad_source" in blob or "gclid" in blob or "utm_source=google" in blob:
        return "Google Ads"
    if "linkedin" in blob or "utm_source=linkedin" in blob:
        return "LinkedIn"
    if "wa.me" in blob or "whatsapp" in blob or "utm_source=whatsapp" in blob:
        return "WhatsApp"
    if "utm_source=" in blob:
        import re
        m = re.search(r"utm_source=([a-z0-9_]+)", blob)
        return (m.group(1).title() if m else "Campaign")
    # first external referrer host that isn't ours
    for t in texts:
        t = (t or "").lower()
        if t.startswith("http") and "acharya.trigunai" not in t and "trigunai.com" not in t and t:
            host = t.split("//", 1)[-1].split("/", 1)[0]
            if host:
                return host
    return "Direct / organic"


def student_detail(db, sid: int) -> dict | None:
    """Full per-student (or per-teacher) activity for the dashboard drill-down. Read-only.
    Students: topics, adaptive tests, mock papers, mastery, page journey, acquisition source.
    Teachers: the class tests they created + how many students sat them."""
    from datetime import datetime as _dt
    from .models import (Student, StudentTopic, TopicAttempt, PaperAttempt, ConceptStat,
                         LearningEvent, Event, Visit, ClassTest, ClassSitting, MockPaper)
    s = db.get(Student, sid)
    if not s:
        return None

    def dts(v):
        return v.strftime("%d %b %H:%M") if isinstance(v, _dt) else v

    visits = db.query(Visit).filter_by(student_id=sid).order_by(Visit.created_at.desc()).limit(60).all()
    source = _classify_source([v.ref for v in visits] + [v.path for v in visits])

    out = {
        "id": s.id, "name": s.name or "—", "email": _mask_email(s.email),
        "role": "teacher" if getattr(s, "is_teacher", False) else "student",
        "institute": getattr(s, "institute", "") or "",
        "course": s.course, "assess_status": getattr(s, "assess_status", "none") or "none",
        "trial_end": dts(getattr(s, "assess_trial_end", None)),
        "joined": dts(s.enrolled_at), "last_active": dts(s.last_active_at),
        "source": source,
        "topics": [{"title": t.title or t.topic_key, "key": t.topic_key, "at": dts(t.created_at)}
                   for t in db.query(StudentTopic).filter_by(student_id=sid).order_by(StudentTopic.created_at).all()],
        "adaptive_tests": [{"subject": a.title or a.subject, "score": a.score, "total": a.total, "at": dts(a.taken_at)}
                           for a in db.query(TopicAttempt).filter_by(student_id=sid).order_by(TopicAttempt.taken_at.desc()).limit(30).all()],
        "papers": [], "weak_concepts": [], "journey": [], "created_tests": [],
    }

    for p in db.query(PaperAttempt).filter_by(student_id=sid).order_by(PaperAttempt.submitted_at.desc()).limit(20).all():
        title = ""
        mp = db.get(MockPaper, p.paper_id) if p.paper_id else None
        if mp:
            title = getattr(mp, "title", "") or getattr(mp, "exam", "")
        dur = None
        if p.started_at and p.submitted_at:
            dur = int((p.submitted_at - p.started_at).total_seconds())
        out["papers"].append({"title": title or f"Mock #{p.paper_id}", "score": p.score, "max": p.max_score,
                              "correct": p.correct, "wrong": p.wrong, "skipped": p.skipped,
                              "seconds": dur, "at": dts(p.submitted_at)})

    for cs in db.query(ConceptStat).filter_by(student_id=sid).order_by(ConceptStat.seen.desc()).limit(12).all():
        rate = round((cs.correct / cs.seen) * 100) if cs.seen else 0
        out["weak_concepts"].append({"concept": cs.concept, "subject": cs.subject, "seen": cs.seen, "pct": rate})

    for v in visits[:40]:
        out["journey"].append({"path": v.path, "ref": v.ref or "", "at": dts(v.created_at)})

    # teacher side — tests they created + total sittings
    if getattr(s, "is_teacher", False):
        for ct in db.query(ClassTest).filter_by(teacher_id=sid).order_by(ClassTest.created_at.desc()).limit(30).all():
            sittings = db.query(func.count(ClassSitting.id)).filter_by(class_test_id=ct.id).scalar() or 0
            out["created_tests"].append({"title": ct.title or ct.subject_label, "code": ct.code,
                                         "subject": ct.subject_label, "n": ct.n,
                                         "sittings": sittings, "at": dts(ct.created_at)})
    return out
