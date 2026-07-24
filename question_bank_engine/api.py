"""HTTP API for the Question Bank Engine — the interface the frontend integrates against.

The API holds the LLM credentials server-side (env), so the frontend NEVER sees the
Azure/proxy keys. It just calls /generate. Run:

    export QBANK_LLM=on \\
           QBANK_LLM_BASE_URL=http://localhost:4000/v1 \\
           QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 \\
           QBANK_CHAT_MODEL=gpt-4o
    # optional: protect it so only your frontend can burn Azure tokens
    export QBANK_API_KEY=<a-long-random-string>
    uvicorn api:app --host 127.0.0.1 --port 8020
"""
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from qbank import config, generator, syllabus
from qbank.llm import LLM
from qbank.storage import Store

MAX_COUNT = int(os.environ.get("QBANK_MAX_COUNT", "20"))
API_KEY = os.environ.get("QBANK_API_KEY")  # if set, callers must send Authorization: Bearer <key>

app = FastAPI(title="TrigunAI Question Generator", version="1.0")

# Frontend runs in a browser on another origin -> allow CORS. Lock allow_origins
# to your real frontend domain(s) in production.
_ORIGINS = os.environ.get("QBANK_CORS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=_ORIGINS, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

# Serve figure images for diagram questions: GET /figures/<id>.png
os.makedirs(config.FIG_DIR, exist_ok=True)
app.mount("/figures", StaticFiles(directory=config.FIG_DIR), name="figures")


def _auth(authorization: str | None):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="invalid or missing API key")


class GenerateRequest(BaseModel):
    exam: str = "JEE Advanced"
    subject: str = "Physics"
    chapter: str = Field(..., description="must be a chapter from GET /chapters")
    concept: str | None = None
    difficulty: str = Field("3-4", description="single '3' or range '3-4' on a 1-5 scale")
    type: str = Field("MCQ_single", description="MCQ_single | MCQ_multi | integer | numeric")
    count: int = Field(5, ge=1, le=MAX_COUNT)
    exemplars: int = Field(3, ge=1, le=8)
    require_figure: bool = Field(False, description="force every question to include an SVG diagram")


@app.get("/health")
def health():
    llm = LLM()
    return {"status": "ok", "llm_reachable": bool(llm.ok),
            "llm_error": None if llm.ok else llm.last_error,
            "bank_verified": Store().stats()["verified_unique"]}


@app.get("/chapters")
def chapters(exam: str = "JEE Advanced", subject: str = "Physics"):
    """Populate the frontend's topic picker. Shows which chapters have exemplars banked."""
    tax = syllabus.get_taxonomy(exam, subject)
    store = Store()
    banked = store.chapter_counts(exam, subject)
    # A chapter is generatable if this exam has exemplars OR its companion exam does
    # (NEET Phy/Chem borrow from JEE Main — same syllabus). `exemplars_banked` stays
    # the number the generator can actually draw on, so existing "> 0" filters in the
    # frontend keep working; `exemplars_own` breaks out this exam's own questions.
    fb = syllabus.exemplar_fallback(exam, subject)
    borrowed = store.chapter_counts(*fb) if fb else {}
    return {"exam": exam, "subject": subject,
            "exemplar_fallback_exam": fb[0] if fb else None,
            "chapters": [
                {"chapter": c, "concepts": list(tax[c]["concepts"].keys()),
                 "exemplars_banked": banked.get(c, 0) + borrowed.get(c, 0),
                 "exemplars_own": banked.get(c, 0)}
                for c in tax]}


@app.get("/pool")
def pool(exam: str = "JEE Advanced", subject: str = "Physics", chapter: str = "",
         difficulty: str = "3-4", type: str = "MCQ_single", count: int = 5, exclude: str = ""):
    """INSTANT serving from the pre-generated SHARED pool — no LLM, no auth (no token cost).
    This is the frontend's hot path: every student draws from the same pool built by
    `run.py batch-generate`. Pass `exclude` = comma-separated ids the student has already
    seen so they never repeat. When a student drains a cell (fewer than `count` returned),
    the frontend falls back to POST /generate to top up (which also refills the pool)."""
    parts = difficulty.split("-")
    try:
        dmin, dmax = int(parts[0]), int(parts[-1])
    except ValueError:
        raise HTTPException(status_code=400, detail="difficulty must be '3' or '3-4'")
    seen = [e for e in exclude.split(",") if e][:400]
    qs = Store().pool_questions(exam=exam, subject=subject, chapter=chapter or None,
                                qtype=type, dmin=dmin, dmax=dmax,
                                exclude_ids=seen or None, limit=min(count, MAX_COUNT))
    return {"exam": exam, "subject": subject, "chapter": chapter, "difficulty": difficulty,
            "count": len(qs), "exhausted": len(qs) < count, "questions": qs}


@app.get("/pool/stats")
def pool_stats(exam: str = "JEE Advanced", subject: str = "Physics"):
    """Ops view: how deep the pre-generated pool is per chapter (for dashboards / batch-fill)."""
    st = Store().pool_stats(exam, subject)
    by_ch = {}
    for (ch, d, qt), n in st.items():
        by_ch[ch] = by_ch.get(ch, 0) + n
    return {"exam": exam, "subject": subject, "pool_total": sum(by_ch.values()),
            "by_chapter": dict(sorted(by_ch.items(), key=lambda x: -x[1]))}


@app.post("/generate")
def generate(req: GenerateRequest, authorization: str | None = Header(default=None)):
    """Generate a NEW test. Returns questions (LaTeX), options, answer_key, solutions.
    Synchronous — 5 questions typically 20-60s on gpt-4o. Use a generous client timeout."""
    _auth(authorization)
    parts = req.difficulty.split("-")
    try:
        dmin, dmax = int(parts[0]), int(parts[-1])
    except ValueError:
        raise HTTPException(status_code=400, detail="difficulty must be '3' or '3-4'")
    spec = {"exam": req.exam, "subject": req.subject, "chapter": req.chapter,
            "concept": req.concept, "qtype": req.type, "dmin": dmin, "dmax": dmax,
            "require_figure": req.require_figure}

    llm = LLM()
    if not llm.ok:
        raise HTTPException(status_code=503, detail=f"LLM not reachable: {llm.last_error}")
    report = generator.generate_test(Store(), spec, llm=llm,
                                     count=req.count, k_exemplars=req.exemplars)
    if report.get("error"):
        raise HTTPException(status_code=400, detail=report["error"])
    return report
