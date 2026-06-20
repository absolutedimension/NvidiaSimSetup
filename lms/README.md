# TrigunAI LMS

Brilliant-style interactive learning system for TrigunAI live cohorts.
First cohort: **Build Agentic AI Systems** (starts Fri 26 Jun 2026). Host: `lms.trigunai.com`.

See `PROJECT_PLAN.md` (architecture) and `LEARNING_DESIGN.md` (pedagogy + gamification).

## Run locally

```bash
cd lms
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit if you like; SQLite + console email work out of the box
python -m app.seed              # create tables + seed the 13-week curriculum + demo accounts
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 → enter `student@example.com` → the magic link **prints to the
console** (no email needed in dev). Click it to land on the dashboard.

> macOS note: use `127.0.0.1`, not `localhost` (IPv6 quirk).

## What works today

- Passwordless **magic-link login** (Azure Communication Services in prod; console in dev)
- **13-week journey dashboard** seeded from the cohort PDF
- **Lesson 1** ("What is an agent?") — Brilliant-style interactive, posts progress + completion
- **Points / levels / streaks / badges** (ledger is source of truth)
- **Daily workbook** with tick-to-earn + balloon-burst / confetti celebrations
- `GET /api/me/stats`, `GET /healthz`

## Verified smoke test

```
POST /login   -> 200      dashboard    -> 200 (renders all 13 weeks)
verify        -> 302      workbook/1   -> 200 (renders daily tasks + bring item)
lesson        -> 200      complete API -> +40 gems, badges: first_steps, loop_master
workbook tick -> +30 gems (bring item), streak +1, level-up to 1
```

## Still to build (see task list)

- **Admin API + dashboard** — per-student progress/points/streak/last-active + CSV export
- **Dockerfile + Azure deploy** to `lms.trigunai.com` (Container Apps + Postgres + ACS)
- Lessons 2–9 (authored weekly on the same engine)
- Wire Koji tutor to the LiteLLM proxy for real conversational tutoring

## Prod config (env)

Set `DATABASE_URL` (Azure Postgres), `SECRET_KEY`, `BASE_URL=https://lms.trigunai.com`,
`ACS_CONNECTION_STRING`, `ACS_SENDER`, `ADMIN_EMAILS`. Production runs Python 3.11.
