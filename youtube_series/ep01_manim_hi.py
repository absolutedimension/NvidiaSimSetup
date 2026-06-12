"""Episode 1 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep01_manim.py."""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; ROSE="#ff9fc4"
FONT="Mukta"          # Devanagari + Latin
random.seed(7)

def T(txt, size, color=INK, weight=BOLD):
    return Text(txt, font=FONT, weight=weight, font_size=size, color=color)
def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]: g.add(Dot(radius=rad,color=color).set_opacity(op))
    return g

class Base(MovingCameraScene):
    def setup(self):
        super().setup(); self.u=0.0
    def P(self,*a,rt=1.0,**k): self.play(*a,run_time=rt,**k); self.u+=rt
    def W(self,t): self.wait(t); self.u+=t
    def ambient(self,n=7):
        dots=VGroup()
        for _ in range(n):
            d=Dot(radius=random.uniform(0.03,0.07),color=random.choice([BLUE,PURPLE,GREEN])).set_opacity(0.5)
            d.move_to([random.uniform(-6.5,6.5),random.uniform(-3.6,3.6),0])
            ph=random.uniform(0,6.28); sp=random.uniform(0.15,0.4)
            d.add_updater(lambda m,dt,ph=ph,sp=sp: m.shift(np.array([math.cos(ph+self.renderer.time*sp),math.sin(ph+self.renderer.time*sp*0.8),0])*0.004))
            dots.add(d)
        self.add(dots)
        self.camera.frame.add_updater(lambda m,dt: m.scale(1+0.0009*dt*30))
        return dots
    def hold(self):
        rem=DUR-self.u
        if rem>0.1: self.W(rem)

def lerp(a,b,t): return a+(b-a)*t
def sm(t): return 0.0 if t<=0 else 1.0 if t>=1 else t*t*(3-2*t)
def cl(x): return max(0.0,min(1.0,x))
def tc(d,cx,cy,txt,sz,fill):
    m=T(txt,sz,color=fill); m.move_to([cx,cy,0]); return m

SENT=["जानवर","ने","सड़क","पार","नहीं","की","क्योंकि","वह","थका","था"]
def lay_sentence(hi_idx=None):
    g=VGroup()
    for i,w in enumerate(SENT):
        g.add(T(w,38,color=GOLD if i==hi_idx else INK, weight=BOLD if i==hi_idx else NORMAL))
    g.arrange(RIGHT,buff=0.22)
    if g.width>13: g.scale(13/g.width)
    return g

class S01(Base):  # किस शब्द का मतलब है "वह"?
    def construct(self):
        self.ambient()
        title=T('किस शब्द का मतलब है "वह"?',46).to_edge(UP,buff=1.0)
        s=lay_sentence(7).shift(UP*0.2)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0)
        self.P(LaggedStartMap(FadeIn,s,shift=UP*0.2,lag_ratio=0.1),rt=1.6)
        it=s[7]; animal=s[0]
        self.P(Indicate(it,color=GOLD,scale_factor=1.5),rt=0.9)
        arc=ArcBetweenPoints(it.get_top(),animal.get_top(),angle=-PI/2.2,color=GOLD); sp=spark(GOLD,0.12)
        self.P(Create(arc),MoveAlongPath(sp,arc),rt=1.6,rate_func=smooth)
        self.P(Indicate(animal,color=GOLD,scale_factor=1.4),Flash(animal,color=GOLD),rt=0.9)
        self.hold()

class S02(Base):
    def construct(self):
        self.ambient()
        yr=T("2017",30,color=DIM).to_edge(UP,buff=1.0)
        card=RoundedRectangle(width=6.4,height=1.5,corner_radius=0.18,stroke_color=BLUE,fill_color="#141d3c",fill_opacity=0.9).shift(UP*0.6)
        lbl=T("Attention Is All You Need",34).move_to(card)
        self.P(FadeIn(yr),GrowFromCenter(card),rt=1.0); self.P(Write(lbl),rt=1.0)
        names=["ChatGPT","Claude","Gemini","Llama"]; chips=VGroup()
        for i,n in enumerate(names):
            x=-4.2+i*2.8
            c=VGroup(RoundedRectangle(width=2.1,height=0.7,corner_radius=0.14,stroke_color=PURPLE,fill_color="#1a1430",fill_opacity=0.9),T(n,26))
            c[1].move_to(c[0]); c.move_to([x,-2.3,0]); chips.add(c)
        lines=VGroup(*[Line(card.get_bottom(),ch.get_top(),color=BLUE,stroke_opacity=0.6) for ch in chips])
        self.P(LaggedStartMap(Create,lines,lag_ratio=0.15),LaggedStartMap(FadeIn,chips,shift=UP*0.2,lag_ratio=0.15),rt=2.2)
        self.hold()

class S03(Base):
    def construct(self):
        self.ambient(4)
        title=T("कॉकटेल पार्टी",46).to_edge(UP,buff=0.9)
        cap=T("एक आवाज़ साफ़ सुनाई देती है — आपका नाम",30,color=GOLD).next_to(title,DOWN,buff=0.25)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0); self.P(FadeIn(cap,shift=UP*0.2),rt=0.9)
        rings=VGroup(*[Circle(radius=r,color=GOLD,stroke_opacity=0.0) for r in [0.5,0.9]]).move_to([1.1,-0.2,0])
        for ring in rings: self.P(ring.animate.set_stroke(opacity=0.5).scale(1.5),rt=0.6,rate_func=there_and_back)
        self.hold()

class S04(Base):
    def construct(self):
        self.ambient(3)
        title=T("एक स्पॉटलाइट जो चुनता है कि क्या अनदेखा करना है",40).to_edge(UP,buff=0.9)
        cap=T("आपका दिमाग हमेशा चुनता है कि क्या अनदेखा करे",28,color=GOLD).next_to(title,DOWN,buff=0.25)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0); self.P(FadeIn(cap,shift=UP*0.2),rt=0.9); self.hold()

class S05(Base):
    def construct(self):
        self.ambient()
        title=T('मशीन "पीछे" कैसे देखती है?',44).to_edge(UP,buff=1.0)
        s=lay_sentence(7)
        self.P(FadeIn(title),FadeIn(s),rt=1.2)
        it=s[7]; sp=spark(GOLD,0.1).move_to(it); self.add(sp); y=it.get_center()
        for w in [s[2],s[0],s[8],s[0]]:
            beam=Line(it.get_center(),w.get_center(),color=BLUE,stroke_opacity=0.5)
            self.P(Create(beam),sp.animate.move_to(w),rt=0.7,rate_func=smooth); self.P(FadeOut(beam),sp.animate.move_to(it),rt=0.5)
        self.hold()

class S06(Base):
    def construct(self):
        self.ambient(4)
        W6=["जानवर","सड़क","पार","क्योंकि","वह","थका"]; gn=len(W6); IT,AN,ST=4,0,1
        title=T("हर शब्द हर दूसरे शब्द को आँकता है",40).to_edge(UP,buff=0.7)
        cells=VGroup(); cell=0.7; GRID=gn*cell+(gn-1)*0.08
        GX=(0-GRID)/2+70/100; GY=(0-GRID)/2+30/100
        grid=VGroup()
        import numpy as np
        for i in range(gn):
            for j in range(gn):
                sq=Square(side_length=cell,stroke_width=1,stroke_color="#2c3666",fill_color="#2a3a68",fill_opacity=0.15)
                sq.move_to([(j-gn/2)*0.78, (gn/2-i)*0.78-0.3, 0]); grid.add(sq); cells.add(sq)
        rowlabels=VGroup(*[T(W6[i],20,color=DIM).next_to(grid[i*gn],LEFT,buff=0.15) for i in range(gn)])
        self.P(FadeIn(title),Create(grid,lag_ratio=0.01),FadeIn(rowlabels),rt=2.0)
        random.seed(3)
        self.P(*[c.animate.set_fill(GOLD,opacity=random.uniform(0.1,0.7)) for c in cells],rt=1.4)
        nonit=VGroup(*[cells[i*gn+j] for i in range(gn) for j in range(gn) if i!=IT])
        self.P(nonit.animate.set_fill("#2a3a68",opacity=0.06),rt=1.0)
        itrow=[cells[IT*gn+j] for j in range(gn)]; weights={AN:0.97,ST:0.12,5:0.55,3:0.3}
        self.P(*[itrow[j].animate.set_fill(GOLD,opacity=weights.get(j,0.12)) for j in range(gn)],rt=1.2)
        lock=itrow[AN]; self.P(lock.animate.set_fill(GOLD,opacity=1).set_stroke(GOLD,3),Flash(lock,color=GOLD),rt=0.9)
        cap=T('"वह"  →  "जानवर"   "सड़क" नहीं',28,color=GOLD).next_to(grid,DOWN,buff=0.35)
        self.P(FadeIn(cap,shift=UP*0.2),rt=0.8); self.hold()

class S07(Base):
    def construct(self):
        self.ambient()
        title=T("Query · Key · Value",44).to_edge(UP,buff=1.0)
        it=VGroup(spark(BLUE,0.5),T('"वह"',30)).move_to(LEFT*3.5)
        an=VGroup(spark(GOLD,0.5),T('"जानवर"',28)).move_to(RIGHT*3.5)
        self.P(FadeIn(title),FadeIn(it,shift=RIGHT*0.3),FadeIn(an,shift=LEFT*0.3),rt=1.2)
        q=spark(BLUE,0.1).move_to(it); self.add(q); self.P(q.animate.move_to(an),rt=1.2,rate_func=smooth)
        link=Line(it.get_right(),an.get_left(),color=GOLD); self.P(Create(link),Flash(an,color=GOLD),rt=0.9)
        cap=T("सवाल से जवाब मिलता है — ध्यान सक्रिय होता है",26,color=GOLD).next_to(link,DOWN,buff=0.6)
        self.P(FadeIn(cap),rt=0.8); self.hold()

class S08(Base):
    def construct(self):
        self.ambient(3)
        title=T("एक ही क्रिया, अरबों बार दोहराई गई",40).to_edge(UP,buff=0.8)
        self.P(FadeIn(title),rt=0.8)
        layers=VGroup()
        for L in range(7):
            g=VGroup(*[Dot(radius=0.05,color=BLUE).set_opacity(0.5-L*0.05) for _ in range(36)])
            for k,d in enumerate(g): d.move_to([(k%6-2.5)*0.5+L*0.22,(k//6-2.5)*0.4+L*0.16-0.5,0])
            layers.add(g)
        self.P(LaggedStartMap(FadeIn,layers,shift=UP*0.2,lag_ratio=0.18),rt=2.4)
        self.P(layers.animate.shift(UP*0.3).set_opacity(0.7),rt=1.2,rate_func=there_and_back); self.hold()

class S09(Base):
    def construct(self):
        self.ambient(4)
        title=T("हमने एक औज़ार बनाया। हमें एक आईना मिला।",44).to_edge(UP,buff=0.9)
        cap=T("ध्यान — पहली बार दिखाई देता हुआ",28,color=GOLD).next_to(title,DOWN,buff=0.25)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0); self.P(FadeIn(cap,shift=UP*0.2),rt=0.9); self.hold()

class S10(Base):
    def construct(self):
        self.ambient(6)
        l1=T("बुद्धिमत्ता सब कुछ जानना नहीं है।",46)
        l2=T("यह जानना है कि क्या अनदेखा करना है।",46)
        VGroup(l1,l2).arrange(DOWN,buff=0.3).shift(UP*2.4)
        sub=T("AI is the Universal Mind  ·  Ep.1 — Attention",28,color=PURPLE).next_to(l2,DOWN,buff=0.4)
        self.P(Write(l1),rt=1.4); self.P(Write(l2),rt=1.4); self.P(FadeIn(sub,shift=UP*0.2),rt=1.0); self.hold()
