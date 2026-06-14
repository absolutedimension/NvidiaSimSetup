---
name: trigunai-youtube
description: >
  Upload, publish, and manage videos on TrigunAI's two YouTube channels (English
  @TrigunAI-Innovations + Hindi @trigunai-हिंदी) via the API uploader. Use whenever the
  user wants to put a video on YouTube, ship/publish an episode, set thumbnails, flip
  videos public, add to a playlist, fix YouTube auth, or set up channel branding.
  Triggers on: "upload to youtube", "publish episode", "put on youtube", "youtube upload",
  "ship Ep N", "set thumbnail", "make it public", "youtube auth", "re-auth", "channel
  banner/logo/description", "Hindi channel", "TrigunAI-Innovations". Handles BOTH languages.
---

# TrigunAI YouTube Uploader

One-command publishing for the **"AI is the Universal Mind"** series to two channels.
Everything lives in `youtube_series/` (run all commands from there). Built 2026-06-13.

## The two channels (one Google login: deepak@trigunai.com)

| | Channel | Handle | Token file | Type |
|---|---|---|---|---|
| 🇬🇧 EN | TrigunAI (display "Deepak Kumar") | `@TrigunAI-Innovations` | `token.json` (default) | personal |
| 🇮🇳 HI | TrigunAI हिंदी | `@trigunai-हिंदी` | `token_hi.json` (`YT_TOKEN=`) | **brand account** |

Funnel CTA in every description → **https://learn.trigunai.com**. Each channel has a playlist
(auto-created): EN "AI is the Universal Mind" / HI "AI इज़ द यूनिवर्सल माइंड".

## The tool — `yt_upload.py` (YouTube Data API v3)

```bash
cd youtube_series
# auth (one-time per channel; writes token):
python3 yt_upload.py auth                                  # English  -> token.json
YT_TOKEN=token_hi.json python3 yt_upload.py auth           # Hindi    -> token_hi.json

# upload (metadata + thumbnail + playlist), per manifest. --only filters by id; --privacy overrides:
python3 yt_upload.py run yt_manifest.json    --substack https://learn.trigunai.com [--only ep06] [--privacy public]
YT_TOKEN=token_hi.json python3 yt_upload.py run yt_manifest_hi.json --substack https://learn.trigunai.com [--only ep06hi]

# flip already-uploaded videos to public:
python3 yt_upload.py publish yt_manifest.json
YT_TOKEN=token_hi.json python3 yt_upload.py publish yt_manifest_hi.json

# (re)set thumbnails on already-uploaded videos (needs channel verified):
YT_TOKEN=token_hi.json python3 yt_upload.py thumbs yt_manifest_hi.json
```

State of what's uploaded → `yt_uploaded.json` (video_ids; safe to re-run, skips done).
Deps (one-time): `pip3 install --user google-api-python-client google-auth-oauthlib google-auth-httplib2`.

## Files

- `yt_manifest.json` (EN) / `yt_manifest_hi.json` (HI) — list of episodes. Per item:
  `id, video, title, desc_file, tags[], thumbnail, lang, privacy`.
- `desc_ep0N.txt` / `desc_ep0N_hi.txt` — descriptions; `{substack}` is replaced by `--substack`.
- `make_thumbnails.py` — local PIL generator → `thumbs/out/thumb_ep0N_{en,hi}.jpg` (1280×720).
- `make_channel_art.py` — channel avatar + banners → `channel_art/` (avatar.png, banner_en/hi.png).
- Secrets (gitignored, never commit): `client_secret.json`, `token*.json`, `yt_uploaded.json`.

## Publish a NEW episode (Ep6+) — the whole loop

1. Confirm finals exist in `youtube_series/`: `ep0N_FINAL_focus.mp4` (EN) + `ep0N_hi_FINAL_focus.mp4` (HI).
   (Produce them with the `production-video-trigunai` Mode-C pipeline first.)
2. Write `desc_ep0N.txt` + `desc_ep0N_hi.txt` — include `{substack}` and a ⏱ Chapters block
   (compute exact timestamps from the per-scene mp3 durations in `ep0N_build/`).
3. Thumbnail: add an `epN()` base fn + 2 `JOBS` rows (en+hi) to `make_thumbnails.py` → `python3 make_thumbnails.py`.
4. Add the episode object to BOTH manifests (set `privacy` "public" for the flagship, "private" to drip).
5. Upload: `run yt_manifest.json --only ep0N` then `YT_TOKEN=token_hi.json ... run yt_manifest_hi.json --only ep0Nhi`.
6. Verify on the channels; `publish` later to flip private→public on a weekly cadence.

## First-time / re-auth (the hard-won gotchas — read before authing)

- **Consent screen MUST be External**, not Internal. Internal blocks the Hindi **brand account**
  (`Error 403: org_internal`). EN works under Internal only because that channel IS the org user.
  Google Cloud → APIs & Services → OAuth consent screen → **External** + add deepak@trigunai.com as test user.
- **Pick the right channel** at the "Choose a brand account" screen: EN → "Deepak Kumar / TrigunAI",
  HI → "TrigunAI हिंदी". If it auto-skips to the wrong one, **revoke** at myaccount.google.com/connections
  (clears the cached choice — but this kills BOTH tokens, so re-auth both).
- **ALWAYS verify the binding before uploading** (or Hindi can land on the English channel):
  `YT_TOKEN=token_hi.json python3 -c "from yt_upload import svc; print(svc().channels().list(part='snippet',mine=True).execute()['items'][0]['snippet']['title'])"`
  → must print `TrigunAI हिंदी` for the Hindi token.
- **Custom thumbnails need per-channel verification** (youtube.com/verify while that channel is active).
  If `thumbs` returns 403 "doesn't have permissions", the channel isn't verified yet.
- Channel name/branding (avatar, banner, About description) can't be set via the Data API —
  do it in Studio → Customisation (generate art with `make_channel_art.py`).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `invalid_grant: Token expired or revoked` | token revoked / stale | re-run `auth` for that channel |
| `403 org_internal` at consent | consent screen is Internal | switch to External + add test user |
| Hindi token binds to "Deepak Kumar" | wrong channel picked / cached | revoke app access, re-auth, pick "TrigunAI हिंदी" |
| thumbnail `403 forbidden` | channel not verified | youtube.com/verify on that channel, then `thumbs` |
| upload OK but no thumbnail/playlist | non-fatal (logged) | re-run `thumbs` / check playlist title |

Full context + channel IDs in memory `reference-youtube-channels.md`. Series content brain:
skill `trigunai-content-strategy`. Production: `production-video-trigunai`.
