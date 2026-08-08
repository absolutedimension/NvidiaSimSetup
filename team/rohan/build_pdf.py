#!/usr/bin/env python3
"""Build the Rohan appointment package as a branded HTML letterhead, ready for Chrome->PDF."""
import base64, pathlib

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
logo_b64 = base64.b64encode((REPO / "brand_logo/pack/trigunai_mark_chrome.png").read_bytes()).decode()
LOGO = f"data:image/png;base64,{logo_b64}"

LETTERHEAD = f"""
<div class="letterhead">
  <img class="mark" src="{LOGO}" alt="TrigunAI">
  <div class="co">
    <div class="co-name">TRIGUNAI INNOVATIONS PRIVATE LIMITED</div>
    <div class="co-sub">Regd. Office: C/O Smt. Rita Yadav, Shivajee Nagar, Sadakat, Patliputra, Patna, Bihar &ndash; 800013</div>
    <div class="co-sub">CIN: U86909BR2025PTC078945 &nbsp;&middot;&nbsp; RoC: Patna &nbsp;&middot;&nbsp; deepak@trigunai.com &nbsp;&middot;&nbsp; trigunai.com</div>
  </div>
</div>
<div class="rule"></div>
"""

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 16mm 16mm 22mm 16mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color:#1f2330; font-size:10.7pt; line-height:1.5; margin:0; }}
.letterhead {{ display:flex; align-items:center; gap:16px; }}
.letterhead .mark {{ width:66px; height:auto; }}
.co-name {{ font-size:15.5pt; font-weight:700; letter-spacing:.2px; color:#12141c; }}
.co-sub {{ font-size:8pt; color:#5a5f6e; margin-top:2px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227 0%,#8a6d1a 55%,#c9a227 100%); margin:9px 0 16px; border-radius:2px; }}
h1.title {{ font-size:13pt; font-weight:700; text-align:center; letter-spacing:1.5px; text-transform:uppercase; margin:6px 0 4px; color:#12141c; }}
.refrow {{ display:flex; justify-content:space-between; font-size:9pt; color:#5a5f6e; border-bottom:1px solid #e6e2d2; padding-bottom:8px; margin-bottom:14px; }}
h2 {{ font-size:11.5pt; font-weight:700; color:#8a6d1a; margin:16px 0 5px; border-left:3px solid #c9a227; padding-left:8px; }}
h3 {{ font-size:10.5pt; margin:12px 0 4px; color:#12141c; }}
p {{ margin:6px 0; }}
ul, ol {{ margin:5px 0 8px 0; padding-left:20px; }}
li {{ margin:3px 0; }}
table {{ width:100%; border-collapse:collapse; margin:8px 0; font-size:9.7pt; }}
th, td {{ border:1px solid #d7d3c4; padding:6px 8px; text-align:left; vertical-align:top; }}
th {{ background:#f6f2e6; color:#12141c; font-weight:700; }}
.addr {{ background:#f8f7f2; border:1px solid #e6e2d2; border-radius:5px; padding:10px 12px; margin:10px 0; }}
.callout {{ background:#fbf6e6; border:1px solid #e3cf87; border-radius:5px; padding:9px 12px; margin:10px 0; font-size:10pt; }}
.sig {{ margin-top:26px; }}
.sigline {{ margin-top:34px; border-top:1px solid #12141c; width:230px; padding-top:3px; font-size:9.5pt; }}
.two {{ display:flex; justify-content:space-between; gap:40px; margin-top:26px; }}
.page {{ page-break-after:always; }}
.page:last-child {{ page-break-after:auto; }}
table, tr {{ page-break-inside:avoid; }}
h2, h3 {{ page-break-after:avoid; }}
.pagefoot {{ border-top:1px solid #d7d3c4; margin-top:22px; padding-top:5px; font-size:7.5pt; color:#9296a2; text-align:center; }}
strong {{ color:#12141c; }}
.small {{ font-size:8.5pt; color:#5a5f6e; }}
</style></head><body>

<!-- ============ PAGE 1: APPOINTMENT LETTER ============ -->
<div class="page">
{LETTERHEAD}
<h1 class="title">Letter of Appointment</h1>
<div class="refrow"><span>Date: 14 July 2026</span><span>Ref: TAI/HR/2026/ROHAN-01</span></div>

<div class="addr">
<strong>To,</strong><br>
<strong>Mr. Rohan Kr. Saurabh</strong><br>
Digha Atal Path, Ganga Vihar Colony, Patna &ndash; 800011<br>
Phone: 7667177063 &nbsp;&middot;&nbsp; Email: rohankrsaurabh@gmail.com
</div>

<p>Dear Rohan,</p>
<p>Congratulations. Following our discussion, we are pleased to appoint you in <strong>TrigunAI Innovations Private Limited</strong> (&ldquo;the Company&rdquo;) on the terms below. This is a field sales and customer-onboarding role for our <strong>Acharya</strong> AI-tutor product in the Patna region.</p>

<h2>1. Position &amp; Reporting</h2>
<ul>
<li><strong>Designation:</strong> Field Sales &amp; Onboarding Associate &mdash; Patna</li>
<li><strong>Reporting to:</strong> Deepak Kumar (Founder &amp; CEO)</li>
<li><strong>Location:</strong> Patna (field-based) + assigned outstation institutes as agreed</li>
<li><strong>Date of joining:</strong> 16 July 2026</li>
<li><strong>Employment type:</strong> Full-time, on probation (see &sect;6)</li>
</ul>

<h2>2. Role &amp; Responsibilities</h2>
<ol>
<li>Visit tuition teachers / coaching institutes from the Company&rsquo;s assigned lead list, in person, in and around Patna.</li>
<li>Call assigned leads, explain the Acharya offer, and hold discovery conversations using the Company&rsquo;s script.</li>
<li>Onboard interested teachers onto the Acharya platform (free pilot &rarr; paid plan) and assist their setup.</li>
<li>Log every call and visit the <strong>same day</strong> in the Company tracker (format provided).</li>
<li>Collect and report teacher pain-points, objections, and competitive information truthfully.</li>
<li>Represent TrigunAI and the Acharya product <strong>honestly</strong> &mdash; no exaggerated or false claims. Misrepresentation to a customer is a serious breach.</li>
</ol>

<h2>3. Compensation Structure</h2>
<p>Your earnings have a <strong>fixed</strong> part and a <strong>variable (incentive)</strong> part. Full details are in <strong>Annexure&nbsp;A</strong>. In summary:</p>
<table>
<tr><th>Component</th><th>Amount</th><th>Basis</th></tr>
<tr><td><strong>Fixed monthly retainer</strong></td><td><strong>&#8377;10,000 / month</strong></td><td>Paid monthly, subject to meeting the minimum activity bar in Annexure&nbsp;A</td></tr>
<tr><td><strong>Field-visit pay</strong></td><td><strong>&#8377;200 per verified visit</strong></td><td>Paid regardless of outcome (proof + same-day log; cap 25/month)</td></tr>
<tr><td><strong>Converted-visit bonus</strong></td><td><strong>+ &#8377;500 per converted visit</strong></td><td>Extra, when a verified visit becomes a paying customer</td></tr>
<tr><td><strong>Conversion incentive</strong></td><td><strong>&#8377;1,100 per successful onboarding</strong></td><td>Paid when a teacher you onboarded makes their <strong>first cleared payment</strong></td></tr>
</table>
<p>There is <strong>no upper limit</strong> on the conversion incentive &mdash; the more teachers you convert to paying customers, the more you earn.</p>

<h2>4. Payment Terms</h2>
<ul>
<li>The retainer, visit pay, and any incentives for a month are computed at month-end and paid <strong>by the 7th of the following month</strong>, by bank transfer to your registered account.</li>
<li>All amounts are subject to applicable statutory deductions (e.g. TDS), if and when applicable.</li>
<li>Incentives/allowances are payable <strong>only against verified records</strong> (call log, visit proof, and confirmed payment from the client).</li>
</ul>

<h2>5. Money-Handling Rule</h2>
<p>You are <strong>not authorised to collect cash or payments from any customer</strong> on the Company&rsquo;s behalf. All customer payments must be made <strong>directly to the official TrigunAI account/link</strong> only. Any in-person collection of money is strictly prohibited and is grounds for immediate termination.</p>

<h2>6. Probation &amp; Notice</h2>
<ul>
<li><strong>Probation:</strong> first <strong>3 months</strong> from joining. During probation either party may end this engagement with <strong>7 days&rsquo;</strong> written notice.</li>
<li><strong>After confirmation:</strong> either party may end with <strong>30 days&rsquo;</strong> written notice (or salary in lieu, at the Company&rsquo;s discretion).</li>
<li>The Company may terminate without notice for misconduct, dishonesty, misrepresentation to customers, or misuse of Company data.</li>
</ul>

<h2>7. Confidentiality &amp; Data Protection</h2>
<ul>
<li>All leads, teacher contacts, student data, pricing, scripts, and materials you access are the <strong>confidential property of TrigunAI</strong>, to be used <strong>only</strong> for your work for the Company.</li>
<li>You will <strong>not</strong> share, sell, copy, or use these leads/data for yourself or any third party, during or after your engagement.</li>
<li>On exit, you will return / delete all Company data, contacts, and materials in your possession.</li>
</ul>

<h2>8. Conduct</h2>
<ul>
<li>You will conduct yourself professionally and courteously with all teachers, institutes, and their students/parents.</li>
<li>You will not make any commitment (pricing, features, timelines) on the Company&rsquo;s behalf beyond the official offer, without written approval.</li>
</ul>

<h2>9. Documents to be Submitted</h2>
<p>See <strong>Annexure&nbsp;B</strong>. Your appointment is subject to submission and verification of a valid Aadhaar, PAN, and bank details.</p>

<p style="margin-top:14px;">Please sign both copies of this letter and Annexure&nbsp;A, attach the documents in Annexure&nbsp;B, and return one signed set to the Company.</p>

<div class="two">
  <div>
    <div class="small">For TrigunAI Innovations Private Limited</div>
    <div class="sigline">Deepak Kumar &mdash; Founder &amp; CEO<br><span class="small">Date:</span></div>
  </div>
  <div>
    <div class="small">Accepted by Employee</div>
    <div class="sigline">Rohan Kr. Saurabh<br><span class="small">Date: &nbsp; Place:</span></div>
  </div>
</div>
</div>

<!-- ============ PAGE 2: ANNEXURE A ============ -->
<div class="page">
{LETTERHEAD}
<h1 class="title">Annexure A &mdash; Compensation &amp; Incentive Structure</h1>
<div class="refrow"><span>Employee: Rohan Kr. Saurabh</span><span>Field Sales &amp; Onboarding Associate &mdash; Patna</span></div>
<p class="small">This annexure forms part of the Letter of Appointment dated 14 July 2026. It defines exactly how each rupee is earned, so there is never a dispute at month-end. Both parties sign it.</p>

<h2>A.1 &nbsp; Fixed Monthly Retainer &mdash; &#8377;10,000</h2>
<ul>
<li>Paid every month for meeting the <strong>minimum activity bar</strong>: at least <strong>100 verified calls/week</strong> to assigned leads, <strong>and same-day logging</strong> of every call and visit.</li>
<li>If the activity bar is not met for reasons within your control, the Company may pro-rate the retainer (agreed in writing before any deduction).</li>
<li>The retainer is your base for showing up and doing the work &mdash; it is not tied to a single conversion.</li>
</ul>

<h2>A.2 &nbsp; Conversion Incentive &mdash; &#8377;1,100 per successful onboarding</h2>
<p>The core earning, and it is <strong>uncapped</strong>. &ldquo;Successful onboarding&rdquo; means ALL of:</p>
<ol>
<li>A teacher/institute <strong>you</strong> sourced or handled agrees to the Acharya plan, <strong>and</strong></li>
<li>Their Acharya instance is <strong>set up and live</strong>, <strong>and</strong></li>
<li>Their <strong>first monthly payment (&#8377;4,999) is received and cleared</strong> in the official TrigunAI account.</li>
</ol>
<ul>
<li>The &#8377;1,100 is credited in the month the first payment clears.</li>
<li>A free 14-day pilot that never pays is <strong>not</strong> a conversion &mdash; no incentive is due for it.</li>
<li>If a converted teacher cancels/refunds within the first payment cycle, that incentive may be reversed/withheld.</li>
</ul>

<h2>A.3 &nbsp; Field-Visit Pay &mdash; &#8377;200 per visit + &#8377;500 bonus on conversion</h2>
<p><strong>(a) Fixed visit pay &mdash; &#8377;200 per verified visit (paid regardless of outcome).</strong> A visit is &ldquo;verified&rdquo; and paid only if:</p>
<ol>
<li>The institute is on the Company&rsquo;s <strong>assigned/approved lead list</strong> (not self-picked, unless pre-approved), <strong>and</strong></li>
<li>You submit <strong>proof</strong>: a photo at the institute (board/nameplate visible) <strong>plus</strong> the visit form &mdash; institute name, owner name, phone, discussion, outcome, <strong>and</strong></li>
<li>The visit is <strong>logged the same day</strong>.</li>
</ol>
<p class="small">Monthly cap on fixed visit pay: up to <strong>25 verified visits/month (&#8377;5,000 max)</strong>. Genuine visits beyond 25 may be approved case-by-case in writing.</p>
<p><strong>(b) Converted-visit bonus &mdash; extra &#8377;500</strong> when a verified in-person visit becomes a successful onboarding under A.2 (first &#8377;4,999 cleared). Uncapped.</p>
<table>
<tr><th>Outcome</th><th>Pay</th></tr>
<tr><td>Verified visit, did <strong>not</strong> convert</td><td><strong>&#8377;200</strong></td></tr>
<tr><td>Verified visit that <strong>converts</strong></td><td>&#8377;200 + &#8377;500 + &#8377;1,100 = <strong>&#8377;1,800</strong></td></tr>
<tr><td>Conversion closed <strong>on phone only</strong> (no visit)</td><td><strong>&#8377;1,100</strong></td></tr>
</table>

<h2>A.4 &nbsp; Illustrative Monthly Earnings <span class="small">(example only &mdash; not a guarantee)</span></h2>
<table>
<tr><th>Scenario</th><th>Retainer</th><th>Visit pay</th><th>Convert bonus</th><th>Onboard</th><th>Total</th></tr>
<tr><td>Ramp-up (15 visits, 2 convert via visit)</td><td>&#8377;10,000</td><td>&#8377;3,000</td><td>&#8377;1,000</td><td>&#8377;2,200</td><td><strong>&#8377;16,200</strong></td></tr>
<tr><td>Strong (25 visits, 5 convert: 3 visit + 2 phone)</td><td>&#8377;10,000</td><td>&#8377;5,000</td><td>&#8377;1,500</td><td>&#8377;5,500</td><td><strong>&#8377;22,000</strong></td></tr>
<tr><td>Big (25 visits, 10 convert: 6 visit + 4 phone)</td><td>&#8377;10,000</td><td>&#8377;5,000</td><td>&#8377;3,000</td><td>&#8377;11,000</td><td><strong>&#8377;29,000</strong></td></tr>
</table>

<h2>A.5 &nbsp; General</h2>
<ul>
<li>All figures are gross and subject to statutory deductions (e.g. TDS) if/when applicable.</li>
<li>Payouts are against <strong>verified records only</strong> (call log + visit proof + confirmed cleared payment).</li>
<li>The Company may revise this structure with <strong>15 days&rsquo; written notice</strong>; already-earned incentives are protected.</li>
</ul>

<div class="two">
  <div><div class="sigline">For TrigunAI Innovations Pvt Ltd<br>Deepak Kumar &mdash; Founder &amp; CEO<br><span class="small">Date:</span></div></div>
  <div><div class="sigline">Accepted &mdash; Rohan Kr. Saurabh<br><span class="small">Date:</span></div></div>
</div>
</div>

<!-- ============ PAGE 3: ANNEXURE B ============ -->
<div class="page">
{LETTERHEAD}
<h1 class="title">Annexure B &mdash; Joining Documents &amp; Onboarding Checklist</h1>
<div class="refrow"><span>Employee: Rohan Kr. Saurabh</span><span>Field Sales &amp; Onboarding Associate &mdash; Patna</span></div>

<h2>Part 1 &mdash; Documents Rohan submits <span class="small">(self-attested copies)</span></h2>
<ul>
<li>&#9744; <strong>Aadhaar card</strong> &mdash; front &amp; back copy (address proof + identity)</li>
<li>&#9744; <strong>PAN card</strong> &mdash; copy (for TDS/tax + bank transfer)</li>
<li>&#9744; <strong>Passport-size photograph</strong> &times; 2</li>
<li>&#9744; <strong>Bank account details</strong> &mdash; cancelled cheque or passbook first-page copy (name, account no., IFSC, branch)</li>
<li>&#9744; <strong>Signed Appointment Letter</strong> (letter + Annexure A) returned to Company</li>
<li>&#9744; <strong>Emergency contact</strong> &mdash; name, relation, phone</li>
<li>&#9744; <span class="small">(Optional)</span> One reference from a prior employer (Ruban Memorial Hospital / Dezire World)</li>
</ul>

<h2>Part 2 &mdash; What the Company provides <span class="small">(Day 1)</span></h2>
<ul>
<li>&#9744; Assigned <strong>lead list</strong> (Patna cluster first)</li>
<li>&#9744; The <strong>call script</strong> + <strong>offer one-pager</strong> (Acharya pitch)</li>
<li>&#9744; The <strong>objection cheat-sheet</strong></li>
<li>&#9744; Access to the <strong>live demo</strong> (WhatsApp Acharya instance)</li>
<li>&#9744; The <strong>call/visit log</strong> template + same-day logging process</li>
<li>&#9744; A short product walkthrough so he can demo confidently</li>
<li>&#9744; Company <strong>payment link/QR</strong> to give teachers (he never collects cash)</li>
</ul>

<h2>Part 3 &mdash; Rohan&rsquo;s starting Patna lead list</h2>
<p class="small">Already sent onboarding template (warmest &mdash; visit/call first):</p>
<table>
<tr><th>Institute</th><th>Phone</th><th>Focus</th></tr>
<tr><td>Goal Institute</td><td>91756 4902125</td><td>Exam prep</td></tr>
<tr><td>Perfect Mathematics Classes</td><td>91915 5962008</td><td>Maths</td></tr>
<tr><td>Physics for IIT-JEE (Er. M.K. Thakur)</td><td>91700 4179675</td><td>Physics JEE</td></tr>
<tr><td>Tution Time Home Tuition Centre</td><td>91778 3835069</td><td>Tuition</td></tr>
</table>
<p class="small">Accepted a demo on Maya&rsquo;s call (Patna cluster):</p>
<table>
<tr><th>Institute</th><th>Phone</th><th>Focus</th></tr>
<tr><td>MCM IIT-JEE &amp; NEET Academy</td><td>91799 2250244</td><td>JEE+NEET</td></tr>
<tr><td>Base Point</td><td>91797 9919133</td><td>NEET (interested &mdash; callback)</td></tr>
<tr><td>Delta Success Point</td><td>91790 3454942</td><td>Exam prep</td></tr>
</table>

<h2>Part 4 &mdash; First-week plan</h2>
<ul>
<li>Day 1: product + script training; shadow one call/demo with Deepak</li>
<li>Day 1&ndash;2: visit the 4 warmest Patna institutes in person (they already have the template)</li>
<li>Daily: log every call + visit same-day; end-of-day 2-line report to Deepak</li>
</ul>

<div class="sig">
<div class="small">Documents received &amp; verified by:</div>
<div class="sigline">Deepak Kumar &mdash; TrigunAI Innovations Pvt Ltd<br><span class="small">Date:</span></div>
</div>
</div>

</body></html>"""

out = REPO / "team/rohan/Appointment_Package_Rohan.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out)
