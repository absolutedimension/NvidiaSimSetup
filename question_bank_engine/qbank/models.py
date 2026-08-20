"""The canonical Question record. 'Clean' == this fully populated + verified=True.

Tagging fields (chapter/concept/difficulty) are intentionally left null in Phase 1 —
they are the NEXT task (the tagging agent). This phase only guarantees a correct,
de-duplicated, validated question."""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


def normalize_for_hash(text: str) -> str:
    """Aggressive normalize so trivially-different copies of the same question collide."""
    t = text.lower()
    t = re.sub(r"\\[a-zA-Z]+", " ", t)      # drop LaTeX command names
    # Keep Devanagari as well as ASCII alnum. The old pattern stripped every non-ASCII
    # character, so EVERY Hindi question normalised to "" and hashed identically — the whole
    # Hindi bank would have collapsed into one "duplicate". English rows are unaffected
    # (they contain no Devanagari), so existing hashes do not change.
    t = re.sub(r"[^a-z0-9\u0900-\u097f]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def content_hash(stem: str) -> str:
    return hashlib.sha1(normalize_for_hash(stem).encode()).hexdigest()[:16]


# LLM JSON+LaTeX corruption: models often emit '\text','\frac','\alpha' with a SINGLE
# backslash; JSON then decodes '\t','\f','\a'… into control chars, breaking the LaTeX.
# Reconstruct the backslash-command from the control char. '\n' is left alone (real
# newlines are legitimate in stems/tables).
_CTRL_TO_TEX = {"\t": r"\t", "\x0c": r"\f", "\x08": r"\b", "\x0b": r"\v",
                "\r": r"\r", "\x07": r"\a"}


def repair_latex(s: str) -> str:
    if not s:
        return s
    for ch, tex in _CTRL_TO_TEX.items():
        s = s.replace(ch, tex)
    return s


# Models sometimes double-escape newlines, so a worked solution arrives carrying the
# two characters \ + n instead of a line break, and the frontend renders a literal
# "\n\n" mid-paragraph. Unescaping blindly would wreck LaTeX, because plenty of real
# commands start with \n — \nu, \neq, \nabla, \not, \nonumber, \nolimits, \newline.
# Every such command is LOWERCASE after the \n, while a broken newline is followed by
# a capital, a digit, punctuation or another backslash ("\nThus", "\n\n1."). So the
# guard is "not followed by a lowercase letter" — narrower than "not a letter", which
# left \nThus / \nFrom / \nTherefore unfixed.
_ESCAPED_NL = re.compile(r"\\n(?![a-z])")


def unescape_newlines(s: str) -> str:
    return _ESCAPED_NL.sub("\n", s) if s else s


# A question "needs a figure" when its text refers to a diagram/graph/circuit it can't
# stand without. Used to (a) flag ingested diagram questions and (b) keep generation
# honest (never emit a figure-less question that requires one).
_FIG_RE = re.compile(
    r"\b(figure|fig\.|diagram|graph|circuit|newman projection|"
    r"as shown|shown in the|shown below|shown above|as depicted|"
    r"in the (figure|diagram|graph|circuit)|the (figure|diagram|graph|circuit)|"
    r"arrangement shown|"
    # "the/given following <thing that is only drawable>"
    r"(following|given|above) (structure|structures|compound|compounds|molecule|molecules|"
    r"carbocation|reaction|reactions|scheme|arrangement|complex|cell|projection|conformation)|"
    r"structures? of the following)\b", re.I)

# a Column-I/Column-II or List-I/List-II matching question -> the lists live in the figure
_MATCH_RE = re.compile(
    r"\b(column\s*-?\s*(i|ii|1|2)\b|list\s*-?\s*(i|ii)\b|match the (following|column|list|reaction|item))",
    re.I)

# an option whose text is only a bare label/reference (i, ii, P, a) — NOT a plain number,
# which is a real numeric answer. Roman numerals / P-S / a-d used as option TEXT mean the
# real answer choices live in the missing figure.
_BARE_OPT_RE = re.compile(r"^\(?\s*([ivx]{1,4}|[a-d]|[pqrs])\s*\)?[.:]?$", re.I)
# options that are an ORDERING of such labels: "a>b>c>d", "II < I < IV < III", "P>Q>R"
_ORDER_OPT_RE = re.compile(r"^[\s(]*[ivxa-dpqrs][\s)]*([<>=,][\s(]*[ivxa-dpqrs][\s)]*)+$", re.I)
_MCQ = {"MCQ_single", "MCQ_multi"}


def references_figure(text: str) -> bool:
    t = text or ""
    return bool(_FIG_RE.search(t) or _MATCH_RE.search(t))


def options_are_bare(options) -> bool:
    """True when MCQ options carry no real content — empty, or just labels/orderings of labels
    (i, ii, a>b>c) — a sign the answer choices live only in the missing figure. Plain numbers are
    real answers, NOT bare. Only meaningful for MCQ-type questions (caller checks qtype)."""
    if not options:
        return True
    texts = [str((o.get("text") if isinstance(o, dict) else o) or "").strip() for o in options]
    if any(t == "" for t in texts):
        return True
    return len(texts) >= 2 and all(_BARE_OPT_RE.match(t) or _ORDER_OPT_RE.match(t) for t in texts)


def is_figure_dependent(stem: str, options=None, qtype: str = "MCQ_single") -> bool:
    """A question is figure-dependent (INCOMPLETE without a figure) if its TEXT references a
    figure/matching-table, or (for MCQs) its options carry no real content. qtype-aware:
    integer/numeric questions legitimately have empty options, so only the stem is checked.
    High precision — safe to gate serving on."""
    if references_figure(stem or ""):
        return True
    if qtype in _MCQ and options_are_bare(options or []):
        return True
    return False


# Valid question types
QTYPES = {"MCQ_single", "MCQ_multi", "integer", "numeric"}


@dataclass
class Question:
    id: str
    exam: str                 # "JEE Advanced"
    subject: str              # "Physics"
    stem: str                 # question text, LaTeX preserved
    qtype: str                # one of QTYPES
    options: list = field(default_factory=list)   # [{"label":"A","text":"..."}]; [] for integer/numeric
    correct_answer: str = ""  # "B" | "AC" | "12" | "3.14"
    solution: str = ""
    figure_refs: list = field(default_factory=list)
    needs_figure: bool = False       # question depends on a diagram/graph/circuit
    figure_url: Optional[str] = None  # served PNG (ingested real questions)
    figure_svg: Optional[str] = None  # inline SVG diagram (generated questions)
    # --- tagging (Phase 2 — the tagging agent fills these) ---
    chapter: Optional[str] = None
    concept: Optional[str] = None
    difficulty: Optional[int] = None
    bloom_level: Optional[str] = None
    # --- provenance ---
    # --- bilingual (Hindi) mirrors. Optional: English-only rows leave these empty and the
    # serving layer falls back to English, so nothing breaks for banks without Hindi.
    # Bihar govt exams (BSSC/BPSC/TRE) print the paper in BOTH languages, so this is the
    # shape the real paper has — not a translation bolted on.
    stem_hi: str = ""
    options_hi: list = field(default_factory=list)   # [{"label":"A","text":"..."}], same order as options
    solution_hi: str = ""
    source: str = ""          # "JEE Adv 2016 Paper 1"
    year: Optional[int] = None
    # --- pipeline state ---
    verified: bool = False
    generated: bool = False   # True = authored by the generator (not a real past-paper question)
    validation_issues: list = field(default_factory=list)
    duplicate_of: Optional[str] = None
    hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
