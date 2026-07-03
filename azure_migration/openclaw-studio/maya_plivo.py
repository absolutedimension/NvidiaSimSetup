#!/usr/bin/env python3
"""
Maya over Plivo Voice (Audio Streaming) — India-native telephony path.
Plivo call -> answer_url returns <Stream wss://.../plivo-stream> -> this WS -> Azure STT -> gpt-4o-mini (India) -> Azure TTS.
Env (see ~/voicebot_wa/wa_voice.env + plivo.env):
  AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
  PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN
Run: uvicorn maya_plivo:app --host 0.0.0.0 --port 7862
Public: https://gurukul.trigunai.com/plivo-answer  (answer_url)  +  wss://gurukul.trigunai.com/plivo-stream
"""
import os, json, asyncio
from fastapi import FastAPI, WebSocket, Request, Response
from pipecat.serializers.plivo import PlivoFrameSerializer
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import (TTSSpeakFrame, EndFrame, TextFrame, StartFrame,
                                    InputAudioRawFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame,
                                    LLMFullResponseStartFrame, LLMFullResponseEndFrame)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.azure.stt import AzureSTTService
from pipecat.services.azure.tts import AzureTTSService
from pipecat.services.azure.llm import AzureLLMService
from pipecat.transcriptions.language import Language
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

SPEECH_KEY = os.environ["AZURE_SPEECH_KEY"]; SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "centralindia")
AOAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]; AOAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://maya-india-aoai.openai.azure.com")
PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID"); PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN")
STREAM_WSS = os.environ.get("MAYA_PLIVO_WSS", "wss://gurukul.trigunai.com/plivo-stream")

OPENER = "नमस्ते! मैं TrigunAI से माया बोल रही हूँ। क्या आप एक teacher हैं, coaching चलाते हैं, या teaching से कमाना चाहते हैं?"

MAYA_SYSTEM = (
    "You are Maya from TrigunAI making a SHORT screening call in Hindi/Hinglish. This is NOT a sales pitch and "
    "NOT a conversation — you only capture yes/no interest and then END the call. "
    "You already greeted and asked: 'क्या आप एक teacher हैं, coaching चलाते हैं, या teaching से कमाना चाहते हैं?' "
    "Do NOT greet again. "
    "HARD RULES: Speak ONE short line per turn. Ask only yes/no or one-word questions. Never chat, never explain at "
    "length, never repeat a line you already said. NEVER mention any price, fees, or rupees. "
    "FLOW (follow strictly, one step at a time, never skip or repeat): "
    "(1) If they are NOT a teacher/tutor and do NOT want to earn from teaching → thank them politely in one line and END. "
    "(2) If they teach, run coaching, or want to earn from teaching → say in ONE line: they get a 14-day free trial "
    "to explore integrating cutting-edge AI technology into their teaching and scale their work. "
    "(3) Then ask ONE line: 'क्या आपको इसमें interest है?' "
    "(4) UNDERSTAND their reply carefully before deciding. Treat ANY sign of engagement as INTERESTED — 'haan', "
    "'yes', 'ठीक है', 'tell me more', 'more information', 'aur batao', 'how does it work', 'kaise', 'details', or "
    "asking ANY question about it all mean INTERESTED. Only a clear refusal ('नहीं', 'no', 'not interested', "
    "'busy', 'abhi nahi') means NOT interested. If the reply is unclear or you didn't catch it, ask one short "
    "yes/no question again — NEVER assume 'no'. "
    "(5) If INTERESTED → say in ONE line exactly 'बढ़िया! हमारी team आपसे पूरी जानकारी के साथ जल्द connect करेगी।' and stop. "
    "(6) If NOT interested → say in ONE line exactly 'कोई बात नहीं, आपके समय के लिए धन्यवाद!' and stop. "
    "Keep the WHOLE call to just a few short turns. Be honest — you are an AI assistant from TrigunAI; "
    "never invent testimonials or numbers."
)

app = FastAPI()

# Detects Maya's CLOSING line by phrase (accumulated over the full streamed response,
# so nothing is spoken) and hangs up a few seconds later, after it plays out.
class EndCallProcessor(FrameProcessor):
    CLOSERS = ("समय के लिए", "connect कर", "connect करेगी")

    def __init__(self):
        super().__init__()
        self._task = None
        self._buf = ""
        self._scheduled = False

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, LLMFullResponseStartFrame):
            self._buf = ""
        elif isinstance(frame, TextFrame) and getattr(frame, "text", None):
            self._buf += frame.text
        elif isinstance(frame, LLMFullResponseEndFrame):
            if (not self._scheduled and self._task is not None
                    and any(c in self._buf for c in self.CLOSERS)):
                self._scheduled = True
                asyncio.create_task(self._hangup_after())
        await self.push_frame(frame, direction)

    async def _hangup_after(self):
        await asyncio.sleep(6)          # let the short closing line play out
        await self._task.queue_frame(EndFrame())

# Ignores the caller's audio for a short window at the start so an early "hello"
# can't interrupt or restart Maya's opening greeting.
class OpenerGuard(FrameProcessor):
    GUARD_SECS = 6.0

    def __init__(self):
        super().__init__()
        self._open_at = None

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, StartFrame) and self._open_at is None:
            self._open_at = asyncio.get_event_loop().time() + self.GUARD_SECS
        if (self._open_at is not None
                and asyncio.get_event_loop().time() < self._open_at
                and direction == FrameDirection.DOWNSTREAM
                and isinstance(frame, (InputAudioRawFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame))):
            return  # swallow early caller audio during the greeting
        await self.push_frame(frame, direction)

@app.get("/plivo-health")
async def health():
    return {"ok": True, "agent": "maya-plivo"}

# Plivo fetches this (GET or POST) when the call is answered; we return streaming XML.
@app.api_route("/plivo-answer", methods=["GET", "POST"])
async def answer(_request: Request):
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Stream bidirectional="true" keepCallAlive="true" '
        f'contentType="audio/x-mulaw;rate=8000" audioTrack="inbound">{STREAM_WSS}</Stream>'
        '</Response>'
    )
    return Response(content=xml, media_type="application/xml")

@app.websocket("/plivo-stream")
async def plivo_stream(ws: WebSocket):
    await ws.accept()
    # Read messages until Plivo's "start" event (carries streamId + callId)
    stream_id = call_id = None
    for _ in range(5):
        msg = json.loads(await ws.receive_text())
        if msg.get("event") == "start":
            st = msg.get("start", {})
            stream_id = st.get("streamId"); call_id = st.get("callId")
            break
    if not stream_id:
        await ws.close(); return

    serializer = PlivoFrameSerializer(stream_id=stream_id, call_id=call_id,
                                      auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)
    vad = SileroVADAnalyzer(params=VADParams(
        confidence=0.7, start_secs=0.10, stop_secs=0.30, min_volume=0.6))
    transport = FastAPIWebsocketTransport(websocket=ws, params=FastAPIWebsocketParams(
        audio_in_enabled=True, audio_out_enabled=True, add_wav_header=False,
        vad_analyzer=vad, serializer=serializer))

    stt = AzureSTTService(api_key=SPEECH_KEY, region=SPEECH_REGION, language=Language.HI_IN)
    tts = AzureTTSService(api_key=SPEECH_KEY, region=SPEECH_REGION, voice="hi-IN-SwaraNeural")
    llm = AzureLLMService(api_key=AOAI_KEY, endpoint=AOAI_ENDPOINT, model="gpt-4o-mini")
    ctx = LLMContext([
        {"role": "system", "content": MAYA_SYSTEM},
        {"role": "assistant", "content": OPENER},
    ])
    agg = LLMContextAggregatorPair(ctx)
    endcall = EndCallProcessor()
    guard = OpenerGuard()
    pipeline = Pipeline([transport.input(), guard, stt, agg.user(), llm, endcall, tts, transport.output(), agg.assistant()])
    task = PipelineTask(pipeline, params=PipelineParams(
        audio_in_sample_rate=8000, audio_out_sample_rate=8000, allow_interruptions=False))
    endcall._task = task

    @transport.event_handler("on_client_connected")
    async def _on_conn(_t, _c):
        await task.queue_frames([TTSSpeakFrame(OPENER)])

    @transport.event_handler("on_client_disconnected")
    async def _on_disc(_t, _c):
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
