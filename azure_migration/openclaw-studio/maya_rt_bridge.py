#!/usr/bin/env python3
"""
Maya realtime bridge: Plivo <-> Azure gpt-realtime (speech-to-speech), direct, no Pipecat.
g711_ulaw end-to-end (Plivo's native format) = zero resampling = lowest latency.
Half-duplex: caller audio is ignored while Maya is speaking (matches "don't interrupt the bot").
Env (~/voicebot_wa/wa_voice.env + plivo.env): AZURE_OPENAI_API_KEY (maya-india-aoai), PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN
Run: uvicorn maya_rt_bridge:app --host 0.0.0.0 --port 7863
"""
import os, json, asyncio, time, urllib.request
from fastapi import FastAPI, WebSocket, Request, Response
import websockets

AOAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
RT_URL = ("wss://maya-india-aoai.openai.azure.com/openai/realtime"
          "?api-version=2025-04-01-preview&deployment=gpt-realtime")
PLIVO_ID = os.environ.get("PLIVO_AUTH_ID"); PLIVO_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN")
STREAM_WSS = os.environ.get("MAYA_RT_WSS", "wss://gurukul.trigunai.com/realtime-stream")
VOICE = os.environ.get("MAYA_VOICE", "coral")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN"); TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

INSTRUCTIONS = (
    "You are Maya, a warm, very polite and friendly caller from TrigunAI, on a short phone call. "
    "Speak natural, gentle, respectful Hindi/Hinglish — like a real person, not a script. Use polite touches "
    "('जी', 'जरूर', 'बहुत अच्छा', 'धन्यवाद'). Keep each turn short (1–2 sentences), never lecture. "
    "OPEN with a genuinely POLITE, soft greeting, e.g.: 'नमस्ते जी! आपका दिन शुभ हो। मैं TrigunAI से माया बोल रही हूँ — "
    "क्या मैं आपका एक मिनट ले सकती हूँ?' Then warmly find out if they are in the teaching/coaching/tuition field, or "
    "want to earn or grow by teaching. "
    "CRITICAL: Greet and introduce yourself ONLY ONCE — in your very first line. After that, NEVER say 'नमस्ते' or "
    "re-introduce yourself or repeat the opening question again. Always continue naturally from what the caller just said. "
    "If you didn't catch their reply, ask a SHORT clarifying question — but never restart or re-greet. "
    "YOUR ONLY JOB: figure out (a) whether this person is in the teaching field (or wants to earn/scale by teaching), and "
    "(b) whether they'd be interested in plugging modern AI into their teaching so they can teach MORE children with LESS "
    "effort and scale/earn more. Do NOT probe which subject or course they teach — that's not needed. NEVER mention any "
    "price, fees, or rupees. "
    "WHAT TO CONVEY (briefly, warmly, only if they teach or want to): TrigunAI has a COMPLETE AI suite that helps teachers "
    "connect with and teach their students more efficiently, and there is a 14-day FREE trial. In today's AI world, plugging "
    "AI into teaching where needed lets a teacher reach more students with far less effort and grow their work. "
    "IF THEY ASK FOR DETAILS: explain simply — Acharya, an AI tutor on WhatsApp that answers students' doubts 24x7 under the "
    "teacher's own brand; a dashboard to manage everything; a WhatsApp channel to engage students; and more. Keep it short, "
    "then steer back to their interest. "
    "HOW TO TALK: acknowledge what they say first. Understand their real meaning — any curiosity or question means interested. "
    "FLOW: polite greeting -> learn if they teach / want to earn by teaching -> if NOT in teaching and no interest, thank them "
    "warmly and close -> if they teach / are interested, share the AI-suite idea + free trial briefly and ask if they'd like to try "
    "-> if interested (any curiosity counts), tell them our team will contact them shortly to set up the free-trial registration "
    "and next steps, thank them, and close. "
    "CLOSING LINES: interested -> 'बहुत बढ़िया! हमारी team आपसे free trial registration और आगे की जानकारी के लिए जल्द संपर्क करेगी। धन्यवाद जी!' ; "
    "not interested -> 'कोई बात नहीं जी, आपके समय के लिए बहुत धन्यवाद!'. "
    "Be honest — if asked, you're an AI assistant from TrigunAI; never invent numbers or testimonials."
)
CLOSERS = ("समय के लिए", "संपर्क कर", "registration", "team आपसे")
TRANSCRIPT_DIR = os.path.expanduser("~/voicebot_wa/transcripts")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

app = FastAPI()

@app.get("/realtime-health")
async def health():
    return {"ok": True, "agent": "maya-rt-bridge"}

@app.api_route("/realtime-answer", methods=["GET", "POST"])
async def answer(request: Request):
    from urllib.parse import urlencode
    ctx = {k: request.query_params.get(k, "") for k in ("name", "city", "segment")}
    su = STREAM_WSS
    qs = urlencode({k: v for k, v in ctx.items() if v})
    if qs:
        su = f"{STREAM_WSS}?{qs}"
    su = su.replace("&", "&amp;")   # XML-escape ampersands for Plivo
    xml = ('<?xml version="1.0" encoding="UTF-8"?><Response>'
           f'<Stream bidirectional="true" keepCallAlive="true" '
           f'contentType="audio/x-mulaw;rate=8000" audioTrack="inbound">{su}</Stream></Response>')
    return Response(content=xml, media_type="application/xml")

import base64

def _plivo_req(path, method, body=None):
    try:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"https://api.plivo.com/v1/Account/{PLIVO_ID}/{path}", data=data, method=method)
        tok = base64.b64encode(f"{PLIVO_ID}:{PLIVO_TOKEN}".encode()).decode()
        req.add_header("Authorization", f"Basic {tok}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        return urllib.request.urlopen(req, timeout=10).read()
    except Exception:
        return None

def _hangup(call_id):
    _plivo_req(f"Call/{call_id}/", "DELETE")

def _telegram(text):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        data = json.dumps({"chat_id": TG_CHAT, "text": text[:4000]}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                     data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

def _start_recording(call_id):
    # Plivo records the call; the mp3 shows up under Recordings + Logs in the console.
    _plivo_req(f"Call/{call_id}/Record/", "POST", {"file_format": "mp3"})

@app.websocket("/realtime-stream")
async def stream(plivo_ws: WebSocket):
    await plivo_ws.accept()
    stream_id = call_id = None
    while True:
        m = json.loads(await plivo_ws.receive_text())
        if m.get("event") == "start":
            stream_id = m["start"]["streamId"]; call_id = m["start"].get("callId"); break

    # per-call caller context (passed as query params by the runner) — Maya sounds informed
    q = plivo_ws.query_params
    name = q.get("name", ""); city = q.get("city", ""); segment = q.get("segment", "")
    instr = INSTRUCTIONS
    if name:
        who = f"'{name}'"
        if segment: who += f" (a {segment} coaching/tuition)"
        if city: who += f" in {city}"
        instr += (f" CALL CONTEXT: You are calling {who}. Use this naturally — you may warmly confirm you've "
                  "reached the right place; do NOT robotically read out the full listing name.")

    az = await websockets.connect(RT_URL, additional_headers={"api-key": AOAI_KEY},
                                  open_timeout=15, max_size=None)
    await az.recv()  # session.created
    await az.send(json.dumps({"type": "session.update", "session": {
        "modalities": ["audio", "text"],
        "instructions": instr,
        "voice": VOICE,
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw",
        "input_audio_transcription": {"model": "gpt-4o-transcribe"},
        "turn_detection": {"type": "server_vad", "threshold": 0.5,
                           "prefix_padding_ms": 300, "silence_duration_ms": 500},
    }}))
    await az.send(json.dumps({"type": "response.create"}))  # Maya greets first

    # start Plivo audio recording + open a transcript file for this call
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _start_recording, call_id)
    tpath = os.path.join(TRANSCRIPT_DIR, f"{call_id or stream_id}.txt")
    tfile = open(tpath, "a", encoding="utf-8")
    def logline(who, text):
        line = f"{who}: {text}".strip()
        tfile.write(line + "\n"); tfile.flush()
        print("TRANSCRIPT " + line, flush=True)

    ended = asyncio.Event()
    state = {"maya_speaking": True, "buf": "", "resp_bytes": 0, "first_audio": None}

    async def plivo_to_az():
        try:
            while True:
                m = json.loads(await plivo_ws.receive_text())
                ev = m.get("event")
                if ev == "media" and not state["maya_speaking"]:
                    await az.send(json.dumps({"type": "input_audio_buffer.append",
                                              "audio": m["media"]["payload"]}))
                elif ev == "stop":
                    break
        except Exception:
            pass
        finally:
            ended.set()

    async def az_to_plivo():
        try:
            async for raw in az:
                m = json.loads(raw); t = m.get("type", "")
                if t.endswith("audio.delta") and m.get("delta"):
                    if state["first_audio"] is None:
                        state["first_audio"] = time.monotonic()
                    state["resp_bytes"] += len(base64.b64decode(m["delta"]))  # g711 8kHz: 8000 bytes/sec
                    await plivo_ws.send_text(json.dumps({"event": "playAudio", "media": {
                        "contentType": "audio/x-mulaw", "sampleRate": 8000, "payload": m["delta"]}}))
                elif t == "response.created":
                    state["maya_speaking"] = True; state["buf"] = ""
                    state["resp_bytes"] = 0; state["first_audio"] = None
                elif t.endswith("audio_transcript.delta"):
                    state["buf"] += m.get("delta", "")
                elif t == "conversation.item.input_audio_transcription.completed":
                    logline("USER", m.get("transcript", ""))
                elif t == "response.audio_transcript.done":
                    logline("MAYA", m.get("transcript", ""))
                elif t == "response.done":
                    state["maya_speaking"] = False
                    if any(c in state["buf"] for c in CLOSERS):
                        # wait for the buffered closing audio to finish playing on the caller side
                        dur = state["resp_bytes"] / 8000.0
                        elapsed = (time.monotonic() - state["first_audio"]) if state["first_audio"] else 0.0
                        await asyncio.sleep(max(1.0, dur - elapsed + 1.5))
                        ended.set(); break
        except Exception:
            pass
        finally:
            ended.set()

    t1 = asyncio.create_task(plivo_to_az()); t2 = asyncio.create_task(az_to_plivo())
    await ended.wait()
    for t in (t1, t2):
        t.cancel()
    try: await az.close()
    except Exception: pass
    await asyncio.get_event_loop().run_in_executor(None, _hangup, call_id)
    try: tfile.close()
    except Exception: pass
    # push the transcript to Telegram
    try:
        body = open(tpath, encoding="utf-8").read()
        msg = f"📞 Maya call transcript\ncall: {call_id}\n\n{body}\n(recording in Plivo → Logs/Recordings)"
        await asyncio.get_event_loop().run_in_executor(None, _telegram, msg)
    except Exception:
        pass
    try: await plivo_ws.close()
    except Exception: pass
