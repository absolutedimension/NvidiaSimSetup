FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
# --timeout 240: the RAG exam generator is a synchronous LLM call (~40s/question on gpt-5.5), so a
# 5-question paper can run ~1-2 min. The old 60s killed the worker mid-request and returned an empty
# response. 240s matches the Container Apps ingress ceiling.
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "240", "--graceful-timeout", "30"]
