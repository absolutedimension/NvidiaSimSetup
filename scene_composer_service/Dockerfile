FROM python:3.11-slim

# usd-core wheel needs libgl/libglib at runtime for some plugins; keep slim.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libgl1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Scripts are mounted from the host repo at /opt/scripts (see docker-compose.yml).
# The app expects them at COMPOSER_SCRIPTS_DIR (default /opt/scripts).

COPY app.py .

EXPOSE 8005

ENV PYTHONUNBUFFERED=1 \
    COMPOSER_SCRIPTS_DIR=/opt/scripts \
    COMPOSER_OUT_BASE=/data/cities \
    COMPOSER_TEXTURE_AGENT_BASE=http://host.docker.internal:8004

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8005"]
