#!/usr/bin/env python3
"""Same-base generator for BOTH arms — isolates method (RAG vs fine-tune) by holding
the base model fixed at Qwen-7B-Instruct.

  --arm rag : base model + retrieved real exemplars in the prompt (your generator.build_prompt)
  --arm ft  : LoRA-fine-tuned model + plain instruction, NO exemplars

Both pass the IDENTICAL validator + novelty gate. Runs on the A10G.

  python3 gen_local.py --arm rag
  FT_MODEL_DIR=artifacts/lora-qwen python3 gen_local.py --arm ft
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)

from qbank import generator, validator          # noqa: E402
from qbank.storage import Store                  # noqa: E402

ART = os.path.join(HERE, "artifacts")
BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
FT_MODEL_DIR = os.environ.get("FT_MODEL_DIR", os.path.join(ART, "lora-qwen"))
MAX_RETRIES = 2
SYSTEM_FT = ("You are an expert author of original Indian competitive-exam physics "
             "questions. You never copy or paraphrase existing questions.")


def _instruction(spec):
    return (f"Write one {spec['exam']} {spec['subject']} question.\n"
            f"Chapter: {spec.get('chapter')}\nConcept: any within the chapter\n"
            f"Difficulty: {spec.get('dmax')} on a 1-5 scale\n"
            f"Format: a single-correct MCQ with exactly 4 options\n"
            'Return JSON: {"stem","options":[{"label","text"}],"correct_answer","solution"}. '
            "Use LaTeX for math.")


def load(arm):
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    # 4-bit so a 7B fits alongside the agent containers (~12 GB free on the shared A10G);
    # identical quantization for both arms -> still a fair method comparison, and it
    # matches the QLoRA-trained adapter's base.
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, quantization_config=bnb, device_map={"": 0},
        torch_dtype=torch.bfloat16)
    if arm == "ft":
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, FT_MODEL_DIR)
    model.eval()
    return tok, model


def gen(tok, model, system, user):
    import torch
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=900, do_sample=True,
                             temperature=0.8, top_p=0.9, pad_token_id=tok.eos_token_id)
    resp = tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"\{.*\}", resp, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["rag", "ft"], required=True)
    a = ap.parse_args()

    specs = json.load(open(os.path.join(ART, "specs.json")))
    bank = json.load(open(os.path.join(ART, "bank_stems.json")))
    store = Store()
    tok, model = load(a.arm)

    out = []
    for s in specs:
        spec = dict(s, qtype="MCQ_single")
        if a.arm == "rag":
            exemplars = generator.retrieve_exemplars(store, spec, k=3)
            system, user = generator.build_prompt(spec, exemplars)
        else:
            system, user = SYSTEM_FT, _instruction(spec)
        clean = 0
        for i in range(s.get("count", 4)):
            for attempt in range(MAX_RETRIES + 1):
                data = gen(tok, model, system, user)
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
        print(f"  {s['chapter']:<32} clean={clean}/{s.get('count')}")

    tag = f"local_{a.arm}"
    json.dump({"arm": tag, "base": BASE_MODEL,
               "adapter": FT_MODEL_DIR if a.arm == "ft" else None, "questions": out},
              open(os.path.join(ART, f"out_{a.arm}_qwen.json"), "w"),
              indent=2, ensure_ascii=False)
    print(f"\nArm [{tag}]: {len(out)} clean -> artifacts/out_{a.arm}_qwen.json")


if __name__ == "__main__":
    main()
