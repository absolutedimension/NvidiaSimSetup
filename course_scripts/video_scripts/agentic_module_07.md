---
title: "Module 7 — Multi-Agent Systems"
course: "Build Agentic AI Systems"
module: 7
video_type: full_lesson
length_target_sec: 500
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
  Sometimes one agent is not the right shape for the job.
  Today we build with several agents working together. An orchestrator and its workers.
  And just as important, we learn when more agents help, and when they only add chaos.
on_screen:
  title: Multi-Agent Systems
  subtitle: Module 7
  layout: center
visual: one node splits into an orchestrator with worker nodes; circuit shader
duration_hint_sec: 16

### scene_02_why_multiple
narration: |
  Why use more than one agent? Specialization, mostly.
  One agent focused on reading documents. Another focused on writing replies.
  Each has a clear job, a clear set of tools, and a simpler context.
  Like a small team, where everyone is good at one thing, instead of one overloaded generalist.
on_screen:
  title: Why More Than One
  body: Specialization — each agent has one clear job, tools, and context
  layout: center
visual: an overloaded single agent versus a tidy team of focused ones
duration_hint_sec: 36

### scene_03_orchestrator_worker
narration: |
  The most useful pattern is orchestrator and workers.
  One orchestrator agent owns the goal and breaks it into jobs.
  It hands each job to the right worker, collects the results, and decides what is next.
  The orchestrator manages. The workers do. Clean roles, clean flow.
on_screen:
  title: Orchestrator + Workers
  body: Orchestrator owns the goal & delegates; workers do the focused jobs
  layout: diagram
visual: orchestrator dispatches tasks to three workers and gathers results
duration_hint_sec: 42

### scene_04_handoffs
narration: |
  When one agent passes work to another, that is a handoff.
  The trick is what travels with it. Enough context to do the job, and nothing more.
  Too little, the worker is lost. Too much, it drowns and costs more.
  A clean handoff is a clear instruction plus exactly the data that step needs.
on_screen:
  title: Clean Handoffs
  body: Pass enough context to do the job — and no more
  layout: center
visual: a task token passes between agents carrying a tidy context packet
duration_hint_sec: 38

### scene_05_when_it_helps
narration: |
  Be honest about when this pays off. Multiple agents help when the work has
  truly distinct skills, or runs in parallel, or needs an independent reviewer.
  A writer agent and a separate checker agent catch each other's mistakes.
  Distinct roles, real benefit.
on_screen:
  title: When Multiple Agents Help
  bullets: ["Truly distinct skills", "Work runs in parallel", "An independent reviewer"]
  layout: bullets
visual: a maker agent and a checker agent improving an output together
duration_hint_sec: 36

### scene_06_when_it_hurts
narration: |
  And when it does not. If you split a simple job across agents, you just add
  handoffs, latency, and cost, for no gain. More agents is not more intelligence.
  Often the right answer is one good agent with good tools.
  Reach for multiple agents when the problem genuinely has parts. Not because it sounds impressive.
on_screen:
  title: When It Just Adds Chaos
  body: Splitting a simple job → more handoffs, latency, cost — no gain
  layout: center
visual: a simple task tangled by needless agents; arrow back to one clean agent
duration_hint_sec: 38

### scene_07_build_it
narration: |
  Let us build a small one. An orchestrator, a reader worker, and a writer worker.
  The orchestrator takes the goal, asks the reader to gather, then asks the writer to draft,
  then reviews and finishes. Each worker is just an agent like we built in module two.
  Nothing new under the hood. We are composing the pieces you already know.
on_screen:
  title: Build a Small Team
  body: Orchestrator + reader + writer — each one the agent you already built
  layout: diagram
visual: the three-agent flow runs one task start to finish
duration_hint_sec: 40

### scene_08_ops_agent_link
narration: |
  For our Ops Agent, we make a clear choice. The daily workflow is mostly sequential,
  so a single well-built agent is the right shape. But we add one specialist.
  A reviewer agent that checks the drafted replies before they reach you.
  We use multiple agents where it earns its keep, and stay simple everywhere else.
on_screen:
  title: The Ops Agent — Right-Sized
  body: One strong agent + a reviewer specialist where it earns its keep
  layout: center
visual: Ops Agent with a small reviewer node added before the human approval gate
duration_hint_sec: 36

### scene_09_cta
narration: |
  You now know how to use one agent, or several, on purpose.
  So far everything has run on your laptop. Next we deploy.
  We put the agent on a server, on a schedule, with a simple interface, so it runs without you. Let us ship it.
on_screen:
  title: Next — Deploy Your Agent
  subtitle: Module 8
  layout: center
visual: a server + clock preview; "Module 8" rises; logo + presenter
duration_hint_sec: 22
