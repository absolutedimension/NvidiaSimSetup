#!/usr/bin/env python3
"""Pull a reference corpus for one GS topic, for the review sheets to quote.

This is the tool history_tables' docstring names and which was never committed — it was written
to /tmp and lost with it, so the corpus it depends on could not be rebuilt. It is here now, and
it is deliberately GENERIC: a topic name and a page list, so economy, agriculture and sports use
one tool instead of three copies that drift.

What this is NOT: a verifier. `history_tables.write_review_sheet` explains at length why automated
pass/fail was abandoned for this data — one checker confirmed "Dandi March -> 1935". The corpus
exists so a HUMAN reviewing a row can see the source sentence without opening a browser, which is
what turns an afternoon into ten minutes.

    python3 tools/fetch_gs_corpus.py economy
"""
import io
import json
import os
import sys
import urllib.parse
import urllib.request

API = ("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1"
       "&format=json&redirects=1&titles=")

# Wikipedia returns 403 to urllib's default User-Agent. Their API policy asks for a descriptive
# one naming the tool and a contact — anonymous scraping is what the block is for.
UA = "TrigunAI-qbank-corpus/1.0 (https://trigunai.com; deepak@trigunai.com)"

# The corpus directory each table module looks in. Derived from the topic name once, here, rather
# than sliced from it at two call sites — a mismatch writes the corpus somewhere the review sheet
# never reads and every row silently reports "no supporting sentence".
OUTDIR = {"economy": "/tmp/econcorpus",
          "agriculture": "/tmp/agricorpus",
          "sports": "/tmp/sportscorpus"}

PAGES = {
    "economy": ["Five-Year_Plans_of_India", "Reserve_Bank_of_India", "Planning_Commission_(India)",
                "NITI_Aayog", "State_Bank_of_India", "Life_Insurance_Corporation",
                "Nationalisation_of_banks_in_India", "NABARD",
                "Securities_and_Exchange_Board_of_India",
                "Economic_liberalisation_in_India", "Goods_and_Services_Tax_(India)",
                "Economy_of_India"],
    "agriculture": ["Green_Revolution_in_India", "Operation_Flood", "Blue_Revolution",
                    "Agriculture_in_India", "Indian_Council_of_Agricultural_Research",
                    "Indian_Agricultural_Research_Institute",
                    "National_Dairy_Research_Institute", "Central_Potato_Research_Institute",
                    "Indian_Institute_of_Horticultural_Research",
                    # Added after the first review sheet reported 8 of 16 rows unsupported: the
                    # corpus simply had no page for these institutes or for the minor revolutions.
                    # An unsupported row is not a wrong row, but it costs the reviewer the ten
                    # minutes this sheet exists to save.
                    "National_Rice_Research_Institute",
                    "Indian_Institute_of_Sugarcane_Research",
                    "Indian_Institute_of_Pulses_Research",
                    "Central_Institute_of_Fisheries_Education",
                    "List_of_revolutions_in_Indian_agriculture", "Yellow_Revolution",
                    "Silver_Revolution", "Potato"],
    "sports": ["Ranji_Trophy", "Duleep_Trophy", "Durand_Cup", "Santosh_Trophy", "Aga_Khan_Gold_Cup", "Field_hockey_in_India",
               "Thomas_Cup", "Davis_Cup", "Ryder_Cup", "Swaythling_Cup", "Ezra_Cup",
               "Eden_Gardens", "Wankhede_Stadium", "M._Chinnaswamy_Stadium",
               "Arun_Jaitley_Stadium", "Moin-ul-Haq_Stadium", "Green_Park_Stadium",
               "M._A._Chidambaram_Stadium", "Barabati_Stadium"],
}


def fetch(topic, outdir=None):
    outdir = outdir or OUTDIR[topic]
    os.makedirs(outdir, exist_ok=True)
    texts, missing = [], []
    for title in PAGES[topic]:
        url = API + urllib.parse.quote(title)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:                      # a page that will not fetch is NAMED, never
            missing.append(f"{title} ({e})")        # silently dropped — a thin corpus that looks
            continue                                # full is how a review sheet goes quiet
        for page in data.get("query", {}).get("pages", {}).values():
            extract = page.get("extract") or ""
            if extract:
                texts.append(extract)
                io.open(f"{outdir}/{title}.json", "w", encoding="utf-8").write(
                    json.dumps(data, ensure_ascii=False))
            else:
                missing.append(f"{title} (no extract)")
    path = f"{outdir}/CORPUS.txt"
    io.open(path, "w", encoding="utf-8").write("\n\n".join(texts))
    print(f"{topic}: {len(texts)}/{len(PAGES[topic])} pages, "
          f"{sum(len(t) for t in texts):,} chars -> {path}")
    if missing:
        print("  NOT FETCHED (rows touching these will show no evidence): " + "; ".join(missing))
    return path


if __name__ == "__main__":
    for t in (sys.argv[1:] or list(PAGES)):
        fetch(t)
