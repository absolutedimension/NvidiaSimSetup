"""Central config for the Question Bank Engine.

Everything is env-overridable so the SAME code runs locally (offline, rule-based)
or in production (pointed at the TrigunAI LiteLLM/Azure proxy).

Production LLM (flip on by exporting these):
    QBANK_LLM_BASE_URL=http://localhost:4000/v1        # SSH-tunnel to EC2 :4000, or Gurukul VM
    QBANK_LLM_API_KEY=sk-trigunai-master-key-2026
    QBANK_LLM=on
"""
import os

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PKG_DIR)

# --- LLM (OpenAI-compatible; defaults match the TrigunAI LiteLLM proxy) ---
LLM_BASE_URL = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1")
LLM_API_KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
CHAT_MODEL = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o-mini")
VISION_MODEL = os.environ.get("QBANK_VISION_MODEL", "gpt-4o")
# auto = try LLM, fall back to rules if unreachable | on = require LLM | off = never call
LLM_ENABLED = os.environ.get("QBANK_LLM", "auto").lower()

# --- storage ---
# SQLite for local/demo; Postgres+pgvector is the production target (see schema_postgres.sql)
DB_PATH = os.environ.get("QBANK_DB", os.path.join(ROOT, "data", "qbank.sqlite"))
DROP_DIR = os.environ.get("QBANK_DROP", os.path.join(ROOT, "drop"))

# --- figures (diagram questions) ---
FIG_DIR = os.environ.get("QBANK_FIG_DIR", os.path.join(ROOT, "figures"))
# public base the frontend uses to fetch a figure: {PUBLIC_BASE}/figures/<id>.png
PUBLIC_BASE = os.environ.get("QBANK_PUBLIC_BASE", "https://rtx.trigunai.com/examgen")

# --- dedup ---
NEAR_DUP_THRESHOLD = float(os.environ.get("QBANK_NEARDUP", "0.90"))
