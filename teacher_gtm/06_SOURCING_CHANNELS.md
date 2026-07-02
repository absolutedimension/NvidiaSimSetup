# Where to find the teachers — sourced channel map (2026-07-02)

> From a 5-angle deep-research run (21 sources fetched, 69 claims extracted).
> ⚠️ Honesty note: the adversarial-verification stage hit a session limit, so claims below
> are **sourced but machine-unverified** — each is a directory-level fact you can confirm
> in 2 minutes by opening the link. Numbers marked "(claimed)" are the platform's own.

## ⚡ The compliance rule that shapes everything

**WhatsApp's Business Messaging Policy requires opt-in before a business messages anyone.**
Cold-WhatsApping numbers scraped from Justdial/Google Maps/Sulekha **violates the policy**
and risks the WABA number we just fixed. ([policy](https://whatsappbusiness.com/policy/))
→ **The move is: CALL the listed business number** (businesses list numbers to receive
calls — that's normal conduct), pitch, and get their WhatsApp opt-in on the call.
Never bulk-blast first-touch WhatsApp.

---

## TIER 1 — use these to land 10 conversations/week (start here)

### 1. Google Maps (free, phone numbers public, owners answer)
Search per city: "tuition centre", "NEET coaching", "SSC coaching", "railway exam coaching",
"class 12 biology tuition" + [Mumbai / Patna / your locality]. Every listing = name, phone,
address, reviews (review count ≈ student volume — filter for the small ones, 10–200 students).
- Response quality: **best of all channels** — you're calling a business owner on the number
  they published for business.
- Scale option: Apify's Google Maps scraper bulk-extracts phone/website/address
  ([apify.com/compass/crawler-google-places](https://apify.com/compass/crawler-google-places))
  — fine for building a CALL list; do NOT feed it into WhatsApp blasts.

### 2. Justdial — per-city exam-coaching categories
Category pages per city, e.g. NEET Tutorials (category `nct-11037560`, ~909 listings in
Hyderabad alone), IIT-JEE (`nct-10502810`), plus SSC/banking/railway categories. Phone
numbers reachable (Justdial connects/reveals). Same play: call as a business caller.

### 3. Sulekha — entrance-exam coaching directory
[sulekha.com/entrance-exam-coaching](https://www.sulekha.com/entrance-exam-coaching/) covers
the full target spectrum (NEET/medical, engineering, bank/SSC/railways). Listing phone
numbers are directly visible + WhatsApp chat on listings; 15,000+ listings claimed in Mumbai
alone. Skew: centres more than solo teachers — qualify for the small ones.

### 4. Facebook groups — coaching OWNERS gather here (warm, slower)
- **"ALL India Coaching/tuition Classes Association"** — explicitly for coaching/tuition
  class owners ([facebook.com/CoachingClassesAssociation](https://www.facebook.com/CoachingClassesAssociation/))
- **"Classplus-Lite Teacher's Community"** ([facebook.com/groups/classpluslite](https://www.facebook.com/groups/classpluslite/))
  — teachers already paying for digital tools = pre-qualified believers
- **"Indian Teachers Group"** ([facebook.com/groups/indianteachersgroup](https://www.facebook.com/groups/indianteachersgroup/))
- Search FB for: "tuition teachers India", "coaching class owners", "[city] tuition"
**Play:** join, give value for a week (answer a question, share the free pilot as help not
ad), then DM engaged members. Group-spam gets you banned; one useful post → inbound DMs.

### 5. Small YouTube educators (highest-fit, underrated)
Search YouTube: "class 10 maths in hindi", "NEET biology chapter", "SSC maths trick" —
filter for channels with **1k–50k subs** (big enough to be serious, small enough to be
independent). They already believe in digital teaching, already have a student audience,
and their **email is in the channel About page** (legit contact route). Pitch: "your own AI
tutor for your subscribers, under your brand."

---

## TIER 2 — secondary (use for names/intel, not primary volume)

| Source | What it gives | Catch |
|---|---|---|
| **TeacherOn** ([teacheron.com/tutors/tutors-in-india](https://www.teacheron.com/tutors/tutors-in-india)) | 135k+ (claimed) browsable tutor profiles — exactly the segment (Class 9–12, NEET, PCB tutors visible); no commission, doesn't lock off-platform contact | No phone/email on profiles — contact via platform messages (vendor pitches may annoy) or use names to find them on Google/LinkedIn/Instagram |
| **UrbanPro** ([urbanpro.com](https://www.urbanpro.com/)) | 7.5 lakh+ (claimed) tutors, full exam coverage incl. SSC/banking/railway | Contact gated behind **paid student-lead system** — pitching via fake student leads = ToS violation + burns the teacher's paid credits (terrible first impression). Use as segment intel only |
| **LinkedIn** | "tuition teacher / coaching institute owner [city]" search; InMail/connect | English-speaking skew; slower |
| **Superprof / MyPrivateTeacher / TheTuitionTeacher** | Smaller listing pools, same model as TeacherOn | Lower volume; same contact-gating |
| **Telegram exam-prep teacher channels** | Exist, active | Research couldn't verify specific channel names — scout manually via Telegram search "teachers India", "coaching owners" |

## ❌ Not viable (don't spend hours here)

- **Vedantu / Unacademy educator sides** — Vedantu employs teachers directly (no public
  independent-tutor profiles); Unacademy educators are platform-contracted. Not your segment.
- **Teachmint** — pivoted to school-digitization software in Apr 2023, discontinued its
  tutor product (Teachmore). Weak channel AND weakened competitor.
- **Coaching Federation of India** — website offline (hosting suspended) as of 2026-07-02. Dead.

## 🥊 Competitor read (from the same research)

**Classplus** = the proof AND the benchmark: 1 lakh+ (claimed) educators across 1,100–3,000+
cities, core product = white-label app "under the teacher's brand" — **teachers demonstrably
PAY for under-their-brand tools**, which validates your thesis. Their realistic Year-1 cost
is reported at **₹4–11 lakh with 12-month lock-in** — your ₹4,999/mo flat, no lock-in, on
WhatsApp (no app for students to install) is a clean wedge underneath them. Their pain
points (cost, lock-in, unused features) are your pitch ammunition — and their Facebook
community is literally a sourcing pool (Tier 1 #4).
**Teachmint's retreat** is also a caution worth holding honestly: they killed their tutor
product because it "wasn't generating sustainable revenue" — small-tutor willingness-to-pay
is real but thin. That's exactly what the 3-week test measures.

---

## The weekly operating recipe (10 conversations/week)

1. **Monday (1 hr):** pull 30 numbers — Google Maps + Justdial + Sulekha for Mumbai/Patna
   localities + 1 exam niche. Paste into 03_CONVERSATION_LOG.md as "queued".
2. **Tue–Thu (calls):** dial the 30. Expect ~1/3 to answer and talk → ~10 conversations.
   Script = 02_CONVERSATION_SCRIPT.md. Opt-in to WhatsApp captured on the call.
3. **Continuous (30 min/day):** 1 valuable post/comment in the FB groups; 3 YouTube-educator
   emails/week; work the 2 inbound leads + ask every call for 1 referral.
4. **Never:** bulk WhatsApp to scraped numbers; fake student leads on UrbanPro/TeacherOn.
