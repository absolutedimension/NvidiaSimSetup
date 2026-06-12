---
title: "AI is the Universal Mind — Ep.1: Attention"
video_type: youtube_episode
length_target_sec: 400
mode: B                                  # motion graphics — needed for the mechanism beat
voice: { name: male_confident, speed: 0.75 }   # OPEN DECISION (see bible) — Deepak host; swap voice/speed freely
background_shader: circuit_mind          # mind/neuron feel; cosmic_drift is the calmer alt
presenter: none                          # 3Blue1Brown / Kurzgesagt style — voice + motion graphics, no face
music: ambient_low
aspect: 16:9
---

## scenes

### scene_01_hook
narration: |
  Here is a question I could not stop thinking about.
  When you read a sentence, how do you know which words matter?
  Take this one. The animal did not cross the street, because it was too tired.
  What does the word "it" point to?
  You knew instantly. The animal. Not the street.
  Nobody ever taught you that rule. So how did you know?
  And here is the stranger part. A machine now knows it too.
on_screen:
  title: Which word does "it" mean?
  body: "The animal didn't cross the street because it was too tired."
  layout: center
visual: sentence fades up; the word "it" pulses gold; a line draws from "it" to "animal"
duration_hint_sec: 30

### scene_02_stakes
narration: |
  This one idea, figuring out which words should pay attention to which other words,
  is the breakthrough behind almost every AI you have heard of.
  ChatGPT. Claude. The whole modern wave of intelligence.
  In twenty seventeen, a research paper gave the idea a name.
  The title was almost arrogant. Attention is all you need.
  And it turned out, they were right.
on_screen:
  title: "Attention Is All You Need"
  subtitle: 2017
  layout: center
visual: paper title materializes; model names branch outward from it like a network
duration_hint_sec: 26

### scene_03_mirror_party
narration: |
  But before we get to the machine, let me show you something about you.
  Imagine a crowded party. A hundred conversations at once. A wall of noise.
  And then, across the room, someone says your name.
  Instantly, that one voice cuts through everything.
  You did not turn up the volume on your name.
  You turned down everything else.
  That is attention.
on_screen:
  title: The Cocktail Party
  layout: center
visual: many faint voice-waves fill the frame; one wave lights up gold while the rest dim
duration_hint_sec: 28

### scene_04_mirror_now
narration: |
  You are doing it right now.
  Out of everything hitting your eyes and your ears in this moment, you chose this.
  The screen. My voice.
  Everything else faded into the background, until I just pointed at it.
  Your mind is a spotlight.
  And it is always, quietly, choosing what to ignore.
on_screen:
  title: A spotlight that chooses what to ignore
  layout: center
visual: a spotlight cone sweeps across a cluttered field of objects, lighting only one
duration_hint_sec: 24

### scene_05_mechanism_problem
narration: |
  So here is the problem the machine had to solve.
  Give it a sentence. To understand any single word,
  it has to know which other words give that word its meaning.
  In "it was too tired", the word "it" has to look back and find "animal".
  But a machine has no eyes. So how does a machine look?
on_screen:
  title: How does a machine "look back"?
  body: "it  →  ?"
  layout: center
visual: the sentence reappears; "it" emits a searching pulse scanning the other words
duration_hint_sec: 24

### scene_06_mechanism_weights
narration: |
  Here is the trick, and it is beautiful.
  Every word gets to score every other word.
  A number, for how much it should listen to each one.
  High score, pay close attention. Low score, ignore.
  So "it" looks across the sentence. It scores "animal" high. It scores "street" low.
  And it locks on.
  The machine is not reading left to right.
  Every word is weighing every other word, all at once.
on_screen:
  title: Every word scores every other word
  layout: diagram
visual: an attention grid; cells glow brighter with higher weight; the it-to-animal cell burns brightest
duration_hint_sec: 32

### scene_07_mechanism_qkv
narration: |
  And the way it scores is almost human.
  Each word quietly asks a question. What am I looking for?
  That is called the query.
  Every other word answers back. Here is what I am.
  That is called the key.
  When a question meets a matching answer, attention fires.
  "It" asks, who am I standing for?
  "Animal" answers, a thing that can be tired.
  Match. The spotlight snaps into place.
on_screen:
  title: "Query · Key · Value"
  bullets: ["Query — what I'm looking for", "Key — what I am", "Value — what I give"]
  layout: bullets
visual: a query token emits a question-pulse; key tokens respond; the matching pair connects with a bright link
duration_hint_sec: 32

### scene_08_scale
narration: |
  Now multiply this.
  Not one sentence. Billions.
  Not one spotlight. Millions, running side by side, layer upon layer.
  A word attends to words. Those patterns attend to other patterns.
  Meaning building on meaning.
  Stack it high enough, and something new appears.
  The machine begins to seem like it understands.
  And all of it, every single layer, is just this one move, repeated.
  Deciding what to attend to. Deciding what to ignore.
on_screen:
  title: One move, repeated billions of times
  layout: center
visual: a single attention grid multiplies into stacked layers, rising into a vast shifting lattice
duration_hint_sec: 30

### scene_09_meaning
narration: |
  Now sit with what just happened.
  We were trying to build a better translator. A smarter autocomplete.
  And to do it, we had to teach a machine to focus.
  To choose what matters, and throw the rest away.
  And the moment we did, we had built a mirror.
  For the first time, we could see attention itself. Measure it.
  Watch a mind decide what to ignore.
  We did not just make a tool.
  We caught a glimpse of the machinery running quietly inside us.
on_screen:
  title: We built a tool. We got a mirror.
  layout: center
visual: the stacked attention lattice slowly morphs into a glowing human-head silhouette
duration_hint_sec: 30

### scene_10_anchor
narration: |
  We tend to think intelligence means knowing more. Holding everything.
  But the machine learned the opposite lesson.
  The same one your mind learned long ago.
  So here is what I want you to carry out of this.
  Intelligence is not knowing everything. It is knowing what to ignore.
  This was the first faculty. Attention.
  In this series, we are going to rebuild the whole mind, one piece at a time.
  I will see you in the next one.
on_screen:
  title: "Intelligence isn't knowing everything. It's knowing what to ignore."
  subtitle: "AI is the Universal Mind · Ep.1 — Attention"
  layout: center
visual: everything dissolves except the anchor line; series title card resolves; soft fade
duration_hint_sec: 30
```
