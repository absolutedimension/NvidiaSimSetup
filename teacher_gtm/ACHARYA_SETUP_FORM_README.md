# Acharya Teacher Setup Form — how to create & send it

Intake form to send a teacher **after they say yes**, collecting everything the
`acharya-technology-transfer` skill needs to stand up their branded tutor + list their course +
enrol their students. One submission → I can provision with no back-and-forth.

## Create it (30 seconds, one time)
1. Open **https://script.google.com** → **New project**.
2. Delete the sample, paste all of **`ACHARYA_SETUP_FORM.gs`**.
3. Click **Run ▶** → authorize with your Google account when asked.
4. Open **Execution log** — it prints two links:
   - **Share link** → this is what you send the teacher (WhatsApp/email).
   - **Edit link** → open to tweak/brand it, add your logo header, or link a responses Sheet.
5. In the form editor: **Responses → link to Sheets** so every teacher's answers land in one sheet.

You only build it **once**; reuse the same form (or link) for every teacher.

## The questions (5 short sections, ~5 min for the teacher)
1. **About you** — coaching name*, your name*, WhatsApp*, city, short branding name.
2. **What you teach** — subject/exam*, classes*, board, language*, **syllabus in teaching order***, syllabus link, teaching style.
3. **Your students** — total count*, trial count (≤10)*, **trial list: Name + WhatsApp, one per line***, list link, do they have WhatsApp*.
4. **Your branding** — logo link, brand colours, tagline, own domain. *(all optional — we start with your name)*
5. **Go-live** — shared vs own number*, start date, **14-day trial → ₹4,999/mo consent***, anything else.

(* = required)

## How answers map to setup
| Form answer | Provisioning target |
|---|---|
| Coaching name, short name | `tenants/<slug>.json` → name, slug, brand + tutor self-intro |
| Subject, classes, syllabus order, style | course concept-bank (`courses/<slug>.json`) → name, `order`, `intro` |
| Trial student list | `tenants/<slug>.json → students[]` → enrolment |
| Logo, colours, tagline, domain | `tenants/<slug>.json → brand / web` (web branding = trial fast-follow) |
| Shared vs own number | `tenants/<slug>.json → whatsapp.mode` |
| Start date, consent | `tenants/<slug>.json → trial.start/end`, status |

## Two caveats (by design)
- **File uploads:** Apps Script can't create native file-upload questions, and uploads force the
  teacher to sign in with a Google account (friction). So logo/syllabus are **"share a link or send
  on WhatsApp"** text fields. If you want true uploads, add a File-upload question manually in the
  editor — just know it requires teacher sign-in.
- **Student list:** collected as a paste-one-per-line paragraph (works for ≤10 trial students). For
  big rosters later, ask for a Google Sheet link instead.
