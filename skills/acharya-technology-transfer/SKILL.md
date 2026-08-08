---
name: acharya-technology-transfer
description: >
  Step-by-step provisioning skill that stands up a branded Acharya AI-tutor instance for a NEW
  paying/trial coaching teacher on the SHARED Gurukul box (multi-tenant by course, one box for
  many teachers). Takes the minimum inputs from Deepak (teacher/coaching name, slug, subject +
  syllabus, students, logo, colors) and: (1) builds the teacher's course concept-bank, (2) deploys
  it live to the WhatsApp tutor on the Gurukul VM, (3) lists the course on acharya.trigunai.com so
  students can study on web, (4) enrols the teacher's students, (5) wires progress tracking for the
  14-day trial, and (6) hands the teacher an onboarding pack. Acharya introduces itself under the
  teacher's brand ("<Teacher>'s tutor") and teaches ONLY their course. A DEDICATED Azure box is a
  documented later step, triggered only when one teacher's student volume outgrows the shared box.
  USE WHEN: a teacher confirms the ₹4,999/mo plan (or the free 14-day trial) and you need to set up
  their system; "onboard a teacher", "set up <teacher>'s Acharya", "provision a teacher", "white-
  label Acharya", "transfer Acharya to a customer", "give the teacher their tutor", "teacher went
  live". Companion to add-trigunai-course (course-bank authoring), maintain-trigunai-system (owns
  the live LMS/VM stack), teacher-outreach-engine (fills the pipeline), trigunai-ceo (the gate).
---

# Acharya Technology Transfer — provision a teacher's branded tutor (shared-tenant)

> **The job:** a teacher said yes → turn that into a LIVE, branded Acharya their students can use
> today, on the shared box, with zero new infra. One repeatable run. Honest about what's instant
> vs what's a fast-follow. Owner: Deepak. Model: **sonnet** (mechanical + content); escalate to
> **opus** only for authoring a deep concept-bank from a raw syllabus.

---

## 0. READ THIS FIRST — the honest architecture (what "transfer" really is)

We do **NOT** clone a box or fork the app per teacher. That doesn't scale and isn't needed. The
system is **multi-tenant by COURSE on one shared box**:

- **One Gurukul VM** (`20.219.2.53`) runs the WhatsApp tutor for ALL teachers. It reads each
  teacher's course live from a JSON file — **no restart, no new server.**
- **One LMS** (`acharya.trigunai.com`) hosts every teacher's course in a shared catalog.
- **A teacher = a tenant record + a course id.** Their students are scoped to their course; teacher
  A's students never see teacher B's.

**What is INSTANT / Monday-ready (this skill does all of it):**
| Capability | How |
|---|---|
| ✅ Branded **tutor** — Acharya says *"I'm <Teacher>'s tutor"* and teaches ONLY their syllabus | course concept-bank + `intro`/`brand` fields, scp'd live to the VM |
| ✅ Students learn on **WhatsApp** 24×7, doubt-solving + practice + revision in their subject | shared Acharya number, per-student routing to their course |
| ✅ Course **live on the web** (acharya.trigunai.com) — students can also study/take assessments | LMS catalog + course-detail entry + deploy |
| ✅ Enrol the teacher's **students**, scoped to their course | `/admin/set-course` or `openclaw agent --course` |
| ✅ **Progress visibility** for the trial (who's active, stuck, streaks) | admin dashboard + course-filtered CSV export |

**What is a FAST-FOLLOW (NOT Monday — needs the multi-tenant LMS refactor; §7):**
| Deferred | Why it's not instant | Trial workaround |
|---|---|---|
| ⏳ Teacher's **own logo/colors on the web page** | LMS branding is single-tenant, hardcoded in `app.css :root` + templates | Tutor is branded by NAME now; capture logo+colors in the tenant record so the rebrand is 1 step later |
| ⏳ Teacher's **own domain** (`tutor.theircoaching.com`) | needs multi-tenant Host-routing + their DNS | Give an instant **subdomain later**; for the trial the shared brand is fine |
| ⏳ Teacher's **own WhatsApp number** | Meta business verification (days) | Use the shared Acharya number with branded persona now; provision a dedicated number during the 14 days |
| ⏳ Self-serve **teacher dashboard** (`/teacher/<id>`) | Teacher table + auth + query filter not built | Deepak reads the admin dashboard / sends a weekly progress screenshot for the trial |
| ⏳ **Dedicated Azure box** | only worth it at high student volume | Stay on the shared box until a teacher is big (§8) |

> **Tell the teacher the honest version:** "Your tutor is live under your name today; your own
> branded website and phone number get switched on during your free 14 days." Value now, polish
> during the trial. This matches the offer in `teacher_gtm/01_OFFER_ONE_PAGER.md`.

---

## 1. MINIMUM INPUTS — collect these before you start

Ask Deepak for these. **Mandatory** blocks the run; **optional** has safe defaults.

**Mandatory**
1. **Coaching / teacher name** — e.g. `Catalyzers Institute` (goes into the tutor's self-intro).
2. **Slug** — kebab-case, becomes the `course_id` + tenant key — e.g. `catalyzers-kota`. Lowercase, no spaces.
3. **Subject / exam** — e.g. `NEET/JEE Physics`, `Class 10 Science`, `UPSC Polity`.
4. **Syllabus outline** — the topics/chapters they teach, in teaching order. A rough list is fine;
   the skill turns it into a concept-bank. (If they hand a PDF/photo, transcribe the topic list.)
5. **Students to enrol** — name + WhatsApp number for the ≤10 trial students (or "teacher will send").

**Optional (capture now, apply now-or-later)**
6. **Logo** — PNG file path (stored in the tenant record; applied on the web in the §7 fast-follow).
7. **Brand colors** — hex (e.g. gold `#E8C66B`). Default = Acharya dark-gold.
8. **Teacher's WhatsApp** (for the weekly report) + **their own domain** (later).
9. **Custom welcome line** — one sentence Acharya opens with.

> If an input is missing, **don't invent syllabus content** — ask, or scaffold a skeleton bank and
> mark it `DRAFT` so Deepak fills the concepts before students hit it.

---

## 2. CREATE THE TENANT RECORD (source of truth for this teacher)

Every teacher gets one JSON in `tenants/<slug>.json` (repo). This is the single place their brand +
config lives, so the later web-rebrand and dedicated-number steps are mechanical.

```bash
cd ~/Documents/01_Active/NvidiaSimSetup
cp tenants/_TEMPLATE.json tenants/<slug>.json
# then fill it in (see the template's comments)
```

Fields: `slug`, `name`, `course_id` (=slug), `subject`, `brand.logo`, `brand.colors`,
`whatsapp.mode` (`shared` | `dedicated`), `whatsapp.number`, `students[]`, `trial.start`,
`trial.end` (start+14d), `status` (`provisioning`→`live`→`paid`|`churned`), `web.subdomain`,
`web.custom_domain`, `notes`. Keep it updated as the tenant progresses — it's the tenant registry.

---

## 3. BUILD THE COURSE CONCEPT-BANK (the tutor's brain)

This is the core. **Reuse the `add-trigunai-course` skill** — it owns the concept-bank schema.
Create `agentic_cohort/gurukul_pipeline/courses/<slug>.json`:

```json
{
  "course_id": "<slug>",
  "name": "<Subject> — by <Teacher name>",
  "brand": "<Teacher name>",
  "intro": "Namaste! I'm <Teacher name>'s tutor. I'll help you master <subject> — one step at a time.",
  "order": ["concept_a", "concept_b", "..."],
  "assessments": { "2": {"title": "...", "url": "https://acharya.trigunai.com/lesson/<slug>"} },
  "concepts": {
    "concept_a": {
      "module": 1,
      "hook": "A one-line intriguing question that opens the concept.",
      "recall": "The check question Acharya asks to gate mastery.",
      "answer": "The gist of the correct answer."
    }
  }
}
```

Rules (from the live tutor design):
- `order` is the **strict** teaching sequence — students can't skip.
- `brand` + `intro` are what make it **the teacher's** tutor (self-intro under their name).
- Aim **20–40 concepts across 5–10 modules**. Each concept = hook + recall + answer.
- Author from the teacher's syllabus (§1.4). For a dense/technical syllabus, escalate to **opus**.
- If you only have a skeleton, ship `order` + module map and mark thin concepts `"draft": true`;
  do NOT let students hit an empty concept.

Validate before deploy:
```bash
python3 -c "import json;d=json.load(open('agentic_cohort/gurukul_pipeline/courses/<slug>.json'));\
assert d['course_id']=='<slug>';assert d['order'];\
missing=[k for k in d['order'] if k not in d['concepts']];\
print('OK concepts:',len(d['concepts']),'modules:',len({c['module'] for c in d['concepts'].values()}),\
'missing_in_order:',missing)"
```

---

## 4. DEPLOY THE COURSE TO THE LIVE TUTOR (WhatsApp — instant, no restart)

```bash
scp -i ~/.ssh/gurukul_key \
  agentic_cohort/gurukul_pipeline/courses/<slug>.json \
  dk_trigun@20.219.2.53:/home/dk_trigun/.openclaw/gurukul/courses/<slug>.json
```

The bridge reads course banks live per student — **the tutor now knows this course.** No service
restart needed.

**Smoke-test the tutor** (from the VM, a fake inbound so no real student is touched):
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 \
 'curl -s -X POST localhost:8788/webhook -H "Content-Type: application/json" \
  -d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"91TESTNUMBER\",\"type\":\"text\",\"text\":{\"body\":\"hi\"}}]}}]}]}"'
# Expect a 200; check the bridge log tail for the routed course.
```

---

## 5. LIST THE COURSE ON THE WEB (acharya.trigunai.com)

So the teacher's students can also study + take scored assessments on the web. Four edits in the
LMS repo (`lms/app/`), then one deploy. **Match the existing formatting exactly.**

1. `lms/app/main.py` → append to `COURSES` (~line 40):
   ```python
   {"id": "<slug>", "title": "<Subject> — <Teacher name>", "ready": True},
   ```
2. `lms/app/main.py` → add to `ACHARYA_BLURBS`:
   ```python
   "<slug>": "<one-line hook for the landing card>",
   ```
3. `lms/app/main.py` → add to `ACHARYA_THUMBS` (shader 0–5, seed to vary):
   ```python
   "<slug>": [2, 4.0],
   ```
4. `lms/app/course_details.py` → add `COURSE_DETAILS["<slug>"] = { tagline, level, modules,
   duration, what_you_build[], curriculum[], prerequisites, outcome }` (copy the shape of an
   existing entry).
5. *(optional)* `lms/app/seed.py` → add a `<SLUG>_MODULES` array for the full web journey. Not
   required for the tutor; add if the teacher wants the web lesson cards.

**Deploy the LMS** (subscription → build → update → verify):
```bash
az account set --subscription cb656d95-2f68-469f-b2b5-aee1ac1be625
cd lms
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .        # bump N
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
for i in $(seq 1 15); do curl -sf https://acharya.trigunai.com/healthz && break || sleep 8; done
```
Verify the course card shows on `https://acharya.trigunai.com/login` and `/`.

> ⚠️ This is a **live production deploy** touching all teachers' shared LMS. Follow
> `maintain-trigunai-system` safety rules — adding a catalog entry is additive/low-risk, but never
> break the existing `COURSES` list or the seed. Find the current `vN` first (`az containerapp show
> -n lms -g trigunai-video-creator --query properties.template.containers[0].image`).

---

## 6. ENROL THE TEACHER'S STUDENTS (scoped to their course)

Per student (≤10 for the trial):

**Web/LMS route** (if the student has/gets an LMS account):
```bash
# admin-only; sets which course this student sees
curl -s "https://acharya.trigunai.com/admin/set-course?email=<student_email>&course=<slug>" \
  -H "Cookie: <admin_session>"
```

**WhatsApp route** (proactive first-touch from Acharya — needs an approved template if it's the
first business-initiated message; otherwise the student messages the number first):
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53
openclaw agent --to +<student_number> --course <slug> \
  --message "Namaste! You're enrolled with <Teacher>'s tutor. Message me any doubt anytime." --json
```

Record each enrolled student back into `tenants/<slug>.json → students[]` with their status.

---

## 7. PROGRESS TRACKING FOR THE TRIAL (the teacher's "dashboard")

A self-serve teacher dashboard isn't built yet (§0). For the 14-day trial, deliver progress as a
**weekly pull** so the teacher sees value:

- **Admin dashboard:** `https://acharya.trigunai.com/admin` — active students, lessons done,
  streaks, learning analytics.
- **Course-filtered export:**
  ```bash
  curl -s "https://acharya.trigunai.com/admin/api/export.csv" -H "Cookie: <admin_session>" \
    | awk -F, 'NR==1 || $0 ~ /<slug>/'
  ```
- Turn it into the teacher's **weekly report** (who practiced, who's stuck, on what) — this is the
  "you see exactly who's falling behind" promise from the offer. Send it on WhatsApp to their number.

> Building the real per-teacher dashboard (`Teacher` table + login + `WHERE course=<slug>` filter)
> is the top fast-follow once the first teacher pays — see `maintain-trigunai-system §8`.

---

## 8. VERIFY → HANDOFF → LOG

**Verify checklist (all green before you tell the teacher it's live):**
- [ ] `tenants/<slug>.json` exists + filled, `status: live`.
- [ ] Course JSON validates (§3) + is on the VM (`ssh … 'ls ~/.openclaw/gurukul/courses/<slug>.json'`).
- [ ] Tutor smoke-test returned 200 and routed the right course (§4).
- [ ] Course card visible on acharya.trigunai.com (§5) + `/healthz` OK.
- [ ] ≥1 student enrolled + confirmed reachable (§6).
- [ ] A first weekly-report pull runs (§7).

**Hand the teacher an onboarding pack** (reuse `teacher_gtm/04_PILOT_ONBOARDING.md`):
- The WhatsApp number their students message + a one-line "how to use it" for students.
- The web link (`acharya.trigunai.com`, their course).
- What they'll get each week (the progress report).
- The trial dates (start + 14 days) and "then ₹4,999/mo, cancel anytime."

**Log it:**
- Append to `teacher_gtm/03_CONVERSATION_LOG.md` (provisioned, trial live, dates).
- `cd teacher_gtm && python3 progress.py` to bump pilots-live.
- Mark the routine **Block 1** done for the day with the tenant slug as the artifact.

---

## 9. SCALE-UP: when to give a teacher a DEDICATED box (later, not now)

Stay on the shared box until a teacher trips one of these, then migrate:
- Their students would push the shared VM (`Standard_B2s`, 2 vCPU/4 GB) — many concurrent chats, or
- They pay for isolation / their own number+domain as a premium tier, or
- They need data isolation for compliance.

**Migration (documented, build when first needed):** create a `Standard_B2s` Ubuntu 24.04 VM (static
IP, NSG 22+443) → install Node 22 + `openclaw` → copy `~/.openclaw` workspace template + their
`courses/<slug>.json` + their `students/*` profiles → Caddy for `tutor.<domain>` (auto-TLS) → point
DNS → move their students' WhatsApp routing. The tutor is stateless + course-agnostic, so this is a
copy-files-and-DNS job, not a rebuild. Reference: `agentic_cohort/WHATSAPP_GURUKUL_SETUP.md`.

---

## 10. RESOURCE & COMMAND REFERENCE

| Thing | Value |
|---|---|
| Gurukul VM (shared tutor) | `ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53` · RG `trigunai-gurukul-rg` (Central India) |
| Course banks on VM | `~/.openclaw/gurukul/courses/<slug>.json` (read live, no restart) |
| Course banks in repo (source of truth) | `agentic_cohort/gurukul_pipeline/courses/<slug>.json` |
| Bridge port / service | `127.0.0.1:8788`, systemd `wa-bridge` · webhook `https://gurukul.trigunai.com/webhook` |
| LMS repo | `lms/` (FastAPI + Jinja2) · catalog in `app/main.py`, details in `app/course_details.py` |
| LMS Azure | sub `cb656d95-2f68-469f-b2b5-aee1ac1be625` · RG `trigunai-video-creator` · Container App `lms` · registry `trigunaicr` |
| LMS deploy | `az acr build --registry trigunaicr --image lms:vN --file Dockerfile .` → `az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN` |
| Web URL | `https://acharya.trigunai.com` (lms.trigunai.com 301→here) |
| Tenant registry | `tenants/<slug>.json` (this skill) |
| Brand tokens (single-tenant, for §7 refactor) | `lms/app/static/app.css :root` + `lms/app/static/brand/` |
| Offer / onboarding copy | `teacher_gtm/01_OFFER_ONE_PAGER.md` · `teacher_gtm/04_PILOT_ONBOARDING.md` |

**Never print secrets.** Meta token / bridge key / DB URL / Razorpay keys live in the LMS Container
App secrets + `~/.openclaw/wa_cloud.env` on the VM. This skill never needs to echo them.

---

*Built 2026-07-04 for the first teacher trial. Shared-tenant by course on one box; dedicated box
only on scale (§9); per-teacher web logo/domain + self-serve dashboard are the named fast-follows
(§0, §7). Companion to add-trigunai-course, maintain-trigunai-system, teacher-outreach-engine.*
