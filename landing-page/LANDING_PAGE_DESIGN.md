# TrigunAI — Interactive Video Landing Page

> **URL:** trigunai.com
> **Style:** Full-screen interactive video — locked scroll, click-to-navigate
> **Inspiration:** Netflix Bandersnatch × Apple keynote × Stripe homepage
> **Two journeys:** Creator (makes content) vs Student (takes courses)

---

## THE CONCEPT

The user lands on trigunai.com and is immediately inside a **full-screen cinematic video**.
No scrolling. No traditional website layout. Just a screen-filling video with interactive
hotspots that respond to clicks.

The video IS the website. Navigation appears ON the video. The user's journey branches
based on what they click — like a choose-your-own-adventure but for a product landing page.

```
USER LANDS ON TRIGUNAI.COM
         │
         ▼
┌─────────────────────────────────────────────┐
│                                             │
│          [FULL SCREEN VIDEO INTRO]          │
│     TrigunAI logo animation + tagline       │
│              (5-8 seconds)                  │
│                                             │
│   "The future of learning is immersive"     │
│                                             │
└─────────────────────┬───────────────────────┘
                      │ auto-transitions to...
                      ▼
┌─────────────────────────────────────────────┐
│                                             │
│     "Who are you?"                          │
│                                             │
│   ┌──────────────┐   ┌──────────────┐      │
│   │  🎬 I CREATE  │   │  📚 I LEARN  │      │
│   │  content      │   │  new skills  │      │
│   └──────┬───────┘   └──────┬───────┘      │
│          │                   │              │
└──────────┼───────────────────┼──────────────┘
           │                   │
     ┌─────▼─────┐      ┌─────▼─────┐
     │ CREATOR    │      │ STUDENT   │
     │ JOURNEY    │      │ JOURNEY   │
     └───────────┘      └───────────┘
```

---

## SCREEN-BY-SCREEN FLOW

### === SCREEN 0: LOADING (2 seconds) ===

**Visual:** Black screen → TrigunAI logo (the Rajas/Tamas/Sattva glowing swirl)
fades in at center. Subtle particle dust in background.

**Audio:** Soft ambient hum, building slightly.

**Interaction:** None — auto-advances.

---

### === SCREEN 1: INTRO VIDEO (8 seconds) ===

**Visual:** Cinematic montage — quick cuts (1.5s each):
1. Hands in VR grabbing a virtual object
2. A student watching a course on a screen
3. AI code appearing on screen
4. A Quest headset on a desk
5. The GuruLok app running in VR

**Text overlay (appearing word by word):**
> "The future of learning is immersive."

**Then:**
> "Where do you want to go?"

**Audio:** Building ambient electronic — the same "inspiring corporate" from our pipeline.

**Interaction:** Two large buttons fade in over the video:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│         "Where do you want to go?"                  │
│                                                     │
│    ┌─────────────────┐  ┌─────────────────┐        │
│    │                  │  │                  │        │
│    │   🎬 I CREATE    │  │   📚 I LEARN     │        │
│    │                  │  │                  │        │
│    │  I'm a teacher,  │  │  I'm a student,  │        │
│    │  creator, or     │  │  developer, or   │        │
│    │  educator        │  │  curious mind    │        │
│    │                  │  │                  │        │
│    └─────────────────┘  └─────────────────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## === CREATOR JOURNEY (clicked "I Create") ===

### SCREEN C1: The Problem (10 seconds)

**Visual:** Dark background, text typing out like a terminal:

> "You have expertise."
> "You want to teach."
> "But creating professional learning videos takes..."

Then a dramatic pause, and:

> "Recording studios. Video editors. Voice artists."
> "Animators. Weeks of work. Thousands of dollars."

**Text fades out. New text appears:**

> "What if you could do it in clicks?"

**Interaction:** Auto-advances, or "Skip →" in corner.

---

### SCREEN C2: The Solution — Video Creator (15 seconds)

**Visual:** Screen recording of the TrigunAI Video Creator app:
- Step 1: Typing script into the editor
- Step 2: Clicking "Generate Voice" — hearing the AI voice
- Step 3: Seeing slides auto-generate
- Step 4: Clicking "Render" — progress bar filling
- Step 5: Playing the final video

**Text overlay:**
> "Script → Voice → Visuals → Music → Video"
> "5 steps. AI does the heavy lifting."
> "You bring the knowledge."

**Interaction:** Two buttons appear:

```
┌───────────────────────┐  ┌───────────────────────┐
│  🚀 Try It Free       │  │  ▶ Watch Demo          │
│  learn.trigunai.com   │  │  See it in action      │
└───────────────────────┘  └───────────────────────┘
```

---

### SCREEN C3: How It Works (interactive cards)

**Visual:** Dark background. 5 floating cards, each clickable:

```
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│  📝  │  │  🎙️  │  │  🎨  │  │  🎵  │  │  🎬  │
│Script│  │Voice │  │Visual│  │Music │  │Render│
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │         │
   ▼         ▼         ▼         ▼         ▼
 Click any card → expands to show that step with a video preview
```

**Interaction:** Clicking a card expands it to show:
- A 5-second clip of that step in action
- 2-line description
- Click elsewhere to collapse

---

### SCREEN C4: Pricing — Creator

**Visual:** Clean, centered:

```
┌─────────────────────────────────────────┐
│                                         │
│         "Start creating for free"       │
│                                         │
│    ┌─────────────┐  ┌─────────────┐    │
│    │    FREE      │  │    PRO      │    │
│    │              │  │              │    │
│    │  3 videos/mo │  │  Unlimited   │    │
│    │  AI voice    │  │  AI voice    │    │
│    │  720p render │  │  1080p + 4K  │    │
│    │              │  │  Priority    │    │
│    │              │  │  queue       │    │
│    │ ┌─────────┐ │  │              │    │
│    │ │ Start   │ │  │  ₹999/month  │    │
│    │ └─────────┘ │  │ ┌─────────┐ │    │
│    └─────────────┘  │ │ Start   │ │    │
│                      │ └─────────┘ │    │
│                      └─────────────┘    │
│                                         │
│    "Both include: 8 AI voices,          │
│     animated slides, background music"  │
│                                         │
└─────────────────────────────────────────┘
```

**Interaction:** "Start" buttons → learn.trigunai.com

---

## === STUDENT JOURNEY (clicked "I Learn") ===

### SCREEN S1: The Vision (8 seconds)

**Visual:** Cinematic — a Quest headset POV showing a virtual classroom,
then a student coding in Unity, then an app running on Quest.

**Text overlay (building up):**
> "Learn by building."
> "Not watching. Building."
> "Real apps. Real skills. Real portfolio."

**Interaction:** Auto-advances.

---

### SCREEN S2: Featured Course (main showcase)

**Visual:** Course card — full screen, cinematic:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │        [Course preview video playing]        │    │
│  │      (the welcome video we created!)         │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Build & Ship Your First VR/MR App                  │
│  AI-Powered Development with Unity & Meta Quest     │
│                                                     │
│  ★★★★★ New course · 14 hours · 11 modules           │
│                                                     │
│  ✅ Hand tracking  ✅ Mixed Reality  ✅ Multiplayer   │
│  ✅ AI coding agents  ✅ Ship to Meta Store           │
│                                                     │
│  "No coding experience needed.                      │
│   The AI handles the code. You handle the vision."  │
│                                                     │
│  ┌──────────────────┐  ┌──────────────────────┐    │
│  │  📚 Self-paced    │  │  🎓 Live Coaching     │    │
│  │  ₹999             │  │  ₹4,999               │    │
│  │                    │  │                        │    │
│  │  All 11 modules   │  │  Everything in Self    │    │
│  │  Lifetime access   │  │  + Weekly live VR      │    │
│  │  Certificate      │  │    classes with me     │    │
│  │                    │  │  + 1-on-1 doubt        │    │
│  │  ┌──────────────┐ │  │    clearing on         │    │
│  │  │  Enroll Now  │ │  │    WhatsApp            │    │
│  │  └──────────────┘ │  │  + Community access    │    │
│  └──────────────────┘  │                        │    │
│                         │  ┌──────────────────┐ │    │
│                         │  │  Enroll Now      │ │    │
│                         │  └──────────────────┘ │    │
│                         └──────────────────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Interaction:**
- Play/pause course preview video
- "Enroll Now" buttons → Udemy or direct payment page
- "View Curriculum" → expands module list

---

### SCREEN S3: Module Breakdown (expandable)

**Visual:** The 11-module timeline (we have this graphic!) with each module clickable:

```
  1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11
  Setup  AI  Hands UI Audio Move Save Multi MR  Polish Ship

  Click any module → expands to show:
  - Module title + description
  - "What you'll build" screenshot
  - Duration
  - Preview clip (if available)
```

**Interaction:** Click modules to expand/collapse.

---

### SCREEN S4: Live Coaching Explainer

**Visual:** Split screen:
- Left: a VR classroom scene (from our renders)
- Right: text explaining the live coaching model

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  🎓 Live Coaching — Learn Inside VR                 │
│                                                     │
│  ┌────────────────────┐                             │
│  │  [VR classroom     │  How it works:              │
│  │   render/video]    │                             │
│  │                    │  1. Join weekly live         │
│  │  "Your instructor  │     VR classes via Quest    │
│  │   is IN the VR     │                             │
│  │   world with you"  │  2. Ask questions in        │
│  │                    │     real-time via WhatsApp   │
│  └────────────────────┘     or YouTube Live          │
│                                                     │
│                          3. Get 1-on-1 doubt         │
│                             clearing                │
│                                                     │
│                          4. Community of fellow      │
│                             VR builders              │
│                                                     │
│          ┌─────────────────────────┐                │
│          │  Start Learning — ₹4,999 │                │
│          └─────────────────────────┘                │
│                                                     │
│     "Don't have a Quest? The self-paced             │
│      course works on any device. ₹999"              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### SCREEN S5: Social Proof / Credibility

**Visual:** Dark, cinematic:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│      "Built by people who shipped"                  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ [GuruLok     │  │ [Meta Dev    │                │
│  │  Store page  │  │  Dashboard]  │                │
│  │  screenshot] │  │              │                │
│  └──────────────┘  └──────────────┘                │
│                                                     │
│  GuruLok: A Spiritual Multiverse                    │
│  Live on Meta Quest Store · Early Access             │
│  Built with the same tools we teach                 │
│                                                     │
│  TrigunAI Innovations Pvt Ltd                       │
│  DPIIT recognized startup                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## NAVIGATION SYSTEM

The navigation is **always visible** as a minimal overlay on the video:

```
Top-left:     TrigunAI logo (click → back to Screen 1)
Top-right:    ☰ Menu (expands to show all screens)
Bottom-left:  Current screen indicator (dots: ● ○ ○ ○ ○)
Bottom-right: 🔊/🔇 Audio toggle
```

**Keyboard:**
- Arrow keys: previous/next screen
- Escape: back to "Who are you?" choice
- Space: pause/play video

**The ☰ menu expands to:**
```
┌──────────────────┐
│  For Creators     │
│    → Video Tool   │
│    → Pricing      │
│    → Try Free     │
│                   │
│  For Students     │
│    → VR Course    │
│    → Curriculum   │
│    → Live Coaching│
│    → Enroll       │
│                   │
│  About            │
│    → Our Story    │
│    → Contact      │
└──────────────────┘
```

---

## TECHNICAL IMPLEMENTATION

### Option A: React + Video.js + GSAP (RECOMMENDED)

```
React app (same Vite stack as Video Creator)
  ├── Full-screen <video> element as background
  ├── GSAP for cinematic text animations
  ├── React state machine for screen navigation
  ├── Video.js for video playback control
  ├── Framer Motion for card animations
  └── Deploy on same Azure Container App or Vercel
```

### Option B: Three.js + WebGL (premium but complex)

Full 3D environment — user navigates through a virtual space.
Overkill for launch. Save for v2.

### Option C: Webflow/Framer (no-code)

Fastest to build but limited interactivity.
Can't do the "video IS the website" concept properly.

**Recommendation: Option A** — React with video backgrounds + GSAP animations.
You already know the stack. It's the same tech as the Video Creator app.

---

## VIDEO ASSETS NEEDED

| Video | Duration | Source | For |
|---|---|---|---|
| Logo animation | 3s | Blender render of TrigunAI logo | Screen 0 |
| Intro montage | 8s | Composite from existing assets | Screen 1 |
| Video Creator demo | 15s | Screen recording of learn.trigunai.com | Screen C2 |
| Course preview | 30-60s | The welcome video we created | Screen S2 |
| VR classroom concept | 10s | Blender/Quest recording | Screen S4 |
| GuruLok footage | 5s | Quest screen mirror | Screen S5 |

Most of these we ALREADY HAVE or can generate with our pipeline.

---

## CONTENT SUMMARY

**For Creators:**
- "Script → Voice → Visuals → Music → Video in clicks"
- Free tier: 3 videos/month
- Pro: ₹999/month, unlimited
- CTA: learn.trigunai.com

**For Students:**
- Course: "Build & Ship Your First VR/MR App"
- Self-paced: ₹999 (all 11 modules, lifetime)
- Live Coaching: ₹4,999 (weekly VR classes + WhatsApp + community)
- CTA: Enroll on Udemy or direct

**Brand voice:**
- Not "corporate education platform"
- More "two founders who built a real VR app and want to teach you how"
- Modern, immersive, cinematic — matches the VR theme
- The landing page FEELS like entering a VR experience

---

## BUILD PLAN

| Day | What | Hours |
|---|---|---|
| 1 | React project + video player + screen state machine + Screen 0-1 | 5h |
| 2 | Creator journey (C1-C4) with animations | 5h |
| 3 | Student journey (S1-S5) with course showcase | 5h |
| 4 | Navigation, responsive, video assets, polish | 5h |
| 5 | Connect to trigunai.com (Squarespace → redirect or embed) | 2h |

**Total: 5 days, ~22 hours**

Or: build a simpler version in 2 days that has the core concept
(intro video → two paths → key screens) without all the animations.
