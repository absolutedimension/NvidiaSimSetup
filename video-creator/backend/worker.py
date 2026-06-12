"""
GPU/CPU Worker Agent — picks jobs from queue, processes them, reports results.

Each worker registers with a worker_id and declares what job types it can handle.
Multiple workers can run on different machines (EC2, Azure GPU, etc.)

Run:
  GPU worker:  python3 worker.py --types voice,music,avatar --id gpu-worker-1
  CPU worker:  python3 worker.py --types slide,render --id cpu-worker-1
  All-in-one:  python3 worker.py --types voice,slide,music,avatar,render --id local-1
"""

import argparse
import time
import traceback
import os
import uuid

from db import claim_next_job, update_job_progress, complete_job, fail_job, get_queue_stats

# WebSocket notification (optional — set by the API server)
_ws_notify = None

def set_ws_notify(fn):
    global _ws_notify
    _ws_notify = fn


def notify_progress(project_id, job_id, progress, step, status="processing"):
    """Notify frontend via WebSocket if available."""
    if _ws_notify:
        _ws_notify({
            "project_id": project_id,
            "job_id": job_id,
            "progress": progress,
            "step": step,
            "status": status,
        })


class BaseAgent:
    """Base class for all processing agents."""
    job_type = "unknown"

    def process(self, job: dict) -> dict:
        """Process a job. Return result dict. Raise on failure."""
        raise NotImplementedError

    def on_progress(self, job_id, project_id, progress, step):
        update_job_progress(job_id, progress, step)
        notify_progress(project_id, job_id, progress, step)


class VoiceAgent(BaseAgent):
    """Generates voice using F5-TTS. Requires GPU."""
    job_type = "voice"
    _tts = None

    def _get_tts(self):
        if self._tts is None:
            from f5_tts.api import F5TTS
            self._tts = F5TTS()
        return self._tts

    def process(self, job: dict) -> dict:
        import json
        config = job["config"]
        text = config["text"]
        tone = config.get("tone", "female_confident")
        speed = config.get("speed", 0.75)
        output_dir = config.get("output_dir", "/home/ubuntu/video-creator-data/voice")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job['id']}.wav")

        self.on_progress(job["id"], job["project_id"], 10, "Loading voice model")

        from services.f5tts_service import generate_speech
        self.on_progress(job["id"], job["project_id"], 30, f"Generating ({tone})")

        result = generate_speech(text=text, tone=tone, speed=speed, output_path=output_path)

        self.on_progress(job["id"], job["project_id"], 100, "Done")
        return {"audio_path": output_path, "duration": result["duration"]}


class SlideAgent(BaseAgent):
    """Generates slide images. CPU only."""
    job_type = "slide"

    def process(self, job: dict) -> dict:
        config = job["config"]
        output_dir = config.get("output_dir", "/home/ubuntu/video-creator-data/slides")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job['id']}.png")

        self.on_progress(job["id"], job["project_id"], 30, "Rendering slide")

        from services.slide_service import render_slide
        render_slide(
            title=config.get("title", ""),
            body=config.get("body", ""),
            accent_color=config.get("accent_color", "blue"),
            layout=config.get("layout", "center"),
            subtitle=config.get("subtitle", ""),
            bullet_points=config.get("bullet_points"),
            screenshot_path=config.get("screenshot_path"),
            transparent=config.get("transparent", False),
            output_path=output_path,
        )

        self.on_progress(job["id"], job["project_id"], 100, "Done")
        return {"slide_path": output_path}


class MusicAgent(BaseAgent):
    """Generates background music. Requires GPU (ACE-Step) or CPU fallback."""
    job_type = "music"

    def process(self, job: dict) -> dict:
        config = job["config"]
        output_dir = config.get("output_dir", "/home/ubuntu/video-creator-data/music")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job['id']}.wav")

        self.on_progress(job["id"], job["project_id"], 20, "Generating music")

        from services.music_service import generate_music
        result = generate_music(
            prompt=config.get("prompt", "ambient inspiring background"),
            duration=config.get("duration", 180),
            output_path=output_path,
        )

        self.on_progress(job["id"], job["project_id"], 100, "Done")
        return {"audio_path": output_path, "duration": result["duration"]}


class AvatarAgent(BaseAgent):
    """Generates talking head video using Hallo2. Requires GPU (12GB+)."""
    job_type = "avatar"

    def process(self, job: dict) -> dict:
        config = job["config"]
        output_dir = config.get("output_dir", "/home/ubuntu/video-creator-data/avatar")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job['id']}.mp4")

        self.on_progress(job["id"], job["project_id"], 10, "Loading Hallo2 model")

        from services.hallo2_service import generate_avatar
        self.on_progress(job["id"], job["project_id"], 20, "Generating avatar video")

        result = generate_avatar(
            image_path=config["image_path"],
            audio_path=config["audio_path"],
            output_path=output_path,
        )

        self.on_progress(job["id"], job["project_id"], 100, "Done")
        return {"video_path": output_path, "duration": result.get("duration", 0)}


class RenderAgent(BaseAgent):
    """Assembles final video with ffmpeg. CPU only."""
    job_type = "render"

    def process(self, job: dict) -> dict:
        config = job["config"]
        output_dir = config.get("output_dir", "/home/ubuntu/video-creator-data/render")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{job['id']}.mp4")

        self.on_progress(job["id"], job["project_id"], 10, "Assembling video")

        # Resolve per-scene asset paths from the completed voice/slide/music jobs.
        from db import get_project_jobs
        jobs = get_project_jobs(job["project_id"])
        voice_by_scene, slide_by_scene, music_path = {}, {}, None
        for j in jobs:
            res = j.get("result") or {}
            sid = (j.get("config") or {}).get("scene_id")
            if j["type"] == "voice" and res:
                voice_by_scene[sid] = res
            elif j["type"] == "slide" and res:
                slide_by_scene[sid] = res
            elif j["type"] == "music" and res:
                music_path = res.get("audio_path")

        proj = dict(config["project"])
        enriched = []
        for sc in proj.get("scenes", []):
            sid = sc.get("id")
            v = voice_by_scene.get(sid, {})
            s = slide_by_scene.get(sid, {})
            enriched.append({
                **sc,
                "voice_path": v.get("audio_path", ""),
                "slide_path": s.get("slide_path", ""),
                "duration": v.get("duration", sc.get("duration", 10)),
            })
        proj["scenes"] = enriched
        proj["music_path"] = music_path
        proj["music_volume"] = config.get("music_volume", proj.get("music_volume", 0.08))

        from services.render_service import render_video
        result = render_video(
            project=proj,
            output_path=output_path,
            progress_callback=lambda p, s: self.on_progress(job["id"], job["project_id"], 10 + int(p * 0.9), s)
        )

        self.on_progress(job["id"], job["project_id"], 100, "Complete")
        return {
            "video_path": output_path,
            "duration": result.get("duration", 0),
            "size_mb": result.get("size_mb", 0),
        }


# Agent registry
AGENTS = {
    "voice": VoiceAgent(),
    "slide": SlideAgent(),
    "music": MusicAgent(),
    "avatar": AvatarAgent(),
    "render": RenderAgent(),
}


def worker_loop(worker_id: str, job_types: list, poll_interval: float = 2.0):
    """
    Main worker loop. Polls the queue for jobs, processes them.
    Runs forever until killed.
    """
    print(f"Worker {worker_id} started")
    print(f"  Job types: {job_types}")
    print(f"  Poll interval: {poll_interval}s")
    print()

    while True:
        try:
            job = claim_next_job(worker_id, job_types)

            if job is None:
                time.sleep(poll_interval)
                continue

            job_type = job["type"]
            job_id = job["id"]
            project_id = job["project_id"]

            print(f"[{worker_id}] Processing {job_type} job {job_id}")

            agent = AGENTS.get(job_type)
            if not agent:
                fail_job(job_id, f"No agent for job type: {job_type}")
                continue

            try:
                result = agent.process(job)
                complete_job(job_id, result)
                print(f"[{worker_id}] Completed {job_type} job {job_id}")
                notify_progress(project_id, job_id, 100, "Done", "completed")

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"[{worker_id}] FAILED {job_type} job {job_id}: {error_msg}")
                traceback.print_exc()
                fail_job(job_id, error_msg)
                notify_progress(project_id, job_id, 0, error_msg, "failed")

        except KeyboardInterrupt:
            print(f"\n[{worker_id}] Shutting down...")
            break
        except Exception as e:
            print(f"[{worker_id}] Worker error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Creator Worker Agent")
    parser.add_argument("--id", default=f"worker-{uuid.uuid4().hex[:6]}", help="Worker ID")
    parser.add_argument("--types", default="voice,slide,music,avatar,render", help="Comma-separated job types")
    parser.add_argument("--poll", type=float, default=2.0, help="Poll interval in seconds")
    args = parser.parse_args()

    job_types = [t.strip() for t in args.types.split(",")]
    worker_loop(args.id, job_types, args.poll)
