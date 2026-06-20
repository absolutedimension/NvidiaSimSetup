# Course 5 — Build Your AI Video Factory (15 Days) · Landing-Page Handoff

> **Status:** Curriculum complete (2026-06-20). This is the parked "Build Your AI Video Studio"
> course, now designed as a **15-day build program**. On-strategy: **we teach the factory, we do
> not sell it as done-for-you SaaS** (CEO decision on record). B2B = **training** a team to build
> their own studio, NOT a setup service.
> **Landing CTA = REGISTER / JOIN THE WAITLIST** (free-now funnel), not a price — same as the other
> drip courses, until willingness-to-pay is validated.

---

## 1. The offer (landing copy)

**Title:** Build Your AI Video Factory
**Tagline:** Turn a script into a finished, narrated, captioned video — in your *own* GPU-powered
studio. 15 days, multiple styles, copyright-clean, at scale. Taught by someone who runs this factory
every day to produce a real channel + course library.

**You build:** your own end-to-end AI video factory — and publish your first 3 videos from it.

**For:** content creators & faceless-channel builders · course creators · marketers & agencies ·
B2B teams who want video production *in-house* instead of outsourced.

**You need:** a laptop + a modest cloud-GPU budget (~$1/hr — we show the cheapest options) + a couple
of API keys. **No video-editing skill, no ML background.** The AI writes most of the code; you direct.

**Outcome:** a working factory you *own*, plus the patterns to produce video in any style, on demand —
faceless explainers, motion-graphics, talking-points-over-b-roll, shorts, localized/bilingual, with
copyright-clean music. The skill, not a subscription.

**Why it's different:** it's not theory or "10 AI tools to try." You build the same kind of pipeline
TrigunAI uses to ship its YouTube series, course modules, and ads — battle-tested, with every gotcha
already solved for you.

---

## 2. The 15-day curriculum

Project-based. Every day = a short lesson + a hands-on lab. The labs compound — by Day 15 you have a
running factory and 3 published videos. Three milestones marked ★.

| Day | Title | You learn | Hands-on lab |
|---|---|---|---|
| **1** | The AI Video Factory | The "script in → finished video out" model; the 5 layers (brain · voice · visuals · captions · compositor); the styles & the business models (faceless channel, course videos, client work, B2B in-house) | Tour a finished factory output frame-by-frame; set your goal & niche |
| **2** | Your cloud GPU + the brain | Why a GPU; the cheapest options (RunPod / Vast.ai / AWS); spin up a box; the LLM + image + voice **API layer** behind one proxy; hard cost control | Launch a GPU box, run a "hello" render, set a spend cap |
| **3** | Script → narration | Writing scripts *for* text-to-speech; voice engines (free edge-tts → studio F5-TTS → premium); **per-scene audio for perfect sync**; accent & pace | Turn a script into a clean, synced voiceover |
| **4** | Visuals I — AI images | Photoreal & stylized stills with image models; prompt craft for b-roll; the content-safety gotchas (and how to reframe around them); building a shot list from a script | Generate a full scene's worth of images |
| **5** | Visuals II — image → motion | Animating stills into living clips on your GPU (image-to-video); subtle vs strong motion; **multi-shot scenes with no ugly "boomerang" loop** | Animate your stills into clips |
| **6** | Captions that pop | Word-synced **kinetic captions** (auto-timed); lower-third labels; fonts & styling; the non-overlap trick | Add synced captions to a clip |
| **7** ★ | The compositor | Layering background + overlays + captions + audio; scene-by-scene assembly (not one fragile mega-filter); clean export settings | **★ Milestone: your first complete faceless video** |
| **8** | Music & sound, copyright-clean | AI music for beds; ducking under the voice; **why copyright-clean matters for monetization** (demonetization horror stories) | Add a music bed that sits under the VO |
| **9** | Style 2 — motion-graphics / explainer | Teaching diagrams, kinetic text, animated cards; when to use this vs b-roll | Build a motion-graphics scene |
| **10** | Style 3 — shaders + the talking-head reality | Audio-reactive abstract backgrounds; **the honest truth about AI talking-heads** (free vs paid, when a presenter is worth it) | A shader-background video; lock your style palette |
| **11** | Localization & reach | Translate + **re-voice into other languages** with a one-swap workflow; bilingual channels; going global | Make a second-language version of your video |
| **12** | Automation & the one-command factory | Turning the steps into a single command / template; presets per style; **batching many videos**; reproducible runs | Build a one-command template for your style |
| **13** | Your factory, your way | Tailor the factory to your lane — faceless YouTube, course/edu, product/marketing, social shorts; channel setup & SEO basics | Configure your factory for your niche |
| **14** | Productize — clients & B2B | Packaging it as a service or in-house capability; pricing; intake → delivery workflow; **what to automate, what to charge, the support trap to avoid** | Draft your offer (channel plan or client package) |
| **15** ★★ | Ship & scale | Publishing workflow (YouTube API + scheduling); a content calendar; your 30-day plan to 10+ videos | **★★ Capstone: publish your first 3 videos from your own factory · Demo Day** |

**What you walk away with:** a running AI video factory you own · 3 published videos · style presets for
faceless / motion-graphics / shader / localized · a copyright-clean music workflow · and a 30-day plan
to scale — plus (for the B2B track) a client/offer package.

---

## 3. Drop-in course card (add to `courses.ts`)

Add this object to `COURSES[]` and a new register key + URL (see §4). Suggested accent: a new `ROSE`.

```ts
// Accent (add near the palette)
const ROSE = '#ff8fb1';

// ── 5. Build Your AI Video Factory — register-interest / waitlist ─────────────
{
  id: 'ai-video-factory',
  badge: 'NEW · REGISTER INTEREST',
  status: 'waitlist',                 // CTA => "Join the waitlist"
  accent: ROSE,
  title: 'Build Your AI Video Factory',
  tagline:
    'Turn a script into a finished, narrated, captioned video — in your own GPU-powered studio. ' +
    '15 days, multiple styles, copyright-clean, at scale. Taught by someone who runs this factory daily.',
  fromEpisodes: 'The workshop behind the whole series — learn to build what produces the content.',
  level: 'Creator → Studio owner',
  modulesCount: 15,
  hours: '~18 hours over 15 days',
  outcome:
    'Your own working AI video factory + your first 3 published videos, in any style, on demand — ' +
    'the skill, not a subscription.',
  forWho:
    'Content creators & faceless-channel builders, course creators, marketers & agencies, ' +
    'and B2B teams who want video production in-house.',
  prerequisites:
    'A laptop + a modest cloud-GPU budget (~$1/hr) + a couple of API keys. No editing or ML background.',
  registerKey: 'VIDEO',
  modules: [
    { n: 1,  title: 'The AI Video Factory',            brief: 'The 5 layers, the styles, the business models.' },
    { n: 2,  title: 'Your cloud GPU + the brain',       brief: 'Spin up a cheap GPU box + the LLM/image/voice API layer.' },
    { n: 3,  title: 'Script → narration',               brief: 'Scripts for TTS; per-scene voice for perfect sync.' },
    { n: 4,  title: 'Visuals I — AI images',            brief: 'Photoreal & stylized stills; shot lists from a script.' },
    { n: 5,  title: 'Visuals II — image → motion',      brief: 'Animate stills into clips; multi-shot, no boomerang.' },
    { n: 6,  title: 'Captions that pop',               brief: 'Word-synced kinetic captions + lower-third labels.' },
    { n: 7,  title: 'The compositor',                   brief: 'Layer it all into your first complete video.' },
    { n: 8,  title: 'Music & sound, copyright-clean',   brief: 'AI music beds, ducking, monetization-safe audio.' },
    { n: 9,  title: 'Style 2 — motion-graphics',        brief: 'Diagrams, kinetic text, animated explainer cards.' },
    { n: 10, title: 'Style 3 — shaders + talking-heads',brief: 'Reactive backgrounds; the honest truth on AI avatars.' },
    { n: 11, title: 'Localization & reach',             brief: 'Re-voice into other languages; bilingual channels.' },
    { n: 12, title: 'The one-command factory',          brief: 'Templates, presets, batching — automate it.' },
    { n: 13, title: 'Your factory, your way',           brief: 'Tailor it to your niche + channel/SEO basics.' },
    { n: 14, title: 'Productize — clients & B2B',       brief: 'Package it, price it, avoid the support trap.' },
    { n: 15, title: 'Ship & scale',                     brief: 'Publish your first 3 videos; a 30-day scale plan.' },
  ],
},
```

## 4. Register wiring (for Deepak)
- Add `'VIDEO'` to the `registerKey` union type and a `REGISTER_URL_VIDEO` (waitlist form or Substack
  fallback, like the other courses).
- Until the form exists, point it at the same waitlist fallback the other drip courses use.

## 5. Update `COURSE_INDEXES.md`
Change the Course 5 row (line ~20) from *"parked — future / ~8 (draft)"* to:
`| 5 | **Build Your AI Video Factory** | (the production craft) | **Register interest** | **Join the waitlist** | Creator → Studio owner | 15 | ~18 |`
…and replace the parked Course-5 section with the §1 + §2 content above.

---

## CEO note (not for the page)
- This is the **workshop taught as a course** — exactly the approved move. Keep the page CTA at
  **waitlist/register**, not a price, until someone pays for the *live agentic cohort* first.
- **Do not let this displace the July-18 launch focus.** It's a post-launch course; collecting
  register-interest now is free validation — building/recording it is *after* the first paid cohort.
- B2B = **training**, never done-for-you setup. If inbound asks for "build it for us," that's a
  separate, deliberate decision — not the default offer.
