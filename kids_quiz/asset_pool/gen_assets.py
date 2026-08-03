#!/usr/bin/env python3
"""
gen_assets.py — the OFFLINE GENERATOR for the kids asset pool. Runs where the endpoints live
(the EC2 GPU box: litellm at localhost:4000 for gpt-image; the AnimatedDrawings factory for
characters). Consumes to_generate.json (from asset_pool.py plan), generates each asset, saves a
web asset under lms/app/static/kids/assets/, and flips the manifest entry to `status: ready`.

  props / backgrounds  → gpt-image-1.5 via litellm  → transparent/flat PNG
  characters           → AnimatedDrawings factory    → rigged animated clip (GIF/WebP)

Never runs in the worksheet request path — this is the OFFLINE fill. Generate the batch, then the
browser (KidsAssets) auto-swaps emoji → art on next load.

Usage (on the GPU box, after scp'ing to_generate.json + this repo):
  python3 gen_assets.py --batch to_generate.json                 # everything in the batch
  python3 gen_assets.py --batch to_generate.json --type prop     # props only (no GPU needed)
  python3 gen_assets.py --batch to_generate.json --dry           # print prompts, generate nothing

Env / endpoints:
  LITELLM_URL   default http://localhost:4000/v1
  LITELLM_KEY   default sk-trigunai-master-key-2026
  IMG_MODEL     default gpt-image-1.5
"""
import json, os, sys, argparse, base64

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
KIDS = os.path.join(REPO, "lms", "app", "static", "kids")
MANIFEST = os.path.join(KIDS, "asset_manifest.json")
ASSET_DIR = os.path.join(KIDS, "assets")

# consistent kid art style so every generated prop matches (thick outline, flat, transparent)
STYLE = ("flat 2D cartoon for a children's learning app, thick clean black outline, bright cheerful "
         "colors, simple friendly shapes, centered single object, plain transparent background, no text, "
         "no shadow, sticker style")

# character style: full-body friendly mascot, front-facing, transparent (in-browser CSS gives it motion)
CHAR_STYLE = ("full-body cute cartoon mascot character for a children's learning app, big friendly eyes, "
              "warm smile, standing front-facing friendly pose, thick clean black outline, bright flat "
              "colors, simple rounded shapes, centered, plain transparent background, no text, no shadow, "
              "sticker style")


def prop_prompt(item):
    return item.get("prompt") or f"A single {item.get('label', item['id'])}, {STYLE}."


def gen_prop(item, dry):
    """gpt-image via litellm → PNG under assets/<id>.png. Returns web-relative path or None."""
    prompt = prop_prompt(item)
    if dry:
        print(f"  [dry] prop {item['id']}: {prompt}")
        return None
    import urllib.request
    url = os.environ.get("LITELLM_URL", "http://localhost:4000/v1") + "/images/generations"
    key = os.environ.get("LITELLM_KEY", "sk-trigunai-master-key-2026")
    model = os.environ.get("IMG_MODEL", "gpt-image-1.5")
    body = json.dumps({"model": model, "prompt": prompt, "size": "1024x1024", "n": 1}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    b64 = data["data"][0].get("b64_json")
    os.makedirs(ASSET_DIR, exist_ok=True)
    rel = f"assets/{item['id']}.png"
    with open(os.path.join(KIDS, rel), "wb") as f:
        f.write(base64.b64decode(b64) if b64 else urllib.request.urlopen(data["data"][0]["url"]).read())
    print(f"  ✓ prop {item['id']} → {rel}")
    return rel


def char_prompt(item):
    return item.get("prompt") or f"A {item.get('label', item['id'])}, {CHAR_STYLE}."


def gen_character(item, dry):
    """Generate a character asset. Two backends:
      source 'factory'   → AnimatedDrawings rigged animated clip (needs the AnimatedDrawings env — NOT
                           installed on this box; heavy detectron2 build). Falls through to gpt-image.
      source 'gpt-image' → a full-body static mascot via gpt-image (reliable; in-browser CSS gives motion).
    Static character art is the proven, reliable path; BVH rigging is a later enhancement."""
    label = item.get("label", item["id"])
    if item.get("source") == "factory":
        try:
            from character_factory import factory  # only inside the AnimatedDrawings env
            if not dry:
                rel = f"assets/{item['id']}.gif"
                factory.build(item["id"], label, motion="celebrate", out=os.path.join(KIDS, rel))
                print(f"  ✓ character {item['id']} (rigged) → {rel}")
                return rel
        except Exception:
            print(f"  · AnimatedDrawings env not present → generating {item['id']} as a gpt-image mascot instead")
    # gpt-image static mascot (transparent PNG)
    prompt = char_prompt(item)
    if dry:
        print(f"  [dry] character {item['id']}: {prompt}")
        return None
    import urllib.request
    url = os.environ.get("LITELLM_URL", "http://localhost:4000/v1") + "/images/generations"
    key = os.environ.get("LITELLM_KEY", "sk-trigunai-master-key-2026")
    model = os.environ.get("IMG_MODEL", "gpt-image-1.5")
    body = json.dumps({"model": model, "prompt": prompt, "size": "1024x1024", "n": 1}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    b64 = data["data"][0].get("b64_json")
    os.makedirs(ASSET_DIR, exist_ok=True)
    rel = f"assets/{item['id']}.png"
    with open(os.path.join(KIDS, rel), "wb") as f:
        f.write(base64.b64decode(b64) if b64 else urllib.request.urlopen(data["data"][0]["url"]).read())
    print(f"  ✓ character {item['id']} (static mascot) → {rel}")
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--type", default="", help="only this type (prop/background/character)")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    batch = json.load(open(args.batch, encoding="utf-8"))["items"]
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    done = 0
    for item in batch:
        if args.type and item.get("type") != args.type:
            continue
        t = item.get("type")
        rel = gen_character(item, args.dry) if t == "character" else gen_prop(item, args.dry)
        if rel and item["id"] in manifest["assets"]:
            manifest["assets"][item["id"]]["status"] = "ready"
            manifest["assets"][item["id"]]["web"] = {"static": rel, "anim": rel}
            done += 1
    if done and not args.dry:
        json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"✓ marked {done} asset(s) ready in {MANIFEST}")
        print("  deploy the kids app to publish the new art (KidsAssets auto-swaps emoji → art).")


if __name__ == "__main__":
    main()
