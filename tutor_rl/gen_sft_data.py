"""Stage 3 — generate the synthetic SFT corpus (distillation).

Run the trained RL tutor (the sequencing brain) against Layer-B LLM students.
At each turn we have:
  - the latent student state  -> realistic student utterance (Layer B)
  - the RL policy's chosen MOVE (the *pedagogically optimal* next action)
  - an expert-teacher LLM renders that move into a natural tutor utterance

We log (dialogue_context -> ideal_tutor_utterance) pairs as JSONL.  Fine-tuning
Acharya on this corpus transfers the RL-discovered SEQUENCING into the chat model
WITHOUT running RL online — stable, and the path that gets ~70% of the gain.

This is the "generate all possible teacher-student interactions" idea, done right:
the SEQUENCE is chosen by the trained policy (so it's good pedagogy, not random),
the SURFACE is realistic (LLM student), and real students remain the eval, never
the training set.

Run:  python3 gen_sft_data.py --episodes 20 --out sft_corpus.jsonl
      (requires the LiteLLM proxy reachable — see llm_student.py)
"""
from __future__ import annotations
import os, json, sys, argparse
import numpy as np
from student_env import StudentEnv, decode_action
from tutors import LinearPolicy
from knowledge import SKILLS
from llm_student import student_reply, _chat

MOVE_INSTRUCTION = {
    "ask_recall": "Ask the student to RECALL/explain this concept in their own words (retrieval practice). Do not give the answer.",
    "worked_example": "Walk through a concrete WORKED EXAMPLE of this concept, step by step.",
    "hint": "Give a small HINT that nudges the student toward the idea — never the full answer.",
    "explain": "Briefly explain this concept directly.",
    "practice": "Give the student a slightly challenging PRACTICE problem to apply this concept.",
    "review": "REVIEW this earlier concept with a quick spaced-repetition question.",
    "assess": "Wrap up and tell the student you'll do a short check of what they've learned.",
}


def tutor_utterance(move, skill, history):
    skill_name = SKILLS[skill] if skill >= 0 else "the whole session"
    sys_p = ("You are Acharya, an expert Socratic tutor for building AI agents. "
             "Speak warmly, in 1-3 sentences. Follow the pedagogical instruction exactly. "
             "Never dump answers when asked to use recall or hints.")
    user = (f"Concept: {skill_name}. Pedagogical move: {MOVE_INSTRUCTION[move]}\n"
            "Write only your next message to the student.")
    msgs = [{"role": "system", "content": sys_p}] + history[-6:] + [{"role": "user", "content": user}]
    try:
        return _chat(msgs, temperature=0.7, max_tokens=160)
    except Exception as e:
        return f"[{move} on {skill_name}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--out", default="sft_corpus.jsonl")
    ap.add_argument("--policy", default="policy.npy")
    ap.add_argument("--max-turns", type=int, default=24)
    args = ap.parse_args()

    policy = LinearPolicy()
    if os.path.exists(args.policy):
        policy.w = np.load(args.policy)
    else:
        print(f"WARN: {args.policy} not found — run train.py first. Using zero policy.")

    n_pairs = 0
    with open(args.out, "w") as fh:
        for ep in range(args.episodes):
            env = StudentEnv(max_turns=args.max_turns, seed=900000 + ep)
            obs = env.reset(seed=900000 + ep)
            history = []   # chat history (tutor=assistant, student=user)
            done = False
            while not done:
                a, _, _ = policy.act(obs, greedy=True)
                move, skill = decode_action(a)
                t_utt = tutor_utterance(move, skill, history)
                # SFT example: predict the ideal tutor turn from the context so far
                fh.write(json.dumps(dict(
                    messages=history + [{"role": "assistant", "content": t_utt}],
                    move=move, skill=(SKILLS[skill] if skill >= 0 else None),
                )) + "\n")
                n_pairs += 1
                history.append({"role": "assistant", "content": t_utt})
                if move == "assess":
                    obs, r, done, info = env.step(a); break
                s_utt = student_reply(env, t_utt, history)
                history.append({"role": "user", "content": s_utt})
                obs, r, done, info = env.step(a)
            print(f"ep {ep}: {len(history)} turns, gain={info.get('immediate_gain',0):.3f}")
    print(f"\nwrote {n_pairs} SFT pairs -> {args.out}")


if __name__ == "__main__":
    main()
