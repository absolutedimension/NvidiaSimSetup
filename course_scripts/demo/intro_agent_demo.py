#!/usr/bin/env python3
"""
LIVE DEMO — the 10-minute "watch an agent think and act" moment for the intro class.
A tiny Ops Agent: goal in -> it calls a tool on its own -> it acts -> it summarizes.
This is Module 1 ("what an agent is") made real in ~50 lines.

Run it (any OpenAI-compatible endpoint works):
  pip install openai
  export OPENAI_API_KEY=sk-...                 # your OpenAI key
  # OR point at the TrigunAI LiteLLM proxy:
  #   export OPENAI_API_KEY=sk-trigunai-master-key-2026
  #   export OPENAI_BASE_URL=http://localhost:4000/v1
  python3 intro_agent_demo.py

Talk track while it runs: "It's not answering me — it's deciding to use a tool,
running it, looking at the result, and only then writing the summary. That loop is
the whole difference between a chatbot and an agent."
"""
import os, json
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY (+ OPENAI_BASE_URL if set)
MODEL = os.environ.get("DEMO_MODEL", "gpt-4o-mini")
TODAY = "2026-06-19"

# --- the agent's one TOOL (its "hands") -------------------------------------
def get_invoices():
    """Returns the company's invoices (pretend this hits a real database/sheet)."""
    return [
        {"id": "INV-101", "client": "Acme Corp",   "amount": 45000, "due": "2026-05-30", "paid": False},
        {"id": "INV-102", "client": "Bluewave",    "amount": 18000, "due": "2026-06-25", "paid": False},
        {"id": "INV-103", "client": "Corian Labs",  "amount": 32000, "due": "2026-06-05", "paid": True},
        {"id": "INV-104", "client": "Dynamo Inc",   "amount": 27000, "due": "2026-06-10", "paid": False},
    ]

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_invoices",
        "description": "Get the list of all company invoices with amount, due date, and paid status.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}]

SYSTEM = (
    f"You are an Ops Agent. Today is {TODAY}. "
    "Goal: find the OVERDUE UNPAID invoices and write a short, friendly summary for the business owner "
    "(which clients, how much total is overdue, and a one-line suggested next step). "
    "Use the get_invoices tool to get the data before answering."
)

def run(goal="Summarize my overdue invoices for today."):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": goal}]
    print(f"🎯 GOAL: {goal}\n")
    for step in range(1, 6):                       # the LOOP (with a safety cap)
        print(f"🤖 step {step}: thinking...")
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        if msg.tool_calls:                         # the model DECIDED to act
            messages.append(msg)
            for tc in msg.tool_calls:
                print(f"🔧 calling tool: {tc.function.name}()")
                result = get_invoices()            # WE run the tool, hand back the result
                print(f"📊 tool returned {len(result)} invoices")
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": json.dumps(result)})
            continue                               # loop again with the new info
        print("\n✅ DONE — the agent's answer:\n")  # final answer => stop
        print(msg.content)
        return
    print("⏹️  hit the step cap (safety stop).")

if __name__ == "__main__":
    run()
