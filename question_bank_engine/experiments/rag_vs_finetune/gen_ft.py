#!/usr/bin/env python3
"""Arm B — fine-tuned model, NO retrieval. Authors questions against the SAME specs.json
using ONLY the LoRA-fine-tuned model (it must have internalized the JEE house style from
training). Runs through the IDENTICAL validator + novelty gate as Arm A, so the only
difference between arms is method (fine-tune-from-weights vs retrieve-exemplars-in-prompt).

Runs on the A10G box (CUDA). Point at the trained adapter:
  FT_MODEL_DIR=./artifacts/lora-qwen  BASE_MODEL=Qwen/Qwen2.5-7B-Instruct  python3 gen_ft.py
Output: artifacts/out_ft.json
"""
import json
import os
import re
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)

from qbank import generator, validator          # noqa: E402

ART = os.path.join(HERE, "artifacts")
BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
FT_MODEL_DIR = os.environ.get("FT_MODEL_DIR", os.path.join(ART, "lora-qwen"))
MAX_RETRIES = 2

SYSTEM = ("You are an expert author of original Indian competitive-exam physics questions. "
          "You never copy or paraphrase existing questions.")


def _instruction(spec: dict) -> str:
    return (
        f"Write one {spec['exam']} {spec['subject']} question.\n"
        f"Chapter: {spec.get('chapter')}\n"
        f"Concept: any within the chapter\n"
        f"Difficulty: {spec.get('dmax')} on a 1-5 scale\n"
        f"Format: a single-correct MCQ with exactly 4 options\n"
        'Return JSON: {"stem","options":[{"label","text"}],"correct_answer","solution"}. '
        "Use LaTeX for math."
    )


def _load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
    model = PeftModel.from_pretrained(model, FT_MODEL_DIR)
    model.eval()
    return tok, model


def _gen_json(tok, model, instruction: str) -> dict | None:
    import torch
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": instruction}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        gen = model.generate(**inputs, max_new_tokens=900, do_sample=True,
                             temperature=0.8, top_p=0.9, pad_token_id=tok.eos_token_id)
    resp = tok.decode(gen[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"\{.*\}", resp, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def main():
    specs = json.load(open(os.path.join(ART, "specs.json")))
    bank = json.load(open(os.path.join(ART, "bank_stems.json")))
    tok, model = _load_model()

    out = []
    for s in specs:
        spec = dict(s, qtype="MCQ_single")
        clean = 0
        for i in range(s.get("count", 4)):
            for attempt in range(MAX_RETRIES + 1):
                data = _gen_json(tok, model, _instruction(spec))
                if not data:
                    continue
                q = generator._to_question(data, spec, i)
                issues = validator.rule_check(q)
                sim = generator.novelty(q, bank)
                if sim >= generator.NOVELTY_MAX_SIM:
                    issues.append(f"too_similar({sim:.2f})")
                if issues and attempt < MAX_RETRIES:
                    continue
                if issues:
                    break
                d = q.to_dict()
                d["_novelty"] = round(sim, 3)
                out.append(d)
                clean += 1
                break
        print(f"  {s['chapter']:<32} requested={s.get('count')} clean={clean}")

    json.dump({"arm": "finetune", "base": BASE_MODEL, "adapter": FT_MODEL_DIR,
               "questions": out}, open(os.path.join(ART, "out_ft.json"), "w"),
              indent=2, ensure_ascii=False)
    print(f"\nArm B (fine-tune): {len(out)} clean questions -> artifacts/out_ft.json")


if __name__ == "__main__":
    main()
