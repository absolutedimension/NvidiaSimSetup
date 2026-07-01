#!/usr/bin/env python3
"""
Runs ON the EC2 box. Drives ComfyUI LTXV 2B distilled image-to-video for each angle image.
Queues one i2v job per input image, waits, leaves MP4s in ComfyUI/output.
"""
import json, time, urllib.request, urllib.parse, sys

COMFY = "http://127.0.0.1:8188"
CKPT  = "ltxv-2b-0.9.8-distilled.safetensors"
T5    = "t5xxl_fp8_e4m3fn.safetensors"

W, H        = 512, 896      # /32 clean, 9:16
LENGTH      = 97            # 8n+1 -> ~4s @24fps
FPS         = 24
STEPS       = 8            # distilled = few steps
CFG         = 1.0          # distilled = cfg 1
FRAME_RATE  = 24.0

NEG = ("low quality, worst quality, deformed, distorted, disfigured, motion smear, "
       "motion artifacts, fused fingers, bad anatomy, blurry, jpeg artifacts, watermark, text")

# Per-image motion prompts (long & descriptive — LTXV needs detail)
PROMPTS = {
    "front.png": ("Gentle rain falls steadily across a serene garden. The white cherry-blossom "
                  "tree sways softly in the breeze, petals trembling. Raindrops ripple across the "
                  "wet stone path and puddles. Pink and yellow flowers nod gently. Storm clouds "
                  "drift slowly across the overcast sky. Cinematic, atmospheric, calm rainy ambiance."),
    "side.png":  ("Soft rain drifts diagonally over a tranquil garden seen from the side. The "
                  "blossom tree's branches sway, pink petals fluttering down. The stream and wet "
                  "stones glisten with rippling raindrops. Bamboo and foliage rustle in the wind. "
                  "Clouds move slowly overhead. Dreamy, cinematic, peaceful rainfall."),
    "low.png":   ("Looking up at a towering cherry-blossom tree in steady rain, the canopy sways "
                  "and petals scatter against moody storm clouds drifting across the sky. Rain "
                  "streaks downward, flowers below tremble, the wet path shimmers. Dramatic, "
                  "cinematic, immersive rainy atmosphere."),
}

def build_graph(image_name, prompt, seed):
    return {
        "ckpt":  {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "clip":  {"class_type": "CLIPLoader", "inputs": {"clip_name": T5, "type": "ltxv"}},
        "img":   {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "pos":   {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}},
        "neg":   {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": NEG}},
        "i2v":   {"class_type": "LTXVImgToVideo", "inputs": {
                    "positive": ["pos", 0], "negative": ["neg", 0],
                    "vae": ["ckpt", 2], "image": ["img", 0],
                    "width": W, "height": H, "length": LENGTH,
                    "batch_size": 1, "strength": 1.0}},
        "cond":  {"class_type": "LTXVConditioning", "inputs": {
                    "positive": ["i2v", 0], "negative": ["i2v", 1], "frame_rate": FRAME_RATE}},
        "sched": {"class_type": "LTXVScheduler", "inputs": {
                    "steps": STEPS, "max_shift": 2.05, "base_shift": 0.95,
                    "stretch": True, "terminal": 0.1}},
        "samp":  {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "ks":    {"class_type": "SamplerCustom", "inputs": {
                    "model": ["ckpt", 0], "add_noise": True, "noise_seed": seed, "cfg": CFG,
                    "positive": ["cond", 0], "negative": ["cond", 1],
                    "sampler": ["samp", 0], "sigmas": ["sched", 0], "latent_image": ["i2v", 2]}},
        "dec":   {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
        "vid":   {"class_type": "CreateVideo", "inputs": {"images": ["dec", 0], "fps": float(FPS)}},
        "save":  {"class_type": "SaveVideo", "inputs": {
                    "video": ["vid", 0], "filename_prefix": "reel/" + image_name.split(".")[0],
                    "format": "mp4", "codec": "h264"}},
    }

def queue(graph):
    data = json.dumps({"prompt": graph}).encode()
    req = urllib.request.Request(COMFY + "/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())["prompt_id"]

def wait(pid, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = json.loads(urllib.request.urlopen(COMFY + f"/history/{pid}").read())
        if pid in h:
            status = h[pid]["status"]
            if status.get("completed"):
                return h[pid]
            if status.get("status_str") == "error":
                raise RuntimeError("ComfyUI error: " + json.dumps(status)[:500])
        time.sleep(4)
    raise TimeoutError("timed out")

def main():
    seed = 712395695050634
    for img, prompt in PROMPTS.items():
        print(f"\n=== {img} ===", flush=True)
        g = build_graph(img, prompt, seed)
        pid = queue(g)
        print(f"queued {pid}, generating...", flush=True)
        res = wait(pid)
        outs = res["outputs"]
        saved = []
        for nid, o in outs.items():
            for key in ("images", "videos", "gifs"):
                for f in o.get(key, []):
                    saved.append(f["filename"])
        print(f"  done -> {saved}", flush=True)
        seed += 101

if __name__ == "__main__":
    main()
