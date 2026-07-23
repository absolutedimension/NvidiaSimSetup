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
    t = re.sub(r"[^a-z0-9]+", " ", t)        # keep only alnum
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
    r"\b(figure|fig\.|diagram|as shown|shown in the|circuit shown|"
    r"the circuit|the graph|graph shown|arrangement shown|shown below|"
    r"shown above|in the figure|as depicted|the figure)\b", re.I)


def references_figure(text: str) -> bool:
    return bool(_FIG_RE.search(text or ""))


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
