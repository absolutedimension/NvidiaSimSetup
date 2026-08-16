CBSE grounding corpus — ABANDONED (not viable). Source: HF ayush7/CBSE_ALL_DATA_all_sub_all_class_v0.4 (no license).

Empirical finding (2026-08-03): NOT a usable grounding source for primary.
- Class 1 slice = 598 rows but only ENGLISH + MATHEMATICS, and just 27 UNIQUE textbook chunks (heavy duplication;
  the rows are many auto-generated META-questions over the same few lesson-plan chunks). NO primary EVS/GK/science.
- Full Class 2-5 pull is blocked: dataset = 7376 parquet shards; /statistics=501; /filter=504; classes are STRING-sorted
  (Class1, Class10-12, then Class2-9) so primary is scattered deep after Class12.
VERDICT: skip this dataset. If we build RAG-verify (Phase 2), ground against a REAL textbook (NCERT EVS PDF the curriculum
cells already cite: https://ncert.nic.in/textbook/pdf/ceap1ps.pdf), not this auto-generated meta-Q&A dump.
Kept: cbse_class1_chunks.jsonl (27 chunks) as a sample only.
