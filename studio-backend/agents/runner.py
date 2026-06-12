"""
Agent runner — the core agentic loop.

Takes a system prompt (from SKILL.md), a user message, and a set of tools.
Runs the Claude API in a loop: Claude decides which tools to call, we execute
them, feed results back, repeat until Claude returns a final text response.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Callable, Awaitable, Any

import anthropic

def _load_env() -> dict:
    """Parse .env file manually (dotenv has issues with some Python versions)."""
    env_path = Path(__file__).parent.parent / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

_ENV = _load_env()
CLAUDE_MODEL = _ENV.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_API_KEY = _ENV.get("ANTHROPIC_API_KEY")
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 15  # safety limit — don't let agent loop forever
TOKEN_BUDGET = 100_000  # kill after this many tokens per job


@dataclass
class ToolDef:
    """A tool the agent can call."""
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., Awaitable[Any]]


@dataclass
class AgentEvent:
    """Events emitted during agent execution — streamed to the frontend."""
    type: str  # "thinking" | "tool_call" | "tool_result" | "text" | "done" | "error"
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        return f"data: {json.dumps({'type': self.type, **self.data})}\n\n"


@dataclass
class AgentResult:
    """Final result of an agent run."""
    text: str
    tool_calls: list[dict]
    total_tokens: int
    rounds: int


def load_system_prompt(agent_name: str) -> str:
    """Load a SKILL.md system prompt by agent name."""
    # Check cowork-plugins first, then ~/.claude/skills/
    paths = [
        Path(__file__).parent.parent.parent / "cowork-plugins" / agent_name / "SKILL.md",
        Path.home() / ".claude" / "skills" / agent_name / "SKILL.md",
    ]
    for p in paths:
        if p.exists():
            content = p.read_text()
            # Strip YAML frontmatter
            if content.startswith("---"):
                end = content.index("---", 3)
                content = content[end + 3:].strip()
            return content
    raise FileNotFoundError(f"No SKILL.md found for agent '{agent_name}' in {[str(p) for p in paths]}")


async def run_agent(
    agent_name: str,
    user_message: str,
    tools: list[ToolDef],
    conversation_history: list[dict] | None = None,
) -> AsyncIterator[AgentEvent]:
    """
    Run a Claude agent with tools in a loop. Yields AgentEvents for streaming.

    The loop:
    1. Send messages to Claude with tools
    2. If Claude returns tool_use → execute tools, feed results back, go to 1
    3. If Claude returns end_turn → yield final text, done
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system_prompt = load_system_prompt(agent_name)

    # Build tool schemas for the API
    api_tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        }
        for t in tools
    ]
    tool_handlers = {t.name: t.handler for t in tools}

    # Build messages
    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    total_tokens = 0
    all_tool_calls = []

    for round_num in range(MAX_TOOL_ROUNDS):
        yield AgentEvent(type="thinking", data={"round": round_num + 1})

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=api_tools,
                messages=messages,
            )
        except anthropic.APIError as e:
            yield AgentEvent(type="error", data={"message": str(e)})
            return

        # Track tokens
        total_tokens += response.usage.input_tokens + response.usage.output_tokens
        if total_tokens > TOKEN_BUDGET:
            yield AgentEvent(type="error", data={
                "message": f"Token budget exceeded ({total_tokens}/{TOKEN_BUDGET})"
            })
            return

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    yield AgentEvent(type="tool_call", data={
                        "tool": tool_name,
                        "input": _safe_truncate(tool_input),
                    })

                    all_tool_calls.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "round": round_num + 1,
                    })

                    # Execute the tool
                    handler = tool_handlers.get(tool_name)
                    if handler:
                        try:
                            result = await handler(**tool_input)
                            result_str = json.dumps(result, default=str)
                        except Exception as e:
                            result_str = json.dumps({"error": str(e)})
                            yield AgentEvent(type="tool_result", data={
                                "tool": tool_name,
                                "error": str(e),
                            })
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                                "is_error": True,
                            })
                            continue
                    else:
                        result_str = json.dumps({"error": f"Unknown tool: {tool_name}"})

                    yield AgentEvent(type="tool_result", data={
                        "tool": tool_name,
                        "result": _safe_truncate(result_str, 500),
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str[:8000],  # cap tool result size
                    })

            # Feed tool results back to Claude
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            # Extract final text
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            yield AgentEvent(type="text", data={"content": final_text})
            yield AgentEvent(type="done", data={
                "total_tokens": total_tokens,
                "rounds": round_num + 1,
                "tool_calls_count": len(all_tool_calls),
            })
            return

        else:
            # Unexpected stop reason
            yield AgentEvent(type="error", data={
                "message": f"Unexpected stop_reason: {response.stop_reason}"
            })
            return

    # Exhausted max rounds
    yield AgentEvent(type="error", data={
        "message": f"Agent hit max rounds ({MAX_TOOL_ROUNDS})",
        "total_tokens": total_tokens,
    })


def _safe_truncate(obj, max_len=200) -> str | dict:
    """Truncate for display in events."""
    if isinstance(obj, str):
        return obj[:max_len] + ("..." if len(obj) > max_len else "")
    if isinstance(obj, dict):
        return {k: _safe_truncate(v, max_len) for k, v in obj.items()}
    return obj
