"""Acharya University — Phase 1 web server.

Self-contained FastAPI app. Does NOT touch the live Acharya / Gurukul data.
Single local user by default (?u=deepak). Run:

    uvicorn server:app --reload --port 8010
"""
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

import llm
import store
from agents import advisor, tutor

app = FastAPI(title="Acharya University")

HERE = os.path.dirname(__file__)
WEB = os.path.join(HERE, "web")


@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(WEB, "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/health")
def health():
    return {"ok": True, "llm": llm.available()}


# ---- Advisor: interview + build curriculum -------------------------------
@app.post("/api/advisor/interview")
async def advisor_interview(req: Request):
    body = await req.json()
    goal = (body.get("goal") or "").strip()
    history = body.get("history") or []
    if not goal:
        return JSONResponse({"error": "goal required"}, status_code=400)
    return advisor.interview(goal, history)


@app.post("/api/advisor/build")
async def advisor_build(req: Request):
    body = await req.json()
    user_id = (body.get("user_id") or "deepak").strip()
    goal = (body.get("goal") or "").strip()
    history = body.get("history") or []
    if not goal:
        return JSONResponse({"error": "goal required"}, status_code=400)
    curr = advisor.build(user_id, goal, history)
    if not curr:
        return JSONResponse({"error": "curriculum generation failed"}, status_code=502)
    store.save_curriculum(curr)
    learner = store.get_learner(user_id)
    learner["goals"] = [curr["curriculum_id"]] + [g for g in learner.get("goals", [])]
    store.save_learner(learner)
    return {"curriculum_id": curr["curriculum_id"]}


# ---- Learner + curriculum reads ------------------------------------------
@app.get("/api/learner")
def learner(u: str = "deepak"):
    store.get_learner(u)
    return {"user_id": u, "curricula": store.list_curricula(u)}


@app.get("/api/curriculum/{cid}")
def curriculum(cid: str):
    c = store.get_curriculum(cid)
    if not c:
        return JSONResponse({"error": "not found"}, status_code=404)
    return c


# ---- Tutor: teach a unit --------------------------------------------------
def _find_unit(curr: dict, unit_id: str) -> dict | None:
    return next((u for u in curr.get("units", []) if u.get("unit_id") == unit_id), None)


@app.get("/api/session/{cid}/{unit_id}")
def get_session(cid: str, unit_id: str):
    return store.get_session(cid, unit_id)


@app.post("/api/tutor/step")
async def tutor_step(req: Request):
    body = await req.json()
    cid = body.get("curriculum_id")
    unit_id = body.get("unit_id")
    message = (body.get("message") or "").strip()
    curr = store.get_curriculum(cid)
    unit = _find_unit(curr, unit_id) if curr else None
    if not unit:
        return JSONResponse({"error": "unit not found"}, status_code=404)
    session = store.get_session(cid, unit_id)
    if message:
        session["history"].append({"role": "user", "content": message})
    reply = tutor.step(curr, unit, session["history"])
    if reply is None:
        return JSONResponse({"error": "tutor unavailable"}, status_code=502)
    session["history"].append({"role": "assistant", "content": reply})
    store.save_session(cid, unit_id, session)
    return {"reply": reply}


# ---- Mastery: recall grading (code owns 'solid' promotion) ----------------
@app.post("/api/recall/grade")
async def recall_grade(req: Request):
    body = await req.json()
    cid = body.get("curriculum_id")
    unit_id = body.get("unit_id")
    concept_key = body.get("concept_key")
    attempt = (body.get("attempt") or "").strip()
    curr = store.get_curriculum(cid)
    unit = _find_unit(curr, unit_id) if curr else None
    if not unit:
        return JSONResponse({"error": "unit not found"}, status_code=404)
    concept = next((c for c in unit.get("concepts", []) if c.get("key") == concept_key), None)
    if not concept:
        return JSONResponse({"error": "concept not found"}, status_code=404)
    result = tutor.grade_recall(concept.get("recall", ""), concept.get("answer", ""), attempt)
    # code grants mastery — model only informs the decision
    concept["mastery"] = 1.0 if result["correct"] else max(0.5, concept.get("mastery", 0.0))
    solid = sum(1 for c in unit["concepts"] if c.get("mastery", 0) >= 1.0)
    unit["mastery"] = round(solid / max(1, len(unit["concepts"])), 2)
    if unit["mastery"] >= 1.0:
        unit["status"] = "done"
        units = curr["units"]
        idx = units.index(unit)
        if idx + 1 < len(units) and units[idx + 1]["status"] == "locked":
            units[idx + 1]["status"] = "active"
    store.save_curriculum(curr)
    return {"correct": result["correct"], "feedback": result["feedback"],
            "concept_mastery": concept["mastery"], "unit_mastery": unit["mastery"],
            "unit_status": unit["status"]}
