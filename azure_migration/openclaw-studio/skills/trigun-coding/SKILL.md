---
name: trigun-coding
description: "Write, edit, run, and debug CODE by delegating to Codex (gpt-5.3-codex) running locally on this box. Use when the user wants real software work: 'write code', 'write a script', 'build a program/app/API', 'fix this bug', 'debug', 'refactor', 'implement X', 'add a feature', 'write tests', 'make a CLI', 'automate X with a script', 'explain this codebase', or pastes code/errors to fix. Codex is an agentic coder — it reads/writes files and runs commands in a project folder. Use the 'plan' profile (gpt-5.5) for architecture/design questions, the default profile (gpt-5.3-codex) for actual coding. Runs on THIS box (no render farm / EC2 needed). NOT for audio/video (studio-music/studio-video/studio-faceless)."
metadata: { "openclaw": { "emoji": "💻", "requires": { "bins": ["codex"] } } }
---

# trigun-coding — Agentic Coding via Codex

Delegate coding to **Codex** (`codex exec`), already installed on this box and wired to Azure OpenAI:
- **default profile** = `gpt-5.3-codex` — purpose-built agentic coder (writes/edits/runs code)
- **`plan` profile** = `gpt-5.5` — deep reasoning for architecture/design

Codex is itself an agent: given a task and a project folder, it reads the code, makes multi-file edits, runs commands (sandboxed), and reports back. This skill drives it.

## When to Use
✅ Write/fix/refactor code, build a script/app/API/CLI, write tests, debug an error, explain a codebase, automate something with code.

## When NOT to Use
❌ Audio/video → `studio-music` / `studio-video` / `studio-faceless`. ❌ Pure chat with no code involved.

## How it works
Coding runs **locally on this box** (CPU + Azure LLM — no GPU, no EC2). Projects live under `~/projects/<name>`. Codex auth needs the Azure key sourced first.

## Commands — ALWAYS run these; never just describe what you'd do

Codex runs **multi-step and can take 1–3 minutes** (cold start ~150s). So **run it DETACHED and poll** — a synchronous call may hit a command timeout and get killed. This is the primary pattern:

```bash
# 1. set up
source ~/.codex/azure.env                 # AZURE_OPENAI_API_KEY for Codex auth
P=~/projects/<project>; mkdir -p "$P"
rm -f /tmp/codex_out.txt /tmp/codex_done

# 2. launch Codex DETACHED (default profile = gpt-5.3-codex; workspace-write = can edit+run in $P)
setsid nohup bash -c '
  source ~/.codex/azure.env
  codex exec --skip-git-repo-check -p dev -s workspace-write -C "'"$P"'" \
    -o /tmp/codex_out.txt "<THE CODING TASK IN PLAIN ENGLISH>" > /tmp/codex_job.log 2>&1
  touch /tmp/codex_done
' >/dev/null 2>&1 </dev/null &

# 3. POLL until done (check every ~20s, up to ~5 min). Keep checking; do not give up early.
for i in $(seq 1 15); do
  [ -f /tmp/codex_done ] && break
  sleep 20
done

# 4. return Codex's final message + show what it built
cat /tmp/codex_out.txt
ls -R "$P"
```

For **planning / architecture** (gpt-5.5, read-only — thinks, doesn't edit), same pattern but `-p plan -s read-only` and `-o /tmp/codex_plan.txt`.

If `/tmp/codex_done` never appears after polling, show the user `tail -n 30 /tmp/codex_job.log` so they see where it's at — don't claim success without `/tmp/codex_out.txt`.

## Delivering results
- **Summarize** Codex's final message (`/tmp/codex_out.txt`) back to the user.
- **Show what changed:** `ls -R "$P"` or `git -C "$P" diff` (if it's a git repo).
- **Send a file** the user wants: deliver the file from `$P` to them in the chat.
- If the user wants to run it: `cd "$P" && <run command>` and report the output.

## Profiles & sandbox quick-ref
- profile `dev` → gpt-5.3-codex (coding) · `plan` → gpt-5.5 (reasoning)
- sandbox `workspace-write` → can edit+run inside the project (default for coding)
- sandbox `read-only` → safe analysis / Q&A / planning
- sandbox `danger-full-access` → only if the task must touch things outside the project (rare; confirm with the user first)

## Notes
- The full Codex CLI + a web UI ("Codex Studio") also run on this box independently; this skill is the chat-driven entry point to the same engine.
- Keep projects under `~/projects/`. Don't run destructive commands outside a project folder.
- For anything ambiguous (language, framework, where to put it), ask one quick question, then go.
