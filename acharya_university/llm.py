"""Chat helper for Acharya University.

Reuses the same Azure OpenAI idiom as lms/app/tutor.py, but also accepts any
OpenAI-compatible endpoint (e.g. the litellm proxy) so it runs locally for Deepak.

Config via env (Azure preferred, OpenAI-compatible fallback):
  AOAI_ENDPOINT, AOAI_KEY, AOAI_DEPLOYMENT (default gpt-4o-mini), AOAI_API_VERSION
  --- or ---
  OPENAI_BASE_URL (e.g. http://localhost:4000/v1), OPENAI_API_KEY, OPENAI_MODEL
"""
import json
import os
import urllib.error
import urllib.request

AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "").strip().rstrip("/")
AOAI_KEY = os.getenv("AOAI_KEY", "").strip()
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o-mini").strip()
AOAI_API_VERSION = os.getenv("AOAI_API_VERSION", "2024-10-21").strip()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()


def available() -> bool:
    return bool((AOAI_ENDPOINT and AOAI_KEY) or (OPENAI_BASE_URL and OPENAI_API_KEY))


def _request(url: str, headers: dict, payload: dict, timeout: int = 60) -> str | None:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        print(f"[llm] call failed: {exc}")
        return None


def chat(messages: list, temperature: float = 0.5, max_tokens: int = 800,
         json_mode: bool = False) -> str | None:
    """One chat completion. messages=[{role,content}]. Returns text or None."""
    if not available():
        print("[llm] no credentials configured (set AOAI_* or OPENAI_*)")
        return None
    payload = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if AOAI_ENDPOINT and AOAI_KEY:
        url = (f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOYMENT}"
               f"/chat/completions?api-version={AOAI_API_VERSION}")
        return _request(url, {"api-key": AOAI_KEY}, payload)
    url = f"{OPENAI_BASE_URL}/chat/completions"
    payload["model"] = OPENAI_MODEL
    return _request(url, {"Authorization": f"Bearer {OPENAI_API_KEY}"}, payload)


def extract_json(text: str | None) -> dict | None:
    """Parse a JSON object from an LLM reply, tolerating fences / stray prose."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start:end + 1])
        except (ValueError, TypeError):
            return None
    return None
