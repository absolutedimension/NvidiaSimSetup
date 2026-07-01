#!/usr/bin/env python3
"""Build the 'What is an Agent' teaching diagrams (SVG -> PNG via Chrome headless)."""
import subprocess, tempfile, os
from pathlib import Path

OUT = Path(__file__).parent / "images"
OUT.mkdir(parents=True, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ── shared style ────────────────────────────────────────────────────────────
INK="#23232b"; MUT="#8a8a99"; IND="#5b63e6"; INDK="#4a52d6"
LAV="#eef0fb"; LAVBD="#c9d0f5"; GOLD="#d99a2b"; GOLDBG="#fbf1da"; GOLDBD="#e8c98c"
GRN="#22c55e"; LINE="#e6e6ee"; FONT="'Avenir Next','Helvetica Neue',Arial,sans-serif"

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" font-family="{FONT}">'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')

def render(name, w, h, body):
    s = svg(w, h, body)
    (OUT / f"{name}.svg").write_text(s)
    html = f'<!doctype html><html><body style="margin:0;padding:0">{s}</body></html>'
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html); tmp = f.name
    subprocess.run([CHROME,"--headless","--disable-gpu","--hide-scrollbars",
                    "--force-device-scale-factor=2",f"--window-size={w},{h}",
                    f"--screenshot={OUT}/{name}.png", f"file://{tmp}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(tmp)
    print(f"  ✓ {name}.png")

# helpers ---------------------------------------------------------------------
def rect(x,y,w,h,fill,stroke="none",rx=14,sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def txt(x,y,s,size=20,fill=INK,weight=400,anchor="middle"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{s}</text>'
def line(x1,y1,x2,y2,stroke=MUT,sw=2,dash=""):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
def arrow(x1,y1,x2,y2,stroke=IND,sw=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" marker-end="url(#ah)"/>')
ARROWHEAD=f'<defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="{IND}"/></marker><marker id="ahg" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="{GOLD}"/></marker><marker id="ahm" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="{MUT}"/></marker></defs>'

# ── D1 — the wanting / future projection ────────────────────────────────────
def d1():
    b=ARROWHEAD
    b+=txt(600,54,"A goal is a projection of yourself into the future",30,INK,600)
    b+=txt(600,86,"Dream · Goal · Outcome · Desire — different words, one shape: a state that does not exist yet, that you pull toward.",17,MUT,400)
    # axis
    y=300
    b+=f'<line x1="120" y1="{y}" x2="1080" y2="{y}" stroke="{IND}" stroke-width="4" marker-end="url(#ah)"/>'
    # NOW node
    b+=f'<circle cx="140" cy="{y}" r="34" fill="{LAV}" stroke="{IND}" stroke-width="3"/>'
    b+=txt(140,y+6,"YOU",17,INDK,600)
    b+=txt(140,y+70,"present state",15,MUT)
    # FUTURE star
    b+=f'<circle cx="1040" cy="{y}" r="40" fill="{GOLDBG}" stroke="{GOLD}" stroke-width="3"/>'
    b+=txt(1040,y+7,"★",30,GOLD,700)
    b+=txt(1040,y+78,"desired state",15,GOLD,600)
    # markers along the axis
    def mark(x,label,desc,col,bg,bd,dash=""):
        s=rect(x-95,y-150,190,76,bg,bd,12)
        s+=txt(x,y-122,label,19,col,600)
        s+=txt(x,y-98,desc,13,MUT)
        s+=line(x,y-74,x,y-12,col,2,dash)
        s+=f'<circle cx="{x}" cy="{y}" r="7" fill="{col}"/>'
        return s
    b+=mark(380,"DESIRE","the fuel — why you move",GRN,"#eaf9ef","#bfe9cd")
    b+=mark(620,"GOAL","named + dated + committed",INDK,LAV,LAVBD)
    b+=mark(860,"OUTCOME","the measurable end-state",INDK,LAV,LAVBD)
    # dream far/fuzzy
    b+=txt(1040,y-120,"DREAM",19,GOLD,600)
    b+=txt(1040,y-96,"far · fuzzy · pulls",13,MUT)
    b+=line(1040,y-74,1040,y-44,GOLD,2,"4 4")
    b+=txt(600,470,"Define:  a goal is a future state you are committed to bringing into reality.",18,INDK,600)
    render("d1_wanting",1200,520,b)

# ── D2 — inside a goal: activity + feedback ─────────────────────────────────
def d2():
    b=ARROWHEAD
    b+=txt(600,50,"Look inside a goal — you never find one action",30,INK,600)
    b+=txt(600,82,"You find a structure: many activities running in a direction, each sensing where it is and feeding a correction back to your system.",16,MUT)
    # goal box
    b+=rect(470,120,260,56,LAV,LAVBD,14); b+=txt(600,155,"THE GOAL",22,INDK,600)
    # system box (right)
    b+=rect(960,250,200,90,GOLDBG,GOLDBD,14)
    b+=txt(1060,285,"YOUR SYSTEM",16,GOLD,600); b+=txt(1060,310,"state / skill /",13,MUT); b+=txt(1060,328,"resources",13,MUT)
    # activities row
    xs=[140,320,500,680]; ay=270; aw=150; ah=70
    labels=["Activity 1","Activity 2","Activity 3","Activity 4"]
    for i,x in enumerate(xs):
        b+=rect(x,ay,aw,ah,"#fff",IND,14)
        b+=txt(x+aw/2,ay+34,labels[i],16,INK,600)
        b+=txt(x+aw/2,ay+55,"do → result",12,MUT)
        if i<len(xs)-1:
            b+=arrow(x+aw,ay+ah/2,xs[i+1],ay+ah/2)
    # goal feeds first activity
    b+=arrow(540,176,215,ay)
    # each activity feeds feedback up to system, system adjusts next
    for x in xs:
        b+=f'<path d="M{x+aw/2},{ay+ah} C {x+aw/2},{ay+150} {960},{420} {1010},{340}" fill="none" stroke="{MUT}" stroke-width="2" stroke-dasharray="5 5" marker-end="url(#ahm)"/>'
    # system loops back to activities
    b+=f'<path d="M960,295 C 760,180 360,150 290,{ay}" fill="none" stroke="{GOLD}" stroke-width="2.5" marker-end="url(#ahg)"/>'
    b+=txt(560,470,"feedback",13,MUT,400,"start")
    b+=txt(600,500,"The unit of a goal is not “an action.”  It is an activity + its feedback loop.",18,INDK,600)
    render("d2_inside_goal",1200,560,b)

# ── D3 — small / medium / hard ──────────────────────────────────────────────
def d3():
    import math, random
    random.seed(7)
    b=ARROWHEAD
    b+=txt(650,50,"Same structure at every size — only the count changes",30,INK,600)
    b+=txt(650,82,"The harder the goal, the more activities, the more feedback — all orchestrated into one direction.",16,MUT)
    cols=[("SMALL","make a cup of tea",3,170),("MEDIUM","clear a certification",8,620),("HARD","build a company",22,1090)]
    for title,sub,n,cx in cols:
        b+=txt(cx,140,title,22,INDK,700)
        b+=txt(cx,166,sub,14,MUT)
        # nodes scattered in a box
        bx,by,bw,bh=cx-150,190,300,260
        pts=[]
        for i in range(n):
            px=bx+30+random.random()*(bw-60); py=by+20+random.random()*(bh-50)
            pts.append((px,py))
        # connect some
        for i in range(len(pts)):
            for j in range(i+1,len(pts)):
                if random.random()< (0.25 if n>10 else 0.5):
                    b+=line(pts[i][0],pts[i][1],pts[j][0],pts[j][1],LINE,1.4)
        for px,py in pts:
            b+=f'<circle cx="{px}" cy="{py}" r="9" fill="{LAV}" stroke="{IND}" stroke-width="1.6"/>'
        b+=txt(cx,by+bh+6,f"{n} activities",13,MUT)
        # direction arrow
        b+=f'<line x1="{cx-120}" y1="510" x2="{cx+120}" y2="510" stroke="{GOLD}" stroke-width="3.5" marker-end="url(#ahg)"/>'
    b+=txt(650,560,"one direction",14,GOLD,600)
    render("d3_sizes",1300,580,b)

# ── D4 — zoom to the agent ──────────────────────────────────────────────────
def d4():
    import random; random.seed(3)
    b=ARROWHEAD
    b+=txt(600,50,"Keep zooming in — the smallest unit is an Agent",30,INK,600)
    b+=txt(600,82,"The smallest self-contained part of the goal that can sense, decide, act, and adjust on its own.",16,MUT)
    # faded web left
    bx,by,bw,bh=70,150,300,300; pts=[]
    for i in range(14):
        pts.append((bx+20+random.random()*(bw-40), by+20+random.random()*(bh-40)))
    for i in range(len(pts)):
        for j in range(i+1,len(pts)):
            if random.random()<0.18:
                b+=line(*pts[i],*pts[j],"#eceef6",1.4)
    for px,py in pts:
        b+=f'<circle cx="{px}" cy="{py}" r="8" fill="#eef0fb" stroke="#cfd3ec" stroke-width="1.4"/>'
    # highlight one node
    hx,hy=pts[5]
    b+=f'<circle cx="{hx}" cy="{hy}" r="12" fill="{GOLDBG}" stroke="{GOLD}" stroke-width="3"/>'
    b+=txt(220,470,"your goal (a web of tasks)",13,MUT)
    # zoom lines to the big agent circle
    cx,cy,R=830,300,180
    b+=line(hx+10,hy-6,cx-R+10,cy-R+40,GOLD,2,"5 5")
    b+=line(hx+10,hy+6,cx-R+10,cy+R-40,GOLD,2,"5 5")
    # big agent
    b+=f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{GOLDBG}" stroke="{GOLD}" stroke-width="3"/>'
    b+=txt(cx,cy-R+34,"AGENT",24,GOLD,700)
    # micro loop 4 steps
    steps=[("SENSE",cx,cy-95),("DECIDE",cx+95,cy),("ACT",cx,cy+95),("FEEDBACK",cx-95,cy)]
    for s,x,y in steps:
        b+=f'<circle cx="{x}" cy="{y}" r="40" fill="#fff" stroke="{IND}" stroke-width="2"/>'
        b+=txt(x,y+5,s,14,INDK,600)
    # arrows around
    b+=f'<path d="M{cx+30},{cy-78} A 80 80 0 0 1 {cx+78},{cy-30}" fill="none" stroke="{IND}" stroke-width="2.5" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx+78},{cy+30} A 80 80 0 0 1 {cx+30},{cy+78}" fill="none" stroke="{IND}" stroke-width="2.5" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx-30},{cy+78} A 80 80 0 0 1 {cx-78},{cy+30}" fill="none" stroke="{IND}" stroke-width="2.5" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx-78},{cy-30} A 80 80 0 0 1 {cx-30},{cy-78}" fill="none" stroke="{IND}" stroke-width="2.5" marker-end="url(#ah)"/>'
    b+=txt(600,520,"An agent = the smallest thing that pursues a sub-goal on its own, with its own perceive → act → adjust loop.",17,INDK,600)
    render("d4_agent_zoom",1200,560,b)

# ── D5 — goal as agentic system (hierarchy) ─────────────────────────────────
def d5():
    b=ARROWHEAD
    b+=txt(600,50,"So any goal is a complex agentic system",30,INK,600)
    b+=txt(600,82,"A hierarchy: the goal on top, sub-goals beneath, and at the leaves — agents doing the real sensing and acting.",16,MUT)
    # goal
    b+=rect(490,120,220,56,LAV,LAVBD,14); b+=txt(600,155,"GOAL",22,INDK,700)
    subs=[280,600,920]
    for sx in subs:
        b+=arrow(600,176,sx,250)
        b+=rect(sx-110,250,220,52,"#fff",IND,14); b+=txt(sx,282,"sub-goal",18,INK,600)
    # agents under each sub
    ax=[ -150,-50,50,150]
    for sx in subs:
        for dx in ax:
            x=sx+dx*0.9
            b+=arrow(sx,302,x,370)
            b+=f'<rect x="{x-52}" y="370" width="104" height="46" rx="12" fill="{GOLDBG}" stroke="{GOLD}" stroke-width="2"/>'
            b+=txt(x,398,"agent",15,GOLD,600)
    b+=txt(600,500,"future projection  =  multi-agent system.   This course teaches you to build it, deliberately.",18,INDK,600)
    render("d5_hierarchy",1200,560,b)

# ── D6 — human ↔ AI agent same loop ─────────────────────────────────────────
def d6():
    b=ARROWHEAD
    b+=txt(600,50,"Human or AI — the agent is the same loop",30,INK,600)
    b+=txt(600,82,"Made of will and muscle, or of an LLM and tools — the shape is identical.",16,MUT)
    cx,cy,R=600,300,120
    steps=[("PERCEIVE",cx,cy-R),("DECIDE",cx+R,cy),("ACT",cx,cy+R),("OBSERVE",cx-R,cy)]
    for s,x,y in steps:
        b+=f'<circle cx="{x}" cy="{y}" r="58" fill="{LAV}" stroke="{IND}" stroke-width="2.5"/>'
        b+=txt(x,y+5,s,16,INDK,700)
    b+=f'<path d="M{cx+45},{cy-R+30} A {R} {R} 0 0 1 {cx+R-30},{cy-45}" fill="none" stroke="{IND}" stroke-width="3" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx+R-30},{cy+45} A {R} {R} 0 0 1 {cx+45},{cy+R-30}" fill="none" stroke="{IND}" stroke-width="3" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx-45},{cy+R-30} A {R} {R} 0 0 1 {cx-R+30},{cy+45}" fill="none" stroke="{IND}" stroke-width="3" marker-end="url(#ah)"/>'
    b+=f'<path d="M{cx-R+30},{cy-45} A {R} {R} 0 0 1 {cx-45},{cy-R+30}" fill="none" stroke="{IND}" stroke-width="3" marker-end="url(#ah)"/>'
    # left human / right AI mappings
    rows=[("PERCEIVE","see where you are","read input · context · tool results",110),
          ("DECIDE","think what to do","the LLM reasons",195),
          ("ACT","do it","call a tool / API",280),
          ("OBSERVE","read the feedback","read the result, loop again",365)]
    b+=txt(150,90,"HUMAN",16,GRN,700,"start")
    b+=txt(1050,90,"AI AGENT",16,GOLD,700,"end")
    for step,h,a,yy in rows:
        b+=txt(150,yy,f"{step}: {h}",14,INK,500,"start")
        b+=txt(1050,yy,f"{step}: {a}",14,INK,500,"end")
    b+=txt(600,500,"A chatbot answers once.  An agent runs the loop until the job is done.",19,INDK,700)
    render("d6_loop",1200,560,b)

for fn in (d1,d2,d3,d4,d5,d6):
    fn()
print("All diagrams rendered.")
