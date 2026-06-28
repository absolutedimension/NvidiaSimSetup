---
name: trigunai-yt-flowart
description: >
  Upload / publish / manage videos on the FLOWART YouTube channel — TrigunFlowArt
  (@trigunflowart), a brand account for flow-state / focus MUSIC (1-hr isochronic sessions,
  dance & deep work). Use when the user says: "upload to flowart", "put this on
  TrigunFlowArt", "publish the music / flow / focus video", "flowart channel", "upload the
  flow music". For the AI series/courses use trigunai-yt-english / trigunai-yt-hindi.
---

# Upload to the FLOWART channel — TrigunFlowArt (@trigunflowart)

Token: **`token_flowart.json`** → prefix every command with `YT_TOKEN=token_flowart.json`.
Run from `youtube_series/`. Use **`/usr/bin/python3`**. Brand account · chan id
`UCgxzQ52rCCl7FCIDLk81lmg` · category **Music (10)** · assets in `youtube_series/flowart/`.

```bash
cd /Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/youtube_series
PY=/usr/bin/python3

# 0) ALWAYS verify the token points at FlowArt first:
YT_TOKEN=token_flowart.json $PY -c "from yt_upload import svc; print(svc().channels().list(part='snippet',mine=True).execute()['items'][0]['snippet']['title'])"
#   → must print: TrigunFlowArt
#   (if wrong/expired: YT_TOKEN=token_flowart.json $PY yt_upload.py auth → pick 'TrigunFlowArt' at chooser)

# 1) upload music videos (thumbnail + playlist), then set Music category via describe:
YT_TOKEN=token_flowart.json $PY yt_upload.py run yt_manifest_flowart.json
YT_TOKEN=token_flowart.json $PY yt_upload.py describe yt_manifest_flowart.json   # sets categoryId 10 (Music) + descriptions

# publish / thumbs / playlist — same, always with YT_TOKEN=token_flowart.json
```

**Manifest:** `yt_manifest_flowart.json` (has `"categoryId":"10"` + playlist "Flow State &
Focus Music"). Descriptions in `flowart/desc_flow_*.txt` link studio.trigunai.com +
lms.trigunai.com + the VR FlowArt platform, with honest sound-science research (alpha=flow,
beta=focus, isochronic). Thumbnails/channel-art generator: `flowart/make_flowart_assets.py`
→ `flowart/out/`. New music-visualizer videos come from skills `hypnotic-techno-trigunai`
(techno+alpha) / `isochronic-deephouse-trigunai` (house+beta).

**Add a NEW video:** add entry to `yt_manifest_flowart.json` (id, video, title, desc_file,
tags, thumbnail, lang:"en", privacy:"public") → `run` → `describe` (for Music category).

**Gotchas (hour-long music!):** an UNVERIFIED channel caps uploads at **15 min** → 1-hr videos
get removed ("too long"); FlowArt is verified (`longUploadsStatus: allowed`) so they stick.
Custom thumbnails also need verification. Brand-account auth: if it binds to the wrong channel,
re-pick at the chooser. Token may expire → re-auth. Full reference: skill **`trigunai-youtube`**.
Memory: `reference-youtube-channels`.
