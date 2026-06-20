"""Catalog of free-tier coding setups a student can choose from. Each has a real free
tier and (where it exists) a student offer. Figures verified June 2026 — revisit periodically."""

CODING_OPTIONS = [
    {
        "id": "codespaces",
        "name": "GitHub Codespaces + Copilot",
        "type": "Runs in your browser · nothing to install",
        "recommended": True,
        "free": "Codespaces: 120 core-hours/month free (~60 hrs). Copilot Free: 2,000 completions + ~50 agent chats/month.",
        "student": "Copilot Pro is FREE for students & teachers via GitHub Education (unlimited completions, big agent limits).",
        "url": "https://github.com/education",
        "cta": "Get free GitHub Education",
        "note": "Runs fully in the browser — needs a free GitHub account (2FA/phone may be required to sign up).",
    },
    {
        "id": "cursor",
        "name": "Cursor",
        "type": "Desktop app (Windows / Mac / Linux)",
        "recommended": False,
        "free": "Hobby tier free forever: 2,000 completions + 50 premium requests/month, no card needed.",
        "student": "Full Pro FREE for students with a school email.",
        "url": "https://cursor.com/students",
        "cta": "Download / student access",
        "note": "Most popular standalone agentic IDE. Download it, then open the starter ZIP — no GitHub needed.",
    },
    {
        "id": "antigravity",
        "name": "Google Antigravity",
        "type": "Desktop app",
        "recommended": False,
        "free": "Free tier: ~20 agent requests/day on Gemini Flash (resets daily — good for daily reps).",
        "student": "No dedicated student plan, but the daily free allowance suits the 40-min daily reps.",
        "url": "https://antigravity.google",
        "cta": "Download Antigravity",
        "note": "Agent-first IDE from Google; multi-model.",
    },
    {
        "id": "windsurf",
        "name": "Windsurf",
        "type": "Desktop app",
        "recommended": False,
        "free": "Free plan: 25 credits/month (a few days of active building).",
        "student": "Student discounts via campus programs — check your school benefits.",
        "url": "https://windsurf.com",
        "cta": "Download Windsurf",
        "note": "Smallest free tier of the four — fine for light use.",
    },
]
VALID_IDS = {o["id"] for o in CODING_OPTIONS}
