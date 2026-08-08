---
name: transfer-caller-role
description: Repeatable new-employee onboarding for the TrigunAI teacher-outreach role. Produces a complete, personalized kit (SSH key + Claude Desktop skill + Quick Start HTML + zip) that a new caller/field-hire can extract on their own machine and be operating the Maya calling + teacher onboarding pipeline within 15 minutes. Also authorizes their SSH key on the Gurukul VM (revocable). USE WHEN Deepak says "hire a new caller", "onboard <name> to calling", "transfer the calling role to <name>", "make a caller kit for <name>", "add <name> to teacher outreach", "prepare <name>'s Claude Desktop for calling". The current field-caller skill (`rohan-field-caller`) + `teacher_gtm/rohan_field_kit/README.md` are the reference for the field variant.
---

# Transfer Caller Role — new-hire kit builder

> **Purpose:** every time Deepak hires a new caller/onboarding employee, this skill produces the
> full deliverable (SSH key + kit zip + HTML Quick Start + VM authorization) in one guided pass.
> The goal: the new hire runs a **single command** on their laptop to be operating within 15 min.

## ⭐ PREFERRED delivery — a self-contained skill via the VM dropbox (STANDARD, 2026-07-16)

Don't email zips of loose docs. Package ALL the role's knowledge as a **self-contained Claude Code
skill** and ship it through the Gurukul VM. This is the company standard — full method in the
`reference-skill-transfer-method` memory. In short:
1. Build the role skill self-contained: `skills/<role-skill>/SKILL.md` + `skills/<role-skill>/references/*`
   (bundle training, guides, data, pitch, strategy). SKILL.md points at its own `references/<file>`.
   **Keep the SSH key OUT of the skill** (install separately to `~/.ssh/`).
2. Mint the hire's key (steps below) + Deepak authorizes it on the VM (step 3).
3. Stage the skill: `scp -i ~/.ssh/gurukul_key -r skills/<role-skill> dk_trigun@20.219.2.53:~/skill_dropbox/`
4. The hire's Claude pulls it: `scp -r -i ~/.ssh/<hire>_gurukul_key dk_trigun@20.219.2.53:~/skill_dropbox/<role-skill> ~/.claude/skills/` → restart Claude Code.
5. **Updates use the same channel:** re-scp to `~/skill_dropbox/` → hire says "update my skill" → re-pull.

(The SSH-key + kit-zip flow below is still the fallback for a hire with no Gurukul-VM access. Note the
shared Claude login does NOT sync skills — they're local files — so the dropbox pull is the transfer.)

## What you produce (the deliverables)

Every run of this skill outputs a folder at `~/Downloads/<Name>_Caller_Kit/` containing:

| File | Purpose |
|---|---|
| `<slug>_gurukul_key` | Fresh Ed25519 private key — the new hire's login to the Gurukul VM |
| `<slug>_gurukul_key.pub` | Public key — for reference / revocation later |
| `skill/maya-caller/SKILL.md` | The current maya-caller skill (fetched fresh from the VM's canonical `~/teacher_gtm/maya-caller-SKILL.md`) |
| `COMPANY_CONTEXT_<Name>.md` | Field handbook — TrigunAI + Acharya context, pitch, objections, values, rules (fetched from `~/teacher_gtm/COMPANY_CONTEXT.md`) |
| `<Name>_Quick_Start.html` | Personalized click-through setup guide (generated fresh — see step 5) |
| `<Name>_SETUP.md` | Plain-text version of the setup steps for terminal-preferring hires |
| `<Name>_Caller_Kit.zip` | Everything above, zipped for the hire to download |

Plus: the new hire's public key is **authorized on the Gurukul VM's** `~/.ssh/authorized_keys` (with a
comment line for later revocation).

## Inputs to gather from Deepak (ask ONLY what's missing)

| Input | Example | If not given |
|---|---|---|
| Employee full name | "Rohan Kr. Saurabh" | Ask |
| Slug (lowercase, alphanumeric only) | "rohan" | Derive from first name, lowercased |
| Role focus | "onboarding + calling", "calling only", "onboarding only" | Default: "onboarding + calling" (matches skill's coverage) |
| Starter leads (optional) | phone numbers to work first | Default: point to the 5 already in `template_sent` (Catalyzers/Goal/Perfect Maths/M.K. Thakur/Tution Time) |
| Claude account | Their email | Default: `deepak@trigunai.com` (they use Deepak's team account on their own machine) |

## The steps (Claude executes these)

### 1. Prepare the kit directory
```bash
KIT="$HOME/Downloads/<Name>_Caller_Kit"
rm -rf "$KIT" && mkdir -p "$KIT/skill/maya-caller"
```

### 2. Generate a fresh Ed25519 keypair (no passphrase — the file itself is the secret)
```bash
ssh-keygen -t ed25519 -f "$KIT/<slug>_gurukul_key" \
  -C "<slug>-caller@trigunai" -N "" -q
# Verify both files exist and mode is 600 on the private
ls -la "$KIT/<slug>_gurukul_key"*
chmod 600 "$KIT/<slug>_gurukul_key"
```

### 3. Authorize the pubkey on the Gurukul VM (using Deepak's own `~/.ssh/gurukul_key`)
```bash
cat "$KIT/<slug>_gurukul_key.pub" | \
  ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 \
    'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo AUTHORIZED'
```
Expect exactly `AUTHORIZED`. If it fails, STOP and report the error; do not continue.

### 4. Fetch the current canonical maya-caller SKILL.md + COMPANY_CONTEXT.md + PDF from the VM
The VM version at `~/teacher_gtm/maya-caller-SKILL.md` is the source of truth (kept up to date
whenever the pipeline changes). Always fetch fresh, never use a stale local copy. Same for
COMPANY_CONTEXT.md/pdf — the field handbook every new hire needs before their first customer call.
```bash
scp -i ~/.ssh/gurukul_key \
  dk_trigun@20.219.2.53:~/teacher_gtm/maya-caller-SKILL.md \
  "$KIT/skill/maya-caller/SKILL.md"
scp -i ~/.ssh/gurukul_key \
  dk_trigun@20.219.2.53:~/teacher_gtm/COMPANY_CONTEXT.md \
  "$KIT/COMPANY_CONTEXT_<Name>.md"
scp -i ~/.ssh/gurukul_key \
  dk_trigun@20.219.2.53:~/teacher_gtm/COMPANY_CONTEXT.pdf \
  "$KIT/COMPANY_CONTEXT_<Name>.pdf"
```
If the VM PDF is out of date (its `.md` was updated but the PDF wasn't), regenerate it by running
the conversion script at `scratchpad/make_context_pdf.py` (Chrome headless → 7-page A4).

### 5. Personalize the Quick Start HTML
Generate the Quick Start HTML fresh for the hire — a simple click-through page covering: (1)
install the SSH key, (2) copy the skill folder into `~/.claude/skills/`, (3) restart Claude
Desktop, (4) the trigger phrase to test ("start my day"). Use the hire's `<Name>` / `<slug>` /
`<Name>_Caller_Kit.zip` throughout. Save as `$KIT/<Name>_Quick_Start.html`.

If the role differs (e.g., onboarding-focused vs pure calling), tune the "How you'll work every day"
section:
- **Calling-focused:** keep the existing prompts ("Who should I call?", "Run a batch...").
- **Onboarding-focused:** add prompts at the top:
  - *"Show me the onboarding pipeline"* (→ `--list`)
  - *"Any teachers waiting on me?"* (→ `needs_name` + `provisioning`)
  - *"Send today's approved batch"* (→ `--send-batch`)

### 6. Write the plain-text SETUP.md
A plain-text version of the setup steps (key install → skill copy → restart → test phrase) for
terminal-preferring hires. Use the hire's `<Name>` / `<slug>` throughout.

### 7. Zip the kit
```bash
cd "$KIT/.."  # so the archive contains the folder itself, not just its contents
zip -qr "<Name>_Caller_Kit.zip" "<Name>_Caller_Kit" \
  -x "*.DS_Store" -x "__MACOSX/*"
# Also drop the .zip inside the folder for easy sharing
cp "<Name>_Caller_Kit.zip" "$KIT/<Name>_Caller_Kit.zip"
```

### 8. Print the exact message Deepak should paste to the new hire
Emit a ready-to-copy message with:
- Attachment reference: `<Name>_Caller_Kit.zip`
- The one-command install for Mac AND Windows (matches the Quick Start HTML)
- The single trigger phrase to test after Claude Desktop restart: *"start my calling"*

## Safety rules (enforce every run)

- **Never reuse a key across hires.** Every run mints a fresh Ed25519. If a `<slug>_gurukul_key` already
  exists in `~/Downloads/<Name>_Caller_Kit/`, ask before overwriting.
- **The pubkey MUST have a comment** with the hire's slug and `@trigunai` — that comment is what
  `DEEPAK_deploy_access.md`-style revocation grep-matches on. `ssh-keygen -C "<slug>-caller@trigunai"`.
- **Only touch the VM's `authorized_keys`** — never anything else. The VM runs the live Acharya student
  tutor + Maya + the onboarding pipeline; a stray edit breaks real students.
- **Do not put multiple hires in one kit.** One kit = one hire = one key = one row in authorized_keys.
- **Verify the VM authorization worked** before proceeding (check the exact `AUTHORIZED` echo).
- **Do NOT commit the private key** to git. The kit directory is under `~/Downloads/` deliberately.

## Revocation recipe (belongs in the kit's README so Deepak has it)

If the hire stops calling / leaves:
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 \
  "grep -v '<slug>-caller@trigunai' ~/.ssh/authorized_keys > ~/.ssh/a && mv ~/.ssh/a ~/.ssh/authorized_keys && echo REVOKED"
```

## When to invoke this skill

- "Hire a new caller"
- "Onboard <name> to teacher outreach"
- "Transfer the calling role to <name>"
- "Make <name>'s kit"
- "Prepare <name>'s Claude Desktop for the calling pipeline"

## When NOT to invoke this skill

- Updating an existing caller's SKILL.md (they just re-scp the file — no new key needed)
- Rotating an existing caller's key (that's a separate rotation flow — mint new key, revoke old with the recipe above)
- Onboarding a *content-marketing* employee (that's a different skill / kit — this one is calling-focused)

## Companion skills / docs
- `maya-caller` skill = what the new hire installs on their Claude Desktop (source of truth on VM at `~/teacher_gtm/maya-caller-SKILL.md`)
- `~/teacher_gtm/OPERATIONS.md` = canonical ops doc any Claude session on the VM reads
- Reference: `skills/rohan-field-caller/SKILL.md` + `teacher_gtm/rohan_field_kit/README.md` (the current field-caller variant) · reusable console reference: `teacher_gtm/caller_console.py` (canonical lives on the VM at `~/caller_console.py`)

*Built 2026-07-08 after the pipeline shipped end-to-end. Owner: Deepak. Iterate whenever the maya-caller pipeline evolves.*
