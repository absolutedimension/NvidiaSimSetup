#!/bin/bash
set -e

mkdir -p /app/data/voice /app/data/slides /app/data/music /app/data/avatar /app/data/render /app/data/uploads

export VIDEO_CREATOR_DB=/app/data/jobs.db
export VIDEO_CREATOR_OUTPUT=/app/data
export RUN_WORKER=${RUN_WORKER:-"0"}

nginx

cd /app/backend
exec uvicorn main:app --host 0.0.0.0 --port 8010 --workers 1
