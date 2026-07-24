"""Pre-generate the shared JEE-Advanced test series (15 full papers) into the LMS database.

Run ONCE (and again only to top up). Papers are shared by every student, so this cost is one-time.
Resumable: any paper code already present in the DB is skipped, so it's safe to re-run after a
crash or to add more papers later.

    EXAMGEN_KEY=... DATABASE_URL=postgresql://... python3 tools/build_mock_papers.py --count 15

Each paper is 17 questions; the 17 are generated IN PARALLEL (~3 min/paper), because the generator
takes ~40-55s per question on gpt-5.5.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.mockpaper import BLUEPRINT, MAX_MARKS, TOTAL_Q, DIFFICULTY, plan_paper  # noqa: E402

EXAMGEN_URL = os.getenv("EXAMGEN_URL", "https://gurukul.trigunai.com/examgen").rstrip("/")
EXAMGEN_KEY = os.getenv("EXAMGEN_KEY", "").strip()
WORKERS = int(os.getenv("PAPER_WORKERS", "10"))
# The backend does generate(<=180s) + key-withheld validation(<=180s) per question, so a single
# request can legitimately need ~6 min. A shorter timeout here just wastes the work and retries.
REQ_TIMEOUT = int(os.getenv("PAPER_REQ_TIMEOUT", "420"))


def _chapters() -> list[dict]:
    url = (f"{EXAMGEN_URL}/chapters?exam={urllib.parse.quote(BLUEPRINT['exam'])}"
           f"&subject={urllib.parse.quote(BLUEPRINT['subject'])}")
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode()).get("chapters", [])


def _gen_one(slot: dict, tries: int = 2) -> dict | None:
    """Generate ONE question for a blueprint slot. Returns the question dict or None."""
    payload = {"exam": BLUEPRINT["exam"], "subject": BLUEPRINT["subject"],
               "chapter": slot["chapter"], "concept": slot["concept"],
               "difficulty": DIFFICULTY, "type": slot["type"], "count": 1, "exemplars": 3,
               # diagram questions: slow (~90-150s) but free here because this runs offline
               "require_figure": bool(slot.get("figure"))}
    req = urllib.request.Request(
        f"{EXAMGEN_URL}/generate", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {EXAMGEN_KEY}"},
        method="POST")
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
                qs = json.loads(r.read().decode()).get("questions") or []
            if qs:
                return qs[0]
        except Exception as exc:
            print(f"    ! {slot['chapter']}/{slot['concept']} [{slot['type']}] {exc}", flush=True)
        time.sleep(2)
    return None


def build_paper(chapters: list[dict], seed: int) -> list[dict]:
    """Generate all 17 questions for one paper, in parallel. Returns the question list."""
    slots = plan_paper(chapters, seed)
    out: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_gen_one, s): s for s in slots}
        for fut in as_completed(futs):
            s = futs[fut]
            q = fut.result()
            if not q:
                continue
            out.append({
                "section": s["section"], "qtype": q.get("qtype", s["type"]),
                "marks": s["marks"], "neg": s["neg"], "partial": s["partial"],
                "stem": q.get("stem", ""),
                "options": [{"label": o.get("label"), "text": o.get("text")}
                            for o in (q.get("options") or [])],
                "correct": q.get("correct_answer"),
                "solution": q.get("solution", ""),
                "chapter": q.get("chapter") or s["chapter"],
                "concept": q.get("concept") or s["concept"],
                "figure": q.get("figure_svg") or None,
            })
    # order by the blueprint's section order, then number them 1..N
    order = {s["name"]: i for i, s in enumerate(BLUEPRINT["sections"])}
    out.sort(key=lambda q: order.get(q["section"], 99))
    for i, q in enumerate(out, 1):
        q["n"] = i
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=15)
    ap.add_argument("--start", type=int, default=1)
    args = ap.parse_args()
    if not EXAMGEN_KEY:
        sys.exit("EXAMGEN_KEY not set")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, MockPaper
    url = os.getenv("DATABASE_URL", "").replace("+psycopg2", "")
    if not url:
        sys.exit("DATABASE_URL not set")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    chapters = _chapters()
    print(f"chapters available: {len(chapters)} · blueprint {TOTAL_Q}Q / {MAX_MARKS} marks", flush=True)

    for i in range(args.start, args.start + args.count):
        code = f"JEEADV-PHY-{i:02d}"
        with Session() as db:
            if db.query(MockPaper).filter_by(code=code).first():
                print(f"[{code}] already exists — skip", flush=True)
                continue
        t0 = time.time()
        print(f"[{code}] generating {TOTAL_Q} questions…", flush=True)
        qs = build_paper(chapters, seed=i * 7919)
        if len(qs) < TOTAL_Q * 0.7:
            print(f"[{code}] only {len(qs)}/{TOTAL_Q} — NOT saving (will retry on re-run)", flush=True)
            continue
        with Session() as db:
            db.add(MockPaper(code=code, subject="jee-physics",
                             title=f"JEE Advanced Physics — Mock Paper {i}",
                             minutes=BLUEPRINT["minutes"],
                             max_marks=sum(q["marks"] for q in qs),
                             questions=qs, status="ready"))
            db.commit()
        print(f"[{code}] ✅ saved {len(qs)} questions in {int(time.time()-t0)}s", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
