---
name: studio-faceless
description: "Produce FACELESS photoreal b-roll explainer videos on the EC2 render farm — real-life AI-generated footage (gpt-image-1.5 → LTX-Video), clear voiceover (edge-tts), word-synced kinetic captions, scene labels, soft music bed. No talking head. Use for: 'faceless explainer', 'b-roll explainer', 'video with real footage', 'documentary-style explainer', 'explain it with real photos/video', 'perspective video', 'same style as the agent video', 'concept video with real footage'. NOT for shader/motion-graphics produced video (studio-video) or audio-only (studio-music)."
metadata: { "openclaw": { "emoji": "🎞️", "requires": { "bins": ["ssh", "scp"] } } }
---

# studio-faceless — Faceless Photoreal Explainer

Drive the faceless pipeline on EC2: photoreal stills (gpt-image-1.5) → motion clips (LTX-Video) → voiceover + kinetic captions + music bed → finished MP4. No talking head, documentary feel.

## When to Use
✅ "Real footage" explainers, perspective videos, concept videos with photoreal b-roll.

## When NOT to Use
❌ Shader / motion-graphics produced video → `studio-video`. ❌ Audio only → `studio-music`. ❌ No script → `studio-script` first (needs `label` + `narration` + `shots` per scene).

## Step 0 — reach the farm (RETRY) + START COMFYUI
Read `TOOLS.md`. IP is the permanent Elastic IP — never ask for a new one. sshd is intermittently slow, so RETRY:
```bash
source ~/.openclaw/ec2.env
farm_up=0; for i in 1 2 3 4 5; do
  ssh -i "$EC2_KEY" -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o BatchMode=yes "$EC2_USER@$EC2_IP" 'nvidia-smi --query-gpu=name --format=csv,noheader' 2>/dev/null | grep -q A10G && { farm_up=1; break; }; sleep 8; done
[ "$farm_up" = 1 ] && echo "FARM UP" || { echo "FARM DOWN — ask Deepak to Start/Reboot the box (IP stays 34.192.145.204)"; exit 1; }
# LTX needs ComfyUI, which does NOT auto-start:
ssh -i "$EC2_KEY" -o ConnectTimeout=20 "$EC2_USER@$EC2_IP" 'cd ~/ComfyUI && nohup ~/comfyenv/bin/python main.py --listen 127.0.0.1 --port 8188 > ~/comfy_run.log 2>&1 & '
sleep 30
ssh -i "$EC2_KEY" -o ConnectTimeout=20 "$EC2_USER@$EC2_IP" 'curl -s -o /dev/null -w "%{http_code}\n" localhost:8188/system_stats'   # want 200
```

## Options
- **voice** (edge-tts): `en-GB-SoniaNeural`(default, female British) / `en-GB-RyanNeural`(male). Rate default `-2%`.
- **resolution**: 1280×720, 25 fps, 16:9.
- **per scene**: 1–3 distinct photoreal `shots` (never boomerang).

## Pipeline (run on EC2, in `/home/ubuntu`)
```bash
source ~/.openclaw/ec2.env
SSH(){ ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" "cd /home/ubuntu && $1"; }
```
1. **Audio (gate):** `SSH 'python3 gen_agent_audio.py'` → produces `agent_vid_build/{s01.mp3..,full_preview.mp3}`. Pull `full_preview.mp3`, get Deepak's approval BEFORE GPU work.
2. **Images (gpt-image-1.5):** `SSH 'python3 gen_variants.py'` → `agent_vid_build/img2/*.png` + `manifest.json` (1–3 photoreal stills per scene). Optional: pull a contact sheet to review.
3. **Animate + composite (long, ~5–15 min, detached):**
   `SSH 'setsid nohup python3 build_agent_video2.py > /tmp/build_agent.log 2>&1 </dev/null &'` then poll `/tmp/build_agent.log`.
   Output: `/home/ubuntu/agent_vid_build/work2/output.mp4`.
4. **Deliver:** `scp -i "$EC2_KEY" "$EC2_USER@$EC2_IP:/home/ubuntu/agent_vid_build/work2/output.mp4" /tmp/out.mp4` → SendUserFile. Have Deepak watch with sound.

## Gotchas
- **ComfyUI must be started manually** (step 0) or LTX silently fails and the build crashes.
- **Azure image-gen blocks photoreal minors** → child/young scenes must be face-free (hands, toys, objects). Reframe; don't fight it.
- **LTX frame cap 137 (~5.5s)** → longer clips OOM. If LTX fails an image, the build does a Ken-Burns zoom-pan fallback (no boomerang).
- **Never boomerang** — multiple distinct shots fill long narration; single-image scenes freeze-pad to audio.
- **Re-voice cheaply:** keep `_vN.mp4` clips, delete `work2/*_scene.mp4` + `*_base*.mp4`, regen audio + manifest durations, rebuild.
- EC2 `/tmp` ephemeral; keep work under `/home/ubuntu/agent_vid_build/`.
