"""Layer B — the SURFACE student (realistic dialogue), wrapping the Layer A latent
state.  Uses the existing LiteLLM proxy on the EC2 box (port 4000 -> Azure
gpt-4o-mini), the same proxy the NVIDIA Content Agents already share.

This is NOT used to train the RL policy (that runs on the cheap numeric env).
It's for: (a) qualitative demos, (b) generating the synthetic SFT corpus
(gen_sft_data.py).  Keeping the latent state as ground truth means the student's
words are always consistent with its true mastery/misconceptions.

Env:
  LITELLM_URL   default http://localhost:4000/v1/chat/completions
                (on the Mac, SSH-tunnel it: ssh -L 4000:localhost:4000 ubuntu@$EC2_IP)
  LITELLM_KEY   default sk-trigunai-master-key-2026
  LITELLM_MODEL default gpt-4o-mini
"""
from __future__ import annotations
import os, json, urllib.request
from knowledge import SKILLS, MISC_BY_ID

URL = os.environ.get("LITELLM_URL", "http://localhost:4000/v1/chat/completions")
KEY = os.environ.get("LITELLM_KEY", "sk-trigunai-master-key-2026")
MODEL = os.environ.get("LITELLM_MODEL", "gpt-4o-mini")


def _chat(messages, temperature=0.8, max_tokens=160):
    body = json.dumps(dict(model=MODEL, messages=messages,
                           temperature=temperature, max_tokens=max_tokens)).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def student_persona(env) -> str:
    """Render the latent state into a system prompt that constrains the LLM student."""
    known = [SKILLS[i] for i in range(len(SKILLS)) if env.mastery[i] > 0.6]
    shaky = [SKILLS[i] for i in range(len(SKILLS)) if 0.3 <= env.mastery[i] <= 0.6]
    unknown = [SKILLS[i] for i in range(len(SKILLS)) if env.mastery[i] < 0.3]
    miscs = [MISC_BY_ID[m]["desc"] for m in env.misc]
    t = env.traits
    style = ("terse" if t["help_seeking"] < 0.4 else "asks lots of questions")
    return (
        "You are roleplaying a STUDENT learning to build AI agents. Stay in character. "
        "Answer in 1-3 short sentences, like a real learner — make mistakes consistent "
        "with what you don't know yet. Do NOT break character or be a perfect student.\n"
        f"- You solidly understand: {', '.join(known) or 'almost nothing yet'}.\n"
        f"- You're shaky on: {', '.join(shaky) or 'n/a'}.\n"
        f"- You do NOT understand: {', '.join(unknown) or 'n/a'}.\n"
        f"- Active misconceptions you currently hold (voice them when relevant): "
        f"{'; '.join(miscs) or 'none'}.\n"
        f"- Personality: {style}; frustration {env.affect['frustration']:.1f}, "
        f"engagement {env.affect['engagement']:.1f}.\n"
        "If a question is above your level, attempt it imperfectly or say you're unsure."
    )


def student_reply(env, tutor_utterance: str, history: list[dict]) -> str:
    msgs = [{"role": "system", "content": student_persona(env)}]
    msgs += history[-6:]
    msgs.append({"role": "user", "content": tutor_utterance})
    try:
        return _chat(msgs)
    except Exception as e:  # offline / no tunnel -> degrade gracefully
        return f"[student-llm unavailable: {e}]"


if __name__ == "__main__":
    # tiny smoke test against a fresh latent student
    from student_env import StudentEnv
    env = StudentEnv(seed=7); env.reset(seed=7)
    print("PERSONA:\n", student_persona(env), "\n")
    print("TUTOR: Can you tell me, in your own words, what makes something an *agent* "
          "rather than just a chatbot?")
    print("STUDENT:", student_reply(env, "What makes something an agent vs a chatbot?", []))
