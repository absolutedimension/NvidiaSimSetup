# Acharya — Student Flow Plan (funnel → login → dashboard)

> **Goal:** a clean student journey — land → take the challenge → log in (Google/email) → land on a
> student **assessment dashboard** where earned free days show, and they can take adaptive tests on
> their subject + add up to 5 topics (₹199/mo package). Teacher flow untouched for now.
> **Repo:** `lms/` (FastAPI). **Deploy:** `maintain-trigunai-system` §2. Date: 2026-07-23.

---

## 1. Target flow (one diagram)

```
acharya.trigunai.com/  ──►  SPLIT LANDING  ┬─ [ I'm a Student ] ─► /exam-prep/quick  (the Challenge — image 2)
                                           └─ [ I'm a Teacher ] ─► existing teacher flow (#teachers / WhatsApp TEACHER)

/exam-prep/quick  (11-Q challenge, ~5 min, pick subject)
        │  answer 11 questions, scored SERVER-side
        ▼
   RESULT: "You earned X days FREE 🏆"   (14 → 60 days by score)
        │
        ▼  LOGIN to CLAIM  ──►  Google One-Tap  (verified email, no magic link)  OR  email
        │                       (this is the login moment — high intent: claim your days)
        ▼
/exam-prep/dashboard  (NEW student home)
        ├─ shows earned free days remaining  (assess_trial_end − now)
        ├─ MY TOPICS (up to 5)  ─ each = an exam+subject, e.g. "NEET Biology", "JEE Rotational Motion"
        │     └─ [ Take today's adaptive test ]  ─► /exam-prep/test?exam=<topic>
        ├─ [ + Add a topic ]  (blocked at 5 → "upgrade / max reached")
        ├─ progress / weak-topics per topic (SWOT)
        └─ when earned days run out ─► ₹199/mo upgrade (/exam-prep/upgrade, Razorpay)
```

---

## 2. What already EXISTS (✅) vs the GAPS (🔴)

| Piece | State | Notes |
|---|---|---|
| `/exam-prep/quick` challenge (11-Q, earn 14–60 days) | ✅ works | `exam_prep_quick.html` + `/api/comp/*` server-scored |
| Earned days banking | ✅ works | `_bank_days()` → `student.assess_trial_end`; fact `earned_days` |
| Email signup (no password) | ✅ works | `/exam-prep/start` sets `session["sid"]` |
| Google One-Tap **code** | ✅ exists | `/api/auth/google` verifies ID token, creates+logs in student |
| Google One-Tap **config** | 🔴 **OFF** | `GOOGLE_CLIENT_ID=""` → returns 503, One-Tap never renders. **This is "gmail login not working."** |
| Assessment access model (₹199 track) | ✅ exists | `assess_status`, `assess_trial_end`, `has_assessment_access()` |
| Dynamic test generation (any topic) | ✅ works | `assess_gen.py` + `AssessmentItem` cache |
| **Split landing (Student / Teacher)** at `/` | 🔴 **missing** | `/` = assessment landing, no clean 2-door split |
| **Challenge → login → dashboard handoff** | 🔴 **missing** | test end (`assess.html`) shows score + a `/dashboard` link (course dash, wrong one). No claim-days-then-home flow. |
| **Student assessment dashboard** | 🔴 **missing** | `/dashboard` is the COURSE dashboard (modules/lessons, ₹499 track). No exam-prep home. |
| **"My topics" (up to 5) model** | 🔴 **missing** | no per-student topic list or limit. `AssessmentItem` caches by topic globally, but student never "owns" topics. |
| Enforce 5-topic limit + tie to ₹199 | 🔴 **missing** | needs a `StudentTopic` table + limit check |

**Verdict:** ~60% is built. The real build = **(A) split landing, (B) student dashboard, (C) 5-topic model, (D) turn on Google login.**

---

## 3. The build — phased (student flow only)

> **STATUS 2026-07-23 — SHIPPED lms:v74:** S2 (dashboard) + S3 (5-topic `StudentTopic` model) + S4
> (challenge→claim→dashboard; both email + Google land on the dashboard, first topic seeded) are LIVE
> and verified in prod. **S1 (Google login) was a console-origins problem, not code** — the client ID
> was already on the container; origins now added in Google Console (propagating).
> REMAINING: Deepak's manual Google sign-in test on the live challenge.
>
> **UPDATE 2026-07-23 — S5 SHIPPED (`lms:v76`) + UX fixes (`lms:v75`):** split landing live at `/`
> (Student→/exam-prep/quick · Teacher→existing landing); logged-in `/exam-prep/quick`→dashboard;
> test-completion CTA→"🏠 My dashboard". **The entire student flow (S1–S5) is now LIVE.** Only open
> item = Deepak's manual Google sign-in test (incognito) + confirm consent screen "In production".

### Phase S1 — Turn ON Google login  *(smallest, unblocks the whole "auto login" idea)*
- **Deepak action (Google Cloud Console):** create a **Web OAuth 2.0 Client ID** → Authorized JS origins = `https://acharya.trigunai.com` (+ `https://lms.trigunai.com`). Copy the client ID.
- **Claude:** set container env `GOOGLE_CLIENT_ID=<id>` on the `lms` app; redeploy; verify One-Tap prompt renders on `/exam-prep/quick` + sign-in creates a student and lands them.
- *No code change — the handler already exists. Purely config + one env var.*

### Phase S2 — The student assessment dashboard  *(the missing "home")*
- New route `GET /exam-prep/dashboard` (or `/study`) — requires a logged-in student; NOT gated by the ₹499 course `has_access`, gated by `has_assessment_access` OR just "logged-in with earned days".
- New template `exam_prep_dashboard.html` (Acharya dark-gold): earned days remaining, MY TOPICS list, "take today's test" per topic, "+ add topic", per-topic weak-areas (from `LearningEvent`/mastery), upgrade CTA when days run low.

### Phase S3 — 5-topic model
- New `StudentTopic` table: `student_id, topic_key, title, exam, created_at` (+ mastery summary later).
- On challenge/test start, the chosen subject becomes the student's **first topic**.
- `+ Add topic` → free-text or curated (reuses `assess_gen`), blocked at 5 → "max reached (₹199 covers 5 topics)".

### Phase S4 — Wire challenge → claim → dashboard
- After the 11-Q result, the CTA is **"Claim your X free days"** → Google One-Tap / email → on success, land on `/exam-prep/dashboard` (not the course `/dashboard`).
- Bank the earned days on claim (already wired via `_bank_days`), seed topic 1 from the challenge subject.

### Phase S5 — Split landing at `/`
- `/` root: two clear doors — **Student** (→ `/exam-prep/quick`) and **Teacher** (→ existing teacher section/flow). Keep the assessment positioning; just make the two audiences a clean choice.
- (Do this LAST so the funnel it points to is already solid.)

---

## 4. Decisions — LOCKED (2026-07-23)
1. **Login moment:** ✅ **Earn-then-claim** — take all 11 Q anonymously → see score → "Claim your X free days" → login → dashboard.
2. **5 topics:** ✅ **5 for everyone** (earned-days-free AND ₹199 paid). One rule. ₹199 = "keep your 5 topics going after free days end."
3. **Dashboard route:** ✅ **New `/exam-prep/dashboard`**, separate from the course `/dashboard` (₹499 cohort track).

## 5. Coherence note — three "free" mechanics
Today there are 14-day trial, earned days (14–60), and ₹199/mo. Proposed clean model:
**earned days (14–60 from the challenge) ARE the free window → when they expire, ₹199/mo.** The flat
14-day trial becomes just the floor (everyone who attempts gets ≥14). One mechanic, not three.
