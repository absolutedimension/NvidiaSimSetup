# examgen API — Frontend Handoff (IIT JEE Advanced: Physics + Chemistry + Maths COMPLETE)

**Status (2026-07-23):** The full IIT JEE Advanced paper is live — all three subjects tagged, verified, and **worked-solved**. JEE Main (all three subjects) is also live on the same API.

> This supersedes the Physics-only `FRONTEND_HANDOFF.md`. Same API contract, now with all subjects.

---

## 1. Base URL + Auth

| | |
|---|---|
| **Base URL** | `https://gurukul.trigunai.com/examgen` |
| **Auth** | `Authorization: Bearer <QBANK_API_KEY>` — required on `POST /generate` only (`/health`, `/chapters` are open) |
| **Host** | Always-on Gurukul VM (migrated off the GPU box; no more "is the server up?" issues) |
| **CORS** | `*` (browser calls OK), but **do NOT ship the Bearer key to the browser** — call `/generate` from your server (see §5) |

The API key is the same one already used by the LMS (`lms` container secret `examgen-key`). Ask Deepak if you need it for a new service.

---

## 2. What's available (exam × subject)

| `exam` | `subject` | Chapters | Exemplar Qs | Solutions |
|---|---|---|---|---|
| `JEE Advanced` | `Physics` | 18 | 241 | 97% worked |
| `JEE Advanced` | `Chemistry` | 25 | 149 | **100% worked** |
| `JEE Advanced` | `Mathematics` | 27 | 226 | **100% worked** |
| `JEE Main` | `Physics` | 28 | 3,447 | 100% |
| `JEE Main` | `Chemistry` | 31 | 3,215 | 100% |
| `JEE Main` | `Mathematics` | 32 | 4,061 | 100% |

**Exact strings matter** — use `"JEE Advanced"` / `"JEE Main"` and `"Physics"` / `"Chemistry"` / `"Mathematics"` verbatim.

These are RAG **exemplars**. `/generate` authors NEW, copyright-clean questions in the style/difficulty of the banked ones (not the past-paper questions themselves).

---

## 3. `GET /health`

```
GET https://gurukul.trigunai.com/examgen/health
→ {"status":"ok","llm_reachable":true,"llm_error":null,"bank_verified":11336}
```
Use for an uptime/status check. `llm_reachable:true` means generation will work.

---

## 4. `GET /chapters` — the topic picker

```
GET /chapters?exam=JEE%20Advanced&subject=Mathematics
```
```json
{
  "exam": "JEE Advanced",
  "subject": "Mathematics",
  "chapters": [
    {"chapter": "Matrices And Determinants", "concepts": ["...","..."], "exemplars_banked": 22},
    {"chapter": "Complex Numbers", "concepts": [...], "exemplars_banked": 16},
    ...
  ]
}
```
- Render chapters where `exemplars_banked > 0` (a chapter with 0 can't generate).
- `concepts` is an optional finer picker — you can pass a chosen `concept` to `/generate`.

---

## 5. `POST /generate` — make a test (server-side)

**Request** (JSON body, Bearer auth):
```json
{
  "exam": "JEE Advanced",
  "subject": "Chemistry",
  "chapter": "Coordination Compounds",
  "concept": null,               // optional; omit or null = any concept in the chapter
  "difficulty": "3-4",            // "2-3" easier, "3-4" harder (JEE Adv is mostly 3-4)
  "type": "MCQ_single",           // MCQ_single | MCQ_multi | integer | numeric
  "count": 5,                     // how many questions
  "exemplars": 3,                 // RAG references per question (3–4 is good)
  "require_figure": false         // true → force a question with a generated SVG diagram
}
```

**Response** (top-level keys): `spec, exemplars_used, requested, generated, rejected, questions, answer_key, mock, llm_used`.

Each item in `questions[]`:
```json
{
  "id": "gen_chemistry_6bca1ae8f9862fbf_0",
  "exam": "JEE Advanced", "subject": "Chemistry",
  "stem": "An octahedral complex ion has the formula $[\\mathrm{Co(NH_3)_2Cl_2Br_2}]^-$ ... (LaTeX)",
  "qtype": "MCQ_single",
  "options": [{"label":"A","text":"$4$"}, {"label":"B","text":"$5$"}, ...],   // [] for integer/numeric
  "correct_answer": "C",          // "C" | "AC" | "12" | "3.14"
  "solution": "…worked solution (LaTeX)…",
  "figure_svg": null,             // inline SVG string if a diagram was generated
  "figure_url": null,             // absolute PNG URL if it reuses a real figure
  "chapter": "Coordination Compounds", "concept": "...", "difficulty": 4
}
```
- `answer_key` is a convenience map `{id: correct_answer}`.
- `generated` may be **less than** `requested` — a verify gate drops questions whose generated answer looks wrong (`rejected[]` tells you why). **Always read `generated`**, and re-call if you need more.
- **Render LaTeX**: `stem`, `options[].text`, and `solution` contain LaTeX (`$...$`, `\mathrm{}`, etc.) — pass through KaTeX/MathJax.
- **Figures**: if `figure_svg` is present, inline it; if `figure_url`, `<img src>` it.

**Latency**: ~15–60s for a 5-question pack (LLM generation). Use a generous client timeout (≥120s) and a loading state.

### Minimal server proxy pattern (what the LMS already does)
```
Browser → yourserver /api/examgen/generate  (no key in browser)
             → POST https://gurukul.trigunai.com/examgen/generate  (adds Bearer key)
             → returns {ok, pack} to the browser
```

---

## 6. Wiring a NEW subject into the student UI (LMS)

The API already serves all 6 banks. But the **LMS student funnel currently only lists "IIT-JEE Physics"** (JEE Advanced Physics). To show Chemistry / Maths (and JEE Main) to students:

1. In `lms/app/examgen.py`, add entries to `RAG_SUBJECTS`, e.g.:
   ```python
   "jee-chemistry": {"label":"IIT JEE Chemistry","exam":"JEE Advanced","subject":"Chemistry","match":[...]},
   "jee-maths":     {"label":"IIT JEE Maths","exam":"JEE Advanced","subject":"Mathematics","match":[...]},
   ```
2. Add matching entries to the `EXAMS` list in `lms/app/main.py` (so they appear at `/exam-prep`).
3. Deploy a new `lms:vN` (see the `maintain-trigunai-system` skill §2).

No backend/API change needed — just the LMS config + a redeploy.

---

## 7. Gotchas / notes

- **Exemplars, not verbatim past papers** — output is generated + validated (copyright-clean). Real past-paper questions carry correct keys; generated ones are practice.
- **3 real past-paper keys are flagged disputed** in the bank (out of scope for `/generate`, which only emits generated Qs) — internal QA note, no frontend impact.
- **`require_figure:true`** guarantees a diagram question but lowers yield (fewer valid Qs). Use sparingly.
- **Difficulty**: JEE Advanced content is calibrated to 3–4; requesting "1-2" may return few/no exemplars → generation falls back to chapter-only.
- If `/health` shows `llm_reachable:false`, generation is temporarily down (Azure hiccup) — retry.

**Questions / key access:** Deepak (deepak@trigunai.com).
