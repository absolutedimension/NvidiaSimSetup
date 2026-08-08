#!/usr/bin/env python3
"""
Part C.1 — THE "OUR OWN MODEL" STEP.

Train a LoRA on seeds_clean/ (our own generated, VLM-approved images) so the base
model carries OUR signature aesthetic. This is what makes it "our model" and keeps
outputs consistent — the actual moat in this niche.

Trains ONLY on seeds_clean/ (never corpus/). A few hundred images -> a few A10G
hours -> a ~100-300 MB LoRA in loras/.

This wraps diffusers' official Flux LoRA trainer (train_dreambooth_lora_flux.py).
Fetch it once:
  git clone --depth 1 https://github.com/huggingface/diffusers /tmp/diffusers
  pip install -r /tmp/diffusers/examples/dreambooth/requirements_flux.txt

Usage: python3 train_lora.py --steps 1500 --rank 16 --name flowscape_v1
"""
import argparse, glob, os, subprocess, sys
import config as C

TRAINER = os.environ.get(
    "FLUX_TRAINER", "/tmp/diffusers/examples/dreambooth/train_dreambooth_lora_flux.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="flowscape_v1")
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--instance-prompt", default="in fscp ambient dreamscape style")
    args = ap.parse_args()

    imgs = glob.glob(os.path.join(C.SEEDS_CLEAN, "*.png"))
    if len(imgs) < 20:
        sys.exit(f"only {len(imgs)} clean seeds — generate/critic more first (want 150+).")
    if not os.path.exists(TRAINER):
        sys.exit(f"trainer not found: {TRAINER}\n  clone diffusers (see docstring) or set FLUX_TRAINER.")

    outdir = os.path.join(C.LORAS, args.name); os.makedirs(outdir, exist_ok=True)
    cmd = [
        "accelerate", "launch", TRAINER,
        f"--pretrained_model_name_or_path={C.IMAGE_MODEL}",
        f"--instance_data_dir={C.SEEDS_CLEAN}",
        f"--output_dir={outdir}",
        f"--instance_prompt={args.instance_prompt}",
        "--mixed_precision=bf16",
        f"--resolution={C.TARGET_H}",
        "--train_batch_size=1", "--gradient_accumulation_steps=4",
        "--gradient_checkpointing",
        f"--rank={args.rank}",
        f"--learning_rate={args.lr}",
        "--lr_scheduler=constant", "--lr_warmup_steps=0",
        f"--max_train_steps={args.steps}",
        "--seed=0", "--use_8bit_adam",
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"\nLoRA -> {outdir}/pytorch_lora_weights.safetensors")
    print("NEXT: python3 scene_plan.py  then  python3 render_flowscape.py")
    print("\n(Optional Part C.2 — MOTION LoRA on LTX-Video: train on 3-5s clips WE")
    print(" generated from these seeds. Same principle. See FLOWSCAPE_ENGINE.md §C.2.)")


if __name__ == "__main__":
    main()
