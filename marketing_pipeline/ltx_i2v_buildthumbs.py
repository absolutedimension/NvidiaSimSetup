#!/usr/bin/env python3
"""Runs ON EC2. LTX 2B distilled i2v for square brand card thumbnails. Subtle looping motion."""
import json, time, urllib.request

COMFY = "http://127.0.0.1:8188"
CKPT  = "ltxv-2b-0.9.8-distilled.safetensors"
T5    = "t5xxl_fp8_e4m3fn.safetensors"
W, H, LENGTH, FPS, STEPS, CFG, FR = 512, 512, 97, 24, 8, 1.0, 24.0
NEG = "low quality, worst quality, deformed, distorted, blurry, jpeg artifacts, watermark, text, flicker"

PROMPTS = {
    "ai_agents.png": ("A glowing violet AI orb of neural filaments pulses gently and breathes with light, "
                      "concentric sound-wave rings ripple outward continuously, tiny particles drift upward, "
                      "soft shimmering energy. Smooth subtle looping motion, dark background, cinematic."),
    "xr_vr.png":     ("A sleek VR headset rotates very slowly in place, holographic teal UI panels drift and "
                      "softly glow around it, gentle light pulses. Smooth subtle looping motion, dark, cinematic."),
    "fullstack.png": ("Electric-blue data streams flow steadily along a glowing network of server nodes, "
                      "nodes pulse with light, code particles drift upward. Smooth subtle looping motion, dark."),
    "robotics.png":  ("Glowing orange motion-trajectory rings rotate smoothly around a robotic arm in a dark "
                      "simulation grid, rim light shimmers, subtle energy pulse. Smooth subtle looping motion."),
}

def graph(img, prompt, seed):
    return {
        "ckpt": {"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":CKPT}},
        "clip": {"class_type":"CLIPLoader","inputs":{"clip_name":T5,"type":"ltxv"}},
        "img":  {"class_type":"LoadImage","inputs":{"image":img}},
        "pos":  {"class_type":"CLIPTextEncode","inputs":{"clip":["clip",0],"text":prompt}},
        "neg":  {"class_type":"CLIPTextEncode","inputs":{"clip":["clip",0],"text":NEG}},
        "i2v":  {"class_type":"LTXVImgToVideo","inputs":{"positive":["pos",0],"negative":["neg",0],
                 "vae":["ckpt",2],"image":["img",0],"width":W,"height":H,"length":LENGTH,
                 "batch_size":1,"strength":1.0}},
        "cond": {"class_type":"LTXVConditioning","inputs":{"positive":["i2v",0],"negative":["i2v",1],"frame_rate":FR}},
        "sched":{"class_type":"LTXVScheduler","inputs":{"steps":STEPS,"max_shift":2.05,"base_shift":0.95,"stretch":True,"terminal":0.1}},
        "samp": {"class_type":"KSamplerSelect","inputs":{"sampler_name":"euler"}},
        "ks":   {"class_type":"SamplerCustom","inputs":{"model":["ckpt",0],"add_noise":True,"noise_seed":seed,"cfg":CFG,
                 "positive":["cond",0],"negative":["cond",1],"sampler":["samp",0],"sigmas":["sched",0],"latent_image":["i2v",2]}},
        "dec":  {"class_type":"VAEDecode","inputs":{"samples":["ks",0],"vae":["ckpt",2]}},
        "vid":  {"class_type":"CreateVideo","inputs":{"images":["dec",0],"fps":float(FPS)}},
        "save": {"class_type":"SaveVideo","inputs":{"video":["vid",0],"filename_prefix":"buildthumbs/"+img.split(".")[0],"format":"mp4","codec":"h264"}},
    }

def queue(g):
    data=json.dumps({"prompt":g}).encode()
    req=urllib.request.Request(COMFY+"/prompt",data=data,headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())["prompt_id"]

def wait(pid,timeout=900):
    t0=time.time()
    while time.time()-t0<timeout:
        h=json.loads(urllib.request.urlopen(COMFY+f"/history/{pid}").read())
        if pid in h and h[pid]["status"].get("completed"): return h[pid]
        if pid in h and h[pid]["status"].get("status_str")=="error": raise RuntimeError("err "+json.dumps(h[pid]["status"])[:300])
        time.sleep(4)
    raise TimeoutError

seed=99221
for img,prompt in PROMPTS.items():
    print(f"\n=== {img} ===",flush=True)
    pid=queue(graph(img,prompt,seed)); print("queued",pid,flush=True)
    res=wait(pid)
    saved=[f["filename"] for o in res["outputs"].values() for k in ("videos","gifs","images") for f in o.get(k,[])]
    print("done ->",saved,flush=True)
    seed+=137
