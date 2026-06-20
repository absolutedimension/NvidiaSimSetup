#!/usr/bin/env python3
"""Build the branded Agentic Cohort schedule PDF (HTML -> Chrome headless -> PDF). Dark theme, 2 pages."""
import base64, subprocess, pathlib
from datetime import date, timedelta

HERE = pathlib.Path(__file__).resolve().parent
LOGO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/course_assets/logo/trigun_mark2.png")

# ---- EDIT THESE before the final render -----------------------------------
FIRST_DATE   = date(2026, 6, 26)              # Session 0 / Kickoff date (next Friday)
SESSION_TIME = "5:00 – 6:30 PM IST"           # weekly live window (90 min)
WEEKLY_DAY   = "Fridays"
LIVE_VENUE   = "Google Meet (link in WhatsApp group)"
OFFICE_HOURS = "Tuesdays · 8:00–8:30 PM IST (optional drop-in)"
HELP_SLA     = "Post in the WhatsApp group anytime — replies daily by 10 PM IST"
CONTACT      = "deepak@trigunai.com"
# ---------------------------------------------------------------------------

logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()
def dt(i): return (FIRST_DATE + timedelta(weeks=i)).strftime("%d %b")
START_FULL = FIRST_DATE.strftime("%a, %d %b %Y") + " · 5:00 PM"
END_FULL   = (FIRST_DATE + timedelta(weeks=12)).strftime("%d %b %Y")

# (module, live-session focus, watch-before)
SCHEDULE = [
    ("Kickoff",                       "Orientation · get your API key working live · fork the starter repo · pick your use-case", "Just bring your laptop"),
    ("What an agent actually is",     "Map your use-case to goal → actions → stop; the loop on a whiteboard",                     "Module 1 video"),
    ("Your first tool-calling agent", "Live-code the agent loop; everyone lands their first tool call",                           "Module 2 + run run.py"),
    ("Tools &amp; integrations",          "Connect YOUR real tool — inbox, sheet, files, web search",                                "Module 3 video"),
    ("Memory &amp; context",              "Add memory to your agent; retrieval (RAG) basics on your own docs",                       "Module 4 video"),
    ("Planning &amp; multi-step",         "Task decomposition, ReAct, reflection &amp; self-correction",                                 "Module 5 video"),
    ("Catch-up &amp; integration",        "No new module — get your agent doing a real 5-step job end-to-end",                       "Finish pending modules"),
    ("Reliability &amp; guardrails",      "JSON validation, retries, human checkpoints, cost control — debug live",                  "Module 6 video"),
    ("Multi-agent systems",           "Orchestrator + worker agents; when multiple agents truly help",                           "Module 7 video"),
    ("Deploy your agent",             "Run it on a schedule on a server, with logging you can read",                             "Module 8 video"),
    ("Ship a real business agent",    "Package it, hand it to a non-technical user, measure time saved",                         "Module 9 video"),
    ("Capstone build",                "Office-hours format — polish your own agent for Demo Day",                                "Bring your agent"),
    ("Demo Day + certificates",       "Each student demos their working agent · certificates awarded",                           "Final agent ready"),
]

rows = "\n".join(
    f'<tr class="{"hl" if m in ("Kickoff","Demo Day + certificates","Catch-up &amp; integration") else ""}">'
    f'<td class="dt">{dt(i)}</td><td class="wk">{i}</td><td class="md">{m}</td>'
    f'<td class="ds">{focus}</td><td class="pw">{pw}</td></tr>'
    for i, (m, focus, pw) in enumerate(SCHEDULE)
)

SESSION_BLOCKS = [
    ("5:00 – 5:10", "Wins &amp; blockers", "Each student: what you built this week, where you're stuck"),
    ("5:10 – 5:30", "The hard part",     "The one tricky concept the video can't carry — taught live, with code"),
    ("5:30 – 6:10", "Live build / debug","We build this week's pattern, or debug YOUR actual agent on screen"),
    ("6:10 – 6:25", "Your assignment",   "This week's build on your own project + the next module to watch"),
    ("6:25 – 6:30", "Cost check &amp; wrap","Check your API spend; questions; next session reminder"),
]
sess_rows = "\n".join(
    f'<tr><td class="tm">{t}</td><td class="bk">{b}</td><td class="bd">{d}</td></tr>'
    for t, b, d in SESSION_BLOCKS
)

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background:#08080c; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ font: 11px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color:#e7e7ef; }}
.page {{ padding: 12mm 12mm 10mm; min-height:297mm; }}
.p2 {{ page-break-before: always; }}
.head {{ text-align:center; padding-bottom:12px; border-bottom:1px solid #23232f; }}
.head .mark {{ height:88px; }}
.head .wm {{ font-family:Arial,Helvetica,sans-serif; font-weight:800; letter-spacing:5px; font-size:16px; color:#eef0fe; margin-top:6px; }}
.head .wmsub {{ font-size:8px; letter-spacing:3px; color:#8a8a9c; margin-top:3px; }}
.head .pill {{ display:inline-block; font-size:9.5px; font-weight:700; letter-spacing:.9px; color:#b9a7ff;
  background:rgba(124,92,246,.12); border:1px solid rgba(124,92,246,.35); padding:4px 11px; border-radius:999px; margin:6px 0 8px; }}
.head h1 {{ font-size:22px; letter-spacing:.2px; }}
.head p {{ color:#9494a8; font-size:11.5px; margin-top:4px; }}
.info {{ display:flex; gap:8px; margin:14px 0; }}
.info .box {{ flex:1; background:#111119; border:1px solid #23232f; border-radius:9px; padding:9px 11px; }}
.info .box .k {{ font-size:8.5px; letter-spacing:.6px; text-transform:uppercase; color:#7d7d92; }}
.info .box .v {{ font-size:11.5px; font-weight:700; margin-top:3px; color:#f2f2f7; }}
.callout {{ background:linear-gradient(90deg,rgba(99,102,241,.10),rgba(168,85,247,.10));
  border:1px solid #2c2740; border-radius:9px; padding:11px 13px; margin:2px 0 14px; color:#cfcfe0; font-size:10.5px; }}
.callout b {{ color:#c4b5fd; }}
h2 {{ font-size:12.5px; margin:14px 0 7px; color:#cfcfe0; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; font-size:8.5px; letter-spacing:.6px; text-transform:uppercase; color:#7d7d92;
  padding:5px 7px; border-bottom:1px solid #2a2a38; }}
td {{ padding:5px 7px; border-bottom:1px solid #1a1a24; vertical-align:top; font-size:10px; }}
td.dt {{ font-weight:700; color:#cfcfe0; width:46px; white-space:nowrap; }}
td.wk {{ font-weight:800; color:#a78bfa; width:24px; }}
td.md {{ font-weight:600; width:150px; color:#f2f2f7; }}
td.ds {{ color:#a8a8bc; }}
td.pw {{ color:#8c8ca0; width:104px; font-style:italic; }}
tr.hl td {{ background:rgba(124,92,246,.08); }}
td.tm {{ font-weight:700; color:#a78bfa; width:80px; white-space:nowrap; }}
td.bk {{ font-weight:600; color:#f2f2f7; width:110px; }}
td.bd {{ color:#a8a8bc; }}
.grid {{ display:flex; gap:13px; }}
.grid .col {{ flex:1; }}
.cardbox {{ background:#101018; border:1px solid #23232f; border-radius:10px; padding:12px 14px; margin-bottom:12px; }}
.cardbox h2 {{ margin:0 0 7px; }}
ul {{ list-style:none; }}
li {{ padding-left:15px; position:relative; margin-bottom:5px; font-size:10.5px; color:#bcbccf; }}
li::before {{ content:"›"; position:absolute; left:1px; color:#a78bfa; font-weight:800; }}
li b {{ color:#e7e7ef; }}
.foot {{ margin-top:16px; padding-top:8px; border-top:1px solid #23232f; font-size:9.5px; color:#74748a;
  display:flex; justify-content:space-between; }}
</style></head><body>

<!-- ===================== PAGE 1 ===================== -->
<div class="page">
  <div class="head">
    <img class="mark" src="data:image/png;base64,{logo_b64}"/>
    <div class="wm">TRIGUN&nbsp;INNOVATIONS</div>
    <div class="wmsub">A PRODUCT OF TRIGUNAI</div>
    <div class="pill">LIVE COHORT 1 · 3-MONTH SCHEDULE</div>
    <h1>Build Agentic AI Systems</h1>
    <p>Build a real AI agent that does a real job of yours — live, over 3 months.</p>
  </div>

  <div class="info">
    <div class="box"><div class="k">Starts</div><div class="v">{START_FULL}</div></div>
    <div class="box"><div class="k">Live every</div><div class="v">{WEEKLY_DAY} · {SESSION_TIME}</div></div>
    <div class="box"><div class="k">Where</div><div class="v">{LIVE_VENUE}</div></div>
    <div class="box"><div class="k">Runs until</div><div class="v">{END_FULL}</div></div>
  </div>

  <div class="callout">
    <b>How it works — the flipped model:</b> before each week you watch that module's video (≈30–60 min).
    The live 90 minutes are for <b>building and debugging your own code</b>, not re-watching. Everyone starts
    from the same starter repo but automates <b>your own</b> real workflow. By Demo Day you have a working,
    deployed agent — plus the patterns to build the next one.
  </div>

  <h2>The 13-week schedule — every session is a {WEEKLY_DAY[:-1]}, {SESSION_TIME}</h2>
  <table>
    <tr><th>Date</th><th>Wk</th><th>Module</th><th>What we do in the live session</th><th>Watch before</th></tr>
    {rows}
  </table>

  <div class="foot">
    <span>TrigunAI Innovations Pvt Ltd · {CONTACT}</span>
    <span>Page 1 of 2 — turn over for session timing &amp; what you need →</span>
  </div>
</div>

<!-- ===================== PAGE 2 ===================== -->
<div class="page p2">
  <div class="head">
    <img class="mark" src="data:image/png;base64,{logo_b64}" style="height:50px"/>
    <div class="pill" style="margin-top:8px">HOW EACH WEEK WORKS</div>
  </div>

  <h2>Inside each 90-minute live session</h2>
  <table>
    <tr><th>Time (IST)</th><th>Block</th><th>What happens</th></tr>
    {sess_rows}
  </table>

  <div class="grid" style="margin-top:14px">
    <div class="col">
      <div class="cardbox">
        <h2>Your weekly rhythm</h2>
        <ul>
          <li><b>Before the session:</b> watch the module video (≈30–60 min)</li>
          <li><b>Come having tried:</b> attempt the week's build, note where you're stuck</li>
          <li><b>In the session:</b> we unblock you and build live</li>
          <li><b>After:</b> finish your build · ~3–4 hrs/week between sessions</li>
        </ul>
      </div>
      <div class="cardbox">
        <h2>What you need to start</h2>
        <ul>
          <li>A laptop (Windows / Mac / Linux)</li>
          <li>An API key — Claude or OpenAI (we set it up with you at Kickoff)</li>
          <li>The starter repo — shared at Kickoff</li>
          <li>Provided API / GPU access for the heavier modules</li>
          <li>Light Python helps, but the agent writes most of the code</li>
        </ul>
      </div>
    </div>
    <div class="col">
      <div class="cardbox">
        <h2>Support between sessions</h2>
        <ul>
          <li><b>WhatsApp group:</b> {HELP_SLA}</li>
          <li><b>Office hours:</b> {OFFICE_HOURS}</li>
          <li><b>Recordings:</b> every session is recorded — catch up anytime</li>
          <li><b>Share your work</b> &amp; resources in the WhatsApp group</li>
        </ul>
      </div>
      <div class="cardbox">
        <h2>How you earn your certificate</h2>
        <ul>
          <li>Attend at least <b>10 of 13</b> live sessions (recordings count if watched within 48 h)</li>
          <li>Ship your <b>capstone agent</b> at Demo Day (Wk 12)</li>
          <li>Complete payment (full, or all 3 EMI installments)</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="cardbox">
    <h2>What you walk away with</h2>
    <ul>
      <li>A <b>working, deployed AI agent</b> automating a real workflow of yours — running on a schedule</li>
      <li>The <b>patterns &amp; starter code</b> to build the next agent for any task</li>
      <li>A <b>completion certificate</b> and a project you can show an employer or client</li>
    </ul>
  </div>

  <div class="foot">
    <span>TrigunAI Innovations Pvt Ltd · {CONTACT}</span>
    <span>See you {WEEKLY_DAY[:-1]} at 5 PM 🚀</span>
  </div>
</div>

</body></html>"""

html_path = HERE / "schedule.html"
pdf_path  = HERE / "Agentic_AI_Cohort_Schedule.pdf"
html_path.write_text(HTML, encoding="utf-8")

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"PDF -> {pdf_path}  ({pdf_path.stat().st_size//1024} KB)")
