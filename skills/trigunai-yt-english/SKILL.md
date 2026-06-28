---
name: trigunai-yt-english
description: >
  Upload / publish / manage videos on the ENGLISH YouTube channel — TrigunAI
  (@TrigunAI-Innovations). The "AI is the Universal Mind" series, VR/MR course, Agentic
  course, Shorts, explainers. Use when the user says: "upload to the English channel",
  "put this on TrigunAI", "publish on the English channel / @TrigunAI-Innovations",
  "english youtube", "main channel upload", "ship this episode (English)". For Hindi use
  trigunai-yt-hindi; for flow/focus music use trigunai-yt-flowart.
---

# Upload to the ENGLISH channel — TrigunAI (@TrigunAI-Innovations)

Token: **`token.json`** (default — no `YT_TOKEN` needed). Run from `youtube_series/`.
Use **`/usr/bin/python3`** (Python 3.9 has the API deps + made the tokens).

```bash
cd /Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/youtube_series
PY=/usr/bin/python3

# 0) ALWAYS verify the token points at the English channel before uploading:
$PY -c "from yt_upload import svc; print(svc().channels().list(part='snippet',mine=True).execute()['items'][0]['snippet']['title'])"
#   → must print: TrigunAI    (if not, run: $PY yt_upload.py auth  → pick 'TrigunAI / Deepak Kumar')

# 1) upload (metadata + thumbnail + playlist), filter with --only:
$PY yt_upload.py run <manifest> --substack "https://learn.trigunai.com" [--only <id>]

# other ops: publish (--to public/unlisted/private) · thumbs · playlist · describe
$PY yt_upload.py publish <manifest> --to public
$PY yt_upload.py thumbs <manifest>
$PY yt_upload.py playlist <manifest>
```

**Manifests on this channel:** `yt_manifest.json` (series Ep1–7), `yt_manifest_modules.json`
(VR/MR course), `yt_manifest_agentic.json` (Agentic course), `yt_manifest_shorts.json`
(reels), `yt_manifest_agent_explainers.json` (What-is-an-AI-Agent set).

**Add a NEW video:** drop the file in place → add an entry to the right manifest
(`id, video, title, desc_file|description, tags[], thumbnail, lang:"en", privacy`) →
`run <manifest> --only <id>`. (Thumbnails via `make_thumbnails.py`.)

**Gotchas:** token may expire (`invalid_grant`) → `$PY yt_upload.py auth`. Videos >15 min &
custom thumbnails need the channel verified (it is). Full reference + troubleshooting:
skill **`trigunai-youtube`**. Memory: `reference-youtube-channels`.
