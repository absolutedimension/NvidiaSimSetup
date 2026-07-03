#!/usr/bin/env python3
"""
Maya over Twilio Programmable Voice (Media Streams).
Twilio call -> <Connect><Stream wss://.../twilio-stream> -> this WS -> Azure STT -> gpt-5.5 -> Azure TTS.
Env: AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT,
     TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
Run: uvicorn maya_twilio:app --host 0.0.0.0 --port 7861
"""
import os, json, random
from fastapi import FastAPI, WebSocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import TTSSpeakFrame, UserStoppedSpeakingFrame
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
AOAI_KEY = os.environ["AZURE_OPENAI_API_KEY"]; AOAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://trigunai-lms-aoai.openai.azure.com")
TW_SID = os.environ["TWILIO_ACCOUNT_SID"]; TW_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

OPENER = "नमस्ते! मैं माया बोल रही हूँ TrigunAI से। क्या मेरी बात किसी teacher या coaching चलाने वाले से हो रही है?"

MAYA_SYSTEM = (
    "You are Maya from TrigunAI on a live phone call with an Indian coaching teacher. "
    "You already greeted them with: 'नमस्ते! मैं माया बोल रही हूँ TrigunAI से। क्या मेरी बात किसी teacher "
    "या coaching चलाने वाले से हो रही है?' — do NOT greet again, just continue naturally from their reply. "
    "Speak warm, natural Hindi/Hinglish by default; switch to English if they do. Keep EVERY reply to ONE "
    "short sentence — this is a live call, sound relaxed and human, not scripted. "
    "Flow: (1) confirm they teach. (2) In one line pitch Acharya — an AI tutor on WhatsApp that answers "
    "their students' doubts 24x7 in Hindi & English, under the teacher's own brand, Rs 4,999/month. "
    "(3) Ask if they'd be interested. (4) THE MOMENT they show any interest, say warmly that you'll connect "
    "them on WhatsApp with full details right away, confirm this is a good number, thank them, and wrap up. "
    "Be honest: never invent testimonials or numbers; if asked, say you're an AI assistant from TrigunAI. "
    "If they're not interested or busy, thank them politely and end. Never repeat yourself."
)

app = FastAPI()

# Backchannel: the instant the caller stops speaking, Maya says a short "listening" nod
# (जी / हाँ / अच्छा / हम्म) so there is never dead air while the LLM composes the real reply.
class Backchannel(FrameProcessor):
    FILLERS = ["जी।", "हाँ जी।", "अच्छा।", "हम्म।", "जी बिल्कुल।"]

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        if isinstance(frame, UserStoppedSpeakingFrame) and direction == FrameDirection.DOWNSTREAM:
            await self.push_frame(TTSSpeakFrame(random.choice(self.FILLERS)))

@app.get("/twilio-health")
async def health():
    return {"ok": True, "agent": "maya-twilio"}

@app.websocket("/twilio-stream")
async def twilio_stream(ws: WebSocket):
    await ws.accept()
    await ws.receive_text()                              # Twilio 'connected'
    start = json.loads(await ws.receive_text())          # Twilio 'start'
    stream_sid = start["start"]["streamSid"]
    call_sid = start["start"]["callSid"]

    serializer = TwilioFrameSerializer(stream_sid=stream_sid, call_sid=call_sid,
                                       account_sid=TW_SID, auth_token=TW_TOKEN)
    # VAD tuned for smooth phone turn-taking: needs a real utterance to trigger,
    # waits a beat after the caller stops so short "hello"/"haan" don't barge in.
    vad = SileroVADAnalyzer(params=VADParams(
        confidence=0.7, start_secs=0.10, stop_secs=0.30, min_volume=0.6))
    transport = FastAPIWebsocketTransport(websocket=ws, params=FastAPIWebsocketParams(
        audio_in_enabled=True, audio_out_enabled=True, add_wav_header=False,
        vad_analyzer=vad, serializer=serializer))

    stt = AzureSTTService(api_key=SPEECH_KEY, region=SPEECH_REGION, language=Language.HI_IN)
    tts = AzureTTSService(api_key=SPEECH_KEY, region=SPEECH_REGION, voice="hi-IN-SwaraNeural")
    llm = AzureLLMService(api_key=AOAI_KEY, endpoint=AOAI_ENDPOINT, model="gpt-4o-mini")
    # Seed the opener as an already-spoken assistant turn so the LLM has context but doesn't re-greet.
    ctx = LLMContext([
        {"role": "system", "content": MAYA_SYSTEM},
        {"role": "assistant", "content": OPENER},
    ])
    agg = LLMContextAggregatorPair(ctx)
    pipeline = Pipeline([transport.input(), stt, agg.user(), llm, tts, transport.output(), agg.assistant()])
    task = PipelineTask(pipeline, params=PipelineParams(
        audio_in_sample_rate=8000, audio_out_sample_rate=8000, allow_interruptions=True))

    @transport.event_handler("on_client_connected")
    async def _on_conn(_t, _c):
        # Speak the opener instantly via TTS (no LLM round-trip) — kills the startup delay.
        await task.queue_frames([TTSSpeakFrame(OPENER)])

    @transport.event_handler("on_client_disconnected")
    async def _on_disc(_t, _c):
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
