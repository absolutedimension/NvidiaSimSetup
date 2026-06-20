# Module 11 — Lab Guide

**Ship to Meta's Store — Publish Your VR App**

> Use this alongside the Module 11 video. The video is the map (the whole path to the store); this
> guide is the terrain (every exact step). By the end, your signed app is uploaded to App Lab with a
> real store page, submitted for review.
>
> **Time:** ~2–3 hours spread over a few days (verification + review take time). **You need:** ZenSpace
> (Modules 1–10), a finished + performant build, Claude Code.

---

## Step 0 — Start the slow things first

- [ ] Create a **Meta developer account** at developer.oculus.com
- [ ] Create an **Organization** (even solo — required to publish)
- [ ] Complete **identity / payment verification** (can take 1–2 days — do it now)

---

## Step 1 — Create the app in the dashboard

1. In the **Meta Quest Developer Dashboard**, create a **New App** → choose **Meta Quest (Store)**.
2. Pick the **App Lab** distribution channel for your first release (open, no curation gate).
3. Note your **App ID** — you'll need it in Unity.

---

## Step 2 — Configure the Unity project for release

1. **Edit → Project Settings → Player:**
   - Set a unique **Package Name**: `com.yourname.zenspace`
   - Set **Version** (e.g. `1.0.0`) and **Bundle Version Code** (`1`)
   - Minimum API level + scripting backend (**IL2CPP**, **ARM64**) per Meta's requirements
2. Fill in **Company Name** and **Product Name**.

```
Check my Player Settings are correct for a Meta Quest store release: package name,
version, IL2CPP + ARM64, min API level, and any Meta-required settings. List anything wrong.
```

---

## Step 3 — Create and guard a keystore

1. **Project Settings → Player → Publishing Settings → Keystore Manager → Create New.**
2. Set a keystore password + a key alias + key password. **Write these down.**
3. **Back up the `.keystore` file in two safe places.**
   - ⚠️ If you lose it, you can **never update your published app** — you'd have to publish a new one.

---

## Step 4 — Build the signed release APK / AAB

1. **File → Build Profiles → Meta Quest → Build** (release, not development).
2. Ensure it's signed with your keystore (Step 3).
3. Output a final `.apk` (or `.aab`). This is what you upload.

---

## Step 5 — Build the store page

In the dashboard's listing section, add:
- [ ] **Title** + **short and long descriptions** (clear: what it is, what you do)
- [ ] **Screenshots** (from your Quest) + a short **trailer** video
- [ ] **App icon** + cover art
- [ ] **Age rating** (IARC questionnaire), **category**, and **comfort rating** (Comfortable / Moderate / Intense)
- [ ] Privacy policy URL (required) + any data-use declarations

> Ask the agent to draft copy: *"Write a Quest store title + short + long description for ZenSpace,
> a VR/MR meditation room. Calm, honest, no hype."*

---

## Step 6 — Upload, pass checks, submit

1. Upload your signed build to the app's **Builds / Release Channels**.
2. Run Meta's **upload checks** (they test performance, manifest, required features) — fix any failures.
3. Attach the build to your **App Lab** channel, link the store listing, and **Submit for Review**.
4. **Wait.** Review can take several days. If rejected, read the feedback, fix exactly that, resubmit.

🎉 Your app is on its way to real headsets.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build rejected at upload checks | Read the exact failure — usually performance, a missing permission, or a manifest setting. |
| "App crashes on launch" in review | Test the **release** build on a clean Quest before submitting (release ≠ dev build). |
| Can't publish at all | Identity/payment verification not complete — finish Step 0. |
| Lost keystore | You cannot update that app — keep two backups from the start. |
| Listing looks empty/unappealing | Add real screenshots + a trailer; the store page drives downloads. |
| Review is slow | Normal — submit early, be patient, respond fast to feedback. |

---

## ✅ Module 11 complete — and the course is complete. You now have:

- A verified Meta developer organization
- A signed, optimized release build (keystore safely backed up)
- A real store page with art, description, and ratings
- An app uploaded to App Lab and submitted for review
- The rarest skill of all: **you finished and shipped**

**You did it.** You went from never opening Unity to a complete, shipped VR + MR app — with hands,
UI, audio, movement, saving, multiplayer, mixed reality, polish, and a store listing. Now go build
the next one.
