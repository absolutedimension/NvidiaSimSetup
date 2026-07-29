"""Assemble shared mock papers from the REAL PYQ pool (no LLM) — for exams served as authentic
past questions rather than generated (UPSC now; CBSE boards later).

    DATABASE_URL=postgresql://... python3 tools/build_pool_papers.py --goal upsc --count 3

Pulls verified real PYQs from examgen /pool across the goal's subjects (per mockpaper.BLUEPRINTS
mix), keeps them DISTINCT across papers, and writes MockPaper rows tagged subject=<goal id> so the
goal-aware /exam-prep/papers page shows them to the right students. Resumable (existing codes skip).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.mockpaper import BLUEPRINTS                    # noqa: E402
from app import examgen                                 # noqa: E402

# Human section labels per subject slug (shown as section headers when sitting the paper).
SECTION_LABEL = {
    "upsc-gs": "General Studies", "upsc-csat": "CSAT — Aptitude",
    "cbse10-science": "Science", "cbse12-physics": "Physics",
    "cbse12-chemistry": "Chemistry", "cbse12-biology": "Biology",
    "cbse12-accountancy": "Accountancy", "cbse12-economics": "Economics",
}


def _collect(subject_slug: str, need: int) -> list[dict]:
    """Gather up to `need` DISTINCT real PYQs for a subject, sweeping its chapters and difficulties."""
    import json, urllib.request, urllib.parse
    from app.config import settings
    cfg = examgen.RAG_SUBJECTS[subject_slug]
    url = (f"{settings.EXAMGEN_URL}/chapters?exam={urllib.parse.quote(cfg['exam'])}"
           f"&subject={urllib.parse.quote(cfg['subject'])}")
    chapters = [c["chapter"] for c in json.loads(urllib.request.urlopen(url, timeout=30).read()).get("chapters", [])]
    seen, out = set(), []
    for diff in ("3-4", "1-5", "2-3"):          # sweep bands — real PYQs sit at varied difficulty
        for ch in chapters:
            if len(out) >= need:
                return out
            qs, _ = examgen.fetch_pool(subject_slug, ch, difficulty=diff, qtype="MCQ_single",
                                       count=20, exclude=list(seen))
            for q in (qs or []):
                qid = q.get("id") or q.get("hash") or q.get("stem", "")[:60]
                if qid in seen or not (q.get("stem") and q.get("options") and q.get("correct_answer")):
                    continue
                seen.add(qid)
                out.append(q)
    return out


def _to_paper_q(q: dict, sec: dict, subject_slug: str) -> dict:
    return {
        "section": SECTION_LABEL.get(subject_slug, sec["name"]),
        "qtype": q.get("qtype", "MCQ_single"),
        "marks": sec["marks"], "neg": sec["neg"], "partial": sec.get("partial", 0),
        "stem": q.get("stem", ""),
        "options": [{"label": o.get("label"), "text": o.get("text")} for o in (q.get("options") or [])],
        "correct": q.get("correct_answer"),
        "solution": q.get("solution", ""),
        "chapter": q.get("chapter", ""), "concept": q.get("concept", ""),
        "figure": q.get("figure_svg") or None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", required=True, help="examgen GOALS id with a mockpaper.BLUEPRINTS entry")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--start", type=int, default=1)
    args = ap.parse_args()
    if args.goal not in BLUEPRINTS:
        sys.exit(f"no blueprint for '{args.goal}' — have {list(BLUEPRINTS)}")
    bp = BLUEPRINTS[args.goal]
    sec = bp["sections"][0]                              # pool papers use one uniform MCQ scheme
    mix = bp["mix"]

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, MockPaper
    url = os.getenv("DATABASE_URL", "").replace("+psycopg2", "")
    if not url:
        sys.exit("DATABASE_URL not set")
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    # collect enough DISTINCT real PYQs per subject for ALL papers at once, then partition
    per_subject = {}
    for subj, n in mix.items():
        need = n * args.count
        got = _collect(subj, need)
        per_subject[subj] = got
        print(f"[{args.goal}] {subj}: collected {len(got)}/{need} real PYQs", flush=True)

    for i in range(args.start, args.start + args.count):
        code = f"{bp['code']}-{i:02d}"
        with Session() as db:
            if db.query(MockPaper).filter_by(code=code).first():
                print(f"[{code}] already exists — skip", flush=True)
                continue
        qlist = []
        ok = True
        for subj, n in mix.items():
            pool = per_subject[subj]
            take = pool[(i - args.start) * n:(i - args.start) * n + n]
            if len(take) < n:
                print(f"[{code}] not enough {subj} PYQs ({len(take)}/{n}) — skip", flush=True)
                ok = False
                break
            qlist += [_to_paper_q(q, sec, subj) for q in take]
        if not ok:
            continue
        for j, q in enumerate(qlist, 1):
            q["n"] = j
        with Session() as db:
            _label = "MCQ Practice" if bp.get("kind") == "mcq" else "Mock Paper"
            db.add(MockPaper(code=code, subject=args.goal,
                             title=f"{bp['label']} — {_label} {i}",
                             minutes=bp["minutes"],
                             max_marks=sum(q["marks"] for q in qlist),
                             questions=qlist, status="ready"))
            db.commit()
        print(f"[{code}] ✅ saved {len(qlist)} real PYQs", flush=True)
    print(f"[{args.goal}] done", flush=True)


if __name__ == "__main__":
    main()
