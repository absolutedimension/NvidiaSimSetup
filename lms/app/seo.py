"""SEO + AI-SEO (robots.txt, sitemap.xml, llms.txt, JSON-LD structured data).

acharya.trigunai.com is the product home for Acharya — an AI **exam-prep & assessment engine**.
It has two sections: **students** (`/exam-prep` — self-serve adaptive practice tests + mock papers
with weak-topic diagnosis) and **teachers** (`/teacher` — create a real exam-pattern test paper,
share a no-signup link, get a live weak-topic dashboard for the class). Both are built on a bank of
46,000+ verified questions across JEE, NEET, CBSE Class 10 & 12, UPSC and Banking.

This module makes those public surfaces discoverable in Google AND by AI assistants (ChatGPT,
Perplexity, Claude, Gemini) via llms.txt + schema.org structured data. The crawl angle is
**exam-authentic test papers**, not the older "courses" framing (courses are now secondary).
"""
import json

SITE = "https://acharya.trigunai.com"   # canonical domain (lms.trigunai.com 301-redirects here)
BRAND = "TrigunAI"
PRODUCT = "Acharya"
LEGAL_NAME = "TRIGUNAI INNOVATIONS PRIVATE LIMITED"
LOGO = f"{SITE}/static/brand/icon-512.png"
QBANK_VERIFIED = "46,000+"      # verified questions behind the papers — the real differentiator
PRICE = 499                     # legacy all-access course subscription (secondary, /pricing only)
# UNIFIED FLAT PRICING (2026-08-04) — ONE price for students, teachers AND institutes, by exam LEVEL.
# Free to start; pay only after the first month. Branding is a FREE self-serve feature (no ₹55k).
PRICE_JUNIOR = 150              # ₹/month (student) or ₹/student/month (teacher & institute) — Junior / Foundation / Board
PRICE_SENIOR = 250             # ₹/month or ₹/student/month — JEE / NEET / Senior
STUDENT_TRIAL_DAYS = 14
WHATSAPP = "+91 91352 55107"

# Reusable truth phrases (keep every SEO surface consistent).
PRICING_LINE = (f"One flat price for students, teachers and institutes: ₹{PRICE_JUNIOR}/month for Junior & "
                f"Foundation, ₹{PRICE_SENIOR}/month for JEE / NEET / Senior. Free to start — pay only after "
                f"your first month, cancel anytime.")
BRANDING_LINE = ("Institutes get free self-serve white-label branding — put their own logo, brand colour and "
                 "watermark on the app and every printed paper (only ‘Powered by Acharya’ stays).")

# The exam range the papers cover (live today). Kept in sync with STUDENT_EXAMS(available) in main.py.
EXAM_RANGE = "JEE, NEET, CBSE Class 10 & 12 (incl. Commerce), UPSC Civil Services and Banking (IBPS / SBI / RRB)"

# Public, indexable pages (path, changefreq, priority)
PUBLIC_PAGES = [
    ("/", "weekly", "1.0"),
    ("/exam-prep", "weekly", "1.0"),     # students
    ("/teacher", "weekly", "1.0"),       # teachers
    ("/login", "weekly", "0.8"),
    ("/pricing", "weekly", "0.8"),
    ("/terms", "yearly", "0.3"),
    ("/privacy", "yearly", "0.3"),
    ("/refund", "yearly", "0.3"),
    ("/contact", "yearly", "0.3"),
]

# One-line, keyword-rich description per course (id must match COURSES ids in main.py). Secondary now.
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

# General FAQ (used on /login + /pricing) — now led by the test-paper / exam-prep angle.
FAQ = [
    ("What is TrigunAI / Acharya?",
     f"TrigunAI builds Acharya — an AI exam-prep and assessment engine. It generates authentic, "
     f"exam-pattern practice papers from a bank of {QBANK_VERIFIED} verified questions ({EXAM_RANGE}) "
     f"and pinpoints exactly which topics are weak. Students practise on their own at "
     f"{SITE}/exam-prep; teachers and institutes create real test papers and track their class at "
     f"{SITE}/teacher."),
    ("What makes Acharya's test papers different?",
     f"They're exam-authentic and unlimited. Every paper is drawn from {QBANK_VERIFIED} verified, "
     "human-checked questions plus a RAG generator that writes fresh, copyright-clean questions in the "
     "real exam pattern — so you never run out of good questions. And Acharya doesn't just score you: "
     "it reads how you answered every question and tells you exactly which topics to revise next."),
    ("Which exams can I prepare for?",
     f"{EXAM_RANGE} are live today, in English or हिंदी. CUET, SSC, GATE, CAT and CLAT are on the way. "
     "Students get adaptive practice tests and full mock papers; teachers can build a paper for any of these."),
    ("I'm a teacher — what do I get?",
     f"Create a real, exam-pattern test paper for JEE, NEET or the boards in minutes, share a link, and "
     f"your students take it with no signup. You get a live dashboard showing each student's weak topics "
     f"and the whole class at a glance. {BRANDING_LINE} Start free at {SITE}/teacher (or message 'TEACHER' "
     f"on WhatsApp {WHATSAPP})."),
    ("How does Acharya find my weak topics?",
     "You take a short adaptive test or a mock paper. Acharya reads every answer — right, wrong, slow, or "
     "confident-but-wrong — maps each to a topic, and marks it solid, shaky or weak. You get a clear report "
     "of exactly what to revise first, not just a mark out of 100."),
    ("How much does it cost?",
     f"{PRICING_LINE} Teachers and coaching institutes pay the same flat per-student rate — any number of "
     f"students, no setup fee — and institute branding is free and self-serve. TrigunAI also offers "
     f"project-based AI/ML/robotics/VR courses (₹{PRICE}/month, secondary to exam prep)."),
    ("Do I need an app or a password?",
     "No. On the web just enter your email and start — no password. On your phone you can start right inside "
     "WhatsApp in English or हिंदी. Your progress saves to the same account."),
]


# ── Student exam-prep (self-serve assessment) SEO ──────────────────────────────
EXAM_DESC = {
    "neet":     "Authentic NEET practice tests and mock papers (Biology, Physics, Chemistry) from a verified question bank, with weak-topic diagnosis — English or हिंदी.",
    "jee":      "Authentic JEE / IIT practice tests and mock papers (Physics, Chemistry, Maths) from a verified question bank, with weak-topic diagnosis — English or हिंदी.",
    "class10":  "CBSE Class 10 board practice papers (Science + Math) that find exactly which chapters are weak — English or हिंदी.",
    "class12":  "CBSE Class 12 board practice papers (Physics + Chemistry + Biology) that diagnose your weak topics — English or हिंदी.",
    "commerce": "CBSE Class 12 Commerce practice papers (Accountancy + Economics) that find your weak areas — English or हिंदी.",
    "banking":  "Banking exam practice papers (IBPS / SBI / RRB quantitative aptitude) with computed answer keys and weak-area diagnosis.",
    "upsc":     "UPSC Civil Services (IAS) Prelims practice from real past-paper questions — GS + CSAT — with topic-level diagnosis.",
}

STUDENT_FAQ = [
    ("Are these real, exam-pattern papers?",
     f"Yes. Every question comes from a bank of {QBANK_VERIFIED} verified questions plus a generator that "
     "writes fresh questions in the real exam pattern — so the papers look and feel like the actual exam and "
     "you never run out of new ones."),
    ("How does Acharya find my weak topics?",
     "Acharya reads how you answered every question — right, wrong, slow, or confident-but-wrong — maps each "
     "to a topic, and marks it solid, shaky or weak. You get a clear report of what to revise first, not just a score."),
    ("Which exams can I practise for?",
     f"{EXAM_RANGE} are live today — practice tests and full mock papers, in English or हिंदी. CUET, SSC, "
     "GATE, CAT and CLAT are being added."),
    ("Is it really free? What does it cost?",
     f"You can join and start testing for free — no card needed. {PRICING_LINE}"),
    ("Are the papers in Hindi?",
     "Yes. Every question is available in both English and हिंदी — tap to switch language anytime during the test."),
]

# ── Teacher exam-prep SEO ──────────────────────────────────────────────────────
TEACHER_FAQ = [
    ("How do I create a test for my class?",
     f"Pick the exam and chapters, and Acharya builds an exam-pattern paper from {QBANK_VERIFIED} verified "
     "questions in minutes. Share the link with your students — they take it with no signup or app."),
    ("What do I see about my students?",
     "A live dashboard: each student's weak topics, the whole class at a glance, and a suggested next test for "
     "students who are slipping. You teach; Acharya tests and tracks."),
    ("Do my students need to install anything?",
     "No. They open the link, take the test in the browser (or on WhatsApp) in English or हिंदी, and their "
     "results flow straight to your dashboard."),
    ("What does it cost for teachers?",
     f"Free to start — pay only after your first month. Then a flat ₹{PRICE_JUNIOR} per student per month for "
     f"Junior/Foundation batches, or ₹{PRICE_SENIOR} for JEE/NEET/Senior — any number of students, no setup "
     f"fee. {BRANDING_LINE}"),
]


def _exam_items(exams):
    items = []
    for i, e in enumerate(exams, 1):
        items.append({
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "Course",
                "name": f"{e['title']} — practice tests, mock papers & weak-topic diagnosis",
                "description": EXAM_DESC.get(e["id"], e.get("title", "")),
                "url": f"{SITE}/exam-prep",
                "provider": {"@type": "Organization", "name": BRAND, "sameAs": "https://trigunai.com"},
                "offers": {"@type": "Offer", "category": "Subscription",
                           "price": str(PRICE_JUNIOR), "priceCurrency": "INR",
                           "availability": "https://schema.org/InStock", "url": f"{SITE}/exam-prep"},
                "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online",
                                      "courseWorkload": "PT30M"},
            },
        })
    return items


def _student_service():
    return {
        "@type": "Service",
        "name": "Acharya Exam Prep — practice tests & mock papers",
        "serviceType": "AI exam-prep: adaptive practice tests, mock papers and weak-topic diagnosis",
        "description": (f"Authentic, exam-pattern practice tests and mock papers for {EXAM_RANGE}, in English "
                        f"or हिंदी, generated from a bank of {QBANK_VERIFIED} verified questions. Acharya finds "
                        f"each student's exact weak topics from their answers — not just a score — and tells them "
                        f"what to revise next. {PRICING_LINE}"),
        "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
        "areaServed": "IN",
        "offers": {"@type": "Offer", "price": str(PRICE_JUNIOR), "priceCurrency": "INR",
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
         "name": "Acharya exam-prep practice tests & mock papers", "itemListElement": _exam_items(exams)},
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
        "description": (f"TrigunAI builds Acharya — an AI exam-prep and assessment engine. It generates "
                        f"authentic, exam-pattern practice papers and mock tests from a bank of {QBANK_VERIFIED} "
                        f"verified questions ({EXAM_RANGE}) and pinpoints exactly which topics are weak. For "
                        f"students preparing on their own and for teachers and coaching institutes who set tests "
                        f"and track their class. In English or हिंदी, on web and WhatsApp."),
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
    """The teacher/institute offering as a Service (not Product — no fabricated reviews)."""
    return {
        "@type": "Service",
        "name": f"{PRODUCT} for Teachers — create exam-pattern test papers & track your class",
        "serviceType": "AI test-paper generation and class assessment for teachers and coaching institutes",
        "description": (f"Teachers and institutes create authentic, exam-pattern test papers for JEE, NEET and "
                        f"the CBSE boards in minutes — drawn from {QBANK_VERIFIED} verified questions — share a "
                        f"link, and students take the test with no signup. A live dashboard shows each student's "
                        f"weak topics and the whole class at a glance. You teach; Acharya tests and tracks. "
                        f"Free to start — pay only after your first month; then a flat ₹{PRICE_JUNIOR}/student "
                        f"(Junior/Foundation) or ₹{PRICE_SENIOR}/student (JEE/NEET/Senior) per month, no setup "
                        f"fee. {BRANDING_LINE} Start free at {SITE}/teacher or message TEACHER on WhatsApp."),
        "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
        "areaServed": "IN",
        "offers": {"@type": "Offer", "price": str(PRICE_JUNIOR), "priceCurrency": "INR",
                   "availability": "https://schema.org/InStock", "url": f"{SITE}/teacher"},
    }


def _teacher_faq():
    return {"@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in TEACHER_FAQ]}


def teacher_jsonld():
    """Org + teacher Service + teacher FAQ — the rich block for /teacher."""
    graph = [
        {"@context": "https://schema.org", **_org()},
        {"@context": "https://schema.org", **_teacher_service()},
        {"@context": "https://schema.org", **_teacher_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


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
    """Organization + exam-prep Service + teacher Service + course catalogue + FAQ — rich block for /login."""
    graph = [
        {"@context": "https://schema.org", **_org()},
        {"@context": "https://schema.org", **_student_service()},
        {"@context": "https://schema.org", **_teacher_service()},
        {"@context": "https://schema.org", "@type": "ItemList",
         "name": "TrigunAI Courses", "itemListElement": _course_items(courses)},
        {"@context": "https://schema.org", **_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


def pricing_jsonld():
    """Exam-prep Service + teacher Service + legacy course subscription + FAQ. Uses schema.org/Service
    (NOT Product): a subscription isn't a shoppable product, and a Product snippet would demand
    review/aggregateRating — which we will not fabricate (0 real reviews)."""
    graph = [
        {"@context": "https://schema.org", **_student_service()},
        {"@context": "https://schema.org", **_teacher_service()},
        {"@context": "https://schema.org", "@type": "Service",
         "name": f"{BRAND} All-Access Course Subscription",
         "serviceType": "Online learning subscription (project-based AI/ML/robotics/VR courses)",
         "description": f"Access to every {BRAND} project-based course and the Acharya AI tutor. ₹{PRICE}/month with a 7-day free trial; cancel anytime. Secondary to Acharya exam prep.",
         "provider": {"@type": "Organization", "name": BRAND, "url": "https://trigunai.com"},
         "areaServed": "IN",
         "offers": {"@type": "Offer", "price": str(PRICE), "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock", "url": f"{SITE}/pricing"}},
        {"@context": "https://schema.org", **_faq()},
    ]
    return json.dumps(graph, ensure_ascii=False)


def robots_txt():
    lines = [
        "# TrigunAI LMS — robots", "User-agent: *",
        "Allow: /$", "Allow: /exam-prep", "Allow: /teacher", "Allow: /login", "Allow: /pricing",
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
        f"# {BRAND} — Acharya, an AI exam-prep & assessment engine (authentic test papers)",
        "",
        f"> {BRAND} builds **Acharya** — an AI exam-prep and assessment engine. It generates **authentic, "
        f"exam-pattern practice papers and mock tests** from a bank of **{QBANK_VERIFIED} verified questions** "
        f"({EXAM_RANGE}) and pinpoints exactly which topics are weak. Two sections: **students** practise on "
        f"their own, and **teachers / coaching institutes** create real test papers and track their class. In "
        f"English or हिंदी, on web and WhatsApp.",
        "",
        "## For students — exam prep & practice papers",
        f"- Short **adaptive practice tests** and full **mock papers** for {EXAM_RANGE}, in English or हिंदी.",
        "- Every paper is exam-authentic and unlimited: drawn from a verified bank plus a generator that writes "
        "fresh, copyright-clean questions in the real exam pattern — so you never run out of good questions.",
        "- Acharya reads every answer and gives you your **exact weak topics** to revise next — not just a score.",
        f"- {PRICING_LINE}",
        f"- Start free: {SITE}/exam-prep",
        "",
        "## For teachers & coaching institutes — create test papers, track your class",
        f"- Create an authentic, exam-pattern **test paper** for JEE, NEET or the CBSE boards in minutes, drawn "
        f"from {QBANK_VERIFIED} verified questions.",
        "- **Share a link — students take the test with no signup or app** (web or WhatsApp, English or हिंदी).",
        "- Get a **live weak-topic dashboard**: each student's weak areas and the whole class at a glance, plus a "
        "suggested next test for students who are slipping. You teach; Acharya tests and tracks.",
        f"- Start free: {SITE}/teacher — or message **TEACHER** on WhatsApp ({WHATSAPP}).",
        f"- Free to start — pay only after your first month; then a flat ₹{PRICE_JUNIOR}/student (Junior/Foundation) "
        f"or ₹{PRICE_SENIOR}/student (JEE/NEET/Senior) per month, any number of students, no setup fee.",
        f"- {BRANDING_LINE}",
        "",
        "## Exams covered",
        f"- Live today: {EXAM_RANGE} — practice tests, mock papers and teacher test-papers.",
        "- Coming soon: CUET, SSC, GATE, CAT, CLAT.",
        "",
        "## Also: an AI tutor that brings discipline (secondary)",
        "- Beyond testing, Acharya can tutor one-on-one on WhatsApp/web: it holds each student's goal, gives one "
        "focused step a day, won't mark a concept learned until they can explain and apply it, and re-engages "
        "students who go quiet. A guru, not a genie.",
        "",
        "## Also: project-based courses (secondary)",
    ]
    for c in courses:
        out.append(f"- [{c['title']}]({SITE}/login?course={c['id']}): {COURSE_DESC.get(c['id'], '')}")
    out += [
        f"- Course subscription: ₹{PRICE}/month with a 7-day free trial ({SITE}/pricing).",
        "",
        "## About",
        f"- Operated by {LEGAL_NAME}. Main site: https://trigunai.com · Product home: {SITE}",
        f"- Students: {SITE}/exam-prep · Teachers: {SITE}/teacher · Sign in: {SITE}/login",
        "",
        "## FAQ",
    ]
    for q, a in FAQ:
        out.append(f"- **{q}** {a}")
    return "\n".join(out) + "\n"
