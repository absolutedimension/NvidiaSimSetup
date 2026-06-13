# Landing Page — Build Handoff (TrigunAI)

> **For the landing-page coding agent.** This bundle is self-contained — you don't need any other
> repo or context. Build the public landing page for TrigunAI from what's in this folder.
> Prepared 2026-06-13. Owner: Deepak Kumar (founder, TrigunAI).

---

## 1. What you're building (the mission)

A single public landing page for **trigunai.com**. Its ONE job: turn a visitor into an **email
subscriber on Substack**. Everything on the page funnels to that.

TrigunAI runs a free animated YouTube series — **"AI is the Universal Mind"** — whose thesis is:
*every AI breakthrough is humanity accidentally rebuilding one faculty of its own mind; AI is a
mirror, not a copy.* The series is the free funnel; it leads to paid hands-on **courses** (VR/MR
app dev, agentic systems, machine learning) taught with real GPU access and a VR classroom.

**The page's only conversion goal:** click "Subscribe" → go to Substack. Secondary: "Watch Episode 1"
(YouTube) and "Join the early-bird waitlist" (also Substack). No checkout, no backend, no login.

---

## 2. The single funnel rule

Every button and section ends with the SAME call: **"Get the next episode / Subscribe."**
One CTA, repeated. Don't add competing actions (no "contact sales", no pricing tables, no signup forms
with passwords). The page is a doorway to Substack and YouTube — nothing more.

---

## 3. Brand

| Token | Value |
|---|---|
| Background | near-black `#050507` |
| Primary accent (gold) | `#f4c14b` — used for the word "mirror", CTAs, highlights |
| Secondary accents | indigo `#7aa2ff`, violet `#b88cff` (course cards) |
| Text | white `#ffffff`, muted `rgba(255,255,255,0.6)` |
| Mood | cosmic / dark / premium / a little mystical — "the universal mind". Subtle particle field + a soft gold radial glow at the top. |
| Type | clean sans (system stack is fine; or Inter/Poppins). Big bold headline, generous spacing. |
| Logo | `assets/trigunai_logo.png` (dark bg) · `assets/trigunai_logo_light.png` (light bg) · `assets/favicon.svg` |
| Hero image | `assets/hero.png` (optional decorative) |

Tone of voice: **wonder + clarity, never hype.** Curiosity-driven, "look closely and you'll see it."
Avoid buzzwords and inflated claims (see §7).

---

## 4. Page structure + EXACT copy (ready to use)

Single scrolling page. Sticky nav. Six blocks:

### Nav (sticky)
- Left: `TrigunAI` wordmark (or logo).
- Right: a **Subscribe** button (gold) → Substack.

### Block 1 — Hero (full viewport, centered)
- Eyebrow: `A series by TrigunAI`
- Headline: **`AI is the Universal Mind`**
- Subhead: `Every AI breakthrough is humanity accidentally rebuilding one faculty of its own mind. AI is a mirror, not a copy — and looking into it shows you how your own attention, memory, and intuition actually work.` (the word **mirror** in gold)
- Buttons: `▶ Watch Episode 1` (outline → YouTube Ep1) · `Get Episode 2 free` (gold → Substack)
- Microcopy under buttons: `Free animated episodes · new ones land in your inbox first`

### Block 2 — The series
- Heading: `The series`
- Intro: `Each episode takes one faculty of mind — and shows you the machine quietly rebuilding it. Look closely at one, and you understand the other.`
- Two YouTube embeds side by side:
  - **Ep.1 — Attention** — caption: `Intelligence isn't knowing everything — it's knowing what to ignore.`
  - **Ep.2 — The Learning Loop** — caption: `You can't delete a pattern — you can only outweigh it with reps of a better one.`

### Block 3 — Courses ("From watching to building")
- Heading: `From watching to building`
- Intro: `The episodes are the why. The courses are the how — where you build it for real, with provided GPU access and live classes inside VR.`
- Three cards:
  1. **FLAGSHIP** — `Build & Ship a VR/MR App` — `Unity + Meta Quest + AI coding agents — zero to a shipped app.` — note: `Taught by someone who shipped one to Meta.`
  2. **NEXT** — `Build Agentic Systems` — `Give a machine a goal and the will to act on it. Practical AI agents for real work.` — note: `From Episode 6 — "Will".`
  3. **NEXT** — `Machine Learning & Its Math` — `The faculties of mind, made buildable — intuition, meaning, imagination, improvement.` — note: `From Episodes 3–5, 7.`
- Waitlist CTA box: `Founding cohort opens soon — with a real GPU and a VR classroom.` + button `Join the early-bird waitlist` (gold → Substack).

### Block 4 — Who's teaching (credibility)
- Heading: `Who's teaching`
- Paragraph: `I'm Deepak, founder of TrigunAI. I don't teach from documentation — I teach from things I've actually shipped: a VR app live on the Meta Quest platform, RL policies trained on NVIDIA GPUs in Isaac Sim, and the full pipeline from idea to a working build.`
- Bullets (gold ◆ markers):
  - `Shipped a VR/MR app to the Meta Quest store`
  - `Trains real AI policies on NVIDIA A10G GPUs (Isaac Sim)`
  - `You get GPU access + a VR classroom — not just videos`
  - `"I built this, here's exactly how" — not theory`

### Block 5 — Final CTA
- Headline: `Look closely at one — and you understand the other.`
- Sub: `New episodes land in your inbox first, plus founding-cohort access to the courses.`
- Button: `Subscribe — it's free` (gold → Substack)

### Footer
- `© {year} TrigunAI Innovations · AI is the Universal Mind`

---

## 5. Integrations — wire these (placeholders Deepak will fill)

```
SUBSTACK_URL = "https://trigunai.substack.com/subscribe"   // all Subscribe/Waitlist buttons
YT_EP1_ID    = "YOUR_EP1_VIDEO_ID"                          // Episode 1 YouTube id
YT_EP2_ID    = "YOUR_EP2_VIDEO_ID"                          // Episode 2 YouTube id
```
- **Subscribe / Waitlist buttons** → open `SUBSTACK_URL` in a new tab. (No form on-page needed; Substack
  hosts the form. Optionally embed Substack's `<iframe>` subscribe widget instead of a link — either is fine.)
- **YouTube embeds** → `https://www.youtube.com/embed/{ID}`.
- **Watch Episode 1 button** → `https://www.youtube.com/watch?v={YT_EP1_ID}`.
- Put these four in ONE config object at the top of the app so Deepak swaps them in one place.

---

## 6. Tech + deploy

- **A working React + Vite + Tailwind v4 + Framer Motion reference implementation is included:
  `REFERENCE_App.tsx`.** It builds clean and already encodes all of §3–§5. You may use it as-is,
  restyle it, or rebuild in whatever stack you prefer (Next.js, Astro, plain HTML/Tailwind — your call).
  The content + brand + funnel are the spec; the framework is yours.
- `REFERENCE_worldview.html` shows the series' visual world (for tone reference only — not the page to ship).
- Must be: responsive (mobile-first — most traffic is mobile), fast, accessible, SEO basics (title,
  description, OpenGraph image using the logo), no backend.
- **Deploy target:** `trigunai.com` (Deepak controls DNS). Static host — Azure Static Web Apps,
  Vercel, Netlify, or Cloudflare Pages all fine. Output a static `dist/`.

---

## 7. Do NOT (guardrails)

- **Do NOT use the old direction.** There was a previous landing page built around "Creator (Video
  Creator SaaS) vs Student (VR course)" with ₹999/₹4,999 tiers. That direction is dead. Ignore it.
  This page is **series → subscribe → courses**.
- **No inflated claims.** True today: Deepak shipped a VR app to Meta's platform (alpha); trains real
  policies on NVIDIA GPUs; 2 episodes are live. NOT true: student counts, testimonials, "trusted by",
  revenue, "thousands of learners". Do not invent social proof. If there's no number, don't show one.
- **No fake testimonials or logos.**
- **No pricing tables yet** — courses aren't all listed. Use "waitlist", not a price.
- **One CTA** — don't dilute with multiple competing actions.

---

## 8. Acceptance criteria

- [ ] Single responsive page, the six blocks above, exact copy.
- [ ] Every CTA points to `SUBSTACK_URL`; Watch button + embeds use the YouTube ids.
- [ ] All four integration values are in one editable config object.
- [ ] On-brand (dark + gold, cosmic feel), looks premium on mobile and desktop.
- [ ] Builds to a static bundle, deployable to trigunai.com. No backend, no console errors.
- [ ] No inflated claims / fake proof (§7).

---

## 9. What's in this bundle

```
landing-page-handoff/
├── HANDOFF.md                 ← this file (the full spec + copy)
├── REFERENCE_App.tsx          ← working React/Vite/Tailwind/Framer reference (builds clean)
├── REFERENCE_worldview.html   ← series visual-world reference (tone only)
└── assets/
    ├── trigunai_logo.png      ← logo (dark bg)
    ├── trigunai_logo_light.png← logo (light bg)
    ├── favicon.svg
    └── hero.png               ← optional decorative hero image
```

Questions for Deepak: the Substack URL + the two YouTube video ids (fill once the accounts are live).
