"""Policy pages required for Razorpay live activation + general compliance.
Served by /terms /privacy /refund /contact via a shared template.
Entity: TRIGUNAI INNOVATIONS PRIVATE LIMITED. Update CONTACT_* + ADDRESS as needed.
"""

COMPANY = "TRIGUNAI INNOVATIONS PRIVATE LIMITED"
BRAND = "TrigunAI"
SITE = "acharya.trigunai.com"
EMAIL = "deepak@trigunai.com"
PHONE = ""                       # add a support phone if you have one (Razorpay likes one)
ADDRESS = "India"                # replace with the registered office address
UPDATED = "27 June 2026"
PRICE = 499
TRIAL_DAYS = 7

_FOOT = f"<p class='upd'>Last updated: {UPDATED}. Questions? Email <a href='mailto:{EMAIL}'>{EMAIL}</a>.</p>"

LEGAL = {
    "terms": {
        "title": "Terms of Service",
        "html": f"""
<p>Welcome to {BRAND} ({SITE}), operated by {COMPANY} ("we", "us"). By creating an account or using the platform you agree to these Terms.</p>
<h2>1. The service</h2>
<p>{BRAND} provides access to online, interactive learning courses and an AI tutor. Course content and features may evolve over time.</p>
<h2>2. Accounts</h2>
<p>You sign in with your email via a one-time login link. You are responsible for keeping access to your email secure. One account is for one learner.</p>
<h2>3. Subscriptions, free trial &amp; billing</h2>
<p>Access is offered on a monthly subscription of <b>₹{PRICE}/month</b>. New learners may start a <b>{TRIAL_DAYS}-day free trial</b>. If you add a payment method, you will be automatically charged ₹{PRICE} at the end of the trial and monthly thereafter, until you cancel. If you start without a payment method, your access ends after the free trial unless you subscribe.</p>
<h2>4. Cancellation</h2>
<p>You can cancel anytime from your Account page. Cancellation stops future renewals; you keep access until the end of your current paid period. See our <a href="/refund">Refund &amp; Cancellation Policy</a>.</p>
<h2>5. Acceptable use</h2>
<p>Do not share your account, resell or redistribute course content, attempt to disrupt the service, or use it unlawfully. We may suspend accounts that violate these Terms.</p>
<h2>6. Intellectual property</h2>
<p>All course content, code, and materials are owned by {COMPANY} and provided for your personal learning only.</p>
<h2>7. Disclaimer &amp; limitation of liability</h2>
<p>The service is provided "as is". To the maximum extent permitted by law, {COMPANY} is not liable for indirect or consequential damages. Our total liability is limited to the amount you paid in the prior 12 months.</p>
<h2>8. Changes &amp; governing law</h2>
<p>We may update these Terms; material changes will be notified on this page. These Terms are governed by the laws of India, with jurisdiction in the courts of India.</p>
{_FOOT}
""",
    },
    "privacy": {
        "title": "Privacy Policy",
        "html": f"""
<p>{COMPANY} ("we") operates {BRAND} ({SITE}). This policy explains what we collect and how we use it.</p>
<h2>1. What we collect</h2>
<ul>
<li><b>Account data</b> — your email and name.</li>
<li><b>Learning data</b> — your course, lesson progress, and optional profile details you share to personalize your learning.</li>
<li><b>Payment data</b> — handled by our payment processor <b>Razorpay</b>. We do not store your card or UPI details; we store only your subscription status and billing dates.</li>
<li><b>Technical data</b> — a session cookie to keep you signed in.</li>
</ul>
<h2>2. How we use it</h2>
<p>To provide and personalize your courses and AI tutor, manage your subscription, and communicate service emails (such as your login link and billing notices).</p>
<h2>3. Who we share with</h2>
<p>We share data only with processors that run the service: <b>Razorpay</b> (payments), <b>Microsoft Azure</b> (hosting), and our email provider for transactional email. We do not sell your data.</p>
<h2>4. Data retention &amp; your rights</h2>
<p>We keep your data while your account is active. You may request access to, correction of, or deletion of your data by emailing <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
<h2>5. Security</h2>
<p>We use industry-standard measures (encrypted transport, hosted on Azure). No method is 100% secure, but we work to protect your data.</p>
{_FOOT}
""",
    },
    "refund": {
        "title": "Refund &amp; Cancellation Policy",
        "html": f"""
<p>This policy applies to {BRAND} subscriptions ({SITE}), operated by {COMPANY}.</p>
<h2>Free trial</h2>
<p>New learners get a <b>{TRIAL_DAYS}-day free trial</b>. If you cancel during the trial, <b>you are not charged anything</b>.</p>
<h2>Cancellation</h2>
<p>You can cancel anytime from your <a href="/account">Account</a> page in one click. Cancellation stops all future renewals. You keep access until the end of your current paid month.</p>
<h2>Refunds</h2>
<p>Because this is a monthly digital subscription with a free trial that lets you fully evaluate the product before paying, fees already charged for the current billing month are generally non-refundable. However, if you were charged in error, or believe there are exceptional circumstances, email us at <a href="mailto:{EMAIL}">{EMAIL}</a> within <b>7 days</b> of the charge and we will review your request fairly. Approved refunds are returned to the original payment method within 5–7 business days.</p>
{_FOOT}
""",
    },
    "contact": {
        "title": "Contact Us",
        "html": f"""
<p>We'd love to hear from you.</p>
<ul>
<li><b>Company:</b> {COMPANY}</li>
<li><b>Email:</b> <a href="mailto:{EMAIL}">{EMAIL}</a></li>
{f'<li><b>Phone:</b> {PHONE}</li>' if PHONE else ''}
<li><b>Address:</b> {ADDRESS}</li>
</ul>
<p>We aim to respond to all queries within 1–2 business days.</p>
{_FOOT}
""",
    },
}
