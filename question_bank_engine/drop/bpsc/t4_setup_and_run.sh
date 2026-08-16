set -e
export HF_HOME=/mnt/hf TMPDIR=/mnt/tmp PIP_CACHE_DIR=/mnt/tmp/pipcache
mkdir -p /mnt/tmp/pipcache /mnt/qbank/out
echo "[$(date -u +%H:%M:%S)] venv+deps"
python3 -m venv /mnt/qbank/venv
/mnt/qbank/venv/bin/pip install -q --upgrade pip wheel
/mnt/qbank/venv/bin/pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu121
/mnt/qbank/venv/bin/pip install -q "transformers>=4.49.0" accelerate qwen-vl-utils pymupdf pillow bitsandbytes
echo "[$(date -u +%H:%M:%S)] SETUP_DONE"
for f in GS-13-12-24 GS-04-01-25; do
  echo "[$(date -u +%H:%M:%S)] extracting $f"
  /mnt/qbank/venv/bin/python /mnt/qbank/qwen_extract_bpsc.py --pdf /mnt/qbank/drop/bpsc/$f.pdf --out /mnt/qbank/out/$f.json --dpi 180
  echo "[$(date -u +%H:%M:%S)] PAPER_DONE $f"
done
echo "[$(date -u +%H:%M:%S)] ALL_DONE"
