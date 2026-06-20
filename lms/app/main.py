from datetime import date, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from . import catalog, gamify, personalize, tutor
from .config import settings
from .db import get_db
from .emailer import send_magic_link
from .models import (
    LearnerFact, Lesson, LessonProgress, Module, Student, TaskCompletion, WorkbookTask, now,
)
from .security import consume_magic_token, get_or_create_student, issue_magic_token

BASE = Path(__file__).parent
COHORT_START = date(2026, 6, 26)

app = FastAPI(title="TrigunAI LMS")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, max_age=60 * 60 * 24 * 30)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.cache = None  # avoid jinja2 LRUCache incompat on Python 3.14; negligible at cohort scale


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


# ---------- auth ----------
@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse("/dashboard" if current_student(request, db) else "/login")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@app.post("/login")
def login_submit(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    email = email.lower().strip()
    raw = issue_magic_token(db, email)
    link = f"{settings.BASE_URL}/auth/verify?token={raw}"
    send_magic_link(email, link)
    return templates.TemplateResponse(request, "check_email.html", {"email": email})


@app.get("/auth/verify")
def verify(request: Request, token: str, db: Session = Depends(get_db)):
    email = consume_magic_token(db, token)
    if not email:
        return templates.TemplateResponse(
            request, "login.html", {"error": "That link expired or was already used. Request a new one."}
        )
    student = get_or_create_student(db, email)
    request.session["sid"] = student.id
    return RedirectResponse("/dashboard", status_code=302)


@app.post("/logout")
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# ---------- dashboard ----------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")

    modules = db.query(Module).order_by(Module.week).all()
    lessons = {l.module_id: l for l in db.query(Lesson).all()}
    done_lessons = {
        lp.lesson_id for lp in db.query(LessonProgress).filter_by(
            student_id=student.id, status="done"
        ).all()
    }
    cw = current_week()
    rows = []
    for m in modules:
        lesson = lessons.get(m.id)
        rows.append({
            "week": m.week, "title": m.title, "summary": m.summary,
            "date": m.session_date, "code": m.code,
            "lesson_slug": lesson.slug if lesson else None,
            "lesson_available": bool(lesson and lesson.available),
            "lesson_done": bool(lesson and lesson.id in done_lessons),
            "state": "done" if m.week < cw else ("current" if m.week == cw else "upcoming"),
        })

    facts = personalize.get_facts(db, student.id)
    return templates.TemplateResponse(request, "dashboard.html", {
        "student": student, "rows": rows,
        "current_week": cw, "stats": gamify.stats(db, student.id),
        "greeting": personalize.greeting(facts),
        "ask": (personalize.next_questions(facts, 1) or [None])[0],
        "starter_repo": settings.STARTER_REPO,
    })


@app.get("/workbook/{week}", response_class=HTMLResponse)
def workbook(request: Request, week: int, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return RedirectResponse("/login")
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
    pts = 0
    if body.get("correct"):
        pts = gamify.award(db, student.id, "step_correct", ref=f"{slug}#{body.get('step')}")
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
    return templates.TemplateResponse(request, "admin.html", {
        "student": student, "rows": rows, "current_week": cw,
        "stats": gamify.stats(db, student.id),
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


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat()}
