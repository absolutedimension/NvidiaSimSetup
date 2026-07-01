"""Session 1 — the smallest real agent: one tool, one loop.

The loop:  PERCEIVE -> DECIDE (LLM) -> ACT (run a tool) -> OBSERVE -> repeat.
A chatbot stops after DECIDE. An agent ACTS, OBSERVES the result, and loops
until the goal is met.

Run:  python agent.py "What time is it in Tokyo right now?"
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

from tools import TOOLS, TOOL_FNS

load_dotenv()                              # read .env -> environment

client = anthropic.Anthropic()             # reads ANTHROPIC_API_KEY from env
MODEL = os.environ["MODEL"]                # set in .env — no hard-coded model ids


def safe_call(fn, **kwargs):
    """Run a tool and ALWAYS return a string the model can read.

    Agents fail at the tool boundary. If the tool raises, we hand the model a
    clean error string instead of crashing — it can read it and recover.
    """
    try:
        return str(fn(**kwargs))
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def run(goal: str, max_turns: int = 6):
    messages = [{"role": "user", "content": goal}]
    for _turn in range(max_turns):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        # Did the model decide to ACT (call a tool)?
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            # No tool call -> the model answered. We're done.
            print(next((b.text for b in resp.content if b.type == "text"), ""))
            return

        # ACT + OBSERVE: run each requested tool, feed the results back in.
        results = []
        for tu in tool_uses:
            out = safe_call(TOOL_FNS[tu.name], **tu.input)
            print(f"  ⚙  {tu.name}({tu.input}) → {out}")
            results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": out,
            })
        messages.append({"role": "user", "content": results})
    print("⚠ hit max_turns without finishing")


if __name__ == "__main__":
    goal = sys.argv[1] if len(sys.argv) > 1 else "What time is it in Tokyo right now?"
    run(goal)
