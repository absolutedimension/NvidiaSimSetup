#!/usr/bin/env python3
"""
Part C.3 — RENDER (the assembly line, mirrors progressive_arrange.py's "build the
final artifact" role).

For each shot in the plan:
  1. text->image with Flux + OUR flowscape LoRA   (the signature still)
  2. image->video with LTX-Video                  (gentle 5s motion)
  3. slow-loop pad to hold_seconds (boomerang/crossfade) so it breathes
Then concat all shots -> upscale -> mux the ambient audio bed -> long-form MP4.

Audio = your OWN copyright-clean bed (ACE-Step / FlowArt stack). Pass --audio.

Usage:
  python3 render_flowscape.py --plan scene_plans/flowscape_30min.json \
      --lora loras/flowscape_v1/pytorch_lora_weights.safetensors \
      --audio /home/ubuntu/ambient_bed_30min.mp3
"""
import argparse, json, os, subprocess
import config as C


def img_to_video(pipe_vid, image, seconds, motion):
    # Stable Video Diffusion: image-conditioned, no prompt. `motion` is advisory only;
    # motion amount is set by motion_bucket_id (low = calm ambient drift). SVD-xt emits
    # up to 25 frames; slow_loop() then stretches each clip to the shot hold time.
    import torch
    img = image.resize((C.SVD_W, C.SVD_H))
    return pipe_vid(
        img, decode_chunk_size=8, num_frames=25,
        motion_bucket_id=C.SVD_MOTION_BUCKET, noise_aug_strength=0.02,
        generator=torch.Generator("cpu").manual_seed(0),
    ).frames[0]


def _dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", path], capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


def hold_smooth(clip_mp4, hold_seconds, out_mp4):
    """Slow the SVD clip to fill hold_seconds while KEEPING its living motion —
    motion-compensated interpolation (minterpolate mci) synthesizes true in-between
    frames along the real motion vectors, so it's smooth slow-motion, NOT a loop
    (no boomerang snap). This is the fix for 'images are still' + 'sudden change'."""
    cd = _dur(clip_mp4) or (25.0 / C.SVD_EXPORT_FPS)
    speed = max(1.0, hold_seconds / cd)   # PTS stretch factor
    vf = (f"setpts={speed:.3f}*PTS,"
          f"minterpolate=fps={C.FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    subprocess.run([
        "ffmpeg", "-y", "-i", clip_mp4, "-t", str(hold_seconds),
        "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def xfade_chain(clips, hold, xf, out_mp4):
    """Crossfade-dissolve equal-length clips into one smooth stream (no hard cuts)."""
    if len(clips) == 1:
        subprocess.run(["ffmpeg", "-y", "-i", clips[0], "-c", "copy", out_mp4], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    inputs, fc, last = [], [], "0:v"
    for c in clips:
        inputs += ["-i", c]
    for i in range(1, len(clips)):
        off = i * (hold - xf)
        lbl = f"v{i}"
        fc.append(f"[{last}][{i}:v]xfade=transition=fade:duration={xf}:offset={off:.3f}[{lbl}]")
        last = lbl
    subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", ";".join(fc), "-map", f"[{last}]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--lora", help="flowscape LoRA .safetensors (Part C.1)")
    ap.add_argument("--audio", help="copyright-clean ambient bed (yours)")
    ap.add_argument("--steps", type=int, default=28)
    args = ap.parse_args()

    with open(args.plan) as f:
        plan = json.load(f)
    workdir = os.path.join(C.OUTPUT, plan["name"]); os.makedirs(workdir, exist_ok=True)

    import torch
    from diffusers import StableVideoDiffusionPipeline
    from imagegen import load_pipeline
    pipe_img, gen = load_pipeline()          # SDXL or Flux per config.IMAGE_MODEL
    if args.lora:
        pipe_img.load_lora_weights(args.lora)   # <-- OUR aesthetic
    pipe_vid = StableVideoDiffusionPipeline.from_pretrained(
        C.VIDEO_MODEL, torch_dtype=torch.float16, variant="fp16")
    pipe_vid.enable_model_cpu_offload()

    shot_files = []
    for shot in plan["shots"]:
        i = shot["idx"]
        img = gen(shot["prompt"], seed=1000 + i)
        frames = img_to_video(pipe_vid, img, shot["clip_seconds"], shot["motion"])

        clip = os.path.join(workdir, f"shot_{i:03d}_raw.mp4")
        from diffusers.utils import export_to_video
        export_to_video(frames, clip, fps=C.SVD_EXPORT_FPS)   # low fps => longer motion (3.5s)

        held = os.path.join(workdir, f"shot_{i:03d}.mp4")
        hold_smooth(clip, shot["hold_seconds"], held)          # living motion, no snap
        shot_files.append(held)
        print(f"  shot {i}/{plan['n_shots']} [{shot['beat']}] {shot['scene']}")

    # crossfade-dissolve all shots (holds are equal per plan)
    hold = plan["shots"][0]["hold_seconds"]
    silent = os.path.join(workdir, f"{plan['name']}_silent.mp4")
    xfade_chain(shot_files, hold, C.CROSSFADE, silent)

    # upscale (Real-ESRGAN if present, else scale filter) + mux audio
    final = os.path.join(C.OUTPUT, f"{plan['name']}.mp4")
    vf = f"scale={C.UPSCALE_TO}:-2:flags=lanczos"
    cmd = ["ffmpeg", "-y", "-i", silent]
    if args.audio:
        cmd += ["-stream_loop", "-1", "-i", args.audio, "-shortest",
                "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-vf", vf, "-c:v", "h264_nvenc", "-preset", "p5", "-b:v", "8M", final]
    subprocess.run(cmd, check=True)

    print(f"\nDONE -> {final}")
    print("VERIFY:  python3 vlm_critic.py --mode video --mp4", final)
    print("UPLOAD:  hand to trigunai-yt-flowart / your FlowArt uploader")


if __name__ == "__main__":
    main()
