#!/usr/bin/env python3
"""
Maya over Plivo using Azure gpt-realtime (speech-to-speech) — true sub-second latency.
Plivo call -> answer_url -> <Stream wss://.../realtime-stream> -> this WS -> Azure gpt-realtime (South India).
No separate STT/LLM/TTS — the realtime model does audio-in -> audio-out directly.
Env (~/voicebot_wa/wa_voice.env + plivo.env): AZURE_OPENAI_API_KEY (maya-india-aoai), PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN
Run: uvicorn maya_realtime:app --host 0.0.0.0 --port 7863
"""
import os, json, asyncio
from fastapi import FastAPI, WebSocket, Request, Response
from pipecat.serializers.plivo import PlivoFrameSerializer
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.azure.realtime.llm import AzureRealtimeLLMService
from pipecat.services.openai.realtime.events import (
    SessionProperties, AudioConfiguration, AudioInput, AudioOutput, TurnDetection)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

AOAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
RT_URL = ("wss://maya-india-aoai.openai.azure.com/openai/realtime"
          "?api-version=2025-04-01-preview&deployment=gpt-realtime")
PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID"); PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN")
STREAM_WSS = os.environ.get("MAYA_RT_WSS", "wss://gurukul.trigunai.com/realtime-stream")

INSTRUCTIONS = (
    "You are Maya from TrigunAI making a SHORT screening phone call in warm, natural Hindi/Hinglish. "
    "The MOMENT the call connects, greet and ask in ONE line: "
    "'नमस्ते! मैं TrigunAI से माया बोल रही हूँ। क्या आप एक teacher हैं, coaching चलाते हैं, या teaching से कमाना चाहते हैं?' "
    "This is NOT a sales pitch and NOT a long conversation — capture yes/no interest, then end. "
    "HARD RULES: speak ONE short line per turn, ask only yes/no or one-word questions, never chat long, never repeat, "
    "NEVER mention any price, fees, or rupees. Understand the caller's meaning before replying. "
    "FLOW: (1) If they are NOT a teacher and do NOT want to earn from teaching -> thank them in one line and end. "
    "(2) If they teach, run coaching, or want to earn from teaching -> say in ONE line they get a 14-day free trial "
    "to explore integrating cutting-edge AI technology into their teaching and scale their work. "
    "(3) Then ask ONE line: 'क्या आपको इसमें interest है?' "
    "(4) Treat ANY engagement (haan/yes/tell me more/aur batao/kaise/details/a question) as INTERESTED; only a clear "
    "'नहीं/no/busy' is NOT interested; if unclear, ask once more, never assume no. "
    "(5) If INTERESTED -> say 'बढ़िया! हमारी team आपसे पूरी जानकारी के साथ जल्द connect करेगी।' then say goodbye. "
    "(6) If NOT interested -> say 'कोई बात नहीं, आपके समय के लिए धन्यवाद!' then say goodbye. "
    "Keep the whole call to a few short turns. Be honest — you are an AI assistant from TrigunAI."
)

app = FastAPI()

@app.get("/realtime-health")
async def health():
    return {"ok": True, "agent": "maya-realtime"}

@app.api_route("/realtime-answer", methods=["GET", "POST"])
async def answer(_r: Request):
    xml = ('<?xml version="1.0" encoding="UTF-8"?><Response>'
           f'<Stream bidirectional="true" keepCallAlive="true" '
           f'contentType="audio/x-mulaw;rate=8000" audioTrack="inbound">{STREAM_WSS}</Stream></Response>')
    return Response(content=xml, media_type="application/xml")

@app.websocket("/realtime-stream")
async def realtime_stream(ws: WebSocket):
    await ws.accept()
    stream_id = call_id = None
    for _ in range(5):
        msg = json.loads(await ws.receive_text())
        if msg.get("event") == "start":
            st = msg.get("start", {}); stream_id = st.get("streamId"); call_id = st.get("callId"); break
    if not stream_id:
        await ws.close(); return

    serializer = PlivoFrameSerializer(stream_id=stream_id, call_id=call_id,
                                      auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)
    transport = FastAPIWebsocketTransport(websocket=ws, params=FastAPIWebsocketParams(
        audio_in_enabled=True, audio_out_enabled=True, add_wav_header=False, serializer=serializer))

    session_props = SessionProperties(
        instructions=INSTRUCTIONS,
        output_modalities=["audio"],
        audio=AudioConfiguration(
            input=AudioInput(turn_detection=TurnDetection(
                type="server_vad", threshold=0.5, prefix_padding_ms=300, silence_duration_ms=500)),
            output=AudioOutput(voice="coral"),
        ),
    )
    llm = AzureRealtimeLLMService(api_key=AOAI_KEY, base_url=RT_URL, session_properties=session_props)
    ctx = LLMContext([{"role": "system", "content": INSTRUCTIONS},
                      {"role": "user", "content": "(call connected — greet now)"}])
    agg = LLMContextAggregatorPair(ctx)
    pipeline = Pipeline([transport.input(), agg.user(), llm, transport.output(), agg.assistant()])
    task = PipelineTask(pipeline, params=PipelineParams(
        audio_in_sample_rate=8000, audio_out_sample_rate=8000, allow_interruptions=False))

    @transport.event_handler("on_client_connected")
    async def _on_conn(_t, _c):
        await task.queue_frames([agg.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def _on_disc(_t, _c):
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
