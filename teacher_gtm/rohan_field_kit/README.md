# Rohan's Field Engine — how it's organised

> One page: what Rohan gets, how it fits your existing system, and the exact steps to hand it to
> him. Built 2026-07-16 for the Patna field pivot. Reuses the existing Maya caller-transfer plumbing.

## The three pieces (that's all it is)

```
①  A SKILL on Rohan's Claude   ──ssh──►  ②  Maya + logs on the Gurukul VM   ◄──reads──  ③  You monitor
   skills/rohan-field-caller/            (caller_console.py, call_runner,        (same shared logs,
   = calling + field + logging            shared caller_log + field log)          correct via the log)
```

| # | Piece | Where it lives | Status |
|---|---|---|---|
| ① | **`rohan-field-caller` skill** — his cockpit: control Maya, tweak the script per institute, run the field-visit motion, log calls + visits | `skills/rohan-field-caller/SKILL.md` | ✅ built |
| ② | **Patna directory + sourcing guide** — where to find institutes + the working shortlist | `teacher_gtm/PATNA_SOURCING_GUIDE.md` + `patna_institutes.csv` (3 warm leads seeded) | ✅ built |
| — | **Strategy (the why)** | `teacher_gtm/PATNA_FIELD_STRATEGY_2026-07.md` | ✅ built |
| ③ | **The transfer kit** — Rohan's SSH key + zip + VM authorization | produced by the **`transfer-caller-role`** skill (golden template: `transfer_kit/`) | ⬜ to run |

Rohan controls Maya through the **existing `caller_console.py`** (leads / review / context / call /
batch / log) — so there's nothing new to build on the VM for calling. He just gets his own key and
the field-aware skill.

## What's genuinely new vs the old phone-only caller setup
1. **Field-visit half** — discovery → demo → free pilot → visit logging (the old setup was phone-only).
2. **Per-institute script control** — Rohan shapes Maya's opener for a specific institute before she
   calls (see the one-line VM patch below to fully wire it).
3. **Patna directory + on-foot sourcing** — the cluster map + shortlist CSV.

## To hand it to Rohan — the steps (run the `transfer-caller-role` skill)
The `transfer-caller-role` skill already automates minting a caller kit. For Rohan, run it with:
- **Name:** Rohan Kr. Saurabh · **slug:** `rohan` · **role focus:** "field + calling"
- **Skill to bundle:** `rohan-field-caller` (this new one) instead of the phone-only `maya-caller`
- **Starter leads:** the 3 warm Patna institutes (MCM / Base Point / Delta Success Point)
- **Extra docs to include in his zip:** `PATNA_FIELD_STRATEGY_2026-07.md`, `PATNA_SOURCING_GUIDE.md`,
  `patna_institutes.csv`

That produces `~/Downloads/Rohan_Field_Kit/` with his key + skill + Quick Start + zip.

### ⚠️ The one step Deepak runs by hand (access-control — not automated by Claude)
Authorizing Rohan's key on the live student VM changes access control, so **you** run this (Claude
prepares the key but does not append it):
```bash
cat ~/Downloads/Rohan_Field_Kit/rohan_gurukul_key.pub | \
  ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 \
  'cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo AUTHORIZED'
```
Expect exactly `AUTHORIZED`. **Revoke** later with:
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 \
 "grep -v 'rohan-caller@trigunai' ~/.ssh/authorized_keys > ~/.ssh/a && mv ~/.ssh/a ~/.ssh/authorized_keys && echo REVOKED"
```

## The one small VM build to fully enable per-institute script control
Today Rohan can edit the **global** Maya script (`~/teacher_gtm/02_CONVERSATION_SCRIPT.md`). For a
**per-institute** opener, `call_runner.py` needs to read a `custom_context` field from the chosen
lead row and inject it into Maya's system prompt for that call. That's a ~10-line change to
`call_runner.py` on the VM + a `--context` flag on `caller_console.py call`. Small, isolated, does
not touch live-student services. Do it when wiring Rohan up; until then he uses the global-script edit.

## How you monitor + correct Rohan
- His calls → `~/leads/caller_log.csv` (VM). His visits → the field log (`by=rohan`).
- You read the same logs (`caller_console.py history` / `review`) and correct him via a message +
  by adjusting the script or the shortlist. No separate dashboard — the shared log IS the interface.

## Open decisions (flagged to Deepak 2026-07-16)
1. **Does Rohan need the ₹200/visit proof workflow** wired into the field log (photo attach), or is
   the same-day text log enough for month one?
