"""Thin OpenAI-compatible client for the TrigunAI LiteLLM/Azure proxy.

Degrades gracefully: if the proxy is unreachable (or QBANK_LLM=off) `.ok` stays
False and every caller falls back to rule-based logic, so the whole pipeline still
runs offline. Set QBANK_LLM=on to make LLM calls mandatory (raises if unreachable)."""
import base64
import json

from . import config


def _is_reasoning_model(name: str) -> bool:
    """Reasoning models (gpt-5.x, o1/o3) reject a custom `temperature` — only the
    default (1) is allowed — so we must omit the param entirely for them."""
    n = (name or "").lower()
    return "gpt-5" in n or n.startswith("o1") or n.startswith("o3")


class LLM:
    def __init__(self):
        self.ok = False
        self.client = None
        self.last_error = None
        if config.LLM_ENABLED == "off":
            self.last_error = "QBANK_LLM=off"
            return
        try:
            from openai import OpenAI
            # reasoning models (gpt-5.x) can take >60s on hard problems — give them room
            self.client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY, timeout=240)
            self.ok = True  # optimistic; a failed call flips callers to fallback
        except Exception as e:  # openai not installed / bad config
            self.last_error = str(e)
            if config.LLM_ENABLED == "on":
                raise

    def chat_json(self, system: str, user: str, model: str | None = None,
                  temperature: float = 0.1) -> dict | None:
        if not self.client:
            return None
        model = model or config.CHAT_MODEL
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                response_format={"type": "json_object"},
            )
            if not _is_reasoning_model(model):
                kwargs["temperature"] = temperature
            r = self.client.chat.completions.create(**kwargs)
            return json.loads(r.choices[0].message.content)
        except Exception as e:
            self.last_error = str(e)
            self.ok = False
            if config.LLM_ENABLED == "on":
                raise
            return None

    def vision_json(self, system: str, prompt: str, image_bytes: bytes,
                    mime: str = "image/png", model: str | None = None) -> dict | None:
        """Used by the PDF extractor path (scanned pages -> structured questions)."""
        if not self.client:
            return None
        model = model or config.VISION_MODEL
        try:
            b64 = base64.b64encode(image_bytes).decode()
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ]},
                ],
                response_format={"type": "json_object"},
            )
            if not _is_reasoning_model(model):
                kwargs["temperature"] = 0.1
            r = self.client.chat.completions.create(**kwargs)
            return json.loads(r.choices[0].message.content)
        except Exception as e:
            self.last_error = str(e)
            self.ok = False
            if config.LLM_ENABLED == "on":
                raise
            return None
