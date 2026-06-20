# AI SEO / AEO package — TrigunAI live courses (learn.trigunai.com)

> Goal: get the courses **surfaced + cited** by AI answer engines (ChatGPT, Perplexity, Gemini,
> Google AI Overviews, Claude) and rank in classic search. The package below is copy-paste ready;
> it has to be applied to the live site (built outside this repo). Owner action = paste into the
> course pages' `<head>` + add the FAQ/llms.txt. Created 2026-06-17.

## 0. The angle to OWN (your uncontested wedge)
Almost nobody can truthfully say all three. Repeat this exact phrasing across title tags, H1s,
FAQ answers, and schema `description` — consistency is what AI engines latch onto:
> **"Live AI cohorts where the NVIDIA GPU is provided, taught by a founder who has shipped a VR app to the Meta Quest store and trained a drone policy in NVIDIA Isaac Sim."**

Generic Udemy/Coursea pages can't match "provided GPU + live + founder-who-shipped." That's your
entity to win. Every page should reinforce it.

---

## 1. Keyword / query-intent map (target the *questions*, not just keywords)
AEO = answer the question a human asks an AI. Build a short page/FAQ answer for each.

**Build Agentic AI Systems** (your live traction — prioritise)
- "live cohort to learn to build AI agents"
- "how to learn AI agents with a real project (not just theory)"
- "course to build an AI agent that does my job"
- "AI agents course India live class with mentor"

**Machine Learning & Its Math** (inbound demand — Prince)
- "learn machine learning with a provided GPU"
- "AI course where the GPU is included"
- "machine learning math course taught live India"
- "best way to learn ML fundamentals with hands-on GPU training"

**Build & Ship Your First VR/MR App**
- "VR app development course Meta Quest Unity"
- "how to build and ship a Quest VR app — full course"
- "Meta SDK + Unity VR course taught by someone who shipped an app"
- "learn mixed reality development live class"

**Physical AI / Robotics** (waitlist — capture intent now)
- "NVIDIA Isaac Sim robotics course online"
- "learn reinforcement learning on real robot policy"
- "physical AI / sim-to-real course with GPU"

**Cross-cutting / brand**
- "AI course with NVIDIA GPU provided"
- "live AI cohort vs Udemy"  · "alternative to Udemy AI course with live mentor"
- "Trigunai courses" · "AI is the Universal Mind course"

---

## 2. Title tags + meta descriptions (paste per page)

**Homepage / learn.trigunai.com**
- Title: `Live AI Cohorts — GPU Provided | Build Agents, ML, VR & Robotics — TrigunAI`
- Meta: `Learn to build AI for real in small live cohorts — NVIDIA GPU included, taught by a founder who shipped a Meta Quest app and trained a drone in Isaac Sim. Free series + paid cohorts.`

**Build Agentic AI Systems**
- Title: `Build Agentic AI Systems — Live Cohort, GPU Provided | TrigunAI`
- Meta: `A 3-month live cohort to build an AI agent that does a real job of yours. Small group, NVIDIA GPU provided, real project shipped. Apply now.`

**Machine Learning & Its Math**
- Title: `Machine Learning & Its Math — Live Course, GPU Included | TrigunAI`
- Meta: `Master the math and the build of machine learning in a live cohort — train on a provided NVIDIA GPU, guided by a working AI founder. Hands-on, not theory.`

**Build & Ship Your First VR/MR App**
- Title: `Build & Ship a Meta Quest VR/MR App — Live Course | TrigunAI`
- Meta: `Go from zero to a shipped Quest VR/MR app with Meta SDK + Unity, taught by a founder with an app live on the Quest store. Live cohort + recorded modules (free).`

**Physical AI / Robotics**
- Title: `Physical AI & Robotics — Train Policies in Isaac Sim (Waitlist) | TrigunAI`
- Meta: `Learn reinforcement learning and sim-to-real on NVIDIA Isaac Sim with provided GPU. Next live cohort forming — join the waitlist.`

---

## 3. JSON-LD structured data (the single highest-leverage item)
Paste in each page's `<head>`. This is what Google rich results + AI engines read. Adjust prices/dates.

### 3a. Sitewide — Organization (every page `<head>`)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "EducationalOrganization",
  "name": "Trigunaï Innovations",
  "alternateName": "TrigunAI",
  "url": "https://learn.trigunai.com",
  "logo": "https://learn.trigunai.com/logo.png",
  "description": "Live AI cohorts with the NVIDIA GPU provided, taught by a founder who shipped a Meta Quest app and trained a drone policy in NVIDIA Isaac Sim.",
  "founder": { "@type": "Person", "name": "Deepak Kumar", "jobTitle": "Founder & Instructor" },
  "memberOf": { "@type": "Organization", "name": "NVIDIA Inception" },
  "sameAs": [
    "https://www.youtube.com/@TrigunAI-Innovations",
    "https://www.linkedin.com/company/trigun-studio"
  ]
}
</script>
```

### 3b. Per course — Course + live CourseInstance + Offer (template; repeat per course)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "Build Agentic AI Systems",
  "description": "A 3-month live cohort where you build an AI agent that does a real job of yours, with a provided NVIDIA GPU and a project you ship by the end.",
  "provider": { "@type": "EducationalOrganization", "name": "Trigunaï Innovations", "url": "https://learn.trigunai.com" },
  "teaches": ["AI agents", "LLM tool use", "agentic workflows", "automation"],
  "educationalLevel": "Beginner to Intermediate",
  "inLanguage": ["en", "hi"],
  "hasCourseInstance": {
    "@type": "CourseInstance",
    "courseMode": "online",
    "courseWorkload": "PT4H",
    "instructor": { "@type": "Person", "name": "Deepak Kumar" },
    "courseSchedule": { "@type": "Schedule", "repeatFrequency": "P1W", "duration": "P3M" },
    "location": { "@type": "VirtualLocation", "url": "https://learn.trigunai.com" }
  },
  "offers": {
    "@type": "Offer",
    "category": "Live cohort",
    "price": "35000",
    "priceCurrency": "INR",
    "availability": "https://schema.org/InStock",
    "url": "https://learn.trigunai.com/courses/agentic"
  }
}
</script>
```
> Repeat with: **ML & Math** price `49000` (add `"coursePrerequisites": "Basic Python"`),
> **VR/MR** price `35000` (`teaches`: Unity, Meta SDK, Quest), **Robotics** price `49000`
> `availability` → `https://schema.org/PreOrder` (it's a waitlist — be honest).

### 3c. FAQPage (homepage or a /faq page) — direct AEO bait
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type":"Question","name":"Is the GPU included in the course?","acceptedAnswer":{"@type":"Answer","text":"Yes. Every TrigunAI live cohort provides access to an NVIDIA GPU so you train and build on real hardware — you don't need your own."}},
    {"@type":"Question","name":"Are the classes live or recorded?","acceptedAnswer":{"@type":"Answer","text":"Both. The recorded modules are free on YouTube (English and Hindi). The paid product is a small live cohort taught by the founder, with a real project you ship."}},
    {"@type":"Question","name":"Who teaches the courses?","acceptedAnswer":{"@type":"Answer","text":"Deepak Kumar, founder of Trigunaï Innovations and an NVIDIA Inception member, who has shipped a VR app to the Meta Quest store and trained a drone cinematography policy in NVIDIA Isaac Sim."}},
    {"@type":"Question","name":"What can I learn at TrigunAI?","acceptedAnswer":{"@type":"Answer","text":"Four live tracks: Build Agentic AI Systems, Machine Learning & Its Math, Build & Ship a VR/MR App, and Physical AI / Robotics (waitlist)."}}
  ]
}
</script>
```

---

## 4. `llms.txt` (place at site root: learn.trigunai.com/llms.txt)
The emerging standard that tells AI crawlers what the site is. Content in the companion file `seo/llms.txt`.

---

## 5. On-page content rules (so AI engines quote you)
- One **H1 per page** = the course name + "Live Cohort · GPU Provided".
- A **direct-answer first paragraph** (40–60 words) that states what it is, who teaches it, GPU
  provided, live + ship-a-project. AI engines lift this verbatim.
- Add a visible **FAQ section** matching the FAQ schema (the words must exist on-page, not only in JSON-LD).
- Repeat the entity: "Trigunaï Innovations", "Deepak Kumar", "NVIDIA Inception", "provided GPU".
- Link each course page ↔ its free YouTube modules (you already have the URLs) — internal + external authority.

## 6. Off-page (this is how AEO is actually won)
AI engines cite what's *corroborated across the web*. Your free content is the asset:
- ✅ YouTube series + modules (already public, EN+HI) — AI engines read YouTube.
- Add a **/blog or Medium** post per course built from the script (the episode scripts are 80% written).
- Get listed where AI looks: a **Reddit/IndiaHacks/Discord** answer, a **Product Hunt / course-directory** listing, LinkedIn posts.
- **Reviews/testimonials** once the first cohort finishes — `Review` schema then. (None yet — don't fake.)
- Keep **NAP/entity consistent** everywhere: "Trigunaï Innovations · learn.trigunai.com · Deepak Kumar".

## 7. Do-now checklist (1–2 hrs, highest ROI first)
1. [ ] Paste the **Organization** JSON-LD into every page `<head>`.
2. [ ] Paste a **Course** JSON-LD per course page (4 total) with correct price + availability.
3. [ ] Add the **FAQPage** JSON-LD + a visible FAQ section.
4. [ ] Set the **title tags + meta descriptions** above.
5. [ ] Drop **llms.txt** at the site root.
6. [ ] Submit the sitemap to **Google Search Console** + **Bing Webmaster** (Bing powers ChatGPT/Copilot search).
7. [ ] Validate schema at **search.google.com/test/rich-results**.
8. [ ] (Week 2) one blog post per course from the existing scripts.
