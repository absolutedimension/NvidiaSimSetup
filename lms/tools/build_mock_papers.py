"""Pre-generate the shared mock-paper test series into the LMS database, PER EXAM/GOAL.

Papers are shared by every student on that goal (a real test series), so the cost is one-time.
Resumable: any paper code already present is skipped, so it's safe to re-run.

    EXAMGEN_KEY=... DATABASE_URL=postgresql://... \
      python3 tools/build_mock_papers.py --goal neet --count 3

--goal is an examgen.GOALS id with a blueprint in mockpaper.BLUEPRINTS
(jee-advanced | jee-main | neet | banking | upsc). Papers are tagged subject=<goal id> so the
goal-aware /exam-prep/papers page shows each student only their own exam's papers.
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
from app.mockpaper import BLUEPRINTS, plan_paper_multi  # noqa: E402
from app.examgen import RAG_SUBJECTS, GOALS             # noqa: E402

EXAMGEN_URL = os.getenv("EXAMGEN_URL", "https://gurukul.trigunai.com/examgen").rstrip("/")
EXAMGEN_KEY = os.getenv("EXAMGEN_KEY", "").strip()
WORKERS = int(os.getenv("PAPER_WORKERS", "10"))
REQ_TIMEOUT = int(os.getenv("PAPER_REQ_TIMEOUT", "420"))


def _exam_subject(subject_slug: str) -> tuple[str, str]:
    """subject slug (e.g. 'neet-biology') -> examgen (exam, subject) display names."""
    rs = RAG_SUBJECTS.get(subject_slug) or {}
    return rs.get("exam", ""), rs.get("subject", "")


def _chapters(subject_slug: str) -> list[dict]:
    exam, subject = _exam_subject(subject_slug)
    url = (f"{EXAMGEN_URL}/chapters?exam={urllib.parse.quote(exam)}"
           f"&subject={urllib.parse.quote(subject)}")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode()).get("chapters", [])
    except Exception as exc:
        print(f"  ! chapters {subject_slug} ({exam}/{subject}): {exc}", flush=True)
        return []


def _gen_one(slot: dict, difficulty: str, tries: int = 2) -> dict | None:
    exam, subject = _exam_subject(slot["subject"])
    payload = {"exam": exam, "subject": subject,
               "chapter": slot["chapter"], "concept": slot["concept"],
               "difficulty": difficulty, "type": slot["type"], "count": 1, "exemplars": 3,
               "require_figure": bool(slot.get("figure"))}
    req = urllib.request.Request(
        f"{EXAMGEN_URL}/generate", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {EXAMGEN_KEY}"},
        method="POST")
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
                qs = json.loads(r.read().decode()).get("questions") or []
            if qs:
                return qs[0]
        except Exception as exc:
            print(f"    ! {slot['subject']}/{slot['chapter']} [{slot['type']}] {exc}", flush=True)
        time.sleep(2)
    return None


def build_paper(goal_id: str, chapters_by_subject: dict, seed: int) -> list[dict]:
    bp = BLUEPRINTS[goal_id]
    slots = plan_paper_multi(goal_id, chapters_by_subject, seed)
    difficulty = bp.get("difficulty", "3")
    out: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_gen_one, s, difficulty): s for s in slots}
        for fut in as_completed(futs):
            s = futs[fut]
            q = fut.result()
            if not q:
                continue
            out.append({
                "section": s["section"], "qtype": q.get("qtype", s["type"]),
                "marks": s["marks"], "neg": s["neg"], "partial": s.get("partial", 0),
                "stem": q.get("stem", ""),
                "options": [{"label": o.get("label"), "text": o.get("text")}
                            for o in (q.get("options") or [])],
                "correct": q.get("correct_answer"),
                "solution": q.get("solution", ""),
                "chapter": q.get("chapter") or s["chapter"],
                "concept": q.get("concept") or s["concept"],
                "figure": q.get("figure_svg") or None,
            })
    order = {sec["name"]: i for i, sec in enumerate(bp["sections"])}
    out.sort(key=lambda q: order.get(q["section"], 99))
    for i, q in enumerate(out, 1):
        q["n"] = i
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", default="jee-advanced", help="examgen GOALS id (see mockpaper.BLUEPRINTS)")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--start", type=int, default=1)
    args = ap.parse_args()
    if not EXAMGEN_KEY:
        sys.exit("EXAMGEN_KEY not set")
    if args.goal not in BLUEPRINTS:
        sys.exit(f"no blueprint for goal '{args.goal}' — have {list(BLUEPRINTS)}")
    bp = BLUEPRINTS[args.goal]
    total_q = sum(sec["n"] for sec in bp["sections"])

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, MockPaper
    url = os.getenv("DATABASE_URL", "").replace("+psycopg2", "")
    if not url:
        sys.exit("DATABASE_URL not set")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    chapters_by_subject = {subj: _chapters(subj) for subj in bp["mix"]}
    avail = {s: len(c) for s, c in chapters_by_subject.items()}
    print(f"[{args.goal}] chapters per subject: {avail} · blueprint {total_q}Q", flush=True)
    if not any(chapters_by_subject.values()):
        sys.exit(f"[{args.goal}] no chapters from examgen — cannot generate")

    for i in range(args.start, args.start + args.count):
        code = f"{bp['code']}-{i:02d}"
        with Session() as db:
            if db.query(MockPaper).filter_by(code=code).first():
                print(f"[{code}] already exists — skip", flush=True)
                continue
        t0 = time.time()
        print(f"[{code}] generating {total_q} questions…", flush=True)
        qs = build_paper(args.goal, chapters_by_subject, seed=i * 7919 + hash(args.goal) % 9973)
        if len(qs) < total_q * 0.7:
            print(f"[{code}] only {len(qs)}/{total_q} — NOT saving (retry on re-run)", flush=True)
            continue
        with Session() as db:
            _label = "MCQ Practice" if bp.get("kind") == "mcq" else "Mock Paper"
            db.add(MockPaper(code=code, subject=args.goal,
                             title=f"{bp['label']} — {_label} {i}",
                             minutes=bp["minutes"],
                             max_marks=sum(q["marks"] for q in qs),
                             questions=qs, status="ready"))
            db.commit()
        print(f"[{code}] ✅ saved {len(qs)} questions in {int(time.time()-t0)}s", flush=True)
    print(f"[{args.goal}] done", flush=True)


if __name__ == "__main__":
    main()
