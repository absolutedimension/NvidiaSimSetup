---
title: "Module 1 — What an AI Agent Actually Is"
course: "Build Agentic AI Systems"
module: 1
video_type: full_lesson
length_target_sec: 540
mode: B                          # motion graphics — concept-heavy module, needs diagrams
voice: { name: male_confident, speed: 0.78 }   # Deepak's instructor voice
background_shader: circuit_mind  # tech/agentic theme
presenter: hybrid                # Deepak Hallo lip-sync 0-30s, then circular presenter
music: ambient_low
aspect: 16:9
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, you will know exactly what an AI agent is.
  Not the hype. The real thing.
  And you will watch one take a goal, make its own decisions, and get a job done.
on_screen:
  title: What an AI Agent Actually Is
  subtitle: Module 1
  body: Goal in. Actions out.
  layout: center
visual: logo top; title fades up over circuit shader; Deepak presenter circle bottom-right
duration_hint_sec: 16

### scene_02_chatbot_vs_agent
narration: |
  Most people have used a chatbot. You ask, it answers. That is where it stops.
  An agent does not stop at the answer. An agent acts.
  You give it a goal, and it goes and does the work to reach that goal.
  A chatbot tells you how to send the email. An agent sends the email.
on_screen:
  title: Chatbot vs Agent
  layout: split
  body: "Chatbot — answers a question. · Agent — completes a goal."
visual: left side a speech bubble (answer); right side a small robot taking three actions; arrow from question to done
duration_hint_sec: 34

### scene_03_what_is_will
narration: |
  In our series, episode six was about Will. Wanting something, and acting to get it.
  An agent is the simplest, most concrete version of that idea you can build.
  Give it a goal. Give it a way to act. And it keeps acting until the goal is met.
  That is will, made out of code. Nothing mystical. Just a goal and a loop.
on_screen:
  title: Will, Made Concrete
  body: A goal + the means to act + a loop that keeps going until done
  layout: center
visual: the word WILL dissolves into a flow — GOAL to ACTION to GOAL-MET
duration_hint_sec: 36

### scene_04_anatomy_overview
narration: |
  Every agent, no matter how fancy, is made of four parts.
  A brain. A loop. Tools. And memory.
  Learn these four, and you can read any agent system ever built.
  Let us take them one at a time.
on_screen:
  title: The Anatomy of an Agent
  bullets: ["The Brain — an LLM", "The Loop — think, act, observe", "Tools — hands to act", "Memory — what it carries"]
  layout: bullets
visual: four labeled blocks assemble into one diagram, one per beat
duration_hint_sec: 28

### scene_05_the_brain
narration: |
  First, the brain. This is a large language model. Claude, or GPT.
  But here is the shift. We are not using it to chat.
  We are using it to decide. At each step it looks at the goal and asks one question.
  What should I do next? The model does not do the work. It chooses the work.
on_screen:
  title: 1. The Brain
  body: The LLM doesn't answer — it decides the next action
  layout: center
visual: a glowing core; inputs (goal, current state) flow in; a single decision flows out
duration_hint_sec: 36

### scene_06_the_loop
narration: |
  Second, the loop. This is the engine of the whole thing.
  The agent thinks. Then it acts. Then it looks at what happened.
  Then it thinks again, with that new information.
  Think, act, observe. Think, act, observe. Over and over.
  A chatbot runs once and stops. An agent runs this loop until the job is done.
  This single loop is the difference between talking and doing.
on_screen:
  title: 2. The Loop
  body: Think → Act → Observe → repeat
  layout: diagram
visual: a circular flow THINK to ACT to OBSERVE looping; each pass the goal-bar fills more
duration_hint_sec: 46

### scene_07_tools
narration: |
  Third, tools. Tools are the agent's hands.
  On its own, the model can only produce text. It cannot touch the world.
  A tool changes that. A tool lets it search the web, read a file, query a database,
  update a spreadsheet, or send a message.
  You hand the agent a set of tools, and suddenly it can act, not just talk.
on_screen:
  title: 3. Tools
  bullets: ["Web search", "Read & write files", "Databases & sheets", "Email & messages"]
  layout: bullets
visual: the brain sprouts connections to icons — search, file, database, mail — lighting up
duration_hint_sec: 40

### scene_08_memory
narration: |
  Fourth, memory. A goal can take many steps.
  The agent has to remember what it already did, and what it learned along the way.
  Short term memory holds the current task. Long term memory holds what matters across tasks.
  Without memory, the agent forgets and goes in circles. With it, the agent makes progress.
on_screen:
  title: 4. Memory
  body: Short-term holds the task · Long-term holds what matters
  layout: center
visual: two stacked layers — a fast scratchpad and a slower store — feeding the loop
duration_hint_sec: 34

### scene_09_when_it_stops
narration: |
  Now the part most tutorials skip. When does it stop?
  An agent without a clear stopping point either quits too early, or runs forever and burns money.
  So we tell it the goal is met, or it hits a limit, or it asks a human.
  Knowing when to stop is part of building a good agent. We will take this seriously.
on_screen:
  title: When Does It Stop?
  bullets: ["Goal is met", "Hits a step or cost limit", "Asks a human"]
  layout: bullets
visual: the loop from scene 6, now with a clear EXIT gate; a small cost-meter on the side
duration_hint_sec: 30

### scene_10_walkthrough
narration: |
  Let us make this real. Give an agent one goal.
  Read today's invoices, find the overdue ones, and email me a short summary.
  It thinks. It uses a tool to read the invoices. It observes what it found.
  It thinks again, and picks out the overdue ones. It drafts the summary.
  It uses the email tool to send it. The goal is met, so it stops.
  Brain, loop, tools, memory. All four, doing one real job.
on_screen:
  title: One Goal, Start to Finish
  body: "Read invoices → find overdue → email a summary"
  layout: diagram
visual: animate the loop running the invoice job step by step, each tool lighting as used, ending on DONE
duration_hint_sec: 52

### scene_11_ops_agent_project
narration: |
  That example is not random. Across this course, you will build exactly that.
  We call it the Ops Agent. An agent that automates one real, small business workflow,
  end to end. It reads an inbox or documents, pulls out the tasks, drafts the replies,
  updates a sheet, and reports every day. By module nine, it runs on its own, on a schedule.
  You will not watch me build it. You will build it, with me.
on_screen:
  title: What You'll Build — the Ops Agent
  bullets: ["Reads an inbox / documents", "Extracts the tasks", "Drafts replies, updates a sheet", "Reports daily — on its own"]
  layout: bullets
visual: the Ops Agent diagram assembling; a small calendar showing it running each day
duration_hint_sec: 44

### scene_12_cta
narration: |
  So that is what an agent actually is. A brain, a loop, tools, and memory, chasing a goal.
  In the next module, we build your first one. A real tool calling agent, from scratch.
  No PhD. Your laptop and an API key are enough. Let us build.
on_screen:
  title: Next — Your First Tool-Calling Agent
  subtitle: Module 2
  body: Bring a laptop + an API key
  layout: center
visual: Ops Agent diagram settles; "Module 2" rises; logo + presenter close
duration_hint_sec: 26
