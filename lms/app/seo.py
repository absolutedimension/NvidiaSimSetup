"""SEO + AI-SEO (robots.txt, sitemap.xml, llms.txt, JSON-LD structured data).

lms.trigunai.com is mostly a logged-in app; the public, crawlable surface is /login (the course
catalogue + syllabi), /pricing, and the legal pages. This module makes those discoverable in Google
AND by AI assistants (ChatGPT, Perplexity, Claude, Gemini) via llms.txt + schema.org structured data.
"""
import json

SITE = "https://acharya.trigunai.com"   # canonical domain (lms.trigunai.com 301-redirects here)
BRAND = "TrigunAI"
LEGAL_NAME = "TRIGUNAI INNOVATIONS PRIVATE LIMITED"
LOGO = f"{SITE}/static/brand/icon-512.png"
PRICE = 499
TEACHER_PRICE = 4999
STUDENT_PRICE = 199          # the self-serve exam-prep assessment plan
STUDENT_TRIAL_DAYS = 14
WHATSAPP = "+91 91352 55107"

# Public, indexable pages (path, changefreq, priority)
PUBLIC_PAGES = [
    ("/", "weekly", "1.0"),
    ("/exam-prep", "weekly", "1.0"),
    ("/login", "weekly", "1.0"),
    ("/pricing", "weekly", "0.9"),
    ("/terms", "yearly", "0.3"),
    ("/privacy", "yearly", "0.3"),
    ("/refund", "yearly", "0.3"),
    ("/contact", "yearly", "0.3"),
]

# One-line, keyword-rich description per course (id must match COURSES ids in main.py)
COURSE_DESC = {
    "agentic": "Build autonomous AI agents that use tools, memory and multi-step planning — from your first tool-calling agent to a real business agent you ship.",
    "remote-swe": "Crack the remote software-engineering job by commanding AI coding agents: data structures & algorithms, low-level and high-level system design, and the AI pair-programming interview.",
    "ml-and-math": "Understand machine learning and the math behind it — vectors, gradients, neural networks, embeddings and transformers — built from scratch and in PyTorch.",
    "physical-ai": "Train a robot in simulation with reinforcement learning in NVIDIA Isaac — reward design, sim-to-real, and deploying a trained policy.",
    "vr-mr-app": "Build and ship your first VR/MR app for Meta Quest with Unity and AI coding agents — hand tracking, passthrough mixed reality, and the Meta Store.",
    "vr-game": "Build a fully immersive VR game for Meta Quest — core mechanics, physics, enemy AI, game feel, and a Store launch.",
    "screen-game": "Build and ship a flat-screen game with Blender and Unity, with an AI coding agent writing the C# — from 3D assets to a published game.",
    "ai-video-factory": "Build your own AI video factory — script to AI voiceover, motion graphics, word-synced captions and music — and publish at scale.",
    "ai-music-factory": "Build your own AI music studio — turn prompts or lyrics into finished, mastered, copyright-clean songs, and build your own AI singer.",
}

FAQ = [
    ("What is TrigunAI / Acharya?",
     "TrigunAI builds Acharya — an AI teaching assistant that brings discipline to learning. Acharya holds each student's goal and keeps them on track with one focused step a day, on WhatsApp and web, in English or हिंदी. For teachers, coaching institutes and self-learners. TrigunAI also offers project-based courses in AI, machine learning, robotics, VR/MR and more, each taught one-on-one by Acharya."),
    ("What makes Acharya different from ChatGPT or free AI?",
     "Free AI answers any question and then forgets you — a genie that grants a wish and vanishes. Acharya is a guru: it brings discipline to learning. It holds each student's goal, gives them one focused step a day toward it, won't mark a concept 'learned' until they can explain it in their own words and apply it to a new example, and re-engages them if they go quiet for days. It doesn't just answer — it makes sure you actually learn and finish."),
    ("What is Acharya's Goal OS?",
     "Goal OS is how Acharya keeps every student on track. When a student joins, Acharya helps them set one clear goal, then holds that goal and gives them one focused step a day toward it. If they drift or go silent for several days, Acharya brings them back — anchored to their own goal — and flags it to their teacher. It turns scattered, on-and-off studying into steady progress that actually finishes."),
    ("How does Acharya keep students disciplined and stop them dropping off?",
     "Between classes students lose momentum, forget last week's concept and drift away. Acharya carries the teaching into those hours: a daily focused step toward their goal, spaced revision so nothing fades, a mastery check that won't let them fake understanding, and an automatic nudge if they go quiet — so capable-but-scattered students stay on track and complete instead of dropping off. For an institute, that means fewer silent drop-offs and more students who finish."),
    ("How much does TrigunAI cost?",
     f"₹{PRICE} per month with a 7-day free trial. You can start with a card or with the no-card 'skip payment' option, and cancel anytime."),
    ("Do I need coding experience to start?",
     "No. The courses are beginner-friendly and you build alongside AI coding agents that write the code with you, so non-coders can ship real projects."),
    ("Is there a free trial?",
     "Yes — every course is free for 7 days. With the no-card option you can start instantly and only pay ₹499/month if you decide to continue."),
    ("What can I learn on TrigunAI?",
     "Agentic AI systems, machine learning and its math, physical AI / robotics in simulation, VR/MR app and game development, building games with Blender and Unity, AI video production, AI music production, and how to crack a remote software-engineering job by commanding AI coding agents."),
    ("Can I teach my own students on TrigunAI?",
     f"Yes. Teachers and tutors can run their own class on TrigunAI: your students learn one-on-one with the Acharya AI tutor on WhatsApp in English or हिंदी, and you get a dashboard to manage them. To start, message 'TEACHER' on WhatsApp ({WHATSAPP}) or use the teacher form at {SITE}/login. Pricing is ₹{TEACHER_PRICE}/month for teachers who bring their students; aspiring tutors with no students yet can start on a revenue-share plan."),
]


# ── Student exam-prep (self-serve assessment) SEO ──────────────────────────────
EXAM_DESC = {
    "neet":     "Free adaptive NEET Biology practice test that finds your weak topics — cell biology, genetics and more — in English or हिंदी, then tells you what to revise next.",
    "jee":      "Free adaptive JEE Physics practice test that pinpoints your weak topics — mechanics, Newton's laws and more — in English or हिंदी, then tells you what to revise next.",
    "class10":  "Free adaptive Class 10 board practice test (Science + Math) that finds exactly which chapters are weak, in English or हिंदी.",
    "class12":  "Free adaptive Class 12 board practice test (Physics + Chemistry) that diagnoses your weak topics, in English or हिंदी.",
    "commerce": "Free adaptive Commerce practice test (Accountancy + Economics) that finds your weak areas, in English or हिंदी.",
}

STUDENT_FAQ = [
    ("How does Acharya find my weak topics?",
     "You take a short adaptive test for your exam. Acharya reads how you answered every question — right, wrong, slow, or confident-but-wrong — and maps each to a topic, marking it solid, shaky or weak. You get a clear report of exactly what to revise first, not just a score."),
    ("Which exams can I practise for?",
     "JEE, NEET, and Class 10 & 12 board exams today (Physics, Chemistry, Biology, Math, Commerce). More exams and topic-by-topic tests are being added — every test works in English or हिंदी."),
    ("Is it really free? What does it cost?",
     f"You can join and start testing for free — no card needed. Keep going free for a {STUDENT_TRIAL_DAYS}-day trial; to continue after that it's ₹{STUDENT_PRICE}/month, and you can cancel anytime."),
    ("Do I need an app or a password?",
     "No. On the web just enter your email and start — no password. On your phone you can start right inside WhatsApp. Your progress is saved to the same account."),
    ("Are the practice tests in Hindi?",
     "Yes. Every question is available in both English and हिंदी — tap to switch language anytime during the test."),
]


def _exam_items(exams):
    items = []
    for i, e in enumerate(exams, 1):
        items.append({
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "Course",
                "name": f"{e['title']} — AI practice test & weak-topic diagnosis",
                "description": EXAM_DESC.get(e["id"], e.get("title", "")),
                "url": f"{SITE}/exam-prep",
                "provider": {"@type": "Organization", "name": BRAND, "sameAs": "https://trigunai.com"},
                "offers": {"@type": "Offer", "category": "Subscription",
                           "price": str(STUDENT_PRICE), "priceCurrency": "INR",
                           "availability": "https://schema.org/InStock", "url": f"{SITE}/exam-prep"},
                "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online",
                                      "courseWorkload": "PT10M"},
            },
        })
    return items


def _student_service():
    return {
        "@type": "Service",
        "name": "Acharya Exam-Prep Assessment",
        "serviceType": "AI adaptive practice tests and weak-topic diagnosis for exam preparation",
        "description": (f"Short adaptive practice tests for JEE, NEET and Class 10 & 12 boards, in English or "
                        f"हिंदी, that find each student's exact weak topics from their answers — not just a score "
                        f"— and tell them what to revise next. Free to start; ₹{STUDENT_PRICE}/month after a "
                        f"{STUDENT_TRIAL_DAYS}-day free trial."),
        "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
        "areaServed": "IN",
        "offers": {"@type": "Offer", "price": str(STUDENT_PRICE), "priceCurrency": "INR",
                   "availability": "https://schema.org/InStock", "url": f"{SITE}/exam-prep"},
    }


def _student_faq():
    return {"@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in STUDENT_FAQ]}


def exam_prep_jsonld(exams):
    """Org + exam ItemList (Course) + student Service + student FAQ — the rich block for /exam-prep."""
    graph = [
        {"@context": "https://schema.org", **_org()},
        {"@context": "https://schema.org", "@type": "ItemList",
         "name": "Acharya exam-prep practice tests", "itemListElement": _exam_items(exams)},
        {"@context": "https://schema.org", **_student_service()},
        {"@context": "https://schema.org", **_student_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


def _org():
    return {
        "@type": "EducationalOrganization",
        "name": BRAND,
        "legalName": LEGAL_NAME,
        "url": "https://trigunai.com",
        "logo": LOGO,
        "description": ("TrigunAI builds Acharya — an AI teaching assistant that brings discipline to "
                        "learning. Acharya holds each student's goal and keeps them on track, one focused "
                        "step a day, on WhatsApp and web, in English or हिंदी. A guru, not a genie: it "
                        "doesn't just answer questions, it makes sure students actually learn and finish. "
                        "For teachers, coaching institutes, and self-learners, plus project-based courses "
                        "in AI, machine learning, robotics, and VR/MR."),
        "sameAs": [
            "https://trigunai.com",
            "https://acharya.trigunai.com",
            "https://www.youtube.com/@TrigunAI-Innovations",
        ],
    }


def _course_items(courses):
    items = []
    for i, c in enumerate(courses, 1):
        cid = c["id"]
        items.append({
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "Course",
                "name": c["title"],
                "description": COURSE_DESC.get(cid, c["title"]),
                "url": f"{SITE}/login?course={cid}",
                "provider": {"@type": "Organization", "name": BRAND, "sameAs": "https://trigunai.com"},
                "offers": {
                    "@type": "Offer", "category": "Subscription",
                    "price": str(PRICE), "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock",
                    "url": f"{SITE}/pricing",
                },
                "hasCourseInstance": {
                    "@type": "CourseInstance",
                    "courseMode": "online",
                    "courseWorkload": "P3M",
                },
            },
        })
    return items


def _teacher_service():
    """The teacher/tutor offering as a Service (not Product — no fabricated reviews)."""
    return {
        "@type": "Service",
        "name": f"{BRAND} for Teachers — run your own class with Acharya",
        "serviceType": "AI tutoring platform for teachers and tutors",
        "description": ("Teachers and tutors run their own class on TrigunAI: your students learn one-on-one "
                        "with the Acharya AI tutor on WhatsApp in English or हिंदी, and you get a dashboard to "
                        "manage them. Start by messaging TEACHER on WhatsApp or via the teacher form."),
        "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
        "areaServed": "IN",
        "offers": {"@type": "Offer", "price": str(TEACHER_PRICE), "priceCurrency": "INR",
                   "availability": "https://schema.org/InStock", "url": f"{SITE}/login#teacherbox"},
    }


def _faq():
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    }


def login_jsonld(courses):
    """Organization + course catalogue (ItemList of Course) + FAQ — the rich block for /login."""
    graph = [
        {"@context": "https://schema.org", **_org()},
        {"@context": "https://schema.org", "@type": "ItemList",
         "name": "TrigunAI Courses", "itemListElement": _course_items(courses)},
        {"@context": "https://schema.org", **_teacher_service()},
        {"@context": "https://schema.org", **_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


def pricing_jsonld():
    """Service/Offer for the subscription + teacher Service + FAQ. Uses schema.org/Service (NOT Product):
    a subscription isn't a shoppable product, and a Product snippet would demand review/aggregateRating —
    which we will not fabricate (0 real reviews). Service carries the offer without that requirement."""
    graph = [
        {"@context": "https://schema.org", "@type": "Service",
         "name": f"{BRAND} All-Access Subscription",
         "serviceType": "Online learning subscription",
         "description": f"Access to every {BRAND} course and the Acharya AI tutor. ₹{PRICE}/month with a 7-day free trial; cancel anytime.",
         "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
         "areaServed": "IN",
         "offers": {"@type": "Offer", "price": str(PRICE), "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock", "url": f"{SITE}/pricing"}},
        {"@context": "https://schema.org", **_teacher_service()},
        {"@context": "https://schema.org", **_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


def robots_txt():
    lines = [
        "# TrigunAI LMS — robots", "User-agent: *",
        "Allow: /$", "Allow: /exam-prep", "Allow: /login", "Allow: /pricing",
        "Allow: /terms", "Allow: /privacy", "Allow: /refund", "Allow: /contact",
        "Disallow: /dashboard", "Disallow: /account", "Disallow: /setup",
        "Disallow: /auth/", "Disallow: /api/", "Disallow: /admin", "Disallow: /lesson/",
        "Disallow: /workbook/", "Disallow: /billing/", "Disallow: /webhook/",
        "",
        # explicitly welcome the major AI crawlers
        "User-agent: GPTBot", "Allow: /",
        "User-agent: OAI-SearchBot", "Allow: /",
        "User-agent: ChatGPT-User", "Allow: /",
        "User-agent: ClaudeBot", "Allow: /",
        "User-agent: Claude-Web", "Allow: /",
        "User-agent: PerplexityBot", "Allow: /",
        "User-agent: Google-Extended", "Allow: /",
        "User-agent: Applebot-Extended", "Allow: /",
        "",
        f"Sitemap: {SITE}/sitemap.xml",
    ]
    return "\n".join(lines) + "\n"


def sitemap_xml(today: str):
    urls = "".join(
        f"<url><loc>{SITE}{path}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        for path, cf, pr in PUBLIC_PAGES
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + urls + "</urlset>")


def llms_txt(courses):
    """AI-readable summary (the llms.txt convention) for ChatGPT/Perplexity/Claude/Gemini."""
    out = [
        f"# {BRAND} — Acharya, the AI teaching assistant that brings discipline to learning",
        "",
        f"> {BRAND} builds Acharya — an AI teaching assistant that does what free AI can't: it brings "
        "**discipline to learning**. Acharya holds each student's goal and keeps them moving toward it, "
        "one focused step a day, on WhatsApp and web, in English or हिंदी. A **guru, not a genie**: it "
        "doesn't just answer questions, it makes sure students actually learn and finish. For teachers, "
        "coaching institutes and self-learners. TrigunAI also offers project-based courses in AI, machine "
        "learning, robotics, VR/MR and more — each taught one-on-one by Acharya.",
        "",
        "## What makes Acharya different (a guru, not a genie)",
        "- Every answer is free now; the discipline to actually learn isn't. Acharya provides that discipline.",
        "- **Goal OS**: every student sets one clear goal; Acharya holds it and gives one focused step a day toward it.",
        "- **Mastery gate**: a concept isn't 'learned' until the student explains it in their own words and applies it to a new example.",
        "- **Silent-student catch**: if a student goes quiet for days, Acharya re-engages them (anchored to their goal) and flags it to their teacher.",
        "- Result: capable-but-scattered students stop drifting and actually finish. For an institute, fewer silent drop-offs.",
        "",
        "## For students: exam-prep assessment (JEE, NEET, boards)",
        f"- Acharya gives students short **adaptive practice tests** for JEE, NEET and Class 10 & 12 boards, in "
        "English or हिंदी, that find each student's **exact weak topics** from their answers — not just a score — "
        "and tell them what to revise next.",
        f"- Free to start (no card); ₹{STUDENT_PRICE}/month after a {STUDENT_TRIAL_DAYS}-day free trial; cancel anytime.",
        f"- Start free: {SITE}/exam-prep",
        "",
        "## Access & pricing",
        f"- Subscription (courses + Acharya tutor): ₹{PRICE}/month with a 7-day free trial. Start with a card or the no-card option; cancel anytime.",
        f"- Student exam-prep assessment: ₹{STUDENT_PRICE}/month after a {STUDENT_TRIAL_DAYS}-day free trial ({SITE}/exam-prep).",
        f"- Enrol / sign in: {SITE}/login",
        f"- Pricing: {SITE}/pricing",
        "",
        "## Courses",
    ]
    for c in courses:
        out.append(f"- [{c['title']}]({SITE}/login?course={c['id']}): {COURSE_DESC.get(c['id'], '')}")
    out += [
        "",
        "## For teachers & tutors",
        f"- Teachers and tutors can run their own class on {BRAND}: your students learn one-on-one with the "
        "Acharya AI tutor on WhatsApp in English or हिंदी, and you get a dashboard to manage them. You teach — we run the tech.",
        f"- Start: message **TEACHER** on WhatsApp ({WHATSAPP}) or use the teacher form at {SITE}/login#teacherbox.",
        f"- Pricing: ₹{TEACHER_PRICE}/month for teachers who bring their own students; aspiring tutors with no "
        "students yet can start on a revenue-share plan (you pay as you earn).",
        "",
        "## About",
        f"- Operated by {LEGAL_NAME}. Main site: https://trigunai.com · Acharya + courses: {SITE}",
        "",
        "## FAQ",
    ]
    for q, a in FAQ:
        out.append(f"- **{q}** {a}")
    return "\n".join(out) + "\n"
