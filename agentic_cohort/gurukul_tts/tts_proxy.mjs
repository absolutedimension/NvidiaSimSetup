// Azure neural TTS proxy for the Acharya web chat (🔊 read-aloud).
// GET/POST /chat/tts  { text, voice? } -> audio/mpeg. Key stays server-side.
import http from "node:http";

const KEY = process.env.AZURE_SPEECH_KEY;
const REGION = process.env.AZURE_SPEECH_REGION || "centralindia";
const PORT = Number(process.env.TTS_PORT || 7870);
const ENDPOINT = `https://${REGION}.tts.speech.microsoft.com/cognitiveservices/v1`;
const DEFAULT_VOICE = process.env.TTS_VOICE || "hi-IN-SwaraNeural";
const ALLOWED = new Set(["hi-IN-SwaraNeural","hi-IN-AnanyaNeural","hi-IN-MadhurNeural","en-IN-NeerjaNeural","en-IN-PrabhatNeural"]);

const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const ssml = (text, voice) =>
  `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="hi-IN">` +
  `<voice name="${voice}"><prosody rate="-4%">${esc(text)}</prosody></voice></speak>`;

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, "http://x");
  if (req.method === "OPTIONS") { res.writeHead(204, {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"Content-Type"}); return res.end(); }
  if (u.pathname === "/health") { res.writeHead(200); return res.end("ok"); }
  if (u.pathname === "/chat/tts" || u.pathname === "/tts") {
    let text = "", voice = DEFAULT_VOICE;
    if (req.method === "POST") {
      let b = ""; for await (const c of req) { b += c; if (b.length > 20000) break; }
      try { const j = JSON.parse(b); text = (j.text||"").toString(); voice = j.voice || DEFAULT_VOICE; } catch {}
    } else { text = u.searchParams.get("text") || ""; voice = u.searchParams.get("voice") || DEFAULT_VOICE; }
    text = text.trim().slice(0, 1500);
    if (!ALLOWED.has(voice)) voice = DEFAULT_VOICE;
    if (!text) { res.writeHead(400, {"Access-Control-Allow-Origin":"*"}); return res.end("no text"); }
    try {
      const r = await fetch(ENDPOINT, { method: "POST", headers: {
        "Ocp-Apim-Subscription-Key": KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "acharya-tts" }, body: ssml(text, voice) });
      if (!r.ok) { res.writeHead(502, {"Access-Control-Allow-Origin":"*"}); return res.end("tts " + r.status); }
      const buf = Buffer.from(await r.arrayBuffer());
      res.writeHead(200, {"Content-Type":"audio/mpeg","Cache-Control":"no-store","Access-Control-Allow-Origin":"*"});
      return res.end(buf);
    } catch (e) { res.writeHead(500, {"Access-Control-Allow-Origin":"*"}); return res.end("err"); }
  }
  res.writeHead(404); res.end("not found");
});
server.listen(PORT, "127.0.0.1", () => console.log(`acharya tts proxy on 127.0.0.1:${PORT} (voice=${DEFAULT_VOICE}, region=${REGION})`));
