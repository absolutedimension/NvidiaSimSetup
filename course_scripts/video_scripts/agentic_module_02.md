---
title: "Module 2 — Your First Tool-Calling Agent"
course: "Build Agentic AI Systems"
module: 2
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
  By the end of this module, you will have built a real agent.
  Small, but real. It takes a goal, calls a tool on its own, and uses the result.
  This is the moment an LLM stops talking and starts doing.
on_screen:
  title: Your First Tool-Calling Agent
  subtitle: Module 2
  layout: center
visual: title over circuit shader; Deepak presenter circle
duration_hint_sec: 16

### scene_02_what_is_tool_calling
narration: |
  Here is the core idea. The model cannot run code or touch the world by itself.
  So we give it a menu of tools, and we describe each one in plain words.
  When the model wants to act, it does not do the action. It asks for it.
  It says, call this tool, with these inputs. Our code runs the tool and hands back the result.
on_screen:
  title: What Tool-Calling Is
  body: The model requests a tool; your code runs it and returns the result
  layout: center
visual: model emits a structured "tool request" card; runtime executes it; result flows back
duration_hint_sec: 40

### scene_03_describe_a_tool
narration: |
  A tool is just a function with a description. A name, what it does, and the inputs it needs.
  Let us start simple. A tool called get_time that returns the current time.
  We describe it clearly, because the model decides when to use it from that description alone.
  Clear descriptions are half the job. Vague ones make a confused agent.
on_screen:
  title: A Tool = a Function + a Description
  bullets: ["name", "what it does", "the inputs it needs"]
  layout: bullets
visual: a function block with a label card; the description text highlighted
duration_hint_sec: 38

### scene_04_the_agent_loop_code
narration: |
  Now the loop, in code form. We send the goal and the tool menu to the model.
  The model replies in one of two ways. Either a final answer, or a tool request.
  If it is a tool request, we run the tool, add the result to the conversation, and ask again.
  We keep looping until the model gives a final answer. That is the whole engine.
on_screen:
  title: The Agent Loop
  body: "Send → model replies → tool request? run it, loop → final answer? stop"
  layout: diagram
visual: animate the send-reply-run-loop cycle, branching on "tool request vs final answer"
duration_hint_sec: 44

### scene_05_parsing
narration: |
  When the model asks for a tool, it gives us structured data. The tool name and the inputs.
  We read that, find the matching function, and call it with those inputs.
  Modern APIs hand this to us cleanly, so we are not parsing messy text.
  We get a clear request, we run it, we return a clear result.
on_screen:
  title: Reading the Tool Request
  body: Structured request → match the function → call it → return the result
  layout: center
visual: a JSON-like request card maps to a function and back to a result
duration_hint_sec: 36

### scene_06_termination
narration: |
  We met this in module one. The agent has to know when to stop.
  In this loop, it stops when the model returns a final answer instead of a tool request.
  We also add a safety cap. A maximum number of steps, so a confused agent cannot loop forever.
  Stopping cleanly is not an afterthought. It is part of the design.
on_screen:
  title: When It Stops
  bullets: ["Final answer returned", "Hit the step cap (safety)", ]
  layout: bullets
visual: the loop with a clear exit and a small step-counter ticking
duration_hint_sec: 32

### scene_07_build_it
narration: |
  Let us put it together. The goal. The tool menu. The loop. The stop condition.
  We run it, and we watch the agent decide to call our tool, take the result, and answer.
  Forty lines of code, and you have something a chatbot can never do.
  It did not just respond. It acted, then responded.
on_screen:
  title: It Runs
  body: Goal + tools + loop + stop = a working agent
  layout: center
visual: terminal-style trace showing the agent calling the tool and finishing
duration_hint_sec: 36

### scene_08_ops_agent_link
narration: |
  Tie it back to our project. The Ops Agent we are building needs exactly this skeleton.
  Today's tiny agent is its heart. In the next modules we give it real tools,
  memory, and the ability to plan. But the loop you wrote today never changes.
  Master this, and everything else is just adding to it.
on_screen:
  title: This Is the Ops Agent's Heart
  body: Real tools, memory, planning all bolt onto this same loop
  layout: center
visual: the small loop sits at the center of the larger Ops Agent diagram
duration_hint_sec: 34

### scene_09_cta
narration: |
  You now have a working tool-calling agent. That is a real milestone.
  In the next module, we give it hands that matter. Web search, files, a database, email.
  The tools that turn a demo into something useful. Let us keep building.
on_screen:
  title: Next — Tools & Integrations
  subtitle: Module 3
  layout: center
visual: tool icons preview; "Module 3" rises; logo + presenter close
duration_hint_sec: 24
