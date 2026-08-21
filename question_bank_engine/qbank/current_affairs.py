"""Current affairs — the one topic whose facts have a SHELF LIFE.

Measured on the real papers: 45 of 552 official General Studies questions (8.2%) carry an explicit
year, and 44 of those are tagged Current Affairs. The commission asks about the exam year and
roughly the twelve months before it — a March-2025 paper asked about Operation Abhyas on 7 May
2025, Wimbledon 2025, and the 2024 Nobel Prizes — and it LOCALISES: *"In the 2025 Duleep Trophy,
which Bihar-born player was appointed captain of the East Zone?"*

Everything else in this bank rests on a fact that cannot change. A state capital is true forever;
`quantgen` computes its own answer. Current affairs breaks that, and it breaks it in two very
different ways which this module deliberately separates:

    SETTLED EVENTS   Who won the 2024 Nobel Prize in Physics. Who hosted the 2024 Olympics.
                     True the moment it happened and true forever after. It only stops being
                     CURRENT — it never stops being CORRECT.

    LIVE STATES      The repo rate. Who the RBI Governor is. The population of a city.
                     These go WRONG, not just stale, and a paper that prints one teaches a
                     student the wrong answer for an exam they sit next month.

**Only settled events go in this file.** That single rule turns an accuracy problem into a
relevance problem, and a relevance problem is one a date can solve. The real papers' own
questions are overwhelmingly of the settled kind, which is what makes the restriction affordable
rather than limiting.

🔴 **REVIEWED = False, and this table needs a person MORE than any other in the repo.** Not
because the facts are subtle but because they are numerous, they churn, and nobody can hold a
year's news in their head accurately. Hand-written data here measures ~1 error in 27 across the
repo; on current affairs, written from memory, assume worse. The institute teaches this material
every single day — **One Step supplies and verifies the facts, we supply the machinery.** That is
the honest division and it is also the cheaper one.

⚖️ COPYRIGHT (skill §7). Facts and dates are not expression, so a Nobel laureate's name is free to
state. A *compilation* — Testbook's or Adda247's "Current Affairs 2025" PDF — is their copyright
and they are our competitors. Source from primary material (PIB, the awarding body, the
federation) or from the institute's own notes. Never from a competitor's compilation.
"""
import datetime
import io

REVIEWED = False
REVIEWED_BY = ""

# How old a fact may be and still be asked as "current". The real papers reach back about a year
# from the exam; twelve months is that, and it is checked rather than assumed — see stale().
WINDOW_MONTHS = 18

# Each row: (question, answer, ANSWER TYPE, ISO date the event settled, primary source).
#
# The ANSWER TYPE is what makes an MCQ possible at all. Every other table in this bank is
# key -> value, so the wrong options are simply other values of the same table — all countries, or
# all capitals, or all atomic numbers. A current-affairs row is a standalone question, so there is
# no sibling column to draw from and the distractors have to come from somewhere. They come from
# the OTHER ROWS OF THE SAME TYPE: a "country" answer is offered against other country answers in
# this table.
#
# The consequence is a hard requirement, checked by `shortfall()` and printed on every build:
# **a type needs at least four rows before ANY of its questions can be asked.** Three facts about
# three different kinds of thing produce zero questions, which is exactly what the seed below did
# before types were added.
#
# The date is not decoration either — `usable()` filters on it and the paper prints it as a cut-off.
EVENTS = [
    # ── sport: settled the moment the final whistle goes ────────────────────────────────────────
    {"en": "Which country hosted the 2024 Summer Olympics?",
     "hi": "2024 के ग्रीष्मकालीन ओलंपिक की मेज़बानी किस देश ने की?",
     "ans": "France", "ans_hi": "फ्रांस", "type": "country", "domain": "sport-host",
     "date": "2024-08-11", "source": "International Olympic Committee"},
    {"en": "Which country hosted the 2023 ICC Cricket World Cup?",
     "hi": "2023 के आईसीसी क्रिकेट विश्व कप की मेज़बानी किस देश ने की?",
     "ans": "India", "ans_hi": "भारत", "type": "country", "domain": "sport-host",
     "date": "2023-11-19", "source": "International Cricket Council"},
    {"en": "Which country hosted the 2022 FIFA World Cup?",
     "hi": "2022 के फीफा विश्व कप की मेज़बानी किस देश ने की?",
     "ans": "Qatar", "ans_hi": "क़तर", "type": "country", "domain": "sport-host",
     "date": "2022-12-18", "source": "FIFA"},
    {"en": "Which country hosted the 2024 Paralympic Games?",
     "hi": "2024 के पैरालंपिक खेलों की मेज़बानी किस देश ने की?",
     "ans": "France", "ans_hi": "फ्रांस", "type": "country", "domain": "sport-host",
     "date": "2024-09-08", "source": "International Paralympic Committee"},

    # ── people: settled on announcement ─────────────────────────────────────────────────────────
    {"en": "Who became the youngest-ever World Chess Champion, in December 2024?",
     "hi": "दिसंबर 2024 में सबसे कम आयु के विश्व शतरंज चैंपियन कौन बने?",
     "ans": "D. Gukesh", "ans_hi": "डी. गुकेश", "type": "person", "domain": "chess",
     "date": "2024-12-12", "source": "FIDE"},
    {"en": "Who won the men's singles title at Wimbledon 2024?",
     "hi": "विंबलडन 2024 का पुरुष एकल खिताब किसने जीता?",
     "ans": "Carlos Alcaraz", "ans_hi": "कार्लोस अल्काराज़", "type": "person", "domain": "tennis-men",
     "date": "2024-07-14", "source": "All England Club"},
    {"en": "Who was awarded the 2024 Nobel Prize in Literature?",
     "hi": "2024 का साहित्य का नोबेल पुरस्कार किसे दिया गया?",
     "ans": "Han Kang", "ans_hi": "हान कांग", "type": "person", "domain": "nobel",
     "date": "2024-10-10", "source": "Swedish Academy"},
    {"en": "Who won the Women's Singles title at the 2024 Australian Open?",
     "hi": "2024 के ऑस्ट्रेलियन ओपन का महिला एकल खिताब किसने जीता?",
     "ans": "Aryna Sabalenka", "ans_hi": "आर्यना सबालेंका", "type": "person", "domain": "tennis-women",
     "date": "2024-01-27", "source": "Tennis Australia"},
]

# Bihar-localised current affairs. The commission does this and we should: a Bihar-born player, a
# Bihar scheme, a Bihar appointment. Seeded EMPTY on purpose — this is exactly the content the
# institute has and we do not, and guessing it is how a paper loses a Patna owner's trust.
BIHAR_EVENTS = []


MIN_PER_TYPE = 4          # four rows of a type, or its questions have no wrong options to offer


def _d(s):
    return datetime.date.fromisoformat(s)


def stale(row, as_of):
    """True when a fact is too old to be asked as 'current' on a paper dated `as_of`.

    Correctness is not in question here — a settled event stays true. This is purely "would the
    commission still call this current", and the answer is measured from the real papers: about a
    year, so WINDOW_MONTHS is the guard rail rather than a guess.
    """
    return (as_of - _d(row["date"])).days > WINDOW_MONTHS * 31


def usable(as_of=None):
    """The rows a paper dated `as_of` may ask. Empty is a legitimate answer and must be reported.

    A current-affairs section that silently falls back to older facts is the failure mode here:
    the paper looks complete, and every question in it is a year and a half out of date.
    """
    as_of = as_of or datetime.date.today()
    return [r for r in (EVENTS + BIHAR_EVENTS) if not stale(r, as_of)]


def status(as_of=None):
    """One line on whether this table can currently supply a paper — printed on every build."""
    as_of = as_of or datetime.date.today()
    ok = usable(as_of)
    total = len(EVENTS) + len(BIHAR_EVENTS)
    if not REVIEWED:
        return (f"current affairs: {total} facts BUILT but NOT REVIEWED — held back "
                f"(see drop/bssc/CURRENT_AFFAIRS_REVIEW.md)")
    if not ok:
        return (f"current affairs: {total} facts, but NONE inside the {WINDOW_MONTHS}-month "
                f"window as of {as_of} — the table needs refreshing before it can be used")
    newest = max(_d(r["date"]) for r in ok)
    short = shortfall(as_of)
    tail = ("; SHORT OF OPTIONS: " + ", ".join(f"{t} has {n}/{MIN_PER_TYPE}"
                                                     for t, n in short.items())) if short else ""
    return (f"current affairs: {len(ok)} of {total} facts usable as of {as_of} "
            f"(newest {newest}, window {WINDOW_MONTHS} months){tail}")


def cutoff_line(as_of=None):
    """The Hindi/English line a paper prints when it carries current-affairs questions.

    Without it a student cannot tell whether a question is out of date or they are, and an
    institute cannot tell whether the paper is fresh. Every real paper is written to a cut-off;
    ours should say what its cut-off is.
    """
    as_of = as_of or datetime.date.today()
    ok = usable(as_of)
    if not ok:
        return ""
    newest = max(_d(r["date"]) for r in ok)
    return (f"करेंट अफेयर्स {newest.strftime('%d.%m.%Y')} तक · "
            f"Current affairs up to {newest.strftime('%d %b %Y')}")


def review_sheet(path="drop/bssc/CURRENT_AFFAIRS_REVIEW.md"):
    """Every current-affairs row with its date and source, for a person to tick."""
    lines = ["# Current affairs — review sheet", "",
             "**These facts have a SHELF LIFE and are the most error-prone rows in the bank.**",
             "Every one is hand-written. Check the fact, the DATE, and that the source column",
             "is a primary one (PIB, the awarding body, the federation) — never a competitor's",
             "current-affairs compilation (see skill §7).", "",
             f"Window: a fact is asked only if it settled within **{WINDOW_MONTHS} months** of the",
             "paper's date. Older rows stay in the file and simply stop being drawn.", "",
             "⚠️ **TWO edits to go live, made together:**", "",
             "1. `REVIEWED = True` in `qbank/current_affairs.py`",
             "2. add `[\"CURRENT_AFFAIRS\"]` to `concepts` for **Science news & current events**",
             "   in `drop/bssc/SYLLABUS_MAP.json`", "",
             "⭐ **This table is meant to be filled by the INSTITUTE, not by us.** One Step teaches",
             "current affairs daily and has the verified material; we own the machinery. The",
             "`BIHAR_EVENTS` list is deliberately empty for the same reason — Bihar-localised",
             "current affairs is exactly what they have and we do not.", ""]
    n = 0
    for label, rows in (("EVENTS", EVENTS), ("BIHAR_EVENTS", BIHAR_EVENTS)):
        lines += [f"## {label}", ""]
        if not rows:
            lines += ["_(empty — to be supplied by the institute)_", ""]
        for r in rows:
            n += 1
            lines += [f'- [ ] **{r["en"]}**', f'      → **{r["ans"]}**  _({r["type"]})_',
                      f'      हिंदी: {r["hi"]} → {r["ans_hi"]}',
                      f'      settled {r["date"]} · source: {r["source"]}', ""]
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} current-affairs rows -> {path}")
    return n


def by_type(as_of=None):
    """Usable rows grouped by (type, domain) — the pool a question draws its wrong options from.

    TYPE alone is too coarse and it showed immediately: "Who won the men's singles title at
    Wimbledon 2024?" came out offered against a novelist, a chess player and the women's champion,
    because all four are of type `person`. Those are category errors — a candidate discards them
    without knowing any tennis, so the question tests nothing.

    DOMAIN is what makes the wrong options plausible: other men's-singles champions, other Nobel
    laureates, other host countries. It is the same principle as gs_ask._near — a distractor has
    to be the kind of thing that could have been the answer.
    """
    out = {}
    for r in usable(as_of):
        out.setdefault((r["type"], r.get("domain") or r["type"]), []).append(r)
    return out


def shortfall(as_of=None):
    """Types that cannot yet produce a question, and how many rows they still need.

    Reported rather than silently skipped. A type with three rows looks like content in the file
    and produces nothing in the paper, which is the shape of gap this repo keeps rediscovering.
    """
    return {f"{t}/{d}": len(rs) for (t, d), rs in by_type(as_of).items() if len(rs) < MIN_PER_TYPE}


def build(rng, diff=2, as_of=None):
    """One current-affairs MCQ, or None when no type has enough rows to offer wrong options."""
    pools = {t: rs for t, rs in by_type(as_of).items() if len(rs) >= MIN_PER_TYPE}
    if not pools:
        return None
    key = rng.choice(sorted(pools))
    rows = pools[key]
    row = rng.choice(rows)
    others = [r for r in rows if r["ans"] != row["ans"]]
    if len(others) < 3:
        return None
    rng.shuffle(others)
    picked = others[:3]
    return {"stem": row["en"], "stem_hi": row["hi"], "correct": row["ans"],
            "distractors": [r["ans"] for r in picked],
            # hi_opts keys on the ENGLISH option text, exactly as gs_ask does, so the renderer can
            # print each option in both scripts without a second lookup path.
            "hi_opts": {r["ans"]: r["ans_hi"] for r in picked + [row]},
            "solution": f'{row["ans"]}. (settled {row["date"]})',
            "solution_hi": f'{row["ans_hi"]}। (दिनांक {row["date"]})',
            "concept": "Current Affairs", "src": ["CURRENT_AFFAIRS"],
            "fact": f'CA|{row["en"]}', "difficulty": 2}
