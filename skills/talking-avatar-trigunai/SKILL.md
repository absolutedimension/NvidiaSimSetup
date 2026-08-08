---
name: talking-avatar-trigunai
description: >
  Generate a lively, cinematic TALKING-AVATAR / lip-sync video on the TrigunAI T4 GPU box. Give
  a face photo OR let it AI-generate the avatar (gpt-image), pick a rich Azure Speech voice, and
  it produces a talking-head MP4 with natural head movement, eye blinks, and a cinematic camera
  move, then delivers the file. Copyright-clean (Azure gpt-image + Azure TTS + the user's photo).
  Use whenever the user wants: "make a talking avatar", "lip-sync video", "talking head",
  "make this photo talk", "AI presenter/spokesperson", "avatar says X", "talking-photo clip",
  "generate an avatar and make it speak", "Acharya presenter video", or to turn a photo + text
  (or photo + audio) into a talking video. Runs the SadTalker + Azure pipeline on the T4
  (azureuser@20.17.162.96). Companion to production-video-trigunai (full narrated videos) and the
  OpenClaw bot skill of the same pipeline (Telegram). This skill is the hands-on Claude version.
---

# talking-avatar-trigunai — lip-sync / talking-avatar video generator

Produces a talking-head video: an avatar face (provided or AI-generated) speaks a line in a rich
Azure voice, with natural head motion + eye blinks + a cinematic camera move. Everything runs on
the **TrigunAI T4 GPU box**; you drive it over SSH, then deliver the MP4 to the user.

## Environment (verify first)

| Item | Value |
|---|---|
| T4 box | `azureuser@20.17.162.96` (Azure NC4as_T4_v3; public IP can change on dealloc) |
| SSH key | `~/Documents/01_Active/NewGPUMachine/ubuntu-new-gp_key.pem` |
| SadTalker lip-sync API | `http://127.0.0.1:8080` (on the box; local only) — `/lipsync`, `/speak`, `/tts` |
| gpt-image + Azure Speech keys | in `~/.music_env` on the box (GPT_IMAGE_KEY, AZURE_SPEECH_KEY) |
| Helpers on the box | `~/make_avatar_image.py`, `~/make_speech.py`, `~/make_cinematic.sh`, `~/tg_send.py` |

Boot check:
```bash
PEM=~/Documents/01_Active/NewGPUMachine/ubuntu-new-gp_key.pem
ssh -i "$PEM" -o ConnectTimeout=15 azureuser@20.17.162.96 'curl -s http://127.0.0.1:8080/health'
```
If SSH times out the box is stopped — start it (Azure portal / `az vm start -g ubuntu-new-gp_group -n ubuntu-new-gpu`), then poll. See memory [[project-t4-music-box]].

## Pipeline — 4 steps (run on the box over SSH)

### Step 1 — the avatar face
- **User provides a photo** → scp it to the box (e.g. `~/face.png`). Clear front-facing face works best.
- **No photo → AI-generate it.** Ask the user for context (gender/age/ethnicity, role/vibe, look,
  background), then:
  ```bash
  python3 ~/make_avatar_image.py "young Indian woman, friendly teacher, warm smile, office background" ~/face.png
  ```
  (Azure gpt-image-1.5; auto-frames a clean front-facing portrait.) Pull it back and show the user
  for approval before animating.

### Step 2 — the voice (Azure Speech)
```bash
python3 ~/make_speech.py "THE TEXT TO SPEAK" indian_female ~/speech.wav [style] [rate] [pitch]
```
Voice menu: `indian_female, indian_female2, indian_male, indian_male2, hindi_female, hindi_male,
hindi_female2, hindi_male2, us_female, us_male, uk_female` (or any full Azure voice id).
Optional style: cheerful / sad / excited / calm / softvoice. rate like `-10%`, pitch like `-2st`.

### Step 3 — lip-sync WITH motion (head movement + eye blinks), no neck dislocation
```bash
curl -s -F image=@$HOME/face.png -F audio=@$HOME/speech.wav \
  "http://127.0.0.1:8080/lipsync?still=false&preprocess=crop&enhancer=gfpgan" -o ~/talking.mp4
```
- `still=false` → natural head movement + eye blinks (dropping `--still`).
- **`preprocess=crop`** → head-and-shoulders crop; avoids the head/neck DISLOCATION that
  `preprocess=full` shows at the start when the head moves. ALWAYS use crop.
- Render is GPU-heavy: ~1.5–3 min. First run after boot is slower (model load).

### Step 4 — cinematic camera move
```bash
bash ~/make_cinematic.sh ~/talking.mp4 ~/talking_final.mp4
```
Adds a slow push-in + gentle drift (ffmpeg zoompan, 1080x1080). Keeps audio.

## Deliver

- **To the user here (Claude):** pull the MP4 to the Mac and send it:
  ```bash
  scp -i "$PEM" azureuser@20.17.162.96:~/talking_final.mp4 <local_dir>/
  ```
  then present it with SendUserFile.
- **To a Telegram chat** (same pipeline as the bot): `python3 ~/tg_send.py <chat_id> ~/talking_final.mp4 "caption"`.

## Voice/look variants
- Steady (no head motion): use `still=true` (skip cinematic if you want a locked shot).
- Photo + text in ONE call (SadTalker's built-in edge-tts, lower-quality voice, faster):
  `curl -F image=@face.png -F text="hello" http://127.0.0.1:8080/speak -o out.mp4`.
- Photo + a user-supplied AUDIO file (no TTS): same `/lipsync` endpoint with their audio.
- True multi-angle / 3D free-viewpoint is NOT native (SadTalker = single viewpoint). For angle
  variety, generate 3/4-left and 3/4-right avatars with make_avatar_image.py and intercut.

## Gotchas
- **Telegram/phone playback**: some players want H.264 — re-encode if needed:
  `ffmpeg -i in.mp4 -c:v libx264 -pix_fmt yuv420p -c:a aac out.mp4`.
- `preprocess=full` + motion = head/neck dislocation at the start → use **crop** (the fix).
- Keys never leave the box (`~/.music_env`); never print them.
- The T4 bills while running (~$0.5/hr). Remind to stop it when idle.

## Copyright
Azure gpt-image + Azure Neural TTS output are licensed for commercial use; combined with the
user's own photo the whole clip is clean. No impersonation of a real named person; follow Azure's
responsible-AI terms.
