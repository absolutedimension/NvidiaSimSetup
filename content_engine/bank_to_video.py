#!/usr/bin/env python3
"""
content_engine/bank_to_video.py
Pull REAL questions from the qbank and emit content JSON for the video engines.
  - format=quiz     -> quiz_video/make_quiz_video.py schema (templated narration)
  - format=solution -> solution_video/make_solution_video.py schema (gpt-5.5 authors steps)
Tracks used question ids in used_ledger.json so nothing repeats.

Runs where the qbank + LiteLLM proxy live (Gurukul VM). Local (Mac) use: SSH-tunnel :4000
and point DB at a synced copy.

Usage:
  bank_to_video.py --format quiz --exam NEET --subject Biology \
      --chapter "Human Health and Disease" --n 3 --lang en --out out.json
  bank_to_video.py --format solution --exam "JEE Advanced" --subject Physics \
      --chapter "Modern Physics" --out out.json
"""
import sqlite3, json, re, os, sys, argparse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("QBANK_DB", os.path.expanduser("~/question_bank_engine/data/qbank.sqlite"))
LEDGER = os.path.join(BASE, "used_ledger.json")
LLM_URL = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1") + "/chat/completions"
LLM_KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
MODEL = os.environ.get("QBANK_CHAT_MODEL", "gpt-5.5")
CTA = "acharya.trigunai.com/exam-prep"

BAD_LATEX = re.compile(r"[$\\{}_^]")

def conn(): return sqlite3.connect(DB)

def load_ledger():
    if os.path.exists(LEDGER):
        return set(json.load(open(LEDGER)))
    return set()

def save_ledger(s):
    json.dump(sorted(s), open(LEDGER, "w"))

# ---------------------------------------------------------------- QUIZ
def pick_quiz(c, exam, subject, chapter, n, used):
    rows = c.execute("""SELECT id,stem,options,correct_answer,solution FROM questions
        WHERE exam=? AND subject=? AND chapter=? AND verified=1 AND generated=0
        AND needs_figure=0 AND qtype='MCQ_single' AND solution!=''
        AND stem NOT LIKE '%$$%' """, (exam, subject, chapter)).fetchall()
    clean = []
    for qid, stem, opts_j, ans, sol in rows:
        if qid in used: continue
        try: opts = [o["text"] for o in json.loads(opts_j)]
        except Exception: continue
        if len(opts) != 4: continue
        if any(BAD_LATEX.search(t) or len(t) > 40 for t in opts): continue
        if BAD_LATEX.search(stem) or not (25 < len(stem) < 170): continue
        clean.append((qid, stem, opts, ans, sol))
    # variety of answer positions
    picks, seen_letters = [], []
    for want in ["A", "C", "B", "D"]:
        for q in clean:
            if q[3] == want and q[0] not in [p[0] for p in picks]:
                picks.append(q); break
    for q in clean:                                   # top up if needed
        if len(picks) >= n: break
        if q[0] not in [p[0] for p in picks]: picks.append(q)
    return picks[:n]

def clean_stem(s):
    s = re.sub(r"^\s*(?:Q\.?\s*)?\d{1,3}\s*[\.\)]\s*", "", s)   # strip "106." / "Q5)" prefixes
    return s.strip()

def build_quiz(exam, subject, chapter, picks, lang):
    voice = "en-IN-NeerjaExpressiveNeural" if lang == "en" else "hi-IN-SwaraNeural"
    qs = []
    for (qid, stem, opts, ans, sol) in picks:
        stem = clean_stem(stem)
        ai = ord(ans) - 65
        explain = re.split(r"(?<=[.!?])\s", (sol or "").strip())[0][:120]
        qs.append({
            "type": "mcq", "q": stem, "options": opts, "answer": ai,
            "explain": explain,
            "voice_q": f"{stem} Five seconds... think!",
            "voice_a": f"The answer is {ans} — {opts[ai]}. {explain}",
            "_id": qid,
        })
    return {
        "lang": lang, "voice": voice,
        "exam": f"{exam} · {subject}", "subject": subject, "chapter": chapter,
        "topic_line": f"Real {exam} questions · beat the timer",
        "timer_seconds": 5, "brand": "Acharya",
        "cta": "Full adaptive test on Acharya",
        "intro_voice": f"{subject}. {chapter}. {len(qs)} real exam questions. Beat the timer... let's go!",
        "outro_voice": f"Want a full test on {chapter}? Acharya builds it — unlimited, exam pattern. Link in bio.",
        "questions": qs,
    }

# ---------------------------------------------------------------- SOLUTION
def pick_solution(c, exam, subject, chapter, used):
    rows = c.execute("""SELECT id,stem,options,correct_answer,solution,difficulty FROM questions
        WHERE exam=? AND subject=? AND chapter=? AND verified=1 AND generated=0
        AND needs_figure=0 AND solution!='' AND length(solution)>150
        ORDER BY length(solution) DESC""", (exam, subject, chapter)).fetchall()
    for r in rows:
        if r[0] in used: continue
        return r
    return rows[0] if rows else None

SYS_PROMPT = """You are a master JEE/NEET physics-chemistry-maths teacher writing a
step-by-step video solution. Given a REAL exam question, its correct answer, and a terse
official solution, produce a CLEAN, pedagogically clear worked solution as STRICT JSON.

Rules:
- Output ONLY a JSON object, no prose, no markdown fences.
- 3 to 5 steps. Each step: a short label, 1-2 equations, and a spoken narration.
- Equations use matplotlib-mathtext LaTeX inside $...$. ALLOWED: \\frac \\dfrac \\sqrt \\times
  \\cdot ^ _ \\pi \\omega \\varepsilon \\theta \\Delta \\lambda \\mu \\Rightarrow \\approx
  \\left[ \\right] \\left( \\right) \\mathrm{...} and greek letters.
- FORBIDDEN (breaks the renderer): \\big \\Big \\begin \\end \\text \\tfrac \\substack
  align/matrix environments, and line breaks inside an equation. ONE line per equation.
- Keep each equation compact (fits one screen line).
- Narration: plain spoken English for text-to-speech. Write numbers/symbols as WORDS
  (e.g. "three point four two", "omega L over R"). NO LaTeX in narration. Warm teacher tone.
- The final answer must match the given correct option.

JSON schema:
{
 "title": "<=6-word topic title",
 "q_prose": "the question in clean plain English (no LaTeX except keep it short)",
 "given_eq": "$...$ a key given formula, or empty string",
 "q_reminder": "one short line summarizing what to find",
 "q_narration": "spoken intro reading the problem + 'let us solve step by step'",
 "steps": [ {"label":"Step 1 — ...","eqs":["$...$"],"narration":"..."}, ... ],
 "answer_eq": "$...$ the boxed final answer",
 "answer_label": "Correct option:  X",
 "answer_narration": "spoken conclusion + a one-line invite to Acharya for more"
}"""

def author_solution(exam, subject, chapter, row):
    qid, stem, opts_j, ans, sol, diff = row
    opts = json.loads(opts_j) if opts_j else []
    opt_lines = "\n".join(f"({o['label']}) {o['text']}" for o in opts) if opts else "(numeric answer)"
    user = (f"EXAM: {exam} · {subject} · {chapter}\n\nQUESTION:\n{stem}\n\n"
            f"OPTIONS:\n{opt_lines}\n\nCORRECT ANSWER: {ans}\n\n"
            f"OFFICIAL (terse) SOLUTION:\n{sol}\n\nWrite the JSON now.")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYS_PROMPT},
                     {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(LLM_URL, data=body,
        headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.loads(r.read())
    content = data["choices"][0]["message"]["content"]
    content = re.sub(r"^```(json)?|```$", "", content.strip()).strip()
    obj = json.loads(content)
    # fill fixed fields
    obj["exam_tag"] = f"{exam} · {subject} · {chapter}"
    obj.setdefault("options", [o["text"] for o in opts] if opts else [])
    obj["cta_line"] = "Want the full step-by-step solution to ANY JEE or NEET question?"
    obj["_id"] = qid
    return obj

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True, choices=["quiz", "solution"])
    ap.add_argument("--exam", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()

    c = conn()
    used = set() if a.no_ledger else load_ledger()

    if a.format == "quiz":
        picks = pick_quiz(c, a.exam, a.subject, a.chapter, a.n, used)
        if len(picks) < a.n:
            print(f"WARN only {len(picks)} clean Qs in {a.chapter}", file=sys.stderr)
        if not picks:
            print("ERROR no questions", file=sys.stderr); sys.exit(2)
        obj = build_quiz(a.exam, a.subject, a.chapter, picks, a.lang)
        new_ids = [q["_id"] for q in obj["questions"]]
        for q in obj["questions"]: q.pop("_id", None)
    else:
        row = pick_solution(c, a.exam, a.subject, a.chapter, used)
        if not row:
            print("ERROR no solvable question", file=sys.stderr); sys.exit(2)
        obj = author_solution(a.exam, a.subject, a.chapter, row)
        new_ids = [obj.pop("_id")]

    json.dump(obj, open(a.out, "w"), ensure_ascii=False, indent=1)
    if not a.no_ledger:
        used.update(new_ids); save_ledger(used)
    print(f"OK {a.format} -> {a.out}  ({len(new_ids)} q, chapter={a.chapter})")

if __name__ == "__main__":
    main()
