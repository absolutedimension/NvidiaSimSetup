import base64
import hashlib
import hmac
import re
import secrets
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from . import analytics, assess_gen, billing, catalog, course_details, examgen, gamify, legal, mockpaper, notify, personalize, seo, teasers, tutor
from . import kids_worksheet as kidsws   # worksheet + adaptive assessment engine (kids + seniors)
from .config import settings
from .db import get_db
from .emailer import send_magic_link
from .models import (
    AssessmentItem, Assignment, AssignmentCompletion, ClassSitting, ClassTest, CompSession, ConceptStat, CourseRequest, GenJob, LearnerFact, Lesson, LessonProgress, LearningEvent, MockPaper, Module, PaperAttempt, SeenQuestion, Student, StudentTopic, TaskCompletion, TeacherInvite, TopicAttempt, WorkbookTask, now,
)
from .security import consume_magic_token, get_or_create_student, issue_magic_token

BASE = Path(__file__).parent
COHORT_START = date(2026, 6, 26)

# The catalog shown on the login page. "ready" courses have live content + the Acharya tutor.
COURSES = [
    {"id": "agentic",          "title": "Build Agentic AI Systems",                          "ready": True},
    {"id": "remote-swe",       "title": "Command the Coding Agent — Crack the Remote SWE Job", "ready": True},
    {"id": "ml-and-math",      "title": "Machine Learning & Its Math",                        "ready": True},
    {"id": "physical-ai",      "title": "Physical AI — Train a Robot in Simulation",          "ready": True},
    {"id": "vr-mr-app",        "title": "Build & Ship Your First VR/MR App",                  "ready": True},
    {"id": "vr-game",          "title": "Build a Fully Immersive VR Game",                    "ready": True},
    {"id": "screen-game",      "title": "Build & Ship a Game with Blender + Unity",           "ready": True},
    {"id": "ai-video-factory", "title": "Build Your AI Video Factory",                        "ready": True},
    {"id": "ai-music-factory", "title": "Build Your AI Music Factory",                        "ready": True},
    {"id": "ai-pm",            "title": "AI Product Management",                              "ready": True},
]
COURSE_TITLES = {c["id"]: c["title"] for c in COURSES}

# One-line build promise per course — used by the acharya.trigunai.com landing page.
ACHARYA_BLURBS = {
    "agentic":          "Design agents that plan, use tools, and act on their own.",
    "remote-swe":       "Drive AI coding agents like a senior engineer — and land the remote role.",
    "ml-and-math":      "The real math under machine learning, built from intuition to working models.",
    "physical-ai":      "Train a robot policy in NVIDIA simulation and watch it learn to move.",
    "vr-mr-app":        "Ship your first real mixed-reality app to a Quest headset.",
    "vr-game":          "Design and build a complete, fully immersive VR game.",
    "screen-game":      "Model in Blender, build in Unity, ship a playable game.",
    "ai-video-factory": "Turn a script into finished, narrated video — on autopilot.",
    "ai-music-factory": "Generate original, copyright-clean music end to end.",
    "ai-pm":            "Scope, ship, and run AI products that actually work — the PM playbook.",
}
# Per-course live-shader thumbnail on the acharya landing: [shader_index, time_seed].
# Shaders (in acharya.html): 0 streams · 1 circuit · 2 particles · 3 orbit · 4 portal · 5 waveform.
ACHARYA_THUMBS = {
    "agentic":          [0, 0.0],
    "remote-swe":       [1, 0.0],
    "ml-and-math":      [2, 0.0],
    "physical-ai":      [3, 0.0],
    "vr-mr-app":        [4, 0.0],
    "vr-game":          [4, 1.7],
    "screen-game":      [1, 2.3],
    "ai-video-factory": [5, 0.0],
    "ai-music-factory": [5, 1.5],
    "ai-pm":            [2, 3.0],
}
# ── Student exam-prep product (acharya.trigunai.com/exam-prep) ──────────────────
# Each exam maps to an assessment "subject" the adaptive engine serves. Phase 1 = curated
# packs (the 5 below); dynamic per-topic generation for any exam is Phase 2.
EXAMS = [
    {"id": "neet",     "subject": "neet-biology", "title": "NEET",     "tag": "Medical entrance",    "emoji": "🧬"},
    {"id": "jee",      "subject": "jee-physics",  "title": "JEE",      "tag": "Engineering entrance", "emoji": "⚛️"},
    {"id": "class10",  "subject": "cbse10-science", "title": "Class 10", "tag": "Boards · Science",   "emoji": "📘"},
    {"id": "class12",  "subject": "cbse12-physics", "title": "Class 12", "tag": "Boards · PCB",        "emoji": "📗"},
    {"id": "commerce", "subject": "cbse12-accountancy", "title": "Class 12 Commerce", "tag": "Accounts · Economics", "emoji": "📊"},
    {"id": "banking",  "subject": "banking-quant", "title": "Banking", "tag": "IBPS · SBI · RRB",     "emoji": "🏦"},
    {"id": "upsc",     "subject": "upsc-gs",      "title": "UPSC",     "tag": "Civil Services · IAS", "emoji": "🏛️"},
    {"id": "class3",   "subject": "class3-maths", "title": "Class 3",  "tag": "ICSE · Maths",        "emoji": "🔢"},
]
EXAM_SUBJECT = {e["id"]: e["subject"] for e in EXAMS}

# Kids product picker (kids-education.trigunai.com). Grade-3 Maths is LIVE; the rest show the
# roadmap as "coming soon" so parents see what's next.
KIDS_EXAMS = [
    {"id": "class3",       "title": "Grade 3 · Maths",   "tag": "ICSE / CBSE",       "emoji": "🔢", "available": True},
    {"id": "class3-evs",   "title": "Grade 3 · EVS",     "tag": "Science & World",   "emoji": "🌍", "available": True},
    {"id": "class3-eng",   "title": "Grade 3 · English", "tag": "Grammar & Reading", "emoji": "📖", "available": True},
    {"id": "class3-gk",    "title": "Grade 3 · GK",      "tag": "General Knowledge", "emoji": "🧠", "available": True},
    {"id": "class3-hindi", "title": "Grade 3 · Hindi",   "tag": "पढ़ना-लिखना",         "emoji": "🇮🇳", "available": True},
    {"id": "class4",       "title": "Grade 4",           "tag": "Coming soon",       "emoji": "🎈", "available": False},
    {"id": "class5",       "title": "Grade 5",           "tag": "Coming soon",       "emoji": "🚀", "available": False},
]
# kids exam id → the worksheet subject it launches (curriculum names the engine understands)
KIDS_EXAM_SUBJECT = {"class3": "Mathematics", "class3-evs": "EVS", "class3-eng": "English",
                     "class3-gk": "GK", "class3-hindi": "Hindi"}

# The student-landing exam picker. JEE + NEET are LIVE (real RAG banks behind them); the rest are
# shown as "coming soon" so students see the roadmap but can only START what actually works today.
# `available: True` ones must have an id in EXAM_SUBJECT so /exam-prep/start accepts them.
STUDENT_EXAMS = [
    {"id": "jee",     "title": "JEE / IIT",     "tag": "Engineering entrance", "emoji": "⚛️", "available": True},
    {"id": "neet",    "title": "NEET",          "tag": "Medical entrance",     "emoji": "🧬", "available": True},
    {"id": "class10", "title": "CBSE Class 10", "tag": "Boards · Science",     "emoji": "📘", "available": True},
    {"id": "class12", "title": "CBSE Class 12", "tag": "Boards · PCB",         "emoji": "📗", "available": True},
    {"id": "commerce","title": "Class 12 Commerce", "tag": "Accounts · Economics", "emoji": "📊", "available": True},
    {"id": "cuet",    "title": "CUET",          "tag": "UG entrance",          "emoji": "🎓", "available": False},
    {"id": "upsc",    "title": "UPSC",          "tag": "Civil Services",       "emoji": "🏛️", "available": True},
    {"id": "ssc",     "title": "SSC",           "tag": "Govt jobs",            "emoji": "📋", "available": False},
    {"id": "banking", "title": "Banking",       "tag": "IBPS · SBI · RRB",     "emoji": "🏦", "available": True},
    {"id": "gate",    "title": "GATE",          "tag": "M.Tech · PSU",         "emoji": "⚙️", "available": False},
    {"id": "cat",     "title": "CAT",           "tag": "MBA entrance",         "emoji": "📊", "available": False},
    {"id": "clat",    "title": "CLAT",          "tag": "Law entrance",         "emoji": "⚖️", "available": False},
]

# Canonical domain. acharya.trigunai.com serves the whole app; lms.trigunai.com 301-redirects here.
CANONICAL_HOST = "acharya.trigunai.com"
ACHARYA_HOSTS = {CANONICAL_HOST}
KIDS_HOSTS = {"kids-education.trigunai.com"}   # kids product — same app, kids landing + (later) theme
LEGACY_HOSTS = {"lms.trigunai.com"}
# Paths NOT redirected from the legacy host — server-to-server callers that can't follow a 301 cleanly
# (Razorpay POSTs the webhook; the learn.trigunai.com admin GETs the bridge over the old host).
REDIRECT_EXEMPT_PREFIXES = ("/webhook", "/api/bridge", "/healthz")

app = FastAPI(title="TrigunAI LMS")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, max_age=60 * 60 * 24 * 30)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.cache = None  # avoid jinja2 LRUCache incompat on Python 3.14; negligible at cohort scale
templates.env.globals["course_title"] = lambda cid: COURSE_TITLES.get(cid, cid)
# Pricing + contact handles exposed to every template (see PRICING_MODEL.md). Billing may be inert;
# these drive the DISPLAYED offer so it's testable on a real buyer, with a WhatsApp/email close.
templates.env.globals["PRICING"] = {
    # UNIFIED FLAT PRICING (2026-08-03) — one price everywhere, by exam level.
    "foundation": settings.PRICE_FOUNDATION_INR,      # ₹120/mo — Foundation / Board
    "senior": settings.PRICE_SENIOR_INR,              # ₹250/mo — JEE / NEET / Senior
    "custom_setup": settings.INSTITUTE_CUSTOM_INR,    # ₹55,000 one-time — institute custom white-label app
    "trial_days": settings.ASSESS_TRIAL_DAYS,
    # legacy keys kept so any un-migrated template reference still resolves (do not surface these)
    "student_pass": settings.ASSESS_PASS_PRICE_INR,
    "student_monthly": settings.ASSESS_PRICE_INR,
    "teacher_solo": settings.TEACHER_SOLO_INR,
    "teacher_coaching": settings.TEACHER_COACHING_INR,
    "teacher_institute": settings.TEACHER_INSTITUTE_INR,
}
templates.env.globals["CONTACT_WA"] = settings.CONTACT_WA
templates.env.globals["CONTACT_EMAIL"] = settings.CONTACT_EMAIL


@app.middleware("http")
async def track_visits(request: Request, call_next):
    # Canonical-domain redirect: legacy lms.trigunai.com -> acharya.trigunai.com (301, keep path+query),
    # except server-to-server paths that can't follow a redirect (webhook, bridge, health probe).
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host in LEGACY_HOSTS and not request.url.path.startswith(REDIRECT_EXEMPT_PREFIXES):
        target = f"https://{CANONICAL_HOST}{request.url.path}"
        if request.url.query:
            target += f"?{request.url.query}"
        return RedirectResponse(target, status_code=301)
    response = await call_next(request)
    try:
        if request.method == "GET":
            path = request.url.path
            ua = request.headers.get("user-agent", "")
            if analytics.should_track(path, ua):
                from .db import SessionLocal
                from .models import Student as _S, now as _now
                db = SessionLocal()
                try:
                    sid = None
                    try:
                        sid = request.session.get("sid")
                    except Exception:
                        sid = None
                    ip = request.client.host if request.client else ""
                    # keep the query string so UTM tags (?utm_source=…) are captured for
                    # source attribution (e.g. the Patna-library WhatsApp campaign). should_track
                    # already ran on the bare path above.
                    track_path = f"{path}?{request.url.query}" if request.url.query else path
                    v = analytics.make_visit(track_path, request.headers.get("referer", ""), ip, ua, sid)
                    db.add(v)
                    if sid:
                        s = db.get(_S, sid)
                        if s:
                            s.last_active_at = _now()
                    db.commit()
                finally:
                    db.close()
    except Exception:
        pass
    return response


@app.on_event("startup")
def _startup():
    try:
        from . import seed
        seed.run()
    except Exception as exc:  # don't crash boot if seed re-runs
        print(f"[startup] seed skipped/failed: {exc}")


# ---------- helpers ----------
def current_week() -> int:
    today = date.today()
    if today < COHORT_START:
        return 0
    return min(12, (today - COHORT_START).days // 7)


def current_student(request: Request, db: Session) -> Student | None:
    sid = request.session.get("sid")
    if not sid:
        return None
    return db.get(Student, sid)


def require_student(request: Request, db: Session) -> Student:
    s = current_student(request, db)
    if not s:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return s


# ---------- access gate (subscriptions) ----------
# Statuses that get full content access. 'grandfathered' = pre-launch cohort students.
ACCESS_OK = {"trialing", "active", "grandfathered"}


def is_live_student(student: Student) -> bool:
    """True if the student is already in the LIVE cohort (has live classes).

    Live-cohort members are tracked as 'grandfathered'. Everyone else on the LMS
    is on the self-paced ("offline") track and is offered the upgrade-to-live CTA.
    To move a student onto the live track, set their sub_status to 'grandfathered'."""
    return (student.sub_status or "") == "grandfathered"


# learn.trigunai.com was retired (301→acharya); the live-cohort flow is now handled on Acharya/LMS.
# The "upgrade to live" CTA sends students to the Acharya sign-in, carrying their course.
LIVE_BOOK_BASE = "https://acharya.trigunai.com/login"


def live_upgrade_url(student: Student) -> str:
    return f"{LIVE_BOOK_BASE}?course={quote(student.course or 'agentic')}"


def _trial_active(student: Student) -> bool:
    return bool(student.trial_end and student.trial_end > datetime.utcnow())


def has_access(student: Student) -> bool:
    """True if the student may see paid content. When SUBS_ENABLED is False this is always
    True (nothing is paywalled) — so deploying this code changes NOTHING until we flip it on.

    Two kinds of trial:
      • card-on-file trial  → has rzp_subscription_id; Razorpay auto-charges at day 7, so access
        stays on (status flips active/past_due via webhook).
      • no-card ("skip payment") trial → no subscription; access ONLY until trial_end, then locked
        until they subscribe."""
    if not settings.SUBS_ENABLED:
        return True
    if student.is_admin:
        return True
    st = student.sub_status or "none"
    if st in ("active", "grandfathered"):
        return True
    if st == "trialing":
        if student.rzp_subscription_id:        # card on file — Razorpay manages it
            return True
        return _trial_active(student)          # no-card trial — only until it expires
    return False


def has_assessment_access(db: Session, student: Student) -> bool:
    """Gate for the ₹199 exam-prep assessment plan (a SEPARATE track from has_access). When
    ASSESS_ENABLED is False this is ALWAYS True — /exam-prep stays free for everyone (the
    soft-launch state), so deploying this changes NOTHING until we flip it on. On the first gated
    access AFTER it's enabled, a 14-day free trial starts LAZILY, so the clock begins when the
    paywall goes live — no existing signup is retroactively expired."""
    if not settings.ASSESS_ENABLED:
        return True
    if student.is_admin:
        return True
    st = student.assess_status or "none"
    if st in ("active", "comped"):
        return True
    if st == "trialing":
        if student.rzp_assess_subscription_id:      # card on file — Razorpay manages it
            return True
        return bool(student.assess_trial_end and student.assess_trial_end > datetime.utcnow())
    if st == "none":                                 # lazy-start the 14-day trial on first gated access
        student.assess_status = "trialing"
        student.assess_trial_end = datetime.utcnow() + timedelta(days=settings.ASSESS_TRIAL_DAYS)
        db.commit()
        return True
    return False   # expired / cancelled → must subscribe


def chat_url_for(email: str, course: str = "agentic") -> str:
    """Signed, 1-hour link to the Acharya web chat (same secret as the Gurukul bridge). Carries the course."""
    if not settings.CHAT_SECRET:
        return ""
    exp = str(int(time.time() * 1000) + 3600_000)  # ms, 1h
    sig = hmac.new(settings.CHAT_SECRET.encode(), f"{email}|{course}|{exp}".encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{email}|{course}|{exp}|{sig}".encode()).decode().rstrip("=")
    return f"{settings.GURUKUL_CHAT_URL}?t={token}"


# ---------- auth ----------
@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db)):
    host = (request.headers.get("host") or "").split(":")[0].lower()
    # Kids product (kids-education.trigunai.com): logged-in kids go to the exam-prep dashboard,
    # visitors get the playful kids landing. Same pipeline underneath.
    if host in KIDS_HOSTS:
        if current_student(request, db):
            return RedirectResponse("/exam-prep/dashboard")
        return HTMLResponse((BASE / "static" / "kids" / "index.html").read_text(encoding="utf-8"),
                            headers={"Cache-Control": "no-cache, must-revalidate"})
    # Logged-in students always go to their dashboard; visitors get the gold Acharya landing.
    if current_student(request, db):
        return RedirectResponse("/dashboard")
    if host in ACHARYA_HOSTS:
        return templates.TemplateResponse(request, "acharya.html",
                                          {"courses": COURSES, "blurbs": ACHARYA_BLURBS,
                                           "thumbs": ACHARYA_THUMBS})
    return RedirectResponse("/login")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, course: str = "", db: Session = Depends(get_db)):
    outlines: dict[str, list[str]] = {}
    for m in db.query(Module).order_by(Module.course, Module.week).all():
        outlines.setdefault(m.course, []).append(m.title)
    return templates.TemplateResponse(request, "login.html",
                                      {"courses": COURSES, "preselect": course, "outlines": outlines,
                                       "details": course_details.COURSE_DETAILS,
                                       "jsonld": seo.login_jsonld(COURSES)})


@app.post("/login")
def login_submit(request: Request, email: str = Form(...), course: str = Form(""), phone: str = Form(""), website: str = Form(""), db: Session = Depends(get_db)):
    email = email.lower().strip()
    if _looks_like_bot(email, website):          # honeypot filled or throwaway domain → send nothing, look normal
        return templates.TemplateResponse(request, "check_email.html", {"email": email})
    raw = issue_magic_token(db, email)
    link = f"{settings.BASE_URL}/auth/verify?token={raw}"
    if course.strip() in COURSE_TITLES:
        link += f"&course={course.strip()}"
    p = "".join(c for c in phone if c.isdigit())[:15]   # optional WhatsApp number → learn on WhatsApp too
    if p:
        link += f"&phone={p}"
    send_magic_link(email, link)
    return templates.TemplateResponse(request, "check_email.html", {"email": email})


@app.get("/auth/verify")
def verify(request: Request, token: str, course: str = "", phone: str = "", db: Session = Depends(get_db)):
    # DO NOT consume the token or create the account on this GET. Corporate email-security
    # scanners (Mimecast / Proofpoint / Microsoft Safe Links) auto-fetch every link in an
    # incoming email — if the GET created the account, those scanners silently sign up real
    # addresses as "bots" (0 page views, empty name, junk phone). Account creation happens ONLY
    # on the POST below, which a link-scanner does not perform. This also stops scanners from
    # prematurely BURNING a one-time token before the human clicks. One extra click for users.
    return templates.TemplateResponse(
        request, "verify_confirm.html",
        {"token": token, "course": course, "phone": phone})


@app.post("/auth/verify")
def verify_complete(request: Request, token: str = Form(...), course: str = Form(""),
                    phone: str = Form(""), website: str = Form(""), db: Session = Depends(get_db)):
    if (website or "").strip():                 # honeypot on the confirm form → bot, do nothing
        return RedirectResponse("/login", status_code=302)
    email = consume_magic_token(db, token)
    if not email:
        outlines: dict[str, list[str]] = {}
        for mod in db.query(Module).order_by(Module.course, Module.week).all():
            outlines.setdefault(mod.course, []).append(mod.title)
        return templates.TemplateResponse(
            request, "login.html",
            {"courses": COURSES, "preselect": "", "outlines": outlines,
             "details": course_details.COURSE_DETAILS, "jsonld": seo.login_jsonld(COURSES),
             "error": "That link expired or was already used. Request a new one."}
        )
    is_new = db.query(Student).filter_by(email=email).first() is None
    student = get_or_create_student(db, email)
    if course.strip() in COURSE_TITLES:        # course chosen at login -> set/switch it
        student.course = course.strip()
    p = "".join(c for c in phone if c.isdigit())[:15]   # optional WhatsApp number captured at signup
    if p:
        student.phone = p
    db.commit()
    if is_new:
        total = db.query(Student).count()
        notify.notify_admin(f"🎓 New signup — {student.email} · {COURSE_TITLES.get(student.course, student.course)} · {total} learners total")
    request.session["sid"] = student.id
    return RedirectResponse("/dashboard", status_code=302)


# ---------- student exam-prep funnel (acharya.trigunai.com/exam-prep) ----------
def _set_fact(db, student, key, value, source="prompt"):
    """Upsert a single LearnerFact (student_id, key) — used to store the chosen exam etc."""
    f = db.query(LearnerFact).filter_by(student_id=student.id, key=key).first()
    if f:
        f.value = value
    else:
        db.add(LearnerFact(student_id=student.id, key=key, value=value, source=source))


# ── "Earn your free access" — the ad hook: an 11-question competition → earn 1-12 months free ──
COMP_N = 11             # questions in the competition
COMP_SECONDS = 300      # ~5 minutes, exam-style





def _start_trial(db, student):
    """Give EVERY student the same flat free trial (ASSESS_TRIAL_DAYS, default 14), then ₹199/mo.

    Replaces the old 'earn 14-60 days by scoring well' competition — one mechanic instead of three
    overlapping ones (flat trial vs earned days vs paid), which was confusing to explain and to price.
    Never shortens an existing window."""
    end = datetime.utcnow() + timedelta(days=settings.ASSESS_TRIAL_DAYS)
    if not student.assess_trial_end or end > student.assess_trial_end:
        student.assess_trial_end = end
    if (student.assess_status or "none") in ("", "none"):
        student.assess_status = "trialing"


# ── "My topics" — the unit the ₹199 plan is metered in (up to 5 per student) ──
MAX_TOPICS = 5


def _topic_from(exam: str, qtext: str):
    """(topic_key, title, kind) for a chosen curated exam id OR a free-text topic."""
    qtext = (qtext or "").strip()[:80]
    if qtext:
        return (_exam_key(qtext), qtext[:120], "custom")          # 'q:<slug>'
    e = next((x for x in EXAMS if x["id"] == exam), None) or EXAMS[0]
    return (e["id"], e["title"], "exam")


def _student_topics(db, student):
    return (db.query(StudentTopic).filter_by(student_id=student.id)
            .order_by(StudentTopic.created_at).all())


def _add_topic(db, student, topic_key: str, title: str, kind: str = "exam"):
    """Add a topic (idempotent, capped at MAX_TOPICS). Returns 'added' | 'exists' | 'full'."""
    existing = _student_topics(db, student)
    if any(t.topic_key == topic_key for t in existing):
        return "exists"
    if len(existing) >= MAX_TOPICS:
        return "full"
    db.add(StudentTopic(student_id=student.id, topic_key=topic_key, title=title[:120], kind=kind))
    return "added"


def _seed_topic(db, student, exam: str, qtext: str):
    """On signup, make the chosen exam/challenge subject the student's first topic."""
    tk, title, kind = _topic_from(exam, qtext)
    _add_topic(db, student, tk, title, kind)


def _student_goal(db, student, topics=None) -> str:
    """The student's goal id. EXPLICIT (chosen in onboarding) wins; otherwise inferred from the
    subjects they're actually practising, so pre-onboarding accounts still get a sane answer."""
    f = db.query(LearnerFact).filter_by(student_id=student.id, key="goal").first()
    if f and f.value in examgen.GOALS:
        return f.value
    for t in (topics if topics is not None else _student_topics(db, student)):
        sid = examgen.match_subject(t.title, t.topic_key)
        g = examgen.goal_of_subject(sid) if sid else None
        if g:
            return g
    hay = " ".join(t.title.lower() for t in (topics if topics is not None else _student_topics(db, student)))
    if "class 12" in hay:
        return "cbse-12"
    if "class 10" in hay:
        return "cbse-10"
    if "neet" in hay:
        return "neet"
    if "upsc" in hay or "civil services" in hay:
        return "upsc"
    return ""                                    # unknown — the dashboard says "Exam prep"


@app.get("/exam-prep/onboarding", response_class=HTMLResponse)
def exam_prep_onboarding(request: Request, new: str = "", db: Session = Depends(get_db)):
    """Explicit goal pick — the first thing a new student sees, and the way any student changes
    goal later. Replaces inferring the goal from whatever topic happened to get auto-seeded."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    topics = _student_topics(db, student)
    have = {examgen.match_subject(t.title, t.topic_key) for t in topics}
    goal = _student_goal(db, student, topics)
    # Kids host: show ONLY the kids goals (Grade 3 …) — never the senior JEE/NEET/UPSC courses.
    kids = (request.headers.get("host") or "").split(":")[0].lower() in KIDS_HOSTS
    goals = ({gid: g for gid, g in examgen.GOALS.items() if gid in _KIDS_TEACHER_GOALS}
             if kids else examgen.GOALS)
    default_goal = ("class3" if kids else examgen.DEFAULT_GOAL)
    if kids and goal not in goals:
        goal = "class3"
    return templates.TemplateResponse(request, "exam_prep_onboarding.html", {
        "student": student,
        "goals": goals,
        "subjects": examgen.RAG_SUBJECTS,
        "goal": goal or default_goal,
        "chosen": {s for s in have if s},        # subjects they already have as topics
        "new": "1" if new == "1" else "",
        "max_topics": MAX_TOPICS,
        "first_time": not any(examgen.match_subject(t.title, t.topic_key) for t in topics),
    })


@app.post("/exam-prep/onboarding")
def exam_prep_onboarding_save(request: Request, goal: str = Form(""), subject: list[str] = Form([]),
                              new: str = Form(""), db: Session = Depends(get_db)):
    """Save the chosen goal + seed one topic per chosen subject, then on to the Today screen."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    goal = goal if goal in examgen.GOALS else examgen.DEFAULT_GOAL
    g = examgen.GOALS[goal]
    picked = [s for s in subject if s in g["subjects"]] or list(g["subjects"])
    _set_fact(db, student, "goal", goal, source="prompt")

    # Make room for — and give priority to — the chosen goal's subjects. We prune two kinds of
    # topic, and NOTHING else (custom 'q:' topics and this goal's own subjects are always kept):
    #   1. the vague auto-seeded curated id ('JEE'/'NEET' — no subject, detail page just says
    #      "being set up"); the real per-subject topics below replace it.
    #   2. RAG subjects that belong to a DIFFERENT goal — so "change goal" actually switches
    #      instead of piling both exams' subjects up against MAX_TOPICS.
    # Progress (ConceptStat) is keyed by subject+concept, independent of these rows, so a student
    # who switches back later keeps their history.
    for t in _student_topics(db, student):
        sid = examgen.match_subject(t.title, t.topic_key)
        if sid and examgen.goal_of_subject(sid) not in (None, goal):
            db.delete(t)                                        # a different goal's subject
        elif t.topic_key in EXAM_SUBJECT and not sid:
            db.delete(t)                                        # vague auto-seeded curated id
    db.flush()

    for sid in picked:                            # _add_topic enforces MAX_TOPICS + idempotency
        _add_topic(db, student, sid, examgen.RAG_SUBJECTS[sid]["label"], "exam")
    db.commit()
    return RedirectResponse("/exam-prep/dashboard" + ("?new=1" if new == "1" else ""), status_code=302)


def _days_left(student) -> int:
    """Whole free-access days remaining in the assessment window (0 if none/expired)."""
    if not student.assess_trial_end:
        return 0
    secs = (student.assess_trial_end - datetime.utcnow()).total_seconds()
    if secs <= 0:
        return 0
    import math
    return int(math.ceil(secs / 86400))


@app.get("/exam-prep", response_class=HTMLResponse)
def exam_prep(request: Request, exam: str = "", g: int = 0, db: Session = Depends(get_db)):
    student = current_student(request, db)
    host = (request.headers.get("host") or "").split(":")[0].lower()
    kids = host in KIDS_HOSTS
    if kids and g in (1, 2, 3, 4, 5):        # class picked on the landing → carried into signup
        request.session["kid_grade"] = g
    # kids site = ONLY the kids exams; acharya = the professional exams. (Separate audiences.)
    exam_list = KIDS_EXAMS if kids else STUDENT_EXAMS
    resume_exam = ("class3" if kids else EXAMS[0]["id"])
    if student:
        f = db.query(LearnerFact).filter_by(student_id=student.id, key="exam").first()
        if f and f.value in EXAM_SUBJECT:
            resume_exam = f.value
    # pre-select a tile if a live exam id came in (e.g. from an ad URL /exam-prep?exam=neet)
    live = {e["id"] for e in exam_list if e["available"]}
    picked = exam.strip() if exam.strip() in live else ("class3" if kids else "")
    return templates.TemplateResponse(request, "exam_prep.html",
                                      {"exams": exam_list, "kids_exams": None,
                                       "student": student, "resume_exam": resume_exam,
                                       "kids": kids,
                                       "picked": picked, "wa_link": "https://wa.me/919135255107?text=quiz",
                                       "google_client_id": settings.GOOGLE_CLIENT_ID,
                                       "jsonld": seo.exam_prep_jsonld(EXAMS)})


# --- Anti-bot signup guard (honeypot + disposable-domain blocklist) ---------
# `website` is a HIDDEN honeypot field: invisible + un-tabbable for humans, but
# auto-filled by form-spamming bots. A filled honeypot OR a known throwaway domain
# => it's a bot, so we create NOTHING and return a normal-looking response. Zero
# friction for real users (no captcha, no email verification). Extend the set as
# new junk domains show up in the pulse.
_BOT_EMAIL_DOMAINS = {"immenseignite.info"}

def _looks_like_bot(email: str, honeypot: str) -> bool:
    if (honeypot or "").strip():                 # honeypot filled → definitely a bot
        return True
    dom = email.split("@")[-1].strip().lower() if "@" in (email or "") else ""
    return dom in _BOT_EMAIL_DOMAINS


@app.post("/exam-prep/start")
def exam_prep_start(request: Request, email: str = Form(...), exam: str = Form(""),
                    phone: str = Form(""), q: str = Form(""), earn: str = Form(""),
                    website: str = Form(""), db: Session = Depends(get_db)):
    """Instant free signup: email → account + session → straight into the assessment.
    No magic-link round-trip for the free tier (the magic link stays the re-login path).
    `q` = a free-text exam/topic → a dynamically-generated test; otherwise a curated exam.
    `earn` = a signed token from the competition → banks the server-scored earned free-access days."""
    email = email.lower().strip()
    if _looks_like_bot(email, website):          # honeypot filled or throwaway domain → no account, no session
        return RedirectResponse("/exam-prep", status_code=302)
    qtext = (q or "").strip()[:80]
    host = (request.headers.get("host") or "").split(":")[0].lower()
    kids = host in KIDS_HOSTS
    # kids: any Grade-3 subject tile → seed Maths (the one examgen kids entry) but remember the picked
    # subject so we can drop the child straight into ITS adaptive worksheet after signup.
    kids_subject = KIDS_EXAM_SUBJECT.get(exam.strip(), "Mathematics") if kids else None
    ex = "class3" if kids else (exam.strip() if exam.strip() in EXAM_SUBJECT else EXAMS[0]["id"])
    if "@" not in email or "." not in email.split("@")[-1]:
        return templates.TemplateResponse(request, "exam_prep.html",
                                          {"exams": EXAMS, "student": None, "resume_exam": ex,
                                           "jsonld": seo.exam_prep_jsonld(EXAMS),
                                           "error": "Please enter a valid email."})
    existed = db.query(Student).filter_by(email=email).first() is not None
    student = get_or_create_student(db, email)
    label = ("q:" + qtext) if qtext else ex
    _set_fact(db, student, "exam", label)
    _start_trial(db, student)          # everyone gets the same free trial
    _seed_topic(db, student, ex, qtext)              # chosen subject → first "my topic"
    p = "".join(c for c in phone if c.isdigit())[:15]
    if p and not student.phone:
        student.phone = p
    db.commit()
    if not existed:
        total = db.query(Student).count()
        notify.notify_admin(f"🎯 New student (exam-prep) — {student.email} · {label} · {total} learners total")
    request.session["sid"] = student.id
    # Kids: straight into the chosen subject's adaptive worksheet (all subjects live). If they picked a
    # CLASS on the landing, remember it so their worksheets serve that grade (and hide the grade picker).
    if kids:
        kg = request.session.pop("kid_grade", None)
        if kg in (1, 2, 3, 4, 5):
            student.grade = kg
            student.board = student.board or "CBSE"
            db.commit()
        return RedirectResponse(f"/exam-prep/worksheet?subject={quote(kids_subject)}", status_code=302)
    # A brand-new student picks their goal first; returning students go straight home.
    # new=1 rides through onboarding so the Ads signup conversion still fires on the dashboard.
    if not existed:
        return RedirectResponse("/exam-prep/onboarding?new=1", status_code=302)
    return RedirectResponse("/exam-prep/dashboard", status_code=302)


@app.get("/exam-prep/test", response_class=HTMLResponse)
def exam_prep_test(request: Request, exam: str = "", q: str = "", new: str = "",
                   src: str = "", subject: str = "", sel: str = "", diff: str = "3-4",
                   n: int = 5, fig: str = "", title: str = "", db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    if not has_assessment_access(db, student):
        return RedirectResponse("/exam-prep/upgrade", status_code=302)
    # Kids product: the bright voice-quiz UI (JJ/Mikey, gems, speak-or-tap) — same look as the
    # landing sample — driven by the SHARED pool. Flow is kid-scoped; data/pool are common.
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host in KIDS_HOSTS:
        # CUSTOM / CHAT / topic-selected tests → the adaptive WORKSHEET flow (any subject/chapter).
        # (Plain exam launch with no topic keeps the quick voice-quiz.)
        topic = (q or sel or "").strip()
        if topic or src == "examgen":
            ch = topic.split("::")[0].split("|")[0].strip()[:60]
            subj = subject.strip() or "Mathematics"
            return RedirectResponse(f"/exam-prep/worksheet?subject={quote(subj)}&chapter={quote(ch)}", status_code=302)
        first_ch = (sel.split("::")[0].strip() if sel else "")
        return templates.TemplateResponse(request, "kids_quiz_live.html", {
            "student": student, "chapter": first_ch, "n": max(1, min(int(n or 5), 10)),
            "diff": (diff if diff in ("1", "1-2", "2") else "1-2")})
    exam = exam.strip()
    qtext = (q or "").strip()[:80]
    ex = next((e for e in EXAMS if e["id"] == exam), None)
    if src == "examgen" and sel:                        # RAG paper (IIT-JEE Physics) — the subtopic picker
        subj = subject or "jee-physics"
        n_clamped = max(1, min(int(n), 15))
        gen = (f"/api/examgen/generate?subject={quote(subj)}&sel={quote(sel)}"
               f"&diff={quote(diff)}&n={n_clamped}" + ("&fig=1" if fig == "1" else ""))
        gtitle = title or examgen.RAG_SUBJECTS.get(subj, {}).get("label", "JEE Physics")
        # __SUBJECT carries the subject id so /api/assess/complete records progress under it
        # (boot still uses __GEN_URL — it takes precedence over the curated-SUBJECTS path).
        inject = (f"<script>window.__STUDENT=true;window.__SUBJECT={subj!r};window.__GEN_URL={gen!r};"
                  f"window.__GEN_TITLE={gtitle!r};window.__TITLE={gtitle!r};</script>")
    elif ex and ex.get("subject"):                     # curated exam → instant, no LLM
        inject = f"<script>window.__STUDENT=true;window.__SUBJECT={ex['subject']!r};</script>"
    elif qtext:                                         # free-text exam → dynamic generation
        gen = f"/api/assess/generate?q={quote(qtext)}"
        inject = (f"<script>window.__STUDENT=true;window.__GEN_URL={gen!r};"
                  f"window.__GEN_TITLE={qtext!r};</script>")
    else:                                               # fallback → first curated exam
        inject = f"<script>window.__STUDENT=true;window.__SUBJECT={EXAM_SUBJECT[EXAMS[0]['id']]!r};</script>"
    # Google Ads "free signup" conversion — fires ONCE, only for a genuinely-new account (new=1),
    # here on the page where the student is actually using the product. Inert until the label is set.
    if new == "1" and settings.STUDENT_SIGNUP_CONV_LABEL and settings.ADS_CONVERSION_ID:
        cid, lbl = settings.ADS_CONVERSION_ID, settings.STUDENT_SIGNUP_CONV_LABEL
        inject += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={cid}"></script>'
                   f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
                   f"gtag('js',new Date());gtag('config','{cid}');"
                   f"gtag('event','conversion',{{'send_to':'{cid}/{lbl}'}});</script>")
    # Kids product: same pool-driven test (shared data), but with the child-voice layer +
    # kid theming injected. The DATA path is identical to acharya; only the FLOW is kid-scoped.
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host in KIDS_HOSTS:
        inject += ('<script>window.__KIDS=true;</script>'
                   '<link rel="stylesheet" href="/static/kids/kids_voice.css">'
                   '<script src="/static/kids/kids_voice.js" defer></script>')
    html = (BASE / "static" / "exam" / "assess.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("</head>", inject + "</head>", 1))


_TTS_CACHE: dict = {}   # (voice|rate|text) sha1 -> mp3 bytes; the pool repeats, so hit-rate is high


@app.get("/kids/tts")
async def kids_tts(text: str = "", voice: str = "en-US-AnaNeural", rate: str = "-6%"):
    """Server-side child-voice TTS for the kids voice test (edge-tts, en-US-AnaNeural).

    Speaks the question the shared pool already served — no change to the data path. Cached
    in-process by (voice,rate,text) hash; a fixed pool means most calls are cache hits."""
    text = (text or "").strip()[:600]
    if not text:
        return Response(status_code=400)
    key = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()
    data = _TTS_CACHE.get(key)
    if data is None:
        try:
            import edge_tts
        except Exception:
            return Response(status_code=503)   # lib missing → client falls back silently
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate)
            buf = bytearray()
            async for chunk in comm.stream():
                if chunk.get("type") == "audio":
                    buf += chunk["data"]
            data = bytes(buf)
        except Exception as exc:
            print(f"[kids_tts] fail: {exc}")
            return Response(status_code=502)
        if len(_TTS_CACHE) > 800:
            _TTS_CACHE.clear()
        _TTS_CACHE[key] = data
    return Response(content=data, media_type="audio/mpeg",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/api/kids/quiz")
def kids_quiz(request: Request, chapter: str = "", n: int = 5, diff: str = "1-2",
              db: Session = Depends(get_db)):
    """Questions for the kids voice-quiz UI, drawn from the SHARED pool (Grade-3 Maths).
    Maps pool rows → {q, options, answer, correct, topic}. Full-subject = a mix of chapters."""
    import random as _rnd
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    sid = "class3-maths"
    n = max(1, min(int(n or 5), 10))
    diff = diff if diff in ("1", "1-2", "2") else "1-2"
    rows = []
    if chapter and chapter not in ("Full subject", "__FULL__", "full"):
        rows, _ = examgen.fetch_pool(sid, chapter, None, diff, "MCQ_single", n * 2)
        rows = rows or []
    else:                                   # mix across the book chapters
        chs = [c["chapter"] for c in examgen.chapters_for_ui(sid)]
        _rnd.shuffle(chs)
        for ch in chs:
            qs, _ = examgen.fetch_pool(sid, ch, None, diff, "MCQ_single", 2)
            if qs:
                rows.extend(qs)
            if len(rows) >= n * 2:
                break
    _rnd.shuffle(rows)
    out = []
    seen = set()
    for qrow in rows:
        stem = (qrow.get("stem") or "").strip()
        if not stem or stem in seen:
            continue
        opts = qrow.get("options") or []
        texts = [(o.get("text") if isinstance(o, dict) else o) for o in opts]
        if len(texts) < 2:
            continue
        corr = qrow.get("correct_answer", "A")
        ai = next((i for i, o in enumerate(opts)
                   if isinstance(o, dict) and str(o.get("label")) == str(corr)), 0)
        seen.add(stem)
        out.append({"q": stem, "options": [str(t) for t in texts], "answer": ai,
                    "correct": str(texts[ai] if ai < len(texts) else texts[0]),
                    "topic": qrow.get("concept") or qrow.get("chapter") or "Maths"})
        if len(out) >= n:
            break
    return JSONResponse({"questions": out, "title": (chapter or "Class 3 Maths")})


# ================= KIDS WORKSHEET + ADAPTIVE ASSESSMENT (2026-08-02) =================
@app.get("/exam-prep/worksheet", response_class=HTMLResponse)
def kids_worksheet_page(request: Request, board: str = "CBSE", cls: int = 3, subject: str = "Mathematics",
                        chapter: str = "", n: int = 8, assign: int = 0, print: int = 0, preview: int = 0,
                        db: Session = Depends(get_db)):
    """The production worksheet experience (kids UI, asset-decorated, adaptive). Kids host only.
    A batch student is LOCKED to their grade/board. `assign` opens a teacher assignment (a fixed test
    loads its frozen pack); `print=1` jumps straight to the printable sheet."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host not in KIDS_HOSTS:
        return RedirectResponse("/exam-prep", status_code=302)
    # a batch student's grade + board are fixed (they can practise any subject, but only at their class)
    locked = bool(getattr(student, "grade", None))
    if locked:
        board, cls = (student.board or "CBSE"), student.grade
    assign_id, assign_pack = 0, None
    if assign:
        a = db.query(Assignment).filter_by(id=int(assign), active=True).first()
        # a student sees their teacher's assignment; a TEACHER can PREVIEW their own (owner) assignment.
        if a and (a.teacher_id == getattr(student, "teacher_id", None) or a.teacher_id == student.id):
            assign_id = a.id
            if a.kind == "kidstest" and isinstance(a.pack, dict):   # fixed test → the frozen sheet
                assign_pack = a.pack.get("items") or None
                subject = a.pack.get("subject") or subject
                board = a.pack.get("board") or board
                cls = a.pack.get("cls") or cls
                chapter = a.pack.get("chapter") or chapter
    return templates.TemplateResponse(request, "kids_worksheet.html", {
        "student": student, "board": board, "cls": cls, "subject": subject, "chapter": chapter,
        "n": max(3, min(int(n), 15)), "locked": locked,
        "assign_id": assign_id, "assign_pack": assign_pack, "auto_print": bool(print),
        "preview": bool(preview)})


@app.get("/api/kids/curriculum")
def kids_curriculum(request: Request, board: str = "CBSE", cls: int = 3, db: Session = Depends(get_db)):
    """Subjects + chapters available for a board+class (drives the picker)."""
    try:
        return JSONResponse({"ok": True, "board": board, "class": cls, "subjects": kidsws.picker(board, int(cls))})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:120]}, status_code=500)


@app.get("/api/kids/worksheet")
def kids_worksheet_api(request: Request, board: str = "CBSE", cls: int = 3, subject: str = "Mathematics",
                       chapter: str = "", n: int = 8, db: Session = Depends(get_db)):
    """An adaptive worksheet: items near the student's target difficulty, enriched with hints + distractors."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    try:
        data = kidsws.serve(db, student, board, int(cls), subject, chapter.strip() or None, n=max(3, min(int(n), 15)))
        return JSONResponse({"ok": True, **data})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:160]}, status_code=500)


@app.post("/api/kids/worksheet/complete")
async def kids_worksheet_complete(request: Request, db: Session = Depends(get_db)):
    """Record a finished worksheet → update BKT mastery + Elo + misconceptions (+ ConceptStat)."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        body = {}
    results = body.get("results", []) or []
    subject = str(body.get("subject", ""))[:40]
    # a fixed-test (injected pack) has no engine skill string — synthesise one so mastery still records.
    skill = str(body.get("skill", ""))[:160] or f"{student.board or 'CBSE'}/{student.grade or 3}/{subject or 'Worksheet'}/all"
    res = kidsws.complete(db, student, skill, results, subject=subject)
    # record the teacher assignment completion (who did it + score + weak topics)
    aid = body.get("assignment_id")
    if aid and getattr(student, "teacher_id", None):
        try:
            a = db.query(Assignment).filter_by(id=int(aid), teacher_id=student.teacher_id).first()
        except (TypeError, ValueError):
            a = None
        if a:
            score = sum(1 for r in results if r.get("correct"))
            weak = sorted({str(r.get("concept")) for r in results
                           if not r.get("correct") and r.get("concept")})[:8]
            row = (db.query(AssignmentCompletion)
                   .filter_by(assignment_id=a.id, student_id=student.id).first())
            if not row:
                row = AssignmentCompletion(assignment_id=a.id, student_id=student.id)
                db.add(row)
            row.score, row.total, row.weak_topics = score, len(results), weak
            db.commit()
    return JSONResponse(res)


@app.post("/api/assess/complete")
async def assess_complete(request: Request, db: Session = Depends(get_db)):
    """Persist a finished assessment's per-topic diagnosis to the student's account
    (as LearningEvent rows, consent-gated). Session cookie authenticates — no token."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        body = {}
    subject = str(body.get("subject", ""))[:40]
    results = body.get("results", []) or []
    outcome_map = {"solid": "correct", "shaky": "partial", "weak": "wrong"}
    mastery_pts = {"solid": 1.0, "shaky": 0.5, "weak": 0.0}
    concepts_seen = []
    _cs_cache: dict = {}   # concept -> ConceptStat pending in this request (see note below)
    for r in results:
        if not isinstance(r, dict):
            continue
        topic = str(r.get("topic", ""))[:120]
        status = str(r.get("status", ""))
        log_learning_event(db, student, surface="web",
                           concept_id=topic[:80],
                           step_type="mcq", action="complete",
                           outcome=outcome_map.get(status, "na"))
        # Product progress (NOT the consent-gated loop above): running per-concept mastery.
        if topic and status in mastery_pts:
            concepts_seen.append(topic)
            # Reuse within THIS request: a test often repeats a concept (5 questions on one topic).
            # Re-querying wouldn't see the pending row, so we'd insert a duplicate and blow the
            # (student, subject, concept) unique constraint — which killed the whole save.
            cs = _cs_cache.get(topic)
            if cs is None:
                cs = db.query(ConceptStat).filter_by(
                    student_id=student.id, subject=subject, concept=topic).first()
                if not cs:
                    cs = ConceptStat(student_id=student.id, subject=subject, concept=topic,
                                     seen=0, correct=0.0)
                    db.add(cs)
                _cs_cache[topic] = cs
            cs.seen += 1
            cs.correct += mastery_pts[status]
            cs.last_at = now()
    # Save the test itself (score history → "N tests taken").
    if subject and concepts_seen:
        try:
            score = int(body.get("score", 0))
            total = int(body.get("graded", 0))
        except Exception:
            score, total = 0, 0
        # keep the full paper so the student can reopen this test later (cap the size)
        detail = body.get("detail") or []
        if isinstance(detail, list):
            # keep `conf` (sure|think|guess) + `chosen` so the report can build the RED BOX
            # (confidently-wrong) + calibration + misconception views. Both are small tokens.
            detail = [{"q": str(d.get("q", ""))[:4000], "a": str(d.get("a", ""))[:800],
                       "chosen": str(d.get("chosen", ""))[:800], "conf": str(d.get("conf", ""))[:8],
                       "explain": str(d.get("explain", ""))[:6000], "ok": d.get("ok"),
                       "type": str(d.get("type", ""))[:20]}
                      for d in detail[:20] if isinstance(d, dict)]
        else:
            detail = []
        db.add(TopicAttempt(student_id=student.id, subject=subject,
                            title=str(body.get("title", subject))[:120],
                            score=score, total=total, concepts=concepts_seen, detail=detail))
    _set_fact(db, student, "last_exam", subject)
    db.commit()
    return JSONResponse({"ok": True})


def _exam_key(qtext: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", qtext.lower()).strip("-")[:60]
    return "q:" + (slug or "exam")


@app.get("/api/assess/generate")
def assess_generate(request: Request, q: str = "", db: Session = Depends(get_db)):
    """Return a validated, cached (or freshly generated) adaptive pack for a free-text exam/topic.
    Cold start = generate → key-withheld verify → cache; warm requests are instant from the bank.
    Code owns the score; only questions whose key an independent solve reproduced are ever served."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not has_assessment_access(db, student):
        return JSONResponse({"ok": False, "error": "trial_over", "redirect": "/exam-prep/upgrade"}, status_code=402)
    qtext = (q or "").strip()[:80]
    if not qtext:
        return JSONResponse({"ok": False, "error": "no exam"}, status_code=400)
    key = _exam_key(qtext)
    WANT = 5
    items = (db.query(AssessmentItem).filter_by(exam_key=key, status="validated")
             .order_by(func.random()).limit(WANT).all())
    if len(items) < WANT and assess_gen.available():
        try:
            validated = assess_gen.generate_validated(qtext, want=8)
        except Exception as exc:
            print(f"[assess] generate failed: {exc}")
            validated = []
        for v in validated:
            db.add(AssessmentItem(exam_key=key, exam_title=qtext[:120],
                                  qtype=v.get("type", "mcq"), payload=v, model=assess_gen.GEN_MODEL_NOTE))
        if validated:
            db.commit()
        items = (db.query(AssessmentItem).filter_by(exam_key=key, status="validated")
                 .order_by(func.random()).limit(WANT).all())
    if len(items) < 3:
        return JSONResponse({"ok": False,
                             "error": "Couldn't prepare enough questions for that — try a more specific exam or topic."})
    cands = [it.payload for it in items]
    pack = assess_gen.build_pack(qtext, cands, topic_line={"en": qtext, "hi": qtext})
    return JSONResponse({"ok": True, "pack": pack})


@app.get("/exam-prep/quick", response_class=HTMLResponse)
def exam_prep_quick(request: Request, exam: str = "", q: str = "", db: Session = Depends(get_db)):
    """RETIRED — the 'earn days' 11-question challenge/competition is gone (per the 2026-07-23
    decision: one flat 14-day trial, no rewards workflow). This URL is kept alive because ad
    campaigns point at it; it now just forwards to the exam-picker signup (or the dashboard if
    already logged in), preserving any `?exam=` so the picker can pre-select it."""
    student = current_student(request, db)
    if student:
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    exam = exam.strip()
    dest = "/exam-prep" + (f"?exam={quote(exam)}" if exam else "")
    return RedirectResponse(dest, status_code=302)


COMP_PROMPT = {
    "neet":     "NEET UG — Biology, Physics and Chemistry — a MIX of easy, medium and hard questions",
    "jee":      "JEE Main — Physics, Chemistry and Mathematics — a MIX of easy, medium and hard questions",
    "class10":  "CBSE Class 10 — Science and Mathematics — a MIX of easy, medium and hard questions",
    "class12":  "CBSE Class 12 — Physics and Chemistry — a MIX of easy, medium and hard questions",
    "commerce": "Class 11-12 Commerce — Accountancy and Economics — a MIX of easy, medium and hard questions",
}


@app.post("/api/comp/validate")
async def comp_validate(request: Request, db: Session = Depends(get_db)):
    """Fast LLM gate: is this a genuine, testable topic? Runs BEFORE the slow generation so the
    student gets instant feedback. Returns {ok, valid, topic (normalized), message (fix-it hint)}."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    topic = (body.get("topic") or "").strip()[:80]
    if len(topic) < 2:
        return JSONResponse({"ok": True, "valid": False, "message": "Type an exam or subject topic to test on."})
    if not assess_gen.available():
        return JSONResponse({"ok": True, "valid": True, "topic": topic})
    try:
        res = assess_gen.validate_topic(topic)
    except Exception as exc:
        print(f"[comp] validate failed: {exc}")
        res = {"valid": True, "topic": topic, "message": ""}
    return JSONResponse({"ok": True, **res})


@app.post("/api/comp/start")
async def comp_start(request: Request, db: Session = Depends(get_db)):
    """Start the 11-question competition: load/generate a validated bank, serve a KEYLESS set,
    stash the answers server-side (CompSession). Anonymous — no login yet."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    exam = (body.get("exam") or "").strip()
    qtext = (body.get("q") or "").strip()[:80]
    if qtext:
        key = "comp:q:" + _exam_key(qtext)[2:]
        title = qtext + " — a mix of easy, medium and hard questions"
    else:
        key = "comp:" + (exam if exam in COMP_PROMPT else "general")
        title = COMP_PROMPT.get(exam, "General aptitude and reasoning for competitive exams — a mix of easy, medium and hard questions")
    def _bank_count():
        return db.query(AssessmentItem).filter_by(exam_key=key, status="validated").count()
    # Build the bank in BATCHES of ~8 (one LLM call for ~17 bilingual Qs overflows the token budget
    # and returns invalid JSON). A few batches accumulate enough validated items, then it's cached.
    tries = 0
    while _bank_count() < COMP_N + 4 and assess_gen.available() and tries < 3:
        tries += 1
        try:
            validated = assess_gen.generate_validated(title, want=8)
        except Exception as exc:
            print(f"[comp] gen failed: {exc}")
            validated = []
        for v in validated:
            db.add(AssessmentItem(exam_key=key, exam_title=title[:120],
                                  qtype=v.get("type", "mcq"), payload=v, model=assess_gen.GEN_MODEL_NOTE))
        if validated:
            db.commit()
        else:
            break
    items = (db.query(AssessmentItem).filter_by(exam_key=key, status="validated")
             .order_by(func.random()).limit(COMP_N).all())
    if len(items) < 6:
        return JSONResponse({"ok": False, "error": "Couldn't prepare the challenge — please try another exam."})
    qs = [it.payload for it in items]
    comp_id = secrets.token_urlsafe(24)
    # opportunistic cleanup of stale competition sessions
    db.query(CompSession).filter(CompSession.created_at < datetime.utcnow() - timedelta(hours=3)).delete()
    db.add(CompSession(comp_id=comp_id, exam=(qtext or exam)[:60], data={"qs": qs}))
    db.commit()
    client_qs = []
    for q in qs:
        cq = {"type": q.get("type", "mcq"), "topic": q.get("topic", {})}
        for lang in ("en", "hi"):
            v = q.get(lang, {})
            cq[lang] = ({"q": v.get("q", ""), "opts": v.get("opts", [])}
                        if q.get("type") == "mcq" else {"q": v.get("q", "")})
        client_qs.append(cq)
    return JSONResponse({"ok": True, "comp_id": comp_id, "seconds": COMP_SECONDS, "n": len(qs), "questions": client_qs})


@app.post("/api/comp/submit")
async def comp_submit(request: Request, db: Session = Depends(get_db)):
    """Score the competition SERVER-SIDE against the stashed keys, return score + earned months +
    a signed earn-token (carried to registration to claim the free days) + the answer review."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    comp_id = (body.get("comp_id") or "").strip()
    answers = body.get("answers") or []
    cs = db.query(CompSession).filter_by(comp_id=comp_id).first()
    if not cs:
        return JSONResponse({"ok": False, "error": "This challenge expired — please start again."}, status_code=400)
    qs = (cs.data or {}).get("qs", [])
    score = 0
    review = []
    for i, q in enumerate(qs):
        a = answers[i] if i < len(answers) else None
        if q.get("type") == "mcq":
            correct = q.get("correct")
            ok = isinstance(a, int) and a == correct
        else:
            correct = bool(q.get("answer"))
            ok = isinstance(a, bool) and a == correct
        if ok:
            score += 1
        rv = {"type": q.get("type", "mcq"), "correct": correct, "your": a, "ok": ok,
              "en": {"explain": q.get("en", {}).get("explain", "")},
              "hi": {"explain": q.get("hi", {}).get("explain", "")}}
        if q.get("type") == "mcq":
            rv["en"]["opts"] = q.get("en", {}).get("opts", [])
            rv["hi"]["opts"] = q.get("hi", {}).get("opts", [])
        review.append(rv)
    total = len(qs)

    db.delete(cs)
    db.commit()
    return JSONResponse({"ok": True, "score": score, "total": total,
                         "review": review})


@app.post("/api/auth/google")
async def api_auth_google(request: Request, db: Session = Depends(get_db)):
    """Register/sign-in with a Google One Tap credential — a VERIFIED email, NO magic link.
    Verifies the ID token with Google, then creates + logs in the student directly."""
    if not settings.GOOGLE_CLIENT_ID:
        return JSONResponse({"ok": False, "error": "google sign-in not configured"}, status_code=503)
    try:
        body = await request.json()
    except Exception:
        body = {}
    cred = (body.get("credential") or "").strip()
    exam = (body.get("exam") or "").strip()
    qtext = (body.get("q") or "").strip()[:80]
    earn = str(body.get("earn") or "").strip()
    if not cred:
        return JSONResponse({"ok": False, "error": "no credential"}, status_code=400)
    import json as _json, urllib.request, urllib.parse
    try:
        vurl = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": cred})
        with urllib.request.urlopen(vurl, timeout=10) as resp:
            tok = _json.loads(resp.read().decode())
    except Exception as exc:
        print(f"[google-auth] verify failed: {exc}")
        return JSONResponse({"ok": False, "error": "verify failed"}, status_code=400)
    if tok.get("aud") != settings.GOOGLE_CLIENT_ID or str(tok.get("email_verified")).lower() != "true":
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=400)
    email = (tok.get("email") or "").lower().strip()
    if "@" not in email:
        return JSONResponse({"ok": False, "error": "no email"}, status_code=400)
    existed = db.query(Student).filter_by(email=email).first() is not None
    student = get_or_create_student(db, email)
    nm = (tok.get("name") or tok.get("given_name") or "")[:120]
    if nm and not student.name:
        student.name = nm
    label = ("q:" + qtext) if qtext else (exam if exam in EXAM_SUBJECT else EXAMS[0]["id"])
    _set_fact(db, student, "exam", label)
    _start_trial(db, student)          # everyone gets the same free trial
    _seed_topic(db, student, exam if exam in EXAM_SUBJECT else "", qtext)   # subject → first "my topic"
    db.commit()
    if not existed:
        total = db.query(Student).count()
        notify.notify_admin(f"🎯 New student (Google · exam-prep) — {student.email} · {label} · {total} learners total")
    request.session["sid"] = student.id
    # New student → goal pick first (new=1 rides through so the Ads conversion still fires on
    # the dashboard); returning student → straight home.
    return JSONResponse({"ok": True, "redirect": "/exam-prep/onboarding?new=1" if not existed
                         else "/exam-prep/dashboard"})


def _prep_stats(db, student) -> dict:
    """Everything the Today screen shows — all DERIVED FROM REAL ANSWERS, nothing invented.
    (Deliberately no XP / cohort rank: we don't track them, and fake numbers on a student's
    progress screen are worse than no numbers.)"""
    stats = [s for s in db.query(ConceptStat).filter_by(student_id=student.id).all() if s.seen]
    attempts = (db.query(TopicAttempt).filter_by(student_id=student.id)
                .order_by(TopicAttempt.taken_at.desc()).limit(200).all())

    def m(s):
        return s.correct / s.seen

    mastery = round(100 * sum(s.correct for s in stats) / sum(s.seen for s in stats)) if stats else 0
    ranked = sorted(stats, key=m)
    weakest = ranked[:3]                       # drives Smart Practice targeting
    # Focus areas must only list genuinely weak topics — showing a 100%-mastery topic under
    # "lowest mastery = biggest score gains" is just wrong.
    focus = [s for s in ranked if m(s) < 0.75][:3]
    strongest = ranked[-1] if ranked else None

    # this week
    wk = datetime.utcnow() - timedelta(days=7)
    recent = [a for a in attempts if a.taken_at and a.taken_at >= wk]
    q_week = sum(a.total or 0 for a in recent)
    acc_week = round(100 * sum(a.score or 0 for a in recent) / q_week) if q_week else 0
    chapters_week = len({c for a in recent for c in (a.concepts or [])})

    # streak: consecutive days (ending today or yesterday) with at least one test
    days = {a.taken_at.date() for a in attempts if a.taken_at}
    streak, cur = 0, date.today()
    if cur not in days and (cur - timedelta(days=1)) in days:
        cur = cur - timedelta(days=1)
    while cur in days:
        streak += 1
        cur -= timedelta(days=1)

    # revision due = practised before, gone cold (>=5 days), not yet solid
    cold = datetime.utcnow() - timedelta(days=5)
    due = [s for s in stats if s.last_at and s.last_at < cold and m(s) < 0.75]

    # last 7 sessions, oldest→newest, as % (for the sparkline)
    graded = [a for a in attempts if a.total]
    trend = [round(100 * a.score / a.total) for a in reversed(graded[:7])]

    # goal identity — the goal the student CHOSE in onboarding, falling back to inference
    topics = _student_topics(db, student)
    goal_id = _student_goal(db, student, topics)
    if goal_id:
        goal = examgen.GOALS[goal_id]["label"]
    else:
        hay = " ".join(t.title.lower() for t in topics)
        goal = "Board exams" if "class" in hay else "Exam prep"

    return {
        "mastery": mastery, "weakest": weakest, "focus": focus, "strongest": strongest,
        "q_week": q_week, "acc_week": acc_week, "chapters_week": chapters_week,
        "streak": streak, "due": due, "trend": trend, "goal": goal, "goal_id": goal_id,
        "tests": len(attempts), "has_data": bool(stats),
    }


@app.get("/exam-prep/smart")
def exam_prep_smart(request: Request, focus_subj: str = "", db: Session = Depends(get_db)):
    """Smart Practice: build today's set from the student's ACTUAL weak spots — weakest concepts
    first, then anything gone cold. Falls back to their first topic for a brand-new student.
    `focus_subj` (from the Today intake card) biases the set toward that subject."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    # Kids: Smart Practice = a fresh adaptive WORKSHEET built on the child's WEAKEST topic (10 Q).
    # Pick the lowest-mastery concept they've actually attempted; the worksheet engine then targets
    # difficulty via BKT/Elo. Brand-new kids (no data) get the picker.
    if (request.headers.get("host") or "").split(":")[0].lower() in KIDS_HOSTS:
        kstats = [s for s in db.query(ConceptStat).filter_by(student_id=student.id).all() if s.seen]
        if kstats:
            w = min(kstats, key=lambda s: s.correct / s.seen)
            return RedirectResponse(
                f"/exam-prep/worksheet?subject={quote(w.subject)}&chapter={quote(w.concept)}&n=10",
                status_code=302)
        return RedirectResponse("/exam-prep/worksheet?n=10", status_code=302)
    st = _prep_stats(db, student)
    picks = (st["weakest"] or []) + [d for d in st["due"] if d not in (st["weakest"] or [])]
    # Just-in-time focus: if the student declared a subject on Today, float its weak concepts first.
    fsubj = focus_subj.strip() if focus_subj.strip() in examgen.RAG_SUBJECTS else ""
    if fsubj:
        picks = [p for p in picks if p.subject == fsubj] + [p for p in picks if p.subject != fsubj]
    # Default to the goal's own first subject — a NEET student must never fall back to JEE Physics.
    goal = examgen.GOALS.get(st["goal_id"] or examgen.DEFAULT_GOAL, examgen.GOALS[examgen.DEFAULT_GOAL])
    sel, subject = [], (fsubj or goal["subjects"][0])
    for s in picks[:3]:
        ch = _chapter_for_concept(s.subject, s.concept)
        if ch:
            sel.append(f"{ch}::{s.concept}")
            subject = s.subject
    if not sel and fsubj:                          # declared a focus subject not yet practised → seed it
        chs = examgen.chapters_for_ui(fsubj)
        if chs:
            subject = fsubj
            c0 = chs[0].get("concepts") or []
            sel = [f"{chs[0]['chapter']}::{c0[0]}" if c0 else f"{chs[0]['chapter']}::"]
    if not sel:                                   # nothing practised yet → start with a topic
        topics = _student_topics(db, student)
        for t in topics:
            sid = examgen.match_subject(t.title, t.topic_key)
            if sid:
                chs = examgen.chapters_for_ui(sid)
                if chs:
                    subject = sid
                    concepts0 = chs[0].get("concepts") or []
                    # a chapter may have no tagged subtopics (e.g. Class 10 Science) → whole-chapter sel
                    sel = [f"{chs[0]['chapter']}::{concepts0[0]}" if concepts0 else f"{chs[0]['chapter']}::"]
                    break
    if not sel:
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    diff = examgen.difficulty_for(subject, st["mastery"] / 100)   # on the exam's own band (NEET 2-3, JEE 3-4)
    # A brand-new student's FIRST set is short (5 Q) — a fast, winnable quick-win beats a long
    # slog for activation. Once they have data, Smart Practice is the full 10.
    n = 5 if not st.get("has_data") else 10
    return RedirectResponse(
        f"/exam-prep/test?src=examgen&subject={quote(subject)}&sel={quote('|'.join(sel))}"
        f"&diff={quote(diff)}&n={n}&title={quote('Smart Practice')}", status_code=302)


@app.get("/exam-prep/dashboard", response_class=HTMLResponse)
def exam_prep_dashboard(request: Request, new: str = "", added: str = "", db: Session = Depends(get_db)):
    """The student HOME — the "Today" screen: goal, real mastery, today's chosen set, the practice
    modes, focus areas and this week's activity. Every number is derived from actual answers."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    topics = _student_topics(db, student)
    st = _prep_stats(db, student)
    hour = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour     # IST
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    # Ads "free signup" conversion — fires ONCE for a genuinely-new account landing here.
    ads_id = settings.ADS_CONVERSION_ID if (new == "1" and settings.STUDENT_SIGNUP_CONV_LABEL and settings.ADS_CONVERSION_ID) else ""
    linked = _linked_teacher(db, student)      # B2B2C: student belongs to an institute?
    institute = ((linked.institute if linked else "") or (linked.name if linked else "")) if linked else ""
    # Just-in-time intake: the focus the student declared for today (+ where 'Practise it' aims).
    ff = db.query(LearnerFact).filter_by(student_id=student.id, key="focus").first()
    focus = ff.value if ff else ""
    focus_href = _focus_practice_href(list(examgen.RAG_SUBJECTS), focus) if focus else ""
    return templates.TemplateResponse(request, "exam_prep_dashboard.html", {
        "student": student,
        "topics": topics,
        "days_left": _days_left(student),
        "st": st, "greeting": greeting,
        "paid": (student.assess_status or "none") == "active",
        "max_topics": MAX_TOPICS,
        "at_max": len(topics) >= MAX_TOPICS,
        "price": settings.ASSESS_PRICE_INR,
        "added": added,
        "ads_id": ads_id,
        "ads_label": settings.STUDENT_SIGNUP_CONV_LABEL,
        "linked": bool(linked), "institute": institute,   # linked → subjects are teacher-controlled
        "assignments": _student_assignments(db, student),  # 📋 assigned by your teacher
        "focus": focus, "focus_href": focus_href,          # just-in-time intake (Today's declared focus)
        "kids": (request.headers.get("host") or "").split(":")[0].lower() in KIDS_HOSTS,  # kids skin + worksheet tile
    })


@app.post("/exam-prep/topics/add")
def exam_prep_topic_add(request: Request, topic: str = Form(""), db: Session = Depends(get_db)):
    """Add a topic to the student's plan (curated exam or free-text), capped at MAX_TOPICS."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    if student.teacher_id:                     # linked student — the institute controls the syllabus
        return RedirectResponse("/exam-prep/dashboard?locked=1", status_code=302)
    topic = (topic or "").strip()[:80]
    if len(topic) < 2:
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    cur = next((e for e in EXAMS if e["id"].lower() == topic.lower()
                or e["title"].lower() == topic.lower()), None)
    if cur:
        reason = _add_topic(db, student, cur["id"], cur["title"], "exam")
    else:
        tk, title, kind = _topic_from("", topic)
        reason = _add_topic(db, student, tk, title, kind)
    db.commit()
    return RedirectResponse(f"/exam-prep/dashboard?added={reason}", status_code=302)


@app.post("/exam-prep/focus")
def exam_prep_focus(request: Request, focus: str = Form(""), db: Session = Depends(get_db)):
    """Just-in-time intake ('let AI ask you'): the student declares what they want to nail RIGHT NOW
    — a signal past performance can't give (an upcoming test, a topic that feels shaky). Stored as a
    LearnerFact and surfaced on Today; 'Practise it' aims at the best-matching subject."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    focus = (focus or "").strip()[:120]
    if focus.lower() in ("", "clear"):
        f = db.query(LearnerFact).filter_by(student_id=student.id, key="focus").first()
        if f:
            db.delete(f); db.commit()
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    _set_fact(db, student, "focus", focus)
    db.commit()
    return RedirectResponse("/exam-prep/dashboard", status_code=302)


def _focus_practice_href(subject_ids: list, focus: str) -> str:
    """Aim 'Practise it' at the subject whose name best matches the student's declared focus, else
    generic Smart Practice. Cheap keyword match — no LLM in the Today hot path."""
    f = (focus or "").lower()
    for sid in subject_ids:
        label = examgen.RAG_SUBJECTS.get(sid, {}).get("label", sid).lower()
        if any(w in f for w in label.replace("-", " ").split() if len(w) > 3):
            return f"/exam-prep/smart?focus_subj={quote(sid)}"
    try:
        sid = examgen.match_subject(focus)
        if sid:
            return f"/exam-prep/smart?focus_subj={quote(sid)}"
    except Exception:
        pass
    return "/exam-prep/smart"


def _log_examgen_request(db, student, title: str) -> bool:
    """Log a 'set up the RAG paper for this subject' request (de-duped per email+topic). True if new."""
    label = f"EXAM-PREP RAG paper: {title}"[:200]
    if db.query(CourseRequest).filter_by(email=student.email, topic=label).first():
        return False
    db.add(CourseRequest(topic=label, email=student.email, phone=student.phone or "", source="web"))
    db.commit()
    try:
        notify.notify_admin(f"📝 RAG test-paper request — {student.email} · {title[:60]}")
    except Exception:
        pass
    return True


@app.get("/exam-prep/subject/{topic_id}", response_class=HTMLResponse)
def exam_prep_subject(request: Request, topic_id: int, db: Session = Depends(get_db)):
    """Subject detail: pick one/more subtopics → build a custom RAG paper (if the subject is covered),
    else a 'we're setting it up' message + a logged request (+ a quick-test fallback)."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    if not has_assessment_access(db, student):
        return RedirectResponse("/exam-prep/upgrade", status_code=302)
    topic = db.query(StudentTopic).filter_by(id=topic_id, student_id=student.id).first()
    if not topic:
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    sid = examgen.match_subject(topic.title, topic.topic_key) if examgen.available() else None
    # Fallback: a topic seeded straight from the landing picker is a bare EXAM id ("upsc", "jee",
    # "class12", "commerce", "neet") whose title ("UPSC", "JEE") match_subject can't resolve to a
    # single RAG subject. Map it to the exam's PRIMARY subject so it opens the chapter picker instead
    # of dead-ending on "coming soon". (Multi-subject exams still get per-subject topics at onboarding.)
    if not sid and examgen.available() and topic.topic_key in EXAM_SUBJECT:
        sid = EXAM_SUBJECT[topic.topic_key]
    if sid:
        chapters = examgen.chapters_for_ui(sid)
        if chapters:
            # progress: per-concept mastery (0..1), test count, and the weakest concept to suggest
            stats = db.query(ConceptStat).filter_by(student_id=student.id, subject=sid).all()
            mastery = {s.concept: round(s.correct / s.seen, 2) for s in stats if s.seen}
            attempts = db.query(TopicAttempt).filter_by(student_id=student.id, subject=sid).count()
            practised = [s for s in stats if s.seen]
            weakest = min(practised, key=lambda s: s.correct / s.seen, default=None)
            suggest = weakest.concept if (weakest and weakest.correct / weakest.seen < 0.7) else None
            return templates.TemplateResponse(request, "exam_prep_subject.html", {
                "student": student, "topic": topic, "available": True,
                "subject_id": sid, "subject_label": examgen.RAG_SUBJECTS[sid]["label"],
                "chapters": chapters, "mastery": mastery, "attempts": attempts, "suggest": suggest,
                "ladder": examgen.difficulty_ladder(sid),   # NEET 2/2-3/3 vs JEE 3/3-4/4
            })
    # not covered by the RAG yet → coming soon + log the request (once)
    just_requested = _log_examgen_request(db, student, topic.title)
    quick = (f"/exam-prep/test?exam={quote(topic.topic_key)}" if topic.kind == "exam"
             else f"/exam-prep/test?q={quote(topic.title)}")
    return templates.TemplateResponse(request, "exam_prep_subject.html", {
        "student": student, "topic": topic, "available": False,
        "just_requested": just_requested, "quick_href": quick,
    })


def _chapter_for_concept(subject_id: str, concept: str) -> str | None:
    """Find which chapter a concept belongs to (so a suggestion can link straight to a test)."""
    for c in examgen.get_chapters(subject_id):
        if concept in (c.get("concepts") or []):
            return c.get("chapter")
    return None


@app.get("/exam-prep/report", response_class=HTMLResponse)
def exam_prep_report(request: Request, db: Session = Depends(get_db)):
    """Reports & Improvement: every test saved, per-concept strengths/weak spots, what to practise
    next, and the difficulty level Acharya recommends from the student's actual results."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    attempts = (db.query(TopicAttempt).filter_by(student_id=student.id)
                .order_by(TopicAttempt.taken_at.desc()).limit(50).all())
    stats = [s for s in db.query(ConceptStat).filter_by(student_id=student.id).all() if s.seen]

    def mastery(s):
        return s.correct / s.seen

    strong = sorted([s for s in stats if mastery(s) >= 0.75], key=mastery, reverse=True)
    shaky = sorted([s for s in stats if 0.5 <= mastery(s) < 0.75], key=mastery)
    weak = sorted([s for s in stats if mastery(s) < 0.5], key=mastery)
    graded = [a for a in attempts if a.total]
    avg = round(100 * sum(a.score for a in graded) / sum(a.total for a in graded)) if graded else 0
    overall = (sum(s.correct for s in stats) / sum(s.seen for s in stats)) if stats else 0
    # difficulty Acharya recommends next, from real performance. The TIER (easy/mix/hard) is what
    # we show; the actual value is resolved per exam band (NEET 2-3 vs JEE 3-4) at link time.
    tier, level_label, level_why = (
        ("hard", "Hard", "you're consistently strong — time for harder problems")
        if overall >= 0.75 else
        (("mix", "Mix (medium–hard)", "you're solid on most topics — a mix keeps you stretching")
         if overall >= 0.5 else
         ("easy", "Medium", "let's lock the basics first, then push the difficulty")))
    # headline difficulty value, on the student's goal band (for display consistency)
    goal_subj = examgen.GOALS.get(_student_goal(db, student), {}).get("subjects", [None])[0]
    level = examgen.difficulty_ladder(goal_subj)[tier] if goal_subj else {"easy": "3", "mix": "3-4", "hard": "4"}[tier]
    # what to practise next (weakest first), each linking to a ready-made test at that tier — on
    # ITS OWN subject's band, so a NEET Biology suggestion asks for NEET difficulty, not JEE.
    kids = (request.headers.get("host") or "").split(":")[0].lower() in KIDS_HOSTS
    picks = (weak + shaky)[:4]
    suggestions = []
    for s in picks:
        if kids:
            # Kids: practise = a FRESH adaptive worksheet on this weak topic (subject + concept as the
            # chapter filter; the engine falls back to mixed if the concept isn't a chapter name).
            href = (f"/exam-prep/worksheet?subject={quote(s.subject)}&chapter={quote(s.concept)}&n=8")
        else:
            ch = _chapter_for_concept(s.subject, s.concept)
            href = ""
            if ch:
                sel = f"{ch}::{s.concept}"
                s_diff = examgen.difficulty_ladder(s.subject)[tier]
                href = (f"/exam-prep/test?src=examgen&subject={quote(s.subject)}&sel={quote(sel)}"
                        f"&diff={quote(s_diff)}&n=5&title={quote(s.concept)}")
        tutor_href = (f"/exam-prep/tutor?subject={quote(s.subject)}&concept={quote(s.concept)}")
        # teach-back (mirror test) — seniors only (kids subjects aren't RAG_SUBJECTS-keyed).
        teachback_href = "" if kids else (f"/exam-prep/teachback?subject={quote(s.subject)}&concept={quote(s.concept)}")
        suggestions.append({"concept": s.concept, "pct": round(100 * mastery(s)),
                            "seen": s.seen, "href": href, "tutor_href": tutor_href,
                            "teachback_href": teachback_href,
                            "prac_label": ("📝 Practice worksheet" if kids else "Practise →")})
    trend = [round(100 * a.score / a.total) for a in reversed(graded[:6]) if a.total]
    # ---- RED BOX + calibration: the "SELF" confidence signals from each attempt's detail ----
    # RED BOX = questions the student was SURE about and got WRONG (a confident misconception hides
    # until it's tested → the highest-value thing to fix). Calibration = how often "Sure" was right.
    redbox, sure_n, sure_ok, guess_n, guess_ok = [], 0, 0, 0, 0
    for a in attempts:
        for d in (a.detail or []):
            if not isinstance(d, dict):
                continue
            conf, ok = (d.get("conf") or ""), d.get("ok")
            if ok is None:
                continue
            if conf == "sure":
                sure_n += 1; sure_ok += 1 if ok else 0
                if ok is False and len(redbox) < 8:
                    redbox.append({"q": str(d.get("q", ""))[:180],
                                   "title": a.title or a.subject, "href": f"/exam-prep/attempt/{a.id}"})
            elif conf == "guess":
                guess_n += 1; guess_ok += 1 if ok else 0
    calib = None
    if sure_n >= 3:
        acc = round(100 * sure_ok / sure_n)
        if acc >= 85:
            calib = {"tone": "good", "text": f"Well-calibrated — when you said “Sure”, you were right {acc}% of the time."}
        elif acc >= 60:
            calib = {"tone": "warn", "text": f"Slightly overconfident — you were “Sure” on {sure_n} answers but right only {acc}% of the time."}
        else:
            calib = {"tone": "bad", "text": f"Overconfident — being “Sure” meant right just {acc}% of the time. Start with the red box below."}
    calib_note = None
    if guess_n >= 3 and (guess_ok / guess_n) >= 0.6:
        calib_note = f"You underrate yourself — {round(100 * guess_ok / guess_n)}% of your “Guessing” answers were actually right."
    # Kids: the recurring diagnostic slips (forgot to carry, added instead of multiplied…) aggregated
    # across every worksheet — the misconception map. Seniors' pool has no tagged distractors yet.
    kid_mis = kidsws.student_misconceptions(db, student) if kids else []
    # Forge it — "practise until you can't get it wrong": concepts truly locked in (high mastery + evidence).
    mastered = [{"c": s.concept, "p": round(100 * mastery(s))}
                for s in sorted(stats, key=mastery, reverse=True) if mastery(s) >= 0.85 and s.seen >= 5][:8]
    # Live it — the ONE next action (do it in 48h). The RED BOX #1 if any, else the weakest topic.
    one_action = None
    if redbox:
        one_action = {"label": redbox[0]["q"], "sub": "You were sure — and wrong. Clear this blind spot first.",
                      "href": redbox[0]["href"], "cta": "Review it"}
    elif suggestions:
        s0 = suggestions[0]
        one_action = {"label": s0["concept"], "sub": f"Your weakest topic ({s0['pct']}%). One focused session moves the needle most.",
                      "href": s0.get("tutor_href") or s0.get("href") or "", "cta": "Start now"}
    # Seniors: enough wrong answers on record to run the LLM misconception diagnosis on demand.
    wrong_ct = sum(1 for a in attempts for d in (a.detail or [])
                   if isinstance(d, dict) and d.get("ok") is False and d.get("q"))
    can_diagnose = (not kids) and tutor.available() and wrong_ct >= 2
    return templates.TemplateResponse(request, "exam_prep_report.html", {
        "student": student, "attempts": attempts, "tests": len(attempts), "avg": avg,
        "strong": [{"c": s.concept, "p": round(100 * mastery(s))} for s in strong[:8]],
        "shaky": [{"c": s.concept, "p": round(100 * mastery(s))} for s in shaky[:8]],
        "weak": [{"c": s.concept, "p": round(100 * mastery(s))} for s in weak[:8]],
        "suggestions": suggestions, "level": level, "level_label": level_label, "level_why": level_why,
        "trend": trend, "overall": round(100 * overall),
        "redbox": redbox, "calib": calib, "calib_note": calib_note, "kid_mis": kid_mis,
        "mastered": mastered, "one_action": one_action, "can_diagnose": can_diagnose,
    })


@app.get("/exam-prep/attempt/{attempt_id}", response_class=HTMLResponse)
def exam_prep_attempt(request: Request, attempt_id: int, db: Session = Depends(get_db)):
    """Reopen a past test exactly as it was sat — questions, correct answers and solutions."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    a = db.query(TopicAttempt).filter_by(id=attempt_id, student_id=student.id).first()
    if not a:
        return RedirectResponse("/exam-prep/report", status_code=302)
    return templates.TemplateResponse(request, "exam_prep_attempt.html", {"student": student, "a": a})


# ---------------------------------------------------------------------------
# WEAK-TOPIC TUTOR — a dedicated Acharya tutor per weak concept, anchored to a
# real exam question of the type the student got wrong. Teaches from the basics,
# step by step, with the question's diagram, via gpt-4o-mini (app/tutor.py).
# ---------------------------------------------------------------------------
def _resolve_chapter(subject_id: str, concept: str) -> str | None:
    """Best-effort: map a weak-topic label to a real chapter so we can pull an anchor question.
    Handles concept-under-chapter, concept-IS-a-chapter, and loose/substring matches (a stored
    label like 'Units' should still resolve to 'Units, Dimensions & Measurement')."""
    chapters = examgen.get_chapters(subject_id)
    cl = (concept or "").strip().lower()
    if not cl:
        return None
    for c in chapters:                                   # exact concept under a chapter
        if concept in (c.get("concepts") or []):
            return c.get("chapter")
    for c in chapters:                                   # concept IS a chapter (exact)
        if (c.get("chapter") or "").strip().lower() == cl:
            return c.get("chapter")
    for c in chapters:                                   # loose: substring on chapter or a concept
        name = (c.get("chapter") or "").lower()
        if cl in name or name in cl:
            return c.get("chapter")
        for x in (c.get("concepts") or []):
            xl = (x or "").lower()
            if xl and (cl in xl or xl in cl):
                return c.get("chapter")
    return None


def _tutor_anchor(subject_id: str, concept: str, difficulty: str):
    """One representative question for a concept (stem/options/correct/solution/figure), pulled
    INSTANTLY from the pool. Returns a dict the tutor + template can use, or None if none exists."""
    ch = _resolve_chapter(subject_id, concept)
    if not ch:
        return None
    # The pool stores questions at specific difficulty bands; the student's mastery-based difficulty
    # may not match what exists for this concept. Try the requested one, then the subject's whole
    # ladder (mix/hard/easy), for the exact concept first, then any question in the chapter.
    ladder = examgen.difficulty_ladder(subject_id)
    diffs, seen = [], set()
    for d in [difficulty, ladder.get("mix"), ladder.get("hard"), ladder.get("easy")]:
        if d and d not in seen:
            seen.add(d); diffs.append(d)
    for co in ([concept] if concept else []) + [None]:
        for d in diffs:
            qs, _ = examgen.fetch_pool(subject_id, ch, co, d, "MCQ_single", 1)
            if not qs:
                continue
            pq = examgen._to_pack_question(qs[0])
            if pq:
                en = pq.get("en", {})
                opts = en.get("opts", []) or []
                ci = pq.get("correct", 0)
                return {
                    "stem": en.get("q", ""), "options": opts, "correct_index": ci,
                    "correct_text": opts[ci] if 0 <= ci < len(opts) else "",
                    "solution": en.get("explain", ""), "figure": pq.get("figure"), "chapter": ch,
                }
    return None


@app.get("/exam-prep/tutor", response_class=HTMLResponse)
def exam_prep_tutor(request: Request, subject: str = "", concept: str = "", db: Session = Depends(get_db)):
    """The dedicated weak-topic tutor screen: an anchor question (with its diagram) + a chat where
    Acharya teaches that concept from the basics, step by step, revolving around the question."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    subject = (subject or "").strip()
    concept = (concept or "").strip()[:120]
    if subject not in examgen.RAG_SUBJECTS or not concept:
        return RedirectResponse("/exam-prep/report", status_code=302)
    cs = db.query(ConceptStat).filter_by(student_id=student.id, subject=subject, concept=concept).first()
    mastery_pct = round(100 * cs.correct / cs.seen) if (cs and cs.seen) else None
    diff = examgen.difficulty_for(subject, (mastery_pct or 0) / 100)   # this subject's own band
    anchor = _tutor_anchor(subject, concept, diff)
    subj_label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", subject)
    return templates.TemplateResponse(request, "tutor_console.html", {
        "student": student, "subject": subject, "subject_label": subj_label,
        "concept": concept, "mastery_pct": mastery_pct, "anchor": anchor,
        "tutor_available": tutor.available(),
    })


@app.post("/api/tutor/step")
async def api_tutor_step(request: Request, db: Session = Depends(get_db)):
    """One tutor turn. Body: {subject, concept, history:[{role,content}], anchor:{...}}.
    Returns {reply}. The anchor was server-provided at page load; we hand it to the LLM."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not tutor.available():
        return JSONResponse({"ok": False, "error": "tutor unavailable"}, status_code=503)
    try:
        body = await request.json()
    except Exception:
        body = {}
    subject = str(body.get("subject", ""))[:40]
    concept = str(body.get("concept", ""))[:120]
    clean = []
    for m in (body.get("history") or [])[-12:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content"):
            clean.append({"role": m["role"], "content": str(m["content"])[:2000]})
    anchor = body.get("anchor") if isinstance(body.get("anchor"), dict) else None
    cs = db.query(ConceptStat).filter_by(student_id=student.id, subject=subject, concept=concept).first()
    mastery_pct = round(100 * cs.correct / cs.seen) if (cs and cs.seen) else None
    subj_label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", subject)
    reply = tutor.exam_chat(clean, concept, subj_label, anchor, mastery_pct)
    if not reply:
        return JSONResponse({"ok": False, "error": "no reply"}, status_code=502)
    return JSONResponse({"ok": True, "reply": reply})


@app.get("/exam-prep/teachback", response_class=HTMLResponse)
def exam_prep_teachback(request: Request, subject: str = "", concept: str = "", db: Session = Depends(get_db)):
    """The 'teach it back' / mirror test: the student EXPLAINS a concept in their own words and
    Acharya grades the explanation against the reference — the deepest check of real understanding."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    subject = (subject or "").strip()
    concept = (concept or "").strip()[:120]
    if subject not in examgen.RAG_SUBJECTS or not concept:
        return RedirectResponse("/exam-prep/report", status_code=302)
    cs = db.query(ConceptStat).filter_by(student_id=student.id, subject=subject, concept=concept).first()
    mastery_pct = round(100 * cs.correct / cs.seen) if (cs and cs.seen) else None
    diff = examgen.difficulty_for(subject, (mastery_pct or 0) / 100)
    anchor = _tutor_anchor(subject, concept, diff)
    subj_label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", subject)
    return templates.TemplateResponse(request, "teachback.html", {
        "student": student, "subject": subject, "subject_label": subj_label,
        "concept": concept, "anchor": anchor, "tutor_available": tutor.available(),
    })


@app.post("/api/teachback/grade")
async def api_teachback_grade(request: Request, db: Session = Depends(get_db)):
    """Grade a teach-back. Body: {subject, concept, explanation, anchor:{...}}.
    Returns {score, correct[], gaps[], verdict}. Read-only — it doesn't change mastery."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not tutor.available():
        return JSONResponse({"ok": False, "error": "unavailable"}, status_code=503)
    try:
        body = await request.json()
    except Exception:
        body = {}
    concept = str(body.get("concept", ""))[:120]
    subject = str(body.get("subject", ""))[:40]
    explanation = str(body.get("explanation", "")).strip()[:3000]
    if len(explanation) < 10:
        return JSONResponse({"ok": False, "error": "too_short"}, status_code=400)
    anchor = body.get("anchor") if isinstance(body.get("anchor"), dict) else None
    subj_label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", subject)
    result = tutor.teachback_grade(concept, subj_label, anchor, explanation)
    if not result:
        return JSONResponse({"ok": False, "error": "grade_failed"}, status_code=502)
    return JSONResponse({"ok": True, **result})


@app.post("/api/misconception/diagnose")
async def api_misconception_diagnose(request: Request, db: Session = Depends(get_db)):
    """On-demand: run an LLM pass over the student's recent WRONG answers (question + what they chose
    + correct + solution, all persisted in TopicAttempt.detail) to name their recurring misconceptions.
    Seniors' version of the kids misconception map. Read-only; called from a report button."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not tutor.available():
        return JSONResponse({"ok": False, "error": "unavailable"}, status_code=503)
    attempts = (db.query(TopicAttempt).filter_by(student_id=student.id)
                .order_by(TopicAttempt.taken_at.desc()).limit(20).all())
    items, subj_label = [], ""
    for a in attempts:
        if not subj_label:
            subj_label = examgen.RAG_SUBJECTS.get(a.subject, {}).get("label", a.subject)
        for d in (a.detail or []):
            if isinstance(d, dict) and d.get("ok") is False and d.get("q"):
                items.append({"q": d.get("q", ""), "chosen": d.get("chosen", ""),
                              "correct": d.get("a", ""), "solution": d.get("explain", "")})
        if len(items) >= 12:
            break
    if len(items) < 2:
        return JSONResponse({"ok": False, "error": "not_enough"}, status_code=400)
    ms = tutor.diagnose_misconceptions(subj_label or "your exam", items)
    if not ms:
        return JSONResponse({"ok": False, "error": "diagnose_failed"}, status_code=502)
    return JSONResponse({"ok": True, "misconceptions": ms})


def _paper_goal_id(subject: str) -> str:
    """Map a MockPaper.subject to its goal/exam id (an examgen.GOALS key). New papers are tagged
    with the goal id directly (e.g. 'neet'); legacy papers carry a fine-grained subject
    ('jee-physics') that maps back via goal_of_subject."""
    subject = (subject or "").strip()
    if subject in examgen.GOALS:
        return subject
    return examgen.goal_of_subject(subject) or ""


@app.get("/exam-prep/papers", response_class=HTMLResponse)
def exam_prep_papers(request: Request, db: Session = Depends(get_db)):
    """The test series: shared, pre-generated full papers, FILTERED to the student's goal/exam so a
    NEET student never sees JEE papers (and vice-versa). Empty goal → honest 'coming soon' state."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    goal_id = _student_goal(db, student) or examgen.DEFAULT_GOAL
    goal = examgen.GOALS.get(goal_id, examgen.GOALS[examgen.DEFAULT_GOAL])
    ready = (db.query(MockPaper).filter_by(status="ready").order_by(MockPaper.code).all())
    papers = [p for p in ready if _paper_goal_id(p.subject) == goal_id]
    done = {}
    if papers:
        pids = {p.id for p in papers}
        for a in (db.query(PaperAttempt).filter_by(student_id=student.id)
                  .filter(PaperAttempt.submitted_at.isnot(None)).all()):
            if a.paper_id in pids:
                prev = done.get(a.paper_id)
                if not prev or a.score > prev.score:
                    done[a.paper_id] = a
    return templates.TemplateResponse(request, "exam_prep_papers.html", {
        "student": student, "papers": papers, "done": done, "goal": goal, "goal_id": goal_id,
        "kind": mockpaper.paper_kind(goal_id),
    })


@app.get("/exam-prep/paper/{paper_id}", response_class=HTMLResponse)
def exam_prep_paper_sit(request: Request, paper_id: int, db: Session = Depends(get_db)):
    """Sit a paper in exam mode. The correct answers and solutions are STRIPPED before the
    questions reach the browser — they only come back on the result page after submitting."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    paper = db.query(MockPaper).filter_by(id=paper_id, status="ready").first()
    if not paper:
        return RedirectResponse("/exam-prep/papers", status_code=302)
    safe = [{"n": q.get("n"), "section": q.get("section"), "qtype": q.get("qtype"),
             "marks": q.get("marks"), "neg": q.get("neg"),
             "stem": q.get("stem"), "options": q.get("options") or [],
             "figure": q.get("figure"), "chapter": q.get("chapter")}
            for q in (paper.questions or [])]
    att = PaperAttempt(student_id=student.id, paper_id=paper.id,
                       max_score=paper.max_marks, answers={})
    db.add(att)
    db.commit()
    import json as _json
    return templates.TemplateResponse(request, "exam_prep_paper.html", {
        "student": student, "paper": paper, "attempt": att,
        "questions_json": _json.dumps(safe, ensure_ascii=False),
        "sections": mockpaper.BLUEPRINT["sections"],
    })


@app.post("/api/paper/{paper_id}/submit")
async def api_paper_submit(request: Request, paper_id: int, db: Session = Depends(get_db)):
    """Score a sitting server-side against the JEE Advanced marking scheme."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    paper = db.query(MockPaper).filter_by(id=paper_id, status="ready").first()
    if not paper:
        return JSONResponse({"ok": False, "error": "no such paper"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        body = {}
    answers = body.get("answers") or {}
    att_id = body.get("attempt_id")
    res = mockpaper.score_attempt(paper.questions or [], answers)
    att = (db.query(PaperAttempt).filter_by(id=att_id, student_id=student.id).first()
           if att_id else None)
    if not att:
        att = PaperAttempt(student_id=student.id, paper_id=paper.id)
        db.add(att)
    att.answers = answers
    att.score = res["score"]
    att.max_score = paper.max_marks
    att.correct, att.wrong, att.skipped = res["correct"], res["wrong"], res["skipped"]
    att.submitted_at = now()
    db.commit()
    return JSONResponse({"ok": True, "redirect": f"/exam-prep/paper/result/{att.id}"})


@app.get("/exam-prep/paper/result/{attempt_id}", response_class=HTMLResponse)
def exam_prep_paper_result(request: Request, attempt_id: int, db: Session = Depends(get_db)):
    """Scorecard: marks with negative marking, per-question verdict, and full solutions."""
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    att = db.query(PaperAttempt).filter_by(id=attempt_id, student_id=student.id).first()
    if not att or not att.submitted_at:
        return RedirectResponse("/exam-prep/papers", status_code=302)
    paper = db.get(MockPaper, att.paper_id)
    res = mockpaper.score_attempt(paper.questions or [], att.answers or {})
    per = {p["n"]: p for p in res["per_q"]}
    rows = [{**q, "verdict": per.get(q.get("n"), {})} for q in (paper.questions or [])]
    pct = round(100 * att.score / att.max_score) if att.max_score else 0
    return templates.TemplateResponse(request, "exam_prep_paper_result.html", {
        "student": student, "paper": paper, "att": att, "rows": rows, "pct": pct,
    })


@app.get("/api/examgen/generate")
def api_examgen_generate(request: Request, subject: str = "jee-physics", sel: str = "",
                         diff: str = "3-4", n: int = 5, fig: str = "", db: Session = Depends(get_db)):
    """Server-side proxy to the RAG generator (Bearer key stays here). Returns {ok, pack} for assess.html."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not has_assessment_access(db, student):
        return JSONResponse({"ok": False, "error": "trial_over", "redirect": "/exam-prep/upgrade"}, status_code=402)
    if not examgen.available():
        return JSONResponse({"ok": False, "error": "RAG generator not configured"})
    selections = []
    for part in (sel or "").split("|"):
        part = part.strip()
        if not part:
            continue
        if "::" in part:
            ch, co = part.split("::", 1)
            selections.append((ch.strip(), co.strip() or None))
        else:
            selections.append((part, None))
    if not selections:
        return JSONResponse({"ok": False, "error": "Pick at least one topic."})
    label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", "JEE Physics")
    # No-repeats: tell the pool which questions this student has already been served.
    seen = [s.question_id for s in db.query(SeenQuestion)
            .filter_by(student_id=student.id, subject=subject)
            .order_by(SeenQuestion.seen_at.desc()).limit(300).all()]
    pack = examgen.generate_pack(subject, selections, diff, n, label,
                                 require_figure=(fig == "1"), exclude=seen)
    if not pack:
        return JSONResponse({"ok": False, "error": "Couldn't generate that test — please try again."})
    # record what we just served so it never comes back
    known = set(seen)
    for q in pack.get("questions", []):
        qid = q.get("qid")
        if qid and str(qid) not in known:
            db.add(SeenQuestion(student_id=student.id, question_id=str(qid), subject=subject))
            known.add(str(qid))
    try:
        db.commit()
    except Exception:
        db.rollback()
    return JSONResponse({"ok": True, "pack": pack})


# ══════════════════════════════════════════════════════════════════════════════════════════════
# TEACHER / INSTITUTE (B2B) — a teacher creates a REAL JEE/NEET test, shares a link, students take
# it with NO signup, and the teacher sees real scores + who's weak in which topic. Reuses the same
# question engine (examgen) and the same assess.html test engine as the student product.
# ══════════════════════════════════════════════════════════════════════════════════════════════

def current_teacher(request: Request, db: Session):
    s = current_student(request, db)
    return s if (s and s.is_teacher) else None


def _new_class_code(db) -> str:
    alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"       # no ambiguous 0/O/1/I
    for _ in range(30):
        code = "".join(secrets.choice(alpha) for _ in range(6))
        if not db.query(ClassTest).filter_by(code=code).first():
            return code
    return secrets.token_urlsafe(6)[:8].upper()


def _weak_from_concepts(concepts) -> list:
    """A sitting's [{topic,status}] → weak concept names (weak first, then shaky)."""
    weak = [c.get("topic") for c in (concepts or []) if c.get("status") == "weak" and c.get("topic")]
    shaky = [c.get("topic") for c in (concepts or []) if c.get("status") == "shaky" and c.get("topic")]
    # de-dupe, keep order
    out, seen = [], set()
    for x in weak + shaky:
        if x not in seen:
            out.append(x); seen.add(x)
    return out


def _confidently_wrong(sits) -> tuple:
    """Aggregate sittings' per-question detail (which carries `conf`) → (reteach, class_calib).
    reteach = questions students were SURE about yet got wrong = a SHARED misconception worth
    re-teaching (grouped by question text, so a fixed pack aggregates across students, and across
    tests identical questions merge). class_calib = how often the class's 'Sure' was actually right."""
    conf_q: dict = {}
    sure_n = sure_ok = 0
    for s in sits:
        for d in (s.detail or []):
            if not isinstance(d, dict):
                continue
            q = str(d.get("q", ""))[:220]
            ok = d.get("ok")
            if not q or ok is None:
                continue
            row = conf_q.setdefault(q, {"q": q, "sure_wrong": 0, "wrong": 0})
            row["wrong"] += 1 if ok is False else 0
            if (d.get("conf") or "") == "sure":
                sure_n += 1
                sure_ok += 1 if ok else 0
                if ok is False:
                    row["sure_wrong"] += 1
    reteach = sorted((r for r in conf_q.values() if r["sure_wrong"] > 0),
                     key=lambda r: (-r["sure_wrong"], -r["wrong"]))[:6]
    calib = None
    if sure_n >= 3:
        acc = round(100 * sure_ok / sure_n)
        calib = {"acc": acc, "n": sure_n,
                 "tone": "good" if acc >= 85 else ("warn" if acc >= 60 else "bad")}
    return reteach, calib


@app.get("/teacher", response_class=HTMLResponse)
def teacher_home(request: Request, new: str = "", db: Session = Depends(get_db)):
    """The teacher console. Not a teacher yet → the signup/promote screen; else their class tests.
    On the KIDS host, a fully kids-themed signup + all-in-one home (batches + assign + roster)."""
    student = current_student(request, db)
    kids = _is_kids(request)
    if not student or not student.is_teacher:
        tmpl = "kids_teacher_signup.html" if kids else "teacher_signup.html"
        return templates.TemplateResponse(request, tmpl, {
            "student": student, "google_client_id": settings.GOOGLE_CLIENT_ID,
            "jsonld": seo.teacher_jsonld()})
    if kids:
        return templates.TemplateResponse(request, "kids_teacher_home.html", _kids_teacher_ctx(request, db, student))
    tests = (db.query(ClassTest).filter_by(teacher_id=student.id)
             .order_by(ClassTest.created_at.desc()).all())
    rows = []
    for t in tests:
        rows.append({"t": t, "sittings": db.query(ClassSitting).filter_by(class_test_id=t.id).count()})
    # Ads "teacher signup" conversion — fires ONCE for a genuinely-new account landing here.
    ads_id = settings.ADS_CONVERSION_ID if (new == "1" and settings.TEACHER_SIGNUP_CONV_LABEL and settings.ADS_CONVERSION_ID) else ""
    return templates.TemplateResponse(request, "teacher_home.html", {
        "student": student, "tests": rows, "ads_id": ads_id, "ads_label": settings.TEACHER_SIGNUP_CONV_LABEL})


DEFAULT_BRAND_COLOR = "#C2591F"   # Acharya saffron — the fallback when an institute hasn't set one

def _teacher_brand(teacher) -> dict:
    """The white-label brand kit for a teacher/institute. Falls back to Acharya defaults.
    Used to theme the printed paper + the linked-student take page. 'Powered by Acharya' always stays."""
    if not teacher:
        return {"color": DEFAULT_BRAND_COLOR, "logo": "", "name": "Acharya", "watermark": False, "custom": False}
    return {
        "color": (getattr(teacher, "brand_color", "") or DEFAULT_BRAND_COLOR),
        "logo": getattr(teacher, "brand_logo", "") or "",
        "name": (getattr(teacher, "institute", "") or "Acharya"),
        "watermark": bool(getattr(teacher, "brand_watermark", False)),
        "custom": bool(getattr(teacher, "brand_color", "") or getattr(teacher, "brand_logo", "")),
    }


@app.get("/teacher/branding", response_class=HTMLResponse)
def teacher_branding(request: Request, saved: str = "", db: Session = Depends(get_db)):
    """Self-serve white-label: the teacher sets their logo, brand colour & paper watermark."""
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=303)
    return templates.TemplateResponse(request, "teacher_branding.html", {
        "student": teacher, "brand": _teacher_brand(teacher),
        "default_color": DEFAULT_BRAND_COLOR, "saved": saved == "1"})


@app.post("/teacher/branding")
async def teacher_branding_save(request: Request,
                                brand_color: str = Form(""),
                                institute: str = Form(""),
                                watermark: str = Form(""),
                                remove_logo: str = Form(""),
                                logo: UploadFile | None = File(None),
                                db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=303)
    if institute.strip():
        teacher.institute = institute.strip()[:120]
    # colour — accept only a valid #RRGGBB (defend against junk); "" clears back to default
    c = (brand_color or "").strip()
    if c and re.fullmatch(r"#[0-9A-Fa-f]{6}", c):
        teacher.brand_color = c.upper()
    elif not c:
        teacher.brand_color = ""
    teacher.brand_watermark = (watermark in ("1", "on", "true", "yes"))
    if remove_logo in ("1", "on", "true", "yes"):
        teacher.brand_logo = ""
    elif logo is not None and logo.filename:
        raw = await logo.read()
        if raw and len(raw) <= 500_000:   # ≤500 KB — keep the row small; institutes use a small mark
            ct = (logo.content_type or "image/png")
            if ct in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml"):
                teacher.brand_logo = f"data:{ct};base64,{base64.b64encode(raw).decode()}"
    db.commit()
    return RedirectResponse("/teacher/branding?saved=1", status_code=303)


def _promote_teacher(db, student, name: str, institute: str):
    student.is_teacher = True
    if institute:
        student.institute = institute[:120]
    if name and not student.name:
        student.name = name[:120]


@app.post("/teacher/signup")
def teacher_signup(request: Request, email: str = Form(...), name: str = Form(""),
                   institute: str = Form(""), website: str = Form(""), db: Session = Depends(get_db)):
    """Instant teacher signup (no magic-link wait) — email → account + session → teacher console."""
    email = email.lower().strip()
    if _looks_like_bot(email, website):          # honeypot filled or throwaway domain → no account, no session
        return RedirectResponse("/teacher", status_code=302)
    if "@" not in email or "." not in email.split("@")[-1]:
        return templates.TemplateResponse(request, "teacher_signup.html",
                                          {"student": None, "google_client_id": settings.GOOGLE_CLIENT_ID,
                                           "error": "Please enter a valid email."})
    existed = db.query(Student).filter_by(email=email).first() is not None
    student = get_or_create_student(db, email)
    _promote_teacher(db, student, name, institute)
    db.commit()
    if not existed:
        notify.notify_admin(f"👩‍🏫 New TEACHER — {student.email} · {institute or '—'}")
    request.session["sid"] = student.id
    # new=1 rides through so the Ads teacher-signup conversion fires once, on landing at /teacher.
    return RedirectResponse("/teacher?new=1" if not existed else "/teacher", status_code=302)


@app.post("/api/teacher/google")
async def teacher_google(request: Request, db: Session = Depends(get_db)):
    """Teacher signup/sign-in via Google One-Tap — verified email, no magic link, promotes to teacher."""
    if not settings.GOOGLE_CLIENT_ID:
        return JSONResponse({"ok": False, "error": "google sign-in not configured"}, status_code=503)
    import json as _json, urllib.request, urllib.parse
    try:
        body = await request.json()
    except Exception:
        body = {}
    cred = (body.get("credential") or "").strip()
    institute = (body.get("institute") or "").strip()
    if not cred:
        return JSONResponse({"ok": False, "error": "no credential"}, status_code=400)
    try:
        vurl = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": cred})
        with urllib.request.urlopen(vurl, timeout=10) as resp:
            tok = _json.loads(resp.read().decode())
    except Exception as exc:
        print(f"[teacher-google] verify failed: {exc}")
        return JSONResponse({"ok": False, "error": "verify failed"}, status_code=400)
    if tok.get("aud") != settings.GOOGLE_CLIENT_ID or str(tok.get("email_verified")).lower() != "true":
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=400)
    email = (tok.get("email") or "").lower().strip()
    if "@" not in email:
        return JSONResponse({"ok": False, "error": "no email"}, status_code=400)
    existed = db.query(Student).filter_by(email=email).first() is not None
    student = get_or_create_student(db, email)
    _promote_teacher(db, student, tok.get("name") or "", institute)
    db.commit()
    if not existed:
        notify.notify_admin(f"👩‍🏫 New TEACHER (Google) — {student.email} · {institute or '—'}")
    request.session["sid"] = student.id
    return JSONResponse({"ok": True, "redirect": "/teacher?new=1" if not existed else "/teacher"})


@app.get("/teacher/chapters")
def teacher_chapters(request: Request, subject: str = "jee-physics", db: Session = Depends(get_db)):
    """Chapters (+ concepts) for a subject, for the create-test picker. Teacher-gated."""
    if not current_teacher(request, db):
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if subject not in examgen.RAG_SUBJECTS:
        return JSONResponse({"ok": False, "error": "unknown subject"}, status_code=400)
    chapters = examgen.chapters_for_ui(subject)
    return JSONResponse({"ok": True, "subject": subject,
                         "label": examgen.RAG_SUBJECTS[subject]["label"],
                         "ladder": examgen.difficulty_ladder(subject), "chapters": chapters})


# Exams offered to TEACHERS = the SAME coverage students get. Was hardcoded to JEE/NEET/Banking only,
# so teachers couldn't make Class 10/12/Commerce/UPSC tests (institute feedback 2026-07-29). Order
# mirrors the student exam picker.
_TEACHER_GOALS = ["jee-advanced", "neet", "cbse-10", "cbse-12", "cbse-12-commerce", "banking", "upsc"]
_KIDS_TEACHER_GOALS = ["class3"]   # kids-education.trigunai.com teachers create Grade-3 tests


def _is_kids(request) -> bool:
    return (request.headers.get("host") or "").split(":")[0].lower() in KIDS_HOSTS


def _teacher_subjects(kids: bool = False):
    """(subject_id, goal_dict) for every live exam's subjects, deduped, in exam order.
    kids=True (kids host) → only the Grade-3 subjects, so a kids teacher never sees JEE/NEET."""
    out, seen = [], set()
    for gid in (_KIDS_TEACHER_GOALS if kids else _TEACHER_GOALS):
        g = examgen.GOALS.get(gid)
        if not g:
            continue
        for sid in g.get("subjects", []):
            if sid in examgen.RAG_SUBJECTS and sid not in seen:
                seen.add(sid)
                out.append((sid, g))
    return out


# ── KIDS teacher flow (batches by grade/board, worksheet assignments) ─────────────────
KIDS_BOARDS = ["CBSE", "ICSE"]   # kids batches — Bihar knowledge banks for grades 1/2/4/5 not generated

def _kids_grade_subjects(grade, board="CBSE") -> list:
    """The kids subjects available at a grade+board (drives the assign picker). From the worksheet engine."""
    try:
        return list(kidsws.picker(board or "CBSE", int(grade or 3)).keys())
    except Exception:
        return ["Mathematics", "EVS", "English", "GK", "Hindi"]


def _kids_teacher_ctx(request, db, teacher) -> dict:
    """Everything the all-in-one kids teacher home needs: batches (+ join links + counts), worksheet
    assignments (+ who completed + class weak topics), and the student roster."""
    invites = (db.query(TeacherInvite).filter_by(teacher_id=teacher.id)
               .order_by(TeacherInvite.created_at.desc()).all())
    linked = db.query(Student).filter_by(teacher_id=teacher.id).all()
    bmap = {i.id: i for i in invites}
    by_batch = {}
    for s in linked:
        by_batch.setdefault(s.batch_id, []).append(s)
    batches = [{"id": i.id, "code": i.code, "label": i.label, "grade": i.grade, "board": i.board,
                "url": f"{settings.BASE_URL}/join/{i.code}", "count": len(by_batch.get(i.id, [])),
                "subjects": _kids_grade_subjects(i.grade, i.board)} for i in invites]
    assigns = (db.query(Assignment).filter_by(teacher_id=teacher.id, active=True)
               .filter(Assignment.kind.in_(["kidsworksheet", "kidstest"]))
               .order_by(Assignment.created_at.desc()).all())
    cmap = {s.id: s for s in linked}
    assign_rows = []
    for a in assigns:
        comps = db.query(AssignmentCompletion).filter_by(assignment_id=a.id).all()
        done = [{"name": (cmap[c.student_id].name if c.student_id in cmap and cmap[c.student_id].name
                          else (cmap[c.student_id].email.split("@")[0] if c.student_id in cmap else "Student")),
                 "score": c.score, "total": c.total} for c in comps]
        weak = {}
        for c in comps:
            for w in (c.weak_topics or []):
                weak[w] = weak.get(w, 0) + 1
        b = bmap.get(a.invite_id)
        from urllib.parse import quote as _q
        parts = (a.ref or "").split("|")
        _subj = parts[0] if parts and parts[0] else (a.subject_label or "Mathematics")
        _ch = parts[1] if len(parts) > 1 else ""
        _n = parts[2] if len(parts) > 2 and parts[2].isdigit() else "8"
        _bd = (b.board if b else "CBSE"); _cl = (b.grade if b else 3)
        preview_url = (f"/exam-prep/worksheet?assign={a.id}&board={_q(_bd)}&cls={_cl}"
                       f"&subject={_q(_subj)}&chapter={_q(_ch)}&n={_n}")
        assign_rows.append({"id": a.id, "title": a.title, "kind": a.kind,
                            "type_label": ("Fixed test — same for all" if a.kind == "kidstest" else "Practice — fresh each time"),
                            "batch": (b.label if b else "All classes"), "preview_url": preview_url,
                            "done": done, "done_n": len(done),
                            "weak": sorted(weak, key=lambda k: -weak[k])[:6]})
    roster = [{"id": s.id, "name": (s.name or s.email.split("@")[0]), "grade": s.grade, "board": s.board,
               "batch": (bmap[s.batch_id].label if s.batch_id in bmap else "—")} for s in linked]
    # subjects for each grade, so the assign form can populate without a round-trip
    grade_subjects = {g: _kids_grade_subjects(g, "CBSE") for g in (1, 2, 3, 4, 5)}
    return {"student": teacher, "google_client_id": settings.GOOGLE_CLIENT_ID,
            "batches": batches, "assignments": assign_rows, "roster": roster,
            "boards": KIDS_BOARDS, "grade_subjects": grade_subjects, "base_url": settings.BASE_URL}


# ── B2B2C: teacher-linked students (institute classroom) ─────────────────────────────
def _new_invite_code(db) -> str:
    alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(30):
        code = "".join(secrets.choice(alpha) for _ in range(7))
        if not db.query(TeacherInvite).filter_by(code=code).first():
            return code
    return secrets.token_urlsafe(7)[:9].upper()


def _linked_teacher(db, student):
    """The teacher/institute Student row this student belongs to, or None."""
    if not student or not getattr(student, "teacher_id", None):
        return None
    return db.query(Student).filter_by(id=student.teacher_id).first()


def _link_subjects(db, student, subject_ids):
    """Seed a linked student's subjects to the teacher's batch list (teacher-controlled — the 5-cap
    and self-service add do NOT apply to linked students; the institute owns the syllabus)."""
    have = {t.topic_key for t in _student_topics(db, student)}
    for sid in subject_ids:
        if sid in examgen.RAG_SUBJECTS and sid not in have:
            db.add(StudentTopic(student_id=student.id, topic_key=sid,
                                title=examgen.RAG_SUBJECTS[sid]["label"][:120], kind="exam"))


def _student_progress(db, s) -> dict:
    """Real per-student progress for the teacher roster — derived only from the student's own answers.
    mastery from ConceptStat when present, else from actual test scores (a class-test-only student still
    gets a real number); tests = adaptive + account-linked class tests; top weak concepts."""
    stats = [x for x in db.query(ConceptStat).filter_by(student_id=s.id).all() if x.seen]
    seen = sum(x.seen for x in stats)
    corr = sum(x.correct for x in stats)
    weak = sorted([x for x in stats if x.seen and (x.correct / x.seen) < 0.5],
                  key=lambda x: x.correct / x.seen)
    tas = db.query(TopicAttempt).filter_by(student_id=s.id).all()
    sits = db.query(ClassSitting).filter_by(student_id=s.id).all()
    graded = ([(a.score, a.total) for a in tas if a.total]
              + [(x.score, x.total) for x in sits if x.total])
    tests = len(tas) + len(sits)
    if seen:
        mastery = round(100 * corr / seen)
    elif graded:
        mastery = round(100 * sum(sc for sc, _ in graded) / sum(t for _, t in graded))
    else:
        mastery = 0
    return {"id": s.id, "name": s.name or s.email.split("@")[0], "email": s.email,
            "mastery": mastery, "tests": tests, "practised": bool(seen or graded),
            "weak": [w.concept for w in weak[:3]],
            "last_active": s.last_active_at}


def _roster(db, teacher):
    """Every linked student of this teacher with real progress, weakest-first (needs-help at top)."""
    linked = (db.query(Student).filter_by(teacher_id=teacher.id)
              .order_by(Student.enrolled_at.desc()).all())
    batches = {b.id: b for b in db.query(TeacherInvite).filter_by(teacher_id=teacher.id).all()}
    out = []
    for s in linked:
        p = _student_progress(db, s)
        b = batches.get(getattr(s, "batch_id", None))
        p["batch"] = b.label if b else "—"
        p["needs_help"] = p["practised"] and p["mastery"] < 40
        out.append(p)
    # not-yet-practised last, then weakest mastery first
    out.sort(key=lambda r: (not r["practised"], r["mastery"]))
    return out


@app.get("/teacher/invites", response_class=HTMLResponse)
def teacher_invites(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    invites = (db.query(TeacherInvite).filter_by(teacher_id=teacher.id)
               .order_by(TeacherInvite.created_at.desc()).all())
    subs = [{"id": sid, "label": examgen.RAG_SUBJECTS[sid]["label"], "exam": g["label"]}
            for sid, g in _teacher_subjects(_is_kids(request))]
    roster = _roster(db, teacher)                        # per-student list with real progress
    inv_rows = [{"id": i.id, "code": i.code, "label": i.label, "active": i.active,
                 "count": sum(1 for r in roster if r.get("batch") == i.label),
                 "sublabels": [examgen.RAG_SUBJECTS[s]["label"] for s in (i.subjects or []) if s in examgen.RAG_SUBJECTS],
                 "url": f"{settings.BASE_URL}/join/{i.code}"} for i in invites]
    assigns = (db.query(Assignment).filter_by(teacher_id=teacher.id, active=True)
               .order_by(Assignment.created_at.desc()).all())
    _bmap = {i.id: i.label for i in invites}
    _linked = db.query(Student).filter_by(teacher_id=teacher.id).all()
    assign_rows = []
    for a in assigns:
        done, scope = _assignment_done_count(db, teacher, a, _linked)
        assign_rows.append({"id": a.id, "title": a.title, "kind": a.kind,
                            "batch": _bmap.get(a.invite_id, "All batches"),
                            "done": done, "scope": scope})
    tests = (db.query(ClassTest).filter_by(teacher_id=teacher.id).order_by(ClassTest.created_at.desc()).limit(20).all())
    return templates.TemplateResponse(request, "teacher_invites.html", {
        "student": teacher, "invites": inv_rows, "subjects": subs,
        "roster": roster, "roster_count": len(roster),
        "base_url": settings.BASE_URL,
        "assignments": assign_rows,
        "tests": [{"code": t.code, "title": t.title or t.subject_label} for t in tests]})


@app.post("/api/teacher/invite")
async def teacher_invite_create(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"error": "login"}, status_code=401)
    body = await request.json()
    label = (body.get("label") or "").strip()[:80] or "My class"
    code = _new_invite_code(db)
    if _is_kids(request):
        # a kids batch scopes by GRADE + BOARD (students can practise any subject at that grade).
        try:
            grade = int(body.get("grade") or 0)
        except (TypeError, ValueError):
            grade = 0
        if grade not in (1, 2, 3, 4, 5):
            return JSONResponse({"error": "Pick a class (1–5) for this batch."}, status_code=400)
        board = (body.get("board") or "CBSE").strip()
        if board not in KIDS_BOARDS:
            board = "CBSE"
        subjects = _kids_grade_subjects(grade, board)   # for display; students aren't subject-restricted
        if not (label and label != "My class"):
            label = f"Class {grade} · {board}"
        db.add(TeacherInvite(code=code, teacher_id=teacher.id, label=label, subjects=subjects,
                             grade=grade, board=board))
        db.commit()
        return JSONResponse({"ok": True, "code": code, "url": f"{settings.BASE_URL}/join/{code}"})
    subjects = [s for s in (body.get("subjects") or []) if s in examgen.RAG_SUBJECTS][:8]
    if not subjects:
        return JSONResponse({"error": "Pick at least one subject for this batch."}, status_code=400)
    db.add(TeacherInvite(code=code, teacher_id=teacher.id, label=label, subjects=subjects))
    db.commit()
    return JSONResponse({"ok": True, "code": code, "url": f"{settings.BASE_URL}/join/{code}"})


@app.get("/join/{code}", response_class=HTMLResponse)
def join_landing(request: Request, code: str, db: Session = Depends(get_db)):
    inv = db.query(TeacherInvite).filter_by(code=code, active=True).first()
    if not inv:
        return RedirectResponse("/exam-prep", status_code=302)
    teacher = db.query(Student).filter_by(id=inv.teacher_id).first()
    institute = ((teacher.institute if teacher else "") or (teacher.name if teacher else "") or "your teacher")
    sublabels = [examgen.RAG_SUBJECTS[s]["label"] for s in (inv.subjects or []) if s in examgen.RAG_SUBJECTS]
    me = current_student(request, db)
    # already this student's batch → straight to their dashboard (no re-signup)
    if me and not me.is_teacher and me.teacher_id == inv.teacher_id:
        return RedirectResponse("/exam-prep/dashboard", status_code=302)
    # a teacher opening their OWN join link (to test) would overwrite this browser's teacher session
    # with a student one → "logged out on refresh". Warn instead of silently clobbering.
    teacher_warning = bool(me and me.is_teacher)
    return templates.TemplateResponse(request, "join.html", {
        "code": code, "institute": institute, "label": inv.label, "sublabels": sublabels,
        "teacher_warning": teacher_warning, "kids": _is_kids(request),
        "grade": getattr(inv, "grade", None), "board": getattr(inv, "board", "") or "",
        "err": request.query_params.get("err", ""),
        "google_client_id": settings.GOOGLE_CLIENT_ID})


@app.post("/join/{code}")
def join_submit(request: Request, code: str, email: str = Form(...), name: str = Form(""),
                db: Session = Depends(get_db)):
    inv = db.query(TeacherInvite).filter_by(code=code, active=True).first()
    if not inv:
        return RedirectResponse("/exam-prep", status_code=302)
    email = email.lower().strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        return RedirectResponse(f"/join/{code}?err=1", status_code=302)
    existing = db.query(Student).filter_by(email=email).first()
    # a teacher account can't be a student in a batch — joining would also nuke their teacher session.
    if existing and existing.is_teacher:
        return RedirectResponse(f"/join/{code}?err=teacher", status_code=302)
    existed = existing is not None
    student = get_or_create_student(db, email)
    if name and not student.name:
        student.name = name[:120]
    student.teacher_id = inv.teacher_id                    # link to the institute
    student.batch_id = inv.id                              # …and to this specific batch
    if getattr(inv, "grade", None):                        # kids batch → lock the student's class + board
        student.grade = inv.grade
        student.board = inv.board or "CBSE"
    _link_subjects(db, student, inv.subjects)              # seed the batch's subjects (no-op for kids labels)
    db.commit()
    if not existed:
        notify.notify_admin(f"🎓 New STUDENT joined a teacher batch — {student.email} · {inv.label}")
    request.session["sid"] = student.id
    return RedirectResponse("/exam-prep/dashboard", status_code=302)


def _student_assignments(db, student):
    """Active assignments from this student's teacher → items with a start URL (the '📋 Assigned'
    section on the student dashboard)."""
    if not student or not getattr(student, "teacher_id", None):
        return []
    bid = getattr(student, "batch_id", None)
    rows = (db.query(Assignment).filter_by(teacher_id=student.teacher_id, active=True)
            .order_by(Assignment.created_at.desc()).all())
    # batch-scope: an assignment with no batch (invite_id=None) is for ALL batches; else only this one.
    rows = [a for a in rows if a.invite_id is None or a.invite_id == bid][:12]
    from urllib.parse import quote as _q
    out = []
    for a in rows:
        if a.kind in ("kidsworksheet", "kidstest"):
            # kids: Solve (on-screen) + Print (offline). Practice regenerates fresh; a fixed test loads
            # the frozen pack. Grade/board come from the student (locked at join).
            parts = (a.ref or "").split("|")
            subject = parts[0] if parts and parts[0] else (a.subject_label or "Mathematics")
            chapter = parts[1] if len(parts) > 1 else ""
            nq = parts[2] if len(parts) > 2 and parts[2].isdigit() else "8"
            board = student.board or "CBSE"
            cls = student.grade or 3
            base = (f"/exam-prep/worksheet?assign={a.id}"
                    f"&board={_q(board)}&cls={cls}&subject={_q(subject)}&chapter={_q(chapter)}&n={nq}")
            out.append({"title": a.title or subject or "Worksheet", "kind": a.kind,
                        "url": base, "print_url": base + "&print=1", "worksheet": True,
                        "icon": ("📝" if a.kind == "kidstest" else "✏️"), "subject": subject})
            continue
        if a.kind == "smart":
            url, icon = f"/exam-prep/smart?subject={a.ref}", "🎯"
        elif a.kind == "mock":
            url, icon = "/exam-prep/papers", "⏱️"
        elif a.kind == "classtest":
            url, icon = f"/t/{a.ref}", "📝"
        else:
            continue
        out.append({"title": a.title or a.subject_label or "Practice", "kind": a.kind,
                    "url": url, "icon": icon, "subject": a.subject_label})
    return out


@app.post("/api/teacher/assign")
async def teacher_assign(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"error": "login"}, status_code=401)
    body = await request.json()
    kind = (body.get("kind") or "").strip()
    ref = (body.get("ref") or "").strip()[:120]
    title = (body.get("title") or "").strip()[:140]
    # optional batch target: an invite_id owned by this teacher, else None = all batches
    invite_id = body.get("invite_id")
    try:
        invite_id = int(invite_id) if invite_id not in (None, "", "all") else None
    except (TypeError, ValueError):
        invite_id = None
    inv = db.query(TeacherInvite).filter_by(id=invite_id, teacher_id=teacher.id).first() if invite_id is not None else None
    if invite_id is not None and not inv:
        invite_id = None

    # ── KIDS worksheet assignment (practice = fresh per student · test = one frozen sheet for all) ──
    if kind in ("kidsworksheet", "kidstest"):
        if not inv or not getattr(inv, "grade", None):
            return JSONResponse({"error": "Pick a class (batch) first."}, status_code=400)
        parts = ref.split("|")
        subject = (parts[0].strip() if parts else "") or "Mathematics"
        chapter = (parts[1].strip() if len(parts) > 1 else "")
        try:
            nq = int(parts[2]) if len(parts) > 2 and parts[2].strip() else 8
        except (TypeError, ValueError):
            nq = 8
        nq = max(3, min(nq, 15))
        if subject not in _kids_grade_subjects(inv.grade, inv.board):
            return JSONResponse({"error": "Pick a subject for this class."}, status_code=400)
        ref = f"{subject}|{chapter}|{nq}"
        title = title or (subject + (f" · {chapter}" if chapter else " · Mixed") +
                          (" (test)" if kind == "kidstest" else " worksheet"))
        pack = None
        if kind == "kidstest":
            try:
                data = kidsws.serve(db, teacher, inv.board or "CBSE", inv.grade, subject, chapter or None, n=nq)
            except Exception as exc:
                return JSONResponse({"error": f"Could not make the test: {str(exc)[:80]}"}, status_code=500)
            its = data.get("items", []) if isinstance(data, dict) else []
            if not its:
                return JSONResponse({"error": "No questions for that topic yet — try Maths or another topic."}, status_code=400)
            pack = {"items": its, "subject": subject, "board": inv.board, "cls": inv.grade, "chapter": chapter}
        db.add(Assignment(teacher_id=teacher.id, invite_id=invite_id, kind=kind, ref=ref,
                          title=title[:140], subject_label=subject, pack=pack))
        db.commit()
        return JSONResponse({"ok": True})

    if kind not in ("smart", "mock", "classtest"):
        return JSONResponse({"error": "bad kind"}, status_code=400)
    sub_label = ""
    if kind == "smart":
        if ref not in examgen.RAG_SUBJECTS:
            return JSONResponse({"error": "pick a subject"}, status_code=400)
        sub_label = examgen.RAG_SUBJECTS[ref]["label"]
        title = title or f"Smart Practice · {sub_label}"
    elif kind == "mock":
        sub_label = examgen.RAG_SUBJECTS.get(ref, {}).get("label", "") if ref else ""
        title = title or ("Mock test" + (f" · {sub_label}" if sub_label else ""))
    elif kind == "classtest":
        ct = db.query(ClassTest).filter_by(code=ref, teacher_id=teacher.id).first()
        if not ct:
            return JSONResponse({"error": "no such test"}, status_code=400)
        title = title or ct.title or ct.subject_label or f"Test {ref}"
    db.add(Assignment(teacher_id=teacher.id, invite_id=invite_id, kind=kind, ref=ref,
                      title=title, subject_label=sub_label))
    db.commit()
    return JSONResponse({"ok": True})


@app.post("/api/teacher/assign/{aid}/remove")
def teacher_assign_remove(request: Request, aid: int, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"error": "login"}, status_code=401)
    a = db.query(Assignment).filter_by(id=aid, teacher_id=teacher.id).first()
    if a:
        a.active = False
        db.commit()
    return JSONResponse({"ok": True})


def _review_detail(raw) -> list:
    """Normalize a stored per-question detail list into template-safe review rows."""
    out = []
    for d in (raw or [])[:60]:
        if not isinstance(d, dict):
            continue
        out.append({"q": d.get("q") or "", "chosen": d.get("chosen") or "",
                    "a": d.get("a") or "", "ok": d.get("ok"), "type": d.get("type") or "mcq"})
    return out


def _mock_review(mp, answers) -> list:
    """Best-effort per-question review for a mock-paper attempt from the paper + the student's answers."""
    out = []
    for q in (mp.questions or [])[:60]:
        n = str(q.get("n"))
        chosen = answers.get(n) if isinstance(answers, dict) else None
        if isinstance(chosen, list):
            chosen = ", ".join(str(c) for c in chosen)
        correct = q.get("correct")
        ok = None
        if chosen not in (None, ""):
            ok = (str(chosen).strip().lower() == str(correct).strip().lower())
        out.append({"q": q.get("stem") or "", "chosen": "" if chosen is None else str(chosen),
                    "a": "" if correct is None else str(correct), "ok": ok, "type": q.get("qtype") or "mcq"})
    return out


def _assignment_done_count(db, teacher, a, linked) -> tuple:
    """(how many, of how many in scope) students have completed this assignment — for the at-a-glance
    '2/5 done' on the roster page."""
    scope = [s for s in linked if a.invite_id is None or getattr(s, "batch_id", None) == a.invite_id]
    ids = [s.id for s in scope]
    if not ids:
        return (0, 0)
    done = 0
    if a.kind == "classtest":
        ct = db.query(ClassTest).filter_by(code=a.ref, teacher_id=teacher.id).first()
        if ct:
            done = (db.query(ClassSitting.student_id)
                    .filter(ClassSitting.class_test_id == ct.id, ClassSitting.student_id.in_(ids))
                    .distinct().count())
    elif a.kind == "smart":
        done = sum(1 for sid in ids if db.query(TopicAttempt.id).filter(
            TopicAttempt.student_id == sid, TopicAttempt.subject == a.ref,
            TopicAttempt.taken_at >= a.created_at).first())
    elif a.kind == "mock":
        done = sum(1 for sid in ids if db.query(PaperAttempt.id).filter(
            PaperAttempt.student_id == sid, PaperAttempt.submitted_at != None,  # noqa: E711
            PaperAttempt.submitted_at >= a.created_at).first())
    return (done, len(ids))


def _assignment_status(db, teacher, s) -> list:
    """For each active assignment this student can see, whether THEY have done it (+ score)."""
    bid = getattr(s, "batch_id", None)
    rows = (db.query(Assignment).filter_by(teacher_id=teacher.id, active=True)
            .order_by(Assignment.created_at.desc()).all())
    rows = [a for a in rows if a.invite_id is None or a.invite_id == bid][:12]
    out = []
    for a in rows:
        done, pct, when = False, 0, ""
        if a.kind == "classtest":
            ct = db.query(ClassTest).filter_by(code=a.ref, teacher_id=teacher.id).first()
            st = (db.query(ClassSitting).filter_by(student_id=s.id, class_test_id=ct.id)
                  .order_by(ClassSitting.submitted_at.desc()).first()) if ct else None
            if st:
                done, pct = True, (round(100 * st.score / st.total) if st.total else 0)
                when = st.submitted_at.strftime("%d %b")
        elif a.kind == "smart":
            ta = (db.query(TopicAttempt).filter(TopicAttempt.student_id == s.id,
                  TopicAttempt.subject == a.ref, TopicAttempt.taken_at >= a.created_at)
                  .order_by(TopicAttempt.taken_at.desc()).first())
            if ta:
                done, pct = True, (round(100 * ta.score / ta.total) if ta.total else 0)
                when = ta.taken_at.strftime("%d %b")
        elif a.kind == "mock":
            pa = (db.query(PaperAttempt).filter(PaperAttempt.student_id == s.id,
                  PaperAttempt.submitted_at != None, PaperAttempt.submitted_at >= a.created_at)  # noqa: E711
                  .order_by(PaperAttempt.submitted_at.desc()).first())
            if pa:
                done, pct = True, (round(100 * pa.score / pa.max_score) if pa.max_score else 0)
                when = pa.submitted_at.strftime("%d %b")
        out.append({"title": a.title, "kind": a.kind, "done": done, "pct": pct, "when": when})
    return out


@app.get("/teacher/student/{sid}", response_class=HTMLResponse)
def teacher_student(request: Request, sid: int, db: Session = Depends(get_db)):
    """A teacher's drill-down on ONE of their linked students — real mastery, weak topics, recent
    tests (expandable to the actual answers), and which assigned tests they've done."""
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    s = db.query(Student).filter_by(id=sid, teacher_id=teacher.id).first()  # ownership-scoped
    if not s:
        return RedirectResponse("/teacher/invites", status_code=302)
    prog = _student_progress(db, s)
    batch = db.query(TeacherInvite).filter_by(id=getattr(s, "batch_id", None)).first()
    subjects = [t.title for t in _student_topics(db, s)]
    recent = []
    for a in (db.query(TopicAttempt).filter_by(student_id=s.id)
              .order_by(TopicAttempt.taken_at.desc()).limit(10).all()):
        recent.append({"title": a.title or a.subject, "score": a.score, "total": a.total,
                       "pct": round(100 * a.score / a.total) if a.total else 0,
                       "when": a.taken_at.strftime("%d %b"), "kind": "Practice",
                       "detail": _review_detail(a.detail), "_at": a.taken_at})
    for st in (db.query(ClassSitting).filter_by(student_id=s.id)
               .order_by(ClassSitting.submitted_at.desc()).limit(10).all()):
        ct = db.query(ClassTest).filter_by(id=st.class_test_id).first()
        recent.append({"title": (ct.title or ct.subject_label) if ct else "Class test",
                       "score": st.score, "total": st.total,
                       "pct": round(100 * st.score / st.total) if st.total else 0,
                       "when": st.submitted_at.strftime("%d %b"), "kind": "Class test",
                       "detail": _review_detail(st.detail), "_at": st.submitted_at})
    for pa in (db.query(PaperAttempt).filter(PaperAttempt.student_id == s.id,
               PaperAttempt.submitted_at != None)  # noqa: E711
               .order_by(PaperAttempt.submitted_at.desc()).limit(10).all()):
        mp = db.query(MockPaper).filter_by(id=pa.paper_id).first()
        recent.append({"title": (mp.title if mp else "Mock paper"),
                       "score": round(pa.score), "total": pa.max_score,
                       "pct": round(100 * pa.score / pa.max_score) if pa.max_score else 0,
                       "when": pa.submitted_at.strftime("%d %b"), "kind": "Mock",
                       "detail": _mock_review(mp, pa.answers) if mp else [], "_at": pa.submitted_at})
    recent.sort(key=lambda r: r["_at"], reverse=True)
    recent = recent[:12]
    return templates.TemplateResponse(request, "teacher_student.html", {
        "student": teacher, "s": s, "prog": prog, "assigned": _assignment_status(db, teacher, s),
        "batch": batch.label if batch else "—", "subjects": subjects, "recent": recent})


@app.get("/teacher/new", response_class=HTMLResponse)
def teacher_new(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    subs = [{"id": sid, "label": examgen.RAG_SUBJECTS[sid]["label"], "exam": g["label"]}
            for sid, g in _teacher_subjects(_is_kids(request))]
    return templates.TemplateResponse(request, "teacher_new.html", {"student": teacher, "subjects": subs})


@app.post("/api/teacher/create")
async def teacher_create(request: Request, db: Session = Depends(get_db)):
    """Generate the test ONCE (examgen) and store it, so every student gets the same paper instantly.
    Returns the share code. Slow (LLM) — the teacher_new page shows a progress UI while it runs."""
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if not examgen.available():
        return JSONResponse({"ok": False, "error": "generator not configured"})
    try:
        body = await request.json()
    except Exception:
        body = {}
    subject = (body.get("subject") or "").strip()
    if subject not in examgen.RAG_SUBJECTS:
        return JSONResponse({"ok": False, "error": "pick a subject"})
    sel_raw = body.get("sel") or []                 # ["Chapter::Concept", "Chapter::", ...]
    diff = (body.get("diff") or examgen.difficulty_ladder(subject)["mix"]).strip()
    n = max(1, min(int(body.get("n") or 5), 12))
    title = (body.get("title") or "").strip()[:120]
    selections = []
    for part in sel_raw:
        part = (part or "").strip()
        if not part:
            continue
        if "::" in part:
            ch, co = part.split("::", 1)
            selections.append((ch.strip(), co.strip() or None))
        else:
            selections.append((part, None))
    if not selections:
        return JSONResponse({"ok": False, "error": "Pick at least one chapter."})
    label = examgen.RAG_SUBJECTS[subject]["label"]
    pack = await run_in_threadpool(examgen.generate_pack, subject, selections, diff, n, title or label)
    if not pack or not pack.get("questions"):
        return JSONResponse({"ok": False, "error": "Couldn't generate the test — please try again."})
    code = _new_class_code(db)
    chapters = [f"{c}" + (f" · {co}" if co else "") for c, co in selections]
    ct = ClassTest(teacher_id=teacher.id, code=code, title=title or f"{label} test",
                   subject_id=subject, subject_label=label, chapters=chapters,
                   difficulty=diff, n=len(pack["questions"]), pack=pack)
    db.add(ct)
    db.commit()
    return JSONResponse({"ok": True, "code": code, "redirect": f"/teacher/test/{code}"})


def _sittings_for(db, ct) -> list:
    return (db.query(ClassSitting).filter_by(class_test_id=ct.id)
            .order_by(ClassSitting.submitted_at.desc()).all())


@app.get("/teacher/test/{code}", response_class=HTMLResponse)
def teacher_test(request: Request, code: str, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    ct = db.query(ClassTest).filter_by(code=code, teacher_id=teacher.id).first()
    if not ct:
        return RedirectResponse("/teacher", status_code=302)
    sits = _sittings_for(db, ct)
    # class weak-topic aggregation
    weak_count: dict = {}
    for s in sits:
        for w in (s.weak_topics or []):
            weak_count[w] = weak_count.get(w, 0) + 1
    class_weak = sorted(weak_count.items(), key=lambda kv: -kv[1])[:8]
    # class RED BOX — questions students were CONFIDENTLY wrong on (sure + wrong) = a shared misconception.
    reteach, class_calib = _confidently_wrong(sits)
    avg = round(sum(s.score for s in sits) / sum(s.total for s in sits) * 100) if sits and sum(s.total for s in sits) else 0
    share = f"{settings.BASE_URL}/t/{ct.code}"
    return templates.TemplateResponse(request, "teacher_test.html", {
        "student": teacher, "ct": ct, "sits": sits, "class_weak": class_weak,
        "reteach": reteach, "class_calib": class_calib,
        "avg": avg, "share": share, "n_students": len(sits)})


@app.get("/teacher/test/{code}/print", response_class=HTMLResponse)
def teacher_test_print(request: Request, code: str, answers: str = "", db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    ct = db.query(ClassTest).filter_by(code=code, teacher_id=teacher.id).first()
    if not ct:
        return RedirectResponse("/teacher", status_code=302)
    return templates.TemplateResponse(request, "teacher_print.html", {
        "student": teacher, "ct": ct, "pack": ct.pack, "show_answers": (answers == "1"),
        "brand": _teacher_brand(teacher)})


@app.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    """Across ALL the teacher's tests: class-at-a-glance, weak-topic heatmap, and every student
    flagged by how they're doing — the 'see & control every student' pitch, on REAL results."""
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    tests = db.query(ClassTest).filter_by(teacher_id=teacher.id).all()
    tids = [t.id for t in tests]
    sits = (db.query(ClassSitting).filter(ClassSitting.class_test_id.in_(tids)).all() if tids else [])
    # per-student roll-up (by name) + class weak-topic counts
    by_student: dict = {}
    weak_count: dict = {}
    for s in sits:
        b = by_student.setdefault(s.student_name or "—", {"name": s.student_name or "—", "tests": 0,
                                                           "score": 0, "total": 0, "weak": {}})
        b["tests"] += 1; b["score"] += s.score; b["total"] += s.total
        for w in (s.weak_topics or []):
            b["weak"][w] = b["weak"].get(w, 0) + 1
            weak_count[w] = weak_count.get(w, 0) + 1
    students = []
    for b in by_student.values():
        pct = round(b["score"] / b["total"] * 100) if b["total"] else 0
        tier = "weak" if pct < 40 else ("shaky" if pct < 70 else "solid")
        top_weak = sorted(b["weak"].items(), key=lambda kv: -kv[1])[:3]
        students.append({"name": b["name"], "pct": pct, "tier": tier, "tests": b["tests"],
                         "weak": [w for w, _ in top_weak]})
    students.sort(key=lambda x: x["pct"])                # weakest first — who needs help
    class_weak = sorted(weak_count.items(), key=lambda kv: -kv[1])[:10]
    # confidently-wrong across ALL the teacher's tests (identical questions merge across packs)
    reteach, class_calib = _confidently_wrong(sits)
    return templates.TemplateResponse(request, "teacher_dashboard.html", {
        "student": teacher, "n_tests": len(tests), "n_sits": len(sits),
        "students": students, "class_weak": class_weak,
        "reteach": reteach, "class_calib": class_calib})


# ---- student side: take a class test with NO account, just a name ----

@app.get("/t/{code}", response_class=HTMLResponse)
def class_take_gate(request: Request, code: str, db: Session = Depends(get_db)):
    ct = db.query(ClassTest).filter_by(code=code).first()
    if not ct:
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:40px'>This test link is not valid.</h2>",
                            status_code=404)
    # a LOGGED-IN student of this institute skips the name gate — we know who they are, and their
    # result ties to their account (so it rolls up to the teacher roster, not an anonymous name).
    me = current_student(request, db)
    if me and not me.is_teacher and me.teacher_id == ct.teacher_id:
        request.session[f"ct_{code}"] = me.name or me.email.split("@")[0]
        return RedirectResponse(f"/t/{code}/go", status_code=302)
    # already gave a name this session → straight into the test
    if request.session.get(f"ct_{code}"):
        return RedirectResponse(f"/t/{code}/go", status_code=302)
    teacher = db.query(Student).filter_by(id=ct.teacher_id).first()
    return templates.TemplateResponse(request, "class_take.html", {"ct": ct, "brand": _teacher_brand(teacher)})


@app.post("/t/{code}")
def class_take_start(request: Request, code: str, name: str = Form(...), db: Session = Depends(get_db)):
    ct = db.query(ClassTest).filter_by(code=code).first()
    if not ct:
        return RedirectResponse("/", status_code=302)
    nm = (name or "").strip()[:80]
    if len(nm) < 1:
        return RedirectResponse(f"/t/{code}", status_code=302)
    request.session[f"ct_{code}"] = nm
    return RedirectResponse(f"/t/{code}/go", status_code=302)


@app.get("/t/{code}/go", response_class=HTMLResponse)
def class_take_go(request: Request, code: str, db: Session = Depends(get_db)):
    ct = db.query(ClassTest).filter_by(code=code).first()
    if not ct:
        return RedirectResponse("/", status_code=302)
    if not request.session.get(f"ct_{code}"):
        return RedirectResponse(f"/t/{code}", status_code=302)
    import json as _json
    inject = ("<script>window.__PACK=" + _json.dumps(ct.pack) + ";"
              "window.__CLASSTEST=" + _json.dumps({"code": code, "sittingUrl": "/api/teacher/sitting"}) + ";"
              "</script>")
    html = (BASE / "static" / "exam" / "assess.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("</head>", inject + "</head>", 1))


@app.post("/api/teacher/sitting")
async def teacher_sitting(request: Request, db: Session = Depends(get_db)):
    """Record a student's class-test attempt (name from session, results from the engine)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    code = (body.get("code") or "").strip()
    ct = db.query(ClassTest).filter_by(code=code).first()
    if not ct:
        return JSONResponse({"ok": False, "error": "unknown test"}, status_code=404)
    name = request.session.get(f"ct_{code}") or "Student"
    # if the taker is a logged-in student of THIS institute, tie the sitting to their account.
    me = current_student(request, db)
    sid = me.id if (me and not me.is_teacher and me.teacher_id == ct.teacher_id) else None
    if me and sid:
        name = me.name or me.email.split("@")[0]
    results = body.get("results") or []
    concepts = [{"topic": r.get("topic"), "status": r.get("status"), "depth": r.get("depth")}
                for r in results if r.get("topic")]
    weak = _weak_from_concepts(concepts)
    detail = body.get("detail") or []
    if not isinstance(detail, list):
        detail = []
    db.add(ClassSitting(class_test_id=ct.id, student_id=sid, student_name=name[:80],
                        score=int(body.get("score") or 0), total=int(body.get("graded") or 0),
                        concepts=concepts, weak_topics=weak, detail=detail[:60]))
    db.commit()
    return JSONResponse({"ok": True})


# ══════════════════════════════════════════════════════════════════════════════════════════════
# CHAT LAYER — the conversational front for BOTH roles. It helps a teacher/student ARTICULATE the
# test they want (chip-guided, free-text accepted) and drives the real deterministic actions.
# Slow generation runs as a BACKGROUND JOB so nothing times out — the chat shows a "thinking…"
# bubble and delivers action buttons when ready (the "Claude thinks, then delivers" feel).
# ══════════════════════════════════════════════════════════════════════════════════════════════

import threading as _threading
from .db import SessionLocal as _SessionLocal


def _run_teacher_test_job(token: str):
    """Background worker: generate the pack, create the ClassTest, mark the job done. Own DB session
    (this runs in a thread, so it must NOT share the request's session)."""
    db = _SessionLocal()
    try:
        job = db.query(GenJob).filter_by(token=token).first()
        if not job:
            return
        p = job.params or {}
        subject = p.get("subject")
        selections = [(s[0], s[1]) for s in p.get("selections", [])]
        diff = p.get("diff") or "3-4"
        n = max(1, min(int(p.get("n") or 5), 20))
        title = (p.get("title") or "").strip()[:120]
        label = examgen.RAG_SUBJECTS.get(subject, {}).get("label", "Test")
        pack = examgen.generate_pack(subject, selections, diff, n, title or label)
        job = db.query(GenJob).filter_by(token=token).first()
        if not pack or not pack.get("questions"):
            job.status = "error"; job.result = {"error": "Couldn't generate that test — please try again."}
            db.commit(); return
        code = _new_class_code(db)
        chapters = [f"{c}" + (f" · {co}" if co else "") for c, co in selections]
        db.add(ClassTest(teacher_id=job.owner_id, code=code, title=title or f"{label} test",
                         subject_id=subject, subject_label=label, chapters=chapters,
                         difficulty=diff, n=len(pack["questions"]), pack=pack))
        job.status = "done"
        job.result = {"code": code, "redirect": f"/teacher/test/{code}", "title": title or f"{label} test",
                      "n": len(pack["questions"]), "subject_label": label,
                      "share": f"{settings.BASE_URL}/t/{code}"}
        db.commit()
    except Exception as exc:
        try:
            job = db.query(GenJob).filter_by(token=token).first()
            if job:
                job.status = "error"; job.result = {"error": str(exc)[:180]}; db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _kick_teacher_job(db, teacher_id: int, params: dict) -> str:
    token = secrets.token_urlsafe(12)
    db.add(GenJob(token=token, owner_id=teacher_id, kind="teacher_test", params=params, status="pending"))
    db.commit()
    _threading.Thread(target=_run_teacher_test_job, args=(token,), daemon=True).start()
    return token


@app.get("/api/chat/job/{token}")
def chat_job(token: str, db: Session = Depends(get_db)):
    job = db.query(GenJob).filter_by(token=token).first()
    if not job:
        return JSONResponse({"ok": False, "error": "unknown job"}, status_code=404)
    return JSONResponse({"ok": True, "status": job.status, "result": job.result or {}})


# ---- chat step function: stateless, driven by the client-held `state` + the latest input ----

def _subject_chips(db=None, student=None):
    """Every LIVE subject (derived from RAG_SUBJECTS so new banks — Class 10/12, Commerce, UPSC —
    appear automatically; no more stale hardcoded list). The student's goal subjects are floated to
    the front so their most relevant options come first."""
    subs = list(examgen.RAG_SUBJECTS.keys())
    if db is not None and student is not None:
        try:
            goal = _student_goal(db, student)
            pref = [s for s in examgen.GOALS.get(goal, {}).get("subjects", []) if s in subs]
            subs = pref + [s for s in subs if s not in pref]
        except Exception:
            pass
    return [{"label": examgen.RAG_SUBJECTS[s]["label"], "value": "subj:" + s} for s in subs]


def _chapter_chips(subject: str):
    chs = examgen.chapters_for_ui(subject)
    chips = [{"label": "✨ Full subject", "value": "full"}]
    for c in chs[:14]:
        chips.append({"label": c["chapter"], "value": "chap:" + c["chapter"]})
    return chips


def _diff_chips(subject: str):
    lad = examgen.difficulty_ladder(subject)
    return [{"label": "Easy", "value": "diff:" + lad["easy"]},
            {"label": "Mix", "value": "diff:" + lad["mix"]},
            {"label": "Hard", "value": "diff:" + lad["hard"]}]


# ---- KIDS chat: curriculum-driven subject + topic chips (all subjects → worksheet flow) ----
KIDS_CHAT_BOARD, KIDS_CHAT_CLASS = "CBSE", 3
KIDS_SUBJECT_LABELS = {"Mathematics": "🔢 Maths", "EVS": "🌍 EVS", "English": "📖 English",
                       "GK": "🧠 GK", "Hindi": "🇮🇳 Hindi"}


def _kids_subject_label(subject: str) -> str:
    return KIDS_SUBJECT_LABELS.get(subject, subject)


def _kids_curriculum() -> dict:
    """{subject: [chapters]} for the kids board/class, straight from the worksheet curriculum."""
    try:
        return kidsws.picker(KIDS_CHAT_BOARD, KIDS_CHAT_CLASS) or {}
    except Exception:
        return {"Mathematics": []}


def _kids_subject_chips():
    curr = _kids_curriculum()
    order = ["Mathematics", "EVS", "English", "GK", "Hindi"]
    subs = [s for s in order if s in curr] + [s for s in curr if s not in order]
    return [{"label": _kids_subject_label(s), "value": "ksubj:" + s} for s in (subs or ["Mathematics"])]


def _kids_chapter_chips(subject: str):
    chs = _kids_curriculum().get(subject, [])
    chips = [{"label": "✨ Mixed practice", "value": "kgo"}]
    for ch in chs[:12]:
        chips.append({"label": ch if len(ch) <= 24 else ch[:24] + "…", "value": "kchap:" + ch})
    return chips


def _reply(msg, chips=None, input=False, job=None, nav=None, actions=None, state=None):
    return {"ok": True, "reply": msg, "chips": chips or [], "input": input,
            "job": job, "nav": nav, "actions": actions or [], "state": state or {}}


KID_SUBJECT = "class3-maths"   # the kids product's single live subject (Grade-3 Maths)


def _chat_step(role: str, state: dict, inp: str, db: Session, student, kids: bool = False):
    """One conversational turn. Returns the reply dict; state is echoed for the client to hold.

    `kids` (kids-education.trigunai.com host) makes the flow KID-ONLY: it never offers other
    exams/subjects — the subject is locked to Grade-3 Maths and the chat jumps straight to the
    book chapters. The DATA + POOL are shared/common; only the conversational FLOW is scoped."""
    st = dict(state or {})
    node = st.get("node", "intro")
    inp = (inp or "").strip()
    teacher = role == "teacher"
    who = student.name or ("teacher" if teacher else "there")

    # ---- global chip routing (a chip value can jump the flow regardless of node) ----
    if inp.startswith("intent:"):
        node = inp.split(":", 1)[1]
    elif inp.startswith("subj:"):
        st["subject"] = inp.split(":", 1)[1]
        st["subject_label"] = examgen.RAG_SUBJECTS.get(st["subject"], {}).get("label", "Test")
        st["chapters"] = []
        node = "chapters"
    elif inp == "full":
        st["chapters"] = ["__FULL__"]; node = "difficulty"
    elif inp.startswith("chap:"):
        ch = inp.split(":", 1)[1]
        chs = [c for c in st.get("chapters", []) if c != "__FULL__"]
        if ch in chs:
            chs.remove(ch)
        else:
            chs.append(ch)
        st["chapters"] = chs
        node = "chapters"
    elif inp == "chapdone":
        node = "difficulty"
    elif inp.startswith("diff:"):
        st["diff"] = inp.split(":", 1)[1]; node = "count"
    elif inp.startswith("n:"):
        st["n"] = int(inp.split(":", 1)[1]); node = "confirm"
    elif inp == "go":
        node = "generate"
    elif inp == "restart":
        st = {}; node = "intro"
    # ---- KIDS worksheet-flow chips (curriculum-driven; ALL subjects, not just Maths) ----
    elif inp.startswith("ksubj:"):
        st["ksubject"] = inp.split(":", 1)[1]; st["kchapter"] = ""; node = "kids_chapters"
    elif inp.startswith("kchap:"):
        st["kchapter"] = inp.split(":", 1)[1]; node = "kids_count"
    elif inp == "kgo":
        st["kchapter"] = ""; node = "kids_count"
    elif inp.startswith("kn:"):
        st["kn"] = int(inp.split(":", 1)[1]); node = "kids_go"

    # ---- free text: try to route to an intent / subject at the top of the flow ----
    elif inp and node in ("intro", "make_test"):
        sid = examgen.match_subject(inp)
        low = inp.lower()
        if sid:
            st["subject"] = sid; st["subject_label"] = examgen.RAG_SUBJECTS[sid]["label"]
            st["chapters"] = []; node = "chapters"
        elif any(w in low for w in ("weak", "report", "progress", "how am i", "class")):
            node = "class_weak" if teacher else "my_progress"
        else:
            node = "make_test"

    # ---- KIDS worksheet flow: whenever the (kid) flow would ask "which subject?" or pick an
    # examgen subject, route into the curriculum-driven picker instead — ALL kids subjects
    # (Maths, EVS, English, GK, Hindi), each → topic → an adaptive worksheet. The MCQ/examgen
    # flow is bypassed for kids; data/curriculum are shared, the FLOW is kid-scoped. ----
    if kids and node in ("make_test", "chapters"):
        node = "kids_subject"

    if kids and node == "kids_subject":
        return _reply("Which subject shall we practise? 🎒 Tap one!",
                      chips=_kids_subject_chips(), input=True, state={**st, "node": "kids_subject"})
    if kids and node == "kids_chapters":
        subj = st.get("ksubject", "Mathematics")
        picked = f" · picked: {st['kchapter']}" if st.get("kchapter") else ""
        return _reply(f"<b>{_kids_subject_label(subj)}</b> — pick a topic, or ✨ Mixed practice!{picked}",
                      chips=_kids_chapter_chips(subj), input=True, state={**st, "node": "kids_chapters"})
    if kids and node == "kids_count":
        where = st.get("kchapter") or "Mixed practice"
        chips = [{"label": f"{k} questions", "value": f"kn:{k}"} for k in (5, 8, 10, 15)]
        return _reply(f"How many questions for <b>{where}</b>? 🔢", chips=chips,
                      state={**st, "node": "kids_count"})
    if kids and node == "kids_go":
        subj = st.get("ksubject", "Mathematics"); ch = st.get("kchapter", ""); nq = int(st.get("kn") or 8)
        nav = f"/exam-prep/worksheet?subject={quote(subj)}&chapter={quote(ch)}&n={nq}"
        return _reply(f"Opening your {nq}-question worksheet — let's go! ✏️", nav=nav, state={"node": "intro"})

    # ══════════ nodes ══════════
    if node == "intro":
        if kids:
            msg = ("Hi superstar! 🦊 I'm Acharya. Want a fun practice worksheet, or to see how you're doing? "
                   "Tap a button below! 🎈")
            chips = [{"label": "✍️ Make me a worksheet", "value": "intent:make_test"},
                     {"label": "⚡ Practise my tricky bits", "value": "intent:smart"},
                     {"label": "📊 How am I doing?", "value": "intent:my_progress"}]
            return _reply(msg, chips=chips, input=True, state={**st, "node": "intro"})
        if teacher:
            msg = (f"Namaste 🙏 I'm Acharya. Tell me what you need — I'll build it. "
                   f"You can type it, or tap below.")
            chips = [{"label": "✍️ Make a test", "value": "intent:make_test"},
                     {"label": "🎯 Who's weak in my class?", "value": "intent:class_weak"}]
        else:
            msg = (f"Namaste 🙏 I'm Acharya. Want a fresh practice test, or your progress? "
                   f"Just tell me — e.g. \"NEET Biology, genetics, 10 questions\".")
            chips = [{"label": "✍️ Make me a test", "value": "intent:make_test"},
                     {"label": "⚡ Practise my weak spots", "value": "intent:smart"},
                     {"label": "📊 How am I doing?", "value": "intent:my_progress"}]
        return _reply(msg, chips=chips, input=True, state={**st, "node": "intro"})

    if node in ("make_test",):
        return _reply("Which subject? (JEE, NEET, CBSE Class 10 &amp; 12, Commerce, Banking &amp; UPSC are ready.)",
                      chips=_subject_chips(db, None if teacher else student),
                      input=True, state={**st, "node": "make_test"})

    if node == "chapters":
        sel = [c for c in st.get("chapters", []) if c != "__FULL__"]
        picked = (" · picked: " + ", ".join(sel)) if sel else ""
        chips = _chapter_chips(st["subject"])
        if sel:
            chips = chips + [{"label": "✅ Done — next", "value": "chapdone"}]
        return _reply(f"<b>{st['subject_label']}</b> — tap the chapters to cover, or ✨ Full subject.{picked}",
                      chips=chips, input=True, state={**st, "node": "chapters"})

    if node == "difficulty":
        return _reply("How hard should it be?", chips=_diff_chips(st["subject"]),
                      state={**st, "node": "difficulty"})

    if node == "count":
        opts = [5, 10, 15, 20] if teacher else [5, 10, 15]
        chips = [{"label": f"{k} questions", "value": f"n:{k}"} for k in opts]
        return _reply("How many questions?", chips=chips, state={**st, "node": "count"})

    if node == "confirm":
        sel = [c for c in st.get("chapters", []) if c != "__FULL__"]
        where = "full subject" if "__FULL__" in st.get("chapters", []) or not sel else ", ".join(sel)
        st["title"] = f"{st['subject_label']} — {where[:40]}"
        diff_word = {v: k for k in ("easy", "mix", "hard")
                     for v in [examgen.difficulty_ladder(st["subject"])[k]]}.get(st.get("diff"), st.get("diff"))
        tail = ("I'll write fresh questions and give you a share link + printable."
                if teacher else "I'll write fresh questions for you.")
        return _reply(f"Ready: <b>{st['subject_label']}</b> · {where} · {diff_word} · <b>{st['n']} questions</b>. {tail}",
                      chips=[{"label": "▶️ Make it", "value": "go"},
                             {"label": "↺ Start over", "value": "restart"}],
                      state={**st, "node": "confirm"})

    if node == "generate":
        subject = st.get("subject")
        chs = st.get("chapters", [])
        if "__FULL__" in chs or not [c for c in chs if c != "__FULL__"]:
            all_ch = [c["chapter"] for c in examgen.chapters_for_ui(subject)]
            selections = [(c, None) for c in all_ch]
        else:
            selections = [(c, None) for c in chs if c != "__FULL__"]
        diff = st.get("diff") or examgen.difficulty_ladder(subject)["mix"]
        n = int(st.get("n") or 5)
        title = st.get("title") or examgen.RAG_SUBJECTS[subject]["label"]
        if teacher:
            token = _kick_teacher_job(db, student.id, {"subject": subject,
                     "selections": [[c, co] for c, co in selections], "diff": diff, "n": n, "title": title})
            return _reply("Writing your test now — fresh questions, never repeated. Give me a moment… ✍️",
                          job=token, state={"node": "intro"})
        else:
            sel = "|".join(f"{c}::" for c, _ in selections[:6])
            nav = (f"/exam-prep/test?src=examgen&subject={quote(subject)}&sel={quote(sel)}"
                   f"&diff={quote(diff)}&n={n}&title={quote(title)}")
            return _reply("Opening your test — I'll write the questions as it loads. All the best! ✍️",
                          nav=nav, state={"node": "intro"})

    if node == "smart":
        return _reply("Building a set from your weakest topics… ⚡", nav="/exam-prep/smart",
                      state={"node": "intro"})

    if node == "my_progress":
        stx = _prep_stats(db, student)
        if not stx["has_data"]:
            return _reply("You haven't taken a test yet — do one and I'll map exactly where you're weak. Ready?",
                          chips=[{"label": "✍️ Make me a test", "value": "intent:make_test"}],
                          state={"node": "intro"})
        focus = ", ".join(s.concept for s in stx["focus"]) or "nothing major"
        msg = (f"You're at <b>{stx['mastery']}% mastery</b> across {stx['tests']} test(s). "
               f"This week: {stx['q_week']} questions, {stx['acc_week']}% accuracy. "
               f"<b>Focus next:</b> {focus}.")
        return _reply(msg, chips=[{"label": "⚡ Practise those now", "value": "intent:smart"},
                                  {"label": "📈 Full report", "value": "nav:/exam-prep/report"},
                                  {"label": "✍️ New test", "value": "intent:make_test"}],
                      state={"node": "intro"})

    if node == "class_weak":
        tests = db.query(ClassTest).filter_by(teacher_id=student.id).all()
        tids = [t.id for t in tests]
        sits = (db.query(ClassSitting).filter(ClassSitting.class_test_id.in_(tids)).all() if tids else [])
        if not sits:
            return _reply("No student results yet. Make a test, share the link, and as students finish "
                          "I'll show you exactly who's weak in what.",
                          chips=[{"label": "✍️ Make a test", "value": "intent:make_test"}],
                          state={"node": "intro"})
        wc = {}
        for s in sits:
            for w in (s.weak_topics or []):
                wc[w] = wc.get(w, 0) + 1
        top = sorted(wc.items(), key=lambda kv: -kv[1])[:5]
        weak_line = ", ".join(f"{t} ({c})" for t, c in top) or "—"
        names = len({s.student_name for s in sits})
        msg = (f"Across {len(sits)} result(s) from {names} student(s), the class is weakest in: "
               f"<b>{weak_line}</b>. Teach these next.")
        return _reply(msg, chips=[{"label": "📊 Full dashboard", "value": "nav:/teacher/dashboard"},
                                  {"label": "✍️ Make a test on the weak topic", "value": "intent:make_test"}],
                      state={"node": "intro"})

    # fallback
    return _reply("Tell me what you'd like — a test, or your progress.",
                  chips=([{"label": "✍️ Make a test", "value": "intent:make_test"}]),
                  input=True, state={"node": "intro"})


@app.post("/api/chat/{role}")
async def chat_api(request: Request, role: str, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    if role == "teacher" and not student.is_teacher:
        return JSONResponse({"ok": False, "error": "not a teacher"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        body = {}
    state = body.get("state") or {}
    inp = body.get("input") or ""
    # a chip can also carry a direct nav (value "nav:/path")
    if isinstance(inp, str) and inp.startswith("nav:"):
        return JSONResponse(_reply("Opening that for you…", nav=inp.split(":", 1)[1], state={"node": "intro"}))
    host = (request.headers.get("host") or "").split(":")[0].lower()
    kids = host in KIDS_HOSTS
    return JSONResponse(_chat_step("teacher" if role == "teacher" else "student",
                                   state, inp, db, student, kids=kids))


@app.get("/teacher/chat", response_class=HTMLResponse)
def teacher_chat(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return RedirectResponse("/teacher", status_code=302)
    return templates.TemplateResponse(request, "chat_console.html", {
        "student": teacher, "role": "teacher", "home": "/teacher",
        "title": "Acharya — Teacher", "sub": teacher.institute or "for teachers"})


@app.get("/exam-prep/chat", response_class=HTMLResponse)
def student_chat(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep/quick", status_code=302)
    if not has_assessment_access(db, student):
        return RedirectResponse("/exam-prep/upgrade", status_code=302)
    return templates.TemplateResponse(request, "chat_console.html", {
        "student": student, "role": "student", "home": "/exam-prep/dashboard",
        "title": "Acharya", "sub": "your exam-prep coach"})


@app.post("/logout")
@app.get("/logout")
def logout(request: Request, next: str = ""):
    # Send them back to the SURFACE they logged out from, not their role flag — a dual-role account
    # (is_teacher=True) can be using the student area, so keying off is_teacher wrongly bounced students
    # to /teacher. Teacher pages pass ?next=/teacher; everything else defaults to the student landing.
    dest = next if next in ("/teacher", "/exam-prep") else "/exam-prep"
    request.session.clear()
    return RedirectResponse(dest, status_code=302)


# ---------- subscriptions (Razorpay) ----------
def _sub_view(student: Student) -> dict:
    st = student.sub_status or "none"
    nocard = (st == "trialing" and not student.rzp_subscription_id)
    days_left = 0
    if student.trial_end:
        secs = (student.trial_end - datetime.utcnow()).total_seconds()
        days_left = max(0, int((secs + 86399) // 86400))  # ceil
    return {
        "status": st,
        "has_access": has_access(student),
        "trial_end": student.trial_end,
        "current_period_end": student.current_period_end,
        "price": settings.PRICE_INR,
        "trial_days": settings.TRIAL_DAYS,
        "configured": billing.configured(),
        "enabled": settings.SUBS_ENABLED,
        "nocard_trial": nocard and _trial_active(student),   # active no-card trial
        "expired_trial": nocard and not _trial_active(student),
        "days_left": days_left,
        # offer "skip payment" only to someone who has never started a trial/sub
        "can_skip": st == "none" and student.trial_end is None and not student.rzp_subscription_id,
    }


@app.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    return templates.TemplateResponse(request, "pricing.html", {
        "student": student,
        "sub": _sub_view(student) if student else None,
        "price": settings.PRICE_INR, "trial_days": settings.TRIAL_DAYS,
        "courses": [c for c in COURSES if c["ready"]],
        "jsonld": seo.pricing_jsonld(),
    })


@app.post("/api/subscribe")
async def api_subscribe(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return JSONResponse({"error": "login required", "redirect": "/login"}, status_code=401)
    if has_access(student) and student.sub_status in ("active", "trialing", "grandfathered"):
        return JSONResponse({"error": "already subscribed", "redirect": "/dashboard"}, status_code=400)
    if not billing.configured():
        return JSONResponse({"error": "Billing is not configured yet."}, status_code=503)
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    contact = (body.get("contact") or "").strip()
    # If they already used their one free trial (e.g. a no-card trial that expired), no second
    # trial — charge immediately (trial_days=0). Otherwise the normal 7-day trial.
    already_trialed = student.trial_end is not None
    try:
        sub = await run_in_threadpool(
            billing.create_subscription, student.name, student.email, student.course, contact,
            student.rzp_customer_id, 0 if already_trialed else None,
        )
    except Exception as exc:
        return JSONResponse({"error": f"Could not start subscription: {exc}"}, status_code=502)
    student.rzp_subscription_id = sub["id"]
    student.rzp_customer_id = sub["customer_id"]
    student.sub_status = "created"
    db.commit()
    # Prefer the embedded Checkout (opens on our page, then redirects to /dashboard); fall
    # back to the hosted short_url if the Checkout script can't load.
    return JSONResponse({
        "ok": True,
        "subscription_id": sub["id"],
        "key_id": settings.RZP_KEY_ID,
        "redirect": sub["short_url"],          # fallback
        "name": student.name or student.email.split("@")[0],
        "email": student.email,
    })


@app.get("/billing/return")
def billing_return(request: Request, db: Session = Depends(get_db)):
    """Razorpay sends the user back here after they authorise the mandate. We optimistically
    mark them 'trialing' so they get in immediately; the webhook is the real source of truth."""
    student = current_student(request, db)
    if student and student.sub_status in ("created",):
        student.sub_status = "trialing"
        if not student.trial_end:
            student.trial_end = datetime.utcfromtimestamp(int(time.time()) + settings.TRIAL_DAYS * 86400)
        db.commit()
        notify.notify_admin(f"💳 Card trial started — {student.email} · {COURSE_TITLES.get(student.course, student.course)}")
    return RedirectResponse("/dashboard", status_code=302)


@app.post("/api/trial/skip")
def api_trial_skip(request: Request, db: Session = Depends(get_db)):
    """Start a 7-day NO-CARD trial. Full access now; locked after trial_end until they subscribe.
    One-time only — once a student has trialed (or subscribed), they must pay to continue."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"error": "login required", "redirect": "/login"}, status_code=401)
    if not settings.SUBS_ENABLED or student.is_admin or student.sub_status in ("active", "grandfathered"):
        return JSONResponse({"ok": True, "redirect": "/dashboard"})
    if student.trial_end is not None or student.rzp_subscription_id or (student.sub_status or "none") != "none":
        return JSONResponse({"error": "Your free trial is already used — subscribe to continue.",
                             "redirect": "/pricing"}, status_code=400)
    student.sub_status = "trialing"
    student.trial_end = datetime.utcnow() + timedelta(days=settings.TRIAL_DAYS)
    db.commit()
    notify.notify_admin(f"✨ No-card trial started — {student.email} · {COURSE_TITLES.get(student.course, student.course)}")
    return JSONResponse({"ok": True, "redirect": "/dashboard"})


# ---------- student assessment plan (₹199/mo) billing — a SEPARATE, parallel track ----------
def _assess_plan(student: Student):
    """Pick the Razorpay plan + price by role. Teachers/institutes → ₹999 plan; students → ₹249."""
    if getattr(student, "is_teacher", False) and settings.RZP_ASSESS_TEACHER_PLAN_ID:
        return settings.RZP_ASSESS_TEACHER_PLAN_ID, settings.ASSESS_TEACHER_PRICE_INR
    return settings.RZP_ASSESS_PLAN_ID, settings.ASSESS_PRICE_INR


def _assess_view(student: Student) -> dict:
    st = student.assess_status or "none"
    nocard = (st == "trialing" and not student.rzp_assess_subscription_id)
    active_trial = bool(student.assess_trial_end and student.assess_trial_end > datetime.utcnow())
    days_left = 0
    if student.assess_trial_end:
        secs = (student.assess_trial_end - datetime.utcnow()).total_seconds()
        days_left = max(0, int((secs + 86399) // 86400))
    plan_id, price = _assess_plan(student)
    is_teacher = bool(getattr(student, "is_teacher", False))
    return {"status": st, "price": price, "trial_days": settings.ASSESS_TRIAL_DAYS,
            "enabled": settings.ASSESS_ENABLED,
            "configured": billing._keys_ok() and bool(plan_id),
            "is_teacher": is_teacher, "role": "teacher" if is_teacher else "student",
            "active_trial": nocard and active_trial, "expired": nocard and not active_trial,
            "days_left": days_left, "key_id": settings.RZP_KEY_ID}


@app.get("/exam-prep/upgrade", response_class=HTMLResponse)
def exam_prep_upgrade(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    return templates.TemplateResponse(request, "exam_prep_upgrade.html",
                                      {"student": student, "sub": _assess_view(student)})


@app.post("/api/assess/subscribe")
async def api_assess_subscribe(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return JSONResponse({"error": "login required", "redirect": "/login"}, status_code=401)
    if student.assess_status == "active" or (student.assess_status == "trialing" and student.rzp_assess_subscription_id):
        return JSONResponse({"error": "already subscribed", "redirect": "/exam-prep"}, status_code=400)
    plan_id, _price = _assess_plan(student)
    if not (billing._keys_ok() and plan_id):
        return JSONResponse({"error": "Assessment billing is not configured yet."}, status_code=503)
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    contact = (body.get("contact") or "").strip()
    already_trialed = student.assess_trial_end is not None    # used their free trial → charge now (trial_days=0)
    plan_label = "assessment-teacher" if getattr(student, "is_teacher", False) and settings.RZP_ASSESS_TEACHER_PLAN_ID else "assessment"
    try:
        sub = await run_in_threadpool(
            billing.create_subscription, student.name, student.email, "exam-prep", contact,
            student.rzp_assess_customer_id, 0 if already_trialed else settings.ASSESS_TRIAL_DAYS,
            plan_id, None, {"email": student.email, "plan": plan_label},
        )
    except Exception as exc:
        return JSONResponse({"error": f"Could not start subscription: {exc}"}, status_code=502)
    student.rzp_assess_subscription_id = sub["id"]
    student.rzp_assess_customer_id = sub["customer_id"]
    student.assess_status = "created"
    db.commit()
    return JSONResponse({"ok": True, "subscription_id": sub["id"], "key_id": settings.RZP_KEY_ID,
                         "redirect": sub["short_url"], "name": student.name or student.email.split("@")[0],
                         "email": student.email})


@app.get("/billing/assess/return")
def billing_assess_return(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if student and student.assess_status == "created":
        student.assess_status = "trialing"
        db.commit()
        notify.notify_admin(f"💳 Assessment card trial started — {student.email}")
    return RedirectResponse("/exam-prep", status_code=302)


def _apply_assess_webhook(db: Session, student: Student, entity: dict):
    """Mirror of the course webhook logic, but on the assess_* columns."""
    new_status = billing.map_status(entity.get("status", ""))
    if new_status != "none":
        old = student.assess_status
        student.assess_status = new_status
        if new_status != old:
            if new_status == "active":
                _p = settings.ASSESS_TEACHER_PRICE_INR if getattr(student, "is_teacher", False) else settings.ASSESS_PRICE_INR
                _who = "TEACHER" if getattr(student, "is_teacher", False) else "student"
                notify.notify_admin(f"💰 New ASSESSMENT subscriber ({_who}) — {student.email} · ₹{_p}/mo")
            elif new_status == "cancelled":
                notify.notify_admin(f"⚠️ Assessment subscription cancelled — {student.email}")
    ce = billing.ts_to_dt(entity.get("current_end"))
    if ce:
        student.assess_period_end = ce
    se = billing.ts_to_dt(entity.get("start_at") or entity.get("charge_at"))
    if se and not student.assess_trial_end:
        student.assess_trial_end = se
    db.commit()
    return JSONResponse({"ok": True, "track": "assess", "status": student.assess_status})


@app.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")
    if not billing.verify_webhook(raw, sig):
        raise HTTPException(status_code=400, detail="bad signature")
    import json as _json
    evt = _json.loads(raw.decode("utf-8"))
    entity = (((evt.get("payload") or {}).get("subscription") or {}).get("entity")) or {}
    sub_id = entity.get("id")
    if not sub_id:
        return JSONResponse({"ok": True, "ignored": evt.get("event")})
    student = db.query(Student).filter_by(rzp_subscription_id=sub_id).first()
    if not student:
        astudent = db.query(Student).filter_by(rzp_assess_subscription_id=sub_id).first()
        if astudent:                                    # a ₹199 assessment-plan event
            return _apply_assess_webhook(db, astudent, entity)
        return JSONResponse({"ok": True, "no_match": sub_id})
    new_status = billing.map_status(entity.get("status", ""))
    if new_status != "none":
        old_status = student.sub_status
        student.sub_status = new_status
        if new_status != old_status:
            if new_status == "active":
                notify.notify_admin(f"💰 New paying subscriber — {student.email} · {COURSE_TITLES.get(student.course, student.course)} · ₹{settings.PRICE_INR}/mo")
            elif new_status == "cancelled":
                notify.notify_admin(f"⚠️ Subscription cancelled — {student.email}")
    ce = billing.ts_to_dt(entity.get("current_end"))
    if ce:
        student.current_period_end = ce
    se = billing.ts_to_dt(entity.get("start_at") or entity.get("charge_at"))
    if se and not student.trial_end:
        student.trial_end = se
    db.commit()
    return JSONResponse({"ok": True, "event": evt.get("event"), "status": student.sub_status})


@app.get("/account", response_class=HTMLResponse)
def account(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "account.html", {
        "student": student, "sub": _sub_view(student),
        "stats": gamify.stats(db, student.id),
    })


@app.post("/api/subscription/cancel")
async def api_cancel(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return JSONResponse({"error": "login required"}, status_code=401)
    if not student.rzp_subscription_id or not billing.configured():
        return JSONResponse({"error": "no active subscription"}, status_code=400)
    try:
        ent = await run_in_threadpool(billing.cancel_subscription, student.rzp_subscription_id, True)
    except Exception as exc:
        return JSONResponse({"error": f"Cancel failed: {exc}"}, status_code=502)
    # Trial cancels immediately; a paid sub stays accessible until current_period_end.
    student.sub_status = billing.map_status(ent.get("status", "cancelled")) if isinstance(ent, dict) else "cancelled"
    db.commit()
    return JSONResponse({"ok": True, "status": student.sub_status})


# ---------- dashboard ----------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    if not has_access(student):
        return RedirectResponse("/pricing")

    modules = db.query(Module).filter_by(course=student.course).order_by(Module.week).all()
    lessons_by_module = {}
    for l in db.query(Lesson).order_by(Lesson.sort, Lesson.id).all():
        lessons_by_module.setdefault(l.module_id, []).append(l)
    done_lessons = {
        lp.lesson_id for lp in db.query(LessonProgress).filter_by(
            student_id=student.id, status="done"
        ).all()
    }
    cw = current_week()
    rows = []
    for m in modules:
        mlessons = lessons_by_module.get(m.id, [])
        lesson_views = [{
            "slug": l.slug,
            "title": l.title,
            "available": bool(l.available),
            "done": l.id in done_lessons,
        } for l in mlessons]
        rows.append({
            "week": m.week, "title": m.title, "summary": m.summary,
            "date": m.session_date, "code": m.code,
            "lessons": lesson_views,
            # back-compat single-lesson fields (first lesson)
            "lesson_slug": lesson_views[0]["slug"] if lesson_views else None,
            "lesson_available": lesson_views[0]["available"] if lesson_views else False,
            "lesson_done": all(lv["done"] for lv in lesson_views) if lesson_views else False,
            "state": "done" if m.week < cw else ("current" if m.week == cw else "upcoming"),
        })

    facts = personalize.get_facts(db, student.id)
    return templates.TemplateResponse(request, "dashboard.html", {
        "student": student, "rows": rows,
        "current_week": cw, "stats": gamify.stats(db, student.id),
        "greeting": personalize.greeting(facts),
        "ask": (personalize.next_questions(facts, 1) or [None])[0],
        "starter_repo": settings.STARTER_REPO,
        "chat_url": chat_url_for(student.email, student.course),
        "sub": _sub_view(student),
        "is_live": is_live_student(student),
        "upgrade_url": live_upgrade_url(student),
    })


@app.get("/admin/set-course")
def admin_set_course(request: Request, email: str, course: str, db: Session = Depends(get_db)):
    """Admin-only: set a student's course. /admin/set-course?email=x@y.com&course=remote-swe"""
    me = current_student(request, db)
    if not me or not me.is_admin:
        raise HTTPException(status_code=403)
    s = db.query(Student).filter_by(email=email.lower().strip()).first()
    if not s:
        return JSONResponse({"error": "no such student"}, status_code=404)
    s.course = course.strip()
    db.commit()
    return JSONResponse({"ok": True, "email": s.email, "course": s.course})


@app.get("/workbook/{week}", response_class=HTMLResponse)
def workbook(request: Request, week: int, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    if not has_access(student):
        return RedirectResponse("/pricing")
    tasks = db.query(WorkbookTask).filter_by(week=week).order_by(WorkbookTask.sort).all()
    done = {
        tc.task_id for tc in db.query(TaskCompletion).filter_by(student_id=student.id).all()
    }
    module = db.query(Module).filter_by(week=week).first()
    return templates.TemplateResponse(request, "workbook.html", {
        "student": student, "week": week, "module": module,
        "tasks": tasks, "done": done, "stats": gamify.stats(db, student.id),
        "starter_repo": settings.STARTER_REPO,
    })


# ---------- coding setup chooser ----------
@app.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    if not has_access(student):
        return RedirectResponse("/pricing")
    facts = personalize.get_facts(db, student.id)
    return templates.TemplateResponse(request, "setup.html", {
        "student": student, "stats": gamify.stats(db, student.id),
        "options": catalog.CODING_OPTIONS, "chosen": facts.get("coding_setup"),
        "starter_repo": settings.STARTER_REPO,
    })


@app.post("/api/setup/choose")
async def setup_choose(request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    body = await request.json()
    choice = (body.get("choice") or "").strip()
    if choice not in catalog.VALID_IDS:
        raise HTTPException(400, "Unknown option")
    is_new = not db.query(LearnerFact).filter_by(student_id=student.id, key="coding_setup").first()
    personalize.capture_fact(db, student.id, "coding_setup", choice, source="lesson")
    pts = gamify.award(db, student.id, "setup_chosen", points=10) if is_new else 0
    return JSONResponse({"ok": True, "chosen": choice, "points": pts,
                         "stats": gamify.stats(db, student.id)})


# ---------- lesson player ----------
@app.get("/lesson/{slug}", response_class=HTMLResponse)
def lesson_player(request: Request, slug: str, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    if not has_access(student):
        return RedirectResponse("/pricing")
    lesson = db.query(Lesson).filter_by(slug=slug).first()
    if not lesson or not lesson.available:
        raise HTTPException(404, "Lesson not available yet")
    path = BASE / "lessons" / f"{slug}.html"
    if not path.exists():
        raise HTTPException(404, "Lesson content missing")
    html = path.read_text(encoding="utf-8")
    inject = f'<script>window.LMS={{slug:"{slug}",api:"/api/lesson/{slug}"}};</script>'
    html = html.replace("</head>", inject + "</head>", 1)
    return HTMLResponse(html)


# ---------- gamification API ----------
def _anon_id(student_id: int) -> str:
    """Stable, non-reversible per-student pseudonym for the training export."""
    return hashlib.sha256(f"{settings.SECRET_KEY}|{student_id}".encode()).hexdigest()[:40]


def log_learning_event(db, student, *, surface="web", concept_id="", lesson_slug="",
                       step_index=0, step_type="", action="attempt", outcome="",
                       attempt_no=1, chosen="", intervention="none", latency_ms=0):
    """Persist one learning_events row — the loop's raw material. Gated behind
    LOOP_CAPTURE_ENABLED + the student's data_loop_consent. Never raises into the request."""
    if not settings.LOOP_CAPTURE_ENABLED:
        return
    if not getattr(student, "data_loop_consent", True):
        return
    try:
        db.add(LearningEvent(
            student_id=student.id, student_anon=_anon_id(student.id),
            course=student.course or "", surface=surface,
            concept_id=(concept_id or lesson_slug)[:80], lesson_slug=lesson_slug[:80],
            step_index=int(step_index or 0), step_type=(step_type or "")[:20],
            action=action[:16], outcome=(outcome or "")[:10], attempt_no=int(attempt_no or 1),
            chosen=str(chosen)[:40], intervention=(intervention or "none")[:12],
            latency_ms=int(latency_ms or 0),
        ))
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[loop] event skip: {exc}")


@app.post("/api/lesson/{slug}/progress")
async def lesson_progress(slug: str, request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    lesson = db.query(Lesson).filter_by(slug=slug).first()
    if not lesson:
        raise HTTPException(404)
    lp = db.query(LessonProgress).filter_by(student_id=student.id, lesson_id=lesson.id).first()
    if not lp:
        lp = LessonProgress(student_id=student.id, lesson_id=lesson.id, status="in_progress", best_score=0)
        db.add(lp)
        db.commit()
        db.refresh(lp)
    body = await request.json()
    action = body.get("action", "attempt")
    correct = bool(body.get("correct"))
    pts = 0
    if action == "attempt" and correct:
        pts = gamify.award(db, student.id, "step_correct", ref=f"{slug}#{body.get('step')}")
    log_learning_event(
        db, student, surface="web", lesson_slug=slug,
        concept_id=body.get("concept", ""), step_index=body.get("step", 0),
        step_type=body.get("type", ""), action=action,
        outcome=("na" if action != "attempt" else ("correct" if correct else "wrong")),
        attempt_no=body.get("attempt_no", 1), chosen=body.get("chosen", ""),
        intervention=body.get("intervention", "none"), latency_ms=body.get("latency_ms", 0),
    )
    streak = gamify.touch_streak(db, student.id)
    return JSONResponse({"points": pts, "streak": streak, "stats": gamify.stats(db, student.id)})


@app.post("/api/lesson/{slug}/complete")
async def lesson_complete(slug: str, request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    lesson = db.query(Lesson).filter_by(slug=slug).first()
    if not lesson:
        raise HTTPException(404)
    body = await request.json()
    score = int(body.get("score", 0))
    perfect = bool(body.get("perfect"))

    lp = db.query(LessonProgress).filter_by(student_id=student.id, lesson_id=lesson.id).first()
    if not lp:
        lp = LessonProgress(student_id=student.id, lesson_id=lesson.id, status="in_progress", best_score=0)
        db.add(lp)
    fresh = lp.status != "done"
    lp.status = "done"
    lp.best_score = max(lp.best_score or 0, score)
    if fresh:
        lp.completed_at = now()
    db.commit()

    log_learning_event(db, student, surface="web", lesson_slug=slug, action="complete",
                       outcome=("correct" if perfect else "partial"), chosen=str(score))

    awarded = 0
    badge = None
    if fresh:
        awarded += gamify.award(db, student.id, "lesson_complete", ref=slug)
        if perfect:
            awarded += gamify.award(db, student.id, "lesson_perfect", ref=slug)
        if gamify.grant_badge(db, student.id, "first_steps"):
            badge = "first_steps"
        if slug == "what-is-an-agent":
            gamify.grant_badge(db, student.id, "loop_master")
    streak = gamify.touch_streak(db, student.id)
    return JSONResponse({
        "awarded": awarded, "fresh": fresh, "badge": badge,
        "celebrate": "lesson", "streak": streak, "stats": gamify.stats(db, student.id),
    })


@app.post("/api/workbook/task/{task_id}/toggle")
def workbook_toggle(task_id: int, request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    task = db.get(WorkbookTask, task_id)
    if not task:
        raise HTTPException(404)
    tc = db.query(TaskCompletion).filter_by(student_id=student.id, task_id=task_id).first()
    if tc:
        db.delete(tc)
        db.commit()
        return JSONResponse({"done": False, "stats": gamify.stats(db, student.id)})
    reason = "bring_item" if task.is_bring else "workbook_task"
    pts = gamify.award(db, student.id, reason, ref=f"wk{task.week}:{task_id}")
    db.add(TaskCompletion(student_id=student.id, task_id=task_id, gems_awarded=pts))
    db.commit()
    streak = gamify.touch_streak(db, student.id)
    return JSONResponse({
        "done": True, "points": pts, "celebrate": ("bring" if task.is_bring else "coin"),
        "streak": streak, "stats": gamify.stats(db, student.id),
    })


@app.get("/api/me/stats")
def me_stats(request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    return JSONResponse(gamify.stats(db, student.id))


# ---------- personalization (progressive profiling) ----------
@app.post("/api/profile/capture")
async def profile_capture(request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    body = await request.json()
    key = (body.get("key") or "").strip()
    value = (body.get("value") or "").strip()
    source = body.get("source") or "prompt"
    is_new = not db.query(LearnerFact).filter_by(student_id=student.id, key=key).first()
    ok = personalize.capture_fact(db, student.id, key, value, source)
    pts = 0
    if ok and is_new:
        pts = gamify.award(db, student.id, "profile_fact", ref=key, points=5)
        gamify.touch_streak(db, student.id)
        if key == "name" and value:
            student.name = value
            db.commit()
    facts = personalize.get_facts(db, student.id)
    return JSONResponse({
        "ok": ok, "points": pts,
        "next": (personalize.next_questions(facts, 1) or [None])[0],
        "stats": gamify.stats(db, student.id),
    })


@app.get("/api/profile")
def profile_get(request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    facts = personalize.get_facts(db, student.id)
    return JSONResponse({"facts": facts, "context": personalize.build_learner_context(facts)})


# ---------- the TrigunAI guide (LLM tutor) ----------
@app.post("/api/tutor/chat")
async def tutor_chat(request: Request, db: Session = Depends(get_db)):
    student = require_student(request, db)
    if not has_access(student):
        return JSONResponse({"error": "subscription required", "redirect": "/pricing"}, status_code=402)
    body = await request.json()
    history = body.get("history") or []
    problem = (body.get("problem") or "")[:2000]
    # sanitize history to role/content strings
    clean = [
        {"role": ("assistant" if m.get("role") == "assistant" else "user"),
         "content": str(m.get("content", ""))[:1500]}
        for m in history if m.get("content")
    ][-12:]
    facts = personalize.get_facts(db, student.id)
    reply = await run_in_threadpool(
        tutor.chat, clean, personalize.build_learner_context(facts), problem
    )
    return JSONResponse({"reply": reply, "llm": tutor.available()})


# ---------- admin ----------
def require_admin(request: Request, db: Session) -> Student:
    s = current_student(request, db)
    if not s or not s.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return s


def _student_rows(db: Session):
    cw = current_week()
    rows = []
    for s in db.query(Student).order_by(Student.enrolled_at).all():
        st = gamify.stats(db, s.id)
        lessons_done = db.query(LessonProgress).filter_by(student_id=s.id, status="done").count()
        tasks_done = db.query(TaskCompletion).filter_by(student_id=s.id).count()
        rows.append({
            "id": s.id, "email": s.email, "name": s.name or "—",
            "is_admin": s.is_admin, "gems": st["gems"], "level": st["level"],
            "streak": st["streak"], "longest": st["longest"], "badges": len(st["badges"]),
            "lessons_done": lessons_done, "tasks_done": tasks_done,
            "last_active": s.last_active_at.strftime("%d %b %H:%M") if s.last_active_at else "—",
            "enrolled": s.enrolled_at.strftime("%d %b") if s.enrolled_at else "—",
        })
    return rows, cw


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
    if not student.is_admin:
        raise HTTPException(403, "Admins only")
    rows, cw = _student_rows(db)
    reqs = db.query(CourseRequest).order_by(CourseRequest.created_at.desc()).limit(60).all()
    req_pending = db.query(CourseRequest).filter_by(status="requested").count()
    return templates.TemplateResponse(request, "admin.html", {
        "student": student, "rows": rows, "current_week": cw,
        "stats": gamify.stats(db, student.id),
        "m": analytics.metrics(db), "course_titles": COURSE_TITLES,
        "course_requests": reqs, "req_pending": req_pending,
    })


@app.get("/admin/api/students")
def admin_students(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    rows, _ = _student_rows(db)
    return JSONResponse(rows)


@app.get("/admin/api/pulse")
def admin_pulse(key: str = "", db: Session = Depends(get_db)):
    """Read-only campaign/funnel command-center payload for the `trigunai-campaign-tracker`
    skill. Gated by a shared key (no session) so it can be curled from a daily script.
    Tracks EVERY signup/login regardless of source. See app/analytics.py:pulse()."""
    if not settings.PULSE_KEY or key != settings.PULSE_KEY:
        raise HTTPException(403, "bad or missing key")
    return JSONResponse(analytics.pulse(db))


@app.get("/admin/api/pulse/student")
def admin_pulse_student(id: int, key: str = "", db: Session = Depends(get_db)):
    """Read-only per-student/teacher activity drill-down for the campaign-tracker dashboard.
    Same key gate as /admin/api/pulse. See app/analytics.py:student_detail()."""
    if not settings.PULSE_KEY or key != settings.PULSE_KEY:
        raise HTTPException(403, "bad or missing key")
    d = analytics.student_detail(db, id)
    if not d:
        raise HTTPException(404, "not found")
    return JSONResponse(d)


@app.get("/admin/api/login-link/{student_id}")
def admin_login_link(student_id: int, request: Request, db: Session = Depends(get_db)):
    """Generate a magic link for a student (so you can hand it over directly)."""
    require_admin(request, db)
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404)
    raw = issue_magic_token(db, s.email)
    return JSONResponse({"email": s.email, "link": f"{settings.BASE_URL}/auth/verify?token={raw}"})


@app.get("/admin/api/export.csv")
def admin_export(request: Request, db: Session = Depends(get_db)):
    require_admin(request, db)
    import csv
    import io
    rows, _ = _student_rows(db)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "email", "gems", "level", "streak", "longest",
                "badges", "lessons_done", "tasks_done", "last_active", "enrolled"])
    for r in rows:
        w.writerow([r["id"], r["name"], r["email"], r["gems"], r["level"], r["streak"],
                    r["longest"], r["badges"], r["lessons_done"], r["tasks_done"],
                    r["last_active"], r["enrolled"]])
    from fastapi.responses import Response
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=cohort_progress.csv"})


# ══════════════════════════════════════════════════════════════════════════════════════════════
# MOBILE API (native Acharya Flutter app) — thin, READ-ONLY JSON re-exposure of data the web
# templates already render. No new product logic; every value comes from the same helpers the web
# uses (_prep_stats, the report route, teacher_dashboard). The app authenticates with the SAME
# session cookie as the browser, so these ride on current_student/current_teacher. Prefix: /api/m/*
# ══════════════════════════════════════════════════════════════════════════════════════════════

def _concept_json(s) -> dict:
    return {"concept": s.concept, "subject": s.subject, "seen": s.seen,
            "pct": round(100 * s.correct / s.seen) if s.seen else 0}


def _smart_target(db, student, weakest) -> dict | None:
    """The single weakest concept → a ready-to-generate test spec (subject, sel, diff, title),
    identical to what the web Smart Practice builds. The app feeds it straight into generate."""
    for s in weakest:
        ch = _chapter_for_concept(s.subject, s.concept)
        if ch:
            mastery = (s.correct / s.seen) if s.seen else 0.0
            return {"subject": s.subject, "sel": f"{ch}::{s.concept}",
                    "diff": examgen.difficulty_for(s.subject, mastery), "title": s.concept}
    return None


@app.get("/api/m/me")
def m_me(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    topics = _student_topics(db, student)
    return JSONResponse({
        "ok": True, "email": student.email, "name": student.name or "",
        "is_teacher": bool(student.is_teacher), "institute": student.institute or "",
        "goal_id": _student_goal(db, student, topics),
        "days_left": _days_left(student), "has_access": has_assessment_access(db, student),
        "subjects": [examgen.match_subject(t.title, t.topic_key) for t in topics],
    })


@app.get("/api/m/home")
def m_home(request: Request, db: Session = Depends(get_db)):
    """Everything the native Today screen shows — from _prep_stats (all real, nothing invented)."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    st = _prep_stats(db, student)
    linked = _linked_teacher(db, student)
    institute = ((linked.institute if linked else "") or (linked.name if linked else "")) if linked else ""
    return JSONResponse({
        "ok": True,
        "mastery": st["mastery"], "goal": st["goal"], "goal_id": st["goal_id"],
        "tests": st["tests"], "has_data": st["has_data"], "streak": st["streak"],
        "q_week": st["q_week"], "acc_week": st["acc_week"], "chapters_week": st["chapters_week"],
        "trend": st["trend"],
        "focus": [_concept_json(s) for s in st["focus"]],
        "weakest": [_concept_json(s) for s in st["weakest"]],
        "strongest": _concept_json(st["strongest"]) if st["strongest"] else None,
        "due": [_concept_json(s) for s in st["due"][:5]],
        "days_left": _days_left(student), "has_access": has_assessment_access(db, student),
        "smart": _smart_target(db, student, st["weakest"]),
        "linked": bool(linked), "institute": institute,
        "assignments": _assignments_json(db, student),
    })


@app.get("/api/m/report")
def m_report(request: Request, db: Session = Depends(get_db)):
    """JSON twin of /exam-prep/report — SWOT, recommended difficulty, practise-next, trend."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    attempts = (db.query(TopicAttempt).filter_by(student_id=student.id)
                .order_by(TopicAttempt.taken_at.desc()).limit(50).all())
    stats = [s for s in db.query(ConceptStat).filter_by(student_id=student.id).all() if s.seen]

    def m(s):
        return s.correct / s.seen

    strong = sorted([s for s in stats if m(s) >= 0.75], key=m, reverse=True)
    shaky = sorted([s for s in stats if 0.5 <= m(s) < 0.75], key=m)
    weak = sorted([s for s in stats if m(s) < 0.5], key=m)
    graded = [a for a in attempts if a.total]
    avg = round(100 * sum(a.score for a in graded) / sum(a.total for a in graded)) if graded else 0
    overall = (sum(s.correct for s in stats) / sum(s.seen for s in stats)) if stats else 0
    tier, level_label = (("hard", "Hard") if overall >= 0.75 else
                         (("mix", "Mix (medium–hard)") if overall >= 0.5 else ("easy", "Medium")))
    suggestions = []
    for s in (weak + shaky)[:5]:
        ch = _chapter_for_concept(s.subject, s.concept)
        spec = None
        if ch:
            spec = {"subject": s.subject, "sel": f"{ch}::{s.concept}",
                    "diff": examgen.difficulty_ladder(s.subject)[tier], "title": s.concept}
        suggestions.append({"concept": s.concept, "subject": s.subject,
                            "pct": round(100 * m(s)), "seen": s.seen, "spec": spec})
    trend = [round(100 * a.score / a.total) for a in reversed(graded[:6]) if a.total]
    return JSONResponse({
        "ok": True, "tests": len(attempts), "avg": avg, "overall": round(100 * overall),
        "level_label": level_label,
        "strong": [{"c": s.concept, "p": round(100 * m(s)), "s": s.subject} for s in strong[:8]],
        "shaky": [{"c": s.concept, "p": round(100 * m(s)), "s": s.subject} for s in shaky[:8]],
        "weak": [{"c": s.concept, "p": round(100 * m(s)), "s": s.subject} for s in weak[:8]],
        "suggestions": suggestions, "trend": trend,
        "attempts": [{"id": a.id, "title": a.title, "score": a.score, "total": a.total,
                      "subject": a.subject} for a in attempts[:20]],
    })


@app.get("/api/m/papers")
def m_papers(request: Request, db: Session = Depends(get_db)):
    """The mock test series for the student's goal, with their best score on each (native)."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    goal_id = _student_goal(db, student) or examgen.DEFAULT_GOAL
    ready = db.query(MockPaper).filter_by(status="ready").order_by(MockPaper.code).all()
    papers = [p for p in ready if _paper_goal_id(p.subject) == goal_id]
    best = {}
    if papers:
        pids = {p.id for p in papers}
        for a in (db.query(PaperAttempt).filter_by(student_id=student.id)
                  .filter(PaperAttempt.submitted_at.isnot(None)).all()):
            if a.paper_id in pids and (a.paper_id not in best or a.score > best[a.paper_id].score):
                best[a.paper_id] = a
    out = []
    for p in papers:
        b = best.get(p.id)
        out.append({"id": p.id, "code": p.code, "title": p.title or p.code,
                    "minutes": p.minutes, "max_marks": p.max_marks,
                    "n": len(p.questions or []),
                    "done": b is not None,
                    "score": b.score if b else None})
    return JSONResponse({"ok": True, "goal": goal_id,
                         "kind": mockpaper.paper_kind(goal_id), "papers": out})


def _safe_paper_q(q: dict) -> dict:
    return {"n": q.get("n"), "section": q.get("section"), "qtype": q.get("qtype"),
            "marks": q.get("marks"), "neg": q.get("neg"), "stem": q.get("stem", ""),
            "options": q.get("options") or [], "figure": q.get("figure"), "chapter": q.get("chapter")}


@app.get("/api/m/paper/{paper_id}")
def m_paper_start(paper_id: int, request: Request, db: Session = Depends(get_db)):
    """Start a paper in the app — creates an attempt, returns questions STRIPPED of answers."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    paper = db.query(MockPaper).filter_by(id=paper_id, status="ready").first()
    if not paper:
        return JSONResponse({"ok": False, "error": "no such paper"}, status_code=404)
    att = PaperAttempt(student_id=student.id, paper_id=paper.id, max_score=paper.max_marks, answers={})
    db.add(att)
    db.commit()
    return JSONResponse({"ok": True, "attempt_id": att.id, "title": paper.title or paper.code,
                         "minutes": paper.minutes, "max_marks": paper.max_marks,
                         "questions": [_safe_paper_q(q) for q in (paper.questions or [])]})


@app.get("/api/m/paper/result/{attempt_id}")
def m_paper_result(attempt_id: int, request: Request, db: Session = Depends(get_db)):
    """The scored result of a submitted paper attempt (native), with per-question verdicts."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    att = db.query(PaperAttempt).filter_by(id=attempt_id, student_id=student.id).first()
    if not att or not att.submitted_at:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    paper = db.get(MockPaper, att.paper_id)
    res = mockpaper.score_attempt(paper.questions or [], att.answers or {})
    per = {p["n"]: p for p in res["per_q"]}
    rows = []
    for q in (paper.questions or []):
        v = per.get(q.get("n"), {})
        rows.append({"n": q.get("n"), "section": q.get("section"), "qtype": q.get("qtype"),
                     "stem": q.get("stem", ""), "options": q.get("options") or [],
                     "marks": q.get("marks"), "given": v.get("given"),
                     "correct": v.get("correct"), "state": v.get("state"),
                     "solution": q.get("solution", "")})
    return JSONResponse({"ok": True, "title": paper.title or paper.code,
                         "score": att.score, "max": att.max_score,
                         "correct": att.correct, "wrong": att.wrong, "skipped": att.skipped,
                         "pct": round(100 * att.score / att.max_score) if att.max_score else 0,
                         "rows": rows})


@app.get("/api/m/tutor/anchor")
def m_tutor_anchor(request: Request, subject: str = "", concept: str = "",
                   db: Session = Depends(get_db)):
    """The anchor question the native 'Understand' tutor teaches around — same
    source as the web tutor (_tutor_anchor), pulled instantly from the pool."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False}, status_code=401)
    subject = (subject or "").strip()
    concept = (concept or "").strip()[:120]
    if subject not in examgen.RAG_SUBJECTS or not concept:
        return JSONResponse({"ok": False, "error": "bad params"}, status_code=400)
    cs = db.query(ConceptStat).filter_by(student_id=student.id, subject=subject, concept=concept).first()
    mastery_pct = round(100 * cs.correct / cs.seen) if (cs and cs.seen) else None
    diff = examgen.difficulty_for(subject, (mastery_pct or 0) / 100)
    return JSONResponse({
        "ok": True, "available": tutor.available(),
        "subject": subject, "subject_label": examgen.RAG_SUBJECTS[subject]["label"],
        "concept": concept, "mastery_pct": mastery_pct,
        "anchor": _tutor_anchor(subject, concept, diff),
    })


def _assignments_json(db, student) -> list:
    """Native-friendly assignments for a linked student (kind + ref so the app can act)."""
    if not student or not getattr(student, "teacher_id", None):
        return []
    bid = getattr(student, "batch_id", None)
    rows = (db.query(Assignment).filter_by(teacher_id=student.teacher_id, active=True)
            .order_by(Assignment.created_at.desc()).all())
    rows = [a for a in rows if a.invite_id is None or a.invite_id == bid][:12]
    return [{"id": a.id, "kind": a.kind, "ref": a.ref,
             "title": a.title or a.subject_label or "Practice", "subject": a.subject_label}
            for a in rows if a.kind in ("smart", "mock", "classtest")]


@app.get("/api/m/teacher/home")
def m_teacher_home(request: Request, db: Session = Depends(get_db)):
    """Everything the native teacher home needs: institute, roster (linked students + real mastery),
    batch invites, active assignments, class tests, and the subjects a teacher can pick."""
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    invites = (db.query(TeacherInvite).filter_by(teacher_id=teacher.id)
               .order_by(TeacherInvite.created_at.desc()).all())
    inv_rows = [{"code": i.code, "label": i.label, "active": i.active,
                 "sublabels": [examgen.RAG_SUBJECTS[s]["label"] for s in (i.subjects or []) if s in examgen.RAG_SUBJECTS],
                 "url": f"{settings.BASE_URL}/join/{i.code}"} for i in invites]
    linked = db.query(Student).filter_by(teacher_id=teacher.id).all()
    roster = []
    for s in linked:
        stats = [x for x in db.query(ConceptStat).filter_by(student_id=s.id).all() if x.seen]
        seen = sum(x.seen for x in stats); corr = sum(x.correct for x in stats)
        roster.append({"sid": s.id, "name": s.name or s.email, "email": s.email,
                       "mastery": round(100 * corr / seen) if seen else 0,
                       "tests": db.query(TopicAttempt).filter_by(student_id=s.id).count()})
    roster.sort(key=lambda r: r["mastery"])
    assigns = (db.query(Assignment).filter_by(teacher_id=teacher.id, active=True)
               .order_by(Assignment.created_at.desc()).all())
    tests = (db.query(ClassTest).filter_by(teacher_id=teacher.id)
             .order_by(ClassTest.created_at.desc()).all())
    test_rows = []
    for t in tests:
        test_rows.append({"code": t.code, "title": t.title or t.subject_label,
                          "subject": t.subject_label, "n": t.n,
                          "sittings": db.query(ClassSitting).filter_by(class_test_id=t.id).count()})
    subs = [{"id": sid, "label": examgen.RAG_SUBJECTS[sid]["label"], "exam": g["label"]}
            for sid, g in _teacher_subjects()]
    return JSONResponse({
        "ok": True, "institute": teacher.institute or teacher.name or "",
        "roster_count": len(linked), "roster": roster, "invites": inv_rows,
        "assignments": [{"id": a.id, "kind": a.kind, "ref": a.ref,
                         "title": a.title, "subject": a.subject_label} for a in assigns],
        "tests": test_rows, "subjects": subs,
    })


@app.post("/api/m/join")
async def m_join(request: Request, db: Session = Depends(get_db)):
    """Link the CURRENT logged-in student to a teacher's batch via its invite code."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        body = {}
    code = (body.get("code") or "").strip().upper()
    inv = db.query(TeacherInvite).filter_by(code=code, active=True).first()
    if not inv:
        return JSONResponse({"ok": False, "error": "That class code isn't valid."}, status_code=404)
    student.teacher_id = inv.teacher_id
    _link_subjects(db, student, inv.subjects)
    db.commit()
    teacher = db.query(Student).filter_by(id=inv.teacher_id).first()
    return JSONResponse({"ok": True,
                         "institute": (teacher.institute or teacher.name or "your teacher") if teacher else "your teacher",
                         "label": inv.label})


@app.get("/api/m/classtest/{code}")
def m_classtest(code: str, request: Request, db: Session = Depends(get_db)):
    """The stored pack for a class test, so a logged-in student can take it IN THE APP. The result
    is submitted to /api/teacher/sitting (which ties it to the student's account if they're linked)."""
    student = current_student(request, db)
    if not student:
        return JSONResponse({"ok": False, "error": "login"}, status_code=401)
    ct = db.query(ClassTest).filter_by(code=code).first()
    if not ct:
        return JSONResponse({"ok": False, "error": "unknown test"}, status_code=404)
    # mark this taker's name in-session so /api/teacher/sitting attributes it correctly
    request.session[f"ct_{code}"] = student.name or student.email.split("@")[0]
    return JSONResponse({"ok": True, "code": ct.code, "title": ct.title,
                         "subject": ct.subject_label, "pack": ct.pack})


@app.get("/api/m/teacher/student")
def m_teacher_student(request: Request, sid: int, db: Session = Depends(get_db)):
    """One linked student's real results — their practice attempts (with per-question answers) AND
    their class-test sittings. This is how a teacher sees 'did my student take it, and how'."""
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    s = db.query(Student).filter_by(id=sid, teacher_id=teacher.id).first()
    if not s:
        return JSONResponse({"ok": False, "error": "not your student"}, status_code=404)
    attempts = (db.query(TopicAttempt).filter_by(student_id=s.id)
                .order_by(TopicAttempt.taken_at.desc()).limit(30).all())
    my_tids = [t.id for t in db.query(ClassTest).filter_by(teacher_id=teacher.id).all()]
    sits = (db.query(ClassSitting).filter(ClassSitting.student_id == s.id,
            ClassSitting.class_test_id.in_(my_tids)).order_by(ClassSitting.submitted_at.desc()).all()
            if my_tids else [])
    paper_atts = (db.query(PaperAttempt).filter_by(student_id=s.id)
                  .filter(PaperAttempt.submitted_at.isnot(None))
                  .order_by(PaperAttempt.submitted_at.desc()).limit(20).all())
    papers = []
    for pa in paper_atts:
        mp = db.get(MockPaper, pa.paper_id)
        papers.append({"id": pa.id, "title": (mp.title or mp.code) if mp else "Mock test",
                       "score": pa.score, "max": pa.max_score,
                       "pct": round(100 * pa.score / pa.max_score) if pa.max_score else 0})
    return JSONResponse({
        "ok": True, "name": s.name or s.email, "email": s.email,
        "papers": papers,
        "attempts": [{"id": a.id, "title": a.title, "subject": a.subject,
                      "score": a.score, "total": a.total,
                      "concepts": a.concepts or []} for a in attempts],
        "sittings": [{"title": next((t.title for t in db.query(ClassTest).filter_by(teacher_id=teacher.id).all() if t.id == x.class_test_id), "Class test"),
                      "score": x.score, "total": x.total,
                      "pct": round(100 * x.score / x.total) if x.total else 0,
                      "weak": x.weak_topics or []} for x in sits],
    })


@app.get("/api/m/teacher/attempt/{aid}")
def m_teacher_attempt(request: Request, aid: int, db: Session = Depends(get_db)):
    """Full per-question detail (the student's ANSWERS) of one of the teacher's students' attempts."""
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    a = db.query(TopicAttempt).filter_by(id=aid).first()
    if not a:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    owner = db.query(Student).filter_by(id=a.student_id).first()
    if not owner or owner.teacher_id != teacher.id:
        return JSONResponse({"ok": False, "error": "not your student"}, status_code=403)
    return JSONResponse({"ok": True, "title": a.title, "score": a.score, "total": a.total,
                         "detail": a.detail or []})


@app.get("/api/m/teacher/paper-attempt/{aid}")
def m_teacher_paper_attempt(request: Request, aid: int, db: Session = Depends(get_db)):
    """Full scored breakdown of one of the teacher's students' mock-paper attempts."""
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    pa = db.query(PaperAttempt).filter_by(id=aid).first()
    if not pa or not pa.submitted_at:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    owner = db.query(Student).filter_by(id=pa.student_id).first()
    if not owner or owner.teacher_id != teacher.id:
        return JSONResponse({"ok": False, "error": "not your student"}, status_code=403)
    paper = db.get(MockPaper, pa.paper_id)
    res = mockpaper.score_attempt(paper.questions or [], pa.answers or {})
    per = {p["n"]: p for p in res["per_q"]}
    rows = []
    for q in (paper.questions or []):
        v = per.get(q.get("n"), {})
        rows.append({"n": q.get("n"), "section": q.get("section"), "qtype": q.get("qtype"),
                     "stem": q.get("stem", ""), "options": q.get("options") or [],
                     "marks": q.get("marks"), "given": v.get("given"),
                     "correct": v.get("correct"), "state": v.get("state")})
    return JSONResponse({"ok": True, "title": (paper.title or paper.code) if paper else "Mock test",
                         "score": pa.score, "max": pa.max_score,
                         "correct": pa.correct, "wrong": pa.wrong, "skipped": pa.skipped,
                         "pct": round(100 * pa.score / pa.max_score) if pa.max_score else 0,
                         "rows": rows})


@app.get("/api/m/teacher/tests")
def m_teacher_tests(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    tests = db.query(ClassTest).filter_by(teacher_id=teacher.id).order_by(ClassTest.id.desc()).all()
    out = []
    for t in tests:
        n_sits = db.query(ClassSitting).filter_by(class_test_id=t.id).count()
        out.append({"code": t.code, "title": t.title, "subject": t.subject_label,
                    "n": t.n, "difficulty": t.difficulty, "sittings": n_sits,
                    "share_url": f"{settings.BASE_URL}/t/{t.code}"})
    return JSONResponse({"ok": True, "institute": teacher.institute or "", "tests": out})


@app.get("/api/m/teacher/test/{code}")
def m_teacher_test(code: str, request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    ct = db.query(ClassTest).filter_by(code=code, teacher_id=teacher.id).first()
    if not ct:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    sits = _sittings_for(db, ct)
    weak_count: dict = {}
    for s in sits:
        for w in (s.weak_topics or []):
            weak_count[w] = weak_count.get(w, 0) + 1
    return JSONResponse({
        "ok": True, "code": ct.code, "title": ct.title, "subject": ct.subject_label,
        "n": ct.n, "difficulty": ct.difficulty, "chapters": ct.chapters or [],
        "share_url": f"{settings.BASE_URL}/t/{ct.code}",
        "print_url": f"{settings.BASE_URL}/teacher/test/{ct.code}/print?answers=1",
        "sittings": [{"name": s.student_name, "score": s.score, "total": s.total,
                      "pct": round(100 * s.score / s.total) if s.total else 0,
                      "weak": s.weak_topics or []} for s in sits],
        "class_weak": sorted(weak_count.items(), key=lambda kv: -kv[1])[:10],
    })


@app.get("/api/m/teacher/dashboard")
def m_teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    teacher = current_teacher(request, db)
    if not teacher:
        return JSONResponse({"ok": False}, status_code=401)
    tests = db.query(ClassTest).filter_by(teacher_id=teacher.id).all()
    tids = [t.id for t in tests]
    sits = (db.query(ClassSitting).filter(ClassSitting.class_test_id.in_(tids)).all() if tids else [])
    by_student: dict = {}
    weak_count: dict = {}
    for s in sits:
        b = by_student.setdefault(s.student_name or "—",
                                  {"name": s.student_name or "—", "tests": 0, "score": 0, "total": 0, "weak": {}})
        b["tests"] += 1; b["score"] += s.score; b["total"] += s.total
        for w in (s.weak_topics or []):
            b["weak"][w] = b["weak"].get(w, 0) + 1
            weak_count[w] = weak_count.get(w, 0) + 1
    students = []
    for b in by_student.values():
        pct = round(b["score"] / b["total"] * 100) if b["total"] else 0
        tier = "weak" if pct < 40 else ("shaky" if pct < 70 else "solid")
        top_weak = sorted(b["weak"].items(), key=lambda kv: -kv[1])[:3]
        students.append({"name": b["name"], "pct": pct, "tier": tier, "tests": b["tests"],
                         "weak": [w for w, _ in top_weak]})
    students.sort(key=lambda x: x["pct"])
    return JSONResponse({"ok": True, "n_tests": len(tests), "n_sits": len(sits),
                         "students": students,
                         "class_weak": sorted(weak_count.items(), key=lambda kv: -kv[1])[:10]})


@app.get("/terms", response_class=HTMLResponse)
@app.get("/privacy", response_class=HTMLResponse)
@app.get("/refund", response_class=HTMLResponse)
@app.get("/disclaimer", response_class=HTMLResponse)
@app.get("/contact", response_class=HTMLResponse)
def policy_page(request: Request):
    slug = request.url.path.strip("/")
    page = legal.LEGAL.get(slug)
    if not page:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "policy.html", {"page": page})


@app.get("/api/bridge/stats")
def bridge_stats(request: Request, db: Session = Depends(get_db)):
    """Self-paced LMS stats for the learn.trigunai.com admin. Server-to-server only —
    requires the shared X-Bridge-Key header (never exposed to a browser)."""
    if not settings.BRIDGE_KEY or request.headers.get("x-bridge-key", "") != settings.BRIDGE_KEY:
        raise HTTPException(status_code=401, detail="bad bridge key")
    m = analytics.metrics(db)
    s, w, g, l = m["subs"], m["web"], m["growth"], m["learning"]
    return JSONResponse({
        "source": "lms.trigunai.com",
        "mrr": s["mrr"], "arr": s["arr"], "paying": s["paying"],
        "active": s["active"], "trial_card": s["trial_card"], "trial_nocard": s["trial_nocard"],
        "trial_expired": s["trial_expired"], "past_due": s["past_due"],
        "cancelled": s["cancelled"], "grandfathered": s["grandfathered"],
        "total_students": s["total"], "new_24h": g["new_24h"], "new_7d": g["new_7d"],
        "lessons_done": l["done"], "lessons_7d": l["done_7d"],
        "visitors_7d": w["uv_7d"], "pageviews_7d": w["pv_7d"], "active_users_24h": w["active_users_24h"],
    })


@app.post("/api/bridge/signup")
async def bridge_signup(request: Request, db: Session = Depends(get_db)):
    """Create/link an LMS account from the WhatsApp onboarding (server-to-server, X-Bridge-Key).
    Acharya's WhatsApp onboarding collects the learner's email + chosen course and calls this so a
    WhatsApp newcomer becomes a real LMS student (same account they can later log into on the web).
    Fires the admin signup notification when the account is new."""
    if not settings.BRIDGE_KEY or request.headers.get("x-bridge-key", "") != settings.BRIDGE_KEY:
        raise HTTPException(status_code=401, detail="bad bridge key")
    body = await request.json()
    email = (body.get("email") or "").lower().strip()
    course = (body.get("course") or "").strip()
    phone = (body.get("phone") or "").strip()
    name = (body.get("name") or "").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        return JSONResponse({"error": "invalid email"}, status_code=400)
    is_new = db.query(Student).filter_by(email=email).first() is None
    s = get_or_create_student(db, email)
    if course in COURSE_TITLES:
        s.course = course
    if phone:
        s.phone = phone
    if name and not s.name:
        s.name = name
    db.commit()
    if is_new:
        total = db.query(Student).count()
        notify.notify_admin(f"🎓 New signup (WhatsApp) — {email} · {COURSE_TITLES.get(s.course, s.course)} · {total} learners total")
    return JSONResponse({"ok": True, "is_new": is_new, "course": s.course})


@app.post("/api/bridge/course-request")
async def bridge_course_request(request: Request, db: Session = Depends(get_db)):
    """A WhatsApp learner asked for a course we don't offer yet. Store it + ping the admin so Deepak
    can build it (then notify the learner on the same number). Server-to-server (X-Bridge-Key)."""
    if not settings.BRIDGE_KEY or request.headers.get("x-bridge-key", "") != settings.BRIDGE_KEY:
        raise HTTPException(status_code=401, detail="bad bridge key")
    body = await request.json()
    topic = (body.get("topic") or "").strip()[:200]
    if not topic:
        return JSONResponse({"error": "empty topic"}, status_code=400)
    email = (body.get("email") or "").lower().strip()
    phone = (body.get("phone") or "").strip()
    db.add(CourseRequest(topic=topic, email=email, phone=phone, source="whatsapp"))
    db.commit()
    pending = db.query(CourseRequest).filter_by(status="requested").count()
    notify.notify_admin(f"📚 Course request (WhatsApp) — '{topic}' · {email or phone} · {pending} pending")
    return JSONResponse({"ok": True})


@app.post("/api/course-request")
async def web_course_request(request: Request, db: Session = Depends(get_db)):
    """Public web form: a visitor on /login asks for a course we don't offer yet. Stores it + pings
    the admin. Light dedup so a double-submit (same email+topic) doesn't spam."""
    body = await request.json()
    topic = (body.get("topic") or "").strip()[:200]
    email = (body.get("email") or "").lower().strip()
    phone = "".join(c for c in (body.get("phone") or "") if c.isdigit())[:15]
    has_email = "@" in email and "." in email.split("@")[-1]
    has_phone = len(phone) >= 8
    # A teacher "Book a demo" lead may prefer WhatsApp/call — accept a valid email OR a phone.
    if not topic or not (has_email or has_phone):
        return JSONResponse({"error": "topic and a contact (email or phone) are required"}, status_code=400)
    dup_q = db.query(CourseRequest).filter_by(topic=topic, status="requested")
    dup = dup_q.filter_by(email=email).first() if has_email else dup_q.filter_by(phone=phone).first()
    if not dup:
        db.add(CourseRequest(topic=topic, email=email, phone=phone, source="web"))
        db.commit()
        pending = db.query(CourseRequest).filter_by(status="requested").count()
        contact = email if has_email else ("+" + phone)
        notify.notify_admin(f"📚 Course/demo request (web) — '{topic}' · {contact} · {pending} pending")
    return JSONResponse({"ok": True})


@app.get("/googled120b7d6012f54e8.html", response_class=PlainTextResponse)
def google_site_verification():
    # Google Search Console ownership verification (HTML file method). Keep this forever.
    return PlainTextResponse("google-site-verification: googled120b7d6012f54e8.html")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return PlainTextResponse(seo.robots_txt(), media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml():
    return Response(seo.sitemap_xml(date.today().isoformat()), media_type="application/xml")


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt():
    return PlainTextResponse(seo.llms_txt(COURSES), media_type="text/plain; charset=utf-8")


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat()}
