"""Session 1 — the tools your agent can call.

A "tool" is just a normal Python function plus a schema that tells the model
*when* and *how* to call it. Start with one universal tool: get_time.
In beat 5 each student swaps this for the first tool THEIR agent needs.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def get_time(timezone: str = "Asia/Kolkata") -> str:
    """Return the current time in the given IANA timezone."""
    return datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M %Z")


# The schema the model sees. `description` matters: it decides WHEN to call.
TOOLS = [{
    "name": "get_time",
    "description": "Get the current date and time in a given IANA timezone (e.g. Asia/Kolkata).",
    "input_schema": {
        "type": "object",
        "properties": {"timezone": {"type": "string"}},
        "required": [],
    },
}]

# Map the tool name -> the real function. agent.py looks the function up here.
TOOL_FNS = {"get_time": get_time}
