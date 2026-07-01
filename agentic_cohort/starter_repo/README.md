# Agentic AI Cohort — Session 1 starter

Your first working agent: **one tool, one loop.**

## Setup (5 min, do this BEFORE the live session)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then open .env and paste your key
```

## Check your setup works (Session 0 baseline)

```bash
python run.py "hello"
```
If it prints a reply, you're ready. If you see an error, bring it to the
"wins & blockers" round at the start of Session 1.

## Run the agent (what we build live in Session 1)

```bash
python agent.py "What time is it in Tokyo right now?"
```
You should see the tool fire, then the answer:
```
  ⚙  get_time({'timezone': 'Asia/Tokyo'}) → 2026-06-26 03:24 JST
It's 3:24 AM on June 26 in Tokyo.
```

## The files

| File | What it is |
|---|---|
| `run.py` | One LLM call, no tools — proves your key works. |
| `tools.py` | The tool(s) your agent can call + their schema. |
| `agent.py` | The loop: PERCEIVE → DECIDE → ACT → OBSERVE → repeat. |
| `.env` | Your key + model id (never commit this). |

## In Session 1 you will

1. Build the loop in `agent.py` live.
2. Watch it break (a bad tool result) and fix it.
3. Swap `get_time` for the **first tool your own BYOA agent needs**.
4. Commit + push your `agent.py` — that's today's proof of work.
