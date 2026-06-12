"""
TrigunAI Studio — FastAPI Backend

The API server that wraps Claude agents with tools. Handles:
- Job creation (mocap render, scene build, etc.)
- Agent chat (free-form conversation with any agent)
- Live streaming of agent progress via SSE
- Artifact storage and download
- Subjective approval gates

Run: uvicorn server:app --port 9000 --reload
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from agents.runner import run_agent, AgentEvent
from agents.registry import get_agent_tools, AGENT_REGISTRY

# --- App ---

app = FastAPI(
    title="TrigunAI Studio",
    description="AI-powered 3D content creation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1: allow all; Phase 3: lock down
    allow_methods=["*"],
    allow_headers=["*"],
)

# Artifact storage
ARTIFACTS_DIR = Path(os.getenv("STUDIO_ARTIFACTS_DIR", "./artifacts"))
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store (Phase 1; Phase 3: SQLite/Postgres)
jobs: dict[str, dict] = {}


# --- Models ---

class ChatRequest(BaseModel):
    agent: str = "trigunai-training"
    message: str
    job_context: str | None = None


class ChatResponse(BaseModel):
    response: str
    agent: str
    tokens_used: int
    tool_calls: int


class JobCreateRequest(BaseModel):
    type: str  # "mocap_render" | "scene_build" | "enrich_asset"
    params: dict = {}


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


# --- Routes ---

@app.get("/")
async def root():
    """Serve the dashboard."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return {"service": "TrigunAI Studio", "version": "0.1.0", "agents": list(AGENT_REGISTRY.keys())}


@app.get("/api/health")
async def health():
    """System health check."""
    return {
        "status": "ok",
        "agents": list(AGENT_REGISTRY.keys()),
        "jobs_in_memory": len(jobs),
        "artifacts_dir": str(ARTIFACTS_DIR),
    }


@app.get("/api/agents")
async def list_agents():
    """List available agents with their tool counts."""
    result = []
    for name in AGENT_REGISTRY:
        tools = get_agent_tools(name)
        result.append({
            "name": name,
            "tools": [t.name for t in tools],
            "tool_count": len(tools),
        })
    return result


# --- Chat endpoint (synchronous — waits for full response) ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to an agent and get a response. Runs the full tool loop."""
    if req.agent not in AGENT_REGISTRY:
        raise HTTPException(400, f"Unknown agent: {req.agent}. Available: {list(AGENT_REGISTRY.keys())}")

    tools = get_agent_tools(req.agent)
    final_text = ""
    total_tokens = 0
    tool_calls_count = 0

    async for event in run_agent(req.agent, req.message, tools):
        if event.type == "text":
            final_text = event.data.get("content", "")
        elif event.type == "done":
            total_tokens = event.data.get("total_tokens", 0)
            tool_calls_count = event.data.get("tool_calls_count", 0)
        elif event.type == "error":
            raise HTTPException(500, event.data.get("message", "Agent error"))

    return ChatResponse(
        response=final_text,
        agent=req.agent,
        tokens_used=total_tokens,
        tool_calls=tool_calls_count,
    )


# --- Chat streaming endpoint (SSE — real-time events) ---

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream agent events in real-time via SSE."""
    if req.agent not in AGENT_REGISTRY:
        raise HTTPException(400, f"Unknown agent: {req.agent}")

    tools = get_agent_tools(req.agent)

    async def event_generator():
        async for event in run_agent(req.agent, req.message, tools):
            yield {"event": event.type, "data": json.dumps(event.data)}

    return EventSourceResponse(event_generator())


# --- Job endpoints ---

@app.post("/api/jobs")
async def create_job(req: JobCreateRequest):
    """Create a new job. Returns job ID for tracking."""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = {
        "id": job_id,
        "type": req.type,
        "status": "queued",
        "params": req.params,
        "created_at": time.time(),
        "events": [],
        "artifacts": [],
        "result": None,
    }
    jobs[job_id] = job

    # Start job in background
    asyncio.create_task(_run_job(job_id))

    return {"id": job_id, "status": "queued", "stream_url": f"/api/jobs/{job_id}/stream"}


async def _run_job(job_id: str):
    """Execute a job using the appropriate agent."""
    job = jobs[job_id]
    job["status"] = "running"

    # Map job types to agent + message
    type_map = {
        "mocap_render": (
            "trigunai-training",
            "Render an MP4 from the mocap session. "
            f"Parameters: {json.dumps(job['params'])}. "
            "Use render_mp4 tool to start the render on EC2."
        ),
        "ec2_health": (
            "trigunai-training",
            "Check the health of all EC2 services. "
            "Report Docker container status, OVRTX health, and GPU usage."
        ),
        "phase_status": (
            "trigunai-orchestrator",
            "What phase are we in? Check the current status of all phase gates."
        ),
        "generate_handoff": (
            "trigunai-orchestrator",
            f"Generate a handoff document. Direction: {job['params'].get('direction', 'training_to_vr')}. "
            f"Version: {job['params'].get('version', 1)}."
        ),
    }

    agent_name, message = type_map.get(job["type"], ("trigunai-training", json.dumps(job)))
    tools = get_agent_tools(agent_name)

    try:
        async for event in run_agent(agent_name, message, tools):
            job["events"].append({"type": event.type, "data": event.data, "ts": event.timestamp})
            if event.type == "text":
                job["result"] = event.data.get("content", "")
            elif event.type == "done":
                job["status"] = "completed"
            elif event.type == "error":
                job["status"] = "failed"
                job["result"] = event.data.get("message", "Unknown error")
    except Exception as e:
        job["status"] = "failed"
        job["result"] = str(e)


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return {
        "id": job["id"],
        "type": job["type"],
        "status": job["status"],
        "result": job["result"],
        "artifacts": job["artifacts"],
        "events_count": len(job["events"]),
        "created_at": job["created_at"],
    }


@app.get("/api/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """Stream job events via SSE."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        job = jobs[job_id]
        sent = 0
        while True:
            # Send any new events
            while sent < len(job["events"]):
                evt = job["events"][sent]
                yield {"event": evt["type"], "data": json.dumps(evt["data"])}
                sent += 1

            # Check if job is done
            if job["status"] in ("completed", "failed"):
                yield {"event": "done", "data": json.dumps({"status": job["status"]})}
                return

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    return [
        {
            "id": j["id"],
            "type": j["type"],
            "status": j["status"],
            "created_at": j["created_at"],
        }
        for j in sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)
    ]


# --- Artifact endpoints ---

@app.get("/api/artifacts/{artifact_id}")
async def download_artifact(artifact_id: str):
    """Download an artifact file."""
    # Search for file in artifacts dir
    for f in ARTIFACTS_DIR.rglob("*"):
        if f.stem == artifact_id or f.name == artifact_id:
            return FileResponse(f)
    raise HTTPException(404, "Artifact not found")


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=9000, reload=True)
