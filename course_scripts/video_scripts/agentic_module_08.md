---
title: "Module 8 — Deploy Your Agent"
course: "Build Agentic AI Systems"
module: 8
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
  An agent that only runs when you press play is not finished.
  Today we deploy. We put the agent on a server, give it a schedule,
  add a simple interface, and turn on monitoring. It runs without you.
on_screen:
  title: Deploy Your Agent
  subtitle: Module 8
  layout: center
visual: agent moves from a laptop onto a server with a clock; circuit shader
duration_hint_sec: 16

### scene_02_from_script_to_service
narration: |
  On your laptop, the agent is a script you run by hand. To deploy, we make it a service.
  Something that lives on a server and is ready to run on demand or on a timer.
  Same code we wrote. We are just changing where it lives and what triggers it.
  This is a smaller leap than it sounds.
on_screen:
  title: From Script to Service
  body: Same code — new home (a server) and new triggers (on-demand or timed)
  layout: center
visual: a script icon transforms into an always-on service box
duration_hint_sec: 36

### scene_03_scheduling
narration: |
  Most useful agents run on a schedule. Our Ops Agent should run every morning.
  We set a simple timer. Every day at eight, wake up, do the daily run, then sleep.
  No one has to remember to start it. It just happens, like clockwork.
  This is the moment an agent becomes part of the operation, not a thing you babysit.
on_screen:
  title: Put It on a Schedule
  body: "Every morning at 8 — wake, run, sleep. No babysitting."
  layout: center
visual: a daily timer fires the agent each morning on a calendar strip
duration_hint_sec: 36

### scene_04_a_simple_ui
narration: |
  People need a way to see and steer the agent. So we add a minimal interface.
  Nothing fancy. A page that shows what it did, and lets a person approve the items waiting.
  This is where your human-in-the-loop checkpoints from module six become real buttons.
  Simple, clear, and enough.
on_screen:
  title: A Minimal Interface
  bullets: ["See what it did", "Approve what's waiting", "Trigger a run"]
  layout: bullets
visual: a clean dashboard listing the agent's actions with approve buttons
duration_hint_sec: 36

### scene_05_secrets_in_prod
narration: |
  On a server, security matters even more. Those keys from module three
  live in the server's secret storage, not in the code, not in the repo.
  We give the agent only the access it needs, and nothing it does not.
  A deployed agent has real reach. We are deliberate about every permission.
on_screen:
  title: Secrets in Production
  bullets: ["Keys in secret storage", "Least privilege", "Never in the code or repo"]
  layout: center
visual: a server vault holds the keys; the agent draws only what it needs
duration_hint_sec: 36

### scene_06_monitoring
narration: |
  Once it runs on its own, you watch it from a distance. Monitoring.
  Did the morning run finish? Did anything fail? Is spending normal?
  We send ourselves a short daily report and an alert if something breaks.
  You are not staring at it. You are informed, and free to do other work.
on_screen:
  title: Monitoring & Alerts
  bullets: ["Did the run finish?", "Anything fail?", "Daily report + alerts"]
  layout: bullets
visual: a health panel green-lit; an alert pings on a failure
duration_hint_sec: 36

### scene_07_reliability_in_prod
narration: |
  Real servers have bad days. So the agent handles its own restarts and recovers a run
  that stopped halfway. The guardrails from module six are what make this safe.
  Validation, retries, budgets, logs. They were not busywork. They are exactly what lets you sleep
  while the agent works.
on_screen:
  title: It Survives Bad Days
  body: Restarts, recovers a half-finished run — because the guardrails are there
  layout: center
visual: a server hiccups; the agent restarts and resumes cleanly
duration_hint_sec: 36

### scene_08_ops_agent_link
narration: |
  Our Ops Agent is now live. Every morning it runs, reads the inbox, drafts the replies,
  updates the sheet, waits for your quick approval, and reports what it did.
  It is no longer a project on your laptop. It is a small worker doing a real job, daily.
  One module left. We make it something you could hand to someone else.
on_screen:
  title: The Ops Agent Is Live
  bullets: ["Runs every morning", "Waits for your approval", "Reports daily"]
  layout: bullets
visual: Ops Agent deployed on a server, daily cycle animating
duration_hint_sec: 34

### scene_09_cta
narration: |
  Your agent runs on its own now. That is a real, deployed system.
  In the final module, we make it shippable to others. We package it,
  write its playbook, hand it to a non-technical user, and prove it actually saves time.
on_screen:
  title: Next — Ship a Real Business Agent
  subtitle: Module 9
  layout: center
visual: a gift-wrapped agent preview; "Module 9" rises; logo + presenter
duration_hint_sec: 22
