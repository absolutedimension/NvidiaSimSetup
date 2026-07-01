# TOOLS: The Render Farm (EC2 A10G)

All heavy media generation runs on the **EC2 GPU box** ("TrigunAI-Omniverse", g5.2xlarge, NVIDIA A10G 24 GB, us-east-1). This CPU box only **directs** it over SSH and **delivers** the result.

## Connection

Connection details live in `~/.openclaw/ec2.env`:

```bash
source ~/.openclaw/ec2.env    # sets EC2_IP, EC2_USER, EC2_KEY
```

- `EC2_KEY` = `~/.ssh/trigunai_key.pem` (already on this box, chmod 600)
- `EC2_USER` = `ubuntu`
- `EC2_IP`  = **`34.192.145.204`** — a **permanent Elastic IP**. It does NOT change on stop/start anymore. **Never ask Deepak for a "new IP"** — the address is fixed.

**Before every production job, verify the box is reachable — ALWAYS RETRY (sshd on this box is intermittently slow; a single attempt often times out even when the box is fine):**

```bash
source ~/.openclaw/ec2.env
farm_up=0
for i in 1 2 3 4 5; do
  if ssh -i "$EC2_KEY" -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o BatchMode=yes \
       "$EC2_USER@$EC2_IP" 'nvidia-smi --query-gpu=name --format=csv,noheader' 2>/dev/null | grep -q A10G; then
    farm_up=1; break
  fi
  sleep 8
done
[ "$farm_up" = 1 ] && echo "FARM UP" || echo "FARM DOWN"
```

**Only if all 5 retries fail** is the farm truly down. In that case the box is **stopped or sshd is hung** (the IP is still `34.192.145.204` — it never changes). Tell Deepak:
> "Render farm unreachable after retries. The box is likely stopped or sshd is hung — please **Start or Reboot** the EC2 box (TrigunAI-Omniverse, us-east-1) in the AWS console. The IP stays `34.192.145.204`, so nothing to send me — just bring it up and I'll run the job."

Use the same retry pattern for the ACTUAL job commands too — wrap each `ssh`/`scp` so a transient timeout retries rather than failing the whole production.

## Running jobs

- **Short jobs** (most music, audio): run synchronously over SSH.
- **Long jobs** (motion-graphics video, LTX faceless builds): launch **detached** and poll the log:
  ```bash
  ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" \
    'cd /home/ubuntu && setsid nohup <cmd> > /tmp/job.log 2>&1 </dev/null & echo pid=$!'
  # then poll: tail -n 5 /tmp/job.log   (ignore tqdm progress bars)
  ```
- **Pull the output** back and deliver it:
  ```bash
  scp -i "$EC2_KEY" "$EC2_USER@$EC2_IP:/home/ubuntu/<output>" /tmp/out_file
  # then SendUserFile /tmp/out_file
  ```

## What's installed on the render farm (do NOT reinstall)

| Capability | Where | Venv / how |
|---|---|---|
| Music (ACE-Step) | `/home/ubuntu/make_music.py` | `~/acestep_venv/bin/python` |
| AI singers (seed-vc) | `/home/ubuntu/singerize.py` | `~/m2_venv/bin/python`, refs in `~/singers/` |
| Video pipeline | `/home/ubuntu/video-creator-backend/` + `compose_welcome.py` / `render_v4.py` | `~/audio_pipeline/venv` |
| Faceless explainer | `gen_agent_audio.py`, `gen_variants.py`, `build_agent_video2.py`, `image_to_clip.py` | system py3 + `~/comfyenv` |
| Voices (F5-TTS) | backend service | in `audio_pipeline/venv` |
| Voices (edge-tts) | for faceless | system py3 |
| Image-gen (gpt-image-1.5) | via LiteLLM proxy `localhost:4000` | auto-starts |
| LTX-Video | ComfyUI `localhost:8188` | `~/comfyenv` — **must start manually** (see below) |
| Blender 4.5 | `blender45` | — |

## ComfyUI (only for faceless / LTX video)

ComfyUI does **not** auto-start. Before any faceless build:
```bash
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" \
  'cd ~/ComfyUI && nohup ~/comfyenv/bin/python main.py --listen 127.0.0.1 --port 8188 > ~/comfy_run.log 2>&1 & '
sleep 30
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" 'curl -s -o /dev/null -w "%{http_code}" localhost:8188/system_stats'  # want 200
```

## Hard rules

- **`/tmp` on EC2 is ephemeral** — wiped on stop. Keep source assets + outputs under `/home/ubuntu/`.
- **Never `rm` under `/home/ubuntu/`** without explicit permission — that's where models + assets live.
- **The box bills ~$1/hr while running.** If you start it for a job, remind Deepak to stop it when done.
- **Push updated scripts before running** if a skill says a script changed (`scp` from this box's `~/studio-scripts/` if present, else the script already lives on EC2).
