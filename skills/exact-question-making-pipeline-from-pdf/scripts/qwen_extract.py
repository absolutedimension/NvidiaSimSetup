#!/usr/bin/env python3
"""
qwen_extract.py — Vision-LLM extractor: exam PDF -> per-question JSON (REAL questions, verbatim).

Runs on a GPU box (proven on the EC2 A10G, 24GB). Uses Qwen2.5-VL-7B-Instruct because
general gpt-4o PARAPHRASES multi-statement questions (drops the numbered statements) — Qwen
keeps the statements intact and renders tables as markdown. It does NOT solve or invent
anything: it transcribes the question text + options exactly as printed.

Output schema (one file per PDF, keyed by question number):
  { "1": {"number": 1, "stem": "...", "raw_options": ["(a) ..","(b) .."],
          "options": {"A": "..", "B": "..", "C": "..", "D": ".."}}, ... }

Idempotent per number: keeps the FIRST non-empty English version of each question number
(bilingual papers repeat every question in Hindi — the prompt tells Qwen to SKIP Hindi pages,
and this keep-first rule is the backstop).

Usage:
  pip install --break-system-packages transformers accelerate qwen-vl-utils pymupdf pillow torch
  python3 qwen_extract.py --pdf 2025_QP1.pdf --out qwen/2025_QP1.json \
      --dpi 200 --max-options 4
  # batch:
  for f in *_QP*.pdf; do python3 qwen_extract.py --pdf "$f" --out "qwen/${f%.pdf}.json"; done

Notes:
  * HF cache on ephemeral NVMe if root disk is small:  export HF_HOME=/mnt/nvme/hf
  * The model loads ONCE and streams pages — do not re-launch per page.
  * Tune SYSTEM_PROMPT per board (see CLASS 10/12 note at bottom).
"""
import argparse, io, json, os, re, sys

MODEL_ID = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")

SYSTEM_PROMPT = """You are a precise exam-paper transcriber. You are shown ONE page image of an
official exam question paper. Transcribe every complete multiple-choice question on the page
VERBATIM — do not paraphrase, summarise, translate, solve, or add anything.

Rules:
- If the page is in Hindi (or any non-English language), return exactly: {"questions": []}
- Keep numbered statements (1., 2., 3. or I., II., III.) EXACTLY as printed, in order.
- Render any table as GitHub-flavoured markdown inside the stem.
- Capture the four options labelled (a)(b)(c)(d) -> keys A,B,C,D. Text only, drop the "(a)" marker.
- Skip cover pages, instruction pages, and blank pages -> {"questions": []}
- Do NOT include the correct answer (the paper does not print it).

Return ONLY JSON of this shape:
{"questions": [
  {"number": <int as printed>, "stem": "<verbatim question incl. statements/table>",
   "options": {"A": "<text>", "B": "<text>", "C": "<text>", "D": "<text>"}}
]}"""


def pdf_pages_to_images(pdf_path, dpi):
    import fitz  # pymupdf
    from PIL import Image
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        yield img


def load_model():
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    return model, processor


def run_page(model, processor, img):
    from qwen_vl_utils import process_vision_info
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": "Transcribe the MCQs on this page as JSON."}]},
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                       padding=True, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=2048, do_sample=False)
    trimmed = out[0][inputs.input_ids.shape[1]:]
    raw = processor.decode(trimmed, skip_special_tokens=True)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return []
    try:
        return (json.loads(m.group(0)) or {}).get("questions", []) or []
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--max-options", type=int, default=4)
    args = ap.parse_args()

    model, processor = load_model()
    by_number = {}
    for i, img in enumerate(pdf_pages_to_images(args.pdf, args.dpi), 1):
        for q in run_page(model, processor, img):
            try:
                n = int(q.get("number"))
            except (TypeError, ValueError):
                continue
            stem = (q.get("stem") or "").strip()
            opts = q.get("options") or {}
            if len(stem) < 15:
                continue
            if str(n) in by_number:            # keep first non-empty English version
                continue
            labels = "ABCD"[: args.max_options]
            by_number[str(n)] = {
                "number": n, "stem": stem,
                "raw_options": [f"({l.lower()}) {opts.get(l, '')}" for l in labels],
                "options": {l: str(opts.get(l, "")).strip() for l in labels},
            }
        print(f"  page {i}: total captured {len(by_number)}", flush=True)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    ordered = {k: by_number[k] for k in sorted(by_number, key=lambda x: int(x))}
    json.dump(ordered, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(f"WROTE {args.out}: {len(ordered)} questions")


if __name__ == "__main__":
    main()

# --- CLASS 10 / 12 (PCM + Commerce) NOTE ---------------------------------------------------
# CBSE board papers are NOT all MCQ. Sections A/B/C/D mix MCQ, 1-mark assertion-reason,
# short-answer, and long derivations. Two adjustments per board:
#   1. Relax the SYSTEM_PROMPT to also capture non-MCQ questions:
#      add a "qtype" field ("MCQ_single" | "assertion_reason" | "short_answer" | "long_answer")
#      and make "options" optional (empty {} for descriptive questions).
#   2. Physics/Chem/Maths questions often reference a FIGURE ("in the given circuit ...").
#      Add a boolean "needs_figure" the model sets when the question depends on a diagram it
#      cannot fully transcribe — those rows are stored with needs_figure=1 and are BLOCKED by
#      the serving gate until a real figure is attached (see the skill's serving section).
