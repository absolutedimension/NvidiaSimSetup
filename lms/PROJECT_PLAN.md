# TrigunAI LMS — Project Plan

> **Product:** A Brilliant-style interactive learning system for TrigunAI's live cohorts.
> **First customer:** Cohort 1 — "Build Agentic AI Systems" (starts Fri 26 Jun 2026).
> **Host:** `lms.trigunai.com`
> **Status:** in active build. This doc is the single source of truth for architecture + scope.

---

## 1. What we're building (one paragraph)

A self-hosted web app where an enrolled cohort student logs in (passwordless), sees their
**13-week journey**, watches the week's module video, completes a **Brilliant-style interactive
lesson** (predict → act → instant feedback → Socratic tutor), and ticks off a **daily workbook**.
Every meaningful action earns **points/coins**, builds a **daily streak**, and triggers
**balloon-burst / confetti** celebrations and **level-ups** — so a solo-paced course *feels* like
a game. An **admin API + dashboard** lets Deepak see, per student: progress, points, streak,
last-active, current week, and workbook completion.

It is **one FastAPI app** (server-rendered Jinja + vanilla-JS interactive lessons) in **one Docker
container**, on **Azure Container Apps**, with **Azure Postgres** for data and **Azure Communication
Services** for magic-link email. No separate frontend build step.

---

## 2. Decisions on record (locked 2026-06-19)

| Decision | Choice | Why |
|---|---|---|
| Auth | **Passwordless magic-link** (email → one-tap link) | No passwords to store/reset; safest + fastest for a small cohort; ACS already in use |
| Friday MVP | **Core student experience** | Login + journey + Lesson 1 + Week-1 workbook + points/streak/burst. Modules 2–9 drip weekly |
| Database | **SQLAlchemy → SQLite (dev) / Azure Postgres (prod)** | Same code both places; zero setup locally; Postgres in prod |
| Frontend | **Jinja templates + vanilla JS** (no React build) | One container, fastest to ship, lessons are already vanilla JS |
| Hosting | **Azure Container Apps** at `lms.trigunai.com` | Consistent with the other 4 TrigunAI hostnames; managed TLS |
| Admin | **API now, polished UI as fast-follow** | Deepak needs student tracking; full UI not required for Friday |

---

## 3. Architecture

```
                         lms.trigunai.com  (Azure Container Apps, managed TLS)
                                   │
                          ┌────────┴─────────┐
                          │   FastAPI app    │   one Docker container
                          │                  │
   Jinja templates  ──────┤  /  /login  /dashboard  /lesson/{slug}  /workbook
   (server-rendered)      │                  │
   vanilla-JS lessons ────┤  /api/*  (progress, points, streak, events)
   (static, in-browser)   │  /admin/* (student tracking, CSV)
                          │                  │
                          └───┬──────────┬───┘
                              │          │
                  ┌───────────┘          └───────────┐
            Azure Postgres                   Azure Communication Services
        (students, progress,                  (magic-link login emails)
         points ledger, streaks)
```

- **Server-rendered shell** (login, dashboard, workbook) = fast, SEO-irrelevant, simple.
- **Interactive lessons** are static HTML/JS (the Brilliant clone) loaded inside the shell; they
  talk to `/api/*` to persist progress + points.
- **Session** = signed JWT in an httpOnly cookie after magic-link verification.

---

## 4. Tech stack

| Layer | Tech |
|---|---|
| Web framework | FastAPI + Uvicorn/Gunicorn |
| Templating | Jinja2 |
| ORM | SQLAlchemy 2.x (+ Alembic later for migrations) |
| DB | SQLite (dev) · Azure Database for PostgreSQL Flexible Server (prod) |
| Auth | Magic-link tokens + `python-jose` JWT session cookie |
| Email | Azure Communication Services (`azure-communication-email`) + console fallback in dev |
| Frontend | Jinja + vanilla JS + the existing Brilliant-style lesson engine |
| Container | Docker (python:3.11-slim) |
| Hosting | Azure Container Apps (region: centralindia, to match existing) |
| Secrets | Container Apps secrets / env vars |

---

## 5. Data model (core tables)

```
students            id, email(unique), name, plan, status(active/paused),
                    enrolled_at, last_active_at
magic_tokens        token(unique), student_id, expires_at, used_at
modules             id, week, code, title, summary, video_url, sort
lessons             id, module_id, slug(unique), title, kind, sort, max_gems
lesson_progress     student_id, lesson_id, status(not_started/in_progress/done),
                    best_score, gems_awarded, completed_at      (unique student+lesson)
workbook_tasks      id, week, day, day_date, focus, task, minutes, bring_flag, sort
task_completions    student_id, task_id, completed_at, gems_awarded  (unique student+task)
points_ledger       id, student_id, points, reason, ref, created_at   ← source of truth for totals
streaks             student_id(unique), current, longest, last_active_date, freezes
achievements        id, student_id, badge_code, awarded_at            (unique student+badge)
events              id, student_id, type, payload(json), created_at   ← admin activity feed
```

**Points are never stored as a running total on the student.** The `points_ledger` is the source of
truth; totals/level are summed on read (cheap at cohort scale, audit-friendly, no drift).

---

## 6. Points & gamification economy (see LEARNING_DESIGN.md for the why)

| Event | Points | Notes |
|---|---|---|
| Lesson step correct (first try) | +10 | partial on retry |
| Lesson completed | +25 | once per lesson |
| Perfect lesson (all first-try) | +15 bonus | |
| Daily workbook task ticked | +10 | the daily-rep driver |
| "Bring to Friday" item done | +30 | the weekly keystone |
| Daily streak continued | +5 ×(streak/7 multiplier) | compounding |
| Week fully completed | +100 | balloon-burst + level check |
| Module video marked watched | +15 | |
| Demo Day capstone | +500 | finale |

**Levels (marks):** `level = floor(sqrt(total_points / 50))` → smooth curve, ~early levels fast.
Display as "Builder Level N" + progress bar to next.

**Celebrations (the juice):**
- Step correct → small coin pop + count tick.
- Lesson complete → confetti burst + gem tally.
- Streak milestone (3/7/14/30) → **balloon burst** + badge.
- Week complete → full-screen balloon-burst + level-up check.

**Badges:** First Steps · 7-Day Streak · Tool Caller · Loop Master · Week N Done · Shipped It (deploy) · Demo Day.

---

## 7. Curriculum map (from the cohort PDF)

13 Friday sessions, flipped model (watch before, build live). Source: `Agentic_AI_Cohort_Welcome.pdf`.

| Wk | Date | Module | Lesson focus | Workbook |
|----|------|--------|--------------|----------|
| 0 | 26 Jun | Kickoff | Orientation, API key, fork repo, pick use-case | bring laptop |
| 1 | 03 Jul | What an agent actually is | **Lesson 1 (built):** Goal·Brain·Tools·Loop | full daily |
| 2 | 10 Jul | First tool-calling agent | the agent loop, first tool call | full daily |
| 3 | 17 Jul | Tools & integrations | connect a real tool | full daily |
| 4 | 24 Jul | Memory & context | memory across runs, RAG basics | full daily |
| 5 | 31 Jul | Planning & multi-step | ReAct, reflection, self-correction | full daily |
| 6 | 07 Aug | Catch-up & integration | end-to-end real job (no new video) | full daily |
| 7 | 14 Aug | Reliability & guardrails | JSON validation, retries, cost caps | full daily |
| 8 | 21 Aug | Multi-agent systems | orchestrator + workers | full daily |
| 9 | 28 Aug | Deploy your agent | schedule + logging | full daily |
| 10 | 04 Sep | Ship a real business agent | package for a non-tech user | full daily |
| 11 | 11 Sep | Capstone build | polish for Demo Day | full daily |
| 12 | 18 Sep | Demo Day + certificates | final demo | full daily |

The full daily workbook for **all 12 weeks** is captured and lives in the seed (`seed.py`).
Lessons 2–9 are authored weekly (drip) using the same lesson engine as Lesson 1.

---

## 8. API surface

**Public / auth**
- `GET /` — landing → redirect to dashboard or login
- `GET /login` · `POST /login` (request magic link) · `GET /check-email`
- `GET /auth/verify?token=…` — verify, set session cookie, redirect to dashboard
- `POST /logout`

**Student (auth required)**
- `GET /dashboard` — the 13-week journey + header stats
- `GET /lesson/{slug}` — lesson player
- `GET /workbook/{week}` — daily checklist
- `POST /api/lesson/{slug}/progress` — `{step, status, score}` → award gems
- `POST /api/lesson/{slug}/complete` — finalize, award completion gems, return celebration payload
- `POST /api/workbook/task/{id}/toggle` — tick/untick a daily task
- `POST /api/module/{id}/watched` — mark video watched
- `GET /api/me/stats` — points, level, streak, badges (for the header)

**Admin (admin-gated)**
- `GET /admin` — student table
- `GET /admin/student/{id}` — full per-student detail
- `GET /admin/api/students` — JSON
- `GET /admin/api/export.csv` — CSV of progress/points/streak/last-active

---

## 9. Build phases (mapped to the task list)

1. ✅ Planning docs (this + LEARNING_DESIGN.md)
2. Backend foundation — FastAPI, config, db, models
3. Magic-link auth + ACS email
4. Curriculum seed (13 weeks)
5. Student dashboard (journey + header stats)
6. Lesson player + progress/points API (wire Lesson 1)
7. Gamification — ledger, streaks, levels, balloon-burst/confetti
8. Admin API + minimal admin page
9. Dockerize + deploy to lms.trigunai.com

**Friday-critical:** 2–7. Admin (8) and full deploy polish (9) can trail by a day if needed,
but the app must be reachable at `lms.trigunai.com` with Lesson 1 working before 26 Jun.

---

## 10. Security & ops notes

- Magic-link tokens: single-use, 15-min expiry, 256-bit random, hashed at rest.
- Session JWT: httpOnly, Secure, SameSite=Lax, 30-day sliding.
- Admin gate: allowlist of admin emails (`deepak@trigunai.com`) checked on the session.
- Rate-limit `POST /login` (don't let it become an email cannon).
- DB: daily automated backup on Azure Postgres; `.env` never committed.
- Cost at cohort scale: Container Apps scale-to-low + burstable Postgres ≈ a few ₹/day.

---

*Owner: TrigunAI. Created 2026-06-19. Update this doc when scope changes.*
