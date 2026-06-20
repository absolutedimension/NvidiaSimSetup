"""
The agent loop (Module 1 & 2) — the heart of every agent.

  goal in  ->  model thinks  ->  model asks for a tool  ->  we run it  ->
  give result back  ->  model thinks again  ->  ... ->  model says "done".

This is the whole idea of "will" made concrete. Read it top to bottom — it's short.
"""
from agent import config
from agent.tools import TOOLS_SCHEMA, run_tool


def run_agent(goal: str) -> str:
    if config.PROVIDER != "anthropic":
        raise SystemExit("This starter ships the Anthropic loop. OpenAI variant comes in Module 2.")

    from anthropic import Anthropic  # imported here so OpenAI users don't need the SDK

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": goal}]

    for step in range(1, config.MAX_STEPS + 1):
        resp = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
            system=config.SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )

        # Collect any text the model said this turn.
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if text:
            print(f"\n[step {step}] 🤖 {text}")

        # Find tool-use requests.
        tool_uses = [b for b in resp.content if b.type == "tool_use"]

        # No tools requested -> the agent is done.
        if not tool_uses:
            return text or "(agent finished with no final message)"

        # Run each requested tool and feed the results back.
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in tool_uses:
            print(f"[step {step}] 🔧 {tu.name}({tu.input})")
            output = run_tool(tu.name, tu.input)
            print(f"[step {step}] ↳ {output[:200]}")
            results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": output,
            })
        messages.append({"role": "user", "content": results})

    return f"⚠️ Hit MAX_STEPS ({config.MAX_STEPS}) without finishing. Tighten the task or raise the limit."
