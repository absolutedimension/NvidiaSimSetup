# Deploy qbank-data onto the OpenClaw box (hearmenow-agentic-system, 20.120.226.5)

1. Copy the skill:   scp -r skills/qbank-data  <box>:~/.openclaw/skills/qbank-data
2. Connection env:   scp skills/qbank-data/qbank.env.example <box>:~/.openclaw/qbank.env   (fill SP_PW, chmod 600)
3. Give OpenClaw the keys to reach the boxes (if not already there):
     scp ~/.ssh/gurukul_key ~/.ssh/qbank_worker_key <box>:~/.ssh/   (chmod 600 both)
4. IDENTITY.md — add to the Skills line + a routing rule:
     "- `qbank-data` (the exam question-bank backend — ingest/convert/embed/go-live + wire exams to the LMS)."
     HARD RULE: "A question-bank / exam-data / 'ingest'/'push live'/'wire exam to LMS' request → invoke `qbank-data`.
      Code changes to that pipeline → `trigun-coding` pointed at ~/question_bank_engine ON the Gurukul box."
5. Reload OpenClaw skills (restart the gateway service, or however studio picks up new skills).
6. Test from Telegram: "search huggingface for class 10 maths data" / "bank stats" / "start the worker".
