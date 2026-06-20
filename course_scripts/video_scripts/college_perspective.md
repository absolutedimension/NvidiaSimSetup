---
title: What is an AI Agent? — Explained to a College Student
slug: college_perspective
style: faceless photoreal b-roll (gpt-image → LTX) + female British VO + kinetic captions + music
voice: en-GB-SoniaNeural, rate -2%
length_target_sec: 95
aspect: 16:9
note: One perspective from the "What is an agent?" concept graph (college level). Branch points map to course modules (M3 tools, M4 memory, M5 planning, M6 guardrails).
---

## scenes

### s01_frame
label: "Ask a college student"
narration: |
  You've used ChatGPT. That's a single call — a prompt goes in, text comes out, and
  it's done. An agent wraps that same model in a loop, and gives it hands: tools it
  can actually call.
shots:
  - A college student at a laptop with a chat interface on screen, campus, candid
  - Close-up of a terminal / code editor glowing on a laptop in a warm room

### s02_loop
label: "One turn of the loop"
narration: |
  One turn looks like this. You give a goal. The model reasons, then asks to call a
  tool — say, web search. The tool runs and returns a result. The model reads it, and
  decides the next move. It repeats until the goal is met.
shots:
  - Terminal output scrolling on a dark screen, close-up
  - A search query being typed into a browser, screen glow
  - Code running line by line, shallow depth of field

### s03_autonomy
label: "You give the goal. It picks the path."
narration: |
  Here's the shift that matters. In a normal program, you write every step. With an
  agent, you give only the goal — and the model chooses the steps itself, at runtime.
  One step, or twelve, and a different path each time. The model is driving, not your code.
shots:
  - A developer leaning back, thinking, laptop open, warm office bokeh
  - A branching flowchart / decision tree on a monitor
  - Hands resting on a keyboard, screen reflected, contemplative

### s04_example
label: "A real agent"
narration: |
  Take a real job: triage my unread emails and flag the urgent ones. The agent reads
  the inbox, classifies each message, and drafts the replies. It chose that sequence —
  you only stated the goal.
shots:
  - An email inbox open on a laptop screen, close-up
  - Someone reviewing emails, hand on trackpad, warm light
  - A reply being typed, screen glow, shallow depth of field

### s05_code
label: "It's just a loop"
narration: |
  In code, it's just a while-loop. Ask the model. If it requests a tool, run the tool,
  feed the result back, and loop. When there are no more tool calls, it's done. That
  handful of lines is the entire heart of every agent.
shots:
  - A code editor showing a while-loop, syntax-highlighted, dark theme close-up
  - Fingers typing code on a laptop, warm focused light
  - Code on a dark screen with a cursor blinking

### s06_guardrails
label: "Autonomy needs guardrails"
narration: |
  Because the model drives, it can loop forever, call the wrong tool, or run up a bill.
  So real agents add guardrails — a step limit, output checks, a cost cap, and a human
  checkpoint before anything risky. Autonomy is powerful; guardrails make it safe.
shots:
  - A monitoring dashboard with graphs on a screen, close-up
  - Someone reviewing and approving something on screen, hand poised, warm light
  - A usage / cost graph trending on a laptop display

### s07_recap
label: "The honest version"
narration: |
  And the honest version: the model isn't thinking like you do. It's predicting the
  next best action, over and over, inside a loop. Powerful, useful — and not magic.
  Understand that, and you can build one for almost any task.
shots:
  - A developer satisfied at a laptop, leaning back, warm golden light, candid
  - A warm closing shot of hands building / code on screen, shallow depth of field
