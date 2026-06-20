---
title: "Module 11 — Ship to Meta's Store"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_11_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, your app will be on its way to the Meta Store,
  where anyone in the world can find it, download it, and put it on their headset.
  This is the step almost no course teaches, and it is the one that matters most.
  An app on your computer is a project. An app in the store is a product.
on_screen:
  title: Ship to Meta's Store
  subtitle: Module 11
  body: Put your app where the world can download it
  layout: center
visual: an app icon lifts off a laptop and lands in a glowing store listing
duration_hint_sec: 22

### scene_02_why
narration: |
  Let us be honest about why this module matters so much.
  Most people who learn VR development never ship anything. They build demos that sit on a hard drive.
  Shipping is hard in a different way than coding. It is paperwork, packaging, and patience.
  But a shipped app, even a small one, is worth more than ten unfinished masterpieces.
  Finishing is the rarest skill, and it is the one that gets you hired and noticed.
on_screen:
  title: Why Shipping Matters
  bullets: ["Most VR learners never ship anything",
            "Shipping is paperwork, packaging, patience",
            "A shipped small app beats ten unfinished ones",
            "Finishing is the rarest, most valued skill"]
  layout: bullets
visual: a graveyard of unfinished demos beside one small, live, shipped app glowing
duration_hint_sec: 38

### scene_03_store_vs_lab
narration: |
  Meta gives you two doors to release through.
  The main Meta Store, which is curated. Meta reviews your app carefully, and the bar is high.
  And App Lab, which is open to any developer and far easier to get into.
  App Lab apps are still real, downloadable, shareable by link, just less prominent.
  For your first release, you aim at App Lab. It is the realistic on-ramp.
on_screen:
  title: The Store vs App Lab
  bullets: ["Main Store — curated, reviewed, high bar",
            "App Lab — open to any developer, easier",
            "App Lab apps are real and shareable by link",
            "Aim your first release at App Lab"]
  layout: bullets
visual: two doors — a grand curated store and an open developer lab — the lab door opens
duration_hint_sec: 38

### scene_04_account
narration: |
  Before you can publish, you set up as a developer.
  You create a Meta developer account, and you make an organization, even if it is just you.
  Meta requires you to verify your identity, usually with a credit card or a two-factor check,
  before they let anyone publish. This protects the store.
  Do this early, because verification can take a day or two to clear.
on_screen:
  title: Set Up as a Developer
  bullets: ["Create a Meta developer account",
            "Make an organization — even if it's just you",
            "Verify your identity (card or 2FA)",
            "Do it early — it can take a day or two"]
  layout: bullets
visual: a developer profile and a verified organization badge light up
duration_hint_sec: 38

### scene_05_build
narration: |
  Now you make a release build, which is different from a test build.
  You give your app a unique package name and a version number.
  You sign it with a keystore, a secret key that proves the app is really from you.
  Guard that keystore. If you lose it, you can never update your own app again.
  Then you build a final, optimized package, ready for upload.
on_screen:
  title: Make a Release Build
  bullets: ["A unique package name + version number",
            "Sign it with a keystore (your secret key)",
            "Never lose the keystore — or you can't update",
            "Build the final, optimized package"]
  layout: bullets
visual: a build is stamped with a version, signed with a key, and sealed into a package
duration_hint_sec: 38

### scene_06_storepage
narration: |
  An app is not just the file. It is the listing people see.
  You write a title and a clear description of what your app does.
  You add screenshots and a short trailer, because people decide in seconds from these.
  You set an age rating, a category, and the comfort level, intense or comfortable.
  A good store page is half of whether anyone ever tries your app.
on_screen:
  title: Build the Store Page
  bullets: ["A title and a clear description",
            "Screenshots and a short trailer",
            "Age rating, category, comfort level",
            "The store page is half of getting tried"]
  layout: bullets
visual: a blank listing fills in with title, shots, a trailer, and rating badges
duration_hint_sec: 38

### scene_07_submit
narration: |
  Then you upload and submit.
  You push your signed build to the Meta dashboard and attach it to your store listing.
  You run it through their checks, which test things like performance and required features.
  Then you submit for review, and you wait.
  Review can take days. If they find issues, they tell you, you fix them, and you resubmit. That is normal.
on_screen:
  title: Upload & Submit for Review
  bullets: ["Push the signed build to the dashboard",
            "Attach it to your store listing",
            "Pass their automated checks",
            "Submit, wait, fix any issues, resubmit"]
  layout: bullets
visual: a build uploads, passes a checklist, and enters a review queue
duration_hint_sec: 38

### scene_08_gotchas
narration: |
  A few shipping traps that catch first-timers.
  A rejected build is usually a missing requirement, a frame rate dip, a permission not declared,
  or a crash on launch. Read their feedback closely and fix exactly that.
  Keystore loss is fatal, so back it up in two places. A weak store page gets no downloads even
  if the app is great. And start the whole process earlier than you think. Shipping always takes longer.
on_screen:
  title: Shipping Gotchas
  bullets: ["Rejected? Usually a missing requirement or a crash",
            "Back up your keystore in two places",
            "A weak store page gets no downloads",
            "Start earlier — shipping always takes longer"]
  layout: bullets
visual: a rejection notice, a lost key, and an empty listing each get a fix marker
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what shipping unlocks.
  Real users, real feedback, and the ability to say I built this and you can download it right now.
  That sentence changes how the world sees you. It is the difference between a learner and a developer.
  You started this course never having built a VR app. You are finishing it about to publish one.
  That is the whole journey, and you did it.
on_screen:
  title: What Shipping Unlocks
  bullets: ["Real users and real feedback",
            "\"I built this — download it now\"",
            "The line between a learner and a developer",
            "You started at zero — you're finishing shipped"]
  layout: bullets
visual: a published app gathers its first downloads and a five-star review
duration_hint_sec: 38

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the whole path to the store.
  The lab guide beside it has every exact step. Account setup, the signed release build,
  the store page, and the submission.
  Watch this once, then open the lab guide and ship your app.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (the path to the store)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then ship your app"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 11, and that is the whole course.
  You went from never having opened Unity to building a complete VR and mixed reality app,
  with hands, sound, movement, multiplayer, and a real-world layer, and shipping it to the store.
  You are not a person who watched a VR course. You are a person who built and shipped a VR app.
  Now go make the next one. I cannot wait to see what you build.
on_screen:
  title: You Built and Shipped a VR App
  subtitle: Course complete
  body: Now go make the next one
  layout: center
visual: the full 11-node timeline lights up complete; the shipped app glows; logo outro
duration_hint_sec: 26
