"""
Scene Composer Agent — FastAPI service that wraps the OSM city pipeline
(osm_to_usd.py + city_add_colliders.py + city_enrich_textures.py) into the
same API contract as the NVIDIA Material/Physics/Texture agents.

Endpoints:
  POST /pipeline                          → submit a city build
  GET  /pipeline/{sid}/status             → status + step + progress
  GET  /artifacts/{sid}/usd               → city.usd
  GET  /artifacts/{sid}/textures          → zip of PBR maps
  GET  /artifacts/{sid}/meta              → meta.json
  GET  /artifacts/{sid}/preview-glb       → decimated GLB (best-effort)
  GET  /health

Runs on EC2 host (not inside isaaclab). Shells out to the three scripts and
calls the Texture Agent on localhost:8004 (mounted into the container as the
host network). One sequential worker thread per process — sufficient for the
expected throughput (a handful of cities per session).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse


# ──────────────────────────────────────────────────────────────────────
# Config — these can be overridden via env vars so the docker container
# binds reliably without baking host paths into the image.
# ──────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(os.environ.get("COMPOSER_SCRIPTS_DIR", "/opt/scripts"))
OUT_BASE = Path(os.environ.get("COMPOSER_OUT_BASE", "/home/ubuntu/assets/cities"))
PY_BIN = os.environ.get("COMPOSER_PYTHON", sys.executable)
BLENDER_BIN = os.environ.get("COMPOSER_BLENDER", "blender45")
TEXTURE_AGENT_BASE = os.environ.get(
    "COMPOSER_TEXTURE_AGENT_BASE", "http://localhost:8004"
)

STEP_NAMES = [
    "osm_fetch",
    "geometry_extrude",
    "collider_bake",
    "texture_generate",
    "texture_apply",
]
# osm_fetch and geometry_extrude both happen inside osm_to_usd.py — we
# attribute the first ~30% of that script to fetch, remaining to extrude.
STEP_WEIGHTS = {
    "osm_fetch": 0.10,
    "geometry_extrude": 0.20,
    "collider_bake": 0.05,
    "texture_generate": 0.55,
    "texture_apply": 0.10,
}


# ──────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────


@dataclass
class Session:
    session_id: str
    fingerprint: str
    params: dict
    status: str = "queued"  # queued | running | completed | failed
    current_step: Optional[str] = None
    completed_steps: list = field(default_factory=list)
    started_at: float = 0.0
    finished_at: Optional[float] = None
    error: Optional[str] = None
    out_dir: Optional[Path] = None
    usd_path: Optional[Path] = None
    meta_path: Optional[Path] = None
    glb_path: Optional[Path] = None

    @property
    def elapsed(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.finished_at or time.time()
        return end - self.started_at

    @property
    def percent(self) -> int:
        if self.status == "completed":
            return 100
        cum = 0.0
        for step in STEP_NAMES:
            if step in self.completed_steps:
                cum += STEP_WEIGHTS[step]
            elif step == self.current_step:
                cum += STEP_WEIGHTS[step] * 0.5
                break
            else:
                break
        return int(round(cum * 100))


SESSIONS: dict[str, Session] = {}
FINGERPRINT_INDEX: dict[str, str] = {}  # fingerprint → session_id
LOCK = threading.Lock()


def _fingerprint(lat: float, lon: float, radius_m: float, prompt: str) -> str:
    """Round inputs so trivially-equal queries (lat=40.758 vs 40.7580001) collide."""
    key = json.dumps(
        {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "radius_m": round(radius_m, 1),
            "prompt": prompt.strip().lower(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ──────────────────────────────────────────────────────────────────────
# Worker
# ──────────────────────────────────────────────────────────────────────


def _run(cmd: list[str], log_file: Path) -> None:
    """Run a subprocess, streaming combined stdout/stderr to log_file. Raise on non-zero."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "ab") as logf:
        logf.write(f"\n$ {' '.join(cmd)}\n".encode())
        logf.flush()
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        tail = log_file.read_text(errors="ignore").splitlines()[-30:]
        raise RuntimeError(
            f"command failed (exit {proc.returncode}): {' '.join(cmd)}\n"
            + "\n".join(tail)
        )


def _mark_step_started(session: Session, step: str) -> None:
    with LOCK:
        session.current_step = step


def _mark_step_done(session: Session, step: str) -> None:
    with LOCK:
        if step not in session.completed_steps:
            session.completed_steps.append(step)


def _process_session(session: Session) -> None:
    sid = session.session_id
    params = session.params
    name = params["name"]
    out_dir = OUT_BASE / name
    out_dir.mkdir(parents=True, exist_ok=True)
    session.out_dir = out_dir
    session.usd_path = out_dir / "city.usd"
    session.meta_path = out_dir / "meta.json"

    log_file = out_dir / "composer.log"
    session.started_at = time.time()
    with LOCK:
        session.status = "running"

    try:
        # Steps 1+2 are both inside osm_to_usd.py. We mark osm_fetch first,
        # then geometry_extrude once the script finishes (it does both inline).
        _mark_step_started(session, "osm_fetch")
        _run(
            [
                PY_BIN,
                str(SCRIPTS_DIR / "osm_to_usd.py"),
                "--lat",
                str(params["lat"]),
                "--lon",
                str(params["lon"]),
                "--radius",
                str(params["radius_m"]),
                "--name",
                name,
                "--out",
                str(OUT_BASE),
            ],
            log_file,
        )
        _mark_step_done(session, "osm_fetch")
        _mark_step_done(session, "geometry_extrude")

        _mark_step_started(session, "collider_bake")
        _run(
            [
                PY_BIN,
                str(SCRIPTS_DIR / "city_add_colliders.py"),
                "--city",
                str(session.usd_path),
            ],
            log_file,
        )
        _mark_step_done(session, "collider_bake")

        # Steps 4 (generate) + 5 (apply) both inside city_enrich_textures.py.
        _mark_step_started(session, "texture_generate")
        env = os.environ.copy()
        env["TEXTURE_AGENT_BASE"] = TEXTURE_AGENT_BASE  # honored if user patches script later
        _run(
            [
                PY_BIN,
                str(SCRIPTS_DIR / "city_enrich_textures.py"),
                "--city",
                str(session.usd_path),
                "--prompt",
                params["facade_prompt"],
            ],
            log_file,
        )
        _mark_step_done(session, "texture_generate")
        _mark_step_done(session, "texture_apply")

        # Best-effort preview GLB. Doesn't fail the run if Blender isn't around.
        usd_to_glb = SCRIPTS_DIR / "usd_to_glb.py"
        if usd_to_glb.exists():
            glb_path = out_dir / "city_preview.glb"
            try:
                _run(
                    [
                        BLENDER_BIN,
                        "--background",
                        "--python",
                        str(usd_to_glb),
                        "--",
                        "--input",
                        str(session.usd_path),
                        "--output",
                        str(glb_path),
                        "--decimate",
                        "0.3",
                        "--max-texture",
                        "1024",
                    ],
                    log_file,
                )
                session.glb_path = glb_path
            except Exception as e:
                # Preview is optional; log and continue.
                with open(log_file, "a") as logf:
                    logf.write(f"\n[preview-glb] skipped: {e}\n")

        with LOCK:
            session.status = "completed"
            session.current_step = None
            session.finished_at = time.time()

    except Exception as e:
        with LOCK:
            session.status = "failed"
            session.error = str(e)
            session.finished_at = time.time()
            # Release the fingerprint so a retry isn't short-circuited.
            if FINGERPRINT_INDEX.get(session.fingerprint) == sid:
                del FINGERPRINT_INDEX[session.fingerprint]


def _spawn_worker(session: Session) -> None:
    t = threading.Thread(target=_process_session, args=(session,), daemon=True)
    t.start()


# ──────────────────────────────────────────────────────────────────────
# FastAPI
# ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Scene Composer Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "scene-composer", "version": "0.1.0"}


@app.post("/pipeline")
def submit(
    lat: float = Form(...),
    lon: float = Form(...),
    radius_m: float = Form(500.0),
    name: str = Form(...),
    facade_prompt: str = Form(
        "weathered urban building façade, mixed glass and concrete, daytime"
    ),
):
    fp = _fingerprint(lat, lon, radius_m, facade_prompt)

    with LOCK:
        # Reuse if an identical request is already completed OR in-flight.
        cached_sid = FINGERPRINT_INDEX.get(fp)
        cached = SESSIONS.get(cached_sid) if cached_sid else None
        if cached and cached.status in ("queued", "running", "completed"):
            return {"session_id": cached.session_id, "cached": True}

        sid = uuid.uuid4().hex[:12]
        session = Session(
            session_id=sid,
            fingerprint=fp,
            params={
                "lat": lat,
                "lon": lon,
                "radius_m": radius_m,
                "name": name,
                "facade_prompt": facade_prompt,
            },
        )
        SESSIONS[sid] = session
        FINGERPRINT_INDEX[fp] = sid  # claim the fingerprint immediately

    _spawn_worker(session)
    return {"session_id": sid, "cached": False}


@app.get("/pipeline/{sid}/status")
def status(sid: str):
    session = SESSIONS.get(sid)
    if session is None:
        raise HTTPException(404, f"unknown session {sid}")
    return {
        "session_id": sid,
        "status": session.status,
        "current_step": (
            {"name": session.current_step} if session.current_step else None
        ),
        "completed_steps": [{"name": s} for s in session.completed_steps],
        "overall_progress": {
            "current_step": len(session.completed_steps),
            "total_steps": len(STEP_NAMES),
            "percent": session.percent,
        },
        "elapsed_seconds": int(session.elapsed),
        "error": session.error,
    }


def _require_completed(sid: str) -> Session:
    session = SESSIONS.get(sid)
    if session is None:
        raise HTTPException(404, f"unknown session {sid}")
    if session.status != "completed":
        raise HTTPException(409, f"session {sid} not completed (status={session.status})")
    return session


@app.get("/artifacts/{sid}/usd")
def artifact_usd(sid: str):
    session = _require_completed(sid)
    if not session.usd_path or not session.usd_path.exists():
        raise HTTPException(404, "city.usd missing")
    return FileResponse(
        session.usd_path,
        media_type="application/octet-stream",
        filename="city.usd",
    )


@app.get("/artifacts/{sid}/textures")
def artifact_textures(sid: str):
    session = _require_completed(sid)
    tx_dir = (session.out_dir or Path()) / "textures"
    if not tx_dir.exists():
        raise HTTPException(404, "no textures directory")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(tx_dir.iterdir()):
            if p.is_file():
                zf.write(p, arcname=f"textures/{p.name}")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{session.params["name"]}_textures.zip"'},
    )


@app.get("/artifacts/{sid}/meta")
def artifact_meta(sid: str):
    session = _require_completed(sid)
    if not session.meta_path or not session.meta_path.exists():
        raise HTTPException(404, "meta.json missing")
    return JSONResponse(json.loads(session.meta_path.read_text()))


@app.get("/artifacts/{sid}/preview-glb")
def artifact_glb(sid: str):
    session = _require_completed(sid)
    if not session.glb_path or not session.glb_path.exists():
        raise HTTPException(404, "preview GLB was not generated for this session")
    return FileResponse(
        session.glb_path,
        media_type="model/gltf-binary",
        filename="city_preview.glb",
    )
