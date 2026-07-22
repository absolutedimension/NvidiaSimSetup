from datetime import datetime, date

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.utcnow()


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    course: Mapped[str] = mapped_column(String(40), default="agentic")     # agentic | remote-swe
    phone: Mapped[str] = mapped_column(String(20), default="")             # WhatsApp number, if onboarded via WA
    plan: Mapped[str] = mapped_column(String(40), default="full")          # full | emi
    status: Mapped[str] = mapped_column(String(20), default="active")      # active | paused
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    # ---- subscription (Razorpay) ----
    # sub_status: none | created | trialing | active | past_due | cancelled | grandfathered
    sub_status: Mapped[str] = mapped_column(String(20), default="none", index=True)
    rzp_customer_id: Mapped[str] = mapped_column(String(40), default="")
    rzp_subscription_id: Mapped[str] = mapped_column(String(40), default="", index=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # ---- learning-loop data consent (the "your usage improves Acharya" surface) ----
    data_loop_consent: Mapped[bool] = mapped_column(Boolean, default=True)


class MagicToken(Base):
    __tablename__ = "magic_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Module(Base):
    __tablename__ = "modules"
    id: Mapped[int] = mapped_column(primary_key=True)
    course: Mapped[str] = mapped_column(String(40), default="agentic", index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    session_date: Mapped[str] = mapped_column(String(20), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(40), default="interactive")
    sort: Mapped[int] = mapped_column(Integer, default=0)
    max_gems: Mapped[int] = mapped_column(Integer, default=100)
    available: Mapped[bool] = mapped_column(Boolean, default=False)
    module: Mapped["Module"] = relationship(back_populates="lessons")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    gems_awarded: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WorkbookTask(Base):
    __tablename__ = "workbook_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    day: Mapped[str] = mapped_column(String(12))            # Sat, Sun, ...
    day_date: Mapped[str] = mapped_column(String(20), default="")
    focus: Mapped[str] = mapped_column(String(60), default="")
    task: Mapped[str] = mapped_column(Text)
    minutes: Mapped[int] = mapped_column(Integer, default=40)
    is_bring: Mapped[bool] = mapped_column(Boolean, default=False)   # the Friday "bring" keystone
    sort: Mapped[int] = mapped_column(Integer, default=0)


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    __table_args__ = (UniqueConstraint("student_id", "task_id", name="uq_student_task"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("workbook_tasks.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    gems_awarded: Mapped[int] = mapped_column(Integer, default=0)


class PointsLedger(Base):
    __tablename__ = "points_ledger"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    points: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(80))
    ref: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Streak(Base):
    __tablename__ = "streaks"
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    current: Mapped[int] = mapped_column(Integer, default=0)
    longest: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("student_id", "badge_code", name="uq_student_badge"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    badge_code: Mapped[str] = mapped_column(String(40))
    awarded_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class LearnerFact(Base):
    """Flexible key/value store of what we learn about a student over time, used to
    personalize examples and the tutor. Captured gradually — never as a big form."""
    __tablename__ = "learner_facts"
    __table_args__ = (UniqueConstraint("student_id", "key", name="uq_student_fact"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    key: Mapped[str] = mapped_column(String(40))          # name, work, interest, why, routine, tools, experience
    value: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="prompt")  # prompt | lesson | inferred
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class Visit(Base):
    """Lightweight, privacy-friendly page-view log for website analytics.
    `anon` = a daily-salted hash of ip+ua (no raw IP stored). student_id set when logged in."""
    __tablename__ = "visits"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(200), index=True)
    ref: Mapped[str] = mapped_column(String(200), default="")
    anon: Mapped[str] = mapped_column(String(40), index=True)
    student_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class LearningEvent(Base):
    """The trainable record of HOW a learner learns — every graded attempt, on web or
    WhatsApp, keyed by concept. This is the loop's raw material: a knowledge-tracing model
    fits on (student_anon, concept_id, outcome, created_at) and the RL teaching simulator
    calibrates on it. NEVER store free text here (reflect prose / chat) — only outcomes +
    small tokens. Exports use student_anon (a salted hash), never the raw student_id."""
    __tablename__ = "learning_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    student_anon: Mapped[str] = mapped_column(String(40), index=True)   # stable per-student pseudonym
    course: Mapped[str] = mapped_column(String(40), default="", index=True)
    surface: Mapped[str] = mapped_column(String(12), default="web")     # web | whatsapp
    concept_id: Mapped[str] = mapped_column(String(80), default="", index=True)  # the trainable key
    lesson_slug: Mapped[str] = mapped_column(String(80), default="")
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    step_type: Mapped[str] = mapped_column(String(20), default="")      # mcq|match|order|truefalse|recall|reflect
    action: Mapped[str] = mapped_column(String(16), default="attempt")  # attempt|hint|tutor_ask|reveal|complete
    outcome: Mapped[str] = mapped_column(String(10), default="")        # correct|wrong|partial|na
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    chosen: Mapped[str] = mapped_column(String(40), default="")         # option index/token — never free text
    intervention: Mapped[str] = mapped_column(String(12), default="none")  # none|hint|tutor|example
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class AssessmentItem(Base):
    """A validated, cached practice question for the dynamic exam-prep generator.
    Generated by assess_gen.py; the correct key survived a key-withheld independent-solver
    check before insert. Only status='validated' items are ever served. `payload` is the
    full question in the assess.html engine shape (bilingual + key). Keyed by exam_key so
    other students hitting the same exam are served instantly from the bank."""
    __tablename__ = "assessment_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    exam_key: Mapped[str] = mapped_column(String(80), index=True)   # slug of the exam/topic
    exam_title: Mapped[str] = mapped_column(String(120), default="")
    qtype: Mapped[str] = mapped_column(String(12), default="mcq")   # mcq | truefalse
    payload: Mapped[dict] = mapped_column(JSON, default=dict)       # the validated question (raw shape)
    status: Mapped[str] = mapped_column(String(12), default="validated", index=True)
    model: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class CourseRequest(Base):
    """A learner asked Acharya (on WhatsApp) for a course we don't offer yet. Deepak builds it,
    then notifies them on the same number. status: requested | building | ready."""
    __tablename__ = "course_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(20), default="", index=True)
    source: Mapped[str] = mapped_column(String(20), default="whatsapp")    # whatsapp | web
    status: Mapped[str] = mapped_column(String(20), default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
