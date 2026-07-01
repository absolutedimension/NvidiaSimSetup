#!/usr/bin/env python3
"""LTXV 2B distilled i2v for the brand-vision scenes. Runs ON EC2."""
import json, time, urllib.request

COMFY = "http://127.0.0.1:8188"
CKPT  = "ltxv-2b-0.9.8-distilled.safetensors"
T5    = "t5xxl_fp8_e4m3fn.safetensors"
W, H, LENGTH, FPS, STEPS, CFG = 512, 896, 97, 24, 8, 1.0
NEG = ("low quality, worst quality, deformed, distorted, flicker, motion smear, "
       "motion artifacts, blurry, jpeg artifacts, watermark, text, letters")

PROMPTS = {
    "1_mind.png":   ("A cosmic mind of golden neural light slowly pulses and shimmers, synapses "
                     "sparking gently, threads of light drifting, galaxies rotating slowly in the "
                     "starfield. Ethereal, hypnotic, slow cinematic glow, particles floating."),
    "2_mirror.png": ("A face of liquid starlight slowly ripples and flows, reflections shifting "
                     "like water, golden and silver light drifting across the surface, cosmos "
                     "swirling softly. Dreamlike, slow, ethereal motion, shimmering particles."),
    "3_build.png":  ("Golden data-light and sacred geometry stream slowly upward around a "
                     "meditating silhouette, energy ascending, particles rising, light pulsing "
                     "gently. Serene, hypnotic, slow cinematic, glowing embers floating."),
    "4_clarity.png":("Radiant dawn light slowly blooms and expands from an opening eye, golden "
                     "rays drifting outward through stars, gentle pulsing glow, particles of "
                     "light floating. Awakening, luminous, slow ethereal cinematic motion."),
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
        "cond": {"class_type":"LTXVConditioning","inputs":{"positive":["i2v",0],"negative":["i2v",1],
                 "frame_rate":float(FPS)}},
        "sched":{"class_type":"LTXVScheduler","inputs":{"steps":STEPS,"max_shift":2.05,
                 "base_shift":0.95,"stretch":True,"terminal":0.1}},
        "samp": {"class_type":"KSamplerSelect","inputs":{"sampler_name":"euler"}},
        "ks":   {"class_type":"SamplerCustom","inputs":{"model":["ckpt",0],"add_noise":True,
                 "noise_seed":seed,"cfg":CFG,"positive":["cond",0],"negative":["cond",1],
                 "sampler":["samp",0],"sigmas":["sched",0],"latent_image":["i2v",2]}},
        "dec":  {"class_type":"VAEDecode","inputs":{"samples":["ks",0],"vae":["ckpt",2]}},
        "vid":  {"class_type":"CreateVideo","inputs":{"images":["dec",0],"fps":float(FPS)}},
        "save": {"class_type":"SaveVideo","inputs":{"video":["vid",0],
                 "filename_prefix":"brand/"+img.split(".")[0],"format":"mp4","codec":"h264"}},
    }

def queue(g):
    req = urllib.request.Request(COMFY+"/prompt", data=json.dumps({"prompt":g}).encode(),
                                 headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())["prompt_id"]

def wait(pid, to=900):
    t0=time.time()
    while time.time()-t0<to:
        h=json.loads(urllib.request.urlopen(COMFY+f"/history/{pid}").read())
        if pid in h:
            s=h[pid]["status"]
            if s.get("completed"): return h[pid]
            if s.get("status_str")=="error": raise RuntimeError(json.dumps(s)[:400])
        time.sleep(4)
    raise TimeoutError()

seed=88123456
for img,p in PROMPTS.items():
    print(f"=== {img} ===",flush=True)
    pid=queue(graph(img,p,seed)); print(" queued",pid,flush=True)
    r=wait(pid)
    fs=[f["filename"] for o in r["outputs"].values() for k in ("images","videos","gifs") for f in o.get(k,[])]
    print(" done",fs,flush=True); seed+=137
