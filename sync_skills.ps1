<#
sync_skills.ps1 — Windows equivalent of sync_skills.sh.

Installs/refreshes the TrigunAI Claude skills on THIS Windows machine from the repo's
version-controlled copy (skills\). Run it after `git pull` so the Windows box (Unity / VR
dev) has the same skills as the Mac.

  Usage (from the repo root, in PowerShell):
    .\sync_skills.ps1                 # PULL (default): repo\skills\  ->  %USERPROFILE%\.claude\skills
    .\sync_skills.ps1 -Push           # PUSH: %USERPROFILE%\.claude\skills  ->  repo\skills\  (then commit)

  Notes:
   - %USERPROFILE%\.claude\skills is the Claude Code skills folder. If your Claude Desktop
     loads skills from a different folder, run `where do my skills live` in Claude on this box
     and set $Active below to that path.
   - After installing, reopen Claude if a new skill doesn't show up yet.
#>
param([switch]$Push)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Active = Join-Path $env:USERPROFILE ".claude\skills"   # where Claude loads skills on this machine
$Repo   = Join-Path $PSScriptRoot "skills"              # version-controlled copy in this repo

# Our skills only (don't touch unrelated plugin skills)
$Patterns = @("trigunai-*","content-*","production-*","faceless-*",
              "video-script-writer-trigunai","add-openclaw-skill")

function Sync-Dir($from, $to) {
    if (-not (Test-Path $to)) { New-Item -ItemType Directory -Path $to -Force | Out-Null }
    # mirror: copy contents, then remove files in $to not present in $from
    robocopy $from $to /MIR /NJH /NJS /NDL /NP | Out-Null
}

$count = 0
if ($Push) {
    if (-not (Test-Path $Repo)) { New-Item -ItemType Directory -Path $Repo -Force | Out-Null }
    foreach ($pat in $Patterns) {
        Get-ChildItem -Path $Active -Directory -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
            Sync-Dir $_.FullName (Join-Path $Repo $_.Name); $count++
        }
    }
    Write-Host "OK PUSH: synced $count skill(s)  ~\.claude\skills  ->  skills\"
} else {
    if (-not (Test-Path $Active)) { New-Item -ItemType Directory -Path $Active -Force | Out-Null }
    foreach ($pat in $Patterns) {
        Get-ChildItem -Path $Repo -Directory -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
            Sync-Dir $_.FullName (Join-Path $Active $_.Name); $count++
        }
    }
    Write-Host "OK INSTALL: synced $count skill(s)  skills\  ->  ~\.claude\skills"
    Write-Host "  Reopen Claude if a newly-installed skill doesn't appear yet."
}
