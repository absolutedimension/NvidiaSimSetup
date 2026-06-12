"""EC2 tool — runs commands on the TrigunAI-Omniverse EC2 instance via SSH."""

import asyncio
import os
import shlex

EC2_HOST = os.getenv("EC2_HOST", "54.162.225.64")
EC2_USER = os.getenv("EC2_USER", "ubuntu")
EC2_KEY = os.getenv("EC2_KEY_PATH", os.path.expanduser("~/.ssh/trigunai_key.pem"))


async def ssh_ec2(command: str, timeout: int = 300) -> dict:
    """Run a command on EC2 via SSH. Returns stdout, stderr, returncode."""
    ssh_cmd = [
        "ssh", "-i", EC2_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", f"ConnectTimeout=10",
        f"{EC2_USER}@{EC2_HOST}",
        command,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode("utf-8", errors="replace")[-4000:],  # cap output
            "stderr": stderr.decode("utf-8", errors="replace")[-2000:],
            "returncode": proc.returncode,
        }
    except asyncio.TimeoutError:
        return {"stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}


async def scp_from_ec2(remote_path: str, local_path: str) -> dict:
    """SCP a file from EC2 to local."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    cmd = [
        "scp", "-i", EC2_KEY,
        "-o", "StrictHostKeyChecking=no",
        f"{EC2_USER}@{EC2_HOST}:{remote_path}",
        local_path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        return {
            "success": proc.returncode == 0,
            "local_path": local_path,
            "error": stderr.decode() if proc.returncode != 0 else None,
        }
    except Exception as e:
        return {"success": False, "local_path": local_path, "error": str(e)}


async def scp_to_ec2(local_path: str, remote_path: str) -> dict:
    """SCP a file from local to EC2."""
    cmd = [
        "scp", "-i", EC2_KEY,
        "-o", "StrictHostKeyChecking=no",
        local_path,
        f"{EC2_USER}@{EC2_HOST}:{remote_path}",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        return {
            "success": proc.returncode == 0,
            "remote_path": remote_path,
            "error": stderr.decode() if proc.returncode != 0 else None,
        }
    except Exception as e:
        return {"success": False, "remote_path": remote_path, "error": str(e)}


async def check_ec2_health() -> dict:
    """Check EC2 services health."""
    result = await ssh_ec2(
        "docker ps --format 'table {{.Names}}\\t{{.Status}}' 2>/dev/null; "
        "echo '---'; "
        "curl -s localhost:8001/health 2>/dev/null | head -5; "
        "echo '---'; "
        "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null",
        timeout=15,
    )
    return result
