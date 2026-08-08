#!/usr/bin/env python3
"""Build Rohan's July 2026 salary slip as a branded HTML letterhead -> Chrome/PDF.
Mirrors the branding of build_pdf.py (the appointment package)."""
import base64, pathlib

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
logo_b64 = base64.b64encode((REPO / "brand_logo/pack/trigunai_mark_chrome.png").read_bytes()).decode()
LOGO = f"data:image/png;base64,{logo_b64}"

# ---- Pay computation (July 2026, joined 16 Jul; 16 of 31 days) ----
RETAINER_FULL = 10000
DAYS_IN_MONTH = 31
DAYS_WORKED = 16
retainer = round(RETAINER_FULL * DAYS_WORKED / DAYS_IN_MONTH)   # 5161
visits = 3
visit_pay = visits * 200                                         # 600
gross = retainer + visit_pay                                     # 5761
reimb_card = 500
tds = 0
deductions = tds
net = gross + reimb_card - deductions                            # 6261

# amount in words
NET_WORDS = "Six Thousand Two Hundred Sixty-One Rupees Only"

# Employee identity — from submitted Aadhaar + PAN (Aadhaar masked to last-4 for privacy)
PAN = "TCZPS8680A"
AADHAAR = "XXXX XXXX 9647"
# Bank details from Rohan (for the transfer)
BANK_AC = "1749907964"
BANK_IFSC = "KKBK0005671"
BANK_NAME = "Kotak Mahindra Bank &mdash; Patna, Gola Road"

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
@page {{ size: A4; margin: 16mm 16mm 20mm 16mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color:#1f2330; font-size:10.7pt; line-height:1.5; margin:0; }}
.letterhead {{ display:flex; align-items:center; gap:16px; }}
.letterhead .mark {{ width:66px; height:auto; }}
.co-name {{ font-size:15.5pt; font-weight:700; letter-spacing:.2px; color:#12141c; }}
.co-sub {{ font-size:8pt; color:#5a5f6e; margin-top:2px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227 0%,#8a6d1a 55%,#c9a227 100%); margin:9px 0 14px; border-radius:2px; }}
h1.title {{ font-size:13pt; font-weight:700; text-align:center; letter-spacing:1.5px; text-transform:uppercase; margin:4px 0 2px; color:#12141c; }}
.subtitle {{ text-align:center; font-size:9pt; color:#5a5f6e; margin-bottom:12px; }}
.refrow {{ display:flex; justify-content:space-between; font-size:9pt; color:#5a5f6e; border-bottom:1px solid #e6e2d2; padding-bottom:8px; margin-bottom:14px; }}
h2 {{ font-size:11pt; font-weight:700; color:#8a6d1a; margin:16px 0 5px; border-left:3px solid #c9a227; padding-left:8px; }}
table {{ width:100%; border-collapse:collapse; margin:8px 0; font-size:9.9pt; }}
th, td {{ border:1px solid #d7d3c4; padding:6px 9px; text-align:left; vertical-align:top; }}
th {{ background:#f6f2e6; color:#12141c; font-weight:700; }}
td.num, th.num {{ text-align:right; white-space:nowrap; }}
.kv {{ width:100%; border-collapse:collapse; margin:4px 0 6px; font-size:9.7pt; }}
.kv td {{ border:1px solid #e6e2d2; padding:5px 9px; }}
.kv td.k {{ background:#f8f7f2; color:#5a5f6e; width:26%; font-weight:600; }}
tr.total td {{ background:#f6f2e6; font-weight:700; color:#12141c; }}
tr.net td {{ background:#fbf6e6; font-weight:700; font-size:11pt; color:#12141c; border-color:#e3cf87; }}
.callout {{ background:#fbf6e6; border:1px solid #e3cf87; border-radius:5px; padding:9px 12px; margin:12px 0; font-size:9.7pt; }}
.small {{ font-size:8.5pt; color:#5a5f6e; }}
.two {{ display:flex; justify-content:space-between; gap:40px; margin-top:34px; }}
.sigline {{ margin-top:34px; border-top:1px solid #12141c; width:230px; padding-top:3px; font-size:9.5pt; }}
.pagefoot {{ border-top:1px solid #d7d3c4; margin-top:26px; padding-top:6px; font-size:7.5pt; color:#9296a2; text-align:center; }}
strong {{ color:#12141c; }}
.cols {{ display:flex; gap:18px; }}
.cols > div {{ flex:1; }}
</style></head><body>

{LETTERHEAD}
<h1 class="title">Salary Slip</h1>
<div class="subtitle">Pay Period: 16 &ndash; 31 July 2026 &nbsp;&middot;&nbsp; (First month &mdash; date of joining 16 July 2026)</div>
<div class="refrow"><span>Payslip No: TAI/PAY/2026-07/ROHAN-01</span><span>Pay date: 31 July 2026</span></div>

<div class="cols">
  <div>
    <table class="kv">
      <tr><td class="k">Employee name</td><td><strong>Rohan Kr. Saurabh</strong></td></tr>
      <tr><td class="k">Employee ID</td><td>TAI-FS-001</td></tr>
      <tr><td class="k">Designation</td><td>Field Sales &amp; Onboarding Associate &mdash; Patna</td></tr>
      <tr><td class="k">Date of joining</td><td>16 July 2026</td></tr>
      <tr><td class="k">Reporting to</td><td>Deepak Kumar (Founder &amp; CEO)</td></tr>
    </table>
  </div>
  <div>
    <table class="kv">
      <tr><td class="k">PAN</td><td>{PAN}</td></tr>
      <tr><td class="k">Aadhaar</td><td>{AADHAAR}</td></tr>
      <tr><td class="k">Bank A/C No.</td><td>{BANK_AC}</td></tr>
      <tr><td class="k">IFSC</td><td>{BANK_IFSC}</td></tr>
      <tr><td class="k">Bank</td><td>{BANK_NAME}</td></tr>
    </table>
  </div>
</div>

<h2>Earnings</h2>
<table>
<tr><th>Component</th><th>Basis</th><th class="num">Amount (&#8377;)</th></tr>
<tr><td>Fixed monthly retainer <span class="small">(pro-rated)</span></td><td>&#8377;10,000 &times; 16/31 days worked</td><td class="num">5,161</td></tr>
<tr><td>Field-visit pay</td><td>3 verified in-person visits &times; &#8377;200</td><td class="num">600</td></tr>
<tr class="total"><td colspan="2">Gross Earnings</td><td class="num">5,761</td></tr>
</table>

<h2>Reimbursements <span class="small" style="font-weight:400">(non-taxable, against approval)</span></h2>
<table>
<tr><th>Item</th><th>Basis</th><th class="num">Amount (&#8377;)</th></tr>
<tr><td>Business-card printing</td><td>Approved out-of-pocket expense</td><td class="num">500</td></tr>
<tr class="total"><td colspan="2">Total Reimbursements</td><td class="num">500</td></tr>
</table>

<h2>Deductions</h2>
<table>
<tr><th>Component</th><th>Basis</th><th class="num">Amount (&#8377;)</th></tr>
<tr><td>TDS</td><td>Not applicable at this level</td><td class="num">0</td></tr>
<tr class="total"><td colspan="2">Total Deductions</td><td class="num">0</td></tr>
</table>

<table style="margin-top:14px;">
<tr class="net"><td>NET PAYABLE (Gross + Reimbursements &minus; Deductions)</td><td class="num">&#8377; 6,261</td></tr>
</table>
<div class="callout"><strong>Amount in words:</strong> {NET_WORDS}.<br>
<span class="small">Paid by bank transfer / UPI to the employee&rsquo;s registered account on 31 July 2026.</span></div>

<p class="small">Notes: Conversion incentive (&#8377;1,100 / successful onboarding) and converted-visit bonus (&#8377;500) are <strong>nil this period</strong> &mdash; no conversion cleared in July. All amounts are per the Letter of Appointment dated 14 July 2026 (Ref: TAI/HR/2026/ROHAN-01) and Annexure&nbsp;A. Payouts are against verified records only. This is a computer-generated payslip; PAN / Aadhaar / bank fields are completed on receipt of the employee&rsquo;s submitted documents.</p>

<div class="two">
  <div>
    <div class="small">For TrigunAI Innovations Private Limited</div>
    <div class="sigline">Deepak Kumar &mdash; Founder &amp; CEO<br><span class="small">Date:</span></div>
  </div>
  <div>
    <div class="small">Received by Employee</div>
    <div class="sigline">Rohan Kr. Saurabh<br><span class="small">Date:</span></div>
  </div>
</div>

<div class="pagefoot">TrigunAI Innovations Private Limited &middot; CIN U86909BR2025PTC078945 &middot; Patna, Bihar &middot; This payslip is issued for the pay period stated above.</div>

</body></html>"""

out = REPO / "team/rohan/Salary_Slip_Rohan_July2026.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out)
