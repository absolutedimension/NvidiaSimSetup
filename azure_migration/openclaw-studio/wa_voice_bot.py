#!/usr/bin/env python3
"""
Maya — WhatsApp Business Calling voice agent (Pipecat + Azure).
Inbound WhatsApp call -> webhook -> WebRTC media -> Azure STT -> gpt-5.5 (Maya) -> Azure TTS -> back.

Env (see ~/.openclaw/wa_voice.env):
  WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_APP_SECRET,
  WHATSAPP_WEBHOOK_VERIFICATION_TOKEN,
  AZURE_SPEECH_KEY, AZURE_SPEECH_REGION,
  AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
Run:  uvicorn wa_voice_bot:app --host 0.0.0.0 --port 7860
Webhook: https://<public-host>/whatsapp   (GET verify + POST events)
"""
import os, asyncio, aiohttp
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager

from aiortc import RTCIceServer
from pipecat.transports.whatsapp.client import WhatsAppClient
from pipecat.transports.whatsapp.api import WhatsAppWebhookRequest
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.base_transport import TransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.azure.stt import AzureSTTService
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.azure.llm import AzureLLMService
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

WA_TOKEN  = os.environ["WHATSAPP_TOKEN"]
WA_PHONE  = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
WA_SECRET = os.environ.get("WHATSAPP_APP_SECRET") or None
WA_VERIFY = os.environ.get("WHATSAPP_WEBHOOK_VERIFICATION_TOKEN", "")
SPEECH_KEY = os.environ["AZURE_SPEECH_KEY"]
SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "centralindia")
AOAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AOAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://trigunai-lms-aoai.openai.azure.com")

MAYA_SYSTEM = (
    "You are Maya, a warm, natural voice agent from TrigunAI on a live WhatsApp call with an Indian "
    "coaching teacher. Speak Hindi/Hinglish by default; switch to English if they do. Keep EVERY turn "
    "to one or two short sentences — this is a phone call. Goal: confirm they teach, then pitch Acharya "
    "(an AI tutor on WhatsApp that answers their students' doubts 24x7 in Hindi & English, under the "
    "teacher's own brand, Rs 4,999/month), gauge interest, and if interested offer to send details on "
    "WhatsApp and book a callback with the founder. Be honest — never invent testimonials or numbers; "
    "if asked, say you're an AI assistant from TrigunAI. If they're not interested or busy, thank them "
    "and end politely. Open the call by greeting and asking if they are a teacher."
)

wa_client: WhatsAppClient | None = None
http_session: aiohttp.ClientSession | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wa_client, http_session
    http_session = aiohttp.ClientSession()
    ice = [RTCIceServer(urls="stun:stun.l.google.com:19302")]
    wa_client = WhatsAppClient(WA_TOKEN, WA_PHONE, http_session, ice_servers=ice, whatsapp_secret=WA_SECRET)
    yield
    await http_session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/whatsapp")
async def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == WA_VERIFY:
        return Response(content=q.get("hub.challenge", ""), media_type="text/plain")
    return Response(status_code=403)

async def on_connect(connection, call):
    """A WhatsApp call connected -> build Maya's pipeline on this WebRTC media."""
    transport = SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )
    stt = AzureSTTService(api_key=SPEECH_KEY, region=SPEECH_REGION, language="hi-IN")
    tts = AzureTTSService(api_key=SPEECH_KEY, region=SPEECH_REGION, voice="hi-IN-SwaraNeural")
    llm = AzureLLMService(api_key=AOAI_KEY, endpoint=AOAI_ENDPOINT, model="gpt-5.5")
    ctx = LLMContext([{"role": "system", "content": MAYA_SYSTEM}])
    agg = LLMContextAggregatorPair(ctx)
    pipeline = Pipeline([
        transport.input(), stt, agg.user(), llm, tts, transport.output(), agg.assistant(),
    ])
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    runner = PipelineRunner(handle_sigint=False)
    asyncio.create_task(runner.run(task))

@app.post("/whatsapp")
async def webhook(request: Request):
    body = await request.json()
    sig = request.headers.get("X-Hub-Signature-256")
    req = WhatsAppWebhookRequest(**body)
    await wa_client.handle_webhook_request(req, connection_callback=on_connect, sha256_signature=sig)
    return Response(status_code=200)

@app.get("/health")
async def health():
    return {"ok": True, "agent": "maya-whatsapp"}
