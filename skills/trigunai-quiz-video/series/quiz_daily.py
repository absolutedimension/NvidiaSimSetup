#!/usr/bin/env python3
"""
Resolve TODAY's 2 quiz topics from schedule.json + series_bank.json, then emit:
  <workdir>/<topic>_en.json, <topic>_hi.json   (engine input, 4 files)
  <workdir>/manifest_en.json, manifest_hi.json  (yt_upload input: 2 EN + 2 HI)

Used by quiz_daily.sh (the 11am cron). Pure stdlib.
  python3 quiz_daily.py --date 2026-07-23 --workdir /tmp/quizday
"""
import os, sys, json, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CTA_LINK = "https://acharya.trigunai.com/exam-prep/quick"

TITLE = {
    "en": "Can you crack this in 5 seconds? ⚡ {chapter} | {subject} #Shorts",
    "hi": "5 सेकंड में हल कर पाओगे? ⚡ {chapter} | {subject} #Shorts",
}
DESC = {
    "en": ("Beat the timer! Two quick {subject} challenges from {chapter}. "
           "Can you get both before the clock runs out?\n\n"
           "\U0001f3af Get your FULL adaptive test that finds exactly where you're weak → {link}\n\n"
           "Acharya is an AI assessment engine for JEE / NEET / Board aspirants — you learn, Acharya tests & tracks.\n\n"
           "#Shorts #JEE #NEET #{stag} #ExamPrep #Acharya"),
    "hi": ("टाइमर को हराओ! {chapter} से दो तेज़ सवाल। "
           "क्या आप समय खत्म होने से पहले दोनों कर पाओगे?\n\n"
           "\U0001f3af अपना पूरा एडाप्टिव टेस्ट लो जो बताता है कि आप कहाँ कमज़ोर हो → {link}\n\n"
           "Acharya एक AI असेसमेंट इंजन है — JEE / NEET / बोर्ड के लिए। आप सीखो, Acharya टेस्ट करे।\n\n"
           "#Shorts #JEE #NEET #ExamPrep #Acharya"),
}

def resolve_day(sched, date_str):
    for d in sched["days"]:
        if d["date"] == date_str:
            return d
    # fallback: day-offset from start_date (keeps working if dates drift)
    start = datetime.date.fromisoformat(sched["start_date"])
    today = datetime.date.fromisoformat(date_str)
    idx = (today - start).days
    if 0 <= idx < len(sched["days"]):
        return sched["days"][idx]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today IST)")
    ap.add_argument("--workdir", default="/tmp/quizday")
    a = ap.parse_args()
    date_str = a.date or (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date().isoformat()
    os.makedirs(a.workdir, exist_ok=True)

    sched = json.load(open(os.path.join(HERE, "schedule.json")))
    bank = json.load(open(os.path.join(HERE, "series_bank.json")))
    day = resolve_day(sched, date_str)
    if not day:
        print(json.dumps({"post": False, "reason": f"no scheduled topics for {date_str}"}))
        return

    man = {"en": [], "hi": []}
    engine_files = []
    for topic in day["topics"]:
        if topic not in bank:
            print(json.dumps({"post": False, "reason": f"topic '{topic}' not authored yet in series_bank.json"}))
            return
        for lang in ("en", "hi"):
            content = bank[topic][lang]
            ejson = os.path.join(a.workdir, f"{topic}_{lang}.json")
            json.dump(content, open(ejson, "w"), ensure_ascii=False, indent=2)
            mp4 = f"{topic}_{lang}.mp4"
            engine_files.append({"json": ejson, "mp4": mp4, "lang": lang, "topic": topic})
            subj, chap = content["subject"], content["chapter"]
            stag = content["subject"] if lang == "hi" else content["subject"].replace(" ", "")
            man[lang].append({
                "id": f"{date_str}_{topic}_{lang}",
                "video": mp4,
                "title": TITLE[lang].format(chapter=chap, subject=subj),
                "description": DESC[lang].format(subject=subj, chapter=chap, stag=stag, link=CTA_LINK),
                "tags": ["JEE", "NEET", subj, "exam prep", "Acharya", chap, "class 11", "physics quiz", "NEET " + subj, "JEE " + subj],
                "lang": lang, "privacy": "public",
            })
    json.dump({"episodes": man["en"]}, open(os.path.join(a.workdir, "manifest_en.json"), "w"), ensure_ascii=False, indent=2)
    json.dump({"episodes": man["hi"]}, open(os.path.join(a.workdir, "manifest_hi.json"), "w"), ensure_ascii=False, indent=2)
    print(json.dumps({"post": True, "date": date_str, "day": day["day"], "topics": day["topics"],
                      "engine_files": engine_files}, ensure_ascii=False))

if __name__ == "__main__":
    main()
