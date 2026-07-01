#!/usr/bin/env python3
"""Runs ON EC2. LTX 2B distilled i2v for square persona thumbnails (gold-cosmic)."""
import json, time, urllib.request
COMFY="http://127.0.0.1:8188"; CKPT="ltxv-2b-0.9.8-distilled.safetensors"; T5="t5xxl_fp8_e4m3fn.safetensors"
W,H,LENGTH,FPS,STEPS,CFG,FR=512,512,97,24,8,1.0,24.0
NEG="low quality, worst quality, deformed, distorted, blurry, jpeg artifacts, watermark, text, flicker"
PROMPTS={
 "curious.png":     "A cosmic eye gently shimmers, galaxies slowly swirl within the iris, golden light sparkles and reflects, particles drift. Smooth subtle looping motion, dark, cinematic.",
 "futureproof.png": "A golden seedling of light gently sways and pulses, particles of light rise upward continuously, soft shimmer. Smooth subtle looping motion, dark, cinematic.",
 "noncoder.png":    "Glowing words and voice waves softly ripple and flow into a luminous holographic app panel that gently pulses, golden particles drift. Smooth subtle looping motion, dark.",
 "builder.png":     "Golden luminous hands and a holographic 3D construct gently rotate and assemble, sparks of light drift and twinkle. Smooth subtle looping motion, dark, cinematic.",
}
def graph(img,prompt,seed):
    return {
     "ckpt":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":CKPT}},
     "clip":{"class_type":"CLIPLoader","inputs":{"clip_name":T5,"type":"ltxv"}},
     "img":{"class_type":"LoadImage","inputs":{"image":img}},
     "pos":{"class_type":"CLIPTextEncode","inputs":{"clip":["clip",0],"text":prompt}},
     "neg":{"class_type":"CLIPTextEncode","inputs":{"clip":["clip",0],"text":NEG}},
     "i2v":{"class_type":"LTXVImgToVideo","inputs":{"positive":["pos",0],"negative":["neg",0],"vae":["ckpt",2],"image":["img",0],"width":W,"height":H,"length":LENGTH,"batch_size":1,"strength":1.0}},
     "cond":{"class_type":"LTXVConditioning","inputs":{"positive":["i2v",0],"negative":["i2v",1],"frame_rate":FR}},
     "sched":{"class_type":"LTXVScheduler","inputs":{"steps":STEPS,"max_shift":2.05,"base_shift":0.95,"stretch":True,"terminal":0.1}},
     "samp":{"class_type":"KSamplerSelect","inputs":{"sampler_name":"euler"}},
     "ks":{"class_type":"SamplerCustom","inputs":{"model":["ckpt",0],"add_noise":True,"noise_seed":seed,"cfg":CFG,"positive":["cond",0],"negative":["cond",1],"sampler":["samp",0],"sigmas":["sched",0],"latent_image":["i2v",2]}},
     "dec":{"class_type":"VAEDecode","inputs":{"samples":["ks",0],"vae":["ckpt",2]}},
     "vid":{"class_type":"CreateVideo","inputs":{"images":["dec",0],"fps":float(FPS)}},
     "save":{"class_type":"SaveVideo","inputs":{"video":["vid",0],"filename_prefix":"personathumbs/"+img.split(".")[0],"format":"mp4","codec":"h264"}},
    }
def queue(g):
    req=urllib.request.Request(COMFY+"/prompt",data=json.dumps({"prompt":g}).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())["prompt_id"]
def wait(pid,t=900):
    s=time.time()
    while time.time()-s<t:
        h=json.loads(urllib.request.urlopen(COMFY+f"/history/{pid}").read())
        if pid in h and h[pid]["status"].get("completed"): return h[pid]
        if pid in h and h[pid]["status"].get("status_str")=="error": raise RuntimeError("err")
        time.sleep(4)
    raise TimeoutError
seed=44011
for img,prompt in PROMPTS.items():
    print(f"\n=== {img} ===",flush=True); pid=queue(graph(img,prompt,seed)); print("queued",pid,flush=True)
    res=wait(pid); saved=[f["filename"] for o in res["outputs"].values() for k in ("videos","gifs","images") for f in o.get(k,[])]
    print("done ->",saved,flush=True); seed+=137
