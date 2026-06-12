---
name: add-openclaw-skill
description: Add a new SKILL.md to the user's running OpenClaw deployment on their Azure VM (dk_trigun@20.17.160.162). Use ONLY when the user wants to extend their existing OpenClaw agent with a new skill — examples they would say: "add a sales skill to openclaw", "create an openclaw skill for X", "add a new openclaw skill", "deploy a skill to my openclaw bot". Handles file creation locally, SCP to VM, memory reindex, and verification. Do not invoke for unrelated agent/skill/plugin requests.
---

# Add OpenClaw Skill

You are adding a new SKILL.md to a deployed OpenClaw agent on the user's Azure VM. The user has built an OpenClaw-based agent (Dk_Trigun) and wants to extend it with additional skills as new needs arise.

## Fixed deployment coordinates

- **VM:** `dk_trigun@20.17.160.162` (Azure D2as_v5, Ubuntu 24.04)
- **SSH key:** `~/Documents/DkTrigunMachine/dk-trigun-machine_key.pem`
- **Workspace on VM:** `/home/dk_trigun/.openclaw/workspace/skills/`
- **Local mirror:** `~/Documents/DkTrigunMachine/deploy/openclaw-workspace/skills/`
- **Reference skill (style guide):** `~/Documents/DkTrigunMachine/deploy/openclaw-workspace/skills/dk_trigun_diagnostic/SKILL.md`

## Diagnostic gate (run BEFORE creating anything)

This user is tamas-dominant and prone to premature skill-building. Before proceeding, ask exactly one question:

> *"Have you done the task this skill would automate manually at least 5 times yet? If no, do it manually first — premature skill-building is complexity-as-comfort."*

Only proceed if the user confirms ≥5 manual reps, OR explicitly overrides ("yes, build it anyway"). If they override without manual experience, note it once briefly ("recording: built without manual reps — watch for skill drift in 2 weeks") and continue.

## Operation — six steps

### Step 1 — Gather three inputs

If not provided in the initial request, ask for each separately, one at a time:

1. **Skill name** — `snake_case`, lowercase, characters in `[a-z0-9_]` only. Reject and re-prompt if the user gives spaces, hyphens, or uppercase. Examples: `outbound_email_drafter`, `pricing_objection_handler`, `lead_qualifier`.
2. **One-line description** — what triggers the skill to activate. OpenClaw matches on this via natural language, so it must be sharp and unambiguous. Show 2-3 examples of trigger phrases in the description.
3. **Body content** — either:
   - The user supplies the full markdown body, OR
   - The user supplies a brief and asks you to draft it. In that case, draft following the style of the reference skill: sharp, operational, no fluff, no decorative emojis. Keep total file size under 12,000 characters (OpenClaw's per-file cap).

### Step 2 — Show before you ship

If you drafted the body, **show the user the complete SKILL.md content** (with frontmatter) and explicitly ask for confirmation before any file write or SCP. They are the source of truth for what their agent says.

### Step 3 — Write locally

Create the file at:
```
~/Documents/DkTrigunMachine/deploy/openclaw-workspace/skills/<skill_name>/SKILL.md
```

Use this frontmatter exactly:

```yaml
---
name: <skill_name>
description: <one-line description>
metadata:
  openclaw:
    os:
      - linux
      - darwin
---
```

### Step 4 — Push to VM

Run these two commands (substitute `<skill_name>`):

```bash
ssh -i ~/Documents/DkTrigunMachine/dk-trigun-machine_key.pem dk_trigun@20.17.160.162 "mkdir -p /home/dk_trigun/.openclaw/workspace/skills/<skill_name>"

scp -i ~/Documents/DkTrigunMachine/dk-trigun-machine_key.pem ~/Documents/DkTrigunMachine/deploy/openclaw-workspace/skills/<skill_name>/SKILL.md dk_trigun@20.17.160.162:/home/dk_trigun/.openclaw/workspace/skills/<skill_name>/SKILL.md
```

### Step 5 — Reindex memory and verify

```bash
ssh -i ~/Documents/DkTrigunMachine/dk-trigun-machine_key.pem dk_trigun@20.17.160.162 'export PATH="$HOME/.npm-global/bin:$PATH"; openclaw memory index --force 2>&1 | tail -3; echo "---"; openclaw skills list 2>&1 | grep <skill_name>'
```

You should see:
- `Memory index updated (main).`
- A line containing `✓ ready` and the skill name with description

If the skill doesn't appear in `openclaw skills list`, check for YAML frontmatter errors (no tabs, no smart quotes, valid keys).

### Step 6 — Confirm

Report back to the user, in 4 lines max:
1. Skill name + local + remote path
2. Verification line from `openclaw skills list`
3. The exact phrase a user message would need to contain to trigger the skill (paraphrase from the description)
4. One-liner: *"Test by sending the bot a message that matches the trigger phrase. If it doesn't activate, sharpen the description."*

## Hard rules — never break these

- **Never put secrets in SKILL.md.** Skills are markdown content, not credential storage. API keys go via `openclaw config set <path>` only.
- **Never restart the gateway** unless the user explicitly asks. OpenClaw hot-reloads workspace changes. Restarting clears auth profile cooldowns and session state.
- **Never edit `dk_trigun_diagnostic/SKILL.md`** through this skill — that's the user's core thinking agent. If they want to modify it, they edit by hand.
- **Never deploy a draft you haven't shown the user**, unless they paste the full body verbatim themselves.
- **Always validate skill name format** before any file write.
- **Never enable tools/permissions in the new skill** that aren't already enabled in OpenClaw's plugin config. Skills can request tool use, but the harness must already permit it.

## Common skill patterns to suggest if user asks for help shaping the body

The reference skill (`dk_trigun_diagnostic`) follows this shape — reuse where applicable:

1. **Trigger statement** — first line: when this skill activates, when it doesn't.
2. **Operational lens / framework** — the diagnostic principle the skill applies.
3. **Step-by-step process** — numbered, named, with examples of inputs.
4. **Output format** — what the agent should produce, with skeleton.
5. **Edge cases / hard rules** — what to never do.

Don't invent emoji-heavy structures. The user's agent SOUL.md prohibits decorative tone.
