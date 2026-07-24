# Diagram clean-redraw research (2026-07-24)

Goal: reproduce exam-figure diagrams as our OWN clean, watermark-free figures (the
recovered getmarks figures are internal-only — see the skill's diagram section).

## Findings (pilots)
- **General VLM (gpt-4o) → structured spec → render**: FAILS. Lossy extraction; the VLM
  verifier gives false-passes. `redraw_graphs.py` (matplotlib), `redraw_chem.py` (RDKit).
- **Specialist OSR (DECIMER) → SMILES → RDKit**: on a SINGLE SKELETAL structure, EXCELLENT
  (read a chiral centre + tritium + stereochemistry correctly). `decimer_osr_pilot.py`.
- **The real blocker = MCQ option panels** (4 candidate molecules in one image), which
  cut across every diagram type. A single-molecule OSR reads a panel as one C300 blob.
- **Segmentation fixes the panel problem**: `segment_osr_render.py` splits a panel into
  per-option crops (dilate + connected-components; tailored to exam panels, no Mask R-CNN
  dep hell), then DECIMER + RDKit per crop. Proven: alcohols panel → 4 clean option crops.
- **Remaining gap = depiction style.** DECIMER excels on SKELETAL line-drawings but is
  only ~50% on the CONDENSED notation Indian exams use (CH3-CH-CH2OH with explicit
  labels) — tert-butanol read perfectly, isobutanol misread on the same panel. This is a
  domain-shift problem; the fix is fine-tuning DECIMER on exam-style condensed structures
  (we have thousands of examples in the bank), not more pipeline.

## Environment (EC2 A10G)
DECIMER + DECIMER deps installed in `~/molscribe_pilot/decimer_env` (venv, TF-based).
MolScribe is NOT usable here (pins Python<=3.10; box has 3.12). Figures at
`~/molscribe_pilot/figs`. Run with the venv activated.
