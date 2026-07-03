#!/usr/bin/env python3
"""
WhatsApp webhook ROUTER (safety layer for Acharya).
Meta -> Caddy(/webhook) -> THIS router -> dispatch:
   field == 'calls'  -> Maya voice agent (127.0.0.1:7860/whatsapp)
   everything else   -> Acharya message bridge (127.0.0.1:8788/webhook)  [UNCHANGED]
Forwards the RAW body + X-Hub-Signature-256 so both services verify signatures correctly.
Run: uvicorn whatsapp_router:app --host 127.0.0.1 --port 8799
"""
import os, json, httpx
from fastapi import FastAPI, Request, Response

VERIFY   = os.environ.get("WHATSAPP_WEBHOOK_VERIFICATION_TOKEN", "")
ACHARYA  = os.environ.get("ACHARYA_URL", "http://127.0.0.1:8788/webhook")
MAYA     = os.environ.get("MAYA_URL",    "http://127.0.0.1:7860/whatsapp")

app = FastAPI()

@app.get("/webhook")
async def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == VERIFY:
        return Response(content=q.get("hub.challenge", ""), media_type="text/plain")
    return Response(status_code=403)

@app.post("/webhook")
async def route(request: Request):
    raw = await request.body()
    fwd_headers = {k: v for k, v in request.headers.items()
                   if k.lower() in ("content-type", "x-hub-signature-256", "x-hub-signature")}
    target = ACHARYA
    try:
        data = json.loads(raw)
        fields = {c.get("field") for e in data.get("entry", []) for c in e.get("changes", [])}
        if "calls" in fields:
            target = MAYA
    except Exception:
        pass  # unparseable -> default to Acharya (safe)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(target, content=raw, headers=fwd_headers)
        return Response(content=r.content, status_code=r.status_code,
                        media_type=r.headers.get("content-type", "application/json"))
    except Exception:
        # never fail the webhook to Meta; Acharya-side already got it if that was the target
        return Response(status_code=200)

@app.get("/router-health")
async def health():
    return {"ok": True, "acharya": ACHARYA, "maya": MAYA}
