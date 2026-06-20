# Landing Page — "For Engineering Students" Section + Registration Handoff

> **For the landing-page agent.** Add a dedicated section + a student path in the registration flow,
> aimed at engineering-college students. Self-contained — you don't need any other repo. Prepared
> 2026-06-18. Owner: Deepak Kumar. Where this and an older file disagree on the student section, **this wins.**
> Companion strategy (optional, not required to build): `../STUDENT_CAMPAIGN.md`.

---

## 1. What to add and why

Engineering students (3rd / final year) have a **forced need**: a college **project**, a mandatory
**internship / industrial training**, and a **placement edge** — and most get hollow versions of all
three. We sell a real one. Add two things to the site:

1. **A new section** on the page: *"For Engineering Students"* (or "Final-Year Project + Internship").
2. **A student path in the registration flow** — when someone identifies as a student, capture a few
   student fields and tag them so the admin dashboard can segment student leads.

**The promise to land (the spine of all copy):** at the end, the student walks away with three things —
> **Knowledge colleges don't teach · a working app they built & can demo · a real certificate.**

This maps to the existing **VR/MR flagship** course (no new course needed) — it's the *same* cohort,
framed for the student buyer.

---

## 2. The section — ready-to-use copy

**Eyebrow:** `FOR ENGINEERING STUDENTS`

**Headline:**
> Make your final-year project something you're actually proud of.

**Subhead:**
> Don't submit a bought project and a hollow internship PDF. In 8 weeks, build and ship a real VR/MR
> app — with an AI coding partner writing most of the code — and learn the things your college syllabus
> never gets to.

**The three outcomes (render as 3 cards / icons):**
| | |
|---|---|
| 🧠 **Knowledge colleges don't teach** | Modern VR/AI build workflow, an AI coding partner, real industry tooling (GPU, Unity, Isaac) — not 2015 syllabus theory. |
| 📱 **A working app you built** | A real, demoable VR/MR app — submit it as your major/final-year project, show it in placements. |
| 📜 **A real certificate** | A genuine training / internship-completion certificate + a project-completion letter for the work you actually did. |

**Trust line (use verbatim — it's the differentiator):**
> Mentored live by a founder with a VR app **live on the Meta Quest store**. You'll ship your own.

**Offer line:**
> 8-Week VR Developer Internship + Live Project · ₹35,000 (installments available) · limited seats ·
> **starts with a free intro class.**

**Primary CTA button:** `Join the free intro class` → routes to the registration flow (§4), student path.
**Secondary link:** `See what you'll build` → the VR/MR course detail.

---

## 3. HONESTY GUARDRAILS — do not cross (legal + brand)

Put these limits in the copy and the FAQ. Overclaiming here breaks trust with the parents who pay.

- ✅ "a real **training / internship-style completion certificate**" + "**project-completion letter**"
- ❌ NOT "AICTE-approved", NOT "university credit", NOT "your college will accept it", NOT "guaranteed
  placement", NOT "industry-recognized certification".
- Include this exact disclaimer near the CTA / in the FAQ:
  > *This is a private training program. The certificate reflects real work you complete; whether your
  > college accepts it for project/internship credit is your institution's decision. No placement is guaranteed.*

**FAQ block to add:**
- *"Can I submit this as my college project?"* → Yes — you build a real app that's yours to submit.
  Acceptance for credit is your college's call; most accept a genuine project + training certificate.
- *"Is the certificate official/AICTE?"* → It's a genuine training/internship-completion certificate
  from Trigunaï for real work done. It is not a university or government accreditation.
- *"I can't pay ₹35k at once."* → Installments are available. Start with the free class.
- *"Do I need to know how to code?"* → No deep coding needed — you'll direct an AI coding partner. Basic
  programming familiarity helps.

---

## 4. Registration flow — the student path

When a visitor clicks any student CTA (or toggles **"I'm a student"** on the existing register form),
show the student path and capture these fields (all on top of the existing email capture):

| Field | Type | Required | Purpose |
|---|---|---|---|
| Email | email | ✅ (existing) | the list |
| Name | text | optional | personalization |
| **I'm a student** | toggle/checkbox | — | flips the form into student mode + sets the segment tag |
| **College / University** | text | optional | institutional signal (feeds the Q3 college outreach) |
| **Year** | select (2nd / 3rd / Final / Passout) | optional | qualify the lead |
| **Branch** | text/select | optional | qualify |
| Interest | hidden = `VR/MR Internship + Project` | auto | so the close knows the offer |

**On submit:**
- Capture as a normal signup, **tagged `segment=student`** (and the student fields) so the **admin
  dashboard can show student class-requests separately** from general ones. This segmentation is the
  whole point — Deepak needs to see student leads vs. general leads.
- Register it as a **free-class request** (same mechanism as the rest of the site — this is the
  conversion event; there is NO online checkout). Payment is handled by Deepak personally after the
  free class (company account + a payment link), per the marketing plan.
- Fire the existing welcome email; if the student template is wired server-side, prefer the student
  version (copy mirrors `../marketing/emails/student_internship_invite.html`).

**Keep it light:** email is the only required field. The student fields are optional qualifiers — do
not gate the signup behind them, or you'll lose leads.

---

## 5. Placement & visual notes

- Section placement: after the main course showcase, as a distinct, clearly-labeled band so a student
  scanning the page lands on it fast. A student arriving from a student-channel ad should recognize
  "this is for me" within one screen.
- Mobile-first (students are on phones). The 3 outcomes must read cleanly stacked on mobile.
- Reuse existing brand tokens / accent palette (see `HANDOFF.md` §3 / `courses.ts`). Suggested accent:
  the VR/MR course accent so the section visually ties to that course.
- Optional: a short looping clip / screenshot of the live Quest app as the section's hero visual
  (proof-of-shipping). Ask Deepak for the asset; don't fabricate one.

---

## 6. Data contract (so the dashboard segments correctly)

Whatever store the registration writes to, ensure each student signup carries:
```json
{
  "email": "...",
  "name": "...",
  "segment": "student",
  "college": "...",
  "year": "Final",
  "branch": "...",
  "interest": "VR/MR Internship + Project",
  "source": "<utm/source if available>",
  "requested_class": true
}
```
`segment` + `requested_class` are the two fields the admin dashboard's **CLASS REQUESTS** metric and
the student/general split depend on. Don't drop them.

---

## 7. Definition of done
- [ ] "For Engineering Students" section live on the page with the §2 copy + 3 outcomes + honest disclaimer.
- [ ] Student path in the register flow (toggle + optional fields), email-only required.
- [ ] Student signups tagged `segment=student` and counted as a class request in the admin dashboard.
- [ ] Welcome email fires (student version if available).
- [ ] No prohibited claims anywhere on the page (re-check §3 before shipping).

*Questions → Deepak. The free intro class is the only conversion event; the page's job is to get a
student to request it and to tag them as a student. Nothing more.*
