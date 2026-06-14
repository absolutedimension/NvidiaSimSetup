# Landing Page — Courses Section + Registration (handoff addendum)

> **Read `HANDOFF.md` first** (brand, tone, funnel, guardrails). This addendum **adds a Courses
> showcase + registration flow** on top of the existing subscribe-only page.
> Prepared 2026-06-13. Owner: Deepak. Data lives in **`courses.ts`** (in this folder).

---

## 1. What changed vs the original handoff

The original page had ONE job: subscribe to Substack, with three teaser course cards. We're
**upgrading the Courses block** so a visitor can read the full curriculum and **register** for a
course. Two intentional updates to `HANDOFF.md`:

- **§2 (single funnel rule):** now there are **two** CTAs by intent — **Subscribe** (soft, the
  series funnel, stays everywhere) and **Register / Reserve your seat** (hard, per course). Keep
  them visually distinct; don't add a third competing action.
- **§7 (no pricing / waitlist only):** we now show course detail + a **Register** button. Still
  **no price numbers on the page yet** unless Deepak provides a payment link — "Reserve your seat"
  / "Join the waitlist" capture intent first. Everything else in §7 still holds: **no invented
  student counts, no testimonials, no "trusted by," no fake logos.**

Everything else in `HANDOFF.md` (brand tokens, hero, series block, who's-teaching, footer, deploy)
is unchanged.

---

## 2. The data — `courses.ts`

All four courses are fully described in **`courses.ts`** as a typed `COURSES: Course[]`. Each course
has: `badge`, `status`, `accent`, `title`, `tagline`, `fromEpisodes`, `level`, `modulesCount`,
`hours`, `outcome`, `forWho`, `prerequisites`, and a `modules[]` array of `{ n, title, brief }`.

**Render from this array — do not hardcode course copy in JSX.** When Deepak edits a module brief,
he edits `courses.ts` only.

Helper exports to use:
- `registerUrl(course)` → the destination for that course's Register button.
- `ctaLabel(course)` → `"Reserve your seat"` (flagship/open) or `"Join the waitlist"` (waitlist).
- `REGISTER_URLS` / `SUBSTACK_URL` → the config object Deepak fills (see §5).

The four courses and their launch state:

| Course | `status` | Badge | CTA |
|---|---|---|---|
| Build & Ship Your First VR/MR App | `flagship` | FLAGSHIP | Reserve your seat |
| Build Agentic AI Systems | `open` | LAUNCHING JULY 18 | Reserve your seat |
| Machine Learning & Its Math | `open` | LAUNCHING JULY 18 | Reserve your seat |
| Physical AI — Train a Robot in Simulation | `waitlist` | COMING SOON | Join the waitlist |

---

## 3. UI to build

Replace the original three-card Courses block (§4 Block 3 of `HANDOFF.md`) with this.

### A. Courses overview section ("From watching to building")
- Keep the heading + intro line from `HANDOFF.md` Block 3.
- Render **one card per `COURSES` entry** (4 cards, responsive grid: 1 col mobile / 2 col tablet /
  2–4 col desktop). Card shows: `badge` pill (color = `accent`), `title`, `tagline`, a meta row
  (`level` · `modulesCount` modules · `hours`), and two actions:
  - **primary** — `ctaLabel(course)` → `registerUrl(course)` (new tab), button tinted with `accent`.
  - **secondary** — `View curriculum` → opens the detail view (B).
- The flagship card (`status: 'flagship'`) is visually emphasized (e.g. wider, gold border/glow).

### B. Course detail view (modal or route — your call)
Opens when "View curriculum" is clicked. Mobile-first; a full-screen modal or a `/courses/:id` route
both fine. Contents, in order:
1. Badge + title + tagline.
2. **At-a-glance row:** Level · Modules · Hours · `fromEpisodes` (the funnel tie-back).
3. **What you'll walk away with** — `outcome`.
4. **Who it's for** — `forWho`.  ·  **What you need** — `prerequisites`.
5. **Curriculum** — the `modules[]` list: each row = `n`. **title** + `brief` underneath. This is
   the "full table of index" — the core of the page. Make it scannable (numbered, generous spacing).
6. **Register CTA** repeated at the bottom: `ctaLabel(course)` → `registerUrl(course)`.

### C. Keep the rest of the page
Hero, the two YouTube embeds (series block), who's-teaching, final Subscribe CTA, footer — all stay
exactly as in `HANDOFF.md`. The Subscribe button stays in the sticky nav.

---

## 4. Registration flow (no backend)

"Register" must capture a lead without a backend or login. In priority order — pick what's wired:

1. **Per-course form (recommended for launch).** `registerUrl(course)` points to a free
   **Tally** or **Google Form** — fields: name, email, which course (prefilled), "Do you have a Meta
   Quest? (yes/no)", optional "anything you want to learn?". Opens in a new tab. Zero cost, captures
   intent + email, proves demand before any video is recorded.
2. **Paid reservation.** Swap `registerUrl` to a **Razorpay Payment Link** or **Gumroad** product so
   the reserve is a real (possibly discounted) pre-payment. Use this only once Deepak decides to take
   money — a paid pre-enroll is the strongest possible demand signal.
3. **Fallback (default in code).** Until forms exist, every Register button falls back to
   `SUBSTACK_URL` (subscribe + reply "RESERVE <course>"). The page works today with no setup.

Either way: **no on-page password/login, no checkout you have to build.** External form or link only.

---

## 5. Config Deepak fills (one place)

In `courses.ts`, bottom block:

```ts
export const SUBSTACK_URL = 'https://trigunai.substack.com/subscribe';
export const REGISTER_URLS = {
  VR:       SUBSTACK_URL,  // → VR/MR reserve form or payment link
  AGENTIC:  SUBSTACK_URL,  // → Agentic reserve form
  ML:       SUBSTACK_URL,  // → ML reserve form
  ROBOTICS: SUBSTACK_URL,  // → Robotics waitlist form
};
```

Plus the existing `YT_EP1_ID` / `YT_EP2_ID` in `App.tsx` for the series embeds. **All five live YouTube
episodes are public now (EN + HI)** — Deepak can wire more than two embeds if desired, but two in the
series block is enough; the rest live on YouTube.

---

## 6. Acceptance criteria (additive to HANDOFF.md §8)

- [ ] Courses section renders all 4 cards from `COURSES` (no hardcoded course copy in JSX).
- [ ] Each card: badge (accent-colored), title, tagline, meta row, Register + View-curriculum actions.
- [ ] Flagship (VR/MR) is visually emphasized.
- [ ] Detail view shows the full module index (`n` · title · brief) plus outcome / who-for / prerequisites.
- [ ] Register buttons use `registerUrl()` + `ctaLabel()`; waitlist course says "Join the waitlist".
- [ ] Subscribe (Substack) still present in nav + final CTA; two CTA intents stay visually distinct.
- [ ] No price numbers unless a payment link is set; no invented social proof (HANDOFF.md §7).
- [ ] Builds to static `dist/`, deployable to trigunai.com, mobile-first, no console errors.

---

## 7. What's in the bundle now

```
landing-page-handoff/
├── HANDOFF.md              ← original spec (brand, funnel, hero, series, deploy) — read first
├── COURSES_HANDOFF.md      ← this file (Courses showcase + registration)
├── courses.ts              ← the 4-course data the Courses section renders from
├── REFERENCE_App.tsx       ← working React/Vite/Tailwind/Framer reference page
├── REFERENCE_worldview.html← series visual-world reference (tone only)
└── assets/                 ← logos, favicon, hero
```

*Full human-readable course indexes (same content, prose form): `../COURSE_INDEXES.md`.*
*Strategy / why these courses: `../COURSE_CATALOG.md`.*
