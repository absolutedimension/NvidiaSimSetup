"""Client for the /examgen RAG question generator — authentic past-paper-style questions.

Runs on the ALWAYS-ON Gurukul VM (migrated off the EC2 GPU box 2026-07-23) and generates with
Azure **gpt-5.5**. The LMS proxies it server-side so the API key never reaches the browser, and
transforms its LaTeX MCQs (+ optional SVG diagrams) into the assess.html engine's "pack" shape.

JEE Advanced + JEE Main (Physics/Chemistry/Maths), NEET (Biology/Physics/Chemistry), CBSE boards,
and Banking Prelims (Quant — a GENERATED bank, not RAG over real past papers, see
project-banking-quant-generator) are wired. Add a subject to RAG_SUBJECTS — and to a GOALS entry —
to grow coverage; the bank must already exist on the VM."""
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
    # ---- CBSE Boards ----
    "cbse10-science": {
        "label": "Class 10 Science", "exam": "CBSE Class 10", "subject": "Science", "kw": "science",
        "match": ["cbse class 10 science", "class 10 science", "class10 science", "cbse10-science",
                  "class 10 board", "10th science", "class 10", "class10"],
    },
    "cbse10-maths": {
        "label": "Class 10 Maths", "exam": "CBSE Class 10", "subject": "Mathematics", "kw": "math",
        "match": ["cbse class 10 maths", "class 10 maths", "class10 maths", "cbse10-maths",
                  "class 10 mathematics", "class 10 math", "10th maths", "10 maths"],
    },
    "class3-maths": {
        "label": "Class 3 Maths", "exam": "ICSE Class 3", "subject": "Mathematics", "kw": "math",
        "match": ["class 3 maths", "grade 3 maths", "icse class 3 maths", "class3 maths",
                  "class 3 mathematics", "grade 3 math", "kids maths", "class 3 math"],
    },
    "cbse12-physics": {
        "label": "Class 12 Physics", "exam": "CBSE Class 12", "subject": "Physics", "kw": "physics",
        "match": ["cbse class 12 physics", "class 12 physics", "class12 physics", "cbse12-physics",
                  "12th physics"],
    },
    "cbse12-chemistry": {
        "label": "Class 12 Chemistry", "exam": "CBSE Class 12", "subject": "Chemistry", "kw": "chem",
        "match": ["cbse class 12 chemistry", "class 12 chemistry", "class12 chemistry", "cbse12-chemistry",
                  "12th chemistry"],
    },
    "cbse12-maths": {
        "label": "Class 12 Maths", "exam": "CBSE Class 12", "subject": "Mathematics", "kw": "math",
        "match": ["cbse class 12 maths", "class 12 maths", "class12 maths", "cbse12-maths",
                  "class 12 mathematics", "class 12 math", "12th maths", "12 maths"],
    },
    "cbse12-biology": {
        "label": "Class 12 Biology", "exam": "CBSE Class 12", "subject": "Biology", "kw": "bio",
        "match": ["cbse class 12 biology", "class 12 biology", "class12 biology", "cbse12-biology",
                  "12th biology"],
    },
    # ---- CBSE Class 12 Commerce (real verified banks: Accountancy ~5.4k, Economics ~3.3k) ----
    "cbse12-accountancy": {
        "label": "Class 12 Accountancy", "exam": "CBSE Class 12", "subject": "Accountancy", "kw": "accountancy",
        "match": ["cbse class 12 accountancy", "class 12 accountancy", "class12 accountancy",
                  "accountancy", "accounts", "cbse12-accountancy", "12th accountancy", "commerce accountancy"],
    },
    "cbse12-economics": {
        "label": "Class 12 Economics", "exam": "CBSE Class 12", "subject": "Economics", "kw": "economics",
        "match": ["cbse class 12 economics", "class 12 economics", "class12 economics",
                  "economics", "cbse12-economics", "12th economics", "commerce economics"],
    },
    # ---- Banking (IBPS/SBI/RRB Prelims) ----
    # GENERATION-first: no ingested past-paper exemplars — the bank behind this is the deterministic
    # compute-the-answer engine (qbank/quantgen.py), not RAG over real questions. Same /pool + /generate
    # contract though, so it slots in with zero frontend-engine changes. See project-banking-quant-generator.
    "banking-quant": {
        "label": "Banking Quant (IBPS/SBI/RRB)", "exam": "Banking Prelims",
        "subject": "Quantitative Aptitude", "kw": "quant",
        "match": ["banking", "ibps", "sbi po", "sbi clerk", "bank po", "bank clerk", "rrb po",
                  "rrb clerk", "banking prelims", "banking quant", "banking quantitative",
                  "banking-quant", "quantitative aptitude"],
    },
    # ---- UPSC Civil Services (Preliminary) — REAL past-paper PYQs (2023-2025), not RAG-generated ----
    "upsc-gs": {
        "label": "UPSC GS (Prelims)", "exam": "UPSC Civil Services (Preliminary)",
        "subject": "General Studies", "kw": "gs",
        "match": ["upsc gs", "upsc general studies", "upsc prelims gs", "civil services gs",
                  "upsc-gs", "general studies prelims", "ias prelims gs"],
    },
    "upsc-csat": {
        "label": "UPSC CSAT (Prelims)", "exam": "UPSC Civil Services (Preliminary)",
        "subject": "CSAT", "kw": "csat",
        "match": ["upsc csat", "csat", "upsc aptitude", "civil services aptitude", "upsc-csat",
                  "csat prelims"],
    },
    # ---- SSC CGL (govt-job) — GENERATION-first (compute-the-answer): Reasoning + Quant are
    # served by qbank/reasoninggen.py + quantgen.py (no ingested exemplars). Same /pool + /generate
    # contract. GS/GK/English roll out later (real PYQ extraction). See SRB_PYQ_SOURCING_GUIDE.md.
    "ssc-reasoning": {
        "label": "SSC Reasoning", "exam": "SSC CGL", "subject": "Reasoning", "kw": "reasoning",
        "match": ["ssc reasoning", "ssc cgl reasoning", "reasoning ssc", "general intelligence",
                  "ssc-reasoning", "reasoning", "logical reasoning"],
    },
    "ssc-quant": {
        "label": "SSC Quant (Maths)", "exam": "SSC CGL", "subject": "Quantitative Aptitude",
        "kw": "quant",
        "match": ["ssc quant", "ssc cgl quant", "ssc maths", "ssc math", "ssc quantitative",
                  "ssc-quant", "ssc numerical"],
    },
    "ssc-gk": {
        "label": "SSC General Knowledge", "exam": "SSC CGL", "subject": "General Knowledge",
        "kw": "gk",
        "match": ["ssc gk", "ssc general knowledge", "static gk", "general knowledge", "ssc-gk",
                  "static portion", "general awareness", "static portion gk"],
    },
    "ssc-english": {
        "label": "SSC English", "exam": "SSC CGL", "subject": "English", "kw": "english",
        "match": ["ssc english", "english", "english language", "ssc-english", "general english",
                  "verbal ability", "english for ssc cgl"],
    },
    # SSC/Railway "General Science" BORROWS the real CBSE Class 10 Science bank (3.4k verified,
    # basic NCERT level = exactly the SSC GS-science difficulty). Real PYQs, not generated.
    "ssc-science": {
        "label": "General Science", "exam": "CBSE Class 10", "subject": "Science", "kw": "science",
        "match": ["ssc science", "general science", "ssc general science", "gs science",
                  "ssc-science", "science gk", "physics chemistry biology"],
    },
    # Current Affairs — MANUAL-ENTRY (time-sensitive, cannot be generated). Real dated questions
    # loaded via current_affairs/import_current_affairs.py; served from /pool (generated=0).
    "current-affairs": {
        "label": "Current Affairs", "exam": "Current Affairs", "subject": "Current Affairs",
        "kw": "ca",
        "match": ["current affairs", "current affair", "current-affairs", "ca", "gk current",
                  "current gk", "latest current affairs"],
    },
    # ---- BPSC (Bihar PSC Prelims) — REAL past-paper PYQs (70th Prelims GS, official keys), NOT
    # generated. Served from /pool (chapter=NULL, all bands). Built via the exact-question pipeline.
    "bpsc-gs": {
        "label": "BPSC GS (Prelims)", "exam": "BPSC", "subject": "General Studies", "kw": "gs",
        "match": ["bpsc gs", "bpsc general studies", "bpsc prelims", "bpsc-gs", "bihar psc gs",
                  "bpsc gs prelims", "bihar psc", "bpsc"],
    },
    # ---- BPSC TRE (Teacher Recruitment) — REAL past-paper PYQs (TRE 1.0/2.0/3.0, official papers,
    # cross-source keyed), 5-option (A-E). Served from /pool (exam="BPSC TRE" starts with "BPSC" so it
    # inherits the real-serve + skip_chapter/skip_difficulty gate). Built via extract_tre.py + keying.
    "bpsc-tre": {
        "label": "BPSC TRE GS (Teacher)", "exam": "BPSC TRE", "subject": "General Studies", "kw": "gs",
        "match": ["bpsc tre", "tre", "teacher recruitment", "bpsc teacher", "bpsc-tre",
                  "bihar teacher", "tre gs", "bpsc tre gs"],
    },
    # ---- GS Science (Physics / Chemistry / Biology) for govt-job GS — BORROW the CBSE Class 12
    # real PYQ banks (4435 / 4101 / 3358 real questions, all served from /pool via the CBSE real-serve
    # gate). Gives the "General Studies — Physics/Chemistry/Biology" column of the One Step note
    # separate, ≥1000-deep, servable banks (no generation). Same borrow pattern as railway-science.
    "gs-physics": {
        "label": "General Science: Physics", "exam": "CBSE Class 12", "subject": "Physics", "kw": "physics",
        "match": ["gs physics", "general science physics", "gs-physics", "physics gk", "science physics"],
    },
    "gs-chemistry": {
        "label": "General Science: Chemistry", "exam": "CBSE Class 12", "subject": "Chemistry", "kw": "chemistry",
        "match": ["gs chemistry", "general science chemistry", "gs-chemistry", "chemistry gk", "science chemistry"],
    },
    "gs-biology": {
        "label": "General Science: Biology", "exam": "CBSE Class 12", "subject": "Biology", "kw": "biology",
        "match": ["gs biology", "general science biology", "gs-biology", "biology gk", "science biology"],
    },
    # ---- GS-Social dimensions — real BPSC TRE PYQs re-subjected from "General Studies" by concept
    # (cross-source keyed). Served from /pool (exam="BPSC TRE" real-serve + skip_difficulty gate).
    # Selectable so a student can focus-practise one social dimension.
    "gs-polity": {
        "label": "GS: Polity", "exam": "BPSC TRE", "subject": "GS Polity", "kw": "polity",
        "match": ["polity", "gs polity", "political science", "civics", "constitution", "gs-polity"],
    },
    "gs-history": {
        "label": "GS: History", "exam": "BPSC TRE", "subject": "GS History", "kw": "history",
        "match": ["history", "gs history", "indian history", "gs-history"],
    },
    "gs-geography": {
        "label": "GS: Geography", "exam": "BPSC TRE", "subject": "GS Geography", "kw": "geography",
        "match": ["geography", "gs geography", "indian geography", "gs-geography"],
    },
    "gs-economics": {
        "label": "GS: Economics", "exam": "BPSC TRE", "subject": "GS Economics", "kw": "economics",
        "match": ["economics", "gs economics", "economy", "indian economy", "gs-economics"],
    },
    # ---- Railway (RRB — NTPC / Group D / ALP) — same generator-served pattern as SSC; General
    # Science borrows the real CBSE Class 10 Science bank. Backend taxonomies already registered.
    "railway-reasoning": {
        "label": "Railway Reasoning", "exam": "Railway (RRB)", "subject": "Reasoning", "kw": "reasoning",
        "match": ["railway reasoning", "rrb reasoning", "railway-reasoning"],
    },
    "railway-quant": {
        "label": "Railway Maths", "exam": "Railway (RRB)", "subject": "Quantitative Aptitude", "kw": "quant",
        "match": ["railway maths", "railway quant", "rrb maths", "rrb quant", "railway-quant"],
    },
    "railway-gk": {
        "label": "Railway General Knowledge", "exam": "Railway (RRB)", "subject": "General Knowledge", "kw": "gk",
        "match": ["railway gk", "rrb gk", "railway general knowledge", "railway-gk"],
    },
    "railway-english": {
        "label": "Railway English", "exam": "Railway (RRB)", "subject": "English", "kw": "english",
        "match": ["railway english", "rrb english", "railway-english"],
    },
    "railway-science": {
        "label": "General Science", "exam": "CBSE Class 10", "subject": "Science", "kw": "science",
        "match": ["railway science", "rrb science", "railway-science"],
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
    "cbse-10": {
        "label": "CBSE Class 10", "tag": "Boards · Science + Maths", "emoji": "📘",
        "subjects": ["cbse10-science", "cbse10-maths"],
    },
    "class3": {
        "label": "Class 3 (ICSE)", "tag": "Kids · Grade 3", "emoji": "🔢",
        "subjects": ["class3-maths"],
    },
    "cbse-12": {
        "label": "CBSE Class 12", "tag": "Boards · PCB", "emoji": "📗",
        "subjects": ["cbse12-physics", "cbse12-chemistry", "cbse12-maths", "cbse12-biology"],
    },
    "cbse-12-commerce": {
        "label": "Class 12 Commerce", "tag": "Boards · Commerce", "emoji": "📊",
        "subjects": ["cbse12-accountancy", "cbse12-economics"],
    },
    "banking": {
        "label": "Banking (IBPS/SBI/RRB)", "tag": "Govt · Banking", "emoji": "🏦",
        "subjects": ["banking-quant"],
    },
    "upsc": {
        "label": "UPSC Civil Services", "tag": "Civil Services · IAS", "emoji": "🏛️",
        "subjects": ["upsc-gs", "upsc-csat"],
    },
    "ssc-cgl": {
        "label": "SSC CGL", "tag": "Govt job · SSC/Railway", "emoji": "📋",
        "subjects": ["ssc-reasoning", "ssc-quant", "ssc-gk", "ssc-english", "ssc-science",
                     "current-affairs"],
    },
    "bpsc": {
        "label": "BPSC (Bihar PSC)", "tag": "Bihar · Civil Services", "emoji": "🏛️",
        "subjects": ["bpsc-gs"],
    },
    "bpsc-tre": {
        "label": "BPSC TRE (Teacher)", "tag": "Bihar · Teacher Recruitment", "emoji": "🧑‍🏫",
        "subjects": ["bpsc-tre", "gs-polity", "gs-history", "gs-geography", "gs-economics",
                     "gs-physics", "gs-chemistry", "gs-biology"],
    },
    "railway": {
        "label": "Railway (RRB)", "tag": "Govt job · Railway", "emoji": "🚂",
        "subjects": ["railway-reasoning", "railway-quant", "railway-gk", "railway-english",
                     "railway-science", "current-affairs"],
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
    # CBSE boards sit lowest — the NCERT-derived bank is difficulty 2 with some 3.
    "CBSE Class 10": {"easy": "2", "mix": "2-3", "hard": "3"},
    "CBSE Class 12": {"easy": "2", "mix": "2-3", "hard": "3"},
    # ICSE Class 3 (kids) sits lowest — generated arithmetic pool at difficulty 1-2.
    "ICSE Class 3": {"easy": "1", "mix": "1-2", "hard": "2"},
    # Banking Prelims (generated, not tagged by an LLM) — the pool is seeded at exactly these
    # bands (see project-banking-quant-generator §runbook); keep the ladder matching what's filled.
    "Banking Prelims": {"easy": "2", "mix": "2-3", "hard": "3"},
    # UPSC PYQs are all stored at difficulty 3 (one mixed prelims paper) — every band maps to 3.
    "UPSC Civil Services (Preliminary)": {"easy": "3", "mix": "3", "hard": "3"},
    # SSC CGL (generated Reasoning + Quant, same compute-the-answer pool as Banking) — match the bands.
    "SSC CGL": {"easy": "2", "mix": "2-3", "hard": "3"},
    # BPSC TRE — real Teacher-Recruitment PYQs served from /pool (same real-serve gate as BPSC; bands nominal).
    "BPSC TRE": {"easy": "3", "mix": "3", "hard": "3"},
    # BPSC — real Prelims GS PYQs served from /pool (chapter=NULL, difficulty bypassed via storage
    # skip_difficulty); the band values are nominal (serving ignores them for BPSC, like UPSC).
    "BPSC": {"easy": "2", "mix": "3", "hard": "3"},
    # Current Affairs — manual-entry real dated Qs; difficulty bypassed via storage skip.
    "Current Affairs": {"easy": "2", "mix": "2", "hard": "2"},
    # Railway (RRB) — same generated pattern/bands as SSC CGL.
    "Railway (RRB)": {"easy": "2", "mix": "2-3", "hard": "3"},
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


def chapters_for_ui(subject_id: str = "jee-physics") -> list[dict]:
    """Chapters to OFFER in the picker (subject page / chat / teacher create).

    Normally = chapters with banked exemplars (RAG can write authentic questions). BUT some live
    banks are POOL-served with no per-chapter exemplar count: UPSC PYQs are stored `chapter=NULL`
    (banked=0 on every taxonomy chapter) yet `/pool` returns real questions for the whole subject.
    Filtering on `exemplars_banked > 0` there hid the entire subject → 'coming soon'. So: prefer
    banked chapters; if a live subject has a taxonomy but ZERO banked chapters, offer all of them
    (they draw from the subject pool). Genuinely-empty subjects still return [] → 'coming soon'."""
    chs = get_chapters(subject_id)
    banked = [c for c in chs if c.get("exemplars_banked", 0) > 0]
    return banked or chs


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
