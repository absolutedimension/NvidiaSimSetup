# Acharya web-chat neural voice (read-aloud 🔊)
Replaces the browser's cheap speechSynthesis with Azure neural TTS.
- `tts_proxy.mjs` → VM `~/.openclaw/gurukul/tts_proxy.mjs`, systemd --user `acharya-tts.service` on :7870, reads AZURE_SPEECH_KEY from `~/voicebot_wa/wa_voice.env`. Calls Azure Speech REST TTS, returns audio/mpeg.
- Caddy route `/chat/tts*` → localhost:7870 (before the catch-all). `/chat` + `/chat/api` still go to the bridge.
- `chat.html` (VM `~/.openclaw/gurukul/chat.html`, read fresh per request → scp = live, no restart): `speak()` now fetches /chat/tts and plays via Audio(); browserSpeak() is the fallback.
- **Change the voice:** edit TTS_VOICE default in tts_proxy.mjs (or set env) — hi-IN-SwaraNeural (default) / hi-IN-AnanyaNeural / hi-IN-MadhurNeural / en-IN-NeerjaNeural. Restart acharya-tts.service.
- Premium option: swap the Azure REST call for ElevenLabs (needs key + $).
