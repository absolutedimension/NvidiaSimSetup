from datetime import datetime, date

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
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
    # B2B2C: if set, this student belongs to a teacher/institute (joined via a teacher's link). Their
    # subjects are teacher-controlled (they can't add their own) and they see teacher-assigned tests.
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    # the specific BATCH (TeacherInvite) this student joined through — scopes their assignments + roster.
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("teacher_invites.id"), nullable=True, index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    # ---- subscription (Razorpay) ----
    # sub_status: none | created | trialing | active | past_due | cancelled | grandfathered
    sub_status: Mapped[str] = mapped_column(String(20), default="none", index=True)
    rzp_customer_id: Mapped[str] = mapped_column(String(40), default="")
    rzp_subscription_id: Mapped[str] = mapped_column(String(40), default="", index=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # ---- student exam-prep assessment plan (₹199/mo) — a SEPARATE Razorpay track, independent of
    # the ₹499 course subscription above. Default 'none' (NOT grandfathered — the assessment plan is
    # a fresh paid track even for the existing cohort). Gated by has_assessment_access(). ----
    assess_status: Mapped[str] = mapped_column(String(20), default="none", index=True)  # none|trialing|active|past_due|cancelled|comped
    rzp_assess_customer_id: Mapped[str] = mapped_column(String(40), default="")
    rzp_assess_subscription_id: Mapped[str] = mapped_column(String(40), default="", index=True)
    assess_trial_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assess_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # ---- learning-loop data consent (the "your usage improves Acharya" surface) ----
    data_loop_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    # ---- teacher/institute (the B2B side): a teacher signs in and creates class tests. Reuses the
    # same auth + session as a student; is_teacher just gates the /teacher surface. ----
    is_teacher: Mapped[bool] = mapped_column(Boolean, default=False)
    institute: Mapped[str] = mapped_column(String(120), default="")
    # ---- self-serve WHITE-LABEL branding (set by the teacher on /teacher/branding). Applied to their
    # linked students' app + every printed paper. brand_logo is a data: URL (base64) so it persists in
    # Postgres without a file store. "Powered by Acharya" always stays. ----
    brand_color: Mapped[str] = mapped_column(String(9), default="")   # hex e.g. #1A73E8; "" → default saffron
    brand_logo: Mapped[str] = mapped_column(Text, default="")         # data:image/...;base64,... (institute logo)
    brand_watermark: Mapped[bool] = mapped_column(Boolean, default=False)  # faint logo/name behind printed papers
    # ---- kids product: the student's class + board, set when they join a teacher's kids batch. Locks
    # their self-generated worksheets to this grade/board (worksheet page hides the grade/board pickers). ----
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1..5 (kids); None for seniors/direct
    board: Mapped[str] = mapped_column(String(24), default="")          # CBSE | ICSE | Bihar Board


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


class CompSession(Base):
    """A live 'earn your access' competition attempt. The served questions + correct keys are
    kept HERE (server-side) so the client never sees the answers — the test is scored on submit.
    Short-lived: created on /api/comp/start, deleted on /api/comp/submit (or expires)."""
    __tablename__ = "comp_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    comp_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    exam: Mapped[str] = mapped_column(String(60), default="")
    data: Mapped[dict] = mapped_column(JSON, default=dict)   # the 11 questions WITH keys + explains
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


class TopicAttempt(Base):
    """One completed exam-prep test — the student's own progress history (NOT the consent-gated
    Acharya learning loop; this is the product's own score-keeping). Powers 'N tests taken'."""
    __tablename__ = "topic_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    subject: Mapped[str] = mapped_column(String(40), index=True)   # 'jee-physics' or a curated subject id
    title: Mapped[str] = mapped_column(String(120), default="")
    score: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    concepts: Mapped[list] = mapped_column(JSON, default=list)     # concept names covered
    # The full paper as sat: [{q, a (correct answer), explain, ok, type}] — lets the student REOPEN
    # any past test from their report instead of losing it the moment they leave the results screen.
    detail: Mapped[list] = mapped_column(JSON, default=list)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class ConceptStat(Base):
    """Running per-concept mastery for a student within a subject — drives the 'Acharya suggests
    next' weakest-concept recommendation. correct: solid=1.0, shaky=0.5, weak=0.0."""
    __tablename__ = "concept_stats"
    __table_args__ = (UniqueConstraint("student_id", "subject", "concept", name="uq_concept_stat"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    subject: Mapped[str] = mapped_column(String(40), index=True)
    concept: Mapped[str] = mapped_column(String(120))
    seen: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[float] = mapped_column(Float, default=0.0)
    last_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class TeacherInvite(Base):
    """A teacher's 'join my class' link (per BATCH). A student who signs up via /join/<code> is
    LINKED to the teacher (Student.teacher_id) and seeded exactly this batch's subjects — the
    institute controls the syllabus, the student can't add their own. E.g. 'Class 12 PCM', 'Commerce'."""
    __tablename__ = "teacher_invites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    label: Mapped[str] = mapped_column(String(80), default="")               # batch name
    subjects: Mapped[list] = mapped_column(JSON, default=list)               # subject ids this batch studies
    # kids batches: the class + board this batch studies. Students who join inherit these (Student.grade/board).
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)         # 1..5 for a kids batch, else None
    board: Mapped[str] = mapped_column(String(24), default="")               # CBSE | ICSE (kids)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Assignment(Base):
    """A practice/test a TEACHER assigns to their LINKED students (Student.teacher_id). Shows in the
    student's '📋 Assigned by your teacher' section. kind = smart (adaptive practice on a subject) |
    mock (a mock paper) | classtest (a shared ClassTest code)."""
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    # the BATCH this assignment targets. Null = applies to ALL of the teacher's batches (back-compat).
    invite_id: Mapped[int | None] = mapped_column(ForeignKey("teacher_invites.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(16))                 # smart | mock | classtest | kidsworksheet | kidstest
    ref: Mapped[str] = mapped_column(String(120), default="")     # subject_id | paper id | classtest code | "subject|chapter|n" (kids)
    title: Mapped[str] = mapped_column(String(140), default="")
    subject_label: Mapped[str] = mapped_column(String(80), default="")
    # kids FIXED test (kind=kidstest): the frozen worksheet items, so every student gets the SAME sheet.
    # Null for practice worksheets (kind=kidsworksheet), which generate fresh per student.
    pack: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AssignmentCompletion(Base):
    """A linked student's completion of a teacher Assignment (kids). Powers the teacher's 'who did it'
    list + class weak-topic aggregation. One row per (assignment, student) — upserted on each finish."""
    __tablename__ = "assignment_completions"
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)   # concept/chapter labels the student missed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ClassTest(Base):
    """A test a TEACHER creates for their class. Questions are generated ONCE (examgen) and stored
    in `pack`, so every student gets the SAME paper instantly — no per-student LLM cost or wait.
    Shared with students via the short `code` (link /t/<code>). This is the B2B/teacher product."""
    __tablename__ = "class_tests"
    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)   # short shareable code
    title: Mapped[str] = mapped_column(String(120), default="")
    subject_id: Mapped[str] = mapped_column(String(40))                      # jee-physics, neet-biology, …
    subject_label: Mapped[str] = mapped_column(String(80), default="")
    chapters: Mapped[list] = mapped_column(JSON, default=list)               # chosen "Chapter::Concept" labels
    difficulty: Mapped[str] = mapped_column(String(8), default="3-4")
    n: Mapped[int] = mapped_column(Integer, default=5)
    pack: Mapped[dict] = mapped_column(JSON, default=dict)                   # the full assess.html pack (keys+solutions)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class ClassSitting(Base):
    """One student's attempt at a ClassTest — NO student account, just a name. Stores the per-concept
    result so the teacher dashboard can aggregate class weak-topics and flag who needs help."""
    __tablename__ = "class_sittings"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_test_id: Mapped[int] = mapped_column(ForeignKey("class_tests.id"), index=True)
    # set when the taker is a LOGGED-IN linked student (institute batch) — ties the result to their
    # account so it rolls up to the teacher roster. Null for anonymous /t/<code> name-gate takers.
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True, index=True)
    student_name: Mapped[str] = mapped_column(String(80), default="")
    score: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)                   # graded-question count
    concepts: Mapped[list] = mapped_column(JSON, default=list)               # [{topic, status, depth}]
    weak_topics: Mapped[list] = mapped_column(JSON, default=list)            # derived weak concept names
    # the full paper as answered — [{q, a (correct), chosen (student's answer), explain, ok, type}] —
    # so the teacher can see exactly what this student answered, question by question.
    detail: Mapped[list] = mapped_column(JSON, default=list)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class GenJob(Base):
    """An async question-generation job. The chat kicks one off, a background thread runs
    examgen (slow: ~40-55s/question) and writes the result here, and the chat polls this row —
    so a big paper NEVER blocks the request (the 'Acharya is thinking… then delivers' UX)."""
    __tablename__ = "gen_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, default=0, index=True)   # teacher/student id (0=anon)
    kind: Mapped[str] = mapped_column(String(20))                           # teacher_test | student_test
    status: Mapped[str] = mapped_column(String(12), default="pending")      # pending | done | error
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)                # {code,redirect,...} or {error}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class SeenQuestion(Base):
    """Every pool question this student has already been served — passed to /pool as `exclude`
    so they never re-see a question. (Pool serving is random, so without this a student WILL get
    repeats across sessions.)"""
    __tablename__ = "seen_questions"
    __table_args__ = (UniqueConstraint("student_id", "question_id", name="uq_seen_question"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    question_id: Mapped[str] = mapped_column(String(80), index=True)
    subject: Mapped[str] = mapped_column(String(40), default="", index=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class MockPaper(Base):
    """A SHARED, pre-generated full mock paper — the test series. Deliberately NOT owned by a
    student: generated once, sat by everyone (exactly how a real test series works), so cost is
    one-time instead of per-signup and papers are instantly available."""
    __tablename__ = "mock_papers"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)      # 'JEEADV-PHY-01'
    subject: Mapped[str] = mapped_column(String(40), default="jee-physics", index=True)
    title: Mapped[str] = mapped_column(String(140), default="")
    minutes: Mapped[int] = mapped_column(Integer, default=60)
    max_marks: Mapped[int] = mapped_column(Integer, default=0)
    # [{n, section, qtype, stem, options[], correct, solution, chapter, concept, marks, neg, figure}]
    questions: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(12), default="draft", index=True)  # draft | ready
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class PaperAttempt(Base):
    """One student's sitting of a MockPaper — answers, marks (with negative marking), timing."""
    __tablename__ = "paper_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("mock_papers.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)   # {"1": "B", "2": ["A","C"], "3": "9"}
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    wrong: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class StudentTopic(Base):
    """A topic the exam-prep student is preparing — the unit the ₹199 plan is metered in
    (up to 5 per student). `topic_key` is a curated exam id (e.g. 'neet') or a free-text slug
    ('q:rotational-motion'); the student takes adaptive tests per topic from the dashboard.
    Seeded from the challenge/first exam on signup; grown via /exam-prep/topics/add."""
    __tablename__ = "student_topics"
    __table_args__ = (UniqueConstraint("student_id", "topic_key", name="uq_student_topic"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    topic_key: Mapped[str] = mapped_column(String(80), index=True)   # exam id, or 'q:<slug>'
    title: Mapped[str] = mapped_column(String(120), default="")      # display, e.g. 'NEET' or 'JEE Rotational Motion'
    kind: Mapped[str] = mapped_column(String(10), default="exam")    # exam | custom
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class KidsSkillState(Base):
    """Per-(student, skill) adaptive state for the worksheet/assessment engine — BKT mastery +
    Elo ability + the 85% controller's target difficulty. skill = 'board/class/subject/chapter'."""
    __tablename__ = "kids_skill_state"
    __table_args__ = (UniqueConstraint("student_id", "skill", name="uq_kids_skill"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    skill: Mapped[str] = mapped_column(String(160), index=True)
    p_mastery: Mapped[float] = mapped_column(Float, default=0.30)
    theta: Mapped[float] = mapped_column(Float, default=0.0)
    ema: Mapped[float] = mapped_column(Float, default=0.85)
    target_b: Mapped[float] = mapped_column(Float, default=-1.73)
    n: Mapped[int] = mapped_column(Integer, default=0)
    n_correct: Mapped[int] = mapped_column(Integer, default=0)
    misconceptions: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
