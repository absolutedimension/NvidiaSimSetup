# Qwen2.5-VL Vision Extractor — Install Handoff (for Avinash's EC2)

> **Goal:** stand up the SAME vision-LLM extraction box we run in us-east-1, on Avinash's
> Mumbai EC2, so he can turn official exam PDFs into verbatim per-question JSON **in parallel**
> with Deepak's box. This handoff covers ONLY the GPU extraction stage (stage ② of the
> real-question pipeline). Storing/serving the questions happens later on the Gurukul serving VM
> — that is **not** part of this box's job (see §7).
>
> **Model:** `Qwen/Qwen2.5-VL-7B-Instruct` (fits the A10G 24 GB in bf16). It transcribes the
> printed question + options **verbatim** — it does not solve, paraphrase, or invent anything.
>
> Self-contained bundle: this file **+ `qwen_extract.py`** (in the same folder). SCP both to the box.

---

## 0. The box (Avinash — TrigunAI-Omniverse-Mumbai)

| Item | Value |
|---|---|
| Instance name | TrigunAI-Omniverse-Mumbai |
| Instance ID | `i-05d9104a0d7bf56be` |
| Region | ap-south-1 (Mumbai) |
| Type | g5.2xlarge — **NVIDIA A10G, 24 GB VRAM** (enough for the 7B model) |
| Public IP | changes on every stop/start — check the AWS console before SSH |
| Cost | **~$1/hr while Running — STOP it the moment extraction is done** |

SSH in (swap in the current public IP + Avinash's key path):
```bash
ssh -i <avinash_key.pem> ubuntu@<CURRENT_PUBLIC_IP>
```

---

## 1. Verify the GPU is visible (do this FIRST)

```bash
nvidia-smi
```
- **See the A10G + a driver version** → good, skip to §2.
- **`nvidia-smi: command not found`** → the box has no driver. Install one:
  ```bash
  sudo apt-get update && sudo apt-get install -y nvidia-driver-535
  sudo reboot            # reconnect after ~60s, re-run nvidia-smi
  ```
  (If it's an NVIDIA GPU Cloud VMI AMI like Deepak's box, the driver is already there.)

---

## 2. Disk + HF cache (the 7B model is ~16 GB of weights)

The root EBS can be small; g5 boxes have a big ephemeral NVMe. Point the HuggingFace cache at
the roomy disk so the download doesn't fill `/`:

```bash
# find the big disk:
df -h
# if there's an NVMe mounted (often /mnt or /opt/dlami/nvme), use it; else make a dir on the biggest mount:
export HF_HOME=/mnt/nvme/hf         # <-- adjust to the actual big mount on this box
mkdir -p "$HF_HOME"
```

> ⚠️ **NVMe is ephemeral — wiped on stop.** The model re-downloads after a stop/start unless
> HF_HOME is on a persistent (EBS) path. For an occasional-use box that's fine (10-min re-pull).
> Keep **source PDFs + output JSON on `~/` (EBS), never in `/tmp` or the NVMe** — those vanish on stop.

Put `export HF_HOME=...` in `~/.bashrc` so every shell has it.

---

## 3. Install the dependencies

```bash
sudo apt-get update && sudo apt-get install -y python3-pip
pip install --break-system-packages transformers accelerate qwen-vl-utils pymupdf pillow torch
```

- `transformers` must be recent enough to expose `Qwen2_5_VLForConditionalGeneration` (the script
  imports it directly). If that import fails, upgrade: `pip install --break-system-packages -U transformers`.
- `torch` should be a CUDA build (the g5 AMIs ship one; if `torch.cuda.is_available()` is False,
  reinstall from the PyTorch CUDA index).

Quick sanity check:
```bash
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
# -> CUDA: True
```

---

## 4. Drop in the extractor + pull the model

SCP `qwen_extract.py` (shipped with this handoff) to the box, e.g. `~/qwen_extract.py`.

First run downloads the model once (~16 GB → a few minutes on Mumbai), then loads it into VRAM.
The model loads **once** and streams pages — never relaunch per page.

---

## 5. Run it

Put official exam PDFs on the box under `~/drop/<exam>/` (question papers only for extraction —
the answer key is transcribed by hand later, on the serving VM).

**Single file:**
```bash
python3 ~/qwen_extract.py \
  --pdf ~/drop/cbse12phy/2025_PHY_SETA.pdf \
  --out ~/drop/cbse12phy/qwen/2025_PHY_SETA.json \
  --dpi 200
```

**Batch a folder:**
```bash
cd ~/drop/cbse12phy
mkdir -p qwen
for f in *_QP*.pdf *_SET*.pdf; do
  [ -e "$f" ] || continue
  python3 ~/qwen_extract.py --pdf "$f" --out "qwen/${f%.pdf}.json" --dpi 200
done
```

**For math-dense papers (Maths / Physics)** whose JSON overflows and truncates, raise the token budget:
```bash
python3 ~/qwen_extract.py --pdf <paper>.pdf --out qwen/<paper>.json --max-new-tokens 6144
```

Output = one JSON per PDF, keyed by question number:
```json
{ "1": {"number":1,"qtype":"MCQ_single","stem":"...","options":{"A":"..","B":"..","C":"..","D":".."},
        "marks":1,"needs_figure":false}, ... }
```

---

## 6. Verify a clean extraction

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); \
print('questions:', len(d)); \
import itertools; [print(k, '=>', v['stem'][:90]) for k,v in itertools.islice(d.items(),3)]" \
  ~/drop/cbse12phy/qwen/2025_PHY_SETA.json
```
Good signs: question count ≈ the paper's real count; stems read verbatim; math shows as `$...$`
LaTeX; numbered statements (1./2./3., Assertion/Reason) preserved in order.

**Then hand the `qwen/*.json` files back to Deepak** (or straight to the Gurukul serving VM) —
storing/keying/serving is stage ④–⑥ and does **not** run on this box.

---

## 7. What this box does NOT do (scope boundary)

This is the **extraction GPU box only**. It stops at "PDF → per-question JSON". The rest of the
pipeline lives on the **Gurukul serving VM** (`dk_trigun@20.219.2.53`, `~/question_bank_engine`):

- ③ **KEY** — the official answer key is transcribed by hand into `keys.json` (the trust anchor —
  never let a model "solve" for the key).
- ④ **STORE** — `store_real_questions.py` writes rows as `generated=0, verified=1`.
- ⑤ **CLEAN** — `clean_option_blocks.py` strips the duplicated option block from stems.
- ⑥ **SERVE** — `enable_pool_serving.py` lets the real rows serve from `/pool`.

So Avinash's deliverable is simply: **clean `qwen/*.json` files**, one per paper. Deepak's side
takes them from there.

---

## 8. Gotchas (hard-won — they WILL recur)

1. **Use Qwen2.5-VL, not gpt-4o.** General VLMs paraphrase multi-statement questions and drop the
   numbered statements. Non-negotiable — this is the whole reason for a vision box.
2. **Bilingual PDFs** repeat every question in Hindi. The prompt returns `{"questions":[]}` for
   non-English pages and the script keeps the first English version — expected, don't "fix" it.
3. **Option block duplicated inside the stem** (~64% of rows) is normal at this stage — it's
   cleaned later by stage ⑤ on the serving VM, not here.
4. **Figures (PCM):** the model flags `needs_figure:true` for diagram/circuit/graph questions.
   Those rows are held back downstream until a real figure is attached — never serve a
   figure-dependent question blind. (No action needed on this box; just don't be surprised by the flag.)
5. **`/tmp` and the NVMe are ephemeral** — wiped on stop. Keep PDFs + JSON on `~/` (EBS).
6. **STOP THE BOX** when done — it bills ~$1/hr in ap-south-1 just like us-east-1.

---

## 9. One-glance quickstart (copy-paste)

```bash
# 1. SSH in (current IP from console)
ssh -i <avinash_key.pem> ubuntu@<CURRENT_PUBLIC_IP>
# 2. GPU + cache
nvidia-smi
export HF_HOME=/mnt/nvme/hf && mkdir -p "$HF_HOME"
# 3. deps
sudo apt-get update && sudo apt-get install -y python3-pip
pip install --break-system-packages transformers accelerate qwen-vl-utils pymupdf pillow torch
# 4. (scp qwen_extract.py + PDFs to the box)  then:
mkdir -p ~/drop/exam/qwen
python3 ~/qwen_extract.py --pdf ~/drop/exam/paper.pdf --out ~/drop/exam/qwen/paper.json --dpi 200
# 5. STOP the instance when done (~$1/hr).
```

---

*Bundle: this file + `qwen_extract.py`. Source of truth: skill `exact-question-making-pipeline-from-pdf`
(stage ②). Serving side: `~/question_bank_engine` on the Gurukul VM.*
