#!/usr/bin/env python3
"""
ad_asset_prompts.py  —  the STYLE DELTA for product/ad video.

This is the one thing that really separates an ad from a learning video: WHAT clip
we fetch per scene. The learning engine prompts image-gen for "evocative dark
cinematic scene art"; here we prompt for clean studio product shots / lifestyle
b-roll sized for 9:16 with negative space for the caption.

Three things live here:
  1. PRODUCT_BG_PROMPT / BROLL_PROMPT  — constrained image-gen prompt builders
  2. HOOK_PATTERNS                     — the 3-second hook library (pick per product)
  3. scaffold_ad_script() + gen_assets() — brief -> ad-scene script -> generated stills

Runs on EC2 next to the engine. Image-gen goes through the SAME LiteLLM proxy on
:4000 (gpt-image-1.5) the Content Agents use. Adapt the BRIEF block and run.
"""
import base64, json, os, sys, textwrap, requests

# ---- LiteLLM proxy (same as the engine / Content Agents) ----------------------
PROXY = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000/v1")
KEY   = os.environ.get("LITELLM_KEY", "sk-trigunai-master-key-2026")
IMG_MODEL = "gpt-image-1.5"

# ---- 1. CONSTRAINED PROMPT BUILDERS (the heart of the style) ------------------
# Every product prompt ends with the same hard constraints so the still drops
# cleanly into a 9:16 ad with a caption: vertical framing, studio light, room for
# text, and crucially NO baked-in text/logos/watermarks (those we add ourselves).
_VERTICAL = ("vertical 9:16 composition, subject centered in the upper two-thirds, "
             "generous clean negative space in the lower third for a text caption")
_SQUARE   = "square 1:1 composition, subject centered, clean margins for a text caption"
_NO_TEXT  = ("absolutely no text, no words, no logos, no watermark, no UI chrome, "
             "no captions baked into the image")

def _aspect_clause(aspect):
    return _SQUARE if aspect == "1:1" else _VERTICAL

def product_bg_prompt(product, *, aspect="9:16", backdrop="seamless gradient",
                      brand_colors=None, mood="premium"):
    """Hero product shot on a studio backdrop. `product` = plain description."""
    color = ""
    if brand_colors:
        color = f", backdrop tinted toward {brand_colors[0]}"
    return ", ".join([
        f"professional product photography of {product}",
        f"{backdrop} studio backdrop{color}",
        "soft large softbox key light, gentle rim light, subtle reflection on the floor",
        f"{mood}, high detail, sharp focus, commercial e-commerce look",
        _aspect_clause(aspect), _NO_TEXT,
    ])

def broll_prompt(scene_desc, *, aspect="9:16", mood="cinematic, relatable"):
    """Lifestyle / problem-state b-roll for hook & problem beats."""
    return ", ".join([
        f"lifestyle b-roll photograph: {scene_desc}",
        f"{mood}, natural light, shallow depth of field, authentic, candid",
        _aspect_clause(aspect), _NO_TEXT,
    ])

def ugc_prompt(product, *, aspect="9:16"):
    """UGC sub-mode: looks phone-shot, person holding / using the product."""
    return ", ".join([
        f"casual user-generated style phone photo of a person holding and using {product}",
        "handheld iphone look, indoor natural window light, slightly imperfect framing, authentic",
        _aspect_clause(aspect), _NO_TEXT,
    ])

# ---- 2. HOOK PATTERN LIBRARY (3-second pattern interrupts) ---------------------
# Pick one to seed scene_01. The payload (what makes them stop) must be sayable +
# show-able inside 3 seconds.
HOOK_PATTERNS = {
    "problem":      "Still {pain}? Watch this.",                 # pain = "editing for hours"
    "bold_claim":   "{product} does {job} in {time}.",           # job/time = "a video / 60 seconds"
    "before_after": "This took {old}. Now it takes {new}.",      # old/new = "a day / a minute"
    "price_drop":   "{product} — now {price}.",                  # price = "40% off"
    "question":     "What if {desired} took zero effort?",       # desired = "a finished ad"
    "social_proof": "{count} people switched to {product}.",     # count = "10,000"
    "mistake":      "You're {mistake} wrong. Here's the fix.",   # mistake = "editing videos the"
}

# ---- 3. BRIEF -> AD SCRIPT SCAFFOLD -------------------------------------------
def scaffold_ad_script(brief):
    """
    brief = {
      product, one_liner, submode('P'|'U'), aspect, length_sec, voice, music,
      cta, benefits:[...], social_proof:str|None, hook:{pattern, **fields},
      brand_colors:[...],
    }
    Returns the ad-scene script (frontmatter + scenes) as a markdown string in the
    production-video-trigunai contract. You then refine narration before audio gen.
    """
    hook = brief.get("hook", {"pattern": "problem", "pain": "doing this the hard way"})
    hook_line = HOOK_PATTERNS[hook["pattern"]].format(product=brief["product"], **hook)
    scenes = [("scene_01_hook", hook_line, 3, "fast b-roll, hard cut on last word")]
    scenes.append(("scene_02_product_reveal", f"Meet {brief['product']}.", 3,
                   "hero shot, Ken-Burns push-in, glow pop on reveal"))
    for i, b in enumerate(brief.get("benefits", [])[:3], start=3):
        scenes.append((f"scene_{i:02d}_benefit_{i-2}", b, 4, "hero/screenshot, benefit card slides up"))
    if brief.get("social_proof"):
        n = len(scenes) + 1
        scenes.append((f"scene_{n:02d}_proof", brief["social_proof"], 3, "review quote card / rating stars"))
    n = len(scenes) + 1
    cta = brief.get("cta", "Link in bio.")
    scenes.append((f"scene_{n:02d}_cta", cta, 4, "product + offer card, brand logo, end on offer"))

    fm = textwrap.dedent(f"""\
    ---
    title: "{brief['product']} — Ad Reel"
    video_type: reel
    submode: {brief.get('submode','P')}
    length_target_sec: {brief.get('length_sec', sum(s[2] for s in scenes))}
    aspect: {brief.get('aspect','9:16')}
    voice: {{ name: {brief.get('voice','female_excited')}, speed: 0.95 }}
    music: {brief.get('music','energetic')}
    presenter: {'circular' if brief.get('submode')=='U' else 'none'}
    caption_style: kinetic_center
    brand_colors: {json.dumps(brief.get('brand_colors', ['#6C5CE7','#0B0B12']))}
    cta: "{cta}"
    ---

    ## scenes
    """)
    body = []
    for sid, line, dur, vis in scenes:
        cap = " ".join(line.replace("—", " ").split()[:4])  # 1-4 word caption seed
        body.append(textwrap.dedent(f"""\
        ### {sid}
        narration: |
          {line}
        on_screen: {{ caption: "{cap}", layout: center }}
        visual: {vis}
        duration_hint_sec: {dur}
        """))
    return fm + "\n".join(body)

# ---- image-gen call (gpt-image-1.5 via LiteLLM) -------------------------------
def gen_image(prompt, out_path, size="1024x1536"):  # 1024x1536 ~= 9:16
    r = requests.post(f"{PROXY}/images/generations",
                      headers={"Authorization": f"Bearer {KEY}"},
                      json={"model": IMG_MODEL, "prompt": prompt, "size": size, "n": 1},
                      timeout=180)
    r.raise_for_status()
    d = r.json()["data"][0]
    raw = base64.b64decode(d["b64_json"]) if "b64_json" in d else requests.get(d["url"]).content
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path

# ---- EXAMPLE (adapt + run on EC2) ---------------------------------------------
if __name__ == "__main__":
    BRIEF = {
        "product": "ZenSpace, an AI video maker",
        "one_liner": "type a topic, get a finished video",
        "submode": "P", "aspect": "9:16", "length_sec": 28,
        "voice": "female_excited", "music": "energetic",
        "cta": "First 100 get 40% off — link in bio.",
        "benefits": ["Type a topic. Get a finished video.",
                     "No camera. No editing. No team.",
                     "Vertical, ready for Reels and Shorts."],
        "social_proof": None,
        "hook": {"pattern": "problem", "pain": "editing videos for hours"},
        "brand_colors": ["#6C5CE7", "#0B0B12"],
    }
    script = scaffold_ad_script(BRIEF)
    print(script)
    # To also generate the hero stills, uncomment:
    # os.makedirs("/home/ubuntu/ad_build/assets", exist_ok=True)
    # gen_image(product_bg_prompt(BRIEF["product"], brand_colors=BRIEF["brand_colors"]),
    #           "/home/ubuntu/ad_build/assets/hero_reveal.png")
