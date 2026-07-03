#!/usr/bin/env python3
"""
TrigunAI cold-call voice agent — brain + voice (no telephony).
Given what the teacher just said + the conversation so far, gpt-5.5 decides Maya's next line
(short, Hinglish, honest), then Azure Speech renders it to MP3.

Usage:
  voicebot_reply.py --user "haan main biology padhata hoon" [--history history.json] --out reply.mp3
Prints Maya's reply text; writes the spoken MP3 to --out; appends the turn to --history.
"""
import os, sys, json, re, argparse, urllib.request, urllib.parse

AOAI_ENDPOINT = "https://trigunai-lms-aoai.openai.azure.com/openai/v1/chat/completions"
AOAI_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "")
SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "centralindia")

SYSTEM = """You are Maya, a warm, natural voice agent calling on behalf of TrigunAI (an Indian ed-tech).
You are phoning independent coaching teachers in Bihar/India. This is a live phone call.

GOAL of the call (in order): 1) confirm they're a teacher, 2) in one or two lines pitch Acharya —
an AI tutor on WhatsApp that answers their students' doubts 24x7, in Hindi & English, UNDER THE
TEACHER'S OWN BRAND NAME, for Rs 4,999/month, 3) gauge interest, 4) if interested, offer to send
details on WhatsApp and book a 10-min callback with the founder. If not interested or busy, thank
them and close politely.

STYLE: This is a PHONE CALL. Speak in natural Hindi/Hinglish by default; switch to English if they do.
Keep EVERY turn to ONE or TWO short sentences — never a paragraph. Sound human, friendly, unhurried.
Ask one thing at a time. Mirror their language.

HONESTY (hard rules): Never invent testimonials, student numbers, or results. If asked, say you're
an AI assistant from TrigunAI. If they say they're on DND / not interested / to remove them, apologize
briefly and end the call. Never pressure.

OUTPUT: reply with ONLY the exact words Maya says next — no quotes, no stage directions, no name prefix."""

def llm(history, user):
    msgs = [{"role": "system", "content": SYSTEM}] + history + [{"role": "user", "content": user}]
    body = json.dumps({"model": "gpt-5.5", "messages": msgs, "max_completion_tokens": 200}).encode()
    req = urllib.request.Request(AOAI_ENDPOINT, data=body,
        headers={"Authorization": f"Bearer {AOAI_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

def tts(text, out):
    # Hindi voice if the reply has Devanagari, else Indian-English
    voice = "hi-IN-SwaraNeural" if re.search(r"[ऀ-ॿ]", text) else "en-IN-NeerjaNeural"
    lang = "hi-IN" if voice.startswith("hi") else "en-IN"
    ssml = f'<speak version="1.0" xml:lang="{lang}"><voice name="{voice}">{text}</voice></speak>'
    req = urllib.request.Request(
        f"https://{SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": SPEECH_KEY, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3"})
    with urllib.request.urlopen(req, timeout=30) as r:
        open(out, "wb").write(r.read())
    return voice

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--history", default="")
    ap.add_argument("--out", default="/tmp/reply.mp3")
    a = ap.parse_args()
    hist = json.load(open(a.history)) if a.history and os.path.exists(a.history) else []
    reply = llm(hist, a.user)
    voice = tts(reply, a.out)
    print(f"[{voice}] MAYA: {reply}")
    if a.history:
        hist += [{"role": "user", "content": a.user}, {"role": "assistant", "content": reply}]
        json.dump(hist, open(a.history, "w"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
