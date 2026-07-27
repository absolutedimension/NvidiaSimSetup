"""Policy / legal pages for Acharya — a data-driven exam-preparation service.

Served by /terms /privacy /refund /disclaimer /contact via a shared template
(policy.html). Written to describe HONESTLY what Acharya actually does (generate
exam-pattern practice tests from a verified question bank + weak-topic analytics
+ teacher tools) and to NOT overclaim (no guarantee of exam results; not
affiliated with any exam authority). Aligned to Indian law: DPDP Act 2023, the
IT Act & Intermediary/Consumer rules, and the Consumer Protection (E-Commerce)
Rules. Entity + contact are set once below.

NOTE: These are plain-language, good-faith policies for a live product; they are
not a substitute for review by a lawyer before you rely on them commercially.
"""

COMPANY = "TRIGUNAI INNOVATIONS PRIVATE LIMITED"
CIN = "U86909BR2025PTC078945"               # RoC-Patna · incorporated 12-09-2025
BRAND = "Acharya"
PARENT = "TrigunAI Innovations"
SITE = "acharya.trigunai.com"
EMAIL = "deepak@trigunai.com"
PHONE = "+91 91352 55107"
CITY = "Patna, Bihar"
ADDRESS = "C/O Smt. Rita Yadav, Shivajee Nagar, Sadakat, Patliputra, Patna, Bihar 800013, India"
JURISDICTION = "Patna, Bihar"
GRIEVANCE_OFFICER = "Deepak Kumar"
UPDATED = "27 July 2026"

# Pricing (kept in sync with config.ASSESS_PRICE_INR / the landing)
STUDENT_PRICE = 249                        # ₹/month
EXAM_PASS = 1299                           # ₹ one-time, "till your exam"
TEACHER_FROM = 999                         # ₹/month, by class size
TRIAL_DAYS = 14

# Exam names used purely to describe what students can practise for. These are
# the trademarks of their respective authorities — see the Disclaimer.
_EXAM_NAMES = "JEE (Main &amp; Advanced), NEET, CBSE Class 10 &amp; 12, banking (IBPS/SBI/RRB) and UPSC Civil Services (Preliminary)"

_FOOT = (f"<p class='upd'>Last updated: {UPDATED}. Questions? Email "
         f"<a href='mailto:{EMAIL}'>{EMAIL}</a> or call {PHONE}.</p>")

LEGAL = {
    "terms": {
        "title": "Terms of Service",
        "html": f"""
<p>{BRAND} ({SITE}) is an online exam-preparation service operated by {COMPANY} (CIN {CIN}), a company registered in India with its registered office at {ADDRESS} ("we", "us", "our"). By creating an account, opening a shared test link, or otherwise using {BRAND} you agree to these Terms. If you do not agree, please do not use the service.</p>

<h2>1. What {BRAND} is — and what it is not</h2>
<p>{BRAND} helps students and teachers <b>practise</b> for competitive and board exams. We do this by:</p>
<ul>
<li>serving questions from a bank of <b>verified past-paper questions</b> and, where noted, <b>new practice questions authored by our AI engine</b> in the pattern of a given exam;</li>
<li>scoring practice tests and showing <b>topic-level strengths and weak spots</b>;</li>
<li>giving teachers/institutes tools to generate a test, share one link, and see how their students performed.</li>
</ul>
<p><b>What {BRAND} is not:</b> we are <b>not a guarantee of any exam result, score, rank, or admission</b>. We do not conduct any actual examination, and we are <b>not affiliated with, authorised by, or endorsed by</b> any examination body or board (see the <a href="/disclaimer">Content &amp; Accuracy Disclaimer</a>). Practice questions — especially AI-authored ones — may occasionally contain errors; treat them as study aids, verify against your official syllabus and textbooks, and please report anything that looks wrong.</p>

<h2>2. Eligibility &amp; accounts</h2>
<p>You sign in with your email (and optionally Google). You are responsible for the accuracy of the details you provide and for keeping access to your email/account secure. One student account is for one learner. If you are under 18, you may use {BRAND} only with the consent and involvement of a parent or legal guardian, who accepts these Terms on your behalf (see the <a href="/privacy">Privacy Policy</a>, section on minors).</p>

<h2>3. Free trial, plans &amp; billing</h2>
<p>Students may start a <b>{TRIAL_DAYS}-day free trial</b>. Paid access is offered as a monthly plan of <b>₹{STUDENT_PRICE}/month</b>, or an <b>Exam Pass of ₹{EXAM_PASS}</b> for access until your target exam. Teacher/institute plans start at <b>₹{TEACHER_FROM}/month</b> and are priced by the number of students. Prices are in Indian Rupees and are shown before you pay. We may change prices prospectively; changes never affect a period you have already paid for. Payments are processed by our payment partner (Razorpay); we never see or store your card/UPI/bank credentials.</p>

<h2>4. Cancellation &amp; refunds</h2>
<p>You can cancel anytime; cancellation stops future renewals and you keep access until the end of your current paid period. Refunds are governed by our <a href="/refund">Refund &amp; Cancellation Policy</a>.</p>

<h2>5. Acceptable use</h2>
<p>You agree not to: share, resell, scrape, or redistribute questions, solutions, or any content; use the content to build or train a competing product or dataset; attempt to break, overload, or reverse-engineer the service; upload unlawful, infringing, or harmful content; or use {BRAND} to cheat in a real, proctored examination. Teachers/institutes are responsible for how they use generated papers and for their own students' data they collect through the class feature. We may suspend or terminate accounts that breach these Terms.</p>

<h2>6. Intellectual property</h2>
<p>The {BRAND} software, question bank, generated questions, worked solutions, analytics, and design are owned by {COMPANY} or its licensors and are provided to you for personal, non-commercial study (or, for teachers, for use with your own students). Exam names and trademarks belong to their respective owners and are used only to describe what you can practise for.</p>

<h2>7. Availability &amp; changes to the service</h2>
<p>We work to keep {BRAND} available but do not promise uninterrupted or error-free service, and features may change or be withdrawn. Some questions are generated on demand by third-party AI models and generation can occasionally be slow or fail.</p>

<h2>8. Disclaimer &amp; limitation of liability</h2>
<p>The service and all content are provided on an "as is" and "as available" basis, without warranties of any kind, including any warranty that practice will improve your result. To the maximum extent permitted by law, {COMPANY} is not liable for any indirect, incidental, or consequential loss, or for exam outcomes. Our total aggregate liability for any claim is limited to the amount you paid us for the service in the 12 months before the claim. Nothing here excludes liability that cannot be excluded under applicable law.</p>

<h2>9. Grievances, governing law &amp; disputes</h2>
<p>For any complaint, contact our Grievance Officer, <b>{GRIEVANCE_OFFICER}</b>, at <a href="mailto:{EMAIL}">{EMAIL}</a> / {PHONE}; we aim to acknowledge within 48 hours and resolve within 30 days. These Terms are governed by the laws of India, and the courts at <b>{JURISDICTION}</b> have exclusive jurisdiction. We may update these Terms; material changes will be posted on this page with a new "last updated" date.</p>
{_FOOT}
""",
    },

    "privacy": {
        "title": "Privacy Policy",
        "html": f"""
<p>{COMPANY} ("we") operates {BRAND} ({SITE}). This policy explains what personal data we collect, why, and your rights. It is written to be consistent with India's <b>Digital Personal Data Protection Act, 2023 (DPDP Act)</b>. By using {BRAND} you consent to the processing described here for the stated purposes.</p>

<h2>1. What we collect</h2>
<ul>
<li><b>Account data</b> — your name, email, and (optionally) your WhatsApp number and the exam/goal you choose.</li>
<li><b>Learning &amp; performance data</b> — the tests you take, your answers, scores, per-topic mastery, and which questions you've already seen. This is the core data that powers your weak-topic report and adaptive practice.</li>
<li><b>Payment data</b> — handled entirely by <b>Razorpay</b>. We do not receive or store your card, UPI, or bank details; we store only your plan status and billing dates.</li>
<li><b>Technical data</b> — a session cookie to keep you signed in, and basic logs (e.g. errors) needed to run the service securely.</li>
</ul>
<p>We ask only for what the service needs. We do <b>not</b> run third-party advertising or behavioural ad-tracking on {BRAND}.</p>

<h2>2. Why we use it (purposes)</h2>
<ul>
<li>to provide the service — generate and score tests, build your weak-topic report, and personalise practice;</li>
<li>to run teacher/institute features — show a teacher the results of students who take that teacher's shared test;</li>
<li>to operate billing and send you essential service messages (login links, billing notices, important changes);</li>
<li>to <b>improve {BRAND}</b> — we analyse aggregated and de-identified usage to fix errors, improve question quality, and make the product better. We do not sell your personal data, and we do not use your identifiable data to train third-party AI models.</li>
</ul>

<h2>3. Who we share with</h2>
<p>We share data only with the processors that run the service, under contract and only as needed: <b>Razorpay</b> (payments), <b>Microsoft Azure</b> (hosting, India/other regions), our transactional email/WhatsApp providers, and the AI model provider that generates questions on demand (which receives the generation prompt, not your identity). We may disclose data if required by law. We do not sell or rent your data to anyone.</p>

<h2>4. Children &amp; students under 18</h2>
<p>{BRAND} is used to prepare for school and entrance exams, so some users are minors. If you are under 18, you must use {BRAND} with the consent and supervision of a parent or legal guardian, who is responsible for the account. We do not knowingly use a child's data for advertising or for any behavioural tracking beyond what is needed to provide the learning features. A parent/guardian may contact us at any time to review or delete a child's data. When a teacher shares a class test, the teacher (as the school/institute) is responsible for having the appropriate consent from students/parents.</p>

<h2>5. Retention</h2>
<p>We keep your data while your account is active and for a reasonable period afterwards as needed to meet legal, accounting, or dispute-resolution obligations, after which it is deleted or anonymised.</p>

<h2>6. Your rights</h2>
<p>You may access, correct, or delete your personal data, withdraw consent, or ask a question about how it is used — email <a href="mailto:{EMAIL}">{EMAIL}</a>. Withdrawing consent may mean we can no longer provide parts of the service. You can also nominate someone to exercise these rights on your behalf as provided under the DPDP Act.</p>

<h2>7. Security</h2>
<p>We use reasonable technical and organisational measures — encrypted transport (HTTPS), access controls, and reputable hosting on Azure. No system is perfectly secure, but we work to protect your data and will notify affected users and the authorities of a significant breach as required by law.</p>

<h2>8. Grievance Officer</h2>
<p>In line with the DPDP Act and the IT Rules, our Grievance Officer is <b>{GRIEVANCE_OFFICER}</b>. For any privacy question or complaint, contact <a href="mailto:{EMAIL}">{EMAIL}</a> / {PHONE}, {COMPANY}, {ADDRESS}. We aim to acknowledge within 48 hours and resolve within 30 days.</p>
{_FOOT}
""",
    },

    "refund": {
        "title": "Refund &amp; Cancellation Policy",
        "html": f"""
<p>This policy applies to {BRAND} plans ({SITE}), operated by {COMPANY}.</p>
<h2>Free trial — pay nothing to evaluate</h2>
<p>Students get a <b>{TRIAL_DAYS}-day free trial</b> with real tests, so you can fully judge whether {BRAND} works for you <b>before you pay</b>. If you don't continue, you are never charged.</p>
<h2>Cancellation</h2>
<p>You can cancel anytime from your account (or by emailing us). Cancellation stops all future renewals immediately; you keep access until the end of the period you've already paid for. Teacher/institute plans can likewise be cancelled to stop the next renewal.</p>
<h2>Refunds</h2>
<p>Because {BRAND} is a digital service with a genuine free trial that lets you evaluate it before paying, fees already charged for the <b>current</b> billing period are generally <b>non-refundable</b>. However, we play fair: if you were <b>charged in error</b>, charged <b>after cancelling</b>, or believe there are genuine exceptional circumstances, email <a href="mailto:{EMAIL}">{EMAIL}</a> within <b>7 days</b> of the charge and we will review it in good faith. Approved refunds go back to the original payment method, typically within 5–7 business days. The one-time Exam Pass, once its access has begun, is non-refundable except for a duplicate/erroneous charge.</p>
{_FOOT}
""",
    },

    "disclaimer": {
        "title": "Content &amp; Accuracy Disclaimer",
        "html": f"""
<p>Please read this carefully — it sets out honestly what {BRAND} does and does not claim.</p>
<h2>A practice tool, not a guarantee</h2>
<p>{BRAND} is a <b>preparation and practice aid</b>. Practising here does <b>not</b> guarantee any particular score, rank, qualification, or admission in any examination. Your result depends on many factors outside our control.</p>
<h2>Not affiliated with any exam authority</h2>
<p>{BRAND} is an independent product of {COMPANY}. We are <b>not affiliated with, sponsored by, authorised by, or endorsed by</b> any examination body, board, or authority — including (without limitation) the NTA, CBSE, UPSC, IBPS, SBI, or any state or national board. Exam names such as {_EXAM_NAMES} are the trademarks of their respective owners and are used <b>only to identify the exam you are preparing for</b>. All such trademarks remain the property of their owners.</p>
<h2>About the questions</h2>
<p>Our bank contains (a) <b>real past-paper questions</b> transcribed from publicly available official papers, provided for study, and (b) <b>new questions authored by our AI engine</b> in the style/pattern of an exam. AI-authored questions and their solutions are generated automatically and, despite our checks, <b>may occasionally contain factual, numerical, or key errors</b>. Always cross-check important facts against your official syllabus and standard textbooks. If you spot a mistake, please tell us so we can fix it — this feedback is how the bank improves.</p>
<h2>Language</h2>
<p>Questions are offered in English and हिंदी; automated translations may not be perfect. The English version prevails if there is any conflict.</p>
{_FOOT}
""",
    },

    "contact": {
        "title": "Contact Us",
        "html": f"""
<p>We'd genuinely like to hear from you — questions, bug reports in a question, or help with billing.</p>
<ul>
<li><b>Company:</b> {COMPANY} ({PARENT})</li>
<li><b>CIN:</b> {CIN} (RoC-Patna)</li>
<li><b>Email:</b> <a href="mailto:{EMAIL}">{EMAIL}</a></li>
<li><b>Phone / WhatsApp:</b> {PHONE}</li>
<li><b>Registered office:</b> {ADDRESS}</li>
<li><b>Grievance Officer:</b> {GRIEVANCE_OFFICER} (for privacy and other complaints)</li>
</ul>
<p>We aim to respond to all queries within 1–2 business days, and to resolve formal grievances within 30 days.</p>
{_FOOT}
""",
    },
}
