"""Idempotent curriculum seed for Cohort 1 — 'Build Agentic AI Systems'.
Source of truth: Agentic_AI_Cohort_Welcome.pdf. Run: python -m app.seed"""
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Lesson, Module, Student, WorkbookTask

# week -> (code, title, session_date, summary)
MODULES = [
    (0, "Kickoff", "Kickoff", "26 Jun", "Orientation · API key live · fork the starter repo · pick your use-case"),
    (1, "M1", "What an agent actually is", "03 Jul", "Map your use-case to goal → actions → stop; the loop"),
    (2, "M2", "Your first tool-calling agent", "10 Jul", "Live-code the agent loop; land your first tool call"),
    (3, "M3", "Tools & integrations", "17 Jul", "Connect YOUR real tool — inbox, sheet, files, web search"),
    (4, "M4", "Memory & context", "24 Jul", "Add memory to your agent; retrieval (RAG) basics on your docs"),
    (5, "M5", "Planning & multi-step", "31 Jul", "Task decomposition, ReAct, reflection & self-correction"),
    (6, "M-INT", "Catch-up & integration", "07 Aug", "No new module — get your agent doing a real 5-step job end-to-end"),
    (7, "M6", "Reliability & guardrails", "14 Aug", "JSON validation, retries, human checkpoints, cost control"),
    (8, "M7", "Multi-agent systems", "21 Aug", "Orchestrator + worker agents; when multiple agents truly help"),
    (9, "M8", "Deploy your agent", "28 Aug", "Run it on a schedule on a server, with logging you can read"),
    (10, "M9", "Ship a real business agent", "04 Sep", "Package it, hand it to a non-technical user, measure time saved"),
    (11, "CAP", "Capstone build", "11 Sep", "Office-hours format — polish your own agent for Demo Day"),
    (12, "DEMO", "Demo Day + certificates", "18 Sep", "Each student demos their working agent · certificates awarded"),
]

# week -> { days: [(day, date, focus, task, minutes)], bring: str }
WORKBOOK = {
    1: {"days": [
        ("Sat", "27 Jun", "Watch", "Watch Module 1. Note: what are the 4 parts of an agent?", 45),
        ("Sun", "28 Jun", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "29 Jun", "Build", "Fork the starter repo, install it, add your API key to .env.", 40),
        ("Tue", "30 Jun", "Build", "Run python run.py \"hello\". Open agent/loop.py and comment each step.", 40),
        ("Wed", "01 Jul", "Make it yours", "Write your use-case (the real job) into config.py and the README.", 45),
        ("Thu", "02 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent saying hello in the terminal (screenshot) + your one-sentence use-case."},
    2: {"days": [
        ("Sat", "04 Jul", "Watch", "Watch Module 2. Note: how does the model ask for a tool, and how do we answer?", 45),
        ("Sun", "05 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "06 Jul", "Build", "Run a goal that triggers a tool: python run.py \"what is today's date?\".", 40),
        ("Tue", "07 Jul", "Build", "Add a print inside the loop to show every tool call + result.", 40),
        ("Wed", "08 Jul", "Make it yours", "List the 2–3 tools YOUR agent will need (names + one line each).", 45),
        ("Thu", "09 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A run log showing a tool call and its result."},
    3: {"days": [
        ("Sat", "11 Jul", "Watch", "Watch Module 3. Note: which of your tools is easiest to add first?", 45),
        ("Sun", "12 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "13 Jul", "Build", "Add one new tool to agent/tools.py (schema + function). Test it in isolation.", 40),
        ("Tue", "14 Jul", "Build", "Wire it into the loop; have the agent call it. Office hours if stuck.", 40),
        ("Wed", "15 Jul", "Make it yours", "Point it at YOUR data — your sheet, a CSV export, your files.", 45),
        ("Thu", "16 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent doing something useful with your own data."},
    4: {"days": [
        ("Sat", "18 Jul", "Watch", "Watch Module 4. Note: what should your agent remember between runs?", 45),
        ("Sun", "19 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "20 Jul", "Build", "Use agent/memory.py: have the agent write a note at the end of a run.", 40),
        ("Tue", "21 Jul", "Build", "On the next run, load that note into the prompt so it 'remembers'.", 40),
        ("Wed", "22 Jul", "Make it yours", "Decide the 1–2 things your agent should remember for your use-case.", 45),
        ("Thu", "23 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Two runs where run #2 clearly uses what run #1 remembered."},
    5: {"days": [
        ("Sat", "25 Jul", "Watch", "Watch Module 5. Note: what is ReAct, in one sentence?", 45),
        ("Sun", "26 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "27 Jul", "Build", "Give the agent a task needing 3+ tool calls. Watch how it sequences them.", 40),
        ("Tue", "28 Jul", "Build", "Add a reflection step: let it check its own work before finishing.", 40),
        ("Wed", "29 Jul", "Make it yours", "Write the real 5-step version of YOUR workflow as a single goal.", 45),
        ("Thu", "30 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A transcript of your agent completing a multi-step task."},
    6: {"days": [
        ("Sat", "01 Aug", "Watch", "No new module. Re-watch any part you were shaky on.", 45),
        ("Sun", "02 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "03 Aug", "Build", "Connect the pieces: tools + memory + planning in one run.", 40),
        ("Tue", "04 Aug", "Build", "Run your real workflow's happy path start to finish. Fix what breaks.", 40),
        ("Wed", "05 Aug", "Make it yours", "Tidy: name things clearly, remove dead code, note remaining gaps.", 45),
        ("Thu", "06 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent doing the real job, start to finish (rough is fine)."},
    7: {"days": [
        ("Sat", "08 Aug", "Watch", "Watch Module 6. Note: where could your agent do something costly or wrong?", 45),
        ("Sun", "09 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "10 Aug", "Build", "Add JSON validation + one retry on a tool that can fail.", 40),
        ("Tue", "11 Aug", "Build", "Set a cost cap in config.py (MAX_USD); add a human confirm before any 'send'.", 40),
        ("Wed", "12 Aug", "Make it yours", "Add the confirm-before-acting checkpoint that fits YOUR workflow.", 45),
        ("Thu", "13 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A run where a tool fails and your agent recovers (or stops) — plus your cost cap."},
    8: {"days": [
        ("Sat", "15 Aug", "Watch", "Watch Module 7. Note: when do multiple agents help vs. add chaos?", 45),
        ("Sun", "16 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "17 Aug", "Build", "Split a job into a planner agent + a worker agent; pass one handoff.", 40),
        ("Tue", "18 Aug", "Build", "Compare: is the 2-agent version actually better than one? Be honest.", 40),
        ("Wed", "19 Aug", "Make it yours", "Decide if YOUR use-case needs multi-agent — and write why / why not.", 45),
        ("Thu", "20 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Either a 2-agent handoff working, OR a clear reason one agent is enough."},
    9: {"days": [
        ("Sat", "22 Aug", "Watch", "Watch Module 8. Note: cron vs. GitHub Actions vs. a server — which fits you?", 45),
        ("Sun", "23 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "24 Aug", "Build", "Add logging so every run records what it did and why.", 40),
        ("Tue", "25 Aug", "Build", "Schedule it (cron or GitHub Actions). Trigger one scheduled run.", 40),
        ("Wed", "26 Aug", "Make it yours", "Pick the schedule YOUR job needs (daily? hourly? on an event?).", 45),
        ("Thu", "27 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A log from a run that fired on a schedule, not by you."},
    10: {"days": [
        ("Sat", "29 Aug", "Watch", "Watch Module 9. Note: what would confuse a non-technical user?", 45),
        ("Sun", "30 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "31 Aug", "Build", "Write your agent's playbook: what it does, how to run it, what it needs.", 40),
        ("Tue", "01 Sep", "Build", "Package the config + a one-line run command. Remove anything fragile.", 40),
        ("Wed", "02 Sep", "Make it yours", "Hand it to ONE non-technical person and watch them try it.", 45),
        ("Thu", "03 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Feedback from your first real user + a rough 'time saved' number."},
    11: {"days": [
        ("Sat", "05 Sep", "Watch", "No new module. Re-watch the part most relevant to your capstone.", 45),
        ("Sun", "06 Sep", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "07 Sep", "Build", "Fix your top 3 rough edges. Clean the README so it's obvious how to run.", 40),
        ("Tue", "08 Sep", "Build", "Do a full dry-run of the real job. Time it.", 40),
        ("Wed", "09 Sep", "Make it yours", "Write your demo story: the problem → your agent → the result.", 45),
        ("Thu", "10 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A near-final agent + a 2-minute demo plan."},
    12: {"days": [
        ("Sat", "12 Sep", "Watch", "No new module. Watch a peer's clip shared in the WhatsApp group for ideas.", 45),
        ("Sun", "13 Sep", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "14 Sep", "Build", "Rehearse the live run twice. Note where it's slow or risky.", 40),
        ("Tue", "15 Sep", "Build", "Record a 1-min backup video in case the live run hiccups.", 40),
        ("Wed", "16 Sep", "Make it yours", "Prepare your before/after: how much time your agent saves you.", 45),
        ("Thu", "17 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your FINAL working agent — ready to demo on Demo Day."},
}

# week 1 lesson is built & available; later weeks get authored on the weekly drip
LESSONS = [
    (1, "what-is-an-agent", "What is an agent?", 100, True),
]


def run():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        mod_by_week = {}
        for week, code, title, sdate, summary in MODULES:
            m = db.query(Module).filter_by(week=week).first()
            if not m:
                m = Module(week=week, code=code, title=title, session_date=sdate,
                           summary=summary, sort=week)
                db.add(m)
                db.flush()
            mod_by_week[week] = m

        for week, slug, title, gems, available in LESSONS:
            l = db.query(Lesson).filter_by(slug=slug).first()
            if not l:
                db.add(Lesson(module_id=mod_by_week[week].id, slug=slug, title=title,
                              max_gems=gems, available=available, sort=0))

        for week, data in WORKBOOK.items():
            existing = db.query(WorkbookTask).filter_by(week=week).count()
            if existing:
                continue
            sort = 0
            for day, ddate, focus, task, minutes in data["days"]:
                db.add(WorkbookTask(week=week, day=day, day_date=ddate, focus=focus,
                                    task=task, minutes=minutes, is_bring=False, sort=sort))
                sort += 1
            db.add(WorkbookTask(week=week, day="Fri", day_date="", focus="Bring to Friday",
                                task=data["bring"], minutes=0, is_bring=True, sort=sort))

        # demo accounts
        for email, name, admin in [
            ("deepak@trigunai.com", "Deepak", True),
            ("student@example.com", "Test Student", False),
        ]:
            if not db.query(Student).filter_by(email=email).first():
                db.add(Student(email=email, name=name, is_admin=admin))

        db.commit()
        print(f"Seeded {len(MODULES)} modules, {len(LESSONS)} lessons, "
              f"{sum(len(w['days']) + 1 for w in WORKBOOK.values())} workbook tasks.")
        print(f"DB: {settings.DATABASE_URL}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
