# 03 · Building the Ara list — where the institutes are

> Companion to `ara_institutes.csv` (your working list) and `02_ARA_MARKET_BRIEF.md` (why Ara is
> different). **In Ara, the list is built on foot and on Maps — not by a scraper.** That is the
> whole point of hiring someone who lives there.

---

## The one rule that shapes everything

**Never cold-WhatsApp a number you scraped.** Businesses publish phone numbers to receive **calls** —
so you call, or you walk in. You get the WhatsApp opt-in **in the room or on the call**, from the
owner's own mouth.

Bulk WhatsApp to scraped numbers gets our business number blocked, and that number also serves live
students and Rohan's Patna work. One shortcut here damages everyone. No exceptions.

---

## A. Google Maps — your primary desk source (do this tonight, before any visit)

This is 80% of your list and costs you two evenings.

Search per locality, in Hindi and English, and work each result:

```
coaching Ara Bihar          BPSC coaching Ara           SSC coaching Ara
railway coaching Ara        daroga coaching Ara         BSSC coaching Ara
tuition Ara Bhojpur         class 10 tuition Ara        class 12 coaching Ara
कोचिंग आरा                  competitive exam coaching Arrah
coaching Gopali Chowk       coaching Station Road Ara   coaching Shiv Ganj Ara
```

⚠️ **Search "Arrah" as well as "Ara"** — Maps listings use both spellings, and you will miss half
the town if you only use one.

For each listing capture into the CSV: **name · area · phone · what they teach · review count**.

**Review count is your size proxy.** More reviews ≈ more students. But **pick the small and mid
ones** — a 500-review chain has no local decision-maker; a 15-review owner-run centre will decide in
front of you.

**Read the reviews themselves.** Complaints about study material, papers, or tests are pure gold —
that is a public, timestamped, named pain you can open the conversation with.

---

## B. On foot — the part only you can do

In a town like Ara **the signboards are the directory.** Walk one cluster per evening with your
phone:

- Photograph every coaching signboard: name + phone + what it teaches
- Note whether the shutter is up and students are actually going in — a board on a wall is not an
  institute
- Coaching centres cluster around **colleges, the station, and the main chowks** — walk those first
- Add each to the CSV that same night. A photo you never transcribe is not a lead.

**Look for the small ones above shops and in lanes.** Those are owner-run, decide instantly, and are
invisible to every competitor selling into Ara from a Patna office.

---

## C. Your own network — your genuine edge

You live there. This is the thing Rohan cannot do in Patna and no scraper can do anywhere.

- Teachers you already know; teachers your family knows
- Your own former coaching centre, your school, your college
- Photocopy / printing shops near the colleges — **they print everyone's test papers.** The owner of
  a printing shop knows exactly which institute runs tests, how often, and how thick the papers are.
  ⚠️ Untested idea, but if it works it is the single best-informed source in town — try one, and
  tell Deepak what happened.
- Book shops selling guidebooks — they know who buys question banks in bulk

**A warm introduction converts several times better than a cold knock.** Spend your first week's
evenings on this, not on the internet.

---

## D. The two institutes we already found (start here)

From the 2026-08-18 Play Store sweep — these two have **already paid for software**, which makes
them pre-qualified on budget and on willingness to buy. Get their number from Google Maps or their
own site (the app listing gives only the vendor's contact, never theirs).

| Institute | Signal | Why they matter |
|---|---|---|
| **PANDEY CLASSES ARA** | Classplus app, 45 reviews, maths-heavy; reviews praise step-by-step solutions | Already pays for a platform whose test module ships **empty**. That is our exact pitch. |
| **Physics World Ara** | Self-built app, 52 reviews, Physics 11/12 | Built their own app → unusually tech-forward owner for Ara. |

Raw sweep output with the verbatim review quotes: `ara_playstore_leads.csv`.

---

## E. Other directories — worth one evening, not more

- **Justdial / Sulekha**, filtered to Ara / Arrah — coaching categories, numbers visible
- **Facebook** — "Ara coaching", "Arrah tuition", local coaching-owner groups. ⚠️ Facebook is
  genuinely strong in small-town Bihar; worth a proper look
- **YouTube** — many small-town teachers run local channels. A teacher with 5k local subscribers has
  a real batch and a real ego about his content. Good lead, good conversation.

---

## F. Do NOT waste time on

- Big national chains — no local buying authority
- Paid-lead sites (UrbanPro / TeacherOn) — gated, low quality, and their student leads are often fake
- Bulk WhatsApp to scraped numbers — see the rule at the top
- **The Play Store sweep for Ara.** It works for Patna; it does not work here. We already ran it and
  it returned mostly false matches on the letters "ara". Don't re-run it hoping for more.

---

## G. How a name moves through the pipeline

```
add to CSV → call ahead (or just walk in) → VISIT → discovery → demo
   → free pilot agreed → pilot LIVE on a batch → students take a test → FIRST PAID
```

Update `precall` / `visit_status` / `pilot_status` / `pain_notes` as it moves. **Same day.**

The `pain_notes` column is the most valuable column in the file. Verbatim quotes, not summaries.
*"Har Sunday raat 11 baje tak paper banata hoon"* is worth more than *"finds paper-making hard"* —
the first one tells Deepak what to build and gives you a line to use on the next owner.

---

*Created 2026-08-18 for the Ara push. **Update this file as you learn which clusters convert** — it
is yours to correct, and the corrected version is what your team will be trained on.*
