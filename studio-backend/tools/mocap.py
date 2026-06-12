"""Mocap tools — parse pose.bin, bake USDA, render MP4."""

import asyncio
import json
import os
from pathlib import Path

from .ec2 import ssh_ec2, scp_from_ec2, scp_to_ec2


async def parse_mocap_session(session_path: str) -> dict:
    """Parse a mocap session on EC2. Returns frame count, duration, joint info."""
    # Upload parse script if needed, then run it
    result = await ssh_ec2(
        f"cd /home/ubuntu && python3 -c \""
        f"import sys; sys.path.insert(0, '.'); "
        f"from parse_pose_bin import load_session; "
        f"s = load_session('{session_path}'); "
        f"import json; print(json.dumps({{"
        f"'num_frames': s.num_frames, "
        f"'fps': s.fps, "
        f"'duration_s': round(s.duration_s, 1), "
        f"'schema': s.schema, "
        f"'num_bodies': len(s.body_names), "
        f"'body_names': s.body_names[:5], "
        f"'has_aux': s.aux is not None"
        f"}}))\"",
        timeout=30,
    )
    if result["returncode"] == 0:
        try:
            return {"success": True, "data": json.loads(result["stdout"].strip())}
        except json.JSONDecodeError:
            return {"success": True, "raw": result["stdout"][:1000]}
    return {"success": False, "error": result["stderr"][:500]}


async def bake_usda(
    session_path: str,
    output_path: str,
    duration: float = 25.0,
    fps: int = 30,
    camera_style: str = "orbital",
) -> dict:
    """Bake a mocap session to animated USDA on EC2."""
    cmd = (
        f"cd /home/ubuntu && python3 render_dancer_mp4.py "
        f"--session {session_path} "
        f"--out {output_path} "
        f"--duration {duration} "
        f"--target-fps {fps} "
        f"--usda-only"
    )
    result = await ssh_ec2(cmd, timeout=60)
    if result["returncode"] == 0:
        # Get file size
        size_result = await ssh_ec2(f"ls -lh {output_path} 2>/dev/null")
        return {"success": True, "usda_path": output_path, "log": result["stdout"][-500:]}
    return {"success": False, "error": result["stderr"][:500], "log": result["stdout"][-500:]}


async def render_mp4(
    session_path: str,
    output_path: str,
    duration: float = 25.0,
    fps: int = 30,
    width: int = 800,
    height: int = 450,
) -> dict:
    """Full pipeline: parse → bake → OVRTX render → ffmpeg → MP4 on EC2."""
    cmd = (
        f"cd /home/ubuntu && nohup python3 render_dancer_mp4.py "
        f"--session {session_path} "
        f"--out {output_path} "
        f"--duration {duration} "
        f"--target-fps {fps} "
        f"--width {width} --height {height} "
        f"> /tmp/render_log.txt 2>&1 &"
        f" echo $!"
    )
    result = await ssh_ec2(cmd, timeout=30)
    if result["returncode"] == 0:
        pid = result["stdout"].strip().split("\n")[-1]
        return {
            "success": True,
            "pid": pid,
            "output_path": output_path,
            "message": f"Render started (PID {pid}). Use check_render_status to monitor.",
        }
    return {"success": False, "error": result["stderr"][:500]}


async def check_render_status(pid: str, output_path: str) -> dict:
    """Check if a background render is still running."""
    result = await ssh_ec2(
        f"ps -p {pid} > /dev/null 2>&1 && echo 'running' || echo 'done'; "
        f"ls -lh {output_path} 2>/dev/null; "
        f"tail -5 /tmp/render_log.txt 2>/dev/null",
        timeout=10,
    )
    stdout = result["stdout"]
    is_running = "running" in stdout.split("\n")[0]
    return {
        "running": is_running,
        "output_exists": output_path in stdout,
        "log_tail": stdout,
    }


async def convert_to_glb(
    usda_path: str,
    glb_path: str,
    animated: bool = True,
    max_texture: int = 1024,
) -> dict:
    """Convert USD/USDA to GLB via Blender on EC2."""
    flags = "--animated" if animated else ""
    cmd = (
        f"blender45 --background --python /home/ubuntu/usd_to_glb.py -- "
        f"--input {usda_path} --output {glb_path} "
        f"{flags} --max-texture {max_texture}"
    )
    result = await ssh_ec2(cmd, timeout=120)
    if result["returncode"] == 0:
        return {"success": True, "glb_path": glb_path, "log": result["stdout"][-500:]}
    return {"success": False, "error": result["stderr"][:500]}
