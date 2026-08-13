# HANDOFF — SRB / BPSC question-bank continuation (for a parallel session)

> **Read this + `SRB_PYQ_SOURCING_GUIDE.md` (same folder).** Load skills
> `exact-question-making-pipeline-from-pdf` and `trigunai-assessment-backend-data` — they own the
> pipeline this executes. Goal: build the SSC/Railway/Banking/BPSC ("SRB") question bank for the
> **One Step Education, Patna** pilot.

## ✅ STATUS after session 2026-08-13 (JOB A done + JOB B in flight)
- **Reasoning + Quant generators LIVE** (unlimited, compute-the-answer) for the whole SRB family.
- **JOB A DONE — 70th GS is LIVE.** 289 real BPSC 70th-Prelims GS questions serve from the live bank
  (`exam="BPSC"`, subject `"General Studies"`), all keyed to the OFFICIAL final answer key. Details below.
- **JOB B IN FLIGHT.** 66/67/67-reexam/68/69/71 GS papers downloaded; extraction running on the T4;
  keys + 5-option handling scoped (below). Daroga = no official archive (deferred).

## JOB A — ✅ COMPLETE (do NOT redo)
Our booklets: **GS-13-12-24 = Set E** (13-12-24 exam), **GS-04-01-25 = Set I** (04-01-25 RE-EXAM, a
separate paper). Official **final** keys sourced from ForumIAS-hosted BPSC notice PDFs (post-objection,
17-01-25) → `drop/bpsc/70th_extracted/keys_src/key_{13-12-24,04-01-25}.pdf`. Transcribed Set E + Set I →
`keys.json` + `tagmap.json`. Deletions (E: 58/101/114/117 · I: 5/13/79/91) cross-confirmed by the keys'
Reason tables; Set-I Q132 corrected B→D. Cross-check vs `solved_GS-13-12-24.json`: 107 high-conf agree, 2
mismatches (Q81=D, Q134=C) verified faithful to the official PDF. Stored (`store_real_questions.py`
`--exam BPSC --id-prefix bpsc`) → recovered 13 mangled Set-I rows (`recover_bpsc.py`) → `clean_option_blocks.py`
→ `enable_pool_serving.py --prefix BPSC` (+ added BPSC to `skip_chapter`/`skip_difficulty` in `storage.py`).
**289 rows all verified; 285 servable (4 figure rows held).** DB backup `backups/qbank.sqlite.pre_bpsc70_*`.
**✅ LMS WIRING DONE (2026-08-13, lms:v135):** BPSC is now student-live at `acharya.trigunai.com/exam-prep`
— `RAG_SUBJECTS bpsc-gs` (exam="BPSC", subject="General Studies") + GOALS `bpsc` + DIFFICULTY_LADDER "BPSC"
+ EXAMS/STUDENT_EXAMS `bpsc`=available. Verified: picker renders "BPSC · available" + `/pool` serves real
keyed Qs. (Same deploy also wired SSC CGL — generated Reasoning+Quant. lms changes UNCOMMITTED.)

## JOB B — papers DOWNLOADED, extraction RUNNING, keys pending
- **Downloaded (Gurukul `~/drop/bpsc/<ed>/`):** 66th, 67th, 67th-reexam, 68th, 69th, 71st Prelims GS.
  The date-stamped URL guess FAILS for old editions; use the WP `question-booklets` AJAX cascade:
  `POST admin-ajax.php action=get_children&parent_id=N&nonce=8484a26a88`, then
  `action=get_question_booklets_pdfs&item_id=N` → PDF in field **`file_url`**. Prelims-GS nodes:
  66=63, 67=60, 67-reexam=61, 68=27, 69=24, 70=20, 71=97. Scripts `drop/bpsc/70th_extracted/qb{crawl,pdfs,dl}.py`.
- **⚠️ 66th/67th/68th are FIVE-option (A–E); 69th/70th/71st are FOUR-option (A–D).** Our series:
  66=A,67=A,68=A,69=A,71=E. 5-opt papers do NOT fit the extractor/`store_real_questions.py`(labels="ABCD")/
  validator/student-UI → new `qwen_extract_bpsc5.py` (A–E) written for 66/67/67re/68; serving them needs
  A–E support added to store+validator+frontend FIRST.
- **Extraction DONE (all 6)** → repo `drop/bpsc/editions_extracted/GS_<ed>.json` + T4 `~/bpsc_out/`.
  Counts (verbatim, verified option-count correct): **69th 147** (4-opt, 126 full+21 inline-recoverable),
  **71st 150** (4-opt, 131 full), **66th 148** (5-opt, all E captured), **67th 149** (5-opt, 146 w/E),
  **67th-reexam 150** (5-opt, 144 w/E), **68th 149** (5-opt, 133 w/E). Rows with <full options are
  recoverable via `recover_bpsc.py` (extend the label loop to A–E for the 5-opt papers).
- **Keys (trust anchor — do NOT serve unverified):** 70th ✅. **71st Set-E PROVISIONAL** transcribed
  (`keys_src/key_71st_SetE_PROVISIONAL.json`; FINAL 31-10-25 deleted 5 Qs — get final before serving).
  **69th Set-A FINAL** still needed (`bpsc.bih.nic.in` geo-blocked even from Gurukul; mirrors had Set-D/B only).
  66/67/68 keys not sourced.
- **NEXT to go live:** get 69th Set-A + 71st Set-E FINAL keys → `store_real_questions.py --exam BPSC`
  (year 2023/2025) → recover/clean (pool already enabled). Then 66/67/68 after A–E support.

### Daroga (BPSSC) — deferred
`bpssc.bihar.gov.in` has NO clean official paper/key archive (only Advts/Notices). Legit route =
candidate **response sheets** (login-gated → needs Rohan's login), or skip and use generators. Deferred.

## COORDINATES
| Thing | Value |
|---|---|
| **T4 GPU box** (extraction) | `ssh -i ~/.ssh/gurukul_key dk-gpu-ubuntu@20.17.162.80` (IP STATIC). NC8as T4 v3, 16 GB. |
| ⚠️ T4 `/mnt` is EPHEMERAL | Wiped on the **nightly 03:30 UTC auto-stop**. Put outputs on `~/bpsc_out` (persistent home) + pull to repo. `/mnt` remounts root-owned → `sudo mkdir -p /mnt/qbank /mnt/hf /mnt/tmp && sudo chown -R dk-gpu-ubuntu:dk-gpu-ubuntu /mnt/qbank /mnt/hf /mnt/tmp`. |
| T4 env recipe (fragile — pin!) | fresh venv on /mnt; `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121` (UNPINNED → 2.3.1+cu121, cuda True); `pip freeze | grep -E '^(torch\|torchvision)==' > constraints.txt`; then `pip install -c constraints.txt "transformers==4.49.0" "accelerate>=0.26.0" qwen-vl-utils pymupdf pillow "bitsandbytes>=0.43.2"`. **Don't pin torch==2.5.1 (its cudnn dep was pulled from the index).** Model = Qwen2.5-VL-7B 4-bit; HF_HOME=/mnt/hf. |
| Extractor | `question_bank_engine/qwen_extract_bpsc.py` (repo) → run `python qwen_extract_bpsc.py --pdf X.pdf --out Y.json --dpi 180`. Skips Hindi pages, outputs verbatim JSON. |
| **Gurukul** (live bank + serving) | `ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53`, `~/question_bank_engine`, store = `data/qbank.sqlite`, API systemd `qbank-api` → `https://gurukul.trigunai.com/examgen`. **Back up the DB before any bulk store.** |
| Live bank size | ~145k verified. Exams present: CBSE10/12, NEET, JEE, ICSE3, UPSC, Banking-Quant. Reasoning+Quant generators serve SRB now. |

## GUARDRAILS
- **Don't restart/deploy Gurukul during active student use** (real students). Back up the DB first.
- **Deallocate the T4 when idle** to save cost: `az vm deallocate -g dk-gpu-machine_group -n dk-gpu-ubuntu --subscription 7db80eaf-a061-45cd-b01e-09c815acbe95`.
- Serving-truth = OFFICIAL keys for real questions; generators for practice. Keep the two postures separate.
- The T4 is SHARED with a music/voice workstream — don't disrupt their processes; disk is ~94% full on root (use /mnt).

_Master ref: `SRB_PYQ_SOURCING_GUIDE.md`. Customer spec: `teacher_gtm/ONE_STEP_EDUCATION_PATNA.md`._
