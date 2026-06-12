"""
Agent registry — maps agent names to their tool sets.

Each agent gets a specific set of tools based on its role. The system prompts
come from the SKILL.md files in cowork-plugins/.
"""
from __future__ import annotations

from .runner import ToolDef
from tools.ec2 import ssh_ec2, scp_from_ec2, check_ec2_health
from tools.mocap import (
    parse_mocap_session,
    bake_usda,
    render_mp4,
    check_render_status,
    convert_to_glb,
)


def get_training_agent_tools() -> list[ToolDef]:
    """Tools for the Training Agent (simulation + rendering side)."""
    return [
        ToolDef(
            name="ssh_ec2",
            description=(
                "Run a bash command on the EC2 GPU instance via SSH. "
                "Use for: checking services, inspecting files, running scripts. "
                "The EC2 runs Isaac Sim, OVRTX renderer, Blender, Docker services."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Bash command to execute on EC2",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 300)",
                        "default": 300,
                    },
                },
                "required": ["command"],
            },
            handler=ssh_ec2,
        ),
        ToolDef(
            name="parse_mocap",
            description=(
                "Parse a mocap session (pose.bin + meta.json) on EC2. "
                "Returns frame count, FPS, duration, schema version, body names."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "session_path": {
                        "type": "string",
                        "description": "Path to the session directory on EC2",
                    },
                },
                "required": ["session_path"],
            },
            handler=parse_mocap_session,
        ),
        ToolDef(
            name="bake_usda",
            description=(
                "Bake a mocap session into an animated USDA scene with stick-figure "
                "dancer, orbital camera, floor, and lighting. USDA-only (no render)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "session_path": {"type": "string", "description": "Mocap session dir on EC2"},
                    "output_path": {"type": "string", "description": "Output .usda path on EC2"},
                    "duration": {"type": "number", "description": "Clip duration in seconds", "default": 25.0},
                    "fps": {"type": "integer", "description": "Target frame rate", "default": 30},
                    "camera_style": {"type": "string", "enum": ["orbital"], "default": "orbital"},
                },
                "required": ["session_path", "output_path"],
            },
            handler=bake_usda,
        ),
        ToolDef(
            name="render_mp4",
            description=(
                "Full pipeline: parse mocap → bake USDA → OVRTX render → ffmpeg → MP4. "
                "Runs in background on EC2. Use check_render_status to monitor."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "session_path": {"type": "string", "description": "Mocap session dir on EC2"},
                    "output_path": {"type": "string", "description": "Output .mp4 path on EC2"},
                    "duration": {"type": "number", "default": 25.0},
                    "fps": {"type": "integer", "default": 30},
                    "width": {"type": "integer", "default": 800},
                    "height": {"type": "integer", "default": 450},
                },
                "required": ["session_path", "output_path"],
            },
            handler=render_mp4,
        ),
        ToolDef(
            name="check_render_status",
            description="Check if a background render process is still running on EC2.",
            input_schema={
                "type": "object",
                "properties": {
                    "pid": {"type": "string", "description": "Process ID from render_mp4"},
                    "output_path": {"type": "string", "description": "Expected output file path"},
                },
                "required": ["pid", "output_path"],
            },
            handler=check_render_status,
        ),
        ToolDef(
            name="convert_to_glb",
            description="Convert USDA to GLB via Blender 4.5 on EC2. Supports animated export with NLA strips.",
            input_schema={
                "type": "object",
                "properties": {
                    "usda_path": {"type": "string", "description": "Input USDA/USD path on EC2"},
                    "glb_path": {"type": "string", "description": "Output GLB path on EC2"},
                    "animated": {"type": "boolean", "default": True},
                    "max_texture": {"type": "integer", "default": 1024},
                },
                "required": ["usda_path", "glb_path"],
            },
            handler=convert_to_glb,
        ),
        ToolDef(
            name="check_ec2_health",
            description="Check EC2 Docker services, OVRTX status, and GPU utilization.",
            input_schema={"type": "object", "properties": {}},
            handler=check_ec2_health,
        ),
    ]


def get_orchestrator_tools() -> list[ToolDef]:
    """Tools for the Orchestrator Agent (phase tracking + handoffs)."""
    return [
        ToolDef(
            name="check_ec2_health",
            description="Check EC2 services status.",
            input_schema={"type": "object", "properties": {}},
            handler=check_ec2_health,
        ),
        # Orchestrator mostly generates text (handoff docs) — fewer tools needed
    ]


def get_vr_agent_tools() -> list[ToolDef]:
    """Tools for the VR Agent (Unity integration guidance)."""
    return [
        # VR agent mostly generates integration guides and feedback templates
        # In Phase 2, this could have Unity-specific tools
    ]


# Registry
AGENT_REGISTRY = {
    "trigunai-training": get_training_agent_tools,
    "trigunai-orchestrator": get_orchestrator_tools,
    "trigunai-vr": get_vr_agent_tools,
}


def get_agent_tools(agent_name: str) -> list[ToolDef]:
    """Get tools for a named agent."""
    factory = AGENT_REGISTRY.get(agent_name)
    if not factory:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}")
    return factory()
