#!/usr/bin/env python3
"""
Pipeline stage: image -> short animated clip via local LTX-Video (ComfyUI API).
Animates a still (our generated hero images) into a few-second clip.
Runs on EC2; ComfyUI server must be up at 127.0.0.1:8188.

Usage:
  python3 image_to_clip.py --image assets/img_party_crowd.png \
     --prompt "a crowded party, dark silhouettes, gentle ambient motion, one figure glowing warmly" \
     --out /home/ubuntu/youtube_series/clips/party.mp4 --frames 97 --width 768 --height 448
"""
import os, sys, json, time, argparse, uuid, urllib.request, urllib.parse, subprocess

SRV="http://127.0.0.1:8188"

def post(path, data, headers=None):
    req=urllib.request.Request(SRV+path, data=data, headers=headers or {})
    return urllib.request.urlopen(req, timeout=60).read()

def get(path):
    return urllib.request.urlopen(SRV+path, timeout=60).read()

def upload_image(path):
    import io
    name=os.path.basename(path)
    boundary="----b"+uuid.uuid4().hex
    body=io.BytesIO()
    def w(s): body.write(s if isinstance(s,bytes) else s.encode())
    w(f"--{boundary}\r\n"); w(f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n')
    w("Content-Type: image/png\r\n\r\n"); w(open(path,"rb").read()); w("\r\n")
    w(f"--{boundary}\r\n"); w('Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n')
    w(f"--{boundary}--\r\n")
    r=post("/upload/image", body.getvalue(), {"Content-Type":f"multipart/form-data; boundary={boundary}"})
    return json.loads(r)["name"]

def workflow(img, prompt, neg, W, H, frames, steps, cfg, seed):
    return {
        "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"ltxv-2b-0.9.8-distilled.safetensors"}},
        "2":{"class_type":"CLIPLoader","inputs":{"clip_name":"t5xxl_fp8_e4m3fn.safetensors","type":"ltxv","device":"default"}},
        "3":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["2",0]}},
        "4":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["2",0]}},
        "5":{"class_type":"LoadImage","inputs":{"image":img}},
        "6":{"class_type":"LTXVImgToVideo","inputs":{"positive":["3",0],"negative":["4",0],"vae":["1",2],
              "image":["5",0],"width":W,"height":H,"length":frames,"batch_size":1,"strength":1.0}},
        "7":{"class_type":"LTXVConditioning","inputs":{"positive":["6",0],"negative":["6",1],"frame_rate":25.0}},
        "8":{"class_type":"KSampler","inputs":{"model":["1",0],"positive":["7",0],"negative":["7",1],
              "latent_image":["6",2],"seed":seed,"steps":steps,"cfg":cfg,"sampler_name":"euler",
              "scheduler":"sgm_uniform","denoise":1.0}},
        "9":{"class_type":"VAEDecode","inputs":{"samples":["8",0],"vae":["1",2]}},
        "10":{"class_type":"SaveWEBM","inputs":{"images":["9",0],"filename_prefix":"ltx_clip","codec":"vp9","fps":25.0,"crf":18.0}},
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--image",required=True); ap.add_argument("--prompt",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--neg",default="worst quality, blurry, jittery, warped, flickering, distorted faces, text")
    ap.add_argument("--width",type=int,default=768); ap.add_argument("--height",type=int,default=448)
    ap.add_argument("--frames",type=int,default=97); ap.add_argument("--steps",type=int,default=10)
    ap.add_argument("--cfg",type=float,default=1.0); ap.add_argument("--seed",type=int,default=42)
    a=ap.parse_args()

    print(">> uploading image", flush=True)
    name=upload_image(a.image)
    wf=workflow(name,a.prompt,a.neg,a.width,a.height,a.frames,a.steps,a.cfg,a.seed)
    print(">> submitting workflow", flush=True)
    r=json.loads(post("/prompt", json.dumps({"prompt":wf}).encode(), {"Content-Type":"application/json"}))
    pid=r["prompt_id"]
    print(f">> prompt_id {pid} — generating (A10G is slow, be patient)", flush=True)
    out_file=None
    t0=time.time()
    while True:
        h=json.loads(get(f"/history/{pid}"))
        if pid in h:
            outs=h[pid]["outputs"]
            for node in outs.values():
                for key in ("images","gifs","videos"):
                    if key in node and node[key]:
                        out_file=node[key][0]; break
            if out_file: break
            if h[pid].get("status",{}).get("status_str")=="error":
                print("ERROR in workflow:", json.dumps(h[pid]["status"])[:800]); sys.exit(1)
        if time.time()-t0>900: print("timeout"); sys.exit(1)
        time.sleep(5)
    print(f">> done in {time.time()-t0:.0f}s: {out_file['filename']}", flush=True)
    q=urllib.parse.urlencode({"filename":out_file["filename"],"subfolder":out_file.get("subfolder",""),"type":out_file.get("type","output")})
    raw=get(f"/view?{q}")
    tmp="/tmp/_ltx_raw"+os.path.splitext(out_file["filename"])[1]
    open(tmp,"wb").write(raw)
    os.makedirs(os.path.dirname(a.out),exist_ok=True)
    subprocess.run(["ffmpeg","-y","-i",tmp,"-c:v","libx264","-pix_fmt","yuv420p","-crf","20",a.out],capture_output=True)
    print(f"✅ clip: {a.out} ({os.path.getsize(a.out)//1024} KB)", flush=True)

if __name__=="__main__": main()
