#!/usr/bin/env python3
"""Play Store lead sweep — find coaching institutes that ALREADY pay for software.

WHY THIS SOURCE BEATS GOOGLE MAPS / LINKEDIN
    An institute with its own branded Android app bought a white-label platform
    (Classplus year-1 runs Rs 4-11 lakh). So the owner is pre-qualified twice over:
    they have budget, and they already said yes to buying software. Better still,
    those platforms ship a test-creation TOOL with no questions in it — the owner
    must supply content themselves. That empty test module is the Acharya pitch.

WHAT IS AUTOMATED HERE
    1. Play Store search across several query shapes for a city.
    2. Resolve each hit to its real app title + white-label vendor.
    3. Fingerprint the platform from the package id (co.<word>.<rand> = Classplus).
    4. Pull reviews via Play's own reviews RPC and mine them for test/paper
       complaints - a public, timestamped, per-institute pain signal.
    5. Score + rank, and emit rows in the patna_institutes.csv schema.

WHAT IS **NOT** AUTOMATED (by design - do not try)
    The phone number. A Play listing's "developer contact" is the VENDOR's
    (e.g. psupdates@classplus.co), never the institute's. Contacts must come from
    the institute's own site or public directory listing - which is also what keeps
    us inside the sourcing rule in SOLO_TUTOR_SOURCING.md: a number is only used
    when the institute self-published it to receive coaching enquiries.

PRECISION WARNING
    Play Store search leaks nationally. It is reliable at finding *institutes with apps*
    and at mining their reviews; it is WEAK at proving which city they are in. A Patna
    sweep is clean because "Patna" sits in the app names. A Gaya sweep is messy because
    "gaya" is also a Hindi word ("ho gaya"), so review matching produces false hits, and
    the top-ranked result was Lakshya Classes *Udaipur*. Rules of thumb:
      * always read the CITY? column; treat UNVERIFIED and "reviews?" as unverified
      * pass --strict-city for ambiguous city names
      * confirm on Google Maps before anyone travels. Always.

USAGE
    python3 playstore_lead_sweep.py --city Gaya --strict-city
    python3 playstore_lead_sweep.py --city Patna --vendor "Education Mobile Media"
    python3 playstore_lead_sweep.py --city Bhagalpur --min-reviews 5 --out leads.csv

Only reads public listing pages, one request at a time with a delay. Keep it that way.
"""
from __future__ import annotations
import argparse, csv, json, re, sys, time, urllib.error, urllib.parse, urllib.request

PLAY = "https://play.google.com"
UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")}
DELAY = 1.0          # be polite; this is someone else's server
_last = [0.0]

# National apps that pollute city searches. These are not leads.
NATIONAL = re.compile(r"""^(
    com\.testbook|com\.unacademyapp|xyz\.penpencil|com\.adda247|com\.studyiq|com\.edurev|
    com\.vedantu|digital\.allen|com\.gradeup|com\.oliveboard|apps\.ibpsguide|com\.vidyakul|
    org\.khanacademy|com\.reddit|net\.one97|in\.swiggy|com\.google|com\.doubtnut|
    com\.toppr|com\.byjus|me\.entri|com\.emedicoz|com\.sathee_app|com\.teachmint\.teachmint|
    com\.spayee|com\.examsnet|com\.sanaedutech|bihar\.exams|com\.statepsc
)""", re.X)

# Non-institute noise: civic apps, school ERPs, metro/news/utility apps.
NOISE = re.compile(r"(grievance|metro|zoo|news|nagarnigam|cab|delivery|instamart|calendar|"
                   r"schoolcanvas|parentsalarm|edunext|schoolknot|cdac|josaa|counsel)", re.I)

# City names that are also everyday Hindi/regional words, so finding them in review
# text proves nothing. "gaya" = "went/has happened"; "ara" and "pali" are also words.
CITY_AMBIGUOUS = {"gaya", "ara", "pali", "sasaram"}

# A review mentioning any of these is talking about the thing we sell.
PAIN = re.compile(r"\b(test|tests|paper|papers|dpp|mock|question|questions|practice|"
                  r"syllabus|series|quiz|pdf|material|notes)\b", re.I)

# Package-id prefix -> white-label platform.
def platform_of(app_id: str, dev: str) -> str:
    if app_id.startswith("co.classplus."):
        return "Classplus"
    if re.match(r"^co\.[a-z0-9]+\.[a-z]{4,8}$", app_id):
        return "Classplus (reseller)"
    if "appx" in app_id.lower() or "appx" in dev.lower():
        return "Appx"
    if re.match(r"^com\.[a-z]{4,8}\.[a-z]{6}$", app_id):
        return "white-label (unknown vendor)"
    return "self-built / other"


def _fetch(url: str, data: bytes | None = None, ctype: str | None = None) -> str:
    wait = DELAY - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    headers = dict(UA)
    if ctype:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""
        raise


def search(query: str) -> list[str]:
    h = _fetch(f"{PLAY}/store/search?q={urllib.parse.quote(query)}&c=apps&hl=en_IN&gl=IN")
    return list(dict.fromkeys(re.findall(r"/store/apps/details\?id=([a-zA-Z0-9._]+)", h)))


def vendor_roster(vendor: str) -> list[str]:
    """Every institute app published under one white-label reseller label (~20 per page)."""
    h = _fetch(f"{PLAY}/store/apps/developer?id={urllib.parse.quote(vendor)}&hl=en_IN")
    return list(dict.fromkeys(re.findall(r"/store/apps/details\?id=([a-zA-Z0-9._]+)", h)))


def detail(app_id: str) -> dict | None:
    h = _fetch(f"{PLAY}/store/apps/details?id={app_id}&hl=en_IN")
    if not h:
        return None
    m = re.search(r"<title[^>]*>([^<]*)</title>", h)
    title = (m.group(1) if m else "").replace(" – Apps on Google Play", "").strip()
    devs = re.findall(r"/store/apps/(?:dev|developer)\?id=([^\"&]+)", h)
    dev = urllib.parse.unquote_plus(devs[0]) if devs else ""
    return {"id": app_id, "title": title, "dev": dev}


def reviews(app_id: str, count: int = 80) -> list[tuple[int, str]]:
    """Play's own reviews RPC. Details pages are JS-rendered; reviews come from here."""
    payload = [[["UsvDTd", json.dumps([None, None, [2, 1, [count, None, None], None, []],
                                       [app_id, 7]]), None, "generic"]]]
    body = urllib.parse.urlencode({"f.req": json.dumps(payload)}).encode()
    t = _fetch(f"{PLAY}/_/PlayStoreUi/data/batchexecute?rpcids=UsvDTd&hl=en_IN&gl=IN",
               data=body, ctype="application/x-www-form-urlencoded;charset=UTF-8")
    out = []
    for rating, raw in re.findall(r',(\d),null,\\"((?:[^"\\]|\\.){12,900}?)\\",\[\d{9,10}', t):
        txt = re.sub(r"\s+", " ", raw.replace('\\\\n', ' ').replace('\\\\"', '"')
                                      .replace('\\', '')).strip()
        out.append((int(rating), txt))
    return out


def assess(app: dict, revs: list[tuple[int, str]], city: str) -> dict:
    total = len(revs)
    low = [r for r in revs if r[0] <= 2]
    pain_low = [f"{r}* {t}" for r, t in revs if r <= 3 and PAIN.search(t)]
    pain_any = [f"{r}* {t}" for r, t in revs if PAIN.search(t)]

    # CITY CONFIDENCE. Play Store search leaks nationally — an "academy Gaya" query
    # happily returns Kavya Classes *Guna* (MP). Never let an unverified row look
    # like a visitable lead; someone travels on these.
    c = city.lower()
    if c in app["title"].lower():
        conf = "title"
    elif any(c in t.lower() for _, t in revs):
        # Some city names are also everyday Hindi words — "gaya" is the past participle
        # of jaana ("ho gaya"), so Hindi reviews match it constantly. Don't trust those.
        conf = "reviews?" if c in CITY_AMBIGUOUS else "reviews"
    else:
        conf = "UNVERIFIED"

    # Rank: a documented complaint about tests is worth far more than raw volume.
    score = len(pain_low) * 10 + len(pain_any) * 2 + (len(low) / total * 8 if total else 0) \
            + min(total, 60) / 20
    if conf == "UNVERIFIED":
        score *= 0.4          # sink it, don't hide it
    elif conf == "reviews?":
        score *= 0.7          # matched the city name, but the name is a common word
    return {**app, "reviews": total, "low_1_2": len(low),
            "pain_low": pain_low[:3], "pain_any": pain_any[:3],
            "city_conf": conf, "score": round(score, 1)}


def looks_like_local_institute(app: dict, city: str) -> bool:
    if NATIONAL.match(app["id"]) or NOISE.search(app["id"]) or NOISE.search(app["title"]):
        return False
    t = app["title"].lower()
    if not t:
        return False
    # Either the city is in the name, or it smells like a coaching brand.
    return (city.lower() in t
            or bool(re.search(r"(class|classes|academy|institute|coaching|tutorial|"
                              r"gurukul|sir|study|educat|learn)", t)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--city", required=True, help='e.g. "Gaya", "Muzaffarpur", "Ranchi"')
    ap.add_argument("--vendor", action="append", default=[],
                    help="also sweep this white-label reseller's whole roster (repeatable)")
    ap.add_argument("--query", action="append", default=[], help="extra search query (repeatable)")
    ap.add_argument("--min-reviews", type=int, default=3,
                    help="skip apps with fewer reviews than this (default 3)")
    ap.add_argument("--limit", type=int, default=40, help="max apps to inspect (default 40)")
    ap.add_argument("--strict-city", action="store_true",
                    help="keep ONLY apps with the city in the app name. Far fewer leads, but "
                         "every one is really in that city. Use this when the city name is also "
                         "a common word (Gaya, Ara, Pali) — otherwise review-text matching lies.")
    ap.add_argument("--out", help="write CSV rows here (default <city>_playstore_leads.csv)")
    a = ap.parse_args()

    city = a.city
    queries = a.query or [f"coaching classes {city}", f"academy {city}", f"institute {city}",
                          f"{city} classes", f"tuition {city}"]

    print(f"== Play Store lead sweep · {city} ==\n")
    cand: list[str] = []
    for q in queries:
        got = search(q)
        cand += got
        print(f"  search {q!r:38} -> {len(got):3} hits")
    for v in a.vendor:
        got = vendor_roster(v)
        cand += got
        print(f"  vendor {v!r:38} -> {len(got):3} apps")
    cand = list(dict.fromkeys(cand))
    print(f"\n  {len(cand)} unique candidates; resolving titles (rate-limited)…\n")

    kept = []
    for app_id in cand[: a.limit]:
        d = detail(app_id)
        if not d or not looks_like_local_institute(d, city):
            continue
        kept.append(d)
        print(f"    ok  {d['title'][:44]:46} [{platform_of(d['id'], d['dev'])}]")

    print(f"\n  {len(kept)} look like local institutes; pulling reviews…\n")
    rows = []
    for d in kept:
        r = assess(d, reviews(d["id"]), city)
        if r["reviews"] < a.min_reviews:
            continue
        if a.strict_city and r["city_conf"] != "title":
            continue
        rows.append(r)
    rows.sort(key=lambda r: -r["score"])

    print(f"{'INSTITUTE':38} {'CITY?':>11} {'REVS':>5} {'LOW':>4} {'PAIN':>5} {'SCORE':>6}")
    for r in rows:
        print(f"{r['title'][:37]:38} {r['city_conf']:>11} {r['reviews']:5} {r['low_1_2']:4} "
              f"{len(r['pain_low']):5} {r['score']:6}")
        for q in r["pain_low"]:
            print(f"      ↳ {q[:108]}")
    n_unver = sum(1 for r in rows if r["city_conf"] == "UNVERIFIED")
    if n_unver:
        print(f"\n  ⚠ {n_unver} row(s) marked UNVERIFIED: the city was found neither in the app "
              f"name nor\n    in any review. Confirm on Google Maps BEFORE anyone travels.")

    out = a.out or f"{city.lower()}_playstore_leads.csv"
    hdr = ["name", "cluster", "subject", "owner", "phone", "size_est", "priority",
           "maya_precall", "visit_status", "pilot_status", "pain_notes"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        for r in rows:
            city_note = {"title": f"city in app name",
                         "reviews": f"city confirmed via review text",
                         "reviews?": (f"WEAK city match: '{city}' appears in reviews but is also "
                                      f"a common Hindi word, so this proves nothing. Treat as "
                                      f"unverified — confirm on Maps."),
                         "UNVERIFIED": (f"!! CITY UNVERIFIED — {city} appears in neither the app "
                                        f"name nor any review. Could be another state entirely "
                                        f"(a 'Gaya' sweep surfaced Kavya Classes *Guna*, MP). "
                                        f"CONFIRM ON MAPS BEFORE TRAVEL.")}[r["city_conf"]]
            note = (f"NEEDS CONTACT (get phone from Google Maps / their own site — the Play "
                    f"listing's developer contact is the VENDOR's, not theirs). {city_note} "
                    f"Platform={platform_of(r['id'], r['dev'])} vendor={r['dev'] or '?'} "
                    f"app={r['id']}. {r['reviews']} reviews / {r['low_1_2']} at 1-2 star.")
            if r["pain_low"]:
                note += " COMPLAINT (verbatim): " + " || ".join(q[:200] for q in r["pain_low"])
            elif r["pain_any"]:
                note += " MENTIONS (verbatim): " + " || ".join(q[:200] for q in r["pain_any"])
            prio = "3" if r["city_conf"] in ("UNVERIFIED", "reviews?") else "2"
            w.writerow([r["title"], "", "", "", "", "", prio, "none", "", "", note])

    print(f"\n  -> {len(rows)} rows written to {out}")
    print("  NEXT (manual, ~2 min each): look each name up on Google Maps for phone + area,")
    print("  fill the phone/cluster columns, then paste into teacher_gtm/patna_institutes.csv.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
