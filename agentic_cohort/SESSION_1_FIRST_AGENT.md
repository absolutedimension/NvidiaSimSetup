# Session 1 — Your First Working Agent (one tool, one loop)

**Format:** live on Google Meet, ~90 min, recorded. **Flipped** — before this session students watched
the *Module 2 video* ("What an Agent Actually Is": the perceive → decide → act → observe loop). The
live time is for **building and debugging their own code**, not re-watching.

**The one goal:** every student leaves with a real agent loop running on *their* machine that calls
**one tool** and acts on the result — and their BYOA use-case sharpened into "what's my agent's first tool."
If everyone's loop ticks with a tool call by the end, the session succeeded. Nothing else matters today.

> Teaching stance (Deepak): screen-share your terminal more than slides. Build it live, let it break live,
> fix it live. "I run these in production" lands hardest when they watch you debug a real error in real time.

---

## Pre-flight (you, 5 min before)
- Starter repo on the `session-1` branch open in your editor + terminal.
- `.env` has a working key; `python run.py "hello"` ticks once (the Session-0 baseline).
- Shared progress sheet open (the use-case column from Session 0).
- One deliberately-broken example ready (a tool with a wrong return type) for the debugging beat.

---

## Beat-by-beat (90 min)

### 1. Wins & blockers (10 min)
Round-robin, fast. Each student: "since kickoff I got ___ working / I'm stuck on ___."
Write blockers in the sheet. **Don't solve them now** — tell them which beat will fix it. This ritual
opens every session: it surfaces who tried and where the real friction is.

### 2. Recap the loop — on ONE slide (5 min)
The whole of Module 2 in one diagram. Don't re-lecture; just anchor vocabulary for the build.
```
        ┌──────────── the agent loop ────────────┐
  goal → │ PERCEIVE → DECIDE (LLM) → ACT (tool) → OBSERVE │ → done?
        └───────────────────▲───────────────────┘
                            └── feed the result back in ──┘
```
One line: "A chatbot stops after DECIDE. An agent ACTS, OBSERVES the result, and loops until the goal's met."

### 3. LIVE build: the smallest real agent (30 min) ← the core of the session
Build this together, slowly, everyone typing along. The scaffold is in the repo; you type the key parts.

**(a) Define ONE tool — a real function the model can call.** Start with the most universal: a calculator
or a "get current time", then show a `read_file` so it feels real.
```python
# tools.py
def get_time(timezone: str = "Asia/Kolkata") -> str:
    """Return the current time in the given IANA timezone."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M %Z")

TOOLS = [{
    "name": "get_time",
    "description": "Get the current date and time in a given IANA timezone (e.g. Asia/Kolkata).",
    "input_schema": {
        "type": "object",
        "properties": {"timezone": {"type": "string"}},
        "required": [],
    },
}]
```

**(b) The loop — DECIDE → ACT → OBSERVE → repeat.** This is the lightbulb moment: the model asks to
call a tool, *your code runs it*, you hand the result back, the model continues.
```python
# agent.py
import os, anthropic, json
from tools import TOOLS, get_time

client = anthropic.Anthropic()           # reads ANTHROPIC_API_KEY from .env
MODEL = os.environ["MODEL"]              # set in .env — no hard-coded model ids
TOOL_FNS = {"get_time": get_time}

def run(goal: str, max_turns: int = 6):
    messages = [{"role": "user", "content": goal}]
    for turn in range(max_turns):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        # Did the model decide to ACT (call a tool)?
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            # No tool call → the model answered. We're done.
            print(next(b.text for b in resp.content if b.type == "text"))
            return

        # ACT + OBSERVE: run each requested tool, feed results back
        results = []
        for tu in tool_uses:
            out = TOOL_FNS[tu.name](**tu.input)
            print(f"  ⚙  {tu.name}({tu.input}) → {out}")
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(out)})
        messages.append({"role": "user", "content": results})
    print("⚠ hit max_turns without finishing")

if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else "What time is it in Tokyo right now?")
```
Run it live: `python agent.py "What time is it in Tokyo right now?"` → they SEE the `⚙ get_time(...)`
line, then the model's answer. **That print line is the whole course in miniature** — the model decided,
your code acted, the model observed and finished. Celebrate it.

### 4. Make it break, then fix it (10 min)
Deliberately return the wrong thing from a tool (e.g. return a dict where a string is expected, or raise).
Show the model getting confused / the traceback. Then fix it together. The lesson: **agents fail at the
tool boundary; you design for it** (validate inputs, wrap tool calls in try/except, return a clean error
string the model can read). This previews Module 3 (tool use + retries).
```python
def safe_call(fn, **kwargs):
    try:
        return str(fn(**kwargs))
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"   # the model can read this and recover
```

### 5. Make it YOURS (20 min) ← the part that matters for BYOA
Each student replaces `get_time` with the **first tool their own agent needs** — pulled from their
Session-0 use-case. Examples to seed them (map their workflow → first tool):
- "tidy my inbox" → a `list_unread(label)` tool
- "summarize a sheet daily" → a `read_sheet(range)` tool
- "draft replies to leads" → a `get_recent_messages()` tool
Push for **real and small**: one tool that reads something real from their world. Walk around (breakout
or screen-share rotations), unblock live. Goal: each student's loop calls *their* tool once by end.

### 6. Close + Module 3 prep (5 min)
- Everyone commits + pushes their `agent.py` with their one tool. (That commit is today's proof of work.)
- Before next week: watch the **Module 3 video** (Tool Use) and add a *second* tool.
- Tease: "Next session your agent gets hands — 3 real tools, web + APIs + your data — and we make it not fall over."

---

## Facilitator notes / common failures (have these ready)
| Symptom | Cause | Fix |
|---|---|---|
| `KeyError: 'MODEL'` | `.env` not loaded / var missing | `pip install python-dotenv`; `from dotenv import load_dotenv; load_dotenv()` at top |
| 401 / auth error | bad or unset `ANTHROPIC_API_KEY` | re-check `.env`; for anyone whose card failed, hand them the **TrigunAI-provided cohort key** (the moat) |
| Loop never ends / hits max_turns | tool result is unreadable or the goal is vague | return a clean string; sharpen the goal; cap with `max_turns` (already in) |
| Model answers without calling the tool | tool description too vague | make `description` concrete about *when* to use it |
| `ZoneInfo` not found (Py<3.9) | old Python | `pip install tzdata` or use `pytz` fallback |

## Definition of done (today)
- [ ] Every student's `agent.py` runs and makes **at least one tool call** they can see in the output.
- [ ] Every student has swapped in (or named) the **first tool for their own BYOA use-case**.
- [ ] Everyone committed + pushed. Blockers logged in the sheet for next week.

*(This session = Module 2 "What an Agent Actually Is" → first 1-tool agent. Mirrors SESSION_0_KICKOFF.md.
Next: SESSION_2 — Tool Use / giving the agent hands (Module 3).)*
