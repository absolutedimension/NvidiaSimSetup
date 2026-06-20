# Ops Agent — Starter Repo

Your project for the **Build Agentic AI Systems** live cohort. You'll grow this one repo across all 9
modules until it's a real agent doing a real job of yours, on a schedule.

> **Same scaffold, your use-case.** Everyone starts from this. By Demo Day, your fork automates
> a workflow *you* actually do.

---

## Option A — run in your browser (recommended · zero install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/OWNER/agentic-ops-agent-starter?quickstart=1)

1. Click **"Open in GitHub Codespaces"** above (or **▶ Open my coding environment** in the LMS).
   A full VS Code opens in your browser and installs Python + all dependencies for you.
2. **Add your API key:** open the `.env` file (already created) and paste your key.
   *(Or set a Codespaces secret: repo → Settings → Secrets → Codespaces.)*
3. In the terminal, run:
   ```bash
   python run.py "hello"
   ```
4. **Let Copilot write the code.** Open Copilot Chat (sidebar), switch it to **Agent mode**, and
   ask it to build what each module's task describes. Sign in with your GitHub account — Copilot's
   free tier is enough for this cohort.

If the agent says hello and stops, **your agent works end-to-end.** That's the day-one win.

> Codespaces is free on your personal GitHub account (~60 hrs/month — more than this cohort needs).
> Same environment for everyone, so on Fridays we debug *your code*, not your setup.

---

## Option B — local setup (if you'd rather run on your own machine)

```bash
git clone <your-fork-url> && cd agentic-ops-agent-starter
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and paste your key
python run.py "hello"
```

Don't have an API key yet? You'll get one working live at Session 0 — no one leaves without it.

---

## What's here

| File | Module | What it is |
|---|---|---|
| `run.py` | — | Entrypoint. `python run.py "your goal"` |
| `agent/loop.py` | M1–M2 | **The agent loop** — read this first, it's the whole idea |
| `agent/tools.py` | M3 | Tool registry — where you give the agent *hands* |
| `agent/memory.py` | M4 | Memory — starts as a JSON file, grows into retrieval |
| `agent/config.py` | M6 | Model, step limit, cost cap, your use-case |
| `deploy/schedule.md` | M8 | Running it without you |

Each module, you fill in one part. By Module 9 this repo *is* your shipped agent.

---

## Your use-case (fill in at Session 0)

> _One sentence: the real, repetitive workflow you want your agent to do._
>
> Example: "Read my support inbox each morning, draft replies to the routine ones, and log the rest in a sheet."

Write yours in `.env` as `USE_CASE=...` and at the top of this section.

---

## House rules

- **Never commit `.env`** (your key). It's already in `.gitignore`.
- **Watch your spend.** `MAX_USD` in `.env` is a rough cap; check your provider dashboard weekly.
- **Bring your blockers to the live session.** Stuck for >30 min? Post in `#help`. That's what it's for.
