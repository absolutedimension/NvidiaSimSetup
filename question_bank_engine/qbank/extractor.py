"""Extractor agent — raw source -> structured Question objects.

Two paths:
  from_dataset_row()  : structured open-dataset row -> Question (rule-based split of
                        inline (A)(B)(C)(D) options; no LLM needed).
  from_pdf()          : PDF page images -> Questions via the vision LLM (gpt-4o).
                        Requires the LLM proxy (QBANK_LLM on/auto + reachable).
"""
import json as _json
import os
import re
import urllib.request

from . import config
from .models import Question, content_hash, references_figure, repair_latex

_TYPE_MAP = {
    "MCQ": "MCQ_single",
    "MCQ(multiple)": "MCQ_multi",
    "Integer": "integer",
    "Numeric": "numeric",
}
_YEAR_RE = re.compile(r"(20\d{2})")
# Option markers drift across years/papers:
#   (A)   [A]   [\mathrm{A}]   $[\mathrm{A}]$   with arbitrary inner whitespace.
_OPT_RE = re.compile(r"[\(\[]\s*(?:\\mathrm\s*\{)?\s*([A-D])\s*\}?\s*[\)\]]")


def _split_options(text: str):
    """Split 'stem (A)... (B)... (C)... (D)...' into (stem, [options])."""
    markers = list(_OPT_RE.finditer(text))
    if len(markers) < 2:
        return text.strip(), []
    stem = text[:markers[0].start()].strip()
    opts, seen = [], set()
    for i, m in enumerate(markers):
        label = m.group(1)
        if label in seen:            # ignore stray '(A)' occurring inside option text
            continue
        seen.add(label)
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        opts.append({"label": label, "text": text[start:end].strip()})
    return stem, opts


def from_dataset_row(row: dict, exam: str = "JEE Advanced", subject: str = "Physics") -> Question:
    qtype = _TYPE_MAP.get(row.get("type", "MCQ"), "MCQ_single")
    raw = (row.get("question") or "").strip()
    if qtype in ("MCQ_single", "MCQ_multi"):
        stem, opts = _split_options(raw)
    else:
        stem, opts = raw, []
    desc = row.get("description", "")
    ym = _YEAR_RE.search(desc)
    year = int(ym.group(1)) if ym else None
    idx = row.get("index", "")
    h = content_hash(raw)
    # NOTE: dataset 'index' resets per paper (2016 P1 and P2 both start at 1), so
    # year+index is NOT unique. Append the content hash to keep the id unique AND
    # idempotent (same question -> same id on re-ingest, so dedup still works).
    qid = f"jee_adv_phy_{year}_{idx}_{h[:6]}" if (year and idx != "") else f"jee_adv_phy_{h}"
    return Question(
        id=qid, exam=exam, subject=subject, stem=stem, qtype=qtype, options=opts,
        correct_answer=str(row.get("gold", "")).strip(), source=desc, year=year, hash=h,
    )


# --- grafite JEE-Main path (pre-tagged + pre-solved text; no LLM needed) ------
# Source: ruh-ai/grafite-jee-mains-qna-no-img — rows carry subject/chapter/topic,
# options as [{"identifier","content"}], correct_option as [letters], plus
# solution+explanation. We map straight across, humanize the slug tags, and let the
# validator decide `verified` from rule_check (answer present + in options, etc.).
_HTML_SUB = re.compile(r"<sub>(.*?)</sub>", re.I | re.S)
_HTML_SUP = re.compile(r"<sup>(.*?)</sup>", re.I | re.S)
_HTML_IMG = re.compile(r"<img[^>]*>", re.I)
_HTML_TAG = re.compile(
    r"</?(?:br|p|div|span|b|i|strong|em|u|font|table|tbody|thead|tr|td|th|ul|ol|li)\s*/?>", re.I)
_PAPER_YEAR = re.compile(r"(?:19|20)\d{2}")


def _humanize_slug(slug):
    """'alternating-current' -> 'Alternating Current'; None/'None' -> None."""
    if not slug or str(slug).strip().lower() in ("none", ""):
        return None
    return " ".join(w.capitalize() for w in re.split(r"[-_\s]+", str(slug)) if w)


def _grafite_text(t):
    """grafite stems/options/solutions carry HTML sub/sup + entities beside $$ LaTeX."""
    import html as _html
    t = t or ""
    t = _HTML_SUB.sub(r"_{\1}", t)
    t = _HTML_SUP.sub(r"^{\1}", t)
    t = _HTML_IMG.sub(" ", t)
    t = _HTML_TAG.sub(" ", t)
    t = _html.unescape(t)
    return re.sub(r"[ \t]+", " ", t).strip()


def from_grafite_row(row, exam="JEE Main", subject="Physics", default_difficulty=2):
    """grafite row -> Question. Returns None if the row is unusable (no stem / too few
    options). Does NOT set `verified` — the validator owns that via rule_check."""
    raw_q = row.get("question") or ""
    stem = _grafite_text(raw_q)
    if len(stem) < 15:
        return None
    needs_fig = bool(_HTML_IMG.search(raw_q))   # stem depends on a diagram we don't have
    qtype_raw = str(row.get("question_type") or "mcq").lower()
    qtype = "integer" if qtype_raw.startswith("int") else "MCQ_single"

    raw_opts = row.get("options")
    if isinstance(raw_opts, str):
        try:
            raw_opts = _json.loads(raw_opts)
        except Exception:
            raw_opts = []
    opts = []
    for o in (raw_opts or []):
        if not isinstance(o, dict):
            continue
        lab = str(o.get("identifier") or o.get("label") or "").strip()
        txt = _grafite_text(o.get("content") or o.get("text") or "")
        if lab:
            opts.append({"label": lab, "text": txt})
    if qtype == "MCQ_single" and len(opts) < 2:
        return None

    co = row.get("correct_option")
    if isinstance(co, str) and co.strip().startswith("["):   # arrives as JSON string '["B"]'
        try:
            co = _json.loads(co)
        except Exception:
            pass
    if isinstance(co, list):
        ans = "".join(str(x).strip().strip('"') for x in co)
    elif co is not None and str(co).strip():
        ans = str(co).strip()
    else:
        ans = str(row.get("answer") or "").strip()
    if qtype == "MCQ_single" and len(re.findall(r"[A-D]", ans.upper())) > 1:
        qtype = "MCQ_multi"

    sol = _grafite_text(row.get("explanation") or "")
    short = _grafite_text(row.get("solution") or "")
    if short and short not in sol:
        sol = (sol + "\n\n" + short).strip() if sol else short

    diff = default_difficulty + (1 if qtype == "integer" else 0)
    pid = str(row.get("paper_id") or "").strip()
    ym = _PAPER_YEAR.search(pid)
    year = int(ym.group(0)) if ym else None
    h = content_hash(stem)
    qid = f"jee_main_phy_{pid or 'na'}_{h[:6]}".replace(" ", "-")

    return Question(
        id=qid, exam=exam, subject=subject, stem=stem, qtype=qtype, options=opts,
        correct_answer=ans, solution=sol,
        chapter=_humanize_slug(row.get("chapter")),
        concept=_humanize_slug(row.get("topic")),
        difficulty=diff, needs_figure=needs_fig,
        source=f"JEE Main ({pid})" if pid else "JEE Main",
        year=year, hash=h,
    )


# --- datavorous entrance-exam path (pre-tagged + pre-solved HTML) ------------
# Source: datavorous/entrance-exam-dataset — ~97k rows (NEET + JEE Main/Advanced).
# tags = "['Subject','Chapter','Exam', ...]" (Python-literal string). options is HTML
# <ul><li class="correct"?> with option-label + option-data. The correct answer is
# marked TWO independent ways: the li.correct class AND correct_option's <span
# class="option-value">TEXT</span>. We use the li.correct class for the letter, and
# cross-check it against the value text — a built-in free key validator. `answer`
# holds a worked solution. No LLM needed (tagged + keyed + solved already).
_DV_LI = re.compile(r'<li class="(correct|)"[^>]*>(.*?)</li>', re.S | re.I)
_DV_LABEL = re.compile(r'option-label">\s*([A-Z])\s*<', re.S)
_DV_DATA = re.compile(r'option-data">(.*?)</span>', re.S)
_DV_SVG = re.compile(r"<svg.*?</svg>", re.S | re.I)
_DV_VALUE = re.compile(r'option-value">(.*?)</span>', re.S)


def _dv_text(t):
    """datavorous fields are HTML (sub/sup/div/svg checkmark) beside $...$ LaTeX."""
    import html as _html
    t = _DV_SVG.sub(" ", t or "")
    t = _HTML_SUB.sub(r"_{\1}", t)
    t = _HTML_SUP.sub(r"^{\1}", t)
    t = _HTML_IMG.sub(" ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return re.sub(r"[ \t]+", " ", t).replace("\r", " ").strip()


def _dv_tags(raw):
    """"['Biology','Environmental Issues','NEET']" -> ['Biology','Environmental Issues','NEET']."""
    import ast
    try:
        v = ast.literal_eval(raw or "[]")
        return [str(x).strip() for x in v] if isinstance(v, (list, tuple)) else []
    except Exception:
        return []


# datavorous Biology chapter names are the same NCERT chapters as our hand-authored
# NEET_BIOLOGY taxonomy, but with punctuation/plural variants. Canonicalise to the
# clean taxonomy names so /chapters + retrieval match. (Physics/Chemistry adopt
# datavorous's names as canonical instead — they had no clean taxonomy of their own.)
_DV_BIO_CHAPTER = {
    "Human Health and Diseases": "Human Health and Disease",
    "Biotechnology - Principles and Processes": "Biotechnology: Principles and Processes",
    "Cell - The Unit of Life": "Cell: The Unit of Life",
    "Biodiversity and its Conservation": "Biodiversity and Conservation",
    "Plant - Growth and Development": "Plant Growth and Development",
    "Biotechnology and Its Applications": "Biotechnology and its Applications",
    "Biomolecules (B)": "Biomolecules",
}


def from_datavorous_row(row, want_exam="NEET", default_difficulty=2):
    """datavorous row -> Question, or None if unusable / wrong exam.

    Cross-checks the li.correct letter against the correct_option value text; if they
    disagree the row is dropped (a mislabelled key would poison the bank). `want_exam`
    filters by the exam tag ('NEET' / 'JEE Main' / 'JEE Advanced')."""
    tags = _dv_tags(row.get("tags"))
    if not tags:
        return None
    tagset = {t for t in tags}
    if want_exam not in tagset:
        return None
    subject = tags[0]
    # datavorous chapters are already clean prose ("Human Health and Diseases"), NOT
    # slugs — use them verbatim so the DB names match, and the derived taxonomy lines
    # up exactly with /chapters. (Running _humanize_slug here capitalised "and"/"of".)
    chapter = tags[1].strip() if len(tags) > 1 and tags[1].strip() else None
    # normalise subject to our canonical names
    subject = {"Maths": "Mathematics", "Math": "Mathematics"}.get(subject, subject)
    if subject == "Biology" and chapter in _DV_BIO_CHAPTER:
        chapter = _DV_BIO_CHAPTER[chapter]

    stem = _dv_text(row.get("question"))
    if len(stem) < 12:
        return None

    opts, correct_lab = [], None
    for m in _DV_LI.finditer(row.get("options") or ""):
        cls, body = m.group(1), m.group(2)
        lm = _DV_LABEL.search(body)
        if not lm:
            continue
        lab = lm.group(1)
        dm = _DV_DATA.search(body)
        data = _dv_text(dm.group(1)) if dm else ""
        opts.append({"label": lab, "text": data})
        if cls.lower() == "correct":
            correct_lab = lab

    # integer/numeric rows: options == "None", answer lives in correct_option value
    cv = _DV_VALUE.search(row.get("correct_option") or "")
    cval = _dv_text(cv.group(1)) if cv else None

    if len(opts) >= 2:
        qtype = "MCQ_single"
        if correct_lab is None:
            return None
        # cross-check the li.correct letter against the value text
        if cval:
            matches = [o["label"] for o in opts if o["text"] and o["text"] == cval]
            if len(matches) == 1 and matches[0] != correct_lab:
                return None                 # markers disagree -> untrustworthy key, drop
        answer = correct_lab
    else:
        # no option list -> integer/numeric; the value text IS the answer
        if not cval:
            return None
        qtype = "integer" if re.fullmatch(r"-?\d+", cval) else "numeric"
        opts, answer = [], cval

    solution = _dv_text(row.get("answer"))
    diff = default_difficulty + (1 if qtype in ("integer", "numeric") else 0)
    h = content_hash(stem)
    src_exam = want_exam
    prefix = {"NEET": "neet", "JEE Main": "jee_main", "JEE Advanced": "jee_adv"}.get(src_exam, "dv")
    sub_slug = re.sub(r"[^a-z]", "", subject.lower())[:4]
    return Question(
        id=f"{prefix}_{sub_slug}_dv_{h[:12]}", exam=src_exam, subject=subject, stem=stem,
        qtype=qtype, options=opts, correct_answer=answer, solution=solution,
        chapter=chapter, difficulty=diff, source=f"{src_exam} (datavorous)", hash=h,
    )


# --- NEET Biology text path (sweatSmile/neet-biology-qa) ---------------------
# Rows are {question, subject, choices:[4 strings], answer:"A"|"1"} — no chapter, no
# solution, so tagging + solving happen downstream. Options arrive UNLABELLED (a plain
# list), so we label them A..D positionally and map a numeric answer to that letter.

def from_neet_bio_row(row, exam="NEET", subject="Biology", default_difficulty=2):
    """sweatSmile-style NEET Biology row -> Question. None if unusable."""
    stem = (row.get("question") or "").strip()
    if len(stem) < 12:
        return None

    raw_opts = row.get("choices") or row.get("options") or []
    if isinstance(raw_opts, str):
        try:
            raw_opts = _json.loads(raw_opts)
        except Exception:
            raw_opts = []
    opts = []
    for i, o in enumerate(raw_opts):
        if isinstance(o, dict):
            lab = str(o.get("label") or o.get("identifier") or chr(65 + i)).strip()
            txt = str(o.get("text") or o.get("content") or "").strip()
        else:
            lab, txt = chr(65 + i), str(o).strip()
        if txt:
            opts.append({"label": lab, "text": txt})
    if len(opts) < 2:
        return None

    ans = str(row.get("answer") or "").strip()
    if ans.isdigit():                      # 1-based option index -> letter
        idx = int(ans) - 1
        ans = opts[idx]["label"] if 0 <= idx < len(opts) else ""
    ans = ans.upper()[:1]
    if ans not in {o["label"].upper() for o in opts}:
        return None                        # no usable key -> not an exemplar

    h = content_hash(stem)
    return Question(
        id=f"neet_bio_{h[:12]}", exam=exam, subject=subject, stem=stem,
        qtype="MCQ_single", options=opts, correct_answer=ans,
        difficulty=default_difficulty, source="NEET Biology (open dataset)", hash=h,
    )


# --- PDF path (production; needs the vision LLM) -----------------------------

_VISION_SYS = (
    "You are an exam-paper parser. You are given an image of one page from an Indian "
    "competitive-exam question paper. Extract EVERY question on the page. Return JSON "
    '{"questions":[{"number":int,"stem":"...(LaTeX for math)","type":"MCQ_single|MCQ_multi|integer|numeric",'
    '"options":[{"label":"A","text":"..."}],"has_figure":bool}]}. '
    "Preserve math as LaTeX. If a question continues from a previous page, set number to null. "
    "Do not invent options that are not printed."
)


def from_pdf(path: str, llm, exam: str, subject: str, year: int | None = None) -> list[Question]:
    """Render pages to images and ask the vision model to structure them.
    Returns questions WITHOUT answers — keymatch.py attaches those from the key PDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError("PDF path needs PyMuPDF: pip install pymupdf") from e
    if not llm.ok:
        raise RuntimeError("PDF extraction needs the vision LLM (set QBANK_LLM proxy).")

    out: list[Question] = []
    doc = fitz.open(path)
    for pno in range(len(doc)):
        pix = doc[pno].get_pixmap(dpi=200)
        img = pix.tobytes("png")
        data = llm.vision_json(_VISION_SYS, f"Parse page {pno + 1}.", img)
        for q in (data or {}).get("questions", []):
            stem = (q.get("stem") or "").strip()
            if not stem:
                continue
            h = content_hash(stem)
            num = q.get("number")
            qid = f"{subject.lower()}_{year or 'na'}_{num or h}"
            out.append(Question(
                id=qid, exam=exam, subject=subject, stem=stem,
                qtype=q.get("type", "MCQ_single"),
                options=q.get("options", []), source=f"{exam} {year or ''}".strip(),
                year=year, figure_refs=([f"{qid}.png"] if q.get("has_figure") else []),
                hash=h,
            ))
    return out


# --- image-dataset path (each question is one PNG; answer in metadata) --------

_IMG_QTYPE = {
    "MCQ_SINGLE_CORRECT": "MCQ_single",
    "MCQ_MULTIPLE_CORRECT": "MCQ_multi",
    "MCQ_MATCHING": "MCQ_single",   # List-I/List-II, single correct option
    "INTEGER": "integer",
    "INTEGER_2": "numeric",         # decimal answer
}


def _img_sys(need_opts: bool, exam: str = "JEE Advanced", subject: str = "Physics") -> str:
    base = (f"This image is ONE {subject.lower()} question from a {exam} paper. Extract it "
            "EXACTLY as printed. Preserve ALL math as LaTeX using $...$ . Include any data "
            "table or List-I/List-II matching table inside the stem. Do NOT include the answer. "
            'Also report "has_figure": true if the question contains a DIAGRAM/graph/circuit/'
            'geometric drawing that the text alone cannot convey, else false. ')
    opts = ('"options":[{"label":"A","text":"..."},{"label":"B","text":"..."},...]'
            if need_opts else '"options":[]')
    return base + f'Return JSON {{"stem":"...",{opts},"has_figure":bool}}.'


# Image-question ids are {prefix}_{year}_{question_id}. JEE-Advanced Physics keeps its
# original prefix so re-ingest stays idempotent against the ~54 diagram questions
# already banked under `jee_adv_phy_`.
_ID_PREFIX = {
    ("JEE Advanced", "Physics"): "jee_adv_phy",
    ("JEE Advanced", "Chemistry"): "jee_adv_chem",
    ("JEE Advanced", "Mathematics"): "jee_adv_math",
    ("NEET", "Physics"): "neet_phy",
    ("NEET", "Chemistry"): "neet_chem",
    ("NEET", "Biology"): "neet_bio",
}


def image_id_prefix(exam: str, subject: str) -> str:
    key = (exam, subject)
    if key in _ID_PREFIX:
        return _ID_PREFIX[key]
    slug = re.sub(r"[^a-z0-9]+", "_", f"{exam} {subject}".lower()).strip("_")
    return slug


_LABEL_CORE = re.compile(r"[A-Za-z0-9]+")


def letterize_options(opts: list[dict], answer: str) -> tuple[list[dict], str]:
    """Normalise numerically-labelled options + index-style answer keys to A/B/C/D.

    NEET papers print options as (1)(2)(3)(4) and Reja1 gives the key as an option
    INDEX ("1"), whereas JEE Advanced papers use (A)(B)(C)(D). The bank standardises
    on letters — the validator, `answers_match` and the frontend all assume A-D — so
    a numeric paper is normalised here rather than special-cased everywhere else.

    Three shapes are handled:
      labels 1,2,3,4  / (1)(2)(3)(4)  -> relabelled A-D, answer mapped by value
      labels A,B,C,D with a numeric key -> answer mapped POSITIONALLY (1 -> first label)
      already-lettered labels + letter key -> untouched

    Positional mapping is deliberately limited to 4-option questions, the NEET/JEE
    standard: a 5+-option extraction is a vision mis-parse, and guessing its key
    would put a wrong answer into the bank."""
    if not opts:
        return opts, answer
    cores = []
    for o in opts:
        m = _LABEL_CORE.search(str(o.get("label", "")))
        cores.append(m.group(0) if m else "")
    ans = (answer or "").strip().upper()

    if all(c.isdigit() and 1 <= int(c) <= 26 for c in cores if c) and any(cores):
        mapping = {c: chr(64 + int(c)) for c in cores if c}   # "1" -> "A"
        for o, c in zip(opts, cores):
            o["label"] = mapping.get(c, o.get("label"))
        # single digits only: a multi-answer key is "13" = options 1 and 3
        return opts, "".join(mapping.get(t, t) for t in re.findall(r"\d|[A-Z]", ans))

    if ans.isdigit() and len(opts) == 4 and all(c.isalpha() for c in cores if c):
        # letters already, but the key is a 1-based index into the printed order
        for o, c in zip(opts, cores):
            o["label"] = c.upper()
        idx = int(ans)
        if 1 <= idx <= len(opts):
            return opts, str(opts[idx - 1]["label"])
    return opts, answer


def from_image_row(row: dict, llm, exam: str = "JEE Advanced", subject: str = "Physics") -> Question | None:
    """Download the question image, structure it with the vision LLM, attach the
    metadata answer. Returns None if the model can't read it."""
    if not llm.ok:
        raise RuntimeError("image extraction needs the vision LLM (set QBANK_LLM proxy).")
    qtype = _IMG_QTYPE.get(row.get("question_type", "MCQ_SINGLE_CORRECT"), "MCQ_single")
    need = qtype in ("MCQ_single", "MCQ_multi")
    img = urllib.request.urlopen(row["image_url"], timeout=45).read()
    data = llm.vision_json(_img_sys(need, exam, subject), "Extract this question.", img,
                           mime="image/png")
    if not data:
        return None
    stem = repair_latex((data.get("stem") or "").strip())
    if not stem:
        return None
    opts = ([{"label": o.get("label"), "text": repair_latex(o.get("text", ""))}
             for o in data.get("options", [])] if need else [])
    try:
        alist = _json.loads(row["correct_answer"])
    except Exception:
        alist = [str(row["correct_answer"])]
    answer = "".join(str(x) for x in alist) if need else str(alist[0])
    if need:
        opts, answer = letterize_options(opts, answer)
    h = content_hash(stem)
    year = row.get("exam_year")
    qid = f"{image_id_prefix(exam, subject)}_{year}_{row.get('question_id')}"

    # figure handling: if the question has a diagram, keep the ORIGINAL image as its figure
    has_fig = bool(data.get("has_figure")) or references_figure(stem)
    figure_url = None
    figure_refs = []
    if has_fig:
        os.makedirs(config.FIG_DIR, exist_ok=True)
        fname = f"{qid}.png"
        with open(os.path.join(config.FIG_DIR, fname), "wb") as f:
            f.write(img)
        figure_url = f"{config.PUBLIC_BASE}/figures/{fname}"
        figure_refs = [fname]

    return Question(id=qid, exam=exam, subject=subject, stem=stem, qtype=qtype, options=opts,
                    correct_answer=answer, source=f"{exam} {year} (img)", year=year, hash=h,
                    needs_figure=has_fig, figure_url=figure_url, figure_refs=figure_refs)
