---
name: kids-quiz-viz
description: >
  The per-question CONCEPT-ANIMATION engine for the kids quiz — a lightweight,
  data-driven visual that reads each MCQ and animates its concept in the empty
  space (tiles sorting, place-value columns lighting up, count-ups, number lines,
  reveal-the-sign). In-browser, zero-GPU, scales per question TYPE (one detector
  covers every instance forever). Load this to add/adjust question-type visuals in
  the kids Smart-Practice quiz. Distinct from the WORKSHEET component (input widgets
  for non-MCQ) — see the coordination note.
---

# kids-quiz-viz

Animate each quiz question's **concept** for kids, in the space below the options.
Not per-question GPU renders (thousands of Qs) — **one tiny in-browser detector per
question TYPE**, parameterized by the question's own numbers. Instant, mobile-perfect,
zero GPU, covers all present + future instances of that type.

## Where it lives
- **`lms/app/templates/kids_quiz_live.html`** (the kids `/exam-prep/test` page, served
  to `KIDS_HOSTS`). Contains:
  - The `#viz` panel: `<div class="vizwrap hidden" id="viz"></div>` after `.opts`.
  - The `window.ConceptViz` module (a `<script>` before the main quiz IIFE).
  - The call in `askQ`: `try{if(window.ConceptViz)ConceptViz.render(id('viz'),q);}catch(e){}`
    and a clear in `finish()`.
  - CSS: `.vizwrap/.viz-cap/.viz-row/.vcell(.op/.dim/.hit/.ans)/.viz-stage/.vtile/.viz-result`.
- **Standalone test harness: `kids_web/viz_test.html`** — every type with a button. ALWAYS
  iterate here first (serve `python3 -m http.server 8799` in `kids_web/`, screenshot), then
  port the module into the template. Keep the two modules identical.

## The render contract
`ConceptViz.render(box, q)` where `q = {q|stem, options, answer, correct, topic}` (from
`/api/kids/quiz`). It walks `DETECTORS[]`; the first detector that returns `true` owns the
panel; if none match it adds `.hidden` (graceful — no breakage). Toggle visibility via the
`.hidden` class (it is `!important`), NOT `style.display`.

## Detectors shipped (Grade-3 qbank = 6 chapters, all covered)
placeValue (place/face value → highlight column) · succPred (successor/predecessor → number
line ±1) · compareSign (fill the sign → `< > =`) · orderFirst (arrange asc/desc → sort +
highlight first) · sequence (skip-count / pattern → reveal next) · formNumber (sliding
tiles → sorted number) · expandedForm ("Write the number: 4000+700+20+6" → count-up) ·
estimateRound (estimate by rounding to nearest 10) · missingBox ("A + ___ = B") · numberName
(uses `q.correct`) · arithmetic (`+ − × ÷`, money ₹, count-up) · wordProblem (add/subtract).

Order matters: specific detectors BEFORE the generic `arithmetic` (which matches any
`n OP n =`). e.g. `expandedForm`/`missingBox`/`estimateRound` must precede `arithmetic`.

## Add a new question type (~30 min)
1. Write `function myType(box,q,s){ ... return true/false; }` using the helpers:
   `cell(txt,cls)`, `cap(box,html)`, `result(box,html)`, `countUp(node,to,ms)`, `nums(s)`,
   and cell classes `op/dim/hit/ans`. Match against `s` (the stem); compute the answer from
   the stem (or fall back to `q.correct`). Return `false` fast if it's not your type.
2. Add it to `DETECTORS[]` in the right position (before `arithmetic` if it contains `=`).
3. Add a sample to `kids_web/viz_test.html` `SAMPLES`, verify visually.
4. Port the module into `kids_quiz_live.html` (keep both copies identical).
5. Deploy (below).

To find real stems to match, read the generators: **`kids_quiz/gen_qbank_g3.py`** (the quiz
pool source — NOT `gen_content.py`, which is video-only). Regex gotcha: parse digits from
AFTER `using/from/with`, and use `\b\d\b` for single digits so "3-digit"/"number" don't
pollute the match.

## Deploy (kids app ONLY — never `lms`/Acharya)
```
SNAP=/tmp/lms_kids_build; rm -rf $SNAP; mkdir -p $SNAP
cp lms/Dockerfile lms/requirements.txt $SNAP/; cp -R lms/app $SNAP/app
az acr build -r trigunaicr -t lms-kids:vN $SNAP           # fresh tag N — see collision note
az containerapp update -n kids -g trigunai-video-creator --image trigunaicr.azurecr.io/lms-kids:vN
```
`az acr build` snapshots the WORKING TREE (git-HEAD is ignored) → it captures ALL uncommitted
kids edits, including other agents'. **Tag-collision gotcha:** ACR tags are mutable and
`az acr build` + `containerapp update` from two sessions on the SAME tag race. Always bump to
a fresh, unused tag and confirm the active revision after: `az containerapp revision list -n
kids -g trigunai-video-creator --query "[?properties.active]" -o table`.

## Coordination with the WORKSHEET component (different layer — don't confuse)
- **kids-quiz-viz (this)** = a read-only concept ANIMATION overlay for MCQ questions, in
  `kids_quiz_live.html`. Classes `.viz-*` / `.vcell`.
- **worksheet component** (worksheet agent) = INPUT widgets for non-MCQ item types (trace,
  match, sort, number-pad, voice-answer): `static/kids/worksheet.{js,css}`, global
  `KidsWorksheet.render(...)`, classes `.ws-*`, demo `worksheet_demo.html`. Do NOT edit,
  rename `.ws-*`, or fork it.
- **Shared collision point = `main.py`** (~kids assess injection, where `kids_voice.css/js`
  is added). Both worksheet-wiring and any viz-related injection would live here. Coordinate
  (ping the other agent / via Deepak) before editing `main.py`. Today ConceptViz needs NO
  `main.py` change (it's inside the template); worksheets still need theirs.

## Limits / next
- Covers the 6 live qbank chapters. Types with no detector hide gracefully.
- Not yet: character-per-topic reactions (a relevant animal reacting) — separate layer,
  reuses the AnimatedDrawings character clips (see `project-kids-quiz-video` memory).

## Related
- Control tower: `trigunai-kids-education` · quiz page + flow: `acharya-student-frontend`
- Qbank stems: `trigunai-assessment-backend-data` / `kids_quiz/gen_qbank_g3.py`
- Character animation (story/reactions): `kids-animation-story-creator`
- Deploy safety: `maintain-trigunai-system`
