#!/usr/bin/env python3
"""Build Heena's appointment package on the SAME branded letterhead as Rohan's (team/rohan/build_pdf.py)."""
import base64, pathlib, subprocess

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
.dsbox {{ margin-top:18px; border:1px dashed #b9b3a0; border-radius:5px; padding:10px 12px; width:290px; font-size:8.5pt; color:#5a5f6e; }}
</style></head><body>

<!-- ============ PAGE 1: APPOINTMENT LETTER ============ -->
<div class="page">
{LETTERHEAD}
<h1 class="title">Letter of Appointment</h1>
<div class="refrow"><span>Date: 19 August 2026</span><span>Ref: TAI/HR/2026/HEENA-01</span></div>

<div class="addr">
<strong>To,</strong><br>
<strong>Ms. Heena Kouser</strong><br>
Patna, Bihar<br>
Email: h.raza20@gmail.com
</div>

<p>Dear Heena,</p>
<p>Congratulations. Following our discussion, we are pleased to appoint you in <strong>TrigunAI Innovations Private Limited</strong> (&ldquo;the Company&rdquo;) on the terms below. This is an inside-sales and client-relationship role for our <strong>Acharya</strong> assessment and exam-paper platform in the Patna region.</p>

<h2>1. Position &amp; Reporting</h2>
<ul>
<li><strong>Designation:</strong> Inside Sales &amp; Client Relationship Executive &mdash; Patna</li>
<li><strong>Reporting to:</strong> Deepak Kumar (Co-Founder, CEO &amp; CTO)</li>
<li><strong>Works alongside:</strong> Mr. Rohan Kr. Saurabh (field visits &amp; demos)</li>
<li><strong>Location:</strong> Patna &mdash; primarily phone-based; occasional in-person work as agreed</li>
<li><strong>Date of joining:</strong> 20 August 2026</li>
<li><strong>Employment type:</strong> Full-time, on probation (see &sect;6)</li>
</ul>

<h2>2. Role &amp; Responsibilities</h2>
<ol>
<li>Call coaching institutes from the Company&rsquo;s assigned list, qualify them, and <strong>book demo appointments</strong> for the field executive so that visits are made only to institutes worth the trip.</li>
<li>Follow up after every field visit and keep each institute warm between visits.</li>
<li>Get institutes <strong>registered and actively testing</strong> Acharya on its 14-day free trial, and keep them using it.</li>
<li>Report proven usage to the Founder, and share institute pain-points and objections truthfully.</li>
<li>Log every call the <strong>same day</strong> in the Company&rsquo;s shared institute ledger (format and tools provided).</li>
<li>Represent TrigunAI and the Acharya product <strong>honestly</strong> &mdash; no exaggerated or false claims about subjects, coverage or results. Misrepresentation to a customer is a serious breach.</li>
</ol>

<div class="callout">
<strong>Your success is measured by institutes whose students have actually taken a test</strong> &mdash; not by the number of calls made.
</div>

<h2>3. Compensation Structure</h2>
<p>Your earnings have a <strong>fixed</strong> part and a <strong>variable (incentive)</strong> part. Full details are in <strong>Annexure&nbsp;A</strong>. In summary:</p>
<table>
<tr><th>Component</th><th>Amount</th><th>When paid</th></tr>
<tr><td><strong>Fixed monthly</strong></td><td><strong>&#8377; 8,000</strong> per month</td><td>By the 7th of the following month</td></tr>
<tr><td><strong>Incentive &mdash; per conversion</strong></td><td><strong>&#8377; 2,500</strong> per institute</td><td>Monthly, with salary, for conversions verified that month</td></tr>
</table>

<h2>4. No collection of payment</h2>
<p>Acharya is offered to institutes on a <strong>14-day free trial</strong>. You are <strong>not required or expected to ask any institute for money, negotiate pricing, offer discounts, or collect payment</strong>. You may state the Company&rsquo;s published pricing openly and factually if asked. All commercial and payment discussions are handled by the Founder, separately, after an institute&rsquo;s trial.</p>

<h2>5. Working Days &amp; Hours</h2>
<ul>
<li>Monday to Saturday. Sundays and public holidays off.</li>
<li>Calling hours to be aligned with institute working hours, as mutually agreed.</li>
</ul>

<h2>6. Probation &amp; Review</h2>
<p>Your first <strong>three months</strong> are on probation. An honest review will be held at the end of your first <strong>six weeks</strong>, covering both what you have achieved and what support you need from the Company.</p>

<h2>7. Confidentiality &amp; Data Protection</h2>
<p>Institute contacts, student data, pricing, product information and internal materials are confidential and must not be shared outside the Company or used for any other purpose. <strong>Student personal data must be handled with particular care and never shared, copied or retained personally.</strong></p>

<h2>8. Notice Period</h2>
<p>Either party may end this engagement with <strong>15 days&rsquo; written notice</strong> during the first three months, and <strong>30 days&rsquo; written notice</strong> thereafter.</p>

<div class="pagefoot">TrigunAI Innovations Private Limited &middot; CIN U86909BR2025PTC078945 &middot; Letter of Appointment</div>
</div>

<!-- ============ PAGE 2: ANNEXURE A ============ -->
<div class="page">
{LETTERHEAD}
<h1 class="title">Annexure A &mdash; Compensation &amp; Onboarding</h1>
<div class="refrow"><span>Heena &mdash; Inside Sales &amp; Client Relationship Executive</span><span>Ref: TAI/HR/2026/HEENA-01</span></div>

<h2>A1. Fixed Component</h2>
<p><strong>&#8377; 8,000 per month</strong>, payable by the 7th of the following month, subject to applicable statutory deductions if and when applicable.</p>

<h2>A2. Incentive &mdash; what counts as a &ldquo;conversion&rdquo;</h2>
<div class="callout">
A <strong>conversion</strong> means an institute that has been <strong>registered on Acharya AND has run at least one test with its students</strong> &mdash; verified in the Company&rsquo;s system &mdash; where you were the person who drove it.
</div>
<p>This has been defined deliberately. Acharya opens on a 14-day free trial, so there is no payment at the time you do your work. Your incentive is therefore tied to a milestone you can genuinely control and see &mdash; an institute actually using the product. Whether that institute subscribes afterwards is the owner&rsquo;s decision and is handled by the Founder.</p>
<table>
<tr><th>Conversions in a month</th><th>Incentive earned</th><th>Total earnings that month</th></tr>
<tr><td>2</td><td>&#8377; 5,000</td><td>&#8377; 13,000</td></tr>
<tr><td>5</td><td>&#8377; 12,500</td><td>&#8377; 20,500</td></tr>
<tr><td>10</td><td>&#8377; 25,000</td><td>&#8377; 33,000</td></tr>
</table>
<p class="small">Illustrative only; not a guarantee or a target.</p>

<h2>A3. Tools provided</h2>
<ul>
<li><strong>Saathi</strong> &mdash; your own AI companion on WhatsApp. It plans your day with you, teaches you the product and the skills the role needs, keeps the institute record for you, tracks your progress and answers anything you ask, at any time.</li>
<li>The assigned calling list, call scripts, and access to the Acharya platform and the shared institute ledger.</li>
</ul>

<h2>A4. First-week plan</h2>
<ul>
<li><strong>Day 1&ndash;2:</strong> product training with Saathi &mdash; what Acharya is, what makes it different, what we do and do not cover. No calling yet.</li>
<li><strong>Day 3 onward:</strong> begin calling the assigned list; qualify and book demo appointments for the field executive.</li>
<li><strong>Daily:</strong> log every call the same day; short end-of-day check-in with Saathi.</li>
</ul>

<h2>A5. Acceptance</h2>
<p>Please sign and return a copy of this letter to confirm your acceptance of the terms set out above.</p>

<div class="two">
  <div>
    <div class="small">For and on behalf of<br>TrigunAI Innovations Private Limited</div>
    <div class="dsbox">
      <strong>Digitally signed by</strong><br>
      Deepak Kumar &mdash; Co-Founder, CEO &amp; CTO<br>
      <span class="small">(Digital Signature Certificate)</span>
    </div>
  </div>
  <div>
    <div class="small">Accepted by</div>
    <div class="sigline">Heena Kouser<br><span class="small">Signature &amp; Date</span></div>
  </div>
</div>

<div class="pagefoot">TrigunAI Innovations Private Limited &middot; CIN U86909BR2025PTC078945 &middot; Annexure A</div>
</div>

</body></html>"""

out_html = REPO / "team/heena/Appointment_Package_Heena.html"
out_html.write_text(HTML, encoding="utf-8")
out_pdf = REPO / "team/heena/Appointment_Letter_Heena.pdf"
for chrome in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium"):
    if pathlib.Path(chrome).exists():
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out_pdf}", out_html.as_uri()],
                       check=False, capture_output=True, timeout=180)
        break
print("wrote", out_html)
print("wrote", out_pdf, out_pdf.stat().st_size if out_pdf.exists() else "FAILED")
