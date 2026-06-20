# Deploying on a schedule (Module 8)

Your agent becomes useful when it runs *without you*. Three options, easiest first:

## 1. Cron on any Linux box (simplest)
```bash
# run every weekday at 9am
0 9 * * 1-5  cd /path/to/agent && /usr/bin/python3 run.py "do my daily ops job" >> agent.log 2>&1
```

## 2. GitHub Actions (free, no server)
`.github/workflows/agent.yml` — scheduled workflow that runs `python run.py`.
Store your API key as a repo secret. Good for once-a-day jobs.

## 3. A tiny always-on server (Module 8 live)
Render / Railway / a small EC2 — for agents that react to events (new email) rather than a fixed time.

**Logging matters (Module 8):** every run should write what it did and why to `agent.log`,
so when it misbehaves you can see the decision trail. We cover this live.
