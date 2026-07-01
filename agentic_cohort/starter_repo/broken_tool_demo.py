"""Beat 4 — make it break, then fix it (facilitator demo).

The lesson: agents fail at the TOOL BOUNDARY. A tool that raises, or returns
the wrong type, confuses the model. You design for it: wrap the call so it
always returns a clean string the model can read.

Run this standalone to rehearse the beat — no API key needed:
    python broken_tool_demo.py
"""


def get_time_broken(timezone: str = "Asia/Kolkata"):
    """A deliberately broken tool: raises instead of returning a time."""
    raise ValueError(f"no clock configured for {timezone}")


def safe_call(fn, **kwargs):
    """The fix: never let a tool crash the loop — return a readable error."""
    try:
        return str(fn(**kwargs))
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


if __name__ == "__main__":
    print("WITHOUT safe_call — the loop would crash here:")
    try:
        get_time_broken("Asia/Tokyo")
    except Exception as e:
        print(f"  💥 {type(e).__name__}: {e}")

    print("\nWITH safe_call — the model gets a clean string it can recover from:")
    print(f"  ✅ {safe_call(get_time_broken, timezone='Asia/Tokyo')}")
