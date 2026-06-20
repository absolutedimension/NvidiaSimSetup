---
title: "Module 6 — Reliability & Guardrails"
course: "Build Agentic AI Systems"
module: 6
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
  This is the module most tutorials skip, and it is the one that matters most.
  A demo agent that works once is easy. An agent you can trust to run unattended is hard.
  Today we add the guardrails that make the difference. Structure, validation, retries, and cost control.
on_screen:
  title: Reliability & Guardrails
  subtitle: Module 6 — the part tutorials skip
  layout: center
visual: a wobbly agent gets a guardrail frame around it; circuit shader
duration_hint_sec: 18

### scene_02_structured_output
narration: |
  First, structure. When the agent's output feeds the next step, free text is dangerous.
  We ask the model for structured output. Clean fields, in a fixed shape, every time.
  Now the next step can rely on the format instead of guessing.
  Structure turns a creative writer into a dependable component.
on_screen:
  title: Structured Output
  body: Fixed fields, predictable shape — so the next step can rely on it
  layout: center
visual: messy paragraph reshaped into clean labeled JSON fields
duration_hint_sec: 36

### scene_03_validation
narration: |
  Structure is a promise. Validation checks the promise was kept.
  Before we trust the agent's output, we verify it. Are the fields present? Is the value sane?
  If it fails the check, we do not pass it on. We catch it right there.
  Validate at every boundary. Never trust, always check.
on_screen:
  title: Validation
  bullets: ["Fields present?", "Values sane?", "Fail the check → don't pass it on"]
  layout: bullets
visual: output passes through a checkpoint; a bad one is stopped at the gate
duration_hint_sec: 36

### scene_04_retries
narration: |
  Things fail. A network blips, a tool times out, the model returns something off.
  Instead of crashing, we retry, carefully. Try again, maybe with a hint about what went wrong.
  But not forever. A few attempts, then escalate. Smart retries absorb the normal chaos of real systems.
  Most one-off failures simply vanish on the second try.
on_screen:
  title: Retries — But Not Forever
  body: Retry with a hint → a few attempts → then escalate
  layout: center
visual: a failed call retries and succeeds; a counter caps the attempts
duration_hint_sec: 38

### scene_05_human_in_the_loop
narration: |
  Some actions are too important to fully automate. Sending money. Emailing a client. Deleting data.
  For these, we put a human in the loop. The agent prepares the action and pauses for approval.
  You glance, you approve, it proceeds. The agent does the work. You keep the final say.
  This single pattern is what makes powerful agents safe to deploy.
on_screen:
  title: Human-in-the-Loop
  body: For high-stakes actions — the agent prepares, a human approves
  layout: center
visual: agent reaches a "needs approval" gate; a human taps approve; action proceeds
duration_hint_sec: 38

### scene_06_cost_control
narration: |
  Now the one that protects your wallet. Every model call and every tool call costs money.
  An agent in a bad loop can burn real cash fast. So we cap it.
  A budget per run. A maximum number of steps. An alert when it gets close.
  A professional agent knows its own spending limit. We build that in from day one.
on_screen:
  title: Cost Control
  bullets: ["Budget per run", "Max steps", "Alert near the limit"]
  layout: bullets
visual: a cost meter rising toward a hard ceiling that stops the run
duration_hint_sec: 38

### scene_07_observability
narration: |
  Last, you cannot trust what you cannot see. So we log everything.
  Every thought, every tool call, every result. When something goes wrong,
  you can read exactly what the agent did and why. This is observability.
  A trustworthy agent is a transparent one. No black boxes.
on_screen:
  title: Log Everything
  body: Every thought, tool call, and result — so you can see what it did and why
  layout: center
visual: a clean trace log scrolling each step the agent took
duration_hint_sec: 34

### scene_08_ops_agent_link
narration: |
  Our Ops Agent is now safe to run on its own. Its outputs are structured and validated.
  It retries through hiccups, asks before it sends anything risky, respects a budget,
  and logs every move. This is the leap from a clever demo to something you would actually deploy.
  Capability plus trust. Now we can scale it.
on_screen:
  title: The Ops Agent Is Trustworthy
  bullets: ["Validated output", "Safe retries + approvals", "Budgeted & logged"]
  layout: bullets
visual: Ops Agent diagram wrapped in a guardrail frame, status all green
duration_hint_sec: 34

### scene_09_cta
narration: |
  Your agent is now reliable, not just clever. That is what separates a project from a toy.
  Next, we go from one agent to many. Orchestrators and workers,
  and the honest question of when multiple agents help, and when they just add chaos.
on_screen:
  title: Next — Multi-Agent Systems
  subtitle: Module 7
  layout: center
visual: several agent nodes preview; "Module 7" rises; logo + presenter
duration_hint_sec: 22
