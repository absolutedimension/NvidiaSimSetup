#!/usr/bin/env bash
# Deploys the Question Generator API as a systemd service on EC2 (port 8020, localhost).
# Idempotent: keeps the existing api.env (and its API key) if already present.
set -euo pipefail
cd /home/ubuntu/question_bank_engine

# deps
python3 -m uvicorn --version >/dev/null 2>&1 || pip3 install --break-system-packages -q "uvicorn[standard]"

# config + secret (generated once)
if [ ! -f api.env ]; then
  KEY=$(openssl rand -hex 24)
  cat > api.env <<EOF
QBANK_LLM=on
QBANK_LLM_BASE_URL=http://localhost:4000/v1
QBANK_LLM_API_KEY=sk-trigunai-master-key-2026
QBANK_CHAT_MODEL=gpt-4o
QBANK_API_KEY=${KEY}
QBANK_CORS=*
EOF
  chmod 600 api.env
  echo "generated new api.env (API key created)"
fi

sudo tee /etc/systemd/system/qbank-api.service >/dev/null <<'UNIT'
[Unit]
Description=TrigunAI Question Generator API
After=network.target docker.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/question_bank_engine
EnvironmentFile=/home/ubuntu/question_bank_engine/api.env
ExecStart=/usr/bin/python3 -m uvicorn api:app --host 127.0.0.1 --port 8020
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable qbank-api >/dev/null 2>&1 || true
sudo systemctl restart qbank-api
sleep 4
echo "service: $(systemctl is-active qbank-api)"
