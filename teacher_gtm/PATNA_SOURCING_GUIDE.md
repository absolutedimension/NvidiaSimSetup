# Patna — where to find the institutes (Rohan's sourcing guide)

> Field-first playbook for building and working the Patna shortlist. Companion to
> `patna_institutes.csv` (the working list) and `PATNA_FIELD_STRATEGY_2026-07.md` (the why).
> National channel map (all cities) is `06_SOURCING_CHANNELS.md` — this doc is Patna + on-foot.

## The rule that shapes everything (don't break it)
**Never cold-WhatsApp a scraped number.** Businesses publish numbers to receive **calls** — so
Maya calls first (that's normal conduct), or you walk in. Get the WhatsApp opt-in *on the call or in
the room*. Bulk WhatsApp to scraped numbers risks our business number. (Same rule as the national doc.)

---

## A. The Patna coaching clusters — walk these, don't drive across town
Density is the whole point: pick ONE cluster per day so you visit 3–4 offices in one trip.

| Cluster | What's there | Notes |
|---|---|---|
| **Musallahpur Hat / Bhikhna Pahari** | THE Patna coaching bazaar — highest density of exam-prep centres | Best for on-foot cold visits; dozens of small boards/NEET/JEE/SSC centres in walking distance |
| **Boring Road / Rajapul** | Mid-premium tuition + spoken English + CA/commerce | Owners more digital-savvy; good for the Acharya pitch |
| **Kankarbagh** | Huge residential + coaching belt (Bank/SSC/board tuition) | Large addressable pool; many owner-run centres (owner = decision maker = ideal) |
| **Rajendra Nagar / Kadamkuan** | Established tuition names, board + competitive | Relationship market — a warm referral opens doors |
| **Patliputra / Bailey Road** | Newer / premium centres | Fewer but higher willingness-to-pay |
| **Ashok Rajpath / Machua Toli** (near Patna University) | Student-dense, graduate tutors, competitive exams | Younger owners, price-sensitive |

> **ICP reminder:** small, **owner-run** centres of ~10–200 students (owner is the decision maker,
> answers on the spot). Skip the big chains (Aakash, Allen, PW, FIITJEE, Goal) — no local authority to buy.

## B. Desk research to BUILD the list (do this to add names to the CSV)
1. **Google Maps** (best) — search per cluster: `"coaching Kankarbagh Patna"`, `"NEET coaching
   Boring Road"`, `"tuition Musallahpur"`, `"SSC coaching Patna"`, `"class 12 tuition Rajendra
   Nagar"`. Each listing = name, phone, address, review count (reviews ≈ student volume → pick the
   small ones). Copy name/phone/area into the CSV.
2. **Justdial Patna** — coaching categories (NEET / IIT-JEE / SSC / Banking / spoken English) filtered
   to Patna. Phone numbers reachable.
3. **Sulekha** — entrance-exam coaching, Patna filter. Numbers + addresses visible.
4. **Facebook** — search "Patna coaching", "Patna tuition teachers"; local coaching-owner groups.
5. **On foot** — in Musallahpur/Bhikhna Pahari the boards ARE the directory. Photograph the
   signboard (name + phone), add to CSV, then Maya pre-calls or you walk in.

## C. The flow for each institute (how a name moves through the pipeline)
```
add to CSV  →  Maya pre-call (warm + confirm visit)  →  VISIT (or call if far)
   →  discovery + demo  →  free pilot agreed  →  pilot live on their subject  →  first paid
```
Update the row's `maya_precall` / `visit_status` / `pilot_status` / `pain_notes` as it moves.
Same-day. The `pain_notes` column is gold — it's the pain-point map that tells us what to build.

## D. Already-warm Patna leads (start here — Maya already got a yes-to-demo)
From `leads/MAYA_ACCEPTED_25_2026-07-12.csv`, these Patna institutes already accepted a demo — they
are your **Week-1 first visits**:
- **MCM IIT-JEE & NEET Academy** — 917992250244 — WARM, call/visit FIRST.
- **Base Point** (NEET) — 917979919133 — same-city, batch with MCM.
- **Delta Success Point** (exam prep) — 917903454942.

Seeded into `patna_institutes.csv` with `maya_precall=accepted`. Add the cluster/area for each after
your first look (Maps or a call).

## E. Do NOT waste time on
- Big national chains (no local buying authority).
- UrbanPro/TeacherOn paid-lead gating; fake student leads (ToS violation, burns trust).
- Bulk WhatsApp to scraped numbers (policy + our number at risk).

---

## F. Play Store sweep — the highest-quality source (automated, 2026-08-17)

**`playstore_lead_sweep.py`** — run it for any city. An institute with its own branded app has
already bought a white-label platform (Classplus yr-1 ≈ ₹4–11 lakh), so the owner is
pre-qualified on **budget** *and* **willingness to buy software** — and those platforms hand
them a test-creation tool with **no questions in it**. That empty test module is our pitch.

```bash
python3 playstore_lead_sweep.py --city Patna --strict-city
python3 playstore_lead_sweep.py --city Muzaffarpur --vendor "Education Mobile Media"
```

It searches Play, resolves each app's real title + white-label vendor, fingerprints the platform
from the package id (`co.<word>.<rand>` = Classplus), pulls reviews through Play's own reviews
RPC, mines them for **verbatim test/paper complaints**, ranks, and writes rows in this repo's
`patna_institutes.csv` schema.

**Two hard limits — respect both:**
1. **It cannot give you a phone number.** The Play listing's developer contact is the *vendor's*
   (`psupdates@classplus.co`), never the institute's. Get the number from the institute's own
   site or public listing — which is also what keeps us inside the §D consent rule.
2. **It is weak on city.** Play search leaks nationally. Read the `CITY?` column: `title` is
   trustworthy, `reviews` is decent, **`reviews?` and `UNVERIFIED` are not leads yet**. Use
   `--strict-city` when the city name is also a common word — a Gaya sweep ranked *Lakshya
   Classes Udaipur* first, because "gaya" is Hindi for "went". **Confirm on Maps before travel.**

Proven: `--strict-city --city Patna` reproduces the hand-built Day 3 leads, ranking Achievers IAS
top off its own 1-star review *"Nothing inside coarse material"*. Gaya output sits in
`gaya_playstore_leads.csv` (needs the Maps pass before anyone visits).

*Built 2026-07-16 for the Patna field push. §F added 2026-08-17. Update as you learn which clusters convert.*
