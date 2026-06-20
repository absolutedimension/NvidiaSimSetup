"""
Tool registry — this is where you give your agent *hands* (Module 3).

A tool is just: (1) a JSON schema the model sees, and (2) a Python function that runs.
Add your real integrations (email, Google Sheets, web search, files) here as the course goes.
Two working examples are included so the loop runs on day one.
"""
import datetime

# --- The tool functions (plain Python) -----------------------------------

def get_today(_input: dict) -> str:
    """Example tool with no integration — proves the loop works on day one."""
    return datetime.date.today().isoformat()


def read_text_file(input: dict) -> str:
    """Read a local text file. Your first real 'hands' tool."""
    path = input["path"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:5000]  # cap so we don't blow the context window
    except Exception as e:
        return f"ERROR reading {path}: {e}"


# --- Tool schemas (what the model sees) -----------------------------------
# Anthropic tool format. The OpenAI format is similar — covered in Module 2.

TOOLS_SCHEMA = [
    {
        "name": "get_today",
        "description": "Return today's date as YYYY-MM-DD.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_text_file",
        "description": "Read a local text file and return its contents (first 5000 chars).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the file"}},
            "required": ["path"],
        },
    },
    # TODO (Module 3): add your real tools here — send_email, append_to_sheet, web_search, ...
]

# Maps tool name -> function. The loop uses this to actually run a tool.
TOOL_FUNCTIONS = {
    "get_today": get_today,
    "read_text_file": read_text_file,
}


def run_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"ERROR: unknown tool '{name}'"
    return str(fn(tool_input))
