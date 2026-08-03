# Kids Asset Pooling System — design

*Owner: Deepak · 2026-08-02. Offline-generate a pool of characters/props/backgrounds; the worksheets
consume them by id, with emoji as the always-works fallback. Companions:
`kids_quiz/WORKSHEET_GRAMMAR.md`, the `kids-animation-story-creator` skill (the character factory),
`lms/app/static/kids/KIDS_ALIVE_CONTRACT.md`.*

## The idea in one line
> Worksheets reference art by **id** (`{"asset":"cow"}`). A **pool manifest** says whether that art is
> `ready` (a generated web asset) or `needed` (show its emoji for now). An **offline generator** fills the
> `needed` ones on the GPU box. The browser **auto-swaps emoji → art** the moment the pool says `ready`.
> Nothing ever blocks a child; the pool just gets richer over time.

## The loop
```
   worksheets reference assets by id
              │  asset_pool.py scan
              ▼
   pool manifest  ── status ──▶  ready ✓ (browser shows art)   /  needed … (browser shows emoji)
              │  asset_pool.py plan
              ▼
   to_generate.json  ──▶  gen_assets.py (EC2)  ──▶  writes assets/<id>.(png|gif) + marks ready
              │                                          props → gpt-image · characters → factory
              ▼
   deploy kids app  ──▶  KidsAssets auto-swaps emoji → art
```

## The four parts (all built)
| Part | File | Runs | Role |
|---|---|---|---|
| **Pool registry** | `lms/app/static/kids/asset_manifest.json` | — | source of truth; each asset `ready`/`needed` + emoji fallback |
| **Runtime resolver** | `lms/app/static/kids/assets.js` (`KidsAssets`) | browser | id → `<img>` if ready, else emoji `<span>` |
| **The brain** | `kids_quiz/asset_pool/asset_pool.py` | local | `status` · `scan` · `request` · `plan` |
| **Offline generator** | `kids_quiz/asset_pool/gen_assets.py` | EC2 GPU | props → gpt-image · characters → AnimatedDrawings factory → mark ready |

## Asset types → tool (the split from the character-factory review)
- **character** (mascot/animal that moves) → **AnimatedDrawings factory** (`kids-animation-story-creator`). 4 already ready: Ellie/Rio/Milo/Bruno = the `characters/*.gif`. Same cast as the YouTube videos → one brand world across the funnel.
- **prop** (apple, coin, shape) → **gpt-image-1.5** via litellm. Static, cheap, consistent `STYLE` prompt.
- **background** (classroom, market) → gpt-image.

## How worksheets consume the pool (the item convention)
A Grammar item can carry, anywhere it shows an object:
```json
{ "asset": "cow" }              // pooled art if ready, else 🐄
{ "emoji": "🍎", "asset": "apple" }   // emoji is the explicit fallback
```
Render with `KidsAssets.node(token, sizePx)` → a DOM node (art or emoji). `worksheet.js` archetypes that
currently inline emoji (count_write, match, odd_one_out…) swap to `KidsAssets.node()` — backward compatible:
no manifest / not-ready ⇒ emoji, exactly as today.

## Everyday commands
```bash
cd kids_quiz/asset_pool
python3 asset_pool.py status                       # ready vs needed
python3 asset_pool.py scan ../../lms/app/static/kids/  # what art do the worksheets reference?
python3 asset_pool.py request penguin,rocket --emoji 🐧 --type prop
python3 asset_pool.py plan --type prop --out to_generate.json
# then on the EC2 GPU box (litellm up):
python3 gen_assets.py --batch to_generate.json --type prop     # generate props (no GPU needed)
python3 gen_assets.py --batch to_generate.json --type character # characters (AnimatedDrawings env)
```

## Status (2026-08-02)
- ✅ Registry + resolver + brain + generator all built and **verified** (resolver: ready→img, needed→emoji; scan detected apple×3/cow×2/… from the worksheet files).
- ✅ 4 characters ready · 21 props/backgrounds `needed` (emoji fallback live).
- 🟡 Offline generation not yet run — needs the EC2 box up (litellm for props; AnimatedDrawings env for characters). Props don't need the GPU, only the litellm endpoint.
- 🟡 `worksheet.js` still inlines emoji — swap the emoji-bearing archetypes to `KidsAssets.node()` (small, backward-compatible edit) so ready art actually shows.

## Coordination
- **Character factory** = the `kids-animation-story-creator` skill / EC2 AnimatedDrawings env. `gen_assets.py` calls `factory.build()` there; if not importable it prints the exact command.
- **Avatar/UI session** owns `characters/*` and the on-screen guide — the pool *reuses* those character files, doesn't regenerate them. Coordinate before changing anything under `characters/`.
- **Deploy**: new art lands under `static/kids/assets/`; ship via the normal kids-app deploy (whole `lms/` snapshot). `KidsAssets` picks it up on next load.
