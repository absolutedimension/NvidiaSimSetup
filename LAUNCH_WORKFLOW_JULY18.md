# Launch Workflow — Course 1 Ship by 18 July 2026

> **Owner:** Deepak Kumar (solo executor)
> **Start:** 5 June 2026 · **Launch:** 18 July 2026 · **Days:** 43
> **Rule:** ONE course ships. The other three are future releases.
> **Tracker:** Check boxes daily. If 3+ boxes slip in a week, trigger scope cut.

---

## The pipeline (what flows into what)

```
WEEK 1–2: DESIGN                    WEEK 3–4: PRODUCE                 WEEK 5–6: SELL + LAUNCH
┌─────────────────┐   ┌─────────────────────────┐   ┌──────────────────────┐
│ Pick course     │──▶│ Record modules (video    │──▶│ List on marketplace  │
│ Map to demand   │   │ pipeline on EC2)         │   │ Pre-enrollment push  │
│ Module breakdown│   │                          │   │ Launch July 18       │
│ Script modules  │   │ Build VR classroom       │   │                      │
│                 │   │ (simple Quest app)        │   │ First live VR class  │
│ Set up YouTube  │   │                          │   │                      │
│ Set up Udemy    │   │ YouTube teasers (2–3)    │   │ YouTube launch video │
└─────────────────┘   └─────────────────────────┘   └──────────────────────┘
```

**Three parallel tracks run the whole time:**
- **Track A — Course content** (design → script → record → edit → upload)
- **Track B — VR classroom** (design → build → test → deploy)
- **Track C — Marketing + sales** (YouTube → marketplace → pre-enrollment → launch)

---

## PHASE 1: DESIGN (June 5–18, 14 days)

### Week 1 — Pick, map, structure (June 5–11)

| Day | Date | Track | Task | Deliverable | Hours |
|-----|------|-------|------|-------------|-------|
| 1 | Thu 5 | A | **Pick ONE course.** Research: what exists on Udemy/Coursera for this topic? What's missing? What's your unique angle? | `COURSE_SELECTION.md` — which course, why, competitor gap, unique angle | 4h |
| 1 | Thu 5 | A | **Define the student.** Who are they? What job do they want? What do they already know? What will they be able to DO after the course? | Student persona + 3 concrete "after this course you can ___" outcomes | 2h |
| 2 | Fri 6 | A | **Module breakdown.** 8–10 modules. Each module: title, 1-line description, learning outcome, estimated length (15–30 min video each). | `COURSE_OUTLINE.md` — full module list with outcomes | 4h |
| 2 | Fri 6 | C | **Set up Udemy instructor account.** Understand their requirements: intro video, course image, minimum content length, pricing rules. | Udemy account created, requirements documented | 2h |
| 3 | Sat 7 | A | **Script Module 1** in full — this is also your free YouTube teaser content. Write what you'll say, what you'll show on screen, what the student builds. | Module 1 script (spoken word + screen plan) | 5h |
| 4 | Sun 8 | A | **Script Modules 2–3.** Same format. | Module 2–3 scripts | 5h |
| 5 | Mon 9 | A | **Script Modules 4–5.** | Module 4–5 scripts | 5h |
| 5 | Mon 9 | C | **YouTube channel setup** (if needed). Channel name, banner, description, first video thumbnail design. | YouTube channel ready for upload | 1h |
| 6 | Tue 10 | A | **Script Modules 6–7.** | Module 6–7 scripts | 5h |
| 7 | Wed 11 | A | **Script Modules 8–10** (or however many remain). | All module scripts complete | 5h |
| 7 | Wed 11 | B | **VR classroom design.** Sketch on paper: what does the simplest possible VR class look like? Screen share? Whiteboard? Voice only? What's the MVP? | `VR_CLASSROOM_DESIGN.md` — feature list, what's in MVP, what's post-launch | 2h |

**Week 1 gate (June 11):**
- [ ] Course selected with documented reasoning
- [ ] All modules scripted (8–10 scripts, each 15–30 min of content)
- [ ] Udemy account set up, requirements understood
- [ ] YouTube channel ready
- [ ] VR classroom MVP scoped on paper

**If you miss this gate:** You spent too long on design. Cut to 6 modules. Ship smaller, add later.

---

### Week 2 — Refine scripts + recording prep + start VR build (June 12–18)

| Day | Date | Track | Task | Deliverable | Hours |
|-----|------|-------|------|-------------|-------|
| 8 | Thu 12 | A | **Review all scripts end-to-end.** Does the course flow? Does Module 1 set up Module 2? Are there gaps? Cut anything redundant. | Revised scripts, tightened | 3h |
| 8 | Thu 12 | A | **Prepare recording environment.** Screen recording software, mic test, camera setup (if face-on-camera), slide templates if using slides. | Recording setup tested, 30-sec test clip looks/sounds good | 3h |
| 9 | Fri 13 | A | **Record Module 1.** This is your YouTube teaser AND your Udemy preview. Get it right — re-record if needed. | Module 1 raw video (15–30 min) | 4h |
| 9 | Fri 13 | A | **Edit Module 1.** Trim dead air, add any screen captures, intro/outro. Use the video pipeline if rendering 3D content. | Module 1 final video | 2h |
| 10 | Sat 14 | C | **Upload Module 1 to YouTube as free teaser.** Title, description, thumbnail, tags optimized for search. | YouTube video #1 live | 2h |
| 10 | Sat 14 | A | **Record Modules 2–3.** | Modules 2–3 raw video | 4h |
| 11 | Sun 15 | A | **Record Modules 4–5.** | Modules 4–5 raw video | 4h |
| 11 | Sun 15 | B | **VR classroom: start building.** Unity project setup, basic room, basic screen/whiteboard, voice chat. | Unity project with empty VR room | 2h |
| 12 | Mon 16 | A | **Record Modules 6–7.** | Modules 6–7 raw video | 4h |
| 12 | Mon 16 | A | **Edit Modules 2–4.** Batch edit while content is fresh. | Modules 2–4 final video | 2h |
| 13 | Tue 17 | A | **Record Modules 8–10.** | All modules recorded (raw) | 5h |
| 13 | Tue 17 | B | **VR classroom: core features.** Screen share + voice + student positions. | VR classroom with basic functionality | 3h |
| 14 | Wed 18 | A | **Edit Modules 5–10.** Marathon edit session. | All modules edited, final videos ready | 6h |

**Week 2 gate (June 18):**
- [ ] All modules recorded and edited (8–10 final videos)
- [ ] Module 1 live on YouTube with views tracking
- [ ] VR classroom MVP building in progress
- [ ] Recording quality is "good enough" — not perfect, not embarrassing

**If you miss this gate:** You're behind on recording. Options:
(a) Record remaining modules as screencasts only (faster, no face-on-cam)
(b) Cut to 6 modules, ship, add rest as "bonus modules" post-launch
(c) Push launch by 1 week to July 25

---

## PHASE 2: PRODUCE + BUILD (June 19–July 2, 14 days)

### Week 3 — Marketplace setup + VR classroom + YouTube #2 (June 19–25)

| Day | Date | Track | Task | Deliverable | Hours |
|-----|------|-------|------|-------------|-------|
| 15 | Thu 19 | C | **Create Udemy course listing.** Course title, description, what you'll learn, requirements, target audience. Upload course image. | Draft Udemy listing (not published yet) | 3h |
| 15 | Thu 19 | C | **Upload first 3 modules to Udemy.** | 3 modules on Udemy (draft) | 1h |
| 16 | Fri 20 | C | **Upload remaining modules to Udemy.** Set pricing. Write promotional copy. | All modules uploaded, pricing set | 2h |
| 16 | Fri 20 | C | **Record Udemy intro video** (required — 2 min, you talking to camera about what students learn). | Udemy intro video | 2h |
| 16 | Fri 20 | B | **VR classroom: student join flow.** How does a student get in? Link? Code? Quest app update? | Student entry flow working | 2h |
| 17 | Sat 21 | C | **YouTube video #2.** Pick the most "wow" module topic. Record a 10-min free version that ends with "full course link in description." | YouTube video #2 live | 3h |
| 17 | Sat 21 | B | **VR classroom: presentation mode.** Can you show slides/screen content in VR? Can students see what you're showing? | Presentation working in VR classroom | 3h |
| 18 | Sun 22 | B | **VR classroom: test with yourself on two devices.** One as teacher, one as student. Does it work? | Test report, bug list | 3h |
| 18 | Sun 22 | A | **Create course landing page.** Simple — can be a Notion page, a Carrd site, or trigunai.com. Course description, price, enroll button. | Landing page live with CTA | 3h |
| 19 | Mon 23 | C | **Submit Udemy course for review.** Udemy takes 2–5 business days to review. Submit NOW to have buffer. | Udemy submission confirmed | 1h |
| 19 | Mon 23 | B | **VR classroom: fix bugs from test.** | Bugs fixed | 3h |
| 19 | Mon 23 | C | **Student acquisition research.** Where do your target students hang out? Reddit subs, Discord servers, LinkedIn groups, Telegram groups, college forums? Make a list of 10 communities. | `STUDENT_CHANNELS.md` — 10 communities with posting plan | 2h |
| 20 | Tue 24 | B | **VR classroom: polish + Quest build.** | APK or App Lab build ready | 4h |
| 20 | Tue 24 | C | **Write 3 community posts** (don't post yet — save for pre-enrollment week). Value-first posts, not "buy my course." Each teaches something from the course, ends with "I'm launching a full course on this July 18." | 3 draft posts | 2h |
| 21 | Wed 25 | B | **VR classroom: test with 1 real person** (friend, Avinash, anyone). Live class simulation — 15 min. | Test passed or bug list | 3h |
| 21 | Wed 25 | C | **Course promo assets.** Thumbnail variations, social media graphics, 30-sec video teaser for Instagram/LinkedIn. | Asset folder with 5+ promo images/clips | 2h |

**Week 3 gate (June 25):**
- [ ] Course submitted to Udemy for review
- [ ] Landing page live with working payment/enrollment link
- [ ] YouTube video #2 live
- [ ] VR classroom tested with at least 1 other person
- [ ] 10 student communities identified
- [ ] 3 community posts drafted

---

### Week 4 — Pre-enrollment opens + marketing push (June 26–July 2)

| Day | Date | Track | Task | Deliverable | Hours |
|-----|------|-------|------|-------------|-------|
| 22 | Thu 26 | C | **Open pre-enrollment.** Early bird discount (20–30% off). Share on personal social media. | Pre-enrollment live, first shares posted | 2h |
| 22 | Thu 26 | C | **Post in 3 communities** (the drafted posts from Week 3). | 3 community posts live | 2h |
| 22 | Thu 26 | A | **Record any bonus/supplementary content.** Q&A video, "common mistakes" video, resource list. | 1–2 bonus videos | 3h |
| 23 | Fri 27 | C | **Post in 3 more communities.** Different angle per community. | 6 total community posts | 2h |
| 23 | Fri 27 | C | **LinkedIn post:** personal story + course announcement. "I built a VR app from zero to Meta alpha. Now I'm teaching how. Launching July 18." | LinkedIn post live | 1h |
| 23 | Fri 27 | B | **VR classroom: final polish.** Fix anything from Week 3 test. | VR classroom release-ready | 3h |
| 24 | Sat 28 | C | **YouTube video #3.** "5 things I wish I knew before building my first [robot/ML model/AI agent/VR app]." Soft pitch at the end. | YouTube video #3 live | 3h |
| 24 | Sat 28 | C | **Check Udemy review status.** If rejected, fix issues and resubmit same day. | Udemy status: approved or resubmitted | 1h |
| 25 | Sun 29 | C | **Post in remaining 4 communities.** | All 10 communities reached | 2h |
| 25 | Sun 29 | C | **Email outreach** (if you have any email list, college contacts, LinkedIn connections in the target space). Personal, not spammy. | 20+ personal emails/DMs sent | 3h |
| 26 | Mon 30 | C | **Check pre-enrollment numbers.** How many? Where did they come from? Double down on what's working. | Pre-enrollment count + source analysis | 1h |
| 26 | Mon 30 | C | **Respond to all comments/questions** on YouTube, community posts, DMs. Every response is a potential student. | All engagement responded to | 2h |
| 27 | Tue 1 Jul | C | **Second wave of community posts.** New angle: "Behind the scenes of building this course" or "Student question I got" (even if from friends). | 3 new posts | 2h |
| 28 | Wed 2 Jul | — | **MID-POINT REVIEW (Day 28 of 43).** Count: pre-enrollments, YouTube views, community engagement, Udemy status. Honest assessment. | `MIDPOINT_REVIEW.md` | 2h |

**Week 4 gate (July 2) — CRITICAL DECISION POINT:**
- [ ] Pre-enrollment count: _____ (target: ≥3)
- [ ] Udemy status: approved / pending / rejected
- [ ] YouTube total views across 3 videos: _____
- [ ] VR classroom: release-ready
- [ ] Community engagement: any DMs asking about the course?

**Decision rules:**
- **≥3 pre-enrollments** → full speed ahead, launch July 18
- **1–2 pre-enrollments** → launch July 18 but adjust: lower price? different marketing angle? different communities?
- **0 pre-enrollments** → **STOP.** Something fundamental isn't working. Diagnose before spending 2 more weeks. Is it the topic? The price? The marketing? The audience? Talk to 5 people who DIDN'T enroll and ask why.

---

## PHASE 3: LAUNCH (July 3–18, 16 days)

### Week 5 — Final push + pre-launch (July 3–9)

| Day | Date | Track | Task | Hours |
|-----|------|-------|------|-------|
| 29 | Thu 3 | A | Final QA: watch every module end-to-end. Fix audio issues, re-record any weak sections. | 4h |
| 30 | Fri 4 | C | YouTube video #4: "What you'll build in this course" — show the final project/outcome. Strong CTA. | 3h |
| 31 | Sat 5 | C | Pre-enrollment reminder push. "7 days left for early bird pricing." Post everywhere again. | 3h |
| 32 | Sun 6 | B | VR classroom: dry run of the FIRST live class (Module 1). Practice teaching in VR. Time it. | 3h |
| 33 | Mon 7 | C | **Schedule the first live VR class.** Pick a date (July 19 or 20 — right after launch). Announce it. "Enroll by July 18, join the first-ever live VR class on July 19." | 2h |
| 34 | Tue 8 | C | Personal outreach round 2. DM everyone who liked/commented on your posts. "Hey, the course launches in 10 days — here's what you'd get." | 3h |
| 35 | Wed 9 | C | **Pre-enrollment count check.** This is your July 10 early warning. | 1h |

**Week 5 gate (July 9):**
- [ ] All content finalized and uploaded
- [ ] First live VR class date announced
- [ ] Pre-enrollment count: _____ (target: ≥5 by July 10)
- [ ] If 0 pre-enrollments: execute the stop condition (see Week 4 decision rules)

---

### Week 6 — LAUNCH WEEK (July 10–18)

| Day | Date | Task | Hours |
|-----|------|------|-------|
| 36 | Thu 10 | "Last chance for early bird" push. Check Udemy is live. Update landing page with final details. | 3h |
| 37 | Fri 11 | **YouTube video #5: launch countdown.** "Launching in 1 week. Here's everything inside." Full walkthrough of what students get. | 3h |
| 38 | Sat 12 | Prep launch-day social media posts (schedule them). Draft launch email if you have a list. | 2h |
| 39 | Sun 13 | Rest day. Seriously. You've been going for 5 weeks straight. | 0h |
| 40 | Mon 14 | Final check: all marketplace listings live, VR classroom APK ready, landing page working, payment flow tested. | 3h |
| 41 | Tue 15 | "3 days to launch" teaser. Share a student testimonial if any beta testers gave feedback. | 2h |
| 42 | Wed 16 | Final prep. Test the entire student journey: find course → enroll → access content → join VR classroom. | 3h |
| 43 | Thu 17 | **Pre-launch night.** Everything ready. Schedule the launch posts for tomorrow morning. | 1h |
| **44** | **Fri 18** | **LAUNCH DAY.** Post everywhere. Udemy goes from pre-order to live. Landing page says "Enroll now." YouTube launch video goes live. | 4h |

**Post-launch (July 19–20):**
- [ ] **First live VR class** (July 19 or 20). Even if only 3 students, do it. Record it for testimonials.
- [ ] Respond to EVERY student message, question, review within 24h.
- [ ] Collect feedback: what worked? what confused students? what do they want more of?

---

## LAUNCH DAY CHECKLIST (July 18)

- [ ] Udemy course: live, all modules accessible, pricing correct
- [ ] Landing page: live, enroll button works, payment processes
- [ ] YouTube: launch video posted with course link in description
- [ ] LinkedIn: launch post with personal story
- [ ] All 10 communities: launch announcement posted
- [ ] Instagram/Twitter: launch posts
- [ ] Personal DMs to everyone who engaged during pre-launch
- [ ] VR classroom: APK available for enrolled students
- [ ] First live VR class: date announced, calendar invite sent to enrolled students
- [ ] Email to all pre-enrolled students: "We're live! Here's how to access everything."

---

## BUDGET

| Item | Cost | When |
|---|---|---|
| Course design + scripting | $0 | Weeks 1–2 |
| Screen recording software (OBS) | $0 (free) | Week 2 |
| EC2 for video rendering (if using 3D pipeline) | ~$5–15 | Weeks 2–3 |
| Udemy instructor account | $0 | Week 1 |
| YouTube channel | $0 | Week 1 |
| Landing page (Carrd / Notion) | $0–$9/mo | Week 3 |
| Canva for thumbnails/graphics | $0 (free tier) | Throughout |
| Domain (if using trigunai.com) | Already owned | — |
| Quest developer account (for VR classroom) | Already have | — |
| **Total pre-launch spend** | **~$10–25** | |

---

## WHAT YOU ARE NOT DOING (scope fence)

These are all good ideas. None of them ship by July 18. Do them AFTER launch.

- [ ] ~~Design courses 2, 3, and 4~~ → After Course 1 has ≥10 paying students
- [ ] ~~Build a full VR learning management system~~ → Simple classroom first
- [ ] ~~Create a mobile app~~ → Web + Quest only for launch
- [ ] ~~Set up cert partnerships~~ → After Course 1 proves demand
- [ ] ~~Improve the drone cinematography pipeline~~ → It works. Use it, don't polish it.
- [ ] ~~Rewrite trigunai.com / studio.trigunai.com~~ → Landing page is enough
- [ ] ~~Apply for grants~~ → After launch, when you have real metrics to cite
- [ ] ~~Build an offline student program~~ → Online first, offline after traction
- [ ] ~~Record all 4 courses~~ → ONE course. Ship it. Learn. Then the next.

---

## DAILY RHYTHM (for solo execution)

| Time | Activity |
|---|---|
| **Morning (2h)** | Marketing/community — posts, responses, YouTube, pre-enrollment tracking |
| **Midday (4–5h)** | Core production — course scripting, recording, editing, OR VR classroom building |
| **Evening (1–2h)** | Admin — Udemy, landing page, grant paperwork in gaps |
| **Night** | Sleep. Not optional. Solo founder burnout kills more startups than bad products. |

**Weekly cadence:**
- **Monday:** Review last week's numbers (views, enrollments, engagement). Plan this week.
- **Tuesday–Friday:** Produce. Record, edit, build.
- **Saturday:** Marketing push + one YouTube video.
- **Sunday:** Light work or rest. Respond to comments. Plan the week ahead.

---

## SUCCESS METRICS

| Metric | Pre-launch target (by July 10) | Launch target (July 18) | 30-day target (Aug 18) |
|---|---|---|---|
| Pre-enrollments | ≥5 | — | — |
| Paying students | — | ≥5 | ≥25 |
| YouTube subscribers | ≥50 | ≥100 | ≥500 |
| YouTube views (total) | ≥500 | ≥2000 | ≥10000 |
| Udemy rating | — | — | ≥4.0 stars |
| VR live class attendees | — | ≥3 (first class) | ≥10/class |
| Revenue | ₹0 | ≥₹5,000 | ≥₹25,000 |

These are not predictions. They are the minimum signals that say "this is working, keep going."
Below these numbers = diagnose and adjust, not push harder on the same plan.

---

*Created 5 June 2026 · Deepak Kumar · Solo execution · One course, ship it, learn, repeat.*
