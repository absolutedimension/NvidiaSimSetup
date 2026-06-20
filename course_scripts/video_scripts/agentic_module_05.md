---
title: "Module 5 — Planning & Multi-Step Reasoning"
course: "Build Agentic AI Systems"
module: 5
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
  Some jobs take one step. Most real jobs take twelve.
  Today we teach our agent to plan. To break a big goal into steps,
  work through them, check its own work, and recover when a step goes wrong.
on_screen:
  title: Planning & Multi-Step Reasoning
  subtitle: Module 5
  layout: center
visual: one big goal splits into a tree of ordered steps; circuit shader
duration_hint_sec: 16

### scene_02_why_planning
narration: |
  Without a plan, an agent reacts step by step and loses the thread on long tasks.
  With a plan, it lays out the steps first, then executes them in order.
  Think of how you handle a big task. You do not just start. You sketch the steps.
  We give the agent that same habit.
on_screen:
  title: Why Plan First
  body: Lay out the steps → then execute in order → don't lose the thread
  layout: center
visual: a chaotic scribble resolves into a clean numbered checklist
duration_hint_sec: 36

### scene_03_decomposition
narration: |
  The first skill is decomposition. Take the goal and break it into smaller tasks.
  Process the invoices becomes. List the invoices. Find the overdue ones.
  Draft a summary. Send it. Each piece is small enough to do reliably.
  A hard goal becomes a list of easy steps.
on_screen:
  title: Decomposition
  body: "Big goal → list of small, doable steps"
  layout: diagram
visual: "Process invoices" expands into four sub-steps
duration_hint_sec: 36

### scene_04_react
narration: |
  Next, a powerful pattern called ReAct. Reason, then act, then observe. In words.
  The agent writes out its thought. Then takes one action. Then reads the result.
  Then reasons again with what it learned. Thinking out loud, between each action.
  This simple habit makes agents far more reliable on multi-step work.
on_screen:
  title: ReAct — Reason + Act
  body: "Think out loud → act → observe → think again"
  layout: diagram
visual: alternating THOUGHT and ACTION cards stacking down a task
duration_hint_sec: 42

### scene_05_reflection
narration: |
  Then, reflection. After acting, the agent checks its own work.
  Did that step actually succeed? Is the result what I expected?
  If yes, move on. If no, try a different approach. This is self-correction.
  An agent that checks itself is the difference between brittle and dependable.
on_screen:
  title: Reflection & Self-Correction
  bullets: ["Did that step succeed?", "Is the result right?", "If not — try another way"]
  layout: bullets
visual: agent reviews its output, catches an error, and retries successfully
duration_hint_sec: 38

### scene_06_when_steps_fail
narration: |
  Real tasks fail in the middle. A tool errors. A file is missing. A result looks wrong.
  A good agent does not crash or pretend. It notices, adjusts the plan, and continues.
  We design for failure on purpose, because failure is normal.
  Recovering gracefully is what makes an agent trustworthy.
on_screen:
  title: Recovering From Failure
  body: Notice → adjust the plan → continue (failure is normal)
  layout: center
visual: a step turns red; the plan reroutes around it and proceeds
duration_hint_sec: 36

### scene_07_putting_it_together
narration: |
  Now combine it. The agent decomposes the goal, reasons and acts step by step,
  checks each result, and adapts when something breaks.
  Memory from module four keeps the plan and progress in view.
  This is an agent handling a twelve step job the way a careful person would.
on_screen:
  title: Plan + Act + Check + Adapt
  body: A twelve-step job, handled the way a careful person would
  layout: center
visual: a full plan executes top to bottom with checks and one recovery
duration_hint_sec: 38

### scene_08_ops_agent_link
narration: |
  Our Ops Agent can now run a real workflow end to end.
  It plans the daily run, works each step, verifies as it goes, and handles the hiccups.
  This is the brain of the thing nearly complete. What remains is making it safe and reliable
  enough to trust unattended. That is exactly module six.
on_screen:
  title: The Ops Agent Can Run a Workflow
  bullets: ["Plans the daily run", "Works step by step", "Verifies & recovers"]
  layout: bullets
visual: Ops Agent diagram now shows a planning core driving the loop
duration_hint_sec: 34

### scene_09_cta
narration: |
  Your agent can plan and self-correct. That is serious capability.
  But capable is not the same as trustworthy. Next we add the guardrails.
  Structured output, validation, retries, and cost control. The part tutorials skip. Let us not skip it.
on_screen:
  title: Next — Reliability & Guardrails
  subtitle: Module 6
  layout: center
visual: a shield + guardrail preview; "Module 6" rises; logo + presenter
duration_hint_sec: 22
