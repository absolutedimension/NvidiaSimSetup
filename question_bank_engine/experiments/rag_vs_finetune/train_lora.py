#!/usr/bin/env python3
"""QLoRA SFT of a Qwen base on the bank's 120 Qs — no trl (peft + transformers.Trainer),
robust across transformers 5.x. Runs on the A10G (shares GPU with the agent containers,
so kept conservative: batch 1, grad-accum 8, seq 1024, 4-bit).

  BASE_MODEL=Qwen/Qwen2.5-7B-Instruct python3 train_lora.py
Writes the adapter to artifacts/lora-qwen/.

HONEST NOTE: ~120 examples = a *style/format* LoRA (house JSON+LaTeX shape + JEE
phrasing), NOT physics knowledge. The eval's novelty gate catches memorization.
"""
import json
import os

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, Trainer, TrainingArguments)

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "artifacts")
OUT = os.path.join(ART, "lora-qwen")
EPOCHS = float(os.environ.get("EPOCHS", "4"))
MAXLEN = int(os.environ.get("MAXLEN", "512"))  # keeps the 152k-vocab logits spike small


def main():
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, quantization_config=bnb, device_map={"": 0},
        torch_dtype=torch.bfloat16)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"]))
    model.print_trainable_parameters()
    model.config.use_cache = False

    raw = load_dataset("json", data_files=os.path.join(ART, "ft_train.jsonl"),
                       split="train")

    def tokenize(ex):
        text = tok.apply_chat_template(ex["messages"], tokenize=False)
        out = tok(text, truncation=True, max_length=MAXLEN, padding="max_length")
        out["labels"] = [t if t != tok.pad_token_id else -100 for t in out["input_ids"]]
        return out

    ds = raw.map(tokenize, remove_columns=raw.column_names)
    print(f"train rows: {len(ds)}  (maxlen {MAXLEN})")

    def collate(batch):
        return {k: torch.tensor([b[k] for b in batch]) for k in
                ("input_ids", "attention_mask", "labels")}

    args = TrainingArguments(
        output_dir=OUT, num_train_epochs=EPOCHS,
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        learning_rate=2e-4, warmup_ratio=0.05, lr_scheduler_type="cosine",
        logging_steps=5, save_strategy="no", bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit", report_to=[])

    Trainer(model=model, args=args, train_dataset=ds, data_collator=collate).train()
    model.save_pretrained(OUT)
    tok.save_pretrained(OUT)
    print(f"adapter saved -> {OUT}")


if __name__ == "__main__":
    main()
