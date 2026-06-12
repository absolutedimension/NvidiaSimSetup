# Episode 1 — Asset Plan (v2: full animation)

> Goal: the viewer should **see what the narrator is describing.** Every line of
> narration gets a synced visual. We use three production tools, each for what it is
> genuinely best at — not one tool forced to do everything.

## The three tools (and their lane)

| Tool | We already have | Best for | NOT for |
|---|---|---|---|
| **Image-gen** (Azure gpt-image-1.5) | ✅ in pipeline | Evocative *scenes* the viewer pictures — a party, a brain, a spotlight room. Static hero art we animate over (Ken-Burns / parallax / reveal). | Precise diagrams, labeled text, exact positions (it can't place "Query/Key/Value" reliably). |
| **Shader engine** (GLSL / ModernGL) | ✅ `circuit_mind` + 11 more | Living *fields* & ambient motion — networks, lattices, flowing energy, voice-waves, spotlight masks. Audio-reactive backgrounds. | Anything needing exact labels or a specific readable diagram. |
| **Motion graphics** (programmatic, PIL/numpy per-frame) | ⚙️ engine exists (needs per-scene authoring) | The *teaching diagrams* — the sentence with a glowing word, the attention grid, the query→key match. Exact control of text, position, timing. | Photoreal scenes (looks flat) — hand those to image-gen. |

**The mix that works (this is how 3Blue1Brown / Kurzgesagt actually do it):**
mostly programmatic motion-graphics for the *teaching*, image-gen for the *imagine-this* moments, shaders for the *living background*. Layered: shader behind → image/motion-graphics mid → text on top.

---

## Per-scene breakdown

| # | Narration beat | What the viewer should SEE | Primary tool | Asset(s) |
|---|---|---|---|---|
| **s01** | "which word does *it* mean?" | The sentence appears; the word **it** pulses gold; an arc draws from *it* → *animal* (not *street*) | Motion graphics | `mg_sentence_link` (text + animated arc) |
| **s02** | "Attention Is All You Need… ChatGPT, Claude, the whole wave" | A glowing paper card; model names **branch out** from it like a growing network | Motion graphics + shader bg | `mg_branch_network`; bg `attention_field` |
| **s03** | the cocktail party; your name cuts through | A stylized crowded-party scene; many faint **voice-waves**; one lights **gold** while the rest dim | **Image-gen** (crowd) + shader (waves) | `img_party_crowd.png`; shader `voice_waves` |
| **s04** | "your mind is a spotlight… choosing what to ignore" | A dark cluttered field of objects; a **spotlight cone** sweeps and lights only one | **Image-gen** (clutter) + shader (spotlight mask) | `img_spotlight_field.png`; shader `spotlight_sweep` |
| **s05** | "how does a machine look back? it → ?" | The sentence again; **it** emits a searching pulse scanning the other words | Motion graphics | reuse `mg_sentence_link` (scan variant) |
| **s06** | "every word scores every other word" | **THE attention grid** — words on rows/cols, cells glow by weight, the *it↔animal* cell burns brightest | **Motion graphics** (centerpiece) | `mg_attention_grid` |
| **s07** | "query / key / value… a question meets an answer" | Tokens float; **it** emits a *query* pulse; *animal* answers with a *key*; the matching pair links bright; labels Q·K·V | Motion graphics | `mg_qkv_match` |
| **s08** | "multiply this — billions, layer upon layer" | One grid **multiplies** into stacked layers rising into a vast, shifting **lattice** | **Shader** (this is its perfect job) | shader `lattice_rise` (audio-reactive) |
| **s09** | "we built a tool, we got a mirror" | The lattice slowly **morphs into a glowing human-head silhouette** made of nodes | **Image-gen** (head) + shader morph | `img_mind_network_head.png` |
| **s10** | anchor: "knowing what to ignore" | Everything dissolves; the **anchor line** resolves alone; series title card | Motion graphics | `mg_anchor_card` |

---

## Consolidated production list

### A. Image-gen assets (Azure gpt-image-1.5) — ~4 images, ~$0.40, minutes
Dark, cinematic, abstract, 16:9, consistent palette (deep indigo/black + cool light, occasional gold/purple accent — to match `circuit_mind`). Style: "elegant minimal editorial illustration, not photoreal, lots of negative space for text."
1. `img_party_crowd.png` — many abstract human silhouettes at a party, warm haze, one figure subtly highlighted; lots of dark space.
2. `img_spotlight_field.png` — top-down dark field scattered with small simple objects/icons, one bright spotlight pool on a single object.
3. `img_mind_network_head.png` — a human head in profile, formed from glowing connected nodes (brain-as-network), deep indigo, negative space around it.
4. *(optional)* `img_neural_substrate.png` — abstract neural tissue texture for ambient use.

### B. Shaders to create or reuse (GLSL — must fit the `u_time/u_rms/u_bass/...` contract)
- ✅ `circuit_mind` — reuse as the global ambient base.
- 🆕 `attention_field` — slow network of nodes + connections, gentle pulse on `u_rms` (background for s02, s05–s07).
- 🆕 `voice_waves` — layered horizontal waves; one band brighter (s03 overlay).
- 🆕 `spotlight_sweep` — radial light mask that drifts (s04 overlay, multiplied over the image).
- 🆕 `lattice_rise` — stacked grid planes receding into depth, scrolling upward, reactive (s08 hero).

### C. Motion-graphics modules (programmatic, per-scene authoring — the real build)
- `mg_sentence_link` — render words as positioned tokens; highlight one; animate a bezier arc between two tokens. (s01, s05)
- `mg_branch_network` — a center card; child labels animate outward on connecting lines. (s02)
- `mg_attention_grid` — **centerpiece.** N×N grid, row/col word labels, each cell alpha = weight; sequential glow reveal; brightest = it↔animal. (s06)
- `mg_qkv_match` — two tokens, a query pulse from one, key from the other, a bright connect on match; Q·K·V labels. (s07)
- `mg_anchor_card` — clean kinetic typography for the closing line + series tag. (s10)

---

## Composition & flow (how it becomes one animated piece)

1. **Per-scene voice already drives timing** (proven in v1) — every animation is rendered to its scene's exact audio length.
2. **Layer stack per scene:** shader bg → (image-gen hero, if any, with slow parallax/Ken-Burns) → motion-graphics diagram (transparent RGBA) → kinetic text.
3. **Continuity:** transitions are matched cuts, not hard slides — e.g. the s06 grid *becomes* the s08 lattice; the s08 lattice *becomes* the s09 head. The visual morphs with the argument.
4. **Reactivity:** shaders pulse to the narration so the background breathes with the voice.
5. **Render:** motion-graphics frames (PIL/numpy) composited over shader + image layers on EC2, same ffmpeg backbone as v1 — but pre-flatten layers per scene (fixes the slow 10-overlay stitch from v1).

---

## Honest scope (CEO note)

Full per-scene animation is a real build — the motion-graphics modules (esp. `mg_attention_grid` and `mg_qkv_match`) are bespoke code, not a setting. This is **3Blue1Brown-tier work** and worth it for a flagship Episode 1 — *if scoped so it doesn't become an endless polish loop.*

**Recommended sequence (prove, then scale):**
1. **Now:** generate the 3 image-gen assets (fast, cheap, tangible) + build **one** hero motion-graphics scene — `mg_attention_grid` (s06), the signature visual.
2. **Gate:** look at that one animated scene. If it makes attention *click* harder than the slide did → green-light the rest.
3. **Then:** build the remaining mg modules + new shaders, and compose the full animated Episode 1 (v2).

This way we spend a little to validate the *animated approach* before committing to all 10 scenes.

*Started 2026-06-12. Status: plan — awaiting go on Step 1 (image assets + attention-grid pilot).*
