---
name: studio-youtube
description: "Upload/publish videos to TrigunAI's YouTube channels (English @TrigunAI-Innovations + Hindi @trigunai-हिंदी) via the API uploader on the EC2 box. Use when the user wants to put a video on YouTube: 'upload to youtube', 'publish to my channel', 'post this on youtube', 'put it on youtube', 'upload the video', 'publish episode', 'make it public on youtube', 'upload to the hindi channel', 'ship this to youtube'. Uploads a rendered video (e.g. the one studio-video / studio-faceless just made) straight from the render box. Defaults to PRIVATE — publishing is outward-facing, so confirm title/description/privacy first. NOT for producing video (studio-video/studio-faceless) — this only uploads an existing file."
metadata: { "openclaw": { "emoji": "📺", "requires": { "bins": ["ssh"] } } }
---

# studio-youtube — Publish to YouTube

Uploads a finished MP4 to TrigunAI's channels using `yt_upload.py` (YouTube Data API v3) **on the EC2 box**, where the rendered videos already live (`~/youtube_series/`, finals under `/home/ubuntu/`).

## Channels (one Google login: deepak@trigunai.com)
| Lang | Channel | Handle | Token |
|---|---|---|---|
| 🇬🇧 EN | TrigunAI | `@TrigunAI-Innovations` | `token.json` (default) |
| 🇮🇳 HI | TrigunAI हिंदी | `@trigunai-हिंदी` | `token_hi.json` (`YT_TOKEN=token_hi.json`) |

## ⚠️ Safety — uploading is an outward-facing, public-ish action
- **Always confirm with the user first:** the exact title, description, privacy, and channel.
- **Default privacy = `private`.** Only use `public` if the user explicitly says "public" (or `unlisted` if they say so). Never auto-publish public.
- Standard CTA to include in descriptions: `https://learn.trigunai.com`.

## When to Use
✅ Upload a rendered video to YouTube. ✅ Flip an uploaded video public.

## When NOT to Use
❌ Producing/rendering video → `studio-video` / `studio-faceless`. ❌ No finished MP4 yet — make it first.

## Step 0 — reach the farm (RETRY)
```bash
source ~/.openclaw/ec2.env
farm_up=0; for i in 1 2 3 4 5; do
  ssh -i "$EC2_KEY" -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o BatchMode=yes "$EC2_USER@$EC2_IP" 'nvidia-smi --query-gpu=name --format=csv,noheader' 2>/dev/null | grep -q A10G && { farm_up=1; break; }; sleep 8; done
[ "$farm_up" = 1 ] && echo FARM_UP || { echo "FARM DOWN — ask Deepak to Start/Reboot EC2 (IP stays 34.192.145.204)"; exit 1; }
```

## Upload (confirm details with the user first)
Write a one-item manifest on EC2 (use Python so titles/descriptions with quotes are safe), then run the uploader. `<...>` = fill from the confirmed brief; `VIDEO` = absolute path of the rendered MP4 on EC2 (e.g. `/home/ubuntu/agent_vid_build/work2/output.mp4` from studio-faceless, or `/home/ubuntu/<name>.mp4` from studio-video).

```bash
source ~/.openclaw/ec2.env
SSH(){ ssh -i "$EC2_KEY" -o ConnectTimeout=25 -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"; }

# 1. build the manifest safely on EC2 (edit the values)
SSH '/usr/bin/python3 - <<PY
import json,time
m={"episodes":[{
  "id":"adhoc_%d"%int(time.time()),          # unique so state never skips it
  "video":"VIDEO_ABS_PATH",
  "title":"TITLE",
  "description":"DESCRIPTION\n\nLearn: https://learn.trigunai.com",
  "tags":["TrigunAI","AI"],
  "lang":"en",                                # "hi" for the Hindi channel
  "privacy":"private"                          # private | unlisted | public
}]}
json.dump(m,open("/tmp/yt_one.json","w"));print("manifest written")
PY'

# 2a. upload to the ENGLISH channel
SSH 'cd ~/youtube_series && /usr/bin/python3 yt_upload.py run /tmp/yt_one.json --substack https://learn.trigunai.com 2>&1 | tail -8'

# 2b. OR upload to the HINDI channel
SSH 'cd ~/youtube_series && YT_TOKEN=token_hi.json /usr/bin/python3 yt_upload.py run /tmp/yt_one.json --substack https://learn.trigunai.com 2>&1 | tail -8'
```
The uploader prints `✅ uploaded: https://youtu.be/<id>` — **return that link to the user.**

### Long uploads
Big files take minutes. Launch detached + poll:
```bash
SSH 'cd ~/youtube_series && setsid nohup /usr/bin/python3 yt_upload.py run /tmp/yt_one.json --substack https://learn.trigunai.com > /tmp/yt_up.log 2>&1 </dev/null & echo started'
# poll: SSH 'tail -n 6 /tmp/yt_up.log'   ; done when you see the youtu.be link
```

### Flip an already-uploaded video public later
Re-run with `--privacy public`, or use the `publish` command on a manifest (see the full `trigunai-youtube` reference on the Mac).

## Verify the right channel before HI uploads
Hindi can accidentally land on the English channel if a token is stale. To be safe:
```bash
SSH 'cd ~/youtube_series && YT_TOKEN=token_hi.json /usr/bin/python3 -c "from yt_upload import svc;print(svc().channels().list(part=\"snippet\",mine=True).execute()[\"items\"][0][\"snippet\"][\"title\"])"'
# must print: TrigunAI हिंदी
```

## Gotchas
- Use `/usr/bin/python3` on EC2 (that's where the Google API deps are installed).
- Custom thumbnails need the channel **verified** (youtube.com/verify); plain uploads work without it.
- Young channels have a **~15 uploads/day cap** → `uploadLimitExceeded` means wait ~24h.
- Tokens auto-refresh; if you ever see `invalid_grant`, the token was revoked → re-auth must be done from the Mac (browser flow), then re-copy the token to EC2.
