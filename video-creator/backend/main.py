"""
TrigunAI Video Creator — API Server with Job Queue + WebSocket

Run on EC2:
  cd /home/ubuntu/video-creator-backend
  source /home/ubuntu/audio_pipeline/venv/bin/activate
  pip install fastapi uvicorn python-multipart websockets

  # Start API server
  uvicorn main:app --host 0.0.0.0 --port 8010 --reload &

  # Start worker (same machine — processes all job types)
  python3 worker.py --id local-gpu-1 --types voice,slide,music,avatar,render &
"""

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import json
import asyncio
import threading
import time

from db import (
    create_project, get_project, update_project_status, list_projects,
    create_job, get_job, get_project_jobs, get_queue_stats,
)

app = FastAPI(title="TrigunAI Video Creator", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory
OUTPUT_DIR = os.environ.get("VIDEO_CREATOR_OUTPUT", "/home/ubuntu/video-creator-data")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "voice"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "slides"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "music"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "avatar"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "render"), exist_ok=True)

app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

# ============================================================
# Custom shaders — paste GLSL from Shader Studio (studio.trigunai.com)
# ============================================================
import re as _re
import subprocess as _sp
from services import shader_service as _shaders
from services.shader_translate import translate_glsl as _translate

_SHADER_SRC_DIR = os.path.join(os.path.dirname(__file__), "shaders")
_SHADER_OUT_DIR = os.path.join(OUTPUT_DIR, "shaders")
os.makedirs(_SHADER_OUT_DIR, exist_ok=True)
_CUSTOM_REGISTRY = os.path.join(_SHADER_OUT_DIR, "custom_shaders.json")


def _load_custom_shaders():
    if os.path.exists(_CUSTOM_REGISTRY):
        try:
            return json.load(open(_CUSTOM_REGISTRY))
        except Exception:
            return {}
    return {}


def _save_custom_shaders(reg):
    json.dump(reg, open(_CUSTOM_REGISTRY, "w"), indent=2)


@app.on_event("startup")
def _register_custom_shaders():
    """Re-register persisted custom shaders into the render service on boot."""
    for sid, t in _load_custom_shaders().items():
        if os.path.exists(os.path.join(_SHADER_SRC_DIR, t["file"])):
            _shaders.SHADER_TEMPLATES[sid] = {
                "file": t["file"], "name": t["name"],
                "desc": t.get("desc", "Imported from Shader Studio"),
                "mood": "custom", "colors": "", "category": "custom",
            }


class CustomShaderRequest(BaseModel):
    name: str
    glsl: str
    params: Optional[dict] = None


@app.get("/api/shaders")
def list_shaders_endpoint():
    """Built-in + custom shader templates for the Visual Builder picker."""
    custom = _load_custom_shaders()
    out = []
    for key, t in _shaders.SHADER_TEMPLATES.items():
        jpg = os.path.join(_SHADER_OUT_DIR, f"{key}.jpg")
        out.append({
            "id": key, "name": t.get("name", key), "desc": t.get("desc", ""),
            "category": t.get("category", ""), "custom": key in custom,
            "preview_url": f"/output/shaders/{key}.jpg" if os.path.exists(jpg) else None,
        })
    return {"shaders": out}


@app.post("/api/shader/custom")
def add_custom_shader(req: CustomShaderRequest):
    """
    Accept raw Shader Studio GLSL, auto-translate to the pipeline contract,
    validate by rendering one short clip, register it, return a preview.
    """
    sid = "custom_" + (_re.sub(r"[^a-z0-9]+", "_", req.name.lower()).strip("_")[:40] or "shader")
    try:
        translated, report = _translate(req.glsl, req.params or {})
    except Exception as e:
        return {"ok": False, "error": f"translate failed: {e}"}

    fname = f"{sid}.glsl"
    with open(os.path.join(_SHADER_SRC_DIR, fname), "w") as f:
        f.write(translated)
    _shaders.SHADER_TEMPLATES[sid] = {
        "file": fname, "name": req.name, "desc": "Imported from Shader Studio",
        "mood": "custom", "colors": "", "category": "custom",
    }

    # Validate by compiling+rendering a short preview on the GPU.
    try:
        mp4 = os.path.join(_SHADER_OUT_DIR, f"{sid}.mp4")
        _shaders.render_shader_video(shader_name=sid, audio_path=None,
                                     output_path=mp4, duration=4.0, fps=24,
                                     width=640, height=360)
        jpg = os.path.join(_SHADER_OUT_DIR, f"{sid}.jpg")
        _sp.run(["ffmpeg", "-y", "-ss", "2", "-i", mp4, "-frames:v", "1", jpg],
                stderr=_sp.DEVNULL)
    except Exception as e:
        _shaders.SHADER_TEMPLATES.pop(sid, None)
        try:
            os.remove(os.path.join(_SHADER_SRC_DIR, fname))
        except OSError:
            pass
        return {"ok": False, "error": f"compile/render failed: {e}", "report": report}

    reg = _load_custom_shaders()
    reg[sid] = {"name": req.name, "file": fname,
                "desc": "Imported from Shader Studio", "report": report}
    _save_custom_shaders(reg)
    return {"ok": True, "id": sid, "report": report,
            "preview_url": f"/output/shaders/{sid}.mp4"}


class ShaderBgRequest(BaseModel):
    shader: str
    duration: float = 30.0
    audio_url: Optional[str] = None   # path under OUTPUT_DIR to react to
    width: int = 1920
    height: int = 1080
    fps: int = 30


@app.post("/api/shader/render-bg")
def render_shader_background(req: ShaderBgRequest):
    """Render a full-resolution shader background clip (optionally voice-reactive)."""
    if req.shader not in _shaders.SHADER_TEMPLATES:
        return {"ok": False, "error": f"unknown shader '{req.shader}'"}
    audio_path = None
    if req.audio_url:
        cand = req.audio_url.replace("/output/", OUTPUT_DIR + "/")
        if os.path.exists(cand):
            audio_path = cand
    out = os.path.join(_SHADER_OUT_DIR, f"bg_{req.shader}.mp4")
    try:
        r = _shaders.render_shader_video(shader_name=req.shader, audio_path=audio_path,
                                         output_path=out, duration=req.duration,
                                         fps=req.fps, width=req.width, height=req.height)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "url": f"/output/shaders/bg_{req.shader}.mp4",
            "frames": r["frames"], "duration": r["duration"]}

# Voice library
VOICE_DIR = "/home/ubuntu/audio_pipeline/voice_library"
VOICE_INDEX = os.path.join(VOICE_DIR, "voice_index.json")


# ============================================================
# WebSocket — real-time progress to frontend
# ============================================================

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # project_id -> [websockets]

    async def connect(self, ws: WebSocket, project_id: str):
        await ws.accept()
        if project_id not in self.active:
            self.active[project_id] = []
        self.active[project_id].append(ws)

    def disconnect(self, ws: WebSocket, project_id: str):
        if project_id in self.active:
            self.active[project_id] = [w for w in self.active[project_id] if w != ws]

    async def broadcast(self, project_id: str, message: dict):
        if project_id in self.active:
            dead = []
            for ws in self.active[project_id]:
                try:
                    await ws.send_json(message)
                except:
                    dead.append(ws)
            for ws in dead:
                self.active[project_id].remove(ws)


ws_manager = ConnectionManager()

# Hook for worker to notify via WebSocket
def _ws_notify_sync(msg):
    """Called from worker thread — bridges to async WebSocket."""
    project_id = msg.get("project_id", "")
    asyncio.run_coroutine_threadsafe(
        ws_manager.broadcast(project_id, msg),
        _loop
    )

_loop = None

@app.on_event("startup")
async def startup():
    global _loop
    _loop = asyncio.get_event_loop()

    # Start inline worker in a thread (for single-machine deployment)
    if os.environ.get("RUN_WORKER", "1") == "1":
        from worker import worker_loop, set_ws_notify
        set_ws_notify(_ws_notify_sync)
        t = threading.Thread(
            target=worker_loop,
            args=("inline-worker", ["voice", "slide", "music", "avatar", "render"], 2.0),
            daemon=True,
        )
        t.start()
        print("Inline worker started in background thread")


@app.websocket("/ws/project/{project_id}")
async def ws_project(ws: WebSocket, project_id: str):
    await ws_manager.connect(ws, project_id)
    try:
        while True:
            # Keep alive — client can send pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
            elif data == "status":
                jobs = get_project_jobs(project_id)
                await ws.send_json({
                    "type": "status",
                    "jobs": [{
                        "id": j["id"],
                        "type": j["type"],
                        "status": j["status"],
                        "progress": j["progress"],
                        "step": j["step"],
                        "result": j["result"],
                        "error": j["error"],
                    } for j in jobs]
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(ws, project_id)


# ============================================================
# Models
# ============================================================

class SceneInput(BaseModel):
    id: str
    title: str
    text: str
    tone: str = "female_confident"
    speed: float = 0.75
    template: str = "T6"
    slide_title: Optional[str] = None
    slide_body: Optional[str] = None
    slide_accent: Optional[str] = "blue"
    slide_layout: Optional[str] = "center"

class CreateVideoRequest(BaseModel):
    project_name: str = "Untitled"
    scenes: list[SceneInput]
    music_prompt: str = "Ambient electronic, inspiring, warm, professional presentation"
    music_volume: float = 0.08
    presenter_image: Optional[str] = None
    generate_avatar: bool = False
    background_shader: Optional[str] = None   # shader id for the video background

class SingleVoiceRequest(BaseModel):
    text: str
    tone: str = "female_confident"
    speed: float = 0.75


# ============================================================
# Routes: Create full video project (the main endpoint)
# ============================================================

@app.post("/api/project/create")
async def create_video_project(req: CreateVideoRequest):
    """
    Create a full video project with all child jobs.
    The worker automatically picks up and processes jobs in order.
    Frontend connects via WebSocket for real-time progress.
    """
    # Create project
    config = {
        "scenes": [s.dict() for s in req.scenes],
        "music_prompt": req.music_prompt,
        "music_volume": req.music_volume,
        "presenter_image": req.presenter_image,
        "generate_avatar": req.generate_avatar,
        "background_shader": req.background_shader,
    }
    project_id = create_project(req.project_name, config)
    update_project_status(project_id, "queued")

    voice_job_ids = []
    slide_job_ids = []

    # Create voice jobs (priority 1 — first to process)
    for scene in req.scenes:
        jid = create_job(project_id, "voice", {
            "text": scene.text,
            "tone": scene.tone,
            "speed": scene.speed,
            "scene_id": scene.id,
            "output_dir": os.path.join(OUTPUT_DIR, "voice"),
        }, priority=1)
        voice_job_ids.append(jid)

    # Create slide jobs (priority 2 — can run in parallel with voice on CPU)
    for scene in req.scenes:
        jid = create_job(project_id, "slide", {
            "title": scene.slide_title or scene.title,
            "body": scene.slide_body or "",
            "accent_color": scene.slide_accent or "blue",
            "layout": scene.slide_layout or "center",
            "scene_id": scene.id,
            "transparent": bool(req.background_shader),
            "output_dir": os.path.join(OUTPUT_DIR, "slides"),
        }, priority=2)
        slide_job_ids.append(jid)

    # Create music job (priority 3)
    music_job_id = create_job(project_id, "music", {
        "prompt": req.music_prompt,
        "duration": 300,  # will be trimmed to actual voice length
        "output_dir": os.path.join(OUTPUT_DIR, "music"),
    }, priority=3)

    # Create avatar job (priority 4 — depends on all voice jobs)
    avatar_job_id = None
    if req.generate_avatar and req.presenter_image:
        avatar_job_id = create_job(project_id, "avatar", {
            "image_path": req.presenter_image,
            "output_dir": os.path.join(OUTPUT_DIR, "avatar"),
            # audio_path will be set by render agent after voice concat
        }, priority=4, depends_on=voice_job_ids)

    # Create final render job (priority 5 — depends on everything)
    all_deps = voice_job_ids + slide_job_ids + [music_job_id]
    if avatar_job_id:
        all_deps.append(avatar_job_id)

    render_job_id = create_job(project_id, "render", {
        "project": config,
        "output_dir": os.path.join(OUTPUT_DIR, "render"),
        "music_volume": req.music_volume,
    }, priority=5, depends_on=all_deps)

    total_jobs = len(voice_job_ids) + len(slide_job_ids) + 1 + (1 if avatar_job_id else 0) + 1

    return {
        "project_id": project_id,
        "total_jobs": total_jobs,
        "voice_jobs": voice_job_ids,
        "slide_jobs": slide_job_ids,
        "music_job": music_job_id,
        "avatar_job": avatar_job_id,
        "render_job": render_job_id,
        "ws_url": f"/ws/project/{project_id}",
    }


# ============================================================
# Routes: Single voice generation (for preview in Voice Studio)
# ============================================================

@app.post("/api/voice/generate")
async def generate_single_voice(req: SingleVoiceRequest):
    """Quick voice generation for preview — bypasses queue."""
    from services.f5tts_service import generate_speech
    import uuid

    job_id = f"preview_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(OUTPUT_DIR, "voice", f"{job_id}.wav")

    result = generate_speech(text=req.text, tone=req.tone, speed=req.speed, output_path=output_path)

    return {
        "audio_url": f"/output/voice/{job_id}.wav",
        "duration": result["duration"],
    }


# ============================================================
# Routes: Job & Project status
# ============================================================

@app.get("/api/project/{project_id}")
async def get_project_status(project_id: str):
    project = get_project(project_id)
    if not project:
        return {"error": "Project not found"}

    jobs = get_project_jobs(project_id)

    total = len(jobs)
    completed = sum(1 for j in jobs if j["status"] == "completed")
    failed = sum(1 for j in jobs if j["status"] == "failed")
    processing = sum(1 for j in jobs if j["status"] == "processing")
    queued = sum(1 for j in jobs if j["status"] == "queued")

    overall_progress = int((completed / total) * 100) if total > 0 else 0

    # Find the render job result (final video)
    render_jobs = [j for j in jobs if j["type"] == "render"]
    final_video = None
    if render_jobs and render_jobs[0]["status"] == "completed" and render_jobs[0]["result"]:
        video_path = render_jobs[0]["result"].get("video_path", "")
        if video_path:
            rel = video_path.replace(OUTPUT_DIR, "")
            final_video = f"/output{rel}"

    return {
        "project": project,
        "jobs": [{
            "id": j["id"],
            "type": j["type"],
            "status": j["status"],
            "progress": j["progress"],
            "step": j["step"],
            "result": j["result"],
            "error": j["error"],
        } for j in jobs],
        "summary": {
            "total": total,
            "completed": completed,
            "processing": processing,
            "queued": queued,
            "failed": failed,
            "overall_progress": overall_progress,
        },
        "final_video": final_video,
    }


@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"status": "not_found"}
    return {
        "id": job["id"],
        "type": job["type"],
        "status": job["status"],
        "progress": job["progress"],
        "step": job["step"],
        "result": job["result"],
        "error": job["error"],
    }


@app.get("/api/projects")
async def list_all_projects():
    projects = list_projects()
    return {"projects": projects}


@app.get("/api/queue/stats")
async def queue_stats():
    return get_queue_stats()


# ============================================================
# Routes: Voices library
# ============================================================

@app.get("/api/voices")
async def get_voices():
    if os.path.exists(VOICE_INDEX):
        with open(VOICE_INDEX) as f:
            voices = json.load(f)
        return {"voices": voices}
    return {"voices": {}}


# ============================================================
# Routes: Upload
# ============================================================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    import uuid
    fid = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{fid}{ext}"
    upload_dir = os.path.join(OUTPUT_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "file_url": f"/output/uploads/{filename}",
        "file_path": filepath,
        "size": len(content),
    }


# ============================================================
# Health
# ============================================================

@app.get("/api/health")
async def health():
    import subprocess
    try:
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.free", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except:
        gpu = "No GPU detected"

    stats = get_queue_stats()
    return {
        "status": "ok",
        "gpu": gpu,
        "queue": stats,
        "voices_available": os.path.exists(VOICE_INDEX),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
