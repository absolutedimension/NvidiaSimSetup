# TrigunAI skills — how they sync across machines

These are the version-controlled copies of the Claude skills. The repo is the **single source
of truth**; each machine keeps its own *active* copy in its Claude skills folder, and you move
skills between the repo and the active folder with the sync scripts.

## Why this exists

Skills are **local files on each machine** — sharing one Claude login does **not** sync them.
So the Mac and the Windows (Unity/VR) box each need their own copy. Git carries the skills
between machines; the sync scripts install them.

```
   Mac  ~/.claude/skills  ⇄  repo/skills/  ⇄  Windows  %USERPROFILE%\.claude\skills
              (active)         (git, shared)          (active)
```

## Daily use

**Mac / Linux:**
```bash
./sync_skills.sh            # PUSH: back up your local skill edits into the repo (checkpoint.sh does this)
./sync_skills.sh --install  # PULL: install/refresh skills from the repo into ~/.claude/skills
```

**Windows (PowerShell), e.g. the VR box:**
```powershell
git pull
.\sync_skills.ps1           # install/refresh skills from the repo into %USERPROFILE%\.claude\skills
.\sync_skills.ps1 -Push     # back up Windows-side skill edits into the repo, then commit
```

## The rule

- **Edited a skill on the Mac?** `checkpoint.sh` already pushes it to the repo + commits. Then on
  Windows: `git pull` + `.\sync_skills.ps1`.
- **Edited a skill on Windows?** `.\sync_skills.ps1 -Push` → commit → push. Then on Mac:
  `git pull` + `./sync_skills.sh --install`.
- One source of truth (the repo). One active copy per machine. `git` is the bus.

## Why not `.claude/skills/` (project scope)?

Putting these in `<repo>/.claude/skills/` would force Claude Code to load them as *project*
skills **on top of** the global copies in `~/.claude/skills/`, duplicating them whenever you work
in the repo — and Claude Desktop's project-skill support is unverified. The sync-script model
gives the same "skills everywhere" outcome with no duplication and works on both apps.

## Note: scheduled tasks do NOT sync

The daily accountability tasks (`~/.claude/scheduled-tasks/`) are **machine-local** and are not
in this repo. They run only on the machine they were created on (the Mac), only while its Claude
app is open. The routine *log* (`daily_routine/ROUTINE_LOG.md`) **is** in the repo, so you can log
work from any machine and the Mac's checks will read it after a pull.
