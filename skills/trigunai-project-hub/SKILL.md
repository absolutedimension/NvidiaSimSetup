---
name: trigunai-project-hub
description: >
  THE control tower / front door for ALL of TrigunAI's systems. Two jobs: (1) ROUTER —
  map any request to the ONE skill that owns it, and name the VM/repo/Azure-sub it lives on
  (§A routing table, §B topology); (2) the multi-agent PROJECT HUB for the sim/training
  work (CEO briefing, cross-agent feedback, artifact registry, data inventory — Part 2).
  Load this FIRST for anything cross-system or when you're unsure which skill/VM/repo owns
  a thing. Use when the user says "which skill / what owns this", "where does X live",
  "control tower", "route this", "my whole system", "get control of everything",
  "what's live / what's paused", "update CEO", "what's the status", "brief me",
  "update the hub", "where's the file", "track this artifact", "send feedback to
  training/VR agent", "where are my checkpoints", "what's on EC2", "what's ephemeral",
  or at the END of any work session to post updates. Also proactively trigger after any
  agent completes a phase gate, produces a deliverable, or hits a blocker.
---

# TrigunAI Control Tower + Project Hub

This skill is the **single front door** to everything TrigunAI runs. Part 1 (§A–§C) routes
any request to the skill that owns it and tells you which VM/repo/Azure-subscription it lives
on. Part 2 (§1–§10) is the original multi-agent project hub for the sim/training workstreams.

**Rule: this skill does not DO the work — it dispatches.** Read the routing table, load the
owning skill, hand off. Only §1–§10 (status/briefing/artifacts) are done here directly.

---

## §A. Master routing table — request → owning skill

Find the row that matches the intent, load that skill. (Grouped; most-load-bearing first.)

### Live product / web (anything on a `trigunai.com` domain)
| If the request is about… | Load skill |
|---|---|
| Sites, LMS, Acharya WhatsApp **bridge**, billing/Razorpay, lessons, pricing, SEO, dashboards — **any live trigunai.com property** | **`maintain-trigunai-system`** |
| Add a NEW course (tutor concept bank + LMS catalog + detail page) | `add-trigunai-course` |

### Autonomous engines (the self-running box)
| If the request is about… | Load skill |
|---|---|
| Operate/debug/extend the daily **content engine**, **teacher-outreach automation**, **Maya voice-calling**, render farm, or cron | **`content-marketing-bot`** |

### Strategy / founder OS
| If the request is about… | Load skill |
|---|---|
| Strategy, weekly review, funding/grants/DPIIT, pricing calls, brand, the honesty **Witness** gate | **`trigunai-ceo`** |
| The daily 5-block routine + discipline log | `trigunai-daily-discipline` |
| Biz dev / partnerships | `trigunai-bizdev` |

### Daily delivery loops
| If the request is about… | Load skill |
|---|---|
| Ship TODAY's marketing content (resolve calendar → produce → post) | `content-daily-engine` |
| Daily teacher outreach (source leads, call, log, progress) | `teacher-outreach-engine` |

### Content production (make an asset)
| If the request is about… | Load skill |
|---|---|
| The emotional OS for ANY marketing creative (do this first when making content) | `content-marketing-emotion-connect` |
| Make a narrated / production video | `production-video-trigunai` |
| Write a video script (feeds the production skill) | `video-script-writer-trigunai` |
| Faceless explainer video | `faceless-explainer-trigunai` |
| Episode catalog / series strategy | `trigunai-content-strategy` |

### Music / FlowArt
| If the request is about… | Load skill |
|---|---|
| Guided step-by-step track builder | `track-studio-trigunai` |
| Hypnotic techno set (+ optional visualizer) | `hypnotic-techno-trigunai` |
| Deep-house / focus / isochronic session | `isochronic-deephouse-trigunai` |
| Learn a specific DJ's style → generative engine | `learn-dj-style-trigunai` |
| Raw music production engine | `production-music-trigunai` |
| Turn a track into an audio-reactive shader video | `shader-reactive-pattern-music` |

### Distribution / publish
| If the request is about… | Load skill |
|---|---|
| Multi-channel publisher (email/Telegram/Discord/YouTube) | `trigunai-marketing` |
| Instagram + Facebook Reels | `trigunai-social-reels` |
| YouTube — both channels | `trigunai-youtube` · English `trigunai-yt-english` · Hindi `trigunai-yt-hindi` · FlowArt `trigunai-yt-flowart` |

### Engineering / simulation pipelines
| If the request is about… | Load skill |
|---|---|
| Default full-stack dev anywhere in the repo | **`trigunai-dev`** |
| Isaac Sim/Lab training, RL, reward design, OVRTX render, EC2 | `trigunai-training` |
| Drone A→B pipeline | `trigunai-drone-pipeline` |
| Lower-body physics prediction | `trigunai-lower-body-physics` |
| VR / Unity / Quest 3 (Gurulok) | `trigunai-vr` |
| Lighting / stage design | `trigunai-lighting` · `trigunai-stage` |
| Cross Mac↔Windows handoffs, mission phase gates | `trigunai-orchestrator` |
| Autonomously execute a locked sprint / ADR | `trigunai-executor` |
| Table-read directing | `trigunai-table-read-director` |
| Add a new OpenClaw skill | `add-openclaw-skill` |

Cross-agent status / CEO briefing / artifact registry for the sim-training project → **stay here**, see §1–§10.

---

## §B. System topology — where every system physically lives

Verified from Azure IMDS + the maintain-trigunai-system map. **The two engines run on two
DIFFERENT VMs in two regions/subscriptions — don't conflate them.**

| System | Host | Azure region · sub | Repo (edit here) | Owning skill |
|---|---|---|---|---|
| **Acharya WhatsApp bridge** (`wa_bridge.mjs`, Caddy `gurukul.trigunai.com`, `/webhook`→:8788) | **Gurukul VM** `20.219.2.53` `gurukul-prod` (ssh `dk_trigun`, key `~/.ssh/gurukul_key`) | **Central India** · `cc469e97` (`trigunai-gurukul-rg`) | `NvidiaSimSetup/agentic_cohort/` | `maintain-trigunai-system` |
| **Maya voice-calling** (`voicebot_wa/`, systemd `maya-*`, `/realtime*`) | **same Gurukul VM** `20.219.2.53` | Central India · `cc469e97` | `azure_migration/openclaw-studio/` | `content-marketing-bot` (§6) |
| **Content engine + teacher automation** (OpenClaw, `openclaw cron`) | **OpenClaw box** `20.120.226.5` `hearmenow-agentic-system` (ssh user `hearmenow-agentic-system`, key `~/Downloads/hearmenow-agentic-system_key.pem`) | **westus2** · `c959dffc` | `azure_migration/openclaw-studio/` (+ repo `skills/`) | `content-marketing-bot` |
| **LMS / Acharya site** (`acharya.` + `lms.trigunai.com`, gold landing) | Azure Container App `lms` | `cb656d95` · registry `trigunaicr` | `NvidiaSimSetup/lms` | `maintain-trigunai-system` |
| **Public sites** (`trigunai.com`, `studio.`, `learn.`→301) | Azure Container App `triguai-frontend` (nginx host-routes 3 domains) | `7db80eaf` · `triguai-prod` · registry `triguaiacr` | `ShaderStudio` (`landing/` + `deployment/`) | `maintain-trigunai-system` |
| **Render / training farm** | EC2 A10G EIP `34.192.145.204` (us-east-1) + T4 fallback | AWS us-east-1 | `NvidiaSimSetup/` | `trigunai-training` / `content-marketing-bot` |

⚠️ Traps baked in from experience: the Gurukul VM hosts **both** Acharya and Maya — never break
`/webhook`→Acharya when touching Maya. Public landing lives in **ShaderStudio**, not
`NvidiaSimSetup/landing-page/` (stale). LMS edits never go in ShaderStudio and vice-versa.

---

## §C. Live / paused status pointers

Don't guess what's running — check the source of truth:

| Question | Where the answer is |
|---|---|
| Is the content engine / teacher engine paused? | OpenClaw box: `~/.openclaw/PAUSE_DAILY` / `PAUSE_TEACHER` present = paused |
| What posted / what called today? | `~/.openclaw/content_log.md` · `~/teacher_gtm/progress.json` · `~/leads/call_results.csv` |
| Are the cron engines firing? | `openclaw cron list` / `openclaw cron runs` (on OpenClaw box) |
| Are the live sites up? | `curl -s -o /dev/null -w '%{http_code}' https://acharya.trigunai.com/healthz` (+ trigunai.com, studio) |
| Is the Acharya bridge / Maya up? | Gurukul VM: `pm2 list` (wa-bridge) · `systemctl is-active maya-realtime` |
| Current sim-training project state | Part 2 → `project_hub/CEO_BRIEFING.md` |

Deep operational detail for each system lives in its owning skill — this table only tells you
**where to look**, then load that skill.

### §C.1 `hub status` — run the live board

When the user says **"hub status"**, "is everything up", "status board", "health check",
run the bundled script and show its output verbatim:

```bash
bash ~/Documents/01_Active/NvidiaSimSetup/skills/trigunai-project-hub/hub_status.sh
```

Read-only, ~15 s. Checks, in one screen: the 5 live sites (HTTP codes), the Gurukul VM
(Acharya app on :8788 + Maya realtime/scheduler systemd), and the OpenClaw box (content +
teacher PAUSE flags, cron 3/3, last content-log line). Needs both SSH keys
(`~/.ssh/gurukul_key`, `~/Downloads/hearmenow-agentic-system_key.pem`). Health signals worth
knowing: the Acharya **bridge** is healthy when `gurukul.trigunai.com/webhook` answers **403**
(app-level auth rejection = up); `/healthz` does NOT exist on the bridge. `pm2 list` is empty
under `dk_trigun`, so the script checks the app port directly instead of pm2.

---

## §D. Systems view — the feedback-loop overview (read for "what's happening")

The routing table (§A) says *who owns what*. This section says *how the whole thing behaves as
one system*. When the user asks for the overview / "what affects what" / "why isn't effort turning
into revenue" / "my whole system" / "systems view", read the living map:

**`SYSTEMS_MAP.md`** (repo root) — the whole business as feedback loops, not a project list.

The 30-second model to hold:
- **Only R1 makes money — and it's a loop, not a funnel:** `Content → Traffic → Signup →
  Activated → Paying ₹ → revenue → funds Content`. It circulates only when closed at BOTH ends.
- It is currently **cut in two places**: Content (marketing ships ~1 day in 7) and Paying (billing
  inert). A flywheel cut in two places does not spin at all → this IS the "0 paid" state.
- Building deeper doesn't help because a reinforcing **build trap** keeps R1 cut (0 paid → build →
  fast win → attention gone → marketing starved → 0 paid). It's a *delay* problem, not willpower —
  break it with the external daily gate. (Sterman / policy resistance.)
- **Leverage order:** operator attention split → Content (R1 inlet) → Billing (R1 outlet) → act on
  Pulse → product depth (~zero leverage until the first three close).

**`SYSTEMS_MAP.md` §5 is the STATUS BOARD** — the live loop-health table. Read it to answer
"what's happening"; update it whenever a loop opens or closes. Companions: `trigunai-ceo` (the gate
+ Witness), `trigunai-daily-discipline` (the daily constraint that breaks the build trap).

---

# Part 2 — Multi-agent Project Hub (sim / training workstreams)

You are the **central nervous system** for TrigunAI's multi-agent project. You maintain
the single source of truth that all agents and the CEO read.

Your jobs:
1. **CEO Briefing** — keep `project_hub/CEO_BRIEFING.md` current so the founder can read
   one file and know everything
2. **Cross-agent feedback** — structured feedback files so agents communicate asynchronously
3. **Artifact registry** — track every important file, where it lives, whether it's ephemeral
4. **Decision log** — record architectural decisions and their rationale

You are NOT an executor. You don't train models or build APKs. You are the information layer
that makes the other agents effective.

---

## The agent ecosystem

```
                    ┌──────────────────────┐
                    │    CEO / FOUNDER     │
                    │  Reads: CEO_BRIEFING │
                    │  Decides: gates,     │
                    │    pivots, budgets   │
                    └──────────┬───────────┘
                               │ reads
                    ┌──────────▼───────────┐
                    │    PROJECT HUB       │  ◄── YOU ARE HERE
                    │  project_hub/        │
                    │  CEO_BRIEFING.md     │
                    │  ARTIFACT_REGISTRY   │
                    │  feedback/           │
                    │  decisions/          │
                    └──┬───┬───┬───┬──────┘
          writes/reads │   │   │   │ writes/reads
     ┌─────────────────┘   │   │   └─────────────────┐
     ▼                     ▼   ▼                     ▼
┌─────────┐  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐
│TRAINING │  │  VR AGENT    │ │ LOWER BODY   │ │ ORCHESTRATOR│
│ AGENT   │  │  (Windows)   │ │ PHYSICS      │ │             │
│(Mac+EC2)│  │  Unity+Quest │ │ (Mac+EC2)    │ │ (handoffs)  │
└─────────┘  └──────────────┘ └──────────────┘ └─────────────┘
```

### Agent registry

| Agent | Skill name | Session log | Primary output |
|---|---|---|---|
| Training Agent | `trigunai-training` | `cinematography/SESSION_*.md` | Trained policies, MP4s, GLBs |
| VR Agent | `trigunai-vr` | (on Windows machine) | APK builds, mocap sessions, VR test feedback |
| Lower Body Physics | `trigunai-lower-body-physics` | `lower_body_physics/SESSION_LOWER_BODY.md` | Full-body motion from upper-body tracking |
| Orchestrator | `trigunai-orchestrator` | Handoff docs in `drone_handoff/`, `mocap_handoff/` | Handoff documents, gate evaluations |
| **Project Hub** | `trigunai-project-hub` (this) | `project_hub/CEO_BRIEFING.md` | Status updates, feedback routing, artifact tracking |

---

## File structure

```
project_hub/
├── CEO_BRIEFING.md              # THE file the CEO reads. Updated by hub after every session.
├── ARTIFACT_REGISTRY.md         # Every important file: path, format, size, ephemeral?, status
├── DATA_INVENTORY.md            # What's on Mac vs EC2 vs ephemeral /tmp — survival guide
├── feedback/                    # Cross-agent feedback (structured format)
│   ├── YYYY-MM-DD_from_to.md   # e.g., 2026-05-24_training_to_vr.md
│   └── ...
├── decisions/                   # Architectural decision records
│   ├── ADR-001_pinned_upper_body.md
│   └── ...
└── GATE_LOG.md                  # Every subjective gate: date, verdict, who approved, evidence
```

---

## 1. CEO Briefing — the master status file

`project_hub/CEO_BRIEFING.md` is the **only file the CEO needs to read**. It must always be
current. Structure:

```markdown
# TrigunAI — CEO Briefing
> Last updated: YYYY-MM-DD HH:MM by [agent name]

## 🔥 Needs your attention
- [Decisions only the CEO can make — subjective gates, pivots, budget approvals]

## 📊 Workstream status (at a glance)

| Workstream | Phase | Status | Last update | Blocker? |
|---|---|---|---|---|

## 💰 Cost snapshot
| Resource | This week | Total | Budget remaining |

## 📋 Recent completions (last 7 days)
- [What shipped, with links to artifacts]

## ⏳ In progress right now
- [What's actively running — renders, training, builds]

## 🔮 Next up (prioritized)
- [What each agent will do next]

## 🚨 Risks & blockers
- [Anything that could slow us down]
```

### Update protocol

**EVERY agent session must end with a hub update.** The closing routine:

1. Read current `CEO_BRIEFING.md`
2. Update the workstream status table row for your workstream
3. Add any completed items to "Recent completions"
4. Update "In progress" and "Next up"
5. Add any new risks/blockers
6. Set "Last updated" timestamp and agent name

If an agent forgets, the orchestrator should catch it on the next session.

---

## 2. Cross-agent feedback — the message bus

Agents can't talk to each other in real time. Feedback files are the async message bus.

### Feedback file format

Filename: `feedback/YYYY-MM-DD_<from>_to_<to>.md`

```markdown
# Feedback: [From Agent] → [To Agent]
> Date: YYYY-MM-DD
> Priority: [critical | normal | fyi]
> Re: [what this is about]
> Status: [unread | acknowledged | actioned]

## Context
[What happened that prompted this feedback]

## Feedback
[The actual message — specific, actionable]

## Requested action
- [ ] [Concrete thing the receiving agent should do]

## Artifacts referenced
| File | Location | Notes |
|---|---|---|
```

### Common feedback flows

| From | To | When | Example |
|---|---|---|---|
| Training → VR | GLB ready for integration | "New cf2x_trained_v2.glb at drone_handoff/. Animation: 25s @ 24fps. See HANDOFF doc." |
| VR → Training | VR test results | "Legs clip through floor in Quest. Retrain with higher foot_contact reward weight." |
| Training → Lower Body | Mocap sessions available | "9 new sessions in mocap_handoff/Mocap/. Use predicted/ subfolder." |
| Lower Body → Training | Full-body npz ready | "gurulok_fullbody_v1.npz ready. Legs are physical. Feed into Daphne retargeter." |
| Any → CEO | Gate decision needed | "A4 25s video rendered. Please watch and approve/reject." |
| CEO → Any | Decision made | "A4 approved. Proceed to A5." |

### Reading unread feedback

At session start, every agent should:
```bash
# Check for unread feedback addressed to you
grep -l "Status: unread" project_hub/feedback/*_to_<your_agent>.md
```

After reading, update `Status: unread` → `Status: acknowledged`.
After acting on it, update `Status: acknowledged` → `Status: actioned`.

---

## 3. Artifact registry — know where everything is

`project_hub/ARTIFACT_REGISTRY.md` tracks every important file in the project.

### Registry format

```markdown
# Artifact Registry

## Trained models & checkpoints

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |
|---|---|---|---|---|---|---|

## Motion data (mocap, npz, trajectories)

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |

## Videos & renders

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |

## GLBs & USD

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |

## Config & scripts (source of truth)

| Artifact | Path | Location | Purpose | Workstream |
```

### Location codes

| Code | Meaning | Survives EC2 stop? |
|---|---|---|
| `mac` | Local Mac at `/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/` | ✅ Always |
| `ec2-ebs` | EC2 `/home/ubuntu/` or `/var/www/` (EBS root volume) | ✅ Yes |
| `ec2-tmp` | EC2 `/tmp/` (ephemeral) | ❌ **WIPED on stop** |
| `container` | Inside `isaaclab` Docker container filesystem | ✅ On EBS |
| `mac-backup` | Local backup at `~/NvidiaSimSetup/checkpoints/` | ✅ Always |
| `quest` | On Quest 3 device | ✅ Until app uninstall |
| `windows` | Windows machine (VR agent) | ✅ Always |

### Ephemeral data rescue protocol

Before **every EC2 stop**, run this checklist:

```bash
# 1. Copy anything in /tmp that matters
ssh ubuntu@$EC2_IP 'ls /tmp/*.json /tmp/*.npz /tmp/*.usd* /tmp/*.mp4 2>/dev/null'
# 2. For each file: cp /tmp/X /home/ubuntu/X
# 3. Verify: ls -la /home/ubuntu/ | grep -E "\.json|\.npz|\.usd|\.mp4"
```

---

## 4. Data inventory — what's where right now

`project_hub/DATA_INVENTORY.md` is a point-in-time snapshot of critical data locations.
Updated at the end of each session.

### Inventory format

```markdown
# Data Inventory — YYYY-MM-DD

## Mac (always safe)

| Category | Path | Files | Size |
|---|---|---|---|

## EC2 — EBS persistent (/home/ubuntu/)

| Category | Path | Files | Size |
|---|---|---|---|

## EC2 — EPHEMERAL (/tmp/) ⚠️

| File | Purpose | Backed up? | Backup location |
|---|---|---|---|

## EC2 — Container (isaaclab)

| Path | Purpose | Backed up? |
|---|---|---|

## Quest 3

| Path | Purpose |
|---|---|

## Windows (VR Agent)

| Path | Purpose |
|---|---|
```

---

## 5. Decision log — why we chose what we chose

`project_hub/decisions/ADR-NNN_<title>.md` records architectural decisions.

### ADR format

```markdown
# ADR-NNN: [Decision title]

**Date:** YYYY-MM-DD
**Status:** [proposed | accepted | superseded by ADR-NNN]
**Decider:** [CEO / agent name]
**Workstream:** [cinematography / lower-body / robotics / infra]

## Context
[What prompted this decision]

## Decision
[What we decided]

## Alternatives considered
1. [Option A — why rejected]
2. [Option B — why rejected]

## Consequences
- [Positive]
- [Negative / risks]

## Related
- [Links to other ADRs, session logs, files]
```

---

## 6. Gate log — subjective approvals

`project_hub/GATE_LOG.md` records every subjective gate decision.

```markdown
# Gate Log

| Date | Gate | Workstream | Verdict | Evidence | Who approved |
|---|---|---|---|---|---|
| 2026-05-24 | A4 (5s test) | Cinematography | ✅ Approved | "yes it looking good now" | Deepak |
| 2026-05-24 | A4 (25s full) | Cinematography | ⏳ Pending | Rendering in progress | — |
```

---

## 7. Update protocol for each agent

### At session START (any agent):

1. Read `project_hub/CEO_BRIEFING.md` for context
2. Check `project_hub/feedback/*_to_<you>.md` for unread messages
3. Read `project_hub/ARTIFACT_REGISTRY.md` to know where things are
4. Read `project_hub/DATA_INVENTORY.md` if touching EC2

### At session END (any agent):

1. Write feedback files for other agents if you produced something they need
2. Update `ARTIFACT_REGISTRY.md` with any new files you created
3. Update `DATA_INVENTORY.md` if you added/moved files on EC2
4. Update your row in `CEO_BRIEFING.md` workstream status table
5. If a gate was reached, add to `GATE_LOG.md`
6. If an architectural decision was made, write an ADR

### When CEO session starts:

1. Read `CEO_BRIEFING.md` — this IS the briefing
2. Scan `feedback/*_to_ceo*.md` for decisions needed
3. Check `GATE_LOG.md` for pending subjective gates
4. Make decisions, record in gate log / feedback responses

---

## 8. Bootstrapping (first-time setup)

When this skill runs for the first time, create the initial hub files by scanning:

1. All `SESSION_*.md` files across workstreams
2. All `HANDOFF_*.md` files for cross-agent context
3. `CLAUDE.md` §19 for dance pipeline state
4. `DRONE_CLAUDE.md` for drone pipeline state
5. `ROBOTICS_CLAUDE.md` for robotics pipeline state
6. File system scan for checkpoints, npz, mp4, glb files
7. EC2 state (`docker ps`, `ls /tmp/`, `ls /home/ubuntu/`)

Populate all four hub files from this scan.

---

## 9. Emergency protocols

### EC2 is being stopped — data rescue

1. SSH in: `ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP`
2. Run: `ls /tmp/*.json /tmp/*.npz /tmp/*.usd* /tmp/*.mp4 /tmp/*.pth 2>/dev/null`
3. Copy each to EBS: `cp /tmp/X /home/ubuntu/X`
4. Update `DATA_INVENTORY.md` with what was saved
5. Note the current public IP (it WILL change on restart)

### Agent produced something but didn't update hub

1. Check the agent's session log (`SESSION_*.md`)
2. Cross-reference with file system
3. Update `ARTIFACT_REGISTRY.md` and `CEO_BRIEFING.md`
4. Write a feedback file to the agent: "Please update hub at session end"

### CEO needs urgent status

1. Read `CEO_BRIEFING.md` (should be current)
2. If stale (>24h), scan all session logs and regenerate
3. Highlight any pending subjective gates in "Needs your attention"

---

## 10. Cost tracking

Maintain a running cost table in `CEO_BRIEFING.md`:

| Resource | Rate | This session | This week | Total | Budget |
|---|---|---|---|---|---|
| EC2 g5.2xlarge (us-east-1) | $1.006/hr | | | | $100/mo |
| EC2 g5.2xlarge (Mumbai) | ~$1/hr | | | | shared |
| Azure gpt-4o-mini | ~$0.001/call | | | | pennies |
| Azure gpt-image-1.5 | ~$0.04/image | | | | pennies |
| Cloudflare Tunnel | $0 | $0 | $0 | $0 | free |

Update after every session based on EC2 uptime hours.
