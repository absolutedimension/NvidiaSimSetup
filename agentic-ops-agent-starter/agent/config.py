"""Central config for your agent. Edit these as the course progresses."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Model ---------------------------------------------------------------
# Default to Claude. Swap to an OpenAI model in Module 2 if you prefer.
PROVIDER = os.getenv("PROVIDER", "anthropic")          # "anthropic" or "openai"
MODEL = os.getenv("MODEL", "claude-sonnet-4-6")        # good default for agents
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Agent loop limits (Module 6: guardrails & cost control) -------------
MAX_STEPS = int(os.getenv("MAX_STEPS", "10"))          # hard stop so it can't loop forever
MAX_USD = float(os.getenv("MAX_USD", "0.50"))          # rough spend cap per run

# --- Your use-case -------------------------------------------------------
# Fill this in at Session 0. One sentence describing the real job your agent does.
USE_CASE = os.getenv("USE_CASE", "TODO: describe the real workflow your agent automates")

SYSTEM_PROMPT = f"""You are an Ops Agent that automates a real workflow.
Your job: {USE_CASE}

Work step by step. Use the tools available to you. When the task is fully done,
stop and give a short summary of what you did. Never invent results — if a tool
fails or you lack information, say so.
"""
