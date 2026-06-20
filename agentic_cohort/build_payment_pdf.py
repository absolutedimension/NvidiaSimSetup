#!/usr/bin/env python3
"""Build the branded Enrolment & Payment PDF (HTML -> Chrome headless -> PDF). Dark theme."""
import base64, subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent
LOGO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/course_assets/logo/trigun_mark2.png")

# ---- EDIT before sharing --------------------------------------------------
WHATSAPP = "+91 XXXXXXXXXX"          # your WhatsApp number for payment confirmation
EMAIL    = "deepak@trigunai.com"
# ---------------------------------------------------------------------------

# --- Company / bank details (from records) ---
ACC_NAME = "TrigunAI Innovations Private Limited"
ACC_NO   = "50200088377205"
IFSC     = "HDFC0002643"
BANK     = "HDFC Bank"
ACC_TYPE = "Current"
PAN      = "AAMCT2881K"
GST      = "10AAMCT2881K1Z4"
CIN      = "U86909BR2025PTC078945"
ADDR     = "C/O Smt Rita Yadav, Shivajee Nagar Sadakat, Patliputra, Phulwari, Patna – 800013, Bihar"

logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ background:#08080c; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ font:11px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:#e7e7ef; }}
.page {{ padding:12mm 12mm 9mm; min-height:297mm; }}
.head {{ text-align:center; padding-bottom:12px; border-bottom:1px solid #23232f; }}
.head .mark {{ height:88px; }}
.head .wm {{ font-family:Arial,Helvetica,sans-serif; font-weight:800; letter-spacing:5px; font-size:16px; color:#eef0fe; margin-top:6px; }}
.head .wmsub {{ font-size:8px; letter-spacing:3px; color:#8a8a9c; margin-top:3px; }}
.pill {{ display:inline-block; font-size:9.5px; font-weight:700; letter-spacing:.9px; color:#b9a7ff;
  background:rgba(124,92,246,.12); border:1px solid rgba(124,92,246,.35); padding:4px 11px; border-radius:999px; margin:7px 0 7px; }}
.head h1 {{ font-size:21px; }}
.head p {{ color:#9494a8; font-size:11.5px; margin-top:4px; }}
h2 {{ font-size:12.5px; margin:16px 0 8px; color:#cfcfe0; }}
ul {{ list-style:none; }}
li {{ padding-left:15px; position:relative; margin-bottom:4px; font-size:10.5px; color:#bcbccf; }}
li::before {{ content:"✓"; position:absolute; left:0; color:#34d399; font-weight:700; }}
.plans {{ display:flex; gap:12px; margin-top:4px; }}
.plan {{ flex:1; background:#13131c; border:1px solid #23232f; border-radius:12px; padding:16px; position:relative; }}
.plan.best {{ border-color:#7c5cf6; }}
.plan .tag {{ position:absolute; top:-10px; left:14px; font-size:9px; font-weight:800; letter-spacing:.5px;
  background:linear-gradient(90deg,#6366f1,#a855f7); color:#fff; padding:3px 9px; border-radius:999px; }}
.plan h3 {{ font-size:12px; color:#9494a8; font-weight:600; }}
.plan .price {{ font-size:27px; font-weight:800; color:#f2f2f7; margin-top:3px; }}
.plan .price small {{ font-size:13px; color:#9494a8; font-weight:500; }}
.plan p {{ font-size:10px; color:#9494a8; margin-top:6px; }}
.acct {{ background:#101018; border:1px solid #23232f; border-radius:12px; padding:6px 16px; }}
.acct .r {{ display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px solid #1a1a24; }}
.acct .r:last-child {{ border-bottom:none; }}
.acct .k {{ color:#9494a8; font-size:10.5px; }}
.acct .v {{ font-weight:700; font-size:12.5px; color:#f2f2f7; letter-spacing:.3px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; font-size:9px; letter-spacing:.5px; text-transform:uppercase; color:#7d7d92; padding:6px 8px; border-bottom:1px solid #2a2a38; }}
td {{ padding:7px 8px; border-bottom:1px solid #1a1a24; font-size:10.5px; }}
td.wk {{ font-weight:700; color:#a78bfa; }}
.note {{ background:rgba(251,191,36,.07); border:1px solid rgba(251,191,36,.25); border-radius:9px; padding:10px 13px; margin-top:10px; font-size:10px; color:#e8d9a8; }}
.confirm {{ background:linear-gradient(90deg,rgba(99,102,241,.10),rgba(168,85,247,.10)); border:1px solid #2c2740; border-radius:11px; padding:13px 15px; margin-top:6px; }}
.confirm b {{ color:#c4b5fd; }}
.confirm .big {{ font-size:13px; font-weight:700; color:#f2f2f7; margin:6px 0 2px; }}
.legal {{ margin-top:16px; padding-top:9px; border-top:1px solid #23232f; font-size:8.8px; color:#74748a; line-height:1.55; text-align:center; }}
.legal b {{ color:#9494a8; }}
</style></head><body><div class="page">

<div class="head">
  <img class="mark" src="data:image/png;base64,{logo_b64}"/>
  <div class="wm">TRIGUN&nbsp;INNOVATIONS</div>
  <div class="wmsub">A PRODUCT OF TRIGUNAI</div>
  <div class="pill">ENROLMENT &amp; PAYMENT</div>
  <h1>Build Agentic AI Systems — Live Cohort 1</h1>
  <p>3 months · weekly live sessions · provided API/GPU access · completion certificate</p>
</div>

<div class="plans">
  <div class="plan best">
    <span class="tag">BEST VALUE · SAVE ₹1,000</span>
    <h3>Pay in full</h3>
    <div class="price">₹35,000</div>
    <p>One transfer. Full access from day one.</p>
  </div>
  <div class="plan">
    <h3>3-month EMI</h3>
    <div class="price">₹12,000 <small>× 3</small></div>
    <p>= ₹36,000 total. One payment a month, in step with the course.</p>
  </div>
</div>

<h2>Bank transfer details</h2>
<div class="acct">
  <div class="r"><span class="k">Account name</span><span class="v">{ACC_NAME}</span></div>
  <div class="r"><span class="k">Account number</span><span class="v">{ACC_NO}</span></div>
  <div class="r"><span class="k">IFSC</span><span class="v">{IFSC}</span></div>
  <div class="r"><span class="k">Bank</span><span class="v">{BANK}</span></div>
  <div class="r"><span class="k">Account type</span><span class="v">{ACC_TYPE}</span></div>
</div>
<div class="note">Transfer via NEFT / IMPS / UPI to the account above. Use your name as the payment reference where possible.</div>

<h2>EMI schedule &amp; access</h2>
<table>
  <tr><th>Installment</th><th>Amount</th><th>Due by</th><th>Unlocks</th></tr>
  <tr><td class="wk">EMI 1</td><td>₹12,000</td><td>Before Session 0 (Kickoff)</td><td>Weeks 0–4 + WhatsApp group + starter repo</td></tr>
  <tr><td class="wk">EMI 2</td><td>₹12,000</td><td>Before Week 5</td><td>Weeks 5–8</td></tr>
  <tr><td class="wk">EMI 3</td><td>₹12,000</td><td>Before Week 9</td><td>Weeks 9–12 + Demo Day + certificate</td></tr>
</table>
<div class="note">Access pauses if an installment is overdue. The completion certificate is issued only after full payment. Paying in full (₹35,000) unlocks everything from day one and saves ₹1,000.</div>

<h2>After you transfer — confirm your seat</h2>
<div class="confirm">
  <div class="big">Pay in full, or your first EMI, on or before the first live session (Fri 26 Jun).</div>
  Then <b>email your payment receipt</b> to <b>{EMAIL}</b> and we'll confirm your seat within a day.
  Please include: Name · Plan paid · Amount · UTR / reference number · receipt screenshot.
</div>

<div class="legal">
  <b>TrigunAI Innovations Private Limited</b> · CIN {CIN} · PAN {PAN} · GST {GST}<br/>
  Registered office: {ADDR}
</div>

</div></body></html>"""

html_path = HERE / "payment_pdf.html"
pdf_path  = HERE / "Agentic_AI_Enrolment_Payment.pdf"
html_path.write_text(HTML, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"PDF -> {pdf_path}  ({pdf_path.stat().st_size//1024} KB)")
