"""Client for the /examgen RAG question generator — authentic past-paper-style questions.

Runs on the ALWAYS-ON Gurukul VM (migrated off the EC2 GPU box 2026-07-23) and generates with
Azure **gpt-5.5**. The LMS proxies it server-side so the API key never reaches the browser, and
transforms its LaTeX MCQs (+ optional SVG diagrams) into the assess.html engine's "pack" shape.

Nine exam×subject banks are wired: JEE Advanced + JEE Main (Physics/Chemistry/Maths) and NEET
(Biology/Physics/Chemistry). Add a subject to RAG_SUBJECTS — and to a GOALS entry — to grow
coverage; the bank must already exist on the VM."""
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import settings

# ---- which dashboard topics map to a RAG subject ----
# Every entry here must have a real bank behind it — verify with:
#   curl -sG "$EXAMGEN_URL/chapters" --data-urlencode "exam=NEET" --data-urlencode "subject=Biology"
# `match` = explicit title phrases; `kw` = the subject keyword used once the exam is already known.
RAG_SUBJECTS = {
    # ---- JEE Advanced (the original three) ----
    "jee-physics": {
        "label": "IIT JEE Physics", "exam": "JEE Advanced", "subject": "Physics", "kw": "physics",
        "match": ["jee advanced physics", "iit jee physics", "jee physics", "iit physics",
                  "physics jee", "jee-physics"],
    },
    "jee-chemistry": {
        "label": "IIT JEE Chemistry", "exam": "JEE Advanced", "subject": "Chemistry", "kw": "chem",
        "match": ["jee advanced chemistry", "iit jee chemistry", "jee chemistry", "iit chemistry",
                  "chemistry jee", "jee-chemistry"],
    },
    "jee-maths": {
        "label": "IIT JEE Mathematics", "exam": "JEE Advanced", "subject": "Mathematics", "kw": "math",
        "match": ["jee advanced math", "jee advanced maths", "iit jee math", "jee math", "jee maths",
                  "iit math", "iit maths", "maths jee", "math jee", "jee-maths", "jee-math"],
    },
    # ---- JEE Main ----
    "jeemain-physics": {
        "label": "JEE Main Physics", "exam": "JEE Main", "subject": "Physics", "kw": "physics",
        "match": ["jee main physics", "jee mains physics", "jeemain-physics"],
    },
    "jeemain-chemistry": {
        "label": "JEE Main Chemistry", "exam": "JEE Main", "subject": "Chemistry", "kw": "chem",
        "match": ["jee main chemistry", "jee mains chemistry", "jeemain-chemistry"],
    },
    "jeemain-maths": {
        "label": "JEE Main Mathematics", "exam": "JEE Main", "subject": "Mathematics", "kw": "math",
        "match": ["jee main math", "jee main maths", "jee mains math", "jee mains maths",
                  "jeemain-maths", "jeemain-math"],
    },
    # ---- NEET ----
    "neet-biology": {
        "label": "NEET Biology", "exam": "NEET", "subject": "Biology", "kw": "bio",
        "match": ["neet biology", "neet bio", "neet-biology", "biology neet"],
    },
    "neet-physics": {
        "label": "NEET Physics", "exam": "NEET", "subject": "Physics", "kw": "physics",
        "match": ["neet physics", "neet-physics", "physics neet"],
    },
    "neet-chemistry": {
        "label": "NEET Chemistry", "exam": "NEET", "subject": "Chemistry", "kw": "chem",
        "match": ["neet chemistry", "neet-chemistry", "chemistry neet"],
    },
}

# ---- goals: what a student is actually preparing for → the subjects that serve it ----
# The onboarding screen picks ONE of these; it decides which subjects get seeded as topics and
# which subject Smart Practice falls back to. `subjects` is ordered — first = the default.
GOALS = {
    "jee-advanced": {
        "label": "IIT-JEE (Advanced)", "tag": "Engineering · IIT", "emoji": "⚛️",
        "subjects": ["jee-physics", "jee-chemistry", "jee-maths"],
    },
    "jee-main": {
        "label": "JEE Main", "tag": "Engineering · NIT/IIIT", "emoji": "📐",
        "subjects": ["jeemain-physics", "jeemain-chemistry", "jeemain-maths"],
    },
    "neet": {
        "label": "NEET", "tag": "Medical entrance", "emoji": "🧬",
        "subjects": ["neet-biology", "neet-physics", "neet-chemistry"],
    },
}
DEFAULT_GOAL = "jee-advanced"


def goal_of_subject(subject_id: str) -> str | None:
    """Which goal a RAG subject belongs to (used to infer a goal from existing topics)."""
    for gid, g in GOALS.items():
        if subject_id in g["subjects"]:
            return gid
    return None


# Per-exam difficulty ladder. Each bank is calibrated to a different band, so the SAME
# "Medium/Mix/Hard" pill must map to different values per exam — asking outside the band returns
# few/no exemplars and forces a weaker chapter-only generation. NEET sits at 2–3, JEE Advanced at
# 3–4 (per FRONTEND_HANDOFF_NEET §1 / _IIT §141); JEE Main is between the two.
DIFFICULTY_LADDER = {
    "NEET":         {"easy": "2",   "mix": "2-3", "hard": "3"},
    "JEE Main":     {"easy": "2-3", "mix": "3",   "hard": "3-4"},
    "JEE Advanced": {"easy": "3",   "mix": "3-4", "hard": "4"},
}
_DEFAULT_LADDER = {"easy": "3", "mix": "3-4", "hard": "4"}


def difficulty_ladder(subject_id: str) -> dict:
    """The {easy, mix, hard} difficulty values appropriate to this subject's exam band."""
    cfg = RAG_SUBJECTS.get(subject_id)
    return DIFFICULTY_LADDER.get(cfg["exam"], _DEFAULT_LADDER) if cfg else _DEFAULT_LADDER


def difficulty_for(subject_id: str, mastery: float) -> str:
    """Pick a difficulty from real mastery, on the exam's own band: <50% → easy, <75% → mix, else hard."""
    lad = difficulty_ladder(subject_id)
    return lad["hard"] if mastery >= 0.75 else (lad["mix"] if mastery >= 0.5 else lad["easy"])


def available() -> bool:
    return bool(settings.EXAMGEN_URL and settings.EXAMGEN_KEY)


# Exam-family phrases, longest-first so "jee advanced" wins over "jee" and "jee main" over "jee".
_EXAM_HINTS = [
    ("jee advanced", "JEE Advanced"), ("iit jee", "JEE Advanced"), ("iit-jee", "JEE Advanced"),
    ("jee mains", "JEE Main"), ("jee main", "JEE Main"),
    ("neet", "NEET"),
    ("iit", "JEE Advanced"), ("jee", "JEE Advanced"),
]


def match_subject(title: str, topic_key: str = "") -> str | None:
    """Return a RAG subject id if this dashboard topic is covered by the RAG, else None.

    Two passes: an exact title phrase, then exam-family + subject keyword (so "NEET — Organic
    Chemistry" resolves to neet-chemistry rather than falling through to a JEE subject)."""
    hay = f"{title} {topic_key}".lower()
    for sid, cfg in RAG_SUBJECTS.items():           # explicit phrases first
        if any(kw in hay for kw in cfg["match"]):
            return sid
    for phrase, exam in _EXAM_HINTS:                # then exam family + subject keyword
        if phrase in hay:
            for sid, cfg in RAG_SUBJECTS.items():
                if cfg["exam"] == exam and cfg["kw"] in hay:
                    return sid
            break                                   # exam known but no subject keyword → no match
    return None


# ---- chapters (short-cached PER SUBJECT; one worker so a module cache is fine) ----
# Keyed by subject_id — a single shared slot would serve Physics chapters for Chemistry.
_CH_CACHE: dict = {}


CHAPTERS_TTL = 300   # 5 min — the bank is actively growing, so new chapters appear promptly
# ONE question per /generate call. gpt-5.5 generates AND key-withheld-validates each question
# serially inside the API (~40-55s each, more on a novelty retry), so batching 2+ per call blew the
# request timeout. Fanning out 1-per-call keeps wall-clock ≈ a single question (verified: 3 concurrent
# calls = 54s, i.e. the backend truly parallelises).
MAX_PER_CALL = 1


def get_chapters(subject_id: str = "jee-physics") -> list[dict]:
    """[{chapter, concepts:[...], exemplars_banked}] for the subject. Short-cached. [] on failure."""
    now = time.time()
    ent = _CH_CACHE.get(subject_id)
    if ent and now - ent["at"] < CHAPTERS_TTL:
        return ent["data"]
    cfg = RAG_SUBJECTS.get(subject_id, RAG_SUBJECTS["jee-physics"])
    url = (f"{settings.EXAMGEN_URL}/chapters?exam={urllib.parse.quote(cfg['exam'])}"
           f"&subject={urllib.parse.quote(cfg['subject'])}")
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        chapters = body.get("chapters", []) or []
        _CH_CACHE[subject_id] = {"at": now, "data": chapters}
        return chapters
    except Exception as exc:
        print(f"[examgen] chapters failed ({subject_id}): {exc}")
        return (ent or {}).get("data") or []


def fetch_pool(subject_id: str, chapter: str, concept: str | None = None,
               difficulty: str = "3-4", qtype: str = "MCQ_single", count: int = 5,
               exclude: list[str] | None = None):
    """INSTANT read from the shared pre-generated pool (no LLM, no auth).

    Returns (questions, exhausted). Returns (None, False) when /pool is unavailable — e.g. not yet
    deployed (404) — so the caller transparently falls back to live generation. That's what lets
    this ship before the pool exists and get faster on its own once it lands."""
    cfg = RAG_SUBJECTS.get(subject_id, RAG_SUBJECTS["jee-physics"])
    params = {"exam": cfg["exam"], "subject": cfg["subject"], "chapter": chapter,
              "difficulty": difficulty, "type": qtype, "count": max(1, int(count))}
    if concept:
        params["concept"] = concept
    if exclude:
        params["exclude"] = ",".join(str(x) for x in exclude[:300])
    url = f"{settings.EXAMGEN_URL}/pool?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=25) as resp:
            body = json.loads(resp.read().decode())
        return (body.get("questions") or []), bool(body.get("exhausted"))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:                      # 404 = /pool not deployed yet; stay quiet
            print(f"[examgen] pool HTTP {exc.code}")
        return None, False
    except Exception as exc:
        print(f"[examgen] pool failed: {exc}")
        return None, False


def pool_available() -> bool:
    """Cheap probe so callers/ops can tell whether the instant path is live."""
    qs, _ = fetch_pool("jee-physics", "Kinematics", count=1)
    return qs is not None


def _letter_to_index(letter: str, options: list) -> int:
    """Map a correct-answer letter ('B') to the option's position; fall back to A=0."""
    letter = (letter or "").strip().upper()[:1]
    for i, o in enumerate(options):
        if str(o.get("label", "")).strip().upper() == letter:
            return i
    return {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}.get(letter, 0)


def _generate_one(subject_id: str, chapter: str, concept: str | None,
                  difficulty: str, count: int, require_figure: bool = False) -> list[dict]:
    """One /generate call → list of examgen questions (MCQ_single). [] on failure."""
    cfg = RAG_SUBJECTS.get(subject_id, RAG_SUBJECTS["jee-physics"])
    payload = {
        "exam": cfg["exam"], "subject": cfg["subject"],
        "chapter": chapter, "concept": concept,
        "difficulty": difficulty, "type": "MCQ_single",
        "count": max(1, min(int(count), 10)), "exemplars": 3,
        "require_figure": bool(require_figure),
    }
    req = urllib.request.Request(
        f"{settings.EXAMGEN_URL}/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {settings.EXAMGEN_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.EXAMGEN_TIMEOUT) as resp:
            body = json.loads(resp.read().decode())
        return body.get("questions", []) or []
    except Exception as exc:
        print(f"[examgen] generate failed ({chapter}/{concept}): {exc}")
        return []


def _to_pack_question(q: dict) -> dict | None:
    """examgen MCQ → assess.html pack question shape (English-only → hi mirrors en)."""
    if (q.get("qtype") or "").lower() != "mcq_single":
        return None
    opts = q.get("options", []) or []
    texts = [str(o.get("text", "")) for o in opts]
    if len(texts) < 2:
        return None
    correct = _letter_to_index(q.get("correct_answer", ""), opts)
    tag = q.get("concept") or q.get("chapter") or "JEE Physics"
    lang = {"tag": tag, "q": str(q.get("stem", "")),
            "opts": texts, "explain": str(q.get("solution", ""))}
    topic = {"en": tag, "hi": tag}
    fig = q.get("figure_svg") or None          # inline SVG diagram (server-sanitized), if any
    return {"type": "mcq", "correct": correct, "topic": topic,
            "qid": q.get("id"),                # pool id → drives no-repeats (`exclude`)
            "figure": fig, "en": dict(lang), "hi": dict(lang)}


def generate_pack(subject_id: str, selections: list[tuple], difficulty: str,
                  total: int, title: str, require_figure: bool = False,
                  exclude: list[str] | None = None) -> dict | None:
    """selections = [(chapter, concept_or_None), ...] → an assess.html pack.

    POOL FIRST: read pre-generated questions instantly (no LLM, no wait). Only whatever the pool
    can't cover falls through to live /generate, which is slow (~40-55s/question). Once the pool is
    filled this path becomes effectively instant with no further code change."""
    if not selections:
        return None
    total = max(1, min(int(total), 15))

    results: list[dict] = []
    if not require_figure:            # forced-figure requests always need live generation
        want_each = max(1, -(-total // len(selections)))     # ceil
        for ch, co in selections:
            if len(results) >= total:
                break
            qs, _exhausted = fetch_pool(subject_id, ch, co, difficulty,
                                        "MCQ_single", want_each, exclude)
            if qs is None:            # /pool not available → skip straight to generation
                break
            for q in qs:
                pq = _to_pack_question(q)
                if pq and len(results) < total:
                    results.append(pq)
        if len(results) >= total:
            return _wrap_pack(results[:total], title)

    # ---- fall back to LIVE generation for whatever the pool couldn't cover ----
    remaining = total - len(results)
    n = len(selections)
    base, extra = divmod(remaining, n)

    # Split into SMALL parallel calls. The generator is ~40s/question on gpt-5.5, so a single
    # call for N questions would run serially inside the API and blow the request timeout.
    # Chunking at MAX_PER_CALL and fanning out keeps wall-clock ≈ one chunk, not the sum.
    tasks: list[tuple] = []
    for i, sel in enumerate(selections):
        c = base + (1 if i < extra else 0)
        while c > 0:
            k = min(c, MAX_PER_CALL)
            tasks.append((sel[0], sel[1], k))
            c -= k
    if not tasks:
        tasks = [(selections[0][0], selections[0][1], 1)]

    # NOTE: append to `results` — do NOT re-initialise it, or anything already drawn from the
    # pool above would be thrown away.
    with ThreadPoolExecutor(max_workers=min(6, len(tasks))) as ex:
        futs = [ex.submit(_generate_one, subject_id, ch, co, difficulty, k, require_figure)
                for (ch, co, k) in tasks]
        for fut in as_completed(futs):
            for q in fut.result():
                pq = _to_pack_question(q)
                if pq:
                    results.append(pq)
    return _wrap_pack(results[:total], title)


def _wrap_pack(results: list[dict], title: str) -> dict | None:
    """Assemble the engine pack. `intro` is REQUIRED — the engine's intro() does S.intro[LANG];
    without it the whole test renders BLANK (the API can be perfect and the student sees nothing)."""
    if not results:
        return None
    n = len(results)
    return {
        "title": title,
        "topic": {"en": title, "hi": title},
        "intro": {
            "en": f"Namaste 🙏 A quick <b>{title}</b> paper — {n} question{'' if n == 1 else 's'} "
                  f"in the real exam style. Just tap to answer.",
            "hi": f"नमस्ते 🙏 <b>{title}</b> का एक क्विक पेपर — {n} सवाल, असली exam स्टाइल में। बस tap करें।",
        },
        "topicMap": [q["topic"] for q in results],
        "questions": results,
    }
