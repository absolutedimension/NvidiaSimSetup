# Acharya University — Phase 1

Self-taught learning OS. Type any goal → the **Advisor** generates your personal
curriculum → the **Tutor** teaches it, unit by unit, with recall-based mastery.
See `ACHARYA_UNIVERSITY.md` for the full phased plan and architecture.

Isolated from the live Acharya/Gurukul system. First user = Deepak, on web.

## Run

```bash
cd acharya_university
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# LLM — Azure OpenAI (same creds pattern as lms/app):
export AOAI_ENDPOINT="https://azure-trigunai-model.openai.azure.com"
export AOAI_KEY="<your-azure-key>"
export AOAI_DEPLOYMENT="gpt-4o-mini"     # optional
export AOAI_API_VERSION="2024-10-21"     # optional
#   --- OR any OpenAI-compatible endpoint (e.g. the litellm proxy) ---
# export OPENAI_BASE_URL="http://<ec2>:4000/v1"
# export OPENAI_API_KEY="sk-trigunai-master-key-2026"
# export OPENAI_MODEL="gpt-4o"

uvicorn server:app --reload --port 8010
# open http://localhost:8010
```

Data is stored as JSON under `./data/` (gitignored).

## What's in Phase 1
- **Advisor** (`agents/advisor.py`) — 5-question interview → generates the full curriculum.
- **Tutor** (`agents/tutor.py`) — Socratic per-unit teacher + recall grading (code owns `solid`).
- **Registrar** — Phase 1 routing is UI-driven; the real router lands in Phase 2.
- **Learner Model** (`store.py`) — JSON store for learners / curricula / tutor sessions.

## Next (see ACHARYA_UNIVERSITY.md)
Phase 2 Registrar + mastery/SRS engine · Phase 3 Librarian + Source Shelf ·
Phase 4 Editor + Roommate · Phase 5 multi-user + deploy · Phase 6 flywheel.
