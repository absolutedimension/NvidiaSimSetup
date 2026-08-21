---
name: trigunai-kids-education
description: >
  CONTROL TOWER for TrigunAI's entire KIDS EDUCATION product (Deepak's son, ICSE Grade 3, and
  the kids market). TWO halves sharing ONE curriculum + ONE question generator: (1) the KIDS
  VIDEO channel "Treasure Trackers" (YouTube @TrigunAI-KidsEducation) — cartoon Lego-style JJ 🐰 &
  Mikey 🐢 maths quiz videos = top-of-funnel; (2) the KIDS PRACTICE APP at
  kids-education.trigunai.com — the full Acharya assessment pipeline (signup, dashboard, Smart
  Practice, Report, tests + a voice quiz), re-skinned bright/playful for kids, running as an
  ISOLATED Azure Container App so it never touches the live acharya/Rohan demo. LOAD THIS FIRST for
  anything kids-education: the videos, the app, the landing/card, the Grade-3 question bank, the
  voice quiz, deploys, or continuing the curriculum work. ALSO owns the WORKSHEET + ADAPTIVE ASSESSMENT
  ENGINE (built 2026-08-02) — a science-backed generator COMMON to kids AND senior courses: worksheet
  archetypes, curriculum-driven generation (75-cell taxonomy), a concept×style×student-profile layer, and
  the assessment core (difficulty radicals, misconception-diagnostic distractors, BKT mastery + 85%
  adaptive controller). Triggers: "kids education", "kids app", "kids-education.trigunai.com", "Treasure
  Trackers", "JJ and Mikey", "grade 3 / class 3", "kids video", "kids quiz", "my son's app", "book images
  / curriculum scans", "kids landing card", "worksheet generator", "worksheet engine", "assessment engine",
  "adaptive assessment", "misconception distractors", "difficulty / mastery / 85% controller", "print
  worksheet", "asset pool / kids characters", "student profile / assessment style". Companions:
  trigunai-kids-quiz (the video engine detail), acharya-student-frontend + trigunai-assessment-backend-data
  (the pipeline this reuses), maintain-trigunai-system (LMS deploy).
---

# trigunai-kids-education — the Kids product control tower

**One sentence:** kids videos drive awareness → **kids-education.trigunai.com** is the practice app →
both run on the **same Grade-3 question generator** (`kids_quiz/gen_content.py`) and the **same Acharya
pipeline** (examgen + assess engine), just re-themed for children.

## ▶ NEXT TASKS (2026-08-03 — product LIVE at v46; KB engine live for GK+EVS G3 + MATHS GAP FIXED)
Full product **LIVE at `lms-kids:v46`** (all 5 subjects × grades 1-5 picker × boards, adaptive, alive art, print, brand landing,
2-action dashboard, Acharya chat, quality-critic). Build detail = **🎨 WORKSHEET PRODUCT** + **🖼️ ASSET/ENTITY-MAP** below.

**✅ MATHS COVERAGE GAP FIXED (v46).** Shapes/Fractions/Measurement/Division/Data no longer silently generate addition —
`worksheet_engine.py` has computed `g_division`/`g_shape`/`g_fraction`/`g_measure`(chapter-aware)/`g_data`, routed via `DIRECT_MATHS`
+ `chapter_concepts()` (matches ICSE clean names + CBSE playful NCERT titles). 0 logic errors / 3000+ items, reuses existing renderers.
Remainder: a real data-handling **pictograph renderer** (g_data is a contextual-count stopgap). Detail = memory [[project-kids-worksheet-allsubjects]] + handoff §4.

**⭐ THE KB+TEMPLATES ENGINE IS BUILT (2026-08-03) and LIVE for GK + EVS Grade 3 (v45).** See **🏗️ ENGINE STRATEGY** below.
The durable engine (`kids_quiz/kb_engine.py` + verified `kids_quiz/kb/<subject>_class<N>.json`) replaces the LLM pool for knowledge:
Opus authors a VERIFIED knowledge base (categories/groupings/relations/facts), the engine COMBINES facts into the 5 renderable
types → every question correct BY CONSTRUCTION. Proven: 1000 distinct, **0 degenerate, 0 factual/grammar errors, ~free, instant**
(vs ~10% error on the old gpt-4o-mini pool). Banks are drop-in — the app's `serve()` already prefers the pre-pooled bank, so NO
app-code change. Old LLM banks backed up to `content/bank/*.llm.bak`.
1. **SCALE the KB engine.** ✅✅ DONE: **ALL grades 1–5 × ALL knowledge subjects (GK/EVS/English/Hindi) on the clean engine (v50, CBSE+ICSE)**;
   Maths computed for all grades. 20 KBs total in `kids_quiz/kb/` (G3 hand-authored; grades 1/2/4/5 via the `author-grade-kbs` multi-agent WORKFLOW,
   32 agents, grade-distinct + verified). To ADD/deepen: edit the KB → `python3 kb_engine.py --kb <name> --n 1000 --board <B> --seed <s> --out content/bank/<board>_class<N>_<subj>.json` → copy into `lms/app/kidsengine/content/bank/` → deploy. Validate `python3 quality_critic.py --glob 'content/bank/*.json'` (degenerate=0). **Engine now `_validate`s templates + pairs + cloze `___`.** Remaining: Bihar grades 1/2/4/5 (deprioritized), maths pictograph renderer, per-chapter depth.
2. **RAG-VERIFY the knowledge facts (agreed direction, NOT yet built).** Decision: keep Opus authoring the KB, add a RAG pass that
   VERIFIES/flags each fact (not textbook-authored-from-scratch). Design = embed a reference corpus (textbook chunks or a trusted set) →
   per KB fact retrieve supporting passage → flag any fact without support for human review + optionally store a `source` snippet. Purpose:
   catch the rare Opus-recall error (e.g. the "national game of India" trap) and make facts defensible/authoritative. Build-time only, never in the serve path.
3. **Data-handling pictograph renderer** — `g_data` is a contextual-count stopgap; a real pictograph/bar-graph needs a new renderer in `worksheet.js`.
4. **Chapter-filter fidelity** (optional) — `serve()`/`_bank_items` matches when the picker chapter is a SUBSTRING of the item `chapter` tag; KB tags are thematic so many chapter picks fall back to the full (still-clean) pool.
5. **Never-repeat memory** (deferred) — per-child seen-question tracking.
6. **COMMIT to git** — v33→v46 code/templates/pools/assets/critic + `kb/` + `kb_engine.py` + the maths generators are UNCOMMITTED (only v26→v37 committed at `c11e8c7`).
*(DONE this session: authored GK + EVS Grade-3 KBs, built `kb_engine.py`, 4 clean banks, deployed v45; then FIXED the maths coverage gap — v46.)*

## 🏗️ ENGINE STRATEGY — KB + TEMPLATES (BUILT & LIVE for GK+EVS G3, 2026-08-03)
**► STATUS: BUILT. `kids_quiz/kb_engine.py` (the template engine) + `kids_quiz/kb/gk_class3.json` + `kids_quiz/kb/evs_class3.json`
(verified KBs). LIVE at v45 for GK + EVS Grade 3 (CBSE+ICSE). Full build/scale handoff = `kids_quiz/KB_TEMPLATE_ENGINE_HANDOFF.md`.**
**How it works:** the KB has `categories` (→ odd_one_out), `groupings` (→ sort_groups + true_false), `relations` (a→b pairs → match + true_false + cloze),
and `facts` (→ true_false True). `kb_engine.py` COMBINES them; a `_validate()` guard rejects any KB shape that could produce a wrong question, and every
"false"/distractor is PROVEN to belong to a different key. Emits the exact bank shape (`AC.enrich`ed) → drop into `content/bank/`. **Article agreement uses `{art}`**
(engine-computed A/An); templates must use `{art} {a}`/`{art} {item}` for any leading article. **To scale: author a verified KB, generate, copy to app, deploy** (see NEXT TASKS §1).
**The insight:** the bottleneck is FACT CORRECTNESS, not volume. **Maths generates infinite correct questions with NO LLM
because facts are COMPUTED, not guessed.** Extend that to knowledge: **separate FACTS from FORM.**
- **FACTS** = a small VERIFIED knowledge base per curriculum subtopic (cow→shed, lotus=India's national flower, big↔small…).
- **FORM** = question templates (odd-one-out / match / true-false / cloze / sort) that COMBINE facts into questions.
- Verify the FACTS once → every templated question is correct BY CONSTRUCTION. Unlimited combinations, ~free, ~100% clean.

**Use a frontier model (Opus) for the ONE-TIME high-value work, NOT per-question brute generation:** (1) build the verified KB
per subtopic, (2) author the templates, (3) handle creative types (comprehension/word-problems) with grounding. Then a cheap
template engine emits millions of clean questions. ~100× cheaper AND higher quality than per-question LLM.

**WHY we're pivoting (findings from the LLM-pool attempt):**
- gpt-4o-**mini** pool = ~10% factual/degenerate errors (e.g. cat→"Air Animals", empty "True or False?").
- **LLM auto-critic is a DEAD END** — ~50% false positives, CONSISTENT even on 2 votes (gpt-4o keeps flagging CORRECT items like
  "national flower is Rose→False", "bones help us move→True"). Do NOT hard-drop on it.
- gpt-4o **generation** is much cleaner than mini (sampled 10/10 correct) — but per-question LLM is still costly + not truly unlimited.
- Only the **deterministic critic** (`kids_quiz/quality_critic.py` `degenerate()`) is reliable — keep it for well-formedness; drop the LLM auto-drop.
**Conclusion:** KB+templates is the durable engine. The current 1000-item LLM pools stay LIVE as a stopgap; the KB engine replaces them per-subject as it's proven.
Assets built this session (reusable): `kids_quiz/quality_critic.py` (degenerate filter = keep; llm_verdicts = unreliable), `fill_knowledge_pool.py` (LLM-pool driver, WS_CRITIC hook), `reclean_bank.py`. The Maths engine (`worksheet_engine.py` COMPUTED path) is the reference template pattern to copy.

## Key facts
| Thing | Value |
|---|---|
| **Kids app (LIVE)** | `https://kids-education.trigunai.com/` — Azure Container App **`kids`** (RG `trigunai-video-creator`, env `trigunai-env`), image `trigunaicr.azurecr.io/lms-kids:vN` (**currently v53**, 2026-08-05 — **ALL grades 1–5 × ALL subjects on the clean engine (CBSE+ICSE)**: GK/EVS/English/Hindi = KB+templates (20 KBs in `kids_quiz/kb/`), Maths = computed; **KIDS TEACHER↔STUDENT FLOW (v51)**: teacher creates grade/board batch → join link → assigns Practice/Fixed worksheets → students Solve/Print + are grade-locked → teacher sees completions + weak topics (`kids_teacher_signup/home.html`, host-gated); **v52 student dashboard decluttered** (kids: no pricing/goal/mock, Class chip, Assigned-first); **v53 PRODUCTION DESIGN PASS = unified lighter OCEAN-BLUE theme** (MAIN `#3AA6E8`/DEEP `#1E6FB5`; recolored all kids surfaces, senior untouched) + TrigunAI mark + favicon everywhere + voice fix (TTS strips emoji). Detail in `acharya-student-frontend` skill + [[project-kids-worksheet-allsubjects]]. Bihar knowledge = Class-3 only). **HF dataset scan → `kids_quiz/HF_DATASETS_PRIMARY_SCAN.md` (no ready primary bank on HF; OBQA/ARC = fact-enrichment feed only).** **Isolated from the live `lms` app.** Deploy = build from a /tmp snapshot then `az containerapp update -n kids` (recipe below); bump the version each deploy. |
| Kids app FQDN | `kids.redflower-9a33748c.eastus.azurecontainerapps.io` (custom domain bound, HTTPS via managed cert) |
| **YouTube channel** | **TrigunAI-KidsEducation**, ID `UC9QWXw-M6W4eqo1dmbHYbLQ` (Brand acct under deepak@trigunai.com). 60 Grade-3 Maths videos uploaded UNLISTED. Token = `youtube_series/token_kids.json` (also on Gurukul). |
| **Video engine** | `kids_quiz/make_kids_quiz_video.py` (Lego JJ/Mikey, gems, kind reveals) + `gen_content.py` (18 Maths topics) + `batch_all.py` / `run_day_kids.py`. Detail = skill **trigunai-kids-quiz**. Render on EC2 `i-047ebf759f2386e71` (34.192.145.204). |
| **Question bank** | exam `"ICSE Class 3"`, subject `"Mathematics"` — **540 generated Qs (gen_content → qbank), 18 chapters, difficulty 1-2**, LIVE in the Gurukul `qbank.sqlite` (`gurukul.trigunai.com/examgen`). Served via `/pool?exam=ICSE Class 3&subject=Mathematics&difficulty=1-2`. |
| **Repos/paths** | app code = `lms/` (NvidiaSimSetup); kids engine + curriculum + generator = `kids_quiz/`; standalone landing = `kids_web/`; plan = `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md` + `KIDS_ASSESSMENT_PLAN.md`. |

## 🎨 WORKSHEET PRODUCT — LIVE (v26→v37, the current main build)
Memory ground-truth: **[[project-kids-worksheet-allsubjects]]**. The live kids worksheet at
`kids-education.trigunai.com/exam-prep/worksheet`. Everything below is DEPLOYED.

**Flow / all subjects.** Acharya chat ("Make me a worksheet") + the worksheet page cover **all 5 subjects**
(Maths/EVS/English/GK/Hindi), curriculum-driven. Chat = a `kids_subject → kids_chapters → kids_count → kids_go`
node chain in `main.py` `_chat_step` (chips `ksubj:`/`kchap:`/`kgo`/`kn:`), navigates to
`/exam-prep/worksheet?subject=&chapter=&n=`. Onboarding goal picker is **kids-only** on the kids host.

**Serving brain = `lms/app/kids_worksheet.py`** (`serve` / `complete` / `picker` / `_bank_items`). Engine packaged
in **`lms/app/kidsengine/`** (source of truth stays `kids_quiz/` — **RE-COPY** `worksheet_engine.py` + `content/bank/`
into `kidsengine/` after any change). **CRITICAL:** `serve()` `random.sample()`s from a difficulty BAND (was the
strict n-closest → same 8 every time). Maths = computed live (~unlimited); knowledge = served from the pre-pooled bank.

**Question pools (offline banks in `kidsengine/content/bank/`):**
- Maths = computed/unlimited (not from a bank; `COUNT_ASSETS` = 20 countable props).
- EVS/English/GK/Hindi = **1000 each per board** (CBSE+ICSE = **8000 items, all distinct**). Hindi is **pure Devanagari**.
- Built with `kids_quiz/fill_knowledge_pool.py` (round-robin over curriculum chapters + BROAD Class-3 topics so
  thin subjects reach 1000; signature dedup; `hindi_pure()` gate; ThreadPool; resumable). Needs EC2 litellm via
  `ssh -fN -L 4000:localhost:4000 ubuntu@34.192.145.204` + `WS_LLM_TEMP`. `worksheet_engine.llm_knowledge` reads
  `WS_LLM_TEMP` env + forces Hindi for the Hindi subject.

**UX (all in `templates/kids_worksheet.html` + `static/kids/worksheet.js`):** canvas backdrop / **no card box** (content
on background); on CORRECT → success chime (`playCheer()`, Web Audio) + lion dances (`celebrate()`) + voice "Correct!"
(NO answer repeat); on WRONG → voice **explains the correct answer** (match/sort state the pairs) + coral hint, and
advance **waits for the audio to actually finish** (`tts` uses real `_audio.duration`, never cuts early); **Back/Next**
buttons + per-index results; chat asks question count. Hindi content → **`hi-IN-SwaraNeural`** voice; per-item Hindi
instruction/hint localization so nothing reads mixed-language. Print (`worksheet_print.js`/`print.html`) outputs the
REAL generated sheet via `localStorage`. Smart Practice + Report "Practice worksheet" target the weak topic.

## 🖼️ ASSET / ENTITY-MAP SYSTEM (how art attaches to questions — v37)
**Runtime resolver = `static/kids/assets.js` (`KidsAssets`).** Loads `asset_manifest.json`, resolves a token →
generated art if `status:ready`, else emoji/text. A question's payload carries either an explicit `{asset,emoji}`
(maths `count_write`) or plain text; `worksheet.js mkVisual()`/`node()` do the lookup at render time.

**Entity→asset map (data-driven, SCALABLE — this is the "alive worksheets" path):**
- Each manifest asset has a **`words:[EN + Hindi]`** synonym list (51 assets). `assets.js` builds a `wordIndex` at
  load + `idFor(token)` resolves an id / emoji / **EN-or-HI word** → asset id; `node()` uses it.
- `worksheet.js` **`entityLabel(text)`** shows the **picture ABOVE the word** (keeps the label so reading/vocab still
  works) and is wired into **tap options + match + sort** renderers. So `गाय`/`cow` → cow art in odd-one-out/match/sort.
- Deliberately NOT applied to cloze/true-false statements (replacing words breaks the reading/grammar exercise).

**Asset pool = 52 ready** (`static/kids/assets/*.png` + manifest). Generate more with
`kids_quiz/asset_pool/gen_assets.py --batch to_generate.json` (gpt-image on EC2 litellm; writes PNGs + flips manifest
`ready`). **gen_assets rewrites the whole manifest at the end** → inject `words` AFTER it finishes, or it clobbers them.
**To scale to "unlimited alive": pool new assets + add their `words` to the manifest — NO code change** (wordIndex auto-indexes).

**Deploy history (worksheet product):** v20-25 base flow · v26 all-subjects+print+goals · v27-30 UX+Hindi voice ·
v31-32 match-answer+smart-practice+no-card · v33 celebration+robust-voice · v34 correct-sound · v35 variety-fix+300-pool ·
v36 1000-pool · v37 asset entity-map + 32 new assets · v38 all-subjects-LIVE-in-picker · v39 brand-gold landing + logo + dashboard NEET-removed ·
v40 print-art + 2-action dashboard · v41 printable-only button · v42 grade+count picker + all-topics · v43 board picker + Acharya-chat-back ·
v44 quality-critic (deterministic clean; LLM-critic found unreliable) + gpt-4o-gen finding → decided KB+templates pivot ·
v45 KB+TEMPLATES engine BUILT & LIVE — GK + EVS Grade 3 served from `kb_engine.py` + verified `kb/*.json` (correct-by-construction, 0 errors, replaces LLM pool) ·
v46 MATHS GAP FIXED — Shapes/Fractions/Measurement/Division/Data now generate the right question type (computed generators + `DIRECT_MATHS`; was silently addition) ·
v47 EVS KB enriched with 10 OpenBookQA-mined+verified facts + HF dataset scan doc ·
v48 English Grade 3 KB LIVE (opposites/synonyms/plurals/gender/tenses/articles/nouns-verbs/rhymes + grammar facts); grouping FALSE-explain now shows the corrected true statement ·
v49 Hindi Grade 3 KB LIVE (विलोम/पर्यायवाची/वचन/लिंग/संज्ञा-क्रिया + Devanagari `strings` block via `_S` helper) — ALL G3 subjects now on the clean engine; 0 Latin leaks by construction ·
**v50 GRADES 1–5 COMPLETE — 16 grade KBs (grades 1,2,4,5 × 4 knowledge subjects) authored via the `author-grade-kbs` multi-agent workflow (32 agents), 30 board banks, all 0-degenerate; `_validate` hardened (templates/pairs/cloze)**.

## 🧩 THE WORKSHEET + ASSESSMENT ENGINE (built 2026-08-02 — the big upgrade)

The kids app grew from an MCQ quiz into a full **worksheet + adaptive assessment engine**, science-backed
and **COMMON to kids AND senior courses** (MCQ is just one format dial). Full design + roadmap = the
"Science of Assessment → Universal Engine" artifact. Layers, concept → item → student:

**A · Curriculum (skeleton)** — `kids_quiz/curriculum/` = **75/75 authentic cells** (3 boards × 5 classes × 5
subjects), machine-readable JSON + `index.json` master. Handoff: `CURRICULUM_AUTHENTIC_HANDOFF.md`. (40 verified,
35 draft — Bihar + GK.)

**B · Worksheet Grammar (delivery formats)** — `kids_quiz/WORKSHEET_GRAMMAR.md` = **~30 archetypes**
(trace/count/match/fill/arith/compare/sort/order/cloze/true-false…). Each = a machine `type` + JSON payload.

**C · Generators**
- `worksheet_engine.py` — **CURRICULUM-DRIVEN**: any board/class/subject/chapter → worksheet. Maths = computed
  (class-scaled ranges); knowledge (EVS/English/GK/Hindi) = **LLM** (litellm, hardened w/ validation+retry)
  grounded on the chapter. STYLE-DRIVEN + student-profile-weighted. Enriches every item via the common engine.
- `gen_worksheet.py` — simpler Grade-3 Maths (8 archetypes).
- `pool_worksheets.py` — the pooling DRIVER (priority-ordered, resumable, skips low-conf). **180 Maths items
  already pooled** → `kids_quiz/content/bank/`. Handoff: `WORKSHEET_POOLING_HANDOFF.md` (knowledge pooling = the avatar/curriculum session's job).

**D · Style system (concept × style × student-type)** — `assessment_styles.json` (4 dials: Bloom · Webb DOK ·
CPA · context; 9 styles) + `student_profiles.json` (kids_1_2 / kids_3_5 / board / jee_neet / upsc weightings).
Doc: `ASSESSMENT_STYLE_SYSTEM.md`. One concept rendered across styles, weighted per learner. `--profile` overrides.

**E · The COMMON assessment engine (the science core — kids + seniors)**
- `assessment_core.py` (**rung 1**) — `enrich(item)` adds **difficulty** (radicals → `b`, band 1-4),
  **misconception-tagged distractors** (wrong answer = a diagnosis), **tiered hints** (process feedback).
  `to_mcq(item)` → a diagnostic MCQ (this is the upgrade the **senior MCQ courses** need — one import).
- `adaptive_engine.py` (**rungs 2-3**) — per-skill **BKT mastery + Elo ability** + the **85% controller** +
  mastery gate + `pick_item(candidates, target_b)`. Closed loop proven: measure → target_b → span candidates → pick → hold ~85%.
- Doc: `ASSESSMENT_ENGINE.md`.

**F · Delivery — 4 renderers in `lms/app/static/kids/`, DEPLOYED (v19)**
- `worksheet.js` / `worksheet.css` — INPUT widgets for every archetype (tap/drag/pad/trace/**voice**).
  `KidsWorksheet.render(mount,item,{onDone})`. Demo → `/static/kids/worksheet_demo.html`.
- `conceptviz.js` / `conceptviz.css` + `worksheet_viz.js` — the **"see it"** concept animation (count-ups,
  compare, number lines). `ConceptViz.render` / `KidsWorksheetViz.show`. (Copy of the module in `kids_quiz_live.html` — keep in sync.)
- `worksheet_print.js` / `worksheet_print.css` + `print.html` — the **PRINT / pencil-&-paper** arm.
  `KidsWorksheetPrint.render`. → `/static/kids/print.html`. (Deepak printed one — works.)
- `alive_worksheet.html` — composes input + concept-anim + **avatar**. Avatar seam = `KIDS_ALIVE_CONTRACT.md`
  (`KidsAvatar.speak(text)` via postMessage; the avatar session owns lip-sync). → `/static/kids/alive_worksheet.html`.

**G · The asset pool** — `asset_manifest.json` + `assets.js` (`KidsAssets`, runtime resolver, emoji fallback) +
`asset_pool.py` (brain: status/scan/plan/request/suggest) + `gen_assets.py` (offline generator). **24 ready** (4
characters Ellie/Rio/Milo/Bruno + 18 props + 2 context-chars nova_owl/lion). Props/mascots via **gpt-image on the
EC2 litellm** (tunnel `ssh -N -L 4000:localhost:4000 ubuntu@34.192.145.204`); rigged characters via the
AnimatedDrawings factory (see `kids-animation-story-creator`). Doc: `POOL_DESIGN.md`. Worksheets reference art by
`{"asset":"cow"}`, emoji fallback until generated.

### HOW TO EXTEND (maintenance — do it from any session)
| Want to… | Do this |
|---|---|
| Add a worksheet archetype | Add to `WORKSHEET_GRAMMAR.md` + a `RENDER.<type>` in `worksheet.js` (+ a `PRINT.<type>` in `worksheet_print.js`) |
| Add a subject/board/class curriculum | Drop a cell JSON in `kids_quiz/curriculum/`; the engine reads it automatically |
| Generate a worksheet for a cell | `python3 kids_quiz/worksheet_engine.py --board X --class N --subject S [--chapter C] [--profile P]` (knowledge needs `LITELLM_URL` tunnel) |
| Pool many cells | `python3 kids_quiz/pool_worksheets.py --maths-only` (offline) or `--n 10` (LLM, needs endpoint) |
| Add a **misconception** (diagnosis) | Add `{id,name,fn,why}` to `MISCONCEPTIONS[concept]` in `assessment_core.py` |
| Add a **difficulty radical** | Add a branch to `difficulty()` in `assessment_core.py` |
| Add a **student profile** (e.g. NEET) | Add a weighting to `student_profiles.json` — no code change |
| Add art (prop / character) | `python3 kids_quiz/asset_pool.py request <id>` → `gen_assets.py` (EC2 litellm tunnel up) |
| **Wire adaptivity into serving** | feed answers → `adaptive_engine.update()` → `next_target_b()` → generate + `pick_item()` (needs `main.py` hook + student-state storage) |
| Upgrade **senior MCQ courses** | in `question_bank_engine/`: `import assessment_core; mcq = to_mcq(item)` — diagnostic distractors |
| Deploy any of `lms/app/static/kids/*` | the kids-app deploy recipe below (bump the version; **currently v44**) |
| Pool more art (props/characters) | `kids_quiz/asset_pool/gen_assets.py --batch to_generate.json` (EC2 litellm tunnel) → then add each asset's `words:[EN+HI]` to `asset_manifest.json` → deploy. NO code change. |
| Fill knowledge question pools | `kids_quiz/fill_knowledge_pool.py --target N` (EC2 litellm tunnel, `WS_LLM_TEMP`) → RE-COPY banks into `kidsengine/content/bank/` → deploy |

### STATUS (deployed `lms-kids:v44`) — NOTE: the engine below is now FULLY SERVED LIVE (packaged in `lms/app/kidsengine/`); the "not served yet" note is obsolete.
- **LIVE:** worksheet component, print, concept-viz, **52-asset pool + entity→asset art**, 8000-item knowledge banks, all wired into serving.
- **Source-of-truth generators (in `kids_quiz/`, re-copied into `kidsengine/` for the app):** `worksheet_engine.py`, `gen_worksheet.py`,
  `pool_worksheets.py`, `assessment_core.py`, `adaptive_engine.py`, the style JSONs, the 180-item bank.
- **CROSS-SESSION (the two remaining seams):** (1) the **`main.py` serving hook** — route students to worksheets +
  inject the adaptive loop (shared collision point — coordinate); (2) **senior qbank** integration (one import).

### Deploy history (kids app): v14 worksheet component · v17 asset pool + 18 props · v18 characters + print · v19 concept-viz + alive-worksheet.

### Sibling sessions (don't collide):
- **Avatar/UI + curriculum session** `local_e74842aa` ("Grade 3 ICSE quiz video plan") — owns `kid.glb` avatar,
  the 75-cell curriculum, and the knowledge-subject pooling. Handoffs sent: `KIDS_ALIVE_CONTRACT.md`, `WORKSHEET_POOLING_HANDOFF.md`.
- **This (worksheet-engine) session** — owns the engine + components + asset pool.
- **Collision point = `main.py`** (the kids assess-page inject where `kids_voice.css/js` load) — ping before editing.

## 🚀 PRODUCTION INTEGRATION — the adaptive worksheet flow is LIVE (2026-08-02, v20→v25)

The worksheet + adaptive engine is now **wired into the live app end-to-end** (login → worksheet → report),
not just a local generator. **This is the current active build.**

**App files (the wiring):**
- `lms/app/kidsengine/` — the engine PACKAGED into the app (worksheet_engine, assessment_core, adaptive_engine,
  gen_worksheet + `assessment_styles.json` + `student_profiles.json` + `curriculum/` (76 cells) + `content/bank`).
  **Source of truth stays `kids_quiz/`** — when you change a generator there, **RE-COPY into `kidsengine/`** or it
  won't take effect in the app. `kids_worksheet.py` adds `kidsengine/` to `sys.path` then `import worksheet_engine`.
- `lms/app/kids_worksheet.py` — the serving BRAIN: `picker(board,cls)` · `serve(db,student,board,cls,subject,chapter,n)`
  (adaptive: load `KidsSkillState` → `target_b` → generate candidates → `pick_item` near target_b) ·
  `complete(db,student,skill,results,subject)` (updates BKT+Elo mastery **AND** `ConceptStat` so the existing Report keeps working).
- `lms/app/models.py` → **`KidsSkillState`** table (per student+skill: p_mastery, theta, ema, target_b, n, misconceptions). Auto-creates on boot.
- **Routes in `main.py`:** `GET /exam-prep/worksheet` (page) · `GET /api/kids/worksheet` (adaptive serve) ·
  `POST /api/kids/worksheet/complete` · `GET /api/kids/curriculum` (picker). Plus **redirects on the kids host**:
  `/exam-prep/smart` → `/exam-prep/worksheet`; `/exam-prep/test` with a **custom topic** (`q`/`sel`/`src=examgen`) →
  `/exam-prep/worksheet` (so **Chat-with-Acharya + custom tests generate worksheets**, not the old MCQ). Plain exam launch keeps `kids_quiz_live.html`.
- **The page** `lms/app/templates/kids_worksheet.html` — kids UI, **Nova-owl guide** + bubbles, **gem progress + "Question N of M"**,
  the **concept teaching-hint** (NO answer spoiler), voice, **◀ Topic / 📄 Full sheet** nav, **subject + chapter picker** (any
  subject→topic), results screen (mastery %, print), 2 big animal buddies behind. Loads `worksheet.js` + `assets.js` + `conceptviz.css`.
- **Dashboard** `exam_prep_dashboard.html` — host-gated `{% if kids %}` KIDS SKIN (colourful palette, tinted cards, pink/purple
  accents) + a **"📝 Practice Worksheets" hero**. Acharya dashboard 100% untouched (dashboard route passes `kids=`).

**Scores → Report (wired):** `complete()` writes `ConceptStat` (concept = readable name e.g. "Addition"), so the mastery ring,
**Focus areas**, and **Reports & Improvement** all reflect worksheet results — same path as the MCQ flow.

**The `worksheet.js` component** now uses the **blue "hint-panel" look** (blue cells, 3D bottom shadow, light-blue gradient, pop-in)
matching `conceptviz.css` — a `worksheet.css` restyle (affects worksheet/print/demo).

**Deploy history:** v20 engine+routes+KidsSkillState · v21 dashboard skin+hero · v22 teaching-hint+smart→worksheet+nav+progress ·
v23 blue component+2 big buddies · v24 blank-end fix+concept labels+dashboard colour · **v25 custom/chat→worksheet + subject picker**.

**GOTCHAS (each cost real time):**
- The app **can't boot locally** (no fastapi/uvicorn in the Mac Python) → test the serving brain via a DB script
  (`from app import kids_worksheet`; import models BEFORE `create_all`), render templates via Jinja, then DEPLOY
  **rollback-safe** (check revision `healthState`; roll to prev tag if unhealthy).
- **Knowledge subjects (EVS/English/Hindi) generate via the LLM at request-time** → the app needs EC2 litellm reachable, OR
  serve from the pre-pooled `content/bank`. **Maths is instant** (computed). Empty EVS worksheet = endpoint, not the flow.
- Removing the `#viz` element left a stale `$('viz').classList` in `finish()` → `null` crash → blank results. Watch stale refs.

**OWNERSHIP:** this build **OWNS `main.py`**; the avatar/curriculum session `local_e74842aa` PAUSED its `main.py`/`exam_prep.html`
edits. **Hand `main.py` back** when the build settles.

**REMAINING (next session):**
1. **Kids skin on the other screens** (onboarding, report, subject-detail) — same `{% if kids %}` pattern.
2. **Knowledge-subject serving** — wire the app to call litellm OR serve the pooled bank (avatar session runs `pool_worksheets.py`).
3. **Difficulty-dial** — a difficulty-parameterised generator for tighter 85% targeting (Science-map rung 1).
4. **Senior courses** — `import assessment_core; to_mcq(item)` in `question_bank_engine/` for diagnostic MCQs.
5. Full **human E2E** (login-gated — Deepak tests) + polish from his feedback.

## The web app (kids-education.trigunai.com)
> ⚠️ **SEPARATE DATABASE since 2026-08-19.** The kids app no longer shares Acharya's `lms` database.
> It runs on **`kidsdb`** on the same Postgres server (`trigunai-lms-pg`, RG `trigunai-video-creator`),
> wired via the container-app secret **`dburlkids`** → env `DATABASE_URL=secretref:dburlkids`. The `lms`
> (Acharya) app still uses secret `dburl` → database `lms` and was NOT touched. Kids students, teachers,
> assignments, mastery and goals are now completely isolated from senior ones — a kids signup can never
> appear in Acharya's admin/pulse counts and the same email can hold separate accounts in each product.
> `kidsdb` was created empty (2026-08-19, Deepak's call); the app self-bootstrapped all 32 tables + course
> seed via `seed.run()` on first boot. **Pre-split kids accounts were NOT migrated** — they still sit in
> the old `lms` DB and must sign up again on the kids site.

Runs the **full lms code** (image `lms-kids`, same examgen + secrets as acharya, but its OWN DB — see above) but host-gated:
- **Root** `/` (host `kids-education.trigunai.com`) → kids landing (`lms/app/static/kids/index.html`),
  else the normal app. Handler: `KIDS_HOSTS` check in `lms/app/main.py` `root()`.
- **`/exam-prep`** → kids-only picker (`KIDS_EXAMS` in main.py, host-gated in the exam_prep route):
  **Grade 3 · Maths = LIVE**, EVS/English/GK/Grade 4/5 = SOON. Bright kids theme (`{% if kids %}` block
  in `exam_prep.html`: body.kids CSS-var overrides + floating emojis + playful copy + `.kids-exams` tiles).
- **Signup/dashboard/Smart Practice/Report/tests** = the SAME student pipeline (see acharya-student-frontend).
- **Voice quiz** at `/static/kids/voice_quiz.html` (edge-tts child voice `en-US-AnaNeural`, auto-driven,
  SPEAK-or-TAP, Voice ON/OFF toggle).
- **acharya landing** (`lms/app/templates/acharya.html`) has a 3rd **"For Kids"** card → the kids site.

## examgen wiring (lms/app/examgen.py)
`RAG_SUBJECTS["class3-maths"]` (exam "ICSE Class 3"), `GOALS["class3"]`,
`DIFFICULTY_LADDER["ICSE Class 3"]={easy 1,mix 1-2,hard 2}`; `main.py` `EXAMS` has `class3`→`class3-maths`.

## Deploy recipes
**Kids app (safe — never touches live):** edit `lms/`, then build from a /tmp snapshot (git-HEAD gotcha)
and deploy to the `kids` app ONLY:
```
cd lms; rm -rf /tmp/lmskids && mkdir /tmp/lmskids && cp Dockerfile requirements.txt /tmp/lmskids/ && cp -R app /tmp/lmskids/app
cd /tmp/lmskids && az acr build --registry trigunaicr --image lms-kids:vNEXT --file Dockerfile .
az containerapp update -n kids -g trigunai-video-creator --image trigunaicr.azurecr.io/lms-kids:vNEXT
```
**acharya landing card = LIVE deploy** (`lms` app, image `lms:vN`) — only when safe to touch live.
**Question pool → Gurukul:** generate rows locally (`kids_quiz/gen_content.py` → qbank `Question` rows,
generated=1/verified=1), scp to Gurukul, upsert via `qbank.storage.Store` — **NO qbank-api restart**
(SQLite WAL live-reads → doesn't disrupt live examgen). Back up `qbank.sqlite` first.

## ⛔ Pending user actions
- **Google sign-in on kids domain:** add `https://kids-education.trigunai.com` to the Google OAuth client
  `984605652262-...h2rs896en...` "Authorized JavaScript origins". Email signup works without it.
- **Made-for-Kids channel setting** in YouTube Studio (per-video flag already set, so compliant).

## Gotchas (each cost real time)
- **Isolation is the whole point:** kids app = a SEPARATE container app; NEVER redeploy `lms` for kids work.
- **git-HEAD build gotcha:** `az acr build` from inside the repo ships HEAD, not your edits → build from /tmp.
- **`--set-env-vars $UNQUOTED` word-splits** + array `secret set` mangles values → set env/secrets via a
  Python subprocess with DISCRETE args (see project memory).
- **Ingress port:** the kids app must be `targetPort 8000` (lms/gunicorn), not 80.
- **/pool default band is 3-4** → kids Qs (difficulty 1-2) are excluded unless the difficulty is passed; the
  frontend sends the right band via the ladder.
- **Apple emoji strike = 160** (not 137) in the video engine.
- **LMS changes are UNCOMMITTED** — commit to `main` or a parallel HEAD-rebuild reverts the kids card + code.
- **Azure managed cert** can sit "Pending" 25-45 min — wait, don't thrash-delete.

## What's LIVE vs NEXT (2026-08-03)
**LIVE (app `lms-kids:v37`):** kids-education.trigunai.com — full **all-subject adaptive worksheet product** wired
end-to-end (chat + worksheet page + serving brain + adaptive engine, all in the app); **1000 questions each** for
EVS/English/GK/Hindi (CBSE+ICSE = 8000, Hindi pure Devanagari) + unlimited computed Maths; the whole UX (canvas/no-card,
celebration+chime, voice-explains-wrong, Hindi voice, Back/Next, print-real-sheet); **52-asset pool + entity→asset art**
(EN+HI words → pictures in odd-one-out/match/sort/counting). Plus landing, voice quiz, 60 YT videos, acharya "For Kids" card.
**NEXT:** see "▶ NEXT TASKS" above — chiefly **never-repeat memory** (deferred) + committing later versions to git.
(The old "engine BUILT-but-LOCAL / not wired" note is obsolete — it's all serving live since v20+.)

Full blow-by-blow history: memory **[[project-kids-worksheet-allsubjects]]** (worksheet product) + **[[project-kids-quiz-video]]** (videos). Curriculum: `kids_quiz/curriculum/` (75 cells)
+ baseline `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md`. Engine docs: `kids_quiz/{WORKSHEET_GRAMMAR,ASSESSMENT_STYLE_SYSTEM,
ASSESSMENT_ENGINE,POOL_DESIGN}.md`.
