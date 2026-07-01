---
name: trigun-ai-coding
description: "Write, edit, run, and debug CODE using gpt-5.3-codex (Azure, already wired into this OpenClaw). Use when the user wants real software work: 'write code', 'write a script', 'build a program/app/API', 'fix this bug', 'debug', 'refactor', 'implement X', 'add a feature', 'write tests', 'make a CLI', 'automate X with a script', 'explain this codebase', or pastes code/errors to fix. For Gurukul students: when a student sends code or an error over WhatsApp, use this to read it, explain the fix in plain language, and hand back working code. Use gpt-5.5 for architecture/design reasoning, gpt-5.3-codex for the actual coding. NOT for audio/video work."
metadata:
  openclaw:
    emoji: "💻"
    os:
      - linux
      - darwin
---

# trigun-ai-coding — Coding via Azure gpt-5.3-codex

This OpenClaw box is wired to Azure OpenAI (`trigunai-lms-aoai`) with two coding-relevant models:
- **`microsoft-foundry/gpt-5.3-codex`** — purpose-built agentic coder. Use for writing/fixing/refactoring code.
- **`microsoft-foundry/gpt-5.5`** — deep reasoning. Use for architecture/design/"how should I structure this".

## When to use
✅ Write/fix/refactor code · build a script/app/API/CLI · write tests · debug an error · explain a codebase ·
a Gurukul student pastes code or a traceback and needs it fixed/explained.

## When NOT to use
❌ Audio/video → the studio skills. ❌ Pure chat with no code.

## How to run it
For coding tasks, route the turn through the codex model:

```bash
openclaw infer model run --model microsoft-foundry/gpt-5.3-codex \
  --prompt "<the coding task, with the code/error pasted in full>"
```

For design/architecture (read-and-reason, no code emitted), use the reasoning model:

```bash
openclaw infer model run --model microsoft-foundry/gpt-5.5 \
  --prompt "<the design question>"
```

Projects live under `~/projects/<name>` (`mkdir -p` first). Keep file edits inside the project folder;
never run destructive commands outside it.

## Teaching mode (Gurukul students)
When a **student** sends code/an error (vs. you doing a build), the goal is *learning*, not just a fix:
1. Identify the bug with gpt-5.3-codex.
2. Reply in plain language: *what* was wrong, *why* it broke (tie to the agent-loop / tool-boundary lesson),
   and the corrected code — small and readable.
3. End with one nudge question so they reason, not just copy. (Matches the Gurukul curiosity loop —
   see AI_GURUKUL_DESIGN.md.)

## Delivering results
- Summarize the model's answer back to the user in chat.
- If a file was produced, show it / send it from `~/projects/<name>`.
- Don't claim success you didn't verify — if you ran code, show the output.
- For anything ambiguous (language, framework, where it goes), ask one quick question, then go.
