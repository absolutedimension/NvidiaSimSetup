# Frontend Handoff — Acharya Practice (pool-based serving + new UX)

**For the frontend agent.** This replaces the "generate a test" model with a **shared pre-generated pool served instantly**, and specifies the new student UX. Supersedes `FRONTEND_HANDOFF_IIT.md` for anything student-facing.

**Interactive design blueprint (clickable):** https://claude.ai/code/artifact/12e61b70-3302-4b71-8c50-9778a937a77a
Build the frontend to match that blueprint's architecture (not pixel-exact).

> **Status (2026-07-23):** `/chapters`, `/generate`, `/health` are LIVE now. The new **`/pool` + `/pool/stats`** endpoints are coded but **not yet deployed** to `gurukul.trigunai.com/examgen`, and the shared pool is **not yet filled** (backend runs `batch-generate` first). You can build the UI against the pool contract below; coordinate go-live with Deepak. Until `/pool` ships, you can prototype against `/generate` (slow) with the same question shape.

---

## 0. The two big model changes

1. **Exam is a registration-time identity, NOT a header toggle.** A student registers as an **IIT-JEE** *or* **NEET** aspirant (never both). Everything downstream is scoped to that one goal. Store it on the student record; pass it as `exam`/`subject` to the API. Changing it is a rare Settings action. *(Within IIT-JEE, "Main vs Advanced" is a level/difficulty inside one track — a JEE aspirant sits both — surfaced as mock types and difficulty tiers, never an identity switch.)*

2. **Serve from the shared POOL, not live generation.** Questions are pre-generated in bulk into a shared pool. The frontend's hot path reads the pool **instantly (no LLM, no wait)**. Live generation is a *fallback* only when a power user drains a topic. This is what lets a student do 50+ questions in a sitting.

---

## 1. Base URL + auth

| | |
|---|---|
| **Base URL** | `https://gurukul.trigunai.com/examgen` |
| **Auth** | Only `POST /generate` needs `Authorization: Bearer <QBANK_API_KEY>` (server-side). `/pool`, `/chapters`, `/health` are open (no token cost). |
| **Never** ship the Bearer key to the browser — call `/generate` from your server. |

---

## 2. Endpoints

### `GET /pool` — the hot path (instant, no LLM) ⭐
Draw questions for a topic from the shared pool. Pass `exclude` = comma-separated IDs the student has already seen (so no repeats).
```
GET /pool?exam=JEE%20Advanced&subject=Chemistry&chapter=Coordination%20Compounds
        &difficulty=3-4&type=MCQ_single&count=10&exclude=id1,id2,id3
```
```json
{ "exam":"...","subject":"...","chapter":"...","difficulty":"3-4",
  "count": 10, "exhausted": false,
  "questions": [ { "id","exam","subject","stem","qtype","options":[{label,text}],
                   "correct_answer","solution","chapter","concept","difficulty",
                   "figure_svg","figure_url" }, ... ] }
```
- **`exhausted: true`** (fewer than `count` returned) → this student has seen most of the pool for that cell. Fall back to `/generate` to top up (see below).
- LaTeX in `stem`, `options[].text`, `solution` → render with KaTeX/MathJax. Figures: inline `figure_svg`, else `<img src=figure_url>`.

### `GET /chapters` — topic picker
```
GET /chapters?exam=JEE%20Advanced&subject=Mathematics
→ { chapters:[ {chapter, concepts:[...], exemplars_banked, exemplars_own}, ... ] }
```
Render chapters with `exemplars_banked > 0`. `concepts` powers the map's expandable sub-rows.

### `POST /generate` — fallback for power users (server-side, Bearer)
Only call when `/pool` returns `exhausted:true` for an active student. Same body as before → returns fresh questions AND refills the pool for everyone.
```json
{exam,subject,chapter,concept?,difficulty:"3-4",type:"MCQ_single",count,exemplars,require_figure}
```

### `GET /pool/stats` — ops/admin
`GET /pool/stats?exam=JEE%20Advanced&subject=Chemistry` → pool depth per chapter. For an admin dashboard, not the student app.

### `GET /health` — status/uptime.

---

## 3. The serving loop the frontend implements

```
Student starts Smart Practice / a topic
  → GET /pool?...&exclude=<seenIds for this cell>&count=10   (instant)
  → serve questions; record each answered id into the student's "seen" set (server-side)
  → if response.exhausted:  POST /generate (server-side) to top up, then continue
Pre-fetch the NEXT batch while the student answers the current one → zero perceived latency.
```
- **Track seen IDs per student** (server-side table: student_id, question_id, correct, confidence, ts). Drives both no-repeats and mastery.
- **Pre-fetch**: request the next 10 while they work the current 10 → questions feel instant, which is what drives volume.

---

## 4. What the frontend owns: mastery + adaptive routing

The API serves questions; **the frontend/LMS computes mastery and picks what to serve next.** Minimum viable:
- **Per-concept mastery %** from the student's answer history (e.g. rolling accuracy weighted by difficulty & recency). Store per (student, chapter/concept).
- **Smart Practice** = pick the next cell by: weakest mastery + spaced-revision-due + "unlock next difficulty." Then `GET /pool` for that cell.
- **Difficulty ladder** — start a topic at 2-3; once mastery passes a threshold, request 3-4.
- **Results screen** — after a session, show score, time, XP, and **per-topic mastery deltas** (the retention driver).

---

## 5. Screens to build (from the blueprint)

1. **Onboarding** — pick goal (IIT-JEE / NEET) → optional quick diagnostic → seed the map.
2. **Today** — mastery ring, "why this set" line, one big **Smart Practice** button, 4 mode chips (Smart / Topic / Mock / Revision / Weak-areas), subject-strength radar, focus areas, streak.
3. **Syllabus Map** — all chapters with mastery bars (fillable), expandable to concepts, filters (All / Weak / Untouched / Strong). The breadth-discovery screen.
4. **Practice** — question card with LaTeX, options, timer, mark-for-review, bookmark, confidence tap, progressive hint→solution, report-issue, progress bar.
5. **Report/Results** — session summary + per-topic mastery deltas + "review mistakes / practice again".

**Exam-scoping in the shell:** header shows a fixed **"🎯 Goal: IIT-JEE"** chip (non-interactive); mobile uses a bottom nav; light + dark themes (Acharya dark-gold).

---

## 6. Gotchas
- **Pool answers are practice-grade** (generated + verified, not official keys). Show the worked `solution` after each answer; the **report button** should POST a flag (feeds the internal dispute queue).
- `/pool` is randomised — always pass `exclude` or a student will occasionally re-see a question across sessions.
- Difficulty `"3-4"` band = Advanced-level; `"2-3"` = Main-level (JEE). NEET Physics/Chemistry currently **borrow JEE Main exemplars** (same syllabus) — `/chapters` exposes this via `exemplar_fallback_exam`; nothing extra for the frontend to do.
- Latency: `/pool` is instant; only `/generate` is slow (15–60 s) — keep it off the hot path, use it as background top-up.

**Backend/pool owner:** Deepak (deepak@trigunai.com) · batch-fill runbook is in the `trigunai-assessment-backend-data` skill §5.5.
