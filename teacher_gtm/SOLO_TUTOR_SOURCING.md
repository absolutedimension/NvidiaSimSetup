# Solo Tutors — build the first authentic list (no scraping, no fake numbers)

> Companion to `solo_tutors.csv` (the working list). Same compliance rule as the institute guide:
> **numbers come only from public self-published listings, Maya calls FIRST, WhatsApp opt-in is taken
> on the call.** Target = **owner-run micro-tuitions & home tutors** where the person teaching is the
> one who can say yes. This is the "buyer in the room" reframe, done digitally.

## The one rule (don't break it)
A tutor publishes a number to receive **calls about tutoring** — that's the consented use. So:
1. **Maya calls first** (normal conduct) → warms + qualifies → asks "can I WhatsApp you the free link?"
2. Only after **opted-in** do we WhatsApp. Bulk-WhatsApping raw scraped numbers = DPDP risk + gets our
   business number banned. Never do it.
3. **Never invent a number.** An empty cell is fine; a wrong number messages a random citizen.

## ICP for this list
Small, **owner-run** — the tutor teaches AND decides. ~10–100 students. Skip anything with a front
desk or multiple branches (that's the slow institute motion we're moving away from).

---

## A. Build 50–80 real rows — the live queries (30–45 min, human pass)

### 1. Google Maps (best — public business phone + review count = size signal)
Search each, per Patna cluster. Small review count = small tutor = ideal. Copy name + phone + area:
- `home tutor Kankarbagh Patna`
- `tuition classes Boring Road Patna`
- `NEET home tuition Patna`
- `class 12 maths tutor Rajendra Nagar Patna`
- `commerce tuition Patna`
- `spoken english tutor Patna`
- (repeat for clusters in `PATNA_SOURCING_GUIDE.md §A`: Musallahpur, Kankarbagh, Boring Road,
  Rajendra Nagar, Bailey Road, Ashok Rajpath)

### 2. Justdial / Sulekha / UrbanPro — "Tutors" category, Patna
Owner-run tuition listings with a visible number. Note: UrbanPro often gates the number — take only
what's genuinely visible; don't pay-to-unlock for a cold list at this stage.

### 3. YouTube — small subject tutors (About tab → business email)
Search `Patna JEE tutor`, `NEET biology tutor Hindi`, `class 10 maths Patna`. Channels with a few
thousand subs and an email in About *want* to be contacted. Email, don't WhatsApp.

### 4. Facebook / Telegram groups where tutors self-post
`Patna tuition teachers`, `Patna coaching`, home-tutor groups. When a tutor posts their OWN number
offering classes → that's self-published + contextual. Add with source=`fb-group`/`telegram`.

### 5. Referral (highest priority — always warmest)
Any tutor a current contact/student names → priority `1-warm`, skip the cold step.

> **Quality > quantity.** 60 genuinely-verified owner-run tutors beat 6,000 scraped. Stop at ~80.

---

## B. Work the list (the funnel — no personal meetings)
1. **Maya pre-call** (Twilio, Hindi/EN) → 30-sec pitch → "shall I WhatsApp you the free link?" →
   set `maya_precall=done`, `optin_status=opted-in`.
2. **WhatsApp the opted-in** with the copy below → they land on **`gurukul.trigunai.com/start`**
   (self-serve, no meeting) → `pay_status=free-active` once they create a test.
3. **Pay trigger** when they want the batch weak-topic dashboard / branded papers → `pay_status=paid`.

## C. The WhatsApp opt-in copy (only after Maya opt-in)
> Namaste [name] ji 🙏 — Acharya se. Aap apne students ke liye **real JEE/NEET/board test papers
> 30 second me bana ke share kar sakte hain — bilkul free**. Apni class ki weak-topic report chahiye?
> Yahan se shuru karein 👉 gurukul.trigunai.com/start

Free hook (create + share papers) that needs **zero meeting**; the paid reason (batch dashboard /
branded papers) is the upsell. Matches the pay-to-unlock line from the strategy call.

## D. What "done" looks like for v1
- 50–80 real rows in `solo_tutors.csv`, source-tagged, **no fabricated numbers**.
- Maya has pre-called the top 20; ≥10 opted-in; WhatsApp sent to those.
- ≥1 tutor `free-active` on `/start`. That's the signal the lane is real → then scale via inbound ads.
