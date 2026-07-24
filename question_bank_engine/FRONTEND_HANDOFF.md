# Frontend Handoff — TrigunAI Question Generator API

**For the frontend agent.** This is a live HTTP API that generates fresh, validated,
copyright-clean exam questions (currently **JEE Physics**) on demand. You build the UI;
this API does the generation. You never touch the LLM or any keys — you just call it.

---

## 1. Base URL & auth

- **Base URL:** `https://rtx.trigunai.com/examgen`
- **Auth:** every `POST /generate` needs a header
  `Authorization: Bearer <API_KEY>`
  The key lives in `/home/ubuntu/question_bank_engine/api.env` on the EC2 box
  (`QBANK_API_KEY=…`). **Get it from Deepak** — do NOT hardcode it in committed
  frontend source; put it in a server-side env var / proxy (see §6 security note).
- `GET /health` and `GET /chapters` need no auth.

Quick check:
```bash
curl https://rtx.trigunai.com/examgen/health
# {"status":"ok","llm_reachable":true,"bank_verified":225}
```

> **Want to see it work in 30 seconds?** Open `test_client.html` (in this folder) in a
> browser, paste the API key, pick a chapter, click Generate. It's a full working
> reference implementation (calls + MathJax rendering) you can copy patterns from.

---

## 2. Endpoints

### `GET /health`
Returns `{status, llm_reachable, bank_verified}`. Use for a status indicator.

### `GET /chapters?exam=JEE%20Advanced&subject=Physics`
Feeds your **topic picker**. Returns:
```json
{
  "exam": "JEE Advanced", "subject": "Physics",
  "chapters": [
    {"chapter": "Modern Physics",
     "concepts": ["Photoelectric Effect","Bohr Model & Atomic Spectra","Nuclear Physics","Dual Nature / de Broglie"],
     "exemplars_banked": 18},
    {"chapter": "Kinematics", "concepts": ["Projectile Motion","Motion in a Straight Line"], "exemplars_banked": 13}
  ]
}
```
> Only offer chapters where `exemplars_banked > 0` — generation needs exemplars to
> imitate. Chapters with 0 will return an error.

### `POST /generate`
Request body:
```json
{
  "exam": "JEE Advanced",     // optional, default "JEE Advanced"
  "subject": "Physics",        // optional, default "Physics"
  "chapter": "Modern Physics", // REQUIRED — a chapter from /chapters
  "concept": null,             // optional, e.g. "Photoelectric Effect"
  "difficulty": "3-4",         // "3" or a range "3-4", scale 1-5
  "type": "MCQ_single",        // MCQ_single | MCQ_multi | integer | numeric
  "count": 5,                  // 1..20
  "exemplars": 3,              // how many past-paper exemplars to imitate (1..8)
  "require_figure": false      // true = force every question to include an SVG diagram
}
```

Response (`200`):
```json
{
  "spec": { "...echo of the request..." },
  "exemplars_used": ["jee_adv_phy_2016_1_cb3150", "..."],
  "requested": 5,
  "generated": 5,
  "rejected": [],
  "questions": [
    {
      "id": "gen_physics_6c5b…_0",
      "stem": "In a photoelectric experiment ...  $\\lambda = 500\\,\\text{nm}$ ...",
      "qtype": "MCQ_single",
      "options": [
        {"label": "A", "text": "$6.0 \\times 10^{-34}\\ \\text{J s}$"},
        {"label": "B", "text": "$6.4 \\times 10^{-34}\\ \\text{J s}$"},
        {"label": "C", "text": "$6.8 \\times 10^{-34}\\ \\text{J s}$"},
        {"label": "D", "text": "$7.2 \\times 10^{-34}\\ \\text{J s}$"}
      ],
      "correct_answer": "B",
      "solution": "Using $E_k = h c/\\lambda - \\phi$ ...",
      "chapter": "Modern Physics",
      "concept": "Photoelectric Effect",
      "difficulty": 4,
      "needs_figure": false,
      "figure_url": null,
      "generated": true
    }
  ],
  "answer_key": {"gen_physics_6c5b…_0": "B"}
}
```

**Answer formats by `qtype`:** `MCQ_single` → one letter (`"B"`); `MCQ_multi` →
letters (`"AC"`); `integer` → an integer string (`"9"`); `numeric` → a decimal
string (`"3.14"`). For integer/numeric, `options` is `[]`.

---

## 3. Rendering (important)

- **`stem`, `options[].text`, and `solution` contain LaTeX.** Render them with
  **KaTeX or MathJax**. Inline math is delimited with `$…$` (and `\[ … \]` for
  display blocks in solutions). Don't HTML-escape the backslashes.
- Some stems contain LaTeX **tables** (`\begin{tabular}…`) — KaTeX needs the
  `\begin{array}` style or MathJax with the AMS packages; MathJax handles these more
  robustly, so prefer **MathJax** if you expect tabular data questions.
- **Diagram questions.** Two figure fields can appear on a question:
  - **`figure_svg`** — an inline SVG string (this is what GENERATED diagram questions
    carry). Render it inline, e.g. `element.innerHTML = q.figure_svg` (React:
    `dangerouslySetInnerHTML`). It's already sanitized server-side (no scripts / event
    handlers / external refs), but **sanitize again client-side** (e.g. DOMPurify with
    SVG profile) as defense-in-depth. Give it a white background — strokes assume light.
  - **`figure_url`** — a served PNG (this is what real *past-paper* questions carry, if
    you ever expose them). Render as `<img src=…>`.
  - `needs_figure: true` + neither field set = a figure is required but unavailable →
    skip/flag that question.
  - To deliberately get diagram questions, POST with `"require_figure": true` — every
    returned question will have a valid `figure_svg`. (See `test_client.html`, "Require
    diagram = yes", for the exact render pattern.)

---

## 4. Latency & UX

- Generation is **synchronous** and LLM-backed: ~**6–12 s per question**
  (a 5-question test ≈ 30–60 s). Set a **client timeout ≥ 180 s** and show a
  progress/spinner state.
- For a snappier UX, request `count: 1` a few times in parallel, or add a
  "generating…" skeleton. (A streaming/async-job endpoint can be added later if you
  want it — ask.)
- `rejected` may be non-empty if the model produced a near-duplicate of a banked
  question (novelty gate) or a malformed one; `generated` is what you actually got.
  Occasionally `generated < requested` — render what came back.

---

## 5. Minimal integration example

```js
async function generateTest() {
  const res = await fetch("https://rtx.trigunai.com/examgen/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`,   // from a server-side env, not the browser bundle
    },
    body: JSON.stringify({
      chapter: "Modern Physics", difficulty: "3-4", type: "MCQ_single", count: 5,
    }),
  });
  if (!res.ok) throw new Error(`generate failed: ${res.status}`);
  const test = await res.json();
  return test.questions;   // render each .stem / .options with MathJax; grade via .answer_key
}
```

---

## 6. Security note (please respect)

- The API key gates **real Azure token spend**. Do **not** ship it in client-side JS.
  Put it in your frontend's **server/BFF** and proxy `/generate` through it, or in a
  serverless function. The browser calls your backend; your backend adds the key.
- **CORS** is currently `*` for dev. Before launch, tell Deepak your frontend domain
  and it'll be locked to it (`QBANK_CORS` env on the API).

---

## 7. Ops (FYI — Deepak/infra owns this)

- Host: EC2 `34.192.145.204` (`i-047ebf759f2386e71`, us-east-1), stable Elastic IP.
- Service: `systemctl status qbank-api` (uvicorn on `127.0.0.1:8020`).
  Restart: `sudo systemctl restart qbank-api`. Logs: `journalctl -u qbank-api -f`.
- Public route: Caddy `handle_path /examgen/*` on `rtx.trigunai.com` → `:8020`.
- LLM: LiteLLM proxy (`:4000`) → Azure `gpt-4o`. Code + bank: `/home/ubuntu/question_bank_engine/`.

---

## 8. Current coverage / limits (so the UI doesn't over-promise)

- **Exam/subject: JEE Advanced Physics only** right now. **225 verified questions**
  spanning **2016–2026** (incl. latest 2024/25/26). **17 chapters** are generatable
  (all with banked exemplars) — fetch the live list from `GET /chapters`. Top ones:
  Modern Physics (30), Waves & Sound (26), Kinematics (23), Electrostatics (22),
  Current Electricity (18), Thermodynamics (17), Ray Optics (13). Chemistry/Maths/NEET
  are a config addition coming next.
- Best-validated type is **`MCQ_single`**. `integer`/`numeric` work; `MCQ_multi` works
  but eyeball a few.
- Difficulty is model-calibrated 1–5; JEE-Advanced content clusters at 3–4.
- Every question is validated (well-formed + answer-plausible) and novelty-checked vs
  the real bank, but this is v1 — surface a lightweight "report question" affordance so
  Deepak can catch the occasional bad one.
```
