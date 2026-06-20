#!/usr/bin/env python3
"""Build the 'Cohort 1 — Start Here' welcome page (self-contained HTML, embedded logo)."""
import base64, pathlib

HERE = pathlib.Path(__file__).resolve().parent
LOGO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/Blender-Antigravity/trigun-logo-output/trigun_2k_transparent.png")

# ---- EDIT THESE before sharing -------------------------------------------
REPO_URL    = "https://github.com/YOUR-USERNAME/agentic-ops-agent-starter"
DISCORD_URL = "https://discord.gg/YOUR-INVITE"
FIRST_LIVE  = "Friday, 19 June 2026 · 5:00 PM IST"
OFFICE_HRS  = "Tuesdays · 8:00–8:30 PM IST (optional)"
CONTACT     = "deepak@trigunai.com"
# --------------------------------------------------------------------------

logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cohort 1 — Start Here | Build Agentic AI Systems</title>
<style>
  :root{{--bg:#08080c;--card:#111119;--card2:#15151f;--line:#23232f;--txt:#e7e7ef;--mut:#9494a8;
    --accent:#818cf8;--accent2:#c084fc;}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--txt);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
  .wrap{{max-width:720px;margin:0 auto;padding:30px 20px 60px}}
  .head{{text-align:center;border-bottom:1px solid var(--line);padding-bottom:18px}}
  .head img{{height:108px}}
  .pill{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.9px;color:#b9a7ff;
    background:rgba(124,92,246,.12);border:1px solid rgba(124,92,246,.35);padding:5px 12px;border-radius:999px;margin:10px 0 8px}}
  h1{{font-size:27px}}
  .head p{{color:var(--mut);margin-top:6px}}
  h2{{font-size:15px;margin:26px 0 12px;color:#cfcfe0}}
  .steps{{display:grid;gap:10px}}
  .step{{display:flex;gap:14px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
  .step .n{{flex:none;width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));
    color:#0a0a12;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:14px}}
  .step .b{{flex:1}}
  .step .t{{font-weight:700}}
  .step .d{{color:var(--mut);font-size:14px;margin-top:2px}}
  .step a{{color:var(--accent);font-weight:600}}
  .cards{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
  @media(max-width:560px){{.cards{{grid-template-columns:1fr}}}}
  .card{{display:flex;gap:13px;align-items:center;text-decoration:none;background:var(--card);
    border:1px solid var(--line);border-radius:12px;padding:15px 16px;color:var(--txt);transition:border-color .15s}}
  .card:hover{{border-color:var(--accent)}}
  .card .ico{{font-size:24px;flex:none}}
  .card .t{{font-weight:700}}
  .card .s{{color:var(--mut);font-size:13px;margin-top:1px}}
  .card.go{{background:linear-gradient(135deg,rgba(129,140,248,.16),rgba(192,132,252,.16));border-color:rgba(129,140,248,.4)}}
  .info{{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}}
  .info .box{{flex:1;min-width:150px;background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:11px 13px}}
  .info .k{{font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:var(--mut)}}
  .info .v{{font-weight:700;margin-top:3px;font-size:14px}}
  .foot{{text-align:center;color:var(--mut);font-size:13px;margin-top:30px}}
  code{{background:#1a1a26;border:1px solid #2a2a38;border-radius:4px;padding:1px 6px;font-size:13px;color:#c4b5fd}}
</style></head><body><div class="wrap">

  <div class="head">
    <img src="data:image/png;base64,{logo_b64}"/>
    <div class="pill">COHORT 1 · START HERE</div>
    <h1>Welcome to Build Agentic AI Systems</h1>
    <p>Everything you need to begin is on this page. First live session: <b>{FIRST_LIVE}</b>.</p>
  </div>

  <h2>✅ Do these 4 things before our first session</h2>
  <div class="steps">
    <div class="step"><div class="n">1</div><div class="b">
      <div class="t">Join the Discord</div>
      <div class="d">Our home base for help, recordings, and sharing work. → <a href="{DISCORD_URL}">Join here</a></div></div></div>
    <div class="step"><div class="n">2</div><div class="b">
      <div class="t">Fork the starter repo</div>
      <div class="d">The agent you'll grow all course long. → <a href="{REPO_URL}">Open on GitHub</a> · follow the 5-min README setup</div></div></div>
    <div class="step"><div class="n">3</div><div class="b">
      <div class="t">Get an API key (Claude or OpenAI)</div>
      <div class="d">Don't have one yet? No problem — we'll set it up together at Kickoff. No one gets left behind.</div></div></div>
    <div class="step"><div class="n">4</div><div class="b">
      <div class="t">Skim the schedule &amp; workbook below</div>
      <div class="d">So you know the rhythm. Then just show up Friday with your laptop. That's it.</div></div></div>
  </div>

  <h2>📂 Your cohort materials</h2>
  <div class="cards">
    <a class="card" href="./Agentic_AI_Cohort_Schedule.pdf">
      <span class="ico">📅</span><span><span class="t">Course Schedule</span><span class="s">13 weeks · dates &amp; timing</span></span></a>
    <a class="card" href="./Agentic_AI_Daily_Workbook.pdf">
      <span class="ico">📓</span><span><span class="t">Daily Workbook</span><span class="s">Your day-by-day homework plan</span></span></a>
    <a class="card" href="{REPO_URL}">
      <span class="ico">💻</span><span><span class="t">Starter Repo</span><span class="s">Fork it &amp; run <code>python run.py</code></span></span></a>
    <a class="card" href="{DISCORD_URL}">
      <span class="ico">💬</span><span><span class="t">Discord</span><span class="s">Help · recordings · community</span></span></a>
  </div>

  <h2>🎟️ Not enrolled yet?</h2>
  <div class="cards">
    <a class="card go" href="./payment.html">
      <span class="ico">💳</span><span><span class="t">Reserve your seat</span><span class="s">Pay in full or in 3 monthly installments</span></span></a>
  </div>

  <h2>🗓️ The essentials</h2>
  <div class="info">
    <div class="box"><div class="k">Live session</div><div class="v">Fridays · 5:00–6:30 PM IST</div></div>
    <div class="box"><div class="k">Office hours</div><div class="v">{OFFICE_HRS}</div></div>
    <div class="box"><div class="k">Help anytime</div><div class="v">Discord #help</div></div>
  </div>

  <p class="foot">Questions? Email <a href="mailto:{CONTACT}" style="color:var(--accent)">{CONTACT}</a> or ask in Discord.<br/>
  TrigunAI Innovations Pvt Ltd · See you Friday at 5 PM 🚀</p>

</div></body></html>"""

out = HERE / "START_HERE.html"
out.write_text(HTML, encoding="utf-8")
print(f"Wrote {out} ({len(HTML)//1024} KB)")
