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
  voice quiz, deploys, or continuing the curriculum work. Triggers: "kids education", "kids app",
  "kids-education.trigunai.com", "Treasure Trackers", "JJ and Mikey", "grade 3 / class 3", "kids
  video", "kids quiz", "my son's app", "book images / curriculum scans", "kids landing card".
  Companions: trigunai-kids-quiz (the video engine detail), acharya-student-frontend +
  trigunai-assessment-backend-data (the pipeline this reuses), maintain-trigunai-system (LMS deploy).
---

# trigunai-kids-education — the Kids product control tower

**One sentence:** kids videos drive awareness → **kids-education.trigunai.com** is the practice app →
both run on the **same Grade-3 question generator** (`kids_quiz/gen_content.py`) and the **same Acharya
pipeline** (examgen + assess engine), just re-themed for children.

## ▶ NEXT TASK (start here in a new session)
**Deepak will provide IMAGES of his son's ICSE Grade-3 school books** (Children's Academy, Thane West).
Do this with them:
1. **Contents/index pages** → extract the EXACT chapter → sub-topic list per subject (Read the images
   directly — I can read photos). Build the authentic per-subject curriculum (supersedes the web-baseline
   in `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md`).
2. **Match to the taxonomy** → update the Grade-3 Maths chapters (and add EVS/English/GK/Hindi) so the
   app's chapters mirror his actual book.
3. **Questions:** Maths = keep the `gen_content.py` generator but align chapter names/scope to the book.
   Knowledge subjects (EVS/GK/English) = NOT computable → use RAG grounded on the book OR the
   `exact-question-making-pipeline-from-pdf` skill (verbatim answer-keyed Qs from the book pages).
4. **Ingest** into the `ICSE Class 3` pool on Gurukul (see "Question bank" below) so the app serves them.

## Key facts
| Thing | Value |
|---|---|
| **Kids app (LIVE)** | `https://kids-education.trigunai.com/` — Azure Container App **`kids`** (RG `trigunai-video-creator`, env `trigunai-env`), image `trigunaicr.azurecr.io/lms-kids:vN` (currently v6). **Isolated from the live `lms` app.** |
| Kids app FQDN | `kids.redflower-9a33748c.eastus.azurecontainerapps.io` (custom domain bound, HTTPS via managed cert) |
| **YouTube channel** | **TrigunAI-KidsEducation**, ID `UC9QWXw-M6W4eqo1dmbHYbLQ` (Brand acct under deepak@trigunai.com). 60 Grade-3 Maths videos uploaded UNLISTED. Token = `youtube_series/token_kids.json` (also on Gurukul). |
| **Video engine** | `kids_quiz/make_kids_quiz_video.py` (Lego JJ/Mikey, gems, kind reveals) + `gen_content.py` (18 Maths topics) + `batch_all.py` / `run_day_kids.py`. Detail = skill **trigunai-kids-quiz**. Render on EC2 `i-047ebf759f2386e71` (34.192.145.204). |
| **Question bank** | exam `"ICSE Class 3"`, subject `"Mathematics"` — **540 generated Qs (gen_content → qbank), 18 chapters, difficulty 1-2**, LIVE in the Gurukul `qbank.sqlite` (`gurukul.trigunai.com/examgen`). Served via `/pool?exam=ICSE Class 3&subject=Mathematics&difficulty=1-2`. |
| **Repos/paths** | app code = `lms/` (NvidiaSimSetup); kids engine + curriculum + generator = `kids_quiz/`; standalone landing = `kids_web/`; plan = `kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md` + `KIDS_ASSESSMENT_PLAN.md`. |

## The web app (kids-education.trigunai.com)
Runs the **full lms code** (image `lms-kids`, same DB + examgen + secrets as acharya) but host-gated:
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

## What's LIVE vs NEXT
**LIVE:** kids-education.trigunai.com (landing + kids /exam-prep + voice quiz + full pipeline), Grade-3 Maths
pool (540 Qs), 60 unlisted YouTube videos, acharya "For Kids" card.
**NEXT:** (1) **book images → exact curriculum → aligned/real questions** (the ▶ task above); (2) carry the
kids theme INTO the internal dashboard/test screens; (3) EVS/GK/English pools; (4) Google origin + go public.

Full blow-by-blow history: memory **[[project-kids-quiz-video]]**. Curriculum baseline:
`kids_quiz/KIDS_QUIZ_ICSE_G3_PLAN.md`. Assessment plan: `KIDS_ASSESSMENT_PLAN.md`.
