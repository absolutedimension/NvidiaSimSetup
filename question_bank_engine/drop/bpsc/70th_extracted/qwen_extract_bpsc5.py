#!/usr/bin/env python3
"""qwen_extract_bpsc.py — BPSC Prelims GS vision extractor for the T4 (16GB), 4-bit Qwen2.5-VL-7B.

Adapted from the exact-question pipeline's qwen_extract.py:
  * load_model() uses 4-bit (bitsandbytes) so the 7B fits the T4's ~14.5GB free VRAM;
  * AutoProcessor gets a max_pixels cap to bound vision-token count (VRAM + speed);
  * BPSC-tuned prompt: every question is a 4-option MCQ; skip Hindi pages; verbatim, no solving.
Output schema per PDF: { "<num>": {number,qtype,stem,raw_options,options{A..D},marks,needs_figure} }
"""
import argparse, io, json, os, re

MODEL_ID = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
MAX_PIXELS = int(os.environ.get("QWEN_MAX_PIXELS", str(1800 * 28 * 28)))  # ~1.4M px cap

SYSTEM_PROMPT = r"""You are a precise exam-paper transcriber. You are shown ONE page image of an
official BPSC (Bihar Public Service Commission) Preliminary General Studies question paper.
Transcribe every complete question on the page VERBATIM — do not paraphrase, translate, solve,
or add anything.

BPSC Prelims questions here are ALL multiple-choice with exactly 5 options labelled (A)(B)(C)(D)(E)
(sometimes (1)(2)(3)(4)(5)). Capture each as qtype "MCQ_single" with 5 options.

Rules:
- The paper is BILINGUAL. If the visible question text is in HINDI (Devanagari script), return
  exactly {"questions": []} — transcribe ONLY the English version of each question.
- Transcribe the stem and all 5 options EXACTLY as printed. Options: drop the "(A)" label, keep
  the text. Keep any numbered statements (1.,2.,3.) or List-I/List-II match items in order.
- Render a match/pairing table as GitHub-flavoured markdown inside the stem.
- Render mathematics in LaTeX ($...$).
- Set "needs_figure": true only if the question depends on a printed map/figure/diagram you cannot
  transcribe as text. Else false. (Most BPSC GS questions are text-only.)
- Use the EXACT printed question number ("Q.1"->1, "37."->37). Transcribe EVERY numbered question
  visible. Do NOT invent, renumber, or solve. Do NOT include a correct answer (not printed).
- Skip cover/instruction/blank pages -> {"questions": []}.

Return ONLY JSON:
{"questions": [
  {"number": <int>, "qtype": "MCQ_single",
   "stem": "<verbatim stem incl. statements/table>",
   "options": {"A": "<text>", "B": "...", "C": "...", "D": "...", "E": "..."},
   "marks": <int or 0>, "needs_figure": <true|false>}
]}"""


def pdf_pages_to_images(pdf_path, dpi):
    import fitz
    from PIL import Image
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        yield Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def load_model():
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                             bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID, quantization_config=bnb, device_map="auto", torch_dtype=torch.float16)
    processor = AutoProcessor.from_pretrained(MODEL_ID, max_pixels=MAX_PIXELS)
    return model, processor


def _sanitize_latex_json(txt):
    def repl(m):
        s = m.group(0)
        if s == "\\\\":
            return s
        c = s[1]
        if c in '"/nrtu':
            return s
        return "\\\\" + c
    return re.sub(r"\\\\|\\.", repl, txt, flags=re.S)


def parse_questions(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    txt = _sanitize_latex_json(m.group(0) if m else raw)
    try:
        qs = (json.loads(txt) or {}).get("questions")
        if qs is not None:
            return qs
    except Exception:
        pass
    i = txt.find("[")
    if i < 0:
        return []
    dec, out, j, n = json.JSONDecoder(), [], i + 1, len(txt)
    while j < n:
        while j < n and txt[j] in " \n\r\t,":
            j += 1
        if j >= n or txt[j] != "{":
            break
        try:
            obj, j = dec.raw_decode(txt, j)
            out.append(obj)
        except Exception:
            break
    return out


def run_page(model, processor, img, max_new_tokens=3072):
    from qwen_vl_utils import process_vision_info
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": "Transcribe ALL English questions on this page as JSON."}]},
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                       padding=True, return_tensors="pt").to(model.device)
    import torch
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    trimmed = out[0][inputs.input_ids.shape[1]:]
    raw = processor.decode(trimmed, skip_special_tokens=True)
    return parse_questions(raw) or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--max-new-tokens", type=int, default=3072)
    ap.add_argument("--limit-pages", type=int, default=0, help="stop after N pages (0=all) for a test run")
    args = ap.parse_args()

    model, processor = load_model()
    by_number = {}
    for i, img in enumerate(pdf_pages_to_images(args.pdf, args.dpi), 1):
        for q in run_page(model, processor, img, max_new_tokens=args.max_new_tokens):
            try:
                n = int(q.get("number"))
            except (TypeError, ValueError):
                continue
            stem = (q.get("stem") or "").strip()
            if len(stem) < 15 or str(n) in by_number:
                continue
            opts = q.get("options") or {}
            labels = [l for l in "ABCDE" if str(opts.get(l, "")).strip()]
            by_number[str(n)] = {
                "number": n, "qtype": q.get("qtype") or "MCQ_single", "stem": stem,
                "raw_options": [f"({l.lower()}) {opts.get(l, '')}" for l in labels],
                "options": {l: str(opts.get(l, "")).strip() for l in labels},
                "marks": int(q.get("marks") or 0),
                "needs_figure": bool(q.get("needs_figure")),
            }
        print(f"  page {i}: total captured {len(by_number)}", flush=True)
        if args.limit_pages and i >= args.limit_pages:
            break

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    ordered = {k: by_number[k] for k in sorted(by_number, key=lambda x: int(x))}
    json.dump(ordered, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"WROTE {args.out}: {len(ordered)} questions")


if __name__ == "__main__":
    main()
