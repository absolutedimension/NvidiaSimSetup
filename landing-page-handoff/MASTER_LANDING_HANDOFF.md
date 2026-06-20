# TrigunAI — MASTER Landing-Page Handoff (the whole site)

> **Read this first.** Single source of truth for the public site. Consolidates every sub-handoff in
> this folder + the new pricing model + the 2 new courses + new video assets. Updated 2026-06-20.
> Owner: Deepak Kumar (founder). For the landing-page coding agent.

This bundle is self-contained. Sub-handoffs hold the deep detail; this file is the index + what's new.

| Need | Read |
|---|---|
| Brand voice, thesis (3 layers), personas, the lens-not-proof stance | `BRAND_HANDOFF.md` |
| Home-page structure + exact copy + reference React app | `HANDOFF.md` + `REFERENCE_App.tsx` |
| Course catalog data (the render source) | `courses.ts` (+ human twin `COURSE_INDEXES.md`) |
| Per-course detail (Video Factory / Music Factory) | `COURSE_VIDEO_FACTORY_HANDOFF.md` · `COURSE_MUSIC_FACTORY_HANDOFF.md` |
| Pricing + duration logic (the *why* behind the numbers) | `../COURSE_PRICING_MODEL.md` |
| Student dashboard / logged-in section | `STUDENT_SECTION_HANDOFF.md` |

---

## 1. What you're building (the whole)

Three surfaces, one funnel:

1. **Home (`trigunai.com`)** — the free funnel. ONE job: visitor → **email subscriber (Substack)**.
   Series-led: "AI is the Universal Mind." (Spec + copy = `HANDOFF.md`; that copy is still current.)
2. **Courses (`/courses` + per-course detail)** — the catalog of 6 courses. CTA = **Register / Join the
   waitlist** (free-now funnel). Prices shown on detail pages per §4 rule.
3. **Register / dashboard (`learn.trigunai.com`)** — magic-link signup → student dashboard (already built,
   separate repo). New registrants land here. See `STUDENT_SECTION_HANDOFF.md`.

**The golden funnel:** *Watch (free series) → Subscribe (email) → Register interest (waitlist) → Pay
(live cohort).* Free to understand, paid to transform.

---

## 2. The funnel + price-display rule (important)

- **Home page:** keep ONE primary CTA — **Subscribe / Get the next episode** (→ Substack). Course cards
  there use **"Join the waitlist / Register interest."** **No prices on the home page.**
- **Course detail pages:** *may* show the **price + EMI + founding-cohort offer** (you now have a real
  model — §3). Deepak's toggle: **`SHOW_PRICES`** — until the first cohort actually pays, keep it `false`
  (waitlist only); flip to `true` once willingness-to-pay is validated. Build both states; default `false`.
- **No checkout on the site.** Payment for the live cohort is **direct bank transfer + email receipt**
  (see §5) — not an on-page gateway. The CTA captures the lead; the close happens over email/WhatsApp.

---

## 3. The full course catalog (6 courses) — with pricing + duration

Pricing rationale + market research → `../COURSE_PRICING_MODEL.md`. Every live course also has a cheap
**recorded self-paced** tier (the passive floor) and optional **founding-cohort** intro price.

| # | Course | Status | Shape · Duration | **Cohort price** | EMI | Recorded | CTA |
|---|---|---|---|---|---|---|---|
| 1 | **Build & Ship a VR/MR App** ⭐ | Flagship · 9/11 modules public | Live cohort · 8 wk | ₹34,999 | 3×₹11,999 | ₹5,999 | Reserve seat |
| 2 | **Build Agentic AI Systems** | **Live · Cohort 1 running (starts 26 Jun)** | Live cohort · 3 mo | **₹35,000** (locked) | 3×₹12,000 | ₹4,999 | Reserve seat |
| 3 | **Machine Learning & Its Math** | Drip-launch | Live cohort · 10 wk | ₹29,999 | 3×₹9,999 | ₹4,999 | Reserve seat |
| 4 | **Physical AI — Train a Robot** | Post-launch | Cohort + hardware · 8 wk | ₹49,999 | 4×₹12,999 | — | Join waitlist |
| 5 | **Build Your AI Video Factory** 🆕 | Register interest | Intensive · 15–21 days | ₹17,999 (founding ₹12,999) | 2×₹9,499 | ₹3,999 | Join waitlist |
| 6 | **Build Your AI Music Factory** 🆕 | Register interest | Intensive · 15–21 days | ₹17,999 (founding ₹12,999) | 2×₹9,499 | ₹3,999 | Join waitlist |

**Plus — feeder workshops:** ₹1,999–₹4,999 weekend live workshops ("Build your first AI agent in a
weekend," "Make your first AI song") that upsell into the cohorts. List under a "Workshops" strip, optional.

**Card copy lives in `courses.ts`.** Courses 5 & 6 objects are in their respective handoffs (§3 of each) —
paste them in, add `registerKey` `'VIDEO'` and `'MUSIC'` + their waitlist URLs.

**Status badges:** Flagship · Live now · Drip · Register interest · Post-launch. Honest — only Agentic is
*Live now* (real cohort). Don't badge anything "best-selling" / with counts (§7).

---

## 4. Course detail page (template)

Each course card → a detail view rendering from `courses.ts`:
- Hero: title · tagline · status badge · **price block** (gated by `SHOW_PRICES`) with cohort / EMI /
  recorded / founding-offer, else "Join the waitlist."
- **What you build · Who it's for · What you need · Outcome** (all in `courses.ts`).
- **Curriculum** — the module list (`modules[]`). For Courses 5 & 6 use the 15-day tables in their handoffs.
- **Who's teaching** — the credibility block (reuse `HANDOFF.md` Block 4).
- A **teaser video** where one exists (§6).
- CTA repeated: Register / Join waitlist (→ register URL or Substack fallback).

---

## 5. Registration + payment flow (current reality)

- **Register interest / waitlist** = email capture (Substack or the learn.trigunai.com magic-link signup).
- **Enrolment (live cohort)** = **direct bank transfer**, no gateway:
  1. Lead registers / replies → gets the **Enrolment & Payment PDF** (bank details: TrigunAI Innovations
     Pvt Ltd · HDFC · A/c 50200088377205 · IFSC HDFC0002643) — *don't put the account on a public page.*
  2. Pay in full or first EMI **on/before the first session** → **email the receipt** → seat confirmed.
  3. Onboarding: starter materials + WhatsApp group + (for cohorts) GPU access.
- This is the model proven with **Agentic Cohort 1** (3 students registered). Reuse it for every course.

---

## 6. Content assets (use these on the site)

- **Free series episodes** (YouTube, EN + HI) — the home-page embeds. Ep 1 (Attention), Ep 2 (Learning
  Loop) currently specced; more episodes exist — embed the latest 2–3.
- **"What is an AI Agent?" perspective videos** 🆕 (in `course_assets/intro_out/`) — faceless, narrated,
  captioned. Perfect as **teasers on the Agentic course detail page** and as social/funnel clips:
  - `What_is_an_AI_Agent_v2.mp4` (5-level montage, 77s) — great hero teaser for the Agentic page
  - `What_is_an_Agent_School.mp4` / `_College.mp4` / `_Graduate.mp4` — the "explain at your level" set
- **Logo:** crisp mark at `course_assets/logo/trigun_mark2.png` (the clean triskelion) + wordmark in HTML;
  older `assets/trigunai_logo*.png` still fine for the existing header.

---

## 7. Brand + guardrails (do NOT)

Brand tokens, voice, thesis-at-3-layers, personas → `BRAND_HANDOFF.md`. The hard rules:
- **One primary CTA on home** (Subscribe). Don't dilute.
- **No inflated claims / fake proof** — no student counts, testimonials, "trusted by", "best-selling",
  revenue. Only Agentic is a *live* cohort; say nothing you can't defend.
- **No prices on the home page**; detail-page prices gated by `SHOW_PRICES` (default off until validated).
- **Wellness copy** (Music Factory 432Hz/focus) = "may support focus/relaxation," **never "heals"/medical**.
- **Courses are taught, not sold as done-for-you services** (Video/Music factories are *training*, not SaaS).
- **No on-page checkout** — bank transfer + email receipt (§5).
- Mobile-first, fast, accessible, static (no backend on the public site).

---

## 8. Integrations (one config object)

```
SUBSTACK_URL        = "https://trigunai.substack.com/subscribe"
LEARN_URL           = "https://learn.trigunai.com"          // register / dashboard
YT_EP1_ID / EP2_ID  = "..."                                  // home embeds
REGISTER_URL_VR / AGENTIC / ML / ROBOTICS / VIDEO / MUSIC = "..."  // per-course waitlist (Substack fallback)
SHOW_PRICES         = false                                  // flip true after first paid cohort
```

## 9. Build order for the agent
1. Home page from `HANDOFF.md` + `REFERENCE_App.tsx` (copy is current) — ship this first.
2. `/courses` grid + detail pages from `courses.ts` (add Courses 5 & 6 objects + the VIDEO/MUSIC keys).
3. Wire the price block (gated by `SHOW_PRICES`) + the perspective-video teasers on the Agentic page.
4. Register CTAs → `LEARN_URL` / waitlist URLs.
5. Acceptance: `HANDOFF.md` §8 + prices match §3 + no guardrail violations (§7).

---

## 10. Status snapshot (for honesty on the page)
- **Live now:** Agentic Cohort 1 (starts 26 Jun) · VR/MR (9/11 modules public) · free series (EN+HI).
- **Waitlist / coming:** ML, Physical AI, Video Factory, Music Factory.
- **0 paid enrollments cleared** as of this handoff — so keep `SHOW_PRICES=false`, waitlist-first, until
  the first payment lands. The page sells the *waitlist*, not a price, until then.
