#!/usr/bin/env python3
"""
Lead extractor for Maya's calling campaign — pulls REAL, phone-verified coaching/tuition
business leads from the Google Places API (New) and writes a clean CSV call list.

Compliance: these are published BUSINESS numbers (owners list them to receive calls) — we CALL
them (normal conduct) and capture WhatsApp opt-in on the call. Never bulk-WhatsApp scraped numbers.

Setup:
  export GOOGLE_PLACES_API_KEY=...        # Places API (New) enabled on a Google Cloud project
  python3 lead_extractor.py               # uses built-in TARGETS
  python3 lead_extractor.py --query "NEET coaching in Kota" --out kota.csv   # single query
Output CSV columns: name, phone, segment, city, rating, reviews, address, website
Filters to small independents (reviews in [MIN_REVIEWS, MAX_REVIEWS]) with a valid phone; dedups by phone.
"""
import os, sys, csv, json, time, argparse, urllib.request, re

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ("places.displayName,places.nationalPhoneNumber,places.internationalPhoneNumber,"
          "places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri,nextPageToken")
MIN_REVIEWS, MAX_REVIEWS = 3, 400   # small independent centres (tune)

# segment -> query templates ; each expanded per city
SEGMENTS = {
    "NEET/JEE": ["NEET coaching in {c}", "IIT JEE coaching in {c}", "class 12 science tuition in {c}"],
    "Tuition":  ["tuition centre in {c}", "class 10 tuition in {c}", "home tuition classes in {c}"],
    "SSC/Bank/Rail": ["SSC coaching in {c}", "bank exam coaching in {c}", "railway exam coaching in {c}"],
}
CITIES = ["Patna", "Kota", "Delhi Mukherjee Nagar", "Prayagraj", "Lucknow",
          "Hyderabad", "Mumbai Andheri", "Pune", "Bengaluru", "Jaipur"]

def _norm_phone(nat, intl):
    raw = (intl or nat or "")
    d = re.sub(r"\D", "", raw)
    if d.startswith("91") and len(d) == 12:
        return d
    if len(d) == 10:
        return "91" + d
    if raw.startswith("+91") and len(d) >= 12:
        return d[-12:]
    return ""  # reject anything not a clean Indian mobile/landline

def search(query, page_token=None):
    body = {"textQuery": query, "pageSize": 20, "regionCode": "IN"}
    if page_token:
        body["pageToken"] = page_token
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Goog-Api-Key", API_KEY)
    req.add_header("X-Goog-FieldMask", FIELDS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def run_query(query, segment, city, seen, rows):
    token = None
    for _page in range(3):   # New API caps at ~60 results (3 pages)
        try:
            data = search(query, token)
        except Exception as e:
            print(f"  ! {query}: {str(e)[:80]}"); return
        for p in data.get("places", []):
            phone = _norm_phone(p.get("nationalPhoneNumber"), p.get("internationalPhoneNumber"))
            reviews = p.get("userRatingCount", 0) or 0
            if not phone or phone in seen:
                continue
            if not (MIN_REVIEWS <= reviews <= MAX_REVIEWS):
                continue
            seen.add(phone)
            rows.append({
                "name": (p.get("displayName") or {}).get("text", ""),
                "phone": phone, "segment": segment, "city": city,
                "rating": p.get("rating", ""), "reviews": reviews,
                "address": p.get("formattedAddress", ""), "website": p.get("websiteUri", ""),
            })
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(2)  # New API requires a brief pause before the page token is valid

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query"); ap.add_argument("--city", default="")
    ap.add_argument("--segment", default="custom")
    ap.add_argument("--out", default="leads.csv")
    args = ap.parse_args()
    if not API_KEY:
        print("ERROR: set GOOGLE_PLACES_API_KEY"); sys.exit(1)

    seen, rows = set(), []
    if args.query:
        run_query(args.query, args.segment, args.city, seen, rows)
    else:
        for seg, templates in SEGMENTS.items():
            for city in CITIES:
                for t in templates:
                    q = t.format(c=city)
                    print(f"· {seg} | {q}")
                    run_query(q, seg, city, seen, rows)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "phone", "segment", "city", "rating", "reviews", "address", "website"])
        w.writeheader(); w.writerows(rows)
    print(f"\n✅ {len(rows)} unique phone-verified leads -> {args.out}")
    # quick per-segment tally
    from collections import Counter
    for k, v in Counter(r["segment"] for r in rows).items():
        print(f"   {k}: {v}")

if __name__ == "__main__":
    main()
