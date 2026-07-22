import base64
import hashlib
import hmac
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from . import analytics, billing, catalog, course_details, gamify, legal, notify, personalize, seo, tutor
from .config import settings
from .db import get_db
from .emailer import send_magic_link
from .models import (
    CourseRequest, LearnerFact, Lesson, LessonProgress, LearningEvent, Module, Student, TaskCompletion, WorkbookTask, now,
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
    {"id": "class10",  "subject": "class10",      "title": "Class 10", "tag": "Boards · Sci + Math",  "emoji": "📘"},
    {"id": "class12",  "subject": "class12",      "title": "Class 12", "tag": "Boards · PCM",         "emoji": "📗"},
    {"id": "commerce", "subject": "commerce",     "title": "Commerce", "tag": "Class 11-12",          "emoji": "📊"},
]
EXAM_SUBJECT = {e["id"]: e["subject"] for e in EXAMS}

# Canonical domain. acharya.trigunai.com serves the whole app; lms.trigunai.com 301-redirects here.
CANONICAL_HOST = "acharya.trigunai.com"
ACHARYA_HOSTS = {CANONICAL_HOST}
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
                    v = analytics.make_visit(path, request.headers.get("referer", ""), ip, ua, sid)
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
def login_submit(request: Request, email: str = Form(...), course: str = Form(""), phone: str = Form(""), db: Session = Depends(get_db)):
    email = email.lower().strip()
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
    email = consume_magic_token(db, token)
    if not email:
        return templates.TemplateResponse(
            request, "login.html",
            {"courses": COURSES, "preselect": "", "error": "That link expired or was already used. Request a new one."}
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


@app.get("/exam-prep", response_class=HTMLResponse)
def exam_prep(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    resume_exam = EXAMS[0]["id"]
    if student:
        f = db.query(LearnerFact).filter_by(student_id=student.id, key="exam").first()
        if f and f.value in EXAM_SUBJECT:
            resume_exam = f.value
    return templates.TemplateResponse(request, "exam_prep.html",
                                      {"exams": EXAMS, "student": student, "resume_exam": resume_exam,
                                       "jsonld": seo.exam_prep_jsonld(EXAMS)})


@app.post("/exam-prep/start")
def exam_prep_start(request: Request, email: str = Form(...), exam: str = Form(""),
                    phone: str = Form(""), db: Session = Depends(get_db)):
    """Instant free signup: email → account + session → straight into the assessment.
    No magic-link round-trip for the free tier (the magic link stays the re-login path)."""
    email = email.lower().strip()
    ex = exam.strip() if exam.strip() in EXAM_SUBJECT else EXAMS[0]["id"]
    if "@" not in email or "." not in email.split("@")[-1]:
        return templates.TemplateResponse(request, "exam_prep.html",
                                          {"exams": EXAMS, "student": None, "resume_exam": ex,
                                           "jsonld": seo.exam_prep_jsonld(EXAMS),
                                           "error": "Please enter a valid email."})
    existed = db.query(Student).filter_by(email=email).first() is not None
    student = get_or_create_student(db, email)
    _set_fact(db, student, "exam", ex)
    p = "".join(c for c in phone if c.isdigit())[:15]
    if p and not student.phone:
        student.phone = p
    db.commit()
    if not existed:
        total = db.query(Student).count()
        notify.notify_admin(f"🎯 New student (exam-prep) — {student.email} · {ex} · {total} learners total")
    request.session["sid"] = student.id
    return RedirectResponse(f"/exam-prep/test?exam={ex}", status_code=302)


@app.get("/exam-prep/test", response_class=HTMLResponse)
def exam_prep_test(request: Request, exam: str = "", db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/exam-prep", status_code=302)
    subject = EXAM_SUBJECT.get(exam.strip(), EXAM_SUBJECT[EXAMS[0]["id"]])
    html = (BASE / "static" / "exam" / "assess.html").read_text(encoding="utf-8")
    inject = f"<script>window.__SUBJECT={subject!r};window.__STUDENT=true;</script>"
    return HTMLResponse(html.replace("</head>", inject + "</head>", 1))


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
    for r in results:
        if not isinstance(r, dict):
            continue
        log_learning_event(db, student, surface="web",
                           concept_id=str(r.get("topic", ""))[:80],
                           step_type="mcq", action="complete",
                           outcome=outcome_map.get(str(r.get("status", "")), "na"))
    _set_fact(db, student, "last_exam", subject)
    db.commit()
    return JSONResponse({"ok": True})


@app.post("/logout")
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


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


@app.get("/terms", response_class=HTMLResponse)
@app.get("/privacy", response_class=HTMLResponse)
@app.get("/refund", response_class=HTMLResponse)
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
