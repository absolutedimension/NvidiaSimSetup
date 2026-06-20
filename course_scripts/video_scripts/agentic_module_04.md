---
title: "Module 4 — Memory & Context"
course: "Build Agentic AI Systems"
module: 4
video_type: full_lesson
length_target_sec: 510
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: hybrid
music: ambient_low
aspect: 16:9
---

## scenes

### scene_01_hook
narration: |
  An agent without memory is like a worker with amnesia.
  Every step, it forgets what it just did. Today we give our agent memory,
  so it can carry a task across many steps and learn across many tasks.
on_screen:
  title: Memory & Context
  subtitle: Module 4
  layout: center
visual: a fading trail of steps becomes a solid remembered chain; circuit shader
duration_hint_sec: 16

### scene_02_short_vs_long
narration: |
  There are two kinds of memory, and they do different jobs.
  Short term memory is the current conversation. What we are doing right now.
  Long term memory is what we keep across tasks. Facts, preferences, past results.
  Short term is the desk. Long term is the filing cabinet. You need both.
on_screen:
  title: Two Kinds of Memory
  bullets: ["Short-term — the current task", "Long-term — across all tasks"]
  layout: bullets
visual: a desk (scratchpad) beside a filing cabinet (store), both feeding the agent
duration_hint_sec: 36

### scene_03_the_context_window
narration: |
  Short term memory lives in the context window. The text the model sees each turn.
  But the window has a limit. You cannot stuff everything in forever.
  As a task grows, the conversation grows, and eventually it will not fit.
  So managing what goes in the window is a real skill. Let us learn it.
on_screen:
  title: The Context Window Has Limits
  body: Everything the model sees each turn — and it can't hold everything
  layout: center
visual: a window filling with text until it overflows; a "limit" line
duration_hint_sec: 36

### scene_04_managing_context
narration: |
  Three moves keep the window healthy. Keep what matters. Summarize what is old.
  And pull in only the relevant facts, just when they are needed.
  We do not feed the agent its whole history. We feed it the right slice.
  A lean context is a faster, cheaper, sharper agent.
on_screen:
  title: Keep the Context Lean
  bullets: ["Keep what matters now", "Summarize old turns", "Pull only relevant facts"]
  layout: bullets
visual: a cluttered window trimmed down to a clean, relevant set
duration_hint_sec: 38

### scene_05_rag_basics
narration: |
  For long term memory we use retrieval. The basic idea behind RAG.
  We store information as searchable chunks. When the agent needs something,
  it searches that store and pulls back only the matching pieces.
  So the agent can know a thousand pages, but only read the one paragraph it needs right now.
on_screen:
  title: Retrieval — the Basics of RAG
  body: Store knowledge as chunks → search → pull back only what's relevant
  layout: diagram
visual: a query searches a store of chunks; the matching ones flow into context
duration_hint_sec: 42

### scene_06_what_to_remember
narration: |
  A subtle skill. Knowing what to remember, and what to forget.
  Remember decisions, results, and stable facts. Forget the noisy chatter in between.
  If you remember everything, your store fills with junk and retrieval gets worse.
  Good memory is curated, not hoarded.
on_screen:
  title: Remember the Signal, Forget the Noise
  bullets: ["Keep — decisions, results, facts", "Drop — filler and chatter"]
  layout: bullets
visual: items sorted into KEEP and DISCARD bins
duration_hint_sec: 34

### scene_07_wire_it_in
narration: |
  We wire memory into the loop from module two. Before the model thinks,
  we retrieve the relevant facts and add them. After it acts, we store what is worth keeping.
  The loop is the same. We have just given it a memory on each side.
  Retrieve, think, act, store. Then again.
on_screen:
  title: Memory in the Loop
  body: "retrieve → think → act → store → repeat"
  layout: diagram
visual: the agent loop now bracketed by a retrieve step and a store step
duration_hint_sec: 38

### scene_08_ops_agent_link
narration: |
  Our Ops Agent can now remember. It knows which invoices it already handled.
  It remembers your preferences for how replies should sound.
  It does not redo work or repeat itself. It builds on what it did yesterday.
  Tools gave it hands. Memory gives it continuity.
on_screen:
  title: The Ops Agent Remembers
  bullets: ["Which tasks are done", "Your reply preferences", "Yesterday's context"]
  layout: bullets
visual: Ops Agent diagram gains a memory store, linking days together
duration_hint_sec: 34

### scene_09_cta
narration: |
  Hands, and now memory. Your agent is becoming capable.
  But long jobs need more than memory. They need a plan.
  Next, we teach the agent to break a big goal into steps and work through them. Let us go.
on_screen:
  title: Next — Planning & Multi-Step Reasoning
  subtitle: Module 5
  layout: center
visual: a plan tree preview; "Module 5" rises; logo + presenter
duration_hint_sec: 22
