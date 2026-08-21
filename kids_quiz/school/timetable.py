#!/usr/bin/env python3
"""timetable.py — the school timetable a child's daily worksheet is built from.

WHY THIS IS A FILE AND NOT A SCRAPER
------------------------------------
The school portal (cags.edusprint.in) puts an IMAGE CAPTCHA on every login
(`POST /cags/Security/Login/MCampusLogin` wants SiteUserName + SitePassword +
LoginCaptcha, image from /cags/Uploader/Captcha) and expires sessions fast. So there is
no unattended login, by design of the site. There doesn't need to be: a timetable is a
FIXED WEEKLY GRID. Capture it once from the portal, keep it here, refresh it only when
the school actually changes the schedule. Everything that varies daily — which weekday
it is, which periods run — is computed locally.

A profile is one child:
  {"name": ..., "board": "ICSE", "cls": 3, "section": "III - A",
   "source": {...where it came from + when...},
   "week": {"mon": [{"period": 1, "subject": "Marathi", "teacher": "..."}, ...], ...}}

School subject names are NOT engine subject names — SUBJECT_MAP does that translation,
and deliberately maps non-academic and unsupported periods to None so we never pretend
to have a bank we don't (there is no Marathi bank; Assembly isn't a subject).
"""
import json
import pathlib
from datetime import date

HERE = pathlib.Path(__file__).parent
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_LABEL = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
             "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}

# school period name (lowercased, trimmed) → the subject our engine actually serves.
# None = we have no bank for it, so it must NOT produce a worksheet section.
# Keys below are the ACTUAL period names on Shivaay's III-A timetable (read from the portal
# 2026-08-18) plus common variants. A name that is NOT in this dict is reported as
# UNRECOGNISED rather than quietly skipped — that's how a new subject gets noticed.
SUBJECT_MAP = {
    # academic, supported by a bank
    "mathematics": "Mathematics", "maths": "Mathematics", "math": "Mathematics",
    "mathlab": "Mathematics",                       # the school's hands-on maths period
    "english": "English", "english language": "English", "english literature": "English",
    "hindi": "Hindi",
    "gk": "GK", "general knowledge": "GK",
    # ICSE splits what our class-3 bank calls EVS into Science + Social Studies
    "evs": "EVS", "environmental studies": "EVS",
    "science": "EVS", "science activity": "EVS", "social studies": "EVS",

    # on the timetable, but NOT something we can generate honest practice for
    "marathi": None,                                # no Marathi bank
    "robotics and computers": None, "computer": None, "computers": None,
    "financial literacy": None,
    "assembly": None, "value education": None, "moral science": None,
    "athletics": None, "traditional game": None, "jpett": None,
    "pt": None, "physical education": None, "games": None, "sports": None,
    "art": None, "drawing": None, "craft": None, "music": None, "dance": None,
    "library": None, "break": None, "lunch": None, "recess": None,
}

# Why a mapped-to-None subject is skipped, so the daily run SAYS it instead of silently
# dropping the period. Anything not named here gets the generic non-academic reason.
PRACTICE_GAPS = {
    "marathi": "no Marathi question bank",
    "robotics and computers": "no computing bank",
    "computer": "no computing bank", "computers": "no computing bank",
    "financial literacy": "no financial-literacy bank",
}


def load(profile: str = "shivaay") -> dict:
    p = HERE / f"{profile}.json"
    if not p.exists():
        raise FileNotFoundError(
            f"No timetable for '{profile}'. Capture it from the school portal once, then "
            f"write it to {p} (see shivaay.json for the shape).")
    return json.loads(p.read_text(encoding="utf-8"))


def day_key(d: date) -> str:
    return DAYS[d.weekday()]


def periods_for(prof: dict, d: date) -> list:
    """The raw timetable rows for that weekday ([] on a holiday/weekend with no entry)."""
    return prof.get("week", {}).get(day_key(d), []) or []


def subjects_for(prof: dict, d: date):
    """(practisable subjects, skipped rows) for a date.

    Each practisable entry is {"subject": <engine subject>, "periods": <how many that day>}.
    Period COUNT matters: three English periods and one Maths period is a day that leaned on
    English, and the sheet should lean the same way. Order follows the school day, so the
    worksheet mirrors the lessons he just sat through.

    A period name missing from SUBJECT_MAP is reported as unrecognised, not silently dropped —
    otherwise a new subject on the timetable would vanish without anyone noticing."""
    practise, skipped, index = [], [], {}
    for row in sorted(periods_for(prof, d), key=lambda r: r.get("period", 99)):
        raw = str(row.get("subject", "")).strip()
        if not raw:
            continue
        key = raw.lower()
        if key not in SUBJECT_MAP:
            skipped.append({"subject": raw, "why": "UNRECOGNISED — add it to SUBJECT_MAP"})
            continue
        mapped = SUBJECT_MAP[key]
        if mapped is None:
            skipped.append({"subject": raw,
                            "why": PRACTICE_GAPS.get(key, "not an academic practice subject")})
            continue
        if mapped in index:
            index[mapped]["periods"] += 1
        else:
            index[mapped] = {"subject": mapped, "periods": 1}
            practise.append(index[mapped])
    return practise, skipped


if __name__ == "__main__":                       # quick look at what today would produce
    import sys
    prof = load(sys.argv[1] if len(sys.argv) > 1 else "shivaay")
    today = date.today()
    p, s = subjects_for(prof, today)
    print(f"{prof['name']} · {prof['board']} class {prof['cls']} · {DAY_LABEL[day_key(today)]}")
    print("  practise:", [f"{x['subject']}×{x['periods']}" for x in p]
          or "(nothing — holiday or no academic periods)")
    print("  skipped :", [f"{x['subject']} ({x['why']})" for x in s] or "none")
