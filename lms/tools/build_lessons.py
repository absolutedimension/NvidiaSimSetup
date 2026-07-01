#!/usr/bin/env python3
"""Build interactive lesson HTML from lesson-source JSON + the shared engine template.

Each source file lives at  lms/lesson_src/<course>/<slug>.json  and is:
    { "slug": "...", "title": "...", "steps": [ ... STEPS array ... ] }

The `steps` array follows the exact authoring schema documented in tools/STEP_SCHEMA.md
(the same vocabulary the agentic lessons use: intro/mcq/classify/reveal/order/trace/tf/
reflect/multi/done). JSON is valid JS, so it's injected straight into `const STEPS = ...;`.

Run:  python3 tools/build_lessons.py            # build everything under lesson_src/
      python3 tools/build_lessons.py <slug>...  # build only these slugs
"""
import json, pathlib, sys, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "tools" / "lesson_template.html").read_text(encoding="utf-8")
SRC_DIR = ROOT / "lesson_src"
OUT_DIR = ROOT / "app" / "lessons"

ALLOWED = {"intro", "mcq", "classify", "reveal", "order", "trace", "tf", "reflect", "multi", "done"}


def validate(slug, data):
    assert isinstance(data.get("steps"), list) and data["steps"], f"{slug}: steps must be a non-empty list"
    assert data["steps"][0].get("type") == "intro", f"{slug}: first step must be type 'intro'"
    assert data["steps"][-1].get("type") == "done", f"{slug}: last step must be type 'done'"
    for i, s in enumerate(data["steps"]):
        t = s.get("type")
        assert t in ALLOWED, f"{slug}: step {i} has unknown type {t!r}"
        if t == "mcq":
            assert isinstance(s.get("correct"), int) and s.get("options"), f"{slug}: step {i} mcq needs options+correct"
        if t in ("multi", "order"):
            assert isinstance(s.get("correct"), list) and s.get("chips"), f"{slug}: step {i} {t} needs chips+correct[]"
        if t == "classify":
            assert s.get("buckets") and s.get("items"), f"{slug}: step {i} classify needs buckets+items"


def build_one(path: pathlib.Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    slug = data.get("slug") or path.stem
    validate(slug, data)
    steps_js = json.dumps(data["steps"], indent=2, ensure_ascii=False)
    html = TEMPLATE.replace("__TITLE__", data["title"]).replace("__STEPS__", steps_js)
    assert "__STEPS__" not in html and "__TITLE__" not in html, "placeholder left unfilled"
    (OUT_DIR / f"{slug}.html").write_text(html, encoding="utf-8")
    return slug, len(data["steps"])


def main():
    wanted = set(sys.argv[1:])
    files = sorted(SRC_DIR.rglob("*.json"))
    built = []
    for p in files:
        if wanted and p.stem not in wanted:
            continue
        slug, n = build_one(p)
        built.append((slug, n))
        print(f"  built {slug}.html  ({n} steps)")
    print(f"Done. {len(built)} lesson(s) built into app/lessons/.")


if __name__ == "__main__":
    main()
