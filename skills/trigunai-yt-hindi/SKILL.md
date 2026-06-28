---
name: trigunai-yt-hindi
description: >
  Upload / publish / manage videos on the HINDI YouTube channel — TrigunAI हिंदी
  (@trigunai-हिंदी), a brand account. Hindi episodes + Hindi VR/MR course. Use when the
  user says: "upload to the Hindi channel", "put this on TrigunAI Hindi", "publish Hindi
  video", "hindi youtube", "हिंदी channel upload". For English use trigunai-yt-english;
  for flow/focus music use trigunai-yt-flowart.
---

# Upload to the HINDI channel — TrigunAI हिंदी (@trigunai-हिंदी)

Token: **`token_hi.json`** → prefix every command with `YT_TOKEN=token_hi.json`.
Run from `youtube_series/`. Use **`/usr/bin/python3`**. It's a **brand account**.

```bash
cd /Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/youtube_series
PY=/usr/bin/python3

# 0) ALWAYS verify the token points at the Hindi channel first (brand-account mixups happen):
YT_TOKEN=token_hi.json $PY -c "from yt_upload import svc; print(svc().channels().list(part='snippet',mine=True).execute()['items'][0]['snippet']['title'])"
#   → must print: TrigunAI हिंदी
#   (if wrong/expired: YT_TOKEN=token_hi.json $PY yt_upload.py auth → at the chooser pick 'TrigunAI हिंदी')

# 1) upload:
YT_TOKEN=token_hi.json $PY yt_upload.py run <manifest> --substack "https://learn.trigunai.com" [--only <id>]

# publish / thumbs / playlist / describe — same, always with YT_TOKEN=token_hi.json
```

**Manifests on this channel:** `yt_manifest_hi.json` (Hindi Ep1–7),
`yt_manifest_modules_hi.json` (Hindi VR/MR course). Hindi items use `lang:"hi"` and
Devanagari titles; thumbnails `thumbs/out/thumb_*_hi.jpg`.

**Add a NEW video:** add the entry to the Hindi manifest → `YT_TOKEN=token_hi.json run <manifest> --only <id>`.

**Gotchas:** brand-account auth — if it binds to "Deepak Kumar"/"TrigunAI", revoke at
myaccount.google.com/connections (kills ALL tokens → re-auth all) OR re-pick at the chooser.
Token may expire (`invalid_grant`) → re-auth. Custom thumbnails / >15-min need channel verified.
Full reference: skill **`trigunai-youtube`**. Memory: `reference-youtube-channels`.
