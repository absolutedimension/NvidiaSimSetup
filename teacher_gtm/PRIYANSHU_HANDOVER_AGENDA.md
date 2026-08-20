# Priyanshu handover — Deepak's session script

> **For Deepak, not for Priyanshu.** This is how you run the transfer session so he walks out able
> to work alone. Budget **2.5 hours**, in one sitting, ideally on a video call where he can share
> his screen.
>
> **The goal of the session is not to explain the product.** The kit explains the product. The goal
> is that **he runs a full demo himself, in front of you, and you correct it** — because that is the
> only part that cannot be transferred by document.

---

## Before the session (your prep — 20 min)

- [ ] Compensation is **settled** — same as Rohan (§7). Have the four numbers in front of you; a
      senior hire asks in the first ten minutes and hesitating there costs you authority for the
      rest of the relationship.
- [ ] Confirm the demo works **today**: generate a TRE paper and an SSC paper yourself
- [ ] Have his kit ready to send (see §6 for the delivery command)
- [ ] Decide what you are **not** giving him yet — Gurukul VM SSH, Maya calling. ⚠️ Recommendation:
      **withhold both for now.** He doesn't need them for the field motion, and the VM runs live
      students. Give access when he has a team that needs it.

---

## §1 · Why you (10 min) — set the altitude first

He is senior and he is heading a region. **Do not open with a product tour** — open with the
position, or he will size the role as "field boy for Ara" and behave accordingly.

Say, in your own words:

- Ara is **his** — the list, the team, the number. You are his escalation, not his supervisor.
- Rohan works Patna as a field caller. **Priyanshu operates a level above that**: he will build and
  run people.
- Be straight about the stage: *we have built a lot and sold very little. The engineering is done.
  What has never been tested is whether institutes will install it and pay.* **That is the job.**
- What you will judge in 15 days: **one batch live with students actually taking tests.** Not visits.

**Why say the honest version:** a senior person who discovers the real situation later feels sold to.
One who is told up front that he is the missing piece tends to own it.

---

## §2 · The product — let him find it, don't present it (30 min)

**Do not screen-share a tour.** Have *him* share *his* screen and drive:

1. He opens `acharya.trigunai.com/exam-prep` on his own phone
2. **He** picks the exam, **he** picks TRE, **he** picks a chapter
3. He generates the paper. You stay quiet and watch his face.
4. He does it again for SSC, and once for Class 10
5. He sets up white-label branding at `/teacher/branding` with a dummy institute name
6. **He prints one paper.** That printed sheet is what Ara actually buys.

Then say the sentence he must be able to repeat cold:

> *"Ye AI ka banaya hua nahi hai. Ye ASLI past-paper ke asli questions hain — asli answer key ke
> saath. Do hazaar se zyada TRE questions."*

**Also show him what's broken.** The ~78 mixed-bucket GS questions, no fee collection, no attendance.
A partner who learns the flaws from you trusts everything else you said. One who discovers them in
front of an owner stops trusting the kit.

---

## §3 · The Ara thesis (20 min) — the part he must argue back at you

This is the section where his knowledge should beat yours. Put the thesis up and **ask him to
disagree**:

- **Ara is a govt-exam town** — TRE / SSC / Railway / Daroga / BSSC / Bihar Board — not JEE-NEET.
  Our deepest bank (2,026 real TRE questions) is exactly what the town studies for. **Is that right?**
- **The "students leave for Patna" wedge** — the owner can't compete on faculty or building, but he
  can compete on weekly tests with real past-paper questions under his own name. **Does that land
  in Ara?**
- **Ara is an on-foot market.** Our Play Store sweep — the best lead source in Patna — found only
  **two** real institutes with apps: PANDEY CLASSES ARA and Physics World Ara. **Does that match
  what he knows?**
- The ⚠️ cluster table in `02_ARA_MARKET_BRIEF.md` §4 is your guess. **Have him correct it live,
  in the file, during the session.**

**Why this matters:** the moment he corrects your document is the moment he owns the region instead
of executing your plan. Make it happen in the session, deliberately.

---

## §4 · He runs the demo at you (40 min) — the core of the session

**This is the part that cannot be transferred by document. Do not cut it for time.**

You play the institute owner. Run it three times:

| Round | You play | Watch for |
|---|---|---|
| **1** | A friendly TRE-coaching owner | Does he do **discovery first**, or jump to the product? Does he hand over the phone? |
| **2** | A skeptic — *"AI se padhai nahi hoti"*, *"per student kitna?"* | Does he **agree first, then reframe**? Does he quote ₹150/₹250 flat correctly? |
| **3** | A busy owner — *"do minute hai"* | Can he compress to 90 seconds and still get the pilot ask out? |

**Correct only three things.** More than that and nothing sticks. The three that matter most:

1. **He must stop talking after handing over the phone.** Almost everyone narrates over it.
2. **He must let the owner choose the chapter.** A demo he drives is a video; one the owner drives is
   his product.
3. **He must never end with *"kaisa laga?"*** — always *"chaliye ek batch pe laga dete hain."*

Then have him say the four capture items from memory: **batch size · exam · start date · who runs it
daily.**

---

## §5 · Rules, escalation, and the first 15 days (20 min)

- Walk `10_RULES_AND_ESCALATION.md` — the honesty rules and no-cash rule out loud, not by reference.
  ⚠️ Be explicit that **the ₹55,000 white-label charge is dead** — it is still in older PDFs and he
  will find it.
- Agree what he reports and when: **weekly number, immediate escalation on a ready buyer or a broken
  demo.**
- Walk `09_FIRST_15_DAYS.md` and agree the day-15 checkpoint date out loud.
- **Team: not yet.** Say plainly that hiring starts only after his own first pilot is live, and why
  — he cannot train a motion he hasn't run. He is senior; give him the reason, not the rule.

---

## §6 · Deliver the kit (10 min, do it while he's on the call)

Have him install it and confirm it works before you hang up.

**Stage it on the Gurukul VM dropbox:**
```bash
scp -i ~/.ssh/gurukul_key -r skills/ara-region-head dk_trigun@20.219.2.53:~/skill_dropbox/
```

**He pulls it** (needs a key — mint one with the `transfer-caller-role` skill, or send the folder
directly over WhatsApp/Drive as a zip if you're not giving him VM access yet):
```bash
scp -r -i ~/.ssh/priyanshu_gurukul_key dk_trigun@20.219.2.53:~/skill_dropbox/ara-region-head ~/.claude/skills/
```

Then he restarts Claude Code and says **"start my day"**. Confirm it responds before you end the
call.

⚠️ **Updates use the same channel** — you re-scp to `~/skill_dropbox/`, he re-pulls. His Claude
does **not** sync automatically; skills are local files.

---

## §7 · Compensation — SETTLED (2026-08-18): same as Rohan

Both his package and his hiring budget mirror the Patna field role, so the two regions stay
comparable. Written into his kit at `11_YOUR_TERMS.md` and `08_TEAM_BUILD_PLAYBOOK.md` §4.

| Component | Amount |
|---|---|
| Fixed | **₹10,000 / month** |
| Per verified, logged visit | **₹200** (cap 25/month → max ₹5,000) |
| Per converted visit — a batch goes live | **₹500** |
| Per first payment received by TrigunAI | **₹1,100** |

No cash handling; payments go only to the official link. **Send these to him in writing after the
session** — the kit states them, but a senior hire should have them from you directly.

**Say the two rules out loud in the session,** because they're what make the numbers work:
paid against **verified logs only**, and the bonus sits on **batches live, not owner interest.**

### ⚠️ Two things to watch (not blockers — just be aware)

1. **The visit fee and the head role pull against each other.** Paying Priyanshu ₹200 per *his own*
   visit rewards him for staying in the field rather than building the team you hired him to build.
   It's fine while he's solo — it's exactly right for the first 15 days. **Revisit it at the day-15
   checkpoint**, once he has someone under him.
2. **Cost stacks per head.** Each hire is ₹10k fixed + up to ₹5k visits before any conversion, so a
   two-person Ara team is ~₹45k/month at full visit cap. Worth knowing the number before he brings
   you a hire to approve.

### Separately — retire the stale partner doc

`ACHARYA_PARTNER_PROGRAM.md` still describes wholesale at ₹80/₹150 per student **plus ₹30,000 per
institute and a ₹15,000/mo minimum** — economics built on the dead ₹55k model. Against today's flat
₹150/₹250 those numbers no longer work. Re-cut or retire it before someone quotes it to an owner.
Priyanshu's kit already routes any reseller question straight to you (`05_PRICING_AND_OFFER.md` §6).

---

## After the session — same day

- [ ] Send the compensation terms **in writing** (WhatsApp is fine; writing is the point)
- [ ] Put the day-15 checkpoint in your calendar
- [ ] Tell Rohan that Ara now has an owner, so the two of them don't collide on a border institute
- [ ] Visiting card: he asked for one. Not needed for day 1 — get his title fixed first
      (**"Regional Head — Ara & Bhojpur, TrigunAI Innovations"** or **"Marketing Partner"**), then
      print. A card with the wrong title is worse than no card.
