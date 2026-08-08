# Google Ads — Student + Teacher campaigns (v2, 2026-07-26 — Patna-only)

> Two Search campaigns, ₹200/day each (₹400/day total), **geo-locked to Patna city** — this runs
> alongside the offline Patna field campaign (Rohan), not instead of it. Conversion =
> **registration** (a new account created and landing back inside the product), not a click. I
> have no Google Ads API/console access from here, so this doc is the copy-paste spec — you
> publish it in the Google Ads UI. Code-side conversion tracking is wired for both funnels (see
> §4) but the **conversion actions themselves must be created in the Ads console first** — until
> then the tags are inert and the campaigns fly blind.
>
> **Reality check on volume:** Patna-only search volume for these terms is genuinely small —
> likely dozens, not hundreds, of daily searches across all keywords combined. Expect the
> campaigns to under-spend the ₹200/day budget most days (that's fine — it means you're capturing
> close to all the *available* local intent, not that something's broken). Don't be tempted to
> widen geo to "spend the budget" — that defeats the point of aligning with the offline push.

---

## 0. Do this BEFORE turning any campaign on

1. Create the two conversion actions in Google Ads (exact steps in §4).
2. Paste their labels into the two env vars (§4) and redeploy `lms` (bumps the teacher-conversion
   code that just shipped — it isn't live in prod yet).
3. Only then publish/enable the campaigns. If you flip campaigns on first, every early click's
   registration goes untracked and you'll under-count real conversions for however long the label
   is missing.

---

## 1. Campaign A — Student (Search)

**Landing page:** `https://acharya.trigunai.com/exam-prep`
**Budget:** ₹200/day · **Bidding:** start on *Maximize Clicks* (no conversion history yet) →
switch to *Maximize Conversions* once ~15-20 conversions have logged (Ads needs a data floor
before its auto-bidder is reliable — flipping too early just makes it guess).
**Networks:** Search only (uncheck Search Partners + Display to keep budget concentrated at
this size).
**Geo: Patna, Bihar, India — city only.** In Ads location settings, set the **Location options**
to **"Presence: People in or regularly in your targeted locations"** — NOT the default
"Presence or interest." The default also serves people anywhere in India who merely search
*about* Patna, which is exactly the waste you don't want on a ₹200/day budget. Add "Patna" as a
single location (Ads' city boundary already covers the metro area — no need to also add a radius
target unless you later find real intent is coming from just outside the city line, e.g. Danapur,
Phulwari Sharif — add those as separate locations if so).
**Ad schedule:** all days, but weight 4pm–11pm IST (post-school/coaching hours, when students
actually search) if you want to set bid adjustments later.

### Ad groups (keep to 2 for ₹200/day — more groups starves each of clicks)

**Ad group 1 — JEE/NEET test prep**
Keywords (phrase + exact, no broad — broad will burn the budget on irrelevant "results"/"admit
card" traffic):
```
"jee mock test online"
"neet mock test online"
"jee practice questions"
"neet practice questions"
[jee test series free]
[neet test series free]
"jee weak topics"
"neet weak topics"
"jee coaching in patna"
"neet coaching in patna"
"jee test series patna"
```
(The last three are low-volume but high-intent — someone searching "jee coaching in patna" is
comparison-shopping alongside the offline coaching search; geo-targeting already restricts the
whole campaign to Patna, so the un-suffixed keywords above still fire for local searchers who
didn't type the city name — the Patna-suffixed ones just catch the minority who did.)

**Ad group 2 — Class 10/12 boards + Banking**
```
"class 10 practice test"
"class 12 practice test"
"class 10 board exam questions"
"class 12 board exam questions"
"ibps po practice test"
"sbi po practice test"
"rrb exam practice questions"
"banking exam mock test"
"class 10 tuition patna"
"class 12 tuition patna"
"banking coaching patna"
```

**Negative keywords (both ad groups):**
```
free -remove if you want zero-friction clicks... actually KEEP "free" (site legitimately offers
free tier) but exclude:
-jobs -vacancy -recruitment -admit card -result -answer key -syllabus pdf -previous year paper
pdf download -notes pdf -salary
```
(Rationale: "admit card"/"result"/"answer key"/"pdf download" searchers want a government portal
or a static file, not an adaptive test — high clicks, zero registrations.)

### Responsive Search Ad (per ad group — Google mixes these; give it options)

**Headlines** (need 3-15, here are 10 — trim/adjust in console):
```
Find Your Weak Topics Free
Adaptive JEE & NEET Mock Tests
AI Finds What to Revise Next
Free Practice Test — 10 Seconds
JEE, NEET, Class 10 & 12 Tests
Banking Exam Practice Tests
Not Just a Score — a Diagnosis
Start Free, No Payment Needed
Acharya: AI Exam Practice
14-Day Free Trial, Then ₹199/mo
```
(Skipped a "trusted by Patna students" style headline deliberately — you don't have that proof
yet and Ads can disapprove unsubstantiated claims; add it honestly once you have real Patna
users/testimonials.)
**Descriptions** (2-4 needed):
```
Take a short adaptive test in English or Hindi. Acharya finds your exact weak topics from
your answers and tells you what to revise next.
No password, no payment to start. Pick your exam — JEE, NEET, boards, or banking — free.
1,29,000+ verified questions across JEE, NEET, Class 10-12 and banking exams. More added weekly.
```
**Final URL:** `https://acharya.trigunai.com/exam-prep`
**Sitelink extensions:** none needed yet (single-page funnel) — skip rather than send traffic
off the conversion path.
**Callout extensions:** `Free to start` · `No payment required` · `English or Hindi` ·
`14-day trial`

---

## 2. Campaign B — Teacher (Search)

**Landing page:** `https://acharya.trigunai.com/teacher`
**Budget:** ₹200/day · **Bidding:** Maximize Clicks → Maximize Conversions after data floor
(same rule as above).
**Networks:** Search only.
**Geo: Patna, Bihar, India — city only**, same "Presence" setting as Campaign A (§1) — this is
the campaign that pairs most directly with the offline field push, since Rohan can follow up
in person with anyone who converts.

**Targeting intent — this must reach people who ALREADY run a coaching business with students,
not people looking for a teaching job or training.** That distinction drives both the keyword
list and the negatives below — "teacher" alone is too broad (catches job-seekers, B.Ed
aspirants, parents looking for a tutor for their kid). The keywords are built around *running a
coaching operation* (institute, batch, students, classes) rather than the word "teacher" in
isolation.

### Ad group — Coaching/institute test creation

```
"online test creation for coaching classes"
"test generator for teachers"
"create online test for students"
"jee neet test generator"
"coaching institute test software"
"question bank for coaching classes"
"coaching institute in patna"
"jee neet coaching institute patna"
"manage students test coaching class"
[online test maker for teachers]
[class test creation tool]
[coaching institute software patna]
```
**Negatives:**
```
-jobs -vacancy -teacher training -how to become a teacher -salary -recruitment -b.ed -tuition
job -home tutor job -teaching job -private tutor for my child -tutor near me
```
(The last two matter here specifically: "tutor near me" / "private tutor for my child" is a
*parent* looking to hire a tutor, not an institute owner looking for software — different buyer,
wrong landing page.)

### Responsive Search Ad

**Headlines:**
```
Create a JEE/NEET Test in Seconds
Acharya Tests & Tracks for You
Share One Link With Students
See Who's Weak in Which Topic
No Password, No Payment to Start
Free Setup for Coaching Classes
AI Test Generator for Teachers
Track Every Student Automatically
For Patna Coaching Institutes
```
**Descriptions:**
```
Create a JEE or NEET test in seconds, share one link with your students, and see exactly who
is weak in which topic — automatically.
Built for coaching classes and institutes. No password, no payment to start.
```
**Final URL:** `https://acharya.trigunai.com/teacher`
**Callout extensions:** `No payment to start` · `Instant setup` · `Auto weak-topic tracking`

---

## 3. What counts as a conversion (confirmed with Deepak)

- **Student:** a new account created via `/exam-prep` (email or Google) — fires once, the first
  time that student lands on `/exam-prep/test?new=1` or `/exam-prep/dashboard?new=1`. **Already
  wired in code**, inert only because the conversion action label isn't created yet (§4).
- **Teacher:** a new account created via `/teacher/signup` (email or Google) — fires once, the
  first time that teacher lands back on `/teacher?new=1`. **Wired today** (2026-07-26) — not yet
  deployed to prod, see §4 step 3.

---

## 4. Conversion action setup (do this first, in Google Ads UI)

Account already has a linked conversion ID: **`AW-18339354528`** (already in code,
`ADS_CONVERSION_ID` in `lms/app/config.py`).

**Steps (repeat twice — once per action):**
1. Google Ads → Goals → Conversions → **+ New conversion action** → Website.
2. If the site isn't already verified/tagged, it already is (the `AW-18339354528` snippet is
   live in the LMS templates) — use "I'll add the tag myself" / skip re-tagging.
3. Category: **Sign-up**. Name: `Student free signup` / `Teacher signup`. Value: don't assign a
   value yet (or use "count all" with no fixed ₹ value — you don't have LTV data yet). Count:
   **One** (per the "fires once on `new=1`" design — don't count "every").
4. Click-through conversion window: 30 days is fine as a default.
5. Save → Ads shows a **conversion label** (a string like `AbCdEfGhIj`) attached to
   `AW-18339354528/<label>`. Copy that label.

**Then wire it into the app (per action):**
```bash
cd lms
AZ=~/Library/Python/3.9/bin/az
$AZ account set --subscription cb656d95-2f68-469f-b2b5-aee1ac1be625
$AZ containerapp update -n lms -g trigunai-video-creator \
  --set-env-vars STUDENT_SIGNUP_CONV_LABEL=<label from step 5> \
                 TEACHER_SIGNUP_CONV_LABEL=<label from step 5>
```
Then redeploy the current image (per `lms/DEPLOY.md`) so the teacher-side code from today ships:
```bash
$AZ acr build --registry trigunaicr --image lms:vNEXT --file Dockerfile .
$AZ containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vNEXT
```

**Verify before spending real budget:** sign up as a fresh test student and a fresh test teacher
(use throwaway emails), confirm each lands on `?new=1` and Chrome DevTools → Network shows a
request to `googleads.g.doubleclick.net` firing on that page load. If it doesn't fire, the
campaigns will run with zero conversion data and Ads' bidding has nothing to learn from.

---

## 5. Still open — need your call before I mark this ready to publish

- ~~Geo targeting~~ **RESOLVED 2026-07-26: Patna city only, both campaigns, Presence-only
  targeting** (§1, §2).
- **Who clicks Publish** — I have no Google Ads tool access from this session. Either paste
  this spec into the console yourself, or if you're logged into Google Ads in your real Chrome
  and want me to click through it with you (stopping before anything spends), say so and I'll use
  the Chrome control tools — I still won't touch billing/payment details.
- Exam coverage note for both ad groups: copy above reflects **JEE, NEET, Class 10/12,
  Banking** (what's live now per your message). When more exams ship, add ad groups rather than
  cramming more keywords into existing ones — keeps Quality Score high per group.
- **Coordinate with the offline campaign**, per Deepak's framing ("we are also doing offline
  campaign there") — worth a short WhatsApp-announce or note to Rohan (`teacher_gtm/`) so a
  teacher who converts via this Google Ads campaign gets folded into his field follow-up list
  rather than sitting as an unattended online lead. Consider whether the online teacher landing
  page should surface Rohan's contact for a Patna-local human touch, given B2B in this market
  closes on relationship, not self-serve (per `project-direction-acharya-b2b` memory).
