# TrigunAI Google Ads Pipeline

Launch & manage Google **Search** campaigns from a single YAML spec, by CLI.
Built first for the **Acharya demand-sensor** (does anyone search for what we solve, and in which
words?), but reusable for **any** future campaign — a new campaign is just a new file in `campaigns/`.

```
google_ads_cli.py            the CLI engine (check / dry-run / launch / report / pause / enable)
campaigns/acharya_teachers.yaml   the campaign (keywords, negatives, ad copy, geo, budget) — copy to make new ones
get_refresh_token.py         one-time OAuth helper
google-ads.yaml(.example)    your API credentials (gitignored)
SETUP_CREDENTIALS.md         how to get the 5 credentials (browser steps + Google's 1–3 day token approval)
requirements.txt
```

## The idea
A campaign spec holds **all the marketing** (the buyer's pain-keywords, negative keywords to filter
job-seekers, responsive-ad copy, geo, budget, bidding). The CLI turns it into a live campaign —
**always created PAUSED**, so nothing spends until you review and enable it. `report` pulls the
numbers that answer the real question: *impressions, clicks, cost, CTR* per keyword/campaign.

## Two ways to run the ₹3k test

### A) Launch NOW via the Google Ads UI  (fastest — no API-token wait)
The Developer Token for real spend needs Google's approval (1–3 days). Don't wait on it for the
first test. Once the account + billing exist (SETUP steps 1):
1. In ads.google.com → **New Campaign → Search → "Website traffic / Leads"**.
2. Paste the assets straight from [`campaigns/acharya_teachers.yaml`](campaigns/acharya_teachers.yaml):
   budget ₹200/day, the keywords (phrase match), the negative keywords, the geo (Bihar/UP/Jharkhand),
   languages English+Hindi, and the responsive-ad headlines/descriptions. Final URL = the demo.
3. Set the end date ~2 weeks out. Launch. Check the **Search terms report** in a few days — that's
   the gold: the *actual queries* people typed to reach you (the buyer's real vocabulary).

### B) Launch by CLI  (once the Developer Token is approved — the reusable path)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

./google_ads_cli.py dry-run campaigns/acharya_teachers.yaml     # validate (no creds needed)
./google_ads_cli.py check                                        # verify creds + list accounts
./google_ads_cli.py launch campaigns/acharya_teachers.yaml --customer 1234567890   # creates it PAUSED
# review in the UI, then:
./google_ads_cli.py enable --customer 1234567890 --campaign <CAMPAIGN_ID>
./google_ads_cli.py report --customer 1234567890 --days 14       # impressions/clicks/cost/CTR
```

## What "signal" looks like (how to read the test)
- **Clicks + low CPC on a keyword** → real demand, in that word. Note which phrases won — that's the
  buyer's language; feed it into SEO, the landing, and Rohan's pitch.
- **Impressions but ~0 clicks** → people search it but your ad/offer doesn't pull → sharpen copy.
- **~0 impressions across the board** → digital search demand is thin for this category → lean back
  into the field motion; don't scale digital. (This is a *valid, valuable* answer for ₹3k.)
- **Clicks that open the demo / tap "TEACHER"** → warmest — a hand-raiser to follow up.

## Make a new campaign later
`cp campaigns/acharya_teachers.yaml campaigns/<new>.yaml`, edit keywords/copy/geo/budget,
`dry-run` it, `launch` it. Same engine, any campaign.

## Conversion tracking (do this before scaling past the sensor)
The demo launcher isn't a lead-capture page. To measure *conversions* (not just clicks), either
(a) add a Google Ads conversion tag that fires when a visitor taps a demo tile / the WhatsApp CTA,
or (b) point `final_url` at a dedicated `/teachers` landing with one CTA + the tag. Ask and I'll
build that landing page + wire the tag.
```
