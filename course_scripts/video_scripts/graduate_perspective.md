---
title: What is an AI Agent? — Explained to a Graduate / Practitioner
slug: graduate_perspective
style: faceless photoreal b-roll (gpt-image → LTX) + female British VO + kinetic captions + music
voice: en-GB-SoniaNeural, rate -2%
length_target_sec: 105
aspect: 16:9
note: Level 4 of the "What is an agent?" concept graph. Precise/architectural framing — policy, action space, memory layers, planning loop, workflow-vs-agent, reliability.
---

## scenes

### s01_policy
label: "Ask a graduate"
narration: |
  If you've shipped code, here's the precise version. An agent is a policy — a function
  that maps observations to actions. The language model is that policy. It decides each move.

### s02_action_space
label: "The action space"
narration: |
  The tools define its action space — everything it can actually do beyond producing text.
  Call an API, query a database, run code, send a message.

### s03_memory
label: "Two kinds of memory"
narration: |
  Its memory has two layers. Short-term — the context window, its working memory for this run.
  And long-term — retrieval over past state, pulling back what matters, when it matters.

### s04_planning
label: "How it plans"
narration: |
  For jobs that take many steps, it plans. Decompose the task, reason and act in turns — the
  ReAct pattern — then reflect and self-correct when a step fails.

### s05_workflow_vs_agent
label: "Workflow vs. agent"
narration: |
  And here's the distinction that separates engineers from tutorial-followers. In a workflow,
  you hard-code the control flow — fixed steps. In an agent, the model decides the control flow
  at runtime. More flexible, more powerful, and less predictable.

### s06_reliability
label: "The reliability tax"
narration: |
  That non-determinism is the tax you pay for autonomy. So production agents wrap the loop in
  guardrails — validation, retries, cost caps, observability — so a probabilistic core behaves
  like a dependable system.

### s07_recap
label: "Architect one"
narration: |
  So: an LLM policy, acting over a tool-defined action space, with layered memory and a planning
  loop, bounded by guardrails. That's an agent, precisely. Now you can architect one.
