#!/usr/bin/env python3
"""Build the student Daily Homework Workbook PDF (HTML -> Chrome headless -> PDF). Dark, one page per week."""
import base64, subprocess, pathlib
from datetime import date, timedelta

HERE = pathlib.Path(__file__).resolve().parent
LOGO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/course_assets/logo/trigun_mark2.png")

FIRST_DATE = date(2026, 6, 26)   # Session 0 / Kickoff (next Friday). Homework week N is due before FIRST_DATE + N weeks.
CONTACT    = "deepak@trigunai.com"

logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()

# Each week: module, goal, watch(Sat), build_mon, build_tue, makeyours_wed, bring(Friday deliverable), done(list)
WEEKS = [
  dict(mod="Setup &amp; Module 1 — What an agent is",
       goal="Your tools work, and you understand the agent loop.",
       watch="Watch Module 1. Note: what are the 4 parts of an agent?",
       mon="Fork the starter repo, install it, add your API key to <code>.env</code>.",
       tue="Run <code>python run.py \"hello\"</code>. Open <code>agent/loop.py</code> and write a one-line comment on each step.",
       wed="Write your use-case (the real job your agent will do) into <code>config.py</code> and the README.",
       bring="Your agent saying hello in the terminal (screenshot) + your one-sentence use-case.",
       done=["Repo runs", "API key works", "Use-case written down"]),
  dict(mod="Module 2 — Your first tool-calling agent",
       goal="You can read and run the tool-calling loop end to end.",
       watch="Watch Module 2. Note: how does the model ask for a tool, and how do we answer?",
       mon="Run a goal that triggers a tool: <code>python run.py \"what is today's date?\"</code>. Watch the loop print each step.",
       tue="Add a print inside the loop to show every tool call + result. Make both example tools fire.",
       wed="List the 2–3 tools YOUR agent will need (just names + one line each).",
       bring="A run log showing a tool call and its result.",
       done=["A tool call fired", "You can explain the loop in your own words", "Your tool list drafted"]),
  dict(mod="Module 3 — Tools &amp; integrations",
       goal="Your agent uses one REAL tool of yours.",
       watch="Watch Module 3. Note: which of your tools is easiest to add first?",
       mon="Add one new tool to <code>agent/tools.py</code> (schema + function). Test it in isolation.",
       tue="Wire it into the loop; have the agent call it. Office hours if stuck.",
       wed="Point it at YOUR data — your sheet, a CSV export, your files.",
       bring="Your agent doing something useful with your own data.",
       done=["A real tool added", "It runs from the agent", "It touches your data"]),
  dict(mod="Module 4 — Memory &amp; context",
       goal="Your agent remembers across runs.",
       watch="Watch Module 4. Note: what should your agent remember between runs?",
       mon="Use <code>agent/memory.py</code>: have the agent write a note at the end of a run.",
       tue="On the next run, load that note into the prompt so it 'remembers'.",
       wed="Decide the 1–2 things your agent should remember for your use-case.",
       bring="Two runs where run #2 clearly uses what run #1 remembered.",
       done=["Memory writes", "Memory reads back", "It's meaningful for your task"]),
  dict(mod="Module 5 — Planning &amp; multi-step",
       goal="Your agent handles a job that takes several steps.",
       watch="Watch Module 5. Note: what is ReAct, in one sentence?",
       mon="Give the agent a task needing 3+ tool calls. Watch how it sequences them.",
       tue="Add a reflection step: let it check its own work before finishing.",
       wed="Write the real 5-step version of YOUR workflow as a single goal.",
       bring="A transcript of your agent completing a multi-step task.",
       done=["3+ steps in one run", "It reached the goal", "Your 5-step task written"]),
  dict(mod="Module 6 week — Catch-up &amp; integration (no new video)",
       goal="Your agent does your real job end-to-end, even if rough.",
       watch="No new module. Re-watch any part you were shaky on.",
       mon="Connect the pieces: tools + memory + planning in one run.",
       tue="Run your real workflow's happy path start to finish. Fix what breaks.",
       wed="Tidy: name things clearly, remove dead code, note remaining gaps.",
       bring="Your agent doing the real job, start to finish (rough is fine).",
       done=["One end-to-end run works", "You know your top 2 gaps", "Code is readable"]),
  dict(mod="Module 6 — Reliability &amp; guardrails",
       goal="Your agent fails safely and never burns money.",
       watch="Watch Module 6. Note: where could your agent do something costly or wrong?",
       mon="Add JSON validation + one retry on a tool that can fail.",
       tue="Set a cost cap in <code>config.py</code> (<code>MAX_USD</code>); add a human confirm step before any 'send'.",
       wed="Add the confirm-before-acting checkpoint that fits YOUR workflow.",
       bring="Show it handling a failure gracefully + your cost cap in action.",
       done=["Validation + retry added", "Cost cap set", "A human checkpoint exists"]),
  dict(mod="Module 7 — Multi-agent systems",
       goal="You know whether your task needs more than one agent.",
       watch="Watch Module 7. Note: when do multiple agents help vs. add chaos?",
       mon="Split a job into a planner agent + a worker agent; pass one handoff.",
       tue="Compare: is the 2-agent version actually better than one? Be honest.",
       wed="Decide if YOUR use-case needs multi-agent — and write why / why not.",
       bring="Either a 2-agent handoff working, OR a clear reason one agent is enough.",
       done=["You tried a handoff", "You made a call for your task", "You can justify it"]),
  dict(mod="Module 8 — Deploy your agent",
       goal="Your agent runs without you.",
       watch="Watch Module 8. Note: cron vs. GitHub Actions vs. a server — which fits you?",
       mon="Add logging so every run records what it did and why.",
       tue="Schedule it (cron or GitHub Actions). Trigger one scheduled run.",
       wed="Pick the schedule YOUR job needs (daily? hourly? on an event?).",
       bring="A log from a run that fired on a schedule, not by you.",
       done=["Logging works", "A scheduled run happened", "Schedule matches your need"]),
  dict(mod="Module 9 — Ship a real business agent",
       goal="Someone else can run your agent.",
       watch="Watch Module 9. Note: what would confuse a non-technical user?",
       mon="Write your agent's playbook: what it does, how to run it, what it needs.",
       tue="Package the config + a one-line run command. Remove anything fragile.",
       wed="Hand it to ONE non-technical person and watch them try it.",
       bring="Feedback from your first real user + a rough 'time saved' number.",
       done=["Playbook written", "One outside user tried it", "You measured time saved"]),
  dict(mod="Capstone build (Week 11)",
       goal="Polish your agent for Demo Day.",
       watch="No new module. Re-watch the part most relevant to your capstone.",
       mon="Fix your top 3 rough edges. Clean the README so it's obvious how to run.",
       tue="Do a full dry-run of the real job. Time it.",
       wed="Write your demo story: the problem → your agent → the result.",
       bring="A near-final agent + a 2-minute demo plan.",
       done=["Top 3 issues fixed", "README is clean", "Demo story written"]),
  dict(mod="Demo Day prep (Week 12)",
       goal="A clean, confident 5-minute demo.",
       watch="No new module. Watch a peer's clip shared in the WhatsApp group for ideas.",
       mon="Rehearse the live run twice. Note where it's slow or risky.",
       tue="Record a 1-min backup video in case the live run hiccups.",
       wed="Prepare your before/after: how much time your agent saves you.",
       bring="Your FINAL working agent — ready to demo on Demo Day. 🎉",
       done=["Rehearsed twice", "Backup recording ready", "Before/after prepared"]),
]

DAYNAMES = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu"]

def week_pages():
    pages = []
    for i, w in enumerate(WEEKS, start=1):
        base = FIRST_DATE + timedelta(weeks=i-1)        # Friday of the prior session
        sess = FIRST_DATE + timedelta(weeks=i)          # the Friday this homework is due before
        d = {dn: (base + timedelta(days=j+1)) for j, dn in enumerate(DAYNAMES)}  # Sat..Thu
        fmt = lambda dd: dd.strftime("%a %d %b")
        days = [
            (fmt(d["Sat"]), "Watch",        w["watch"],                                          "45 min"),
            (fmt(d["Sun"]), "Rest / buffer","Catch up if you're behind. Otherwise — recharge.",  "—"),
            (fmt(d["Mon"]), "Build",        w["mon"],                                            "40 min"),
            (fmt(d["Tue"]), "Build +",      w["tue"],                                            "40 min"),
            (fmt(d["Wed"]), "Make it yours",w["wed"],                                            "45 min"),
            (fmt(d["Thu"]), "Test &amp; show",  "Run it, fix one bug, post a screenshot in the WhatsApp group, and write your #1 question for Friday.", "30 min"),
        ]
        rows = "\n".join(
            f'<tr class="{"rest" if lbl=="Rest / buffer" else ""}">'
            f'<td class="dy">{dt}</td><td class="fc">{lbl}</td><td class="tk">{task}</td>'
            f'<td class="tm">{tm}</td><td class="ck">☐</td></tr>'
            for dt, lbl, task, tm in days
        )
        done = "".join(f'<span class="chip">☐ {c}</span>' for c in w["done"])
        pages.append(f"""
<div class="page {'p2' if i>1 else ''}">
  <div class="wk-head">
    <div class="wk-num">WEEK {i}</div>
    <div class="wk-mid">
      <div class="wk-mod">{w['mod']}</div>
      <div class="wk-due">Complete before your <b>{sess.strftime('%a %d %b')}</b> session · ~3.5 hrs across the week</div>
    </div>
    <img src="data:image/png;base64,{logo_b64}"/>
  </div>
  <div class="goal"><b>This week's goal:</b> {w['goal']}</div>
  <table>
    <tr><th>Day</th><th>Focus</th><th>What to do</th><th>Time</th><th>✓</th></tr>
    {rows}
    <tr class="sess"><td class="dy">{sess.strftime('%a %d %b')}</td><td class="fc">LIVE 5 PM</td>
      <td class="tk" colspan="2"><b>Show your work.</b> {w['bring']}</td><td class="ck">★</td></tr>
  </table>
  <div class="bring"><b>📦 Bring to Friday:</b> {w['bring']}</div>
  <div class="donebar"><span class="dl">Done when:</span> {done}</div>
</div>""")
    return "\n".join(pages)

COVER = f"""
<div class="page cover">
  <div class="chead">
    <img class="mark" src="data:image/png;base64,{logo_b64}"/>
    <div class="wm">TRIGUN&nbsp;INNOVATIONS</div>
    <div class="wmsub">A PRODUCT OF TRIGUNAI</div>
    <div class="pill">BUILD AGENTIC AI SYSTEMS · COHORT 1</div>
    <h1>Your Weekly Workbook</h1>
    <p>A day-by-day plan for the 6 days between each live session. Small reps, every day — so you walk into Friday with something to show.</p>
  </div>

  <div class="cbox">
    <h2>How this works</h2>
    <ul>
      <li>We meet <b>live every Friday, 5:00–6:30 PM IST</b>. This workbook covers the days in between.</li>
      <li>Each week has the <b>same daily rhythm</b> — it becomes a habit. Only the build task changes.</li>
      <li>Every day is <b>30–45 minutes</b>. Total ≈ 3.5 hrs/week. Don't cram it into Thursday night.</li>
      <li>Each week ends with one thing to <b>bring and show</b> on Friday. That's how we track you.</li>
    </ul>
  </div>

  <div class="cgrid">
    <div class="cbox">
      <h2>Your daily rhythm</h2>
      <ul>
        <li><b>Sat</b> — Watch the module, note 3 takeaways</li>
        <li><b>Sun</b> — Rest / catch-up buffer</li>
        <li><b>Mon</b> — Guided build in the starter repo</li>
        <li><b>Tue</b> — Extend it (+ office hours if stuck)</li>
        <li><b>Wed</b> — Make it yours: your own use-case</li>
        <li><b>Thu</b> — Test, post a screenshot, write your question</li>
        <li><b>Fri</b> — Live session: show your work</li>
      </ul>
    </div>
    <div class="cbox">
      <h2>3 golden rules</h2>
      <ul>
        <li><b>Done beats perfect.</b> Bring something rough every week — we fix it together.</li>
        <li><b>Post your blocker by Thursday</b> in the WhatsApp group. Don't suffer in silence for 6 days.</li>
        <li><b>Build on YOUR use-case.</b> Every exercise should move your real agent forward.</li>
      </ul>
    </div>
  </div>

  <div class="cbox" style="margin-top:auto">
    <h2>The one habit that makes this work</h2>
    <p style="color:#bcbccf;font-size:11px">Open your laptop for 40 minutes a day, six days a week. That's the whole secret. Students who do the daily reps ship a working agent; students who wait for the weekend don't. Tick each box as you go. 🚀</p>
  </div>

  <div class="foot"><span>TrigunAI Innovations Pvt Ltd · {CONTACT}</span><span>See you Fridays at 5 PM</span></div>
</div>"""

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ background:#08080c; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ font:11px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:#e7e7ef; }}
.page {{ padding:12mm 12mm 10mm; min-height:297mm; display:flex; flex-direction:column; }}
.p2 {{ page-break-before:always; }}
code {{ background:#1a1a26; border:1px solid #2a2a38; border-radius:4px; padding:0 4px; font-size:10px; color:#c4b5fd; }}

/* cover */
.cover {{ page-break-after:always; }}
.chead {{ text-align:center; padding-bottom:14px; border-bottom:1px solid #23232f; }}
.chead .mark {{ height:96px; }}
.chead .wm {{ font-family:Arial,Helvetica,sans-serif; font-weight:800; letter-spacing:5px; font-size:17px; color:#eef0fe; margin-top:7px; }}
.chead .wmsub {{ font-size:8.5px; letter-spacing:3px; color:#8a8a9c; margin-top:3px; }}
.pill {{ display:inline-block; font-size:9.5px; font-weight:700; letter-spacing:.9px; color:#b9a7ff;
  background:rgba(124,92,246,.12); border:1px solid rgba(124,92,246,.35); padding:4px 11px; border-radius:999px; margin:8px 0 8px; }}
.chead h1 {{ font-size:26px; }}
.chead p {{ color:#9494a8; font-size:12px; margin-top:6px; max-width:460px; margin-left:auto; margin-right:auto; }}
.cgrid {{ display:flex; gap:12px; }}
.cgrid .cbox {{ flex:1; }}
.cbox {{ background:#101018; border:1px solid #23232f; border-radius:11px; padding:14px 16px; margin-top:14px; }}
.cbox h2 {{ font-size:13px; margin-bottom:8px; color:#cfcfe0; }}

/* week page */
.wk-head {{ display:flex; align-items:center; gap:14px; padding-bottom:10px; border-bottom:1px solid #23232f; }}
.wk-num {{ font-size:30px; font-weight:800; color:#a78bfa; letter-spacing:.5px; white-space:nowrap; }}
.wk-mid {{ flex:1; }}
.wk-mod {{ font-size:16px; font-weight:700; color:#f2f2f7; }}
.wk-due {{ font-size:11px; color:#9494a8; margin-top:2px; }}
.wk-head img {{ height:46px; opacity:.95; }}
.goal {{ background:linear-gradient(90deg,rgba(99,102,241,.10),rgba(168,85,247,.10)); border:1px solid #2c2740;
  border-radius:9px; padding:10px 13px; margin:14px 0; color:#cfcfe0; font-size:11.5px; }}
.goal b {{ color:#c4b5fd; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ text-align:left; font-size:9px; letter-spacing:.5px; text-transform:uppercase; color:#7d7d92;
  padding:7px 8px; border-bottom:1px solid #2a2a38; }}
td {{ padding:9px 8px; border-bottom:1px solid #1a1a24; vertical-align:top; font-size:11px; }}
td.dy {{ font-weight:700; color:#cfcfe0; width:62px; white-space:nowrap; }}
td.fc {{ font-weight:600; color:#a78bfa; width:78px; }}
td.tk {{ color:#c3c3d4; }}
td.tm {{ color:#8c8ca0; width:48px; white-space:nowrap; }}
td.ck {{ width:22px; color:#6a6a80; font-size:14px; text-align:center; }}
tr.rest td {{ color:#6f6f86; }}
tr.rest td.tk {{ color:#6f6f86; font-style:italic; }}
tr.sess td {{ background:rgba(124,92,246,.12); }}
tr.sess td.fc {{ color:#c4b5fd; font-weight:800; }}
tr.sess td.ck {{ color:#facc15; }}
.bring {{ margin-top:14px; background:#13131c; border:1px dashed #3a3550; border-radius:9px; padding:11px 13px; font-size:11.5px; color:#dcdce8; }}
.bring b {{ color:#c4b5fd; }}
.donebar {{ margin-top:11px; font-size:10.5px; color:#9494a8; }}
.donebar .dl {{ font-weight:700; color:#cfcfe0; margin-right:6px; }}
.chip {{ display:inline-block; background:#15151f; border:1px solid #2a2a38; border-radius:999px;
  padding:3px 10px; margin:3px 5px 0 0; color:#bcbccf; font-size:10px; }}

ul {{ list-style:none; }}
li {{ padding-left:15px; position:relative; margin-bottom:5px; font-size:11px; color:#bcbccf; }}
li::before {{ content:"›"; position:absolute; left:1px; color:#a78bfa; font-weight:800; }}
li b {{ color:#e7e7ef; }}
.foot {{ margin-top:14px; padding-top:8px; border-top:1px solid #23232f; font-size:9.5px; color:#74748a;
  display:flex; justify-content:space-between; }}
</style></head><body>
{COVER}
{week_pages()}
</body></html>"""

html_path = HERE / "workbook.html"
pdf_path  = HERE / "Agentic_AI_Daily_Workbook.pdf"
html_path.write_text(HTML, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"PDF -> {pdf_path}  ({pdf_path.stat().st_size//1024} KB) · {len(WEEKS)} weeks + cover")
