# SRB Past-Paper Sourcing Guide (SSC · Railway · Banking · BPSC · Daroga)

> **Purpose:** how to MANUALLY collect the last ~10 years of REAL question papers + official
> answer keys for the govt-job exams, so the **exact-question pipeline** (`skill:
> exact-question-making-pipeline-from-pdf`, Qwen2.5-VL → key-match) can turn them into REAL,
> verbatim, answer-keyed questions in the bank (like the 517 real UPSC PYQs). Reusable for
> every future govt-job client, not just One Step Education.

## The rule that keeps it legal (READ FIRST)
The pipeline needs, **per paper**: (1) the **question paper PDF** + (2) the **official answer
key** (a candidate *response sheet* contains both together).

- ✅ **Download ONLY from the official exam-body government portal** (the `.gov.in` / `.nic.in`
  sites below). Government-published papers are the legitimate source — this is exactly how the
  UPSC bank was built.
- ⚠️ **Do NOT scrape or redistribute coaching-site compilations** (Adda247, Testbook, Kiran PDFs,
  etc.). You may keep a PYQ *book* as an **internal cross-check only** — never serve it verbatim.
  For any exam where official papers don't exist, our served output is **GENERATED + validated**
  (copyright-clean), not their content.

---

## Per-exam sourcing (verified portals, Aug 2026)

> **✅ CONFIRMED + STARTED 2026-08-12:** BPSC Prelims GS papers download directly (no login) from
> `bpsc.bihar.gov.in/question-booklets/` (3-level cascade: CCE → edition → Preliminary). Editions
> **66th–71st** are listed. Real URL pattern (date-stamped, not edition-numbered):
> `https://bpsc.bihar.gov.in/wp-content/uploads/BPSC_content/QuestionBooklets/GENERAL-STUDIES-<DD-MM-YY>.pdf`
> The **70th** (both sittings) is downloaded to Gurukul `~/drop/bpsc/70th/` (GS-04-01-25.pdf 9.4M,
> GS-13-12-24.pdf 9.5M, valid PDFs). **GAP = answer keys:** BPSC archives the PAPERS cleanly but
> posts the official ANSWER KEYS separately (notices / objection-window), NOT on the booklets page —
> so keys must be sourced per edition (the pipeline's trust anchor). Remaining editions' paper URLs
> require clicking each edition in the browser cascade (date-stamped, unguessable). Daroga = still to do.

### 1. BPSC — Prelims + Mains GS + TRE (Teacher) → **bpsc.bihar.gov.in**  ⭐ DO THIS FIRST
The RICHEST official source, and Bihar-specific — it covers the exact GS/GK gap One Step wants.
- Go to **bpsc.bihar.gov.in** → look for "Previous Question Papers" / "Answer Key" / the exam's
  notice page. BPSC posts the **Prelims GS question paper** and a separate **official answer key**
  after each cycle.
- Collect: **70th, 69th, 68th, 67th, 66th, 65th, 64th, 63rd…** Prelims GS papers + their keys.
- One BPSC Prelims GS paper already covers: **Polity, Geography, History, Economics, General
  Science, Static GK, and (Bihar) Current Affairs** — i.e. almost the entire GS column of the note.
- **BPSC TRE** (Teacher Recruitment) papers are also here, subject-wise — grab them for the "TRE"
  line in the note.
- Google helper: `BPSC 69th prelims question paper pdf site:bpsc.bihar.gov.in` · `BPSC answer key 2023 bpsc.bihar.gov.in`

### 2. Bihar Daroga / Sub-Inspector → **bpssc.bihar.gov.in** (SI) + **csbc.bih.nic.in** (Constable)
Official, Bihar-specific — the "Daroga" line in the note. Papers + keys available ~2015→2024.
- **bpssc.bihar.gov.in** → "Question Paper / Answer Key" for the SI (Daroga) Prelims & Mains.
- **csbc.bih.nic.in** → Bihar Police Constable papers + keys.

### 3. SSC CGL / CHSL → **ssc.gov.in**  (official, but recent years are login-gated)
After each exam SSC releases: **provisional answer key → final answer key + candidate response
sheet** (the response sheet = the actual question paper + correct key + your marked answers).
- **Recent years (CBT):** the response sheet is behind a **candidate login** (registration no +
  password). Practical route: download from **your own / Rohan's candidate logins** for exams you
  sat; that gives a real, official paper+key per shift.
- **Older years:** SSC's pre-CBT and early-CBT Tier-1 papers were released as PDFs — check the
  ssc.gov.in archive / notices.
- **Years you can't get officially:** use a PYQ book as INTERNAL reference only + rely on our
  **generators** (Reasoning ✅ live, Quant ✅ live) for the Maths + Reasoning sections. English +
  GK from BPSC/other official keys.
- Google helper: `SSC CGL tier 1 question paper pdf site:ssc.gov.in`

### 4. Railway — RRB NTPC / Group D / ALP → **rrb.digialm.com** + regional RRB sites
Same model as SSC: during each exam's **objection window**, RRB publishes the **question paper +
response sheet + provisional answer key**, downloadable by **login (reg no + DOB)**.
- Download your/Rohan's response sheets where available; otherwise generate (Reasoning + Quant) +
  take GS/GK from the BPSC official keys.
- Regional boards: rrbcdg.gov.in, rrbald.gov.in, etc. (all link through rrb.digialm.com).

### 5. Banking — IBPS / SBI → **NO official papers are ever released**
IBPS/SBI publish only scorecards, never the paper. So **Banking = 100% GENERATION** — which we've
already built (compute-the-answer Quant + Reasoning). No sourcing needed here; a Kiran/Arihant PYQ
book is optional internal pattern-reference only.

---

## The manual workflow (what YOU do, then hand to me)
1. Make a folder per exam+year:  `question_bank_engine/drop/<EXAM>/<YEAR>/`
   (e.g. `drop/BPSC/2023/`, `drop/DAROGA/2022/`, `drop/SSC_CGL/2019/`).
2. Into each, save **two files**: `paper.pdf` (the question paper) and `key.pdf` (the official
   answer key). For subject-wise papers (BPSC TRE), name them `paper_maths.pdf`, `key_maths.pdf`, etc.
3. Scans are fine — the pipeline reads them with vision (Qwen2.5-VL). Prefer the clearest scan.
4. When a batch is ready, zip the `drop/` folder (or just tell me the paths) → **I run the
   exact-question pipeline**: extract each question verbatim → match the official key → store as
   REAL verified questions (`generated=0, verified=1`), servable directly to students.

## Priority order (max coverage, fastest, most legal)
1. **BPSC Prelims GS ×10 yrs** — covers Polity/Geo/History/Econ/Science/Static-GK/CA + Bihar + it's fully official. Biggest single win.
2. **Bihar Daroga (BPSSC) ×10 yrs** — official, Bihar, One Step teaches it.
3. **BPSC TRE** — the "TRE" line, subject-wise official papers.
4. **SSC CGL Tier-1** — whatever you can pull officially (Maths/Reasoning/English/GK).
5. **RRB** — where obtainable by login.
6. **Banking → skip sourcing**, use the generators.

## What we already have (don't re-source these)
- **Reasoning** — LIVE generator, unlimited, all SRB exams (`qbank/reasoninggen.py`).
- **Quantitative Aptitude / Maths** — LIVE generator, unlimited (`qbank/quantgen.py`).
- These cover **two of the four Tier-1 sections** already — sourcing PYQs mainly fills GS / GK /
  Current Affairs / English + gives us REAL past questions for authenticity.

## ⚙️ GPU box for extraction (CHANGED 2026-08-12)
The **EC2 A10G was DELETED** (billing). Vision OCR now runs on the **Azure T4** `dk-gpu-ubuntu`
(Standard_NC8as_T4_v3, **16 GB VRAM**, 8 vCPU, Malaysia West, RG `dk-gpu-machine_group`,
sub `7db80eaf-…`, IP 20.17.162.80, admin user `dk-gpu-ubuntu`).
- **16 GB is tight for Qwen2.5-VL-7B fp16** → run **4-bit (bitsandbytes)** or use **Qwen2.5-VL-3B**.
- **Driver-mismatch lesson** (from the sibling music T4): if CUDA/cuDNN NOT_INITIALIZED → `sudo reboot` first.
- **BPSC papers are SCANNED image PDFs (0 text layer)** → vision OCR is required; no pdftotext shortcut.
- **ACCESS (RESOLVED 2026-08-13 by the parallel session):** `ssh -i ~/.ssh/gurukul_key dk-gpu-ubuntu@20.17.162.80`
  (gurukul_key was authorized on the box; IP is STATIC). GPU driver fixed (535.309.01) + Secure Boot off.
- **SHARED BOX — coordinate:** this T4 is ALSO the music/voice box for another workstream. Before a long
  extraction: (1) **disk is ~94% full (~11 GB free)** — Qwen2.5-VL-7B weights (~16 GB) won't fit → use the
  **3B model** or free space (their `voice_agent`/`acestep`/`audio_pipeline` ≈ 32 GB); (2) a daily 03:30 UTC
  auto-stop runs (automation `dk-gpu-scheduler`, schedule `stopT4`) — pause it for long jobs; (3) don't
  disrupt their running GPU work. `az vm start -g dk-gpu-machine_group -n dk-gpu-ubuntu --subscription 7db80eaf-a061-45cd-b01e-09c815acbe95` if off.

## ✅ 70th GS EXTRACTED (2026-08-13) + ANSWER-KEY STEP (the trust anchor)
- **300 real questions extracted** (both 70th Prelims GS sittings, 150 each) → `question_bank_engine/drop/bpsc/70th_extracted/{GS-13-12-24,GS-04-01-25}.json` + T4 `~/bpsc_out`.
- **Opus cross-check solved** for GS-13-12-24: `solved_GS-13-12-24.json` (109 high-confidence · 38 flagged · 4 figure). BPSC GS is ~25% current-affairs/Bihar-local → my solve is a CROSS-CHECK, not the source of truth.
- **DECISION (Deepak, 2026-08-13): use the OFFICIAL BPSC answer key as truth.** GS-04-01-25 NOT yet Opus-solved (paused — official key covers it).
- **Official 70th final answer key:** on **bpsc.bih.nic.in** (released Jan 2025; mirrored ForumIAS / freejobalert). **4 SETS E/F/G/H × 150 Q, some deleted.**
  **KEY-MATCH STEPS:** (1) find which SET our extracted booklet is (printed on the cover page — our extract skipped page 1; re-open the PDF cover to read the set letter); (2) transcribe THAT set's answers by Q-number → `keys.json {TAG:{qnum:"A"}}`; (3) mark deleted/bonus Qs as `"X"` (store step skips them); (4) cross-check vs `solved_GS-13-12-24.json` — mismatches on my HIGH-confidence answers flag a possible key mis-transcription (this caught 2 wrong UPSC keys before). Then `store_real_questions.py` (generated=0, verified=1) → clean → enable_pool_serving.

## ✅ 70th LIVE + 66–71 STAGED (SESSION 2026-08-13, JOB A+B)

**JOB A — 70th GS is LIVE (289 real Qs).** Sourced the OFFICIAL BPSC **final** answer keys
(ForumIAS-hosted BPSC notice PDFs, dated 17-01-25 = post-objection final): 13-12-24 sets E/F/G/H
+ 04-01-25 (re-exam) sets I/J/K/L → saved `drop/bpsc/70th_extracted/keys_src/key_{13-12-24,04-01-25}.pdf`.
Our booklets = **Set E** (13-12-24) and **Set I** (04-01-25). Transcribed both → `keys.json`+`tagmap.json`;
deletions (E: 58/101/114/117 · I: 5/13/79/91) cross-confirmed by the keys' own "Reason" tables; Set-I
Q132 corrected B→D per the key note. Cross-check vs `solved_GS-13-12-24.json`: 107 high-conf agree, 2
high-conf mismatches (Q81=D, Q134=C) both verified faithful to the official PDF (Opus wrong). Stored via
`store_real_questions.py` (exam **BPSC**, subject **General Studies**, id-prefix **bpsc**) → recovered 13
Set-I inline-option rows (`recover_bpsc.py`) → `clean_option_blocks.py` → `enable_pool_serving.py --prefix BPSC`
(also added BPSC to `skip_chapter`+`skip_difficulty` in `storage.py`). **289 rows, all verified; 285 servable
(4 figure rows held by the guard).** Live: `curl ".../examgen/pool?exam=BPSC&subject=General+Studies&count=3"`.
**Remaining:** frontend agent (`acharya-student-frontend`) must wire BPSC into LMS `EXAMS`/`RAG_SUBJECTS`.

**JOB B — 66th/67th/67th-reexam/68th/69th/71st GS papers DOWNLOADED + extraction run.**
- **Download mechanism (reusable):** `bpsc.bihar.gov.in/question-booklets` is a WP `question-booklets`
  plugin. Crawl via admin-ajax `POST action=get_children&parent_id=N&nonce=8484a26a88` then
  `action=get_question_booklets_pdfs&item_id=N&nonce=…` → PDF in the **`file_url`** field. Prelims-GS
  nodes: 66th=63, 67th=60, 67th-reexam=61, 68th=27, 69th=24, 70th=20, 71st=97. Scripts:
  `drop/bpsc/70th_extracted/qb{crawl,pdfs,dl}.py`. Papers on Gurukul `~/drop/bpsc/<edition>/`.
- **⚠️ CRITICAL — option count differs by era:** **66th/67th/68th = FIVE options (A–E)**;
  **69th/70th/71st = FOUR options (A–D)**. Booklet series of our copies: 66=A,67=A,68=A,69=A,71=E.
  The 4-opt papers fit the existing pipeline/UI; the 5-opt ones do NOT (extractor, `store_real_questions.py`
  `labels="ABCD"`, validator, and the student UI all assume A–D). A 5-opt extractor
  `qwen_extract_bpsc5.py` (prompt+schema+parse → A–E) was written for 66/67/67re/68.
- **Extraction (T4 20.17.162.80, `/mnt/qbank/run_v2.sh` → `~/bpsc_out/GS_<ed>.json`):** 69th+71st with the
  4-opt extractor (live candidates); 66/67/67re/68 with the 5-opt extractor (staged). 69th is born-digital
  (has a text layer) but run through vision anyway for consistency.
- **KEYS status (trust anchor — do NOT serve unverified):** 70th ✅done. **71st Set-E PROVISIONAL** captured
  (`keys_src/key_71st_SetE_PROVISIONAL.json`, all 150; the FINAL 31-10-25 deleted 5 Qs — get it before serving).
  **69th** needs the **Set-A FINAL** key (28-10-23) — `bpsc.bih.nic.in` is geo-blocked even from Gurukul;
  mirrors only had Set-D/Set-B. 66/67/68 keys not yet sourced.
- **Daroga (BPSSC):** `bpssc.bihar.gov.in` has NO clean official paper/key archive (only Advts/Notices) →
  legit route = candidate **response sheets** (login-gated, needs Rohan). **Deferred.**

**NEXT (to take 69th+71st live):** (1) get 69th Set-A final + 71st Set-E final keys; (2) `store_real_questions.py`
--exam BPSC (year 2023/2025) → recover/clean → already pool-enabled. **For 66/67/68:** add A–E support to
store+validator+student UI first, then key (5-opt) + store. Extracted JSONs land in `drop/bpsc/70th_extracted/`.

_Portals verified Aug 2026: bpsc.bihar.gov.in · bpssc.bihar.gov.in · csbc.bih.nic.in · ssc.gov.in
· rrb.digialm.com. Feeds `skill: exact-question-making-pipeline-from-pdf` → the question bank._
