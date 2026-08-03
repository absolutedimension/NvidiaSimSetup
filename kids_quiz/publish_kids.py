#!/usr/bin/env python3
"""
publish_kids.py — upload rendered kids videos to the TrigunAI-KidsEducation channel.

Uses youtube_series/yt_upload.py with YT_TOKEN=token_kids.json and made_for_kids=True.
Input = items JSON: [{"mp4": abs_path, "adventure": str, "topic": str, "day": int, "slot": int}]

  python3 publish_kids.py --items items.json --privacy public
  python3 publish_kids.py --items items.json --privacy unlisted     # test first
"""
import os, json, subprocess, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
YT_DIR = os.path.join(REPO, "youtube_series")
YT_UPLOAD = os.path.join(YT_DIR, "yt_upload.py")
# interpreter that has the google libs: VM uses kids_quiz/.venv, Mac uses system python3
_VENV = os.path.join(BASE, ".venv", "bin", "python")
PY = os.environ.get("KIDS_PY") or (_VENV if os.path.exists(_VENV) else "/usr/bin/python3")
KIDS_TOKEN = "token_kids.json"          # per-channel token (created once via `auth`)

SITE = "https://kids-education.trigunai.com/"

# human-readable topic label for titles/keywords
TOPIC_LABEL = {
    "place_value": "Place Value", "compare": "Comparing Numbers", "skip_count": "Skip Counting",
    "roman": "Roman Numerals", "ordinal": "Ordinal Numbers", "patterns": "Number Patterns",
    "add": "Addition", "sub": "Subtraction", "mul_fact": "Multiplication Tables",
    "mul_word": "Multiplication Word Problems", "div": "Division", "fraction": "Fractions",
    "money": "Money", "time": "Telling Time", "length": "Length & Measurement",
    "weight": "Weight & Measurement", "shapes": "Shapes & Geometry", "data": "Data Handling",
}

def meta(adventure, topic, day, slot):
    label = TOPIC_LABEL.get(topic, adventure)
    title = f"{adventure} 🗺️ {label} for Kids | Grade 3 Maths Quiz with JJ & Mikey"[:99]
    desc = (
        f"Join JJ 🐰 and Mikey 🐢 on a treasure hunt in {adventure}! Answer 5 fun {label.lower()} "
        f"questions, collect all the gems 💎, and find the treasure 🏆.\n\n"
        f"Perfect for Grade 3 / Class 3 kids (ages 7–9) learning {label.lower()} — a bright, friendly, "
        f"cartoon way to practise maths at home or school. Pause and shout your answer before the timer!\n\n"
        f"🎓 More free kids learning: {SITE}\n"
        f"⭐ New Treasure Trackers maths adventure every day.\n"
        f"👍 Like & subscribe to help JJ & Mikey find more treasure!\n\n"
        f"Great for: Grade 3 maths, Class 3 maths, ICSE / CBSE primary maths, homeschooling, "
        f"kindergarten to primary practice, maths revision, times tables, mental maths.\n\n"
        f"Topic: {label}\n\n"
        f"#mathsforkids #grade3maths #class3maths #{topic.replace('_','')} #kidslearning "
        f"#TreasureTrackers #JJandMikey #funmaths #kidsquiz #learnmaths #mathforkids #primarymaths "
        f"#homeschool #ICSE #CBSE #educationalvideos #kidseducation #mathgames #kidsvideos #cartoonlearning"
    )
    tags = ["maths for kids", "grade 3 maths", "class 3 maths", label, "kids maths quiz",
            "learn maths", "primary maths", "mental maths", "kids learning", "math for kids",
            "educational videos", "Treasure Trackers", "cartoon maths", "ICSE maths", "kids quiz"]
    return title, desc, _cap_tags(tags)   # keep total tag length under YouTube's ~500-char limit

def _cap_tags(tags, limit=440):
    """YouTube rejects (invalidTags) when total tag length exceeds ~500 chars; a multi-word tag
    also costs ~2 extra (quotes). Drop tags once we'd exceed a safe cap."""
    out, total = [], 0
    for t in tags:
        cost = len(t) + (2 if " " in t else 0)
        if total + cost > limit:
            break
        out.append(t); total += cost
    return out

def build_manifest(items):
    eps = []
    for it in items:
        day, slot = it["day"], it["slot"]
        title, desc, tags = meta(it["adventure"], it["topic"], day, slot)
        eps.append({
            "id": f"tt_d{day:02d}_s{slot}_{it['topic']}",     # unique -> dedup via yt_uploaded.json
            "video": os.path.abspath(it["mp4"]),               # absolute -> yt_upload uses as-is
            "title": title, "description": desc, "tags": tags,
            "lang": "en", "made_for_kids": True,
        })
    return {"episodes": eps}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    a = ap.parse_args()
    items = json.load(open(a.items))
    manifest = build_manifest(items)
    mpath = os.path.join(YT_DIR, "_kids_manifest.json")
    json.dump(manifest, open(mpath, "w"), indent=1)
    if not os.path.exists(os.path.join(YT_DIR, KIDS_TOKEN)):
        raise SystemExit(f"!! missing {KIDS_TOKEN}. Run ONE-TIME:\n"
                         f"   cd {YT_DIR} && YT_TOKEN={KIDS_TOKEN} {PY} yt_upload.py auth\n"
                         f"   (sign in + pick the TrigunAI-KidsEducation channel)")
    env = dict(os.environ, YT_TOKEN=KIDS_TOKEN)
    subprocess.run([PY, YT_UPLOAD, "run", mpath, "--privacy", a.privacy], check=True, env=env)

if __name__ == "__main__":
    main()
