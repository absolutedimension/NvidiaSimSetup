#!/usr/bin/env python3
"""
content_engine/publish.py
Build YouTube titles/descriptions/tags from a rendered video + its content JSON,
write a manifest, and upload via youtube_series/yt_upload.py to the right channel.

Usage:
  publish.py --items items.json --privacy public
where items.json = [ {mp4, content_json, format, exam, subject, chapter, lang}, ... ]
Groups by lang -> EN uses token.json (channel "TrigunAI"), HI uses token_hi.json.
"""
import os, sys, json, re, subprocess, argparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YT_DIR = os.path.join(REPO, "youtube_series")
YT_UPLOAD = os.path.join(YT_DIR, "yt_upload.py")
PY = "/usr/bin/python3"                       # interpreter that has the google libs
CTA = "https://acharya.trigunai.com/exam-prep"

def _short_exam(exam):
    return {"JEE Advanced": "JEE Advanced", "JEE Main": "JEE Main", "NEET": "NEET"}.get(exam, exam)

def solution_meta(c, exam, subject, chapter):
    topic = c.get("title", chapter)
    title = f"{topic} — {_short_exam(exam)} {subject} Solved Step by Step | Acharya"[:99]
    prose = c.get("q_prose", "").strip()
    desc = (
        f"A REAL {_short_exam(exam)} {subject} question on {chapter}, solved step by step — "
        f"the way a teacher explains it on the board, with every formula worked out.\n\n"
        f"Question: {prose}\n\n"
        f"📝 Practise UNLIMITED exam-pattern JEE & NEET tests — free on Acharya:\n{CTA}\n\n"
        f"Acharya is an authentic test-paper engine: it generates real-pattern JEE (Main & "
        f"Advanced) and NEET papers with fully worked solutions — unlimited practice, instant answers.\n\n"
        f"Topic: {chapter}\nExam: {_short_exam(exam)} · {subject}\n\n"
        f"#JEE #NEET #{subject.replace(' ','')} #{_short_exam(exam).replace(' ','')} "
        f"#IITJEE #ExamPrep #StepByStep #Acharya"
    )
    tags = ["JEE", "NEET", "IIT JEE", exam, subject, chapter, "exam prep",
            "step by step solution", "JEE physics", "Acharya", "TrigunAI"]
    return title, desc, tags

def quiz_meta(c, exam, subject, chapter):
    title = f"{chapter} — {_short_exam(exam)} {subject} Quiz · Beat the Timer! #shorts"[:99]
    desc = (
        f"3 REAL {_short_exam(exam)} {subject} questions on {chapter}. Can you beat the timer?\n\n"
        f"📝 Get your FULL adaptive {_short_exam(exam)} test — free on Acharya:\n{CTA}\n\n"
        f"Acharya generates unlimited, exam-pattern JEE & NEET practice with instant answers.\n\n"
        f"#shorts #{_short_exam(exam).replace(' ','')} #NEET #JEE #{subject.replace(' ','')} "
        f"#{chapter.split('(')[0].strip().replace(' ','')} #ExamPrep #quiz #Acharya"
    )
    tags = ["shorts", exam, subject, chapter, "NEET", "JEE", "quiz", "exam prep", "Acharya", "TrigunAI"]
    return title, desc, tags

def build_manifest(items):
    by_lang = {}
    for it in items:
        c = json.load(open(it["content_json"]))
        if it["format"] == "solution":
            title, desc, tags = solution_meta(c, it["exam"], it["subject"], it["chapter"])
        else:
            title, desc, tags = quiz_meta(c, it["exam"], it["subject"], it["chapter"])
        eid = os.path.splitext(os.path.basename(it["mp4"]))[0]
        ep = {"id": eid, "video": os.path.abspath(it["mp4"]),
              "title": title, "description": desc, "tags": tags, "lang": it.get("lang", "en")}
        by_lang.setdefault(it.get("lang", "en"), []).append(ep)
    return by_lang

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    items = json.load(open(a.items))
    by_lang = build_manifest(items)
    token = {"en": "token.json", "hi": "token_hi.json"}
    for lang, eps in by_lang.items():
        man = {"categoryId": "27", "episodes": eps}   # 27 = Education
        mpath = os.path.join(YT_DIR, f"_auto_manifest_{lang}.json")
        json.dump(man, open(mpath, "w"), ensure_ascii=False, indent=1)
        print(f"\n=== {lang.upper()} channel · {len(eps)} videos ===")
        for e in eps:
            print(f"  • {e['title']}")
        if a.dry_run:
            print(f"  (dry-run; manifest at {mpath})"); continue
        env = dict(os.environ, YT_TOKEN=token.get(lang, "token.json"))
        subprocess.run([PY, YT_UPLOAD, "run", mpath, "--privacy", a.privacy],
                       cwd=YT_DIR, env=env, check=True)

if __name__ == "__main__":
    main()
