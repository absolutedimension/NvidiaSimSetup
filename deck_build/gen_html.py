import base64, html, os
REPO = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup"

def b64(p):
    full = p if os.path.isabs(p) else os.path.join(REPO, p)
    with open(full, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

logo_light = b64("/Users/deepakkumarrai/Documents/01_Active/Blender-Antigravity/trigun-logo-output/trigun_2k_transparent.png")

NAVY="#0B1B2E"; NAVY2="#13314F"; GOLD="#C9A227"; INK="#1A2333"; MUTED="#667085"
LIGHT="#F6F8FB"; CARD="#FFFFFF"; LINE="#E3E8EF"; GREEN="#76B900"

def kicker(k,t,color=GOLD):
    return f'<div class="kick" style="color:{color}">{k}</div><h1>{t}</h1>'

slides = []

# 1 TITLE
slides.append(f'''<section class="s dark">
  <div class="topbar"></div>
  <img class="logo" src="{logo_light}"/>
  <h1 class="title">TrigunAI Innovations</h1>
  <p class="sub">Two engines, one company — AI education that ships, and physical-AI research.</p>
  <div class="chips"><span class="chip">NVIDIA Inception Member</span><span class="chip">Google Android XR Catalyst</span></div>
  <div class="foot2">Patna · Mumbai, India&nbsp;&nbsp;|&nbsp;&nbsp;CIN U86909BR2025PTC078945&nbsp;&nbsp;|&nbsp;&nbsp;Incorporated 2025</div>
</section>''')

# 2 WHY NOW
slides.append(f'''<section class="s light">{kicker("WHY NOW","Two pressures, one company built for both")}
  <div class="two">
    <div class="card"><h3>India needs an AI workforce</h3><ul>
      <li>The world's #1 AI-learning market — 1.3M+ learners and rising (NASSCOM–Deloitte).</li>
      <li>But the talent pipeline is fragmented and theory-heavy.</li>
      <li>We teach by shipping — learners leave with a published app or a trained policy.</li></ul></div>
    <div class="card"><h3>Physical AI is the next decade</h3><ul>
      <li>Robotics &amp; embodied AI is where value compounds next.</li>
      <li>India has minimal indigenous capability and little founder-accessible Isaac-grade infra.</li>
      <li>We build that capability in-house on the NVIDIA stack.</li></ul></div>
  </div>
  <p class="banner-i">Our bet: build the human-capital pipeline for India's physical-AI workforce — and own a piece of the stack while we do it.</p>
</section>''')

# 3 MODEL
slides.append(f'''<section class="s light">{kicker("THE MODEL","One company, two coupled engines")}
  <div class="two">
    <div class="card"><div class="tab" style="background:{GOLD}"></div><div class="lab" style="color:{GOLD}">ENGINE A</div><h2>Learning Engine</h2><p>Courses that teach by shipping. Free content → paid live cohort. Run by Deepak. The revenue engine — funds everything.</p></div>
    <div class="card"><div class="tab" style="background:{NAVY2}"></div><div class="lab" style="color:{NAVY2}">ENGINE B</div><h2>Physical AI Engine</h2><p>Embodied-AI research → IP, course material, and (when funded) hardware products. Avinash leads; Deepak co-leads the drone.</p></div>
  </div>
  <div class="strip">Revenue funds research&nbsp;&nbsp;·&nbsp;&nbsp;Research makes the teaching credible&nbsp;&nbsp;·&nbsp;&nbsp;Both feed talent</div>
</section>''')

# 4 ENGINE A
rows=[("Live courses platform","learn.trigunai.com — magic-link auth, student + admin dashboards. In production."),
("Flagship course","Build &amp; Ship a VR/MR App — 9 of 11 modules produced and public (EN + HI)."),
("Course lineup","VR/MR (flagship) + Agentic AI + ML &amp; Math, with Physical AI / Robotics in development."),
("Free funnel","“AI is the Universal Mind” — 7 animated episodes, bilingual, on YouTube."),
("Proof of shipping","GuruLok — a meditation VR app live on the Meta Quest store.")]
rowhtml="".join(f'<div class="row"><div class="rl">{a}</div><div class="rr">{b}</div></div>' for a,b in rows)
slides.append(f'''<section class="s light">{kicker("ENGINE A — LEARNING","Teach by shipping")}
  <p class="note">Recorded videos are free (the funnel). The paid product is a live cohort.</p>{rowhtml}</section>''')

# 5 ENGINE B
slides.append(f'''<section class="s light">{kicker("ENGINE B — PHYSICAL AI","Simulation-trained intelligence, deployed to the edge")}
  <div class="two">
    <div class="card"><div class="tab" style="background:{GREEN}"></div><div class="lab" style="color:{GREEN}">TRACK 1</div><h3>Drone Cinematography Policy</h3><ul>
      <li>PPO trained in NVIDIA Isaac Sim / Isaac Lab (4096 envs, A10G).</li>
      <li>Exported to ONNX (~80 KB), runs on-device at 50 Hz; VR-validated in our Quest app.</li>
      <li>Target hardware: Modal AI Starling 2 + GoPro Hero 12.</li></ul></div>
    <div class="card"><div class="tab" style="background:{GREEN}"></div><div class="lab" style="color:{GREEN}">TRACK 2</div><h3>ModusXR — AR Attention Guidance</h3><ul>
      <li>Three additive focus modes for optical see-through AR.</li>
      <li>Participant in Google's Android XR Catalyst program.</li>
      <li>Target hardware: XREAL Project Aura; prototyped on Quest 3 passthrough.</li></ul></div>
  </div></section>''')

# 6 FLYWHEEL
steps=[("1","The Robotics course's labs ARE the real drone-policy pipeline."),
("2","Students learn RL on real NVIDIA hardware — not a toy copy."),
("3","Graduates become collaborators, hires, or customers."),
("4","We sit at the center of India's physical-AI talent flow.")]
sh="".join(f'<div class="step"><div class="num">{n}</div><div class="stxt">{t}</div></div>' for n,t in steps)
slides.append(f'''<section class="s light">{kicker("THE FLYWHEEL WE'RE BUILDING","Students learn inside the real research")}
  <span class="pill">Roadmap thesis — not yet operational</span>{sh}
  <p class="note">Honest today: the two engines run independently; the robotics course is in development. The coupling is the plan, not a current claim.</p></section>''')

# 7 NVIDIA STACK
tech=["Isaac Sim","Isaac Lab","Omniverse","CUDA Toolkit","NVIDIA PyTorch","ONNX → edge"]
th="".join(f'<div class="techbox">{t}</div>' for t in tech)
slides.append(f'''<section class="s dark">{kicker("NVIDIA TECH","NVIDIA, end to end",GREEN)}
  <div class="techgrid">{th}</div>
  <p class="sub" style="text-align:center;margin-top:24px">Member of NVIDIA Inception. Policies train on A10G GPUs; edge target is Jetson-class. Not locked in — the ONNX policy ports anywhere.</p></section>''')

# 8 TRACTION
shipped=["GuruLok VR app live on the Meta Quest store","7 bilingual episodes published (EN + HI)","Courses platform + 9 VR/MR modules live","Drone policy trained + VR-validated","ModusXR in Google Android XR Catalyst","5 hostnames in production (Azure, India)"]
stage=["Pre-revenue. Founding-cohort phase.","Paid wall opens with the first live cohort.","~₹4,000/mo infrastructure. Bootstrapped.","2 founders, no outside capital raised."]
sl="".join(f"<li>{x}</li>" for x in shipped); stl="".join(f"<li>{x}</li>" for x in stage)
slides.append(f'''<section class="s light">{kicker("TRACTION","Where we actually are")}
  <div class="two">
    <div class="card"><div class="tab" style="background:{GOLD}"></div><h3>Shipped &amp; live</h3><ul>{sl}</ul></div>
    <div class="card"><div class="tab" style="background:{NAVY2}"></div><h3>Honest stage</h3><ul>{stl}</ul>
      <p class="note">We show the real stage on purpose — pre-seed, built, and ready to validate willingness-to-pay.</p></div>
  </div></section>''')

# 9 MODEL LADDER
ladder=[("01","Free series","Funnel + email capture",False),("02","Community","Recurring bridge",False),("03","Recorded courses","Proof + passive floor",False),("04","Live cohort + GPU + VR","THE PROFIT ENGINE",True),("05","B2B AI-literacy","Later",False)]
lh="".join(f'<div class="lad {"hot" if h else ""}"><div class="ln">{n}</div><div class="lt">{t}</div><div class="ld">{d}</div></div>' for n,t,d,h in ladder)
slides.append(f'''<section class="s light">{kicker("BUSINESS MODEL","Free to understand · paid to transform")}
  <div class="ladder">{lh}</div>
  <p class="banner-i">One self-run cohort (₹35–49k × ~20) ≈ ₹7–8 L. The moat — provided GPU + VR + “we shipped it” — is uncopyable.</p></section>''')

# 10 TEAM
slides.append(f'''<section class="s light">{kicker("FOUNDERS","Two founders, two engines")}
  <div class="two">
    <div class="card"><h2>Deepak Kumar</h2><div class="role">CEO · Mumbai</div><ul>
      <li>Runs the Learning Engine; co-leads the drone policy.</li>
      <li>Shipped a Quest app to Meta alpha; built the full video + RL training pipeline.</li></ul></div>
    <div class="card"><h2>Avinash</h2><div class="role">CTO · Patna</div><ul>
      <li>Leads the Physical AI Engine — ModusXR (Android XR Catalyst).</li>
      <li>Deep-learning depth; maintains the shipped Quest apps.</li></ul></div>
  </div>
  <p class="note" style="text-align:center">Bootstrapped. NVIDIA Inception member. Google Android XR Catalyst participant.</p></section>''')

# 11 ASK
asks=[("Drone hardware","Modal AI Starling 2 + GoPro Hero 12 (~$2.5–3K) + a 6-month flight-test runway."),("AR hardware","XREAL Aura developer kits + sustained ModusXR build bandwidth.")]
ah="".join(f'<div class="askrow"><div class="al">{a}</div><div class="ar">{b}</div></div>' for a,b in asks)
slides.append(f'''<section class="s dark">{kicker("THE ASK","Seed capital for hardware — operations are self-funded")}
  {ah}
  <p class="sub" style="text-align:center;margin-top:22px">The software pipeline is ready. Hardware procurement is the only bottleneck to closing the sim-to-real gap. The Learning Engine funds day-to-day operations.</p></section>''')

# 12 CONTACT
slides.append(f'''<section class="s dark center">
  <img class="logo2" src="{logo_light}"/>
  <h1 class="title" style="text-align:center">Let's build the physical-AI workforce.</h1>
  <p class="sub" style="text-align:center">trigunai.com&nbsp;&nbsp;·&nbsp;&nbsp;learn.trigunai.com&nbsp;&nbsp;·&nbsp;&nbsp;physical-ai.trigunai.com</p>
  <p style="text-align:center;color:#fff;font-size:22px;margin-top:14px"><b>deepak@trigunai.com</b> <span style="color:#8FA6BD">— subject: "Investor enquiry — Physical AI"</span></p>
  <p style="text-align:center;color:{GOLD};font-size:17px;margin-top:18px">NVIDIA Inception Member · Google Android XR Catalyst</p>
  <div class="topbar" style="top:auto;bottom:0"></div>
</section>''')

css=f'''
*{{box-sizing:border-box;margin:0;padding:0;-webkit-print-color-adjust:exact !important;print-color-adjust:exact !important}}
body{{background:#222;font-family:'Helvetica Neue',Arial,sans-serif;padding:24px 0}}
@page{{size:1280px 720px;margin:0}}
@media print{{
  body{{background:#fff;padding:0}}
  .s{{margin:0 !important;box-shadow:none !important;page-break-after:always;break-after:page}}
  .s:last-child{{page-break-after:auto}}
}}
.s{{position:relative;width:1280px;height:720px;margin:0 auto 28px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,.5);padding:60px 64px}}
.dark{{background:{NAVY};color:#fff}}
.light{{background:{LIGHT};color:{INK}}}
.center{{display:flex;flex-direction:column;justify-content:center;align-items:center}}
.topbar{{position:absolute;top:0;left:0;width:100%;height:16px;background:{GOLD}}}
.kick{{font-size:15px;font-weight:700;letter-spacing:2px;margin-bottom:6px}}
.s h1{{font-family:Georgia,serif;font-size:40px;font-weight:700;margin-bottom:10px}}
.light h1{{color:{INK}}}
.title{{font-size:60px!important;margin-top:14px}}
.dark .title{{color:#fff}}
.sub{{font-size:20px;color:#CFE0F0}} .light .sub{{color:{MUTED}}}
.logo{{width:140px;height:140px;object-fit:contain;margin-top:20px}}
.logo2{{width:120px;height:120px;object-fit:contain;margin-bottom:18px}}
.chips{{margin-top:26px;display:flex;gap:16px}}
.chip{{border:1px solid {GOLD};background:{NAVY2};color:#fff;font-weight:700;font-size:14px;padding:9px 18px;border-radius:8px}}
.foot2{{position:absolute;bottom:40px;left:64px;color:#8FA6BD;font-size:14px}}
.two{{display:flex;gap:26px;margin-top:30px}}
.card{{flex:1;background:{CARD};border:1px solid {LINE};border-radius:6px;padding:26px 28px;position:relative;box-shadow:0 4px 14px rgba(0,0,0,.06)}}
.card h2{{font-size:24px;margin:6px 0 10px}} .card h3{{font-size:20px;margin:4px 0 12px}}
.card p{{font-size:16px;line-height:1.5;color:{INK}}}
.card ul{{margin-left:18px}} .card li{{font-size:15.5px;line-height:1.5;margin-bottom:9px}}
.tab{{position:absolute;top:0;left:0;width:100%;height:7px;border-radius:6px 6px 0 0}}
.lab{{font-size:14px;font-weight:700;letter-spacing:2px;margin-top:4px}}
.strip{{margin-top:34px;background:{NAVY};color:#fff;font-weight:700;font-size:18px;text-align:center;padding:24px;border-radius:4px}}
.note{{font-size:15px;font-style:italic;color:{MUTED};margin-top:18px}}
.row{{display:flex;align-items:center;background:{CARD};border:1px solid {LINE};border-left:5px solid {GOLD};border-radius:4px;padding:14px 20px;margin-top:12px}}
.rl{{font-weight:700;width:300px;font-size:16px}} .rr{{font-size:15.5px;color:{INK}}}
.pill{{display:inline-block;background:#FFF4D6;border:1px solid {GOLD};color:#8A6D1A;font-weight:700;font-size:14px;padding:8px 16px;border-radius:8px;margin-top:8px}}
.step{{display:flex;align-items:center;gap:18px;margin-top:18px}}
.num{{width:50px;height:50px;border-radius:50%;background:{NAVY};color:{GOLD};font-size:22px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}}
.stxt{{font-size:19px}}
.techgrid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-top:34px}}
.techbox{{background:{NAVY2};border:1px solid {GREEN};border-radius:4px;padding:26px;text-align:center;font-size:20px;font-weight:700;color:#fff}}
.banner-i{{margin-top:26px;text-align:center;font-size:18px;font-style:italic;font-weight:700;color:{NAVY2}}}
.ladder{{display:flex;gap:14px;margin-top:34px}}
.lad{{flex:1;background:{CARD};border:1px solid {LINE};border-radius:5px;padding:18px 12px;text-align:center}}
.lad.hot{{background:{NAVY};border-color:{NAVY}}}
.ln{{font-size:15px;font-weight:700;color:{MUTED}}} .lad.hot .ln{{color:{GOLD}}}
.lt{{font-size:15px;font-weight:700;margin:12px 0;min-height:42px}} .lad.hot .lt{{color:#fff}}
.ld{{font-size:12px;color:{MUTED}}} .lad.hot .ld{{color:{GOLD}}}
.role{{color:{GOLD};font-weight:700;font-size:15px;margin-bottom:12px}}
.askrow{{display:flex;align-items:center;background:{NAVY2};border-left:5px solid {GOLD};border-radius:4px;padding:20px 22px;margin-top:16px}}
.al{{color:{GOLD};font-weight:700;width:220px;font-size:18px}} .ar{{color:#fff;font-size:16px}}
'''
out=f'''<!doctype html><html><head><meta charset="utf-8"><title>TrigunAI Company Pitch v2</title><style>{css}</style></head><body>{"".join(slides)}</body></html>'''
path=os.path.join(REPO,"outreach/Trigunai_Company_Pitch_v2.html")
with open(path,"w") as f: f.write(out)
print("wrote",path)
