#!/usr/bin/env bash
# Waits for the running enrich-solutions to finish, then runs self-consistency reverify,
# then prints a final JEE-Advanced-Physics quality report.
cd /home/ubuntu/question_bank_engine
export QBANK_LLM=on QBANK_LLM_BASE_URL=http://localhost:4000/v1 \
       QBANK_LLM_API_KEY=sk-trigunai-master-key-2026 QBANK_CHAT_MODEL=gpt-4o PYTHONUNBUFFERED=1

while pgrep -f "run.py enrich" >/dev/null; do sleep 20; done
echo "=== ENRICH DONE ==="

python3 run.py reverify --k 3
echo "=== REVERIFY DONE ==="

python3 - <<'PY'
import sqlite3
c=sqlite3.connect("data/qbank.sqlite")
W="generated=0 AND verified=1 AND duplicate_of IS NULL"
o=lambda q:c.execute(q).fetchone()[0]
tot=o(f"SELECT COUNT(*) FROM questions WHERE {W}")
sol=o(f"SELECT COUNT(*) FROM questions WHERE {W} AND solution!='' AND solution IS NOT NULL")
ver=o(f"SELECT COUNT(*) FROM questions WHERE {W} AND solution!='' AND validation_issues NOT LIKE '%needs_review%'")
rev=o(f"SELECT COUNT(*) FROM questions WHERE {W} AND validation_issues LIKE '%needs_review%'")
figskip=o(f"SELECT COUNT(*) FROM questions WHERE {W} AND needs_figure=1")
cnull=o(f"SELECT COUNT(*) FROM questions WHERE {W} AND (concept IS NULL OR concept='')")
print("=== FINAL JEE ADVANCED PHYSICS QUALITY ===")
print("total real questions:", tot)
print("with solution:", sol)
print("  verified solution (independent/self-consistent solve = official):", ver)
print("  needs_review (LLM disagreed after voting):", rev)
print("needs_figure (solution skipped, has figure image):", figskip)
print("concept still NULL:", cnull)
PY
echo "=== ALL DONE ==="
