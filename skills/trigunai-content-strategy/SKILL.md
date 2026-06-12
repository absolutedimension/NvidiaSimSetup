---
name: trigunai-content-strategy
description: The content-strategy brain for TrigunAI's "AI is the Universal Mind" YouTube series and its education funnel. Holds the series worldview (thesis, method, editorial stance, the mathematical deep well), the MASTER EPISODE CATALOG, and the episode→paid-class funnel. Use when planning episodes, deciding what video/content to make next, recalling the series thesis or stance, mapping content to classes, or when the CEO agent needs the current content state. Triggers on "content strategy", "what episode next", "episode list", "episode catalog", "what should I make", "series", "season", "AI is the universal mind", "funnel", "what video next", "content plan", "which class", or when reviewing the YouTube/course content direction.
---

# TrigunAI Content Strategy — "AI is the Universal Mind"

> The single source of truth for what TrigunAI is making and why. The CEO agent reads this
> to remember the content worldview and the episode pipeline. Detailed creative doc lives at
> `youtube_series/SERIES_BIBLE.md`; production runs through the `production-video-trigunai`
> staged pipeline. Owner: Deepak.

## The worldview (4 pillars — locked)

1. **Thesis (the hook):** Each AI breakthrough is humanity accidentally rebuilding one
   faculty of its own mind. AI is a *mirror*, not a copy — it makes the invisible machinery
   of cognition visible for the first time.
2. **Method (the engine):** Find the story already inside the concept. Two strokes —
   **Mirror** ("you already do this") then **Divergence** ("but the machine does it *unlike*
   you, and that's the revelation"). The mirror earns trust; the divergence delivers insight.
3. **Stance (the conscience): AGNOSTIC BUT POINTED.** No metaphysical claims. Humble about
   the cosmic "are they the same?" question (never answered); razor-sharp about the mechanism.
   Anchor lines are *observations true of both*, not claims. Divergences stay unresolved.
4. **The deep well (the source):** the hidden beauty of the *mathematics itself*. The **mind
   is the doorway, the math is the treasure** — keep the magnetic "faculty of mind" frame on
   the outside; reveal the mathematical beauty inside. The math is what *grounds* the
   agnosticism: it's the observable thing we point to.

**Series ethos / recurring close:** *"Look closely at one — and you understand the other."*

## Production

Every episode ships through the **staged pipeline** in `production-video-trigunai`:
**Stage 1 audio-first (human approves quality+pace) → Stage 2 asset-gen (image-gen +
shaders + motion-graphics per scene) → Stage 3 per-scene render + concat → Stage 4 verify.**
Script first via `video-script-writer-trigunai`. Style: 3Blue1Brown/Kurzgesagt — voice +
motion-graphics, no presenter. ~6–9 min/episode, 5-beat arc (Mystery→Mirror→Mechanism→
Meaning→Memory/anchor).

---

## MASTER EPISODE CATALOG

Status key: ✅ shipped · 📄 research/script ready · 💡 idea seeded

| # | Episode | Faculty of mind | Math / architecture | Anchor (observation, true of both) | Status | Funnel → paid class |
|---|---|---|---|---|---|---|
| 1 | **Attention** | Focus / what to ignore | Transformers · attention weights · Q/K/V | "Intelligence isn't knowing everything — it's knowing what to ignore." | ✅ **v1 + v2 fully animated, rendered** | (foundations / hook) |
| 2 | **The Learning Loop** (Humans & Robots) | Learning / habit | RL · reward · Isaac Sim · dopamine↔reward · neuroplasticity · domain randomization | "You can't delete a pattern — you can only outweigh it with reps of a better one." | 📄 **research done** (`research/How_Humans_and_Robots_Learn.pdf`) → script next | **Robotics / Physical AI** |
| 3 | **Imagination** | Dreaming form out of nothing | Diffusion models (creation from noise, refined) | "Creation is just noise, refined." | 💡 idea (most *visually* stunning — noise→image on screen) | ML / generative |
| 4 | **Meaning** | How we hold meaning | Embeddings · vector space | "Meaning is a place, not a thing." | 💡 idea | ML |
| 5 | **Intuition** | Knowing without reasoning; modeling anything | Neural nets · universal approximation | "A hunch is a pattern you can't yet name." | 💡 idea | ML |
| 6 | **Will** | Wanting and acting toward a goal | Agentic systems · RL | "A goal is just a reward you haven't reached." | 💡 idea | **Agentic Systems** |
| 7 | **Getting Better** | Learning from mistakes | Gradient descent | "You don't learn from success — you learn from the size of your error." | 💡 idea | ML |
| — | **Re-Learning / breaking habits** (could be a short, or a beat inside Ep 2) | Changing a burned-in pattern | Catastrophic forgetting ↔ relapse | "You cannot delete a pattern; you can only outvote it." | 💡 from the PDF | Robotics / self-dev crossover |

> Idea bank for later seasons (the well is inexhaustible): information/entropy, eigen-structure,
> convolution (how a mind sees), recurrence/memory, backprop-through-time, attention-as-graph,
> embeddings-as-geometry, RLHF (how a mind is shaped by approval).

## The funnel (free episodes → paid live classes)

**Free YouTube episode = the WHY (wonder). Paid live class = the HOW (build it).** Tightest
funnel pairs a class to its episode's *topic* (same concept, deeper). There are **two funnels**:

- **"Understand → Build the Mind"** — Episodes 2,3,4,5,6,7 feed paid classes in **Robotics/
  Physical AI**, **Agentic Systems**, and **ML systems**. (Tight — same conceptual universe.)
- **"Build VR/MR"** — Deepak's *deepest, most battle-tested* skill (Meta alpha). Separate
  audience/funnel; NOT a faculty of mind. Run it as its own product.

**Solo-founder discipline:** prove ONE episode→class loop converts before scaling. The idea
problem is solved (catalog above is effectively infinite); the real constraint is **shipping
episodes on a schedule + standing up the funnel.** Lead paid classes with deepest expertise
(VR shipped) even though robotics is the most exciting.

## How agents use this file

- **CEO agent:** at content-strategy moments, read this for the current state; the catalog's
  Status column is ground truth for "what's shipped vs idea." Keep pushing toward *shipping
  the next episode + the funnel*, not generating more ideas (ideas are not the bottleneck).
- **To make the next episode:** pick the top non-✅ row, run `video-script-writer-trigunai`
  (frame via the 4 pillars + 5-beat arc), then `production-video-trigunai` (staged pipeline).
- **When a new idea/research arrives:** add a row here (and a seed line in `SERIES_BIBLE.md`).

*Last updated 2026-06-12. Episode 1 shipped (v1+v2). Episode 2 (Learning Loop) is research-ready — next to script.*
