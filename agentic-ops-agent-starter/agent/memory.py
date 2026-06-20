"""
Memory (Module 4). Start trivially simple: a JSON file the agent reads at the
start of a run and writes at the end. You'll upgrade this to retrieval/RAG later.
"""
import json
import os

MEMORY_FILE = os.getenv("MEMORY_FILE", "memory_store.json")


def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"notes": []}


def remember(note: str) -> None:
    mem = load_memory()
    mem["notes"].append(note)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def memory_summary() -> str:
    notes = load_memory().get("notes", [])
    if not notes:
        return "(no long-term memory yet)"
    return "\n".join(f"- {n}" for n in notes[-10:])  # last 10 notes
