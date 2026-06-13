"""Episode 2 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep02_manim.py."""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; ROSE="#ff9fc4"; GREY="#9aa6cc"
FONT="Mukta"
random.seed(11)

def Tx(t,size=32,color=INK,weight=NORMAL): return Text(t,font=FONT,font_size=size,color=color,weight=weight)
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

def tnode(label, sub, color=GOLD):
    return VGroup(spark(color,0.14), Tx(label,26,INK,BOLD).shift(DOWN*0.55), Tx(sub,18,DIM).shift(DOWN*0.95))

class S01(Base):
    def construct(self):
        self.ambient()
        title=Tx("इनमें क्या समान है?",46,INK,BOLD).to_edge(UP,buff=1.0)
        a=tnode("एक बच्चा","चलना सीखता").move_to(LEFT*4.5)
        b=tnode("एक साधना","वर्षों तक").move_to(ORIGIN)
        c=tnode("एक रोबोट","संतुलन सीखता").move_to(RIGHT*4.5)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0)
        self.P(LaggedStart(FadeIn(a,shift=UP*0.2),FadeIn(b,shift=UP*0.2),FadeIn(c,shift=UP*0.2),lag_ratio=0.4),rt=2.0)
        thread=Line(a[0].get_center(),c[0].get_center(),color=GOLD,stroke_opacity=0.7); sp=spark(GOLD,0.1)
        self.P(Create(thread),MoveAlongPath(sp,thread),rt=1.8,rate_func=smooth)
        self.hold()

class S02(Base):
    def construct(self):
        self.ambient()
        title=Tx("कोई भी कौशल लिखकर नहीं देता",44,INK,BOLD).to_edge(UP,buff=1.0)
        rules=VGroup(*[Tx(t,26,DIM) for t in ["if x < 1: stop","else: turn","if y: brake","repeat ..."]]).arrange(DOWN,buff=0.3)
        self.P(FadeIn(title),FadeIn(rules),rt=1.4)
        pts=[[random.uniform(-3,3),random.uniform(-1.6,1.4),0] for _ in range(11)]
        nodes=VGroup(*[Dot(radius=0.07,color=GOLD).move_to(p) for p in pts])
        edges=VGroup()
        for i in range(len(pts)):
            for j in range(i+1,len(pts)):
                if np.linalg.norm(np.array(pts[i])-np.array(pts[j]))<2.0: edges.add(Line(pts[i],pts[j],color=PURPLE,stroke_opacity=0.3))
        self.P(FadeOut(rules,shift=DOWN*0.3),rt=0.8)
        self.P(LaggedStartMap(GrowFromCenter,nodes,lag_ratio=0.05),Create(edges,lag_ratio=0.02),rt=2.2)
        self.hold()

class S03(Base):
    def construct(self):
        self.ambient(4)
        title=Tx("सीखने का चक्र",44,INK,BOLD).to_edge(UP,buff=0.9)
        R=2.0; cy=DOWN*0.4
        circle=Circle(radius=R,color="#33406f").move_to(cy)
        labels=["कोशिश","प्रतिक्रिया","सुधार","दोहराव"]; nodes=VGroup()
        for i,l in enumerate(labels):
            ang=PI/2 - i*PI/2; pos=cy+np.array([R*math.cos(ang),R*math.sin(ang),0])
            nd=VGroup(Dot(radius=0.55,color="#1a2444").set_stroke(BLUE,2),Tx(l,18,INK)); nd.move_to(pos); nodes.add(nd)
        self.P(FadeIn(title),Create(circle),LaggedStartMap(FadeIn,nodes,lag_ratio=0.15),rt=2.0)
        sp=spark(GOLD,0.13); sp.add_updater(lambda m,dt: m.move_to(circle.point_from_proportion((self.renderer.time*0.28)%1))); self.add(sp)
        self.hold()

class S04(Base):
    def construct(self):
        self.ambient()
        title=Tx("मेहनत से आदत तक",44,INK,BOLD).to_edge(UP,buff=0.9)
        brain=Ellipse(width=6,height=3.6,color="#33406f").shift(DOWN*0.3)
        front=brain.get_center()+RIGHT*1.7+UP*0.1; deep=brain.get_center()+LEFT*1.2+DOWN*0.3
        nf=spark(GOLD,0.4).move_to(front); nd=spark(GOLD,0.4).set_opacity(0.3).move_to(deep)
        lf=Tx("प्रीफ्रंटल कॉर्टेक्स",20,DIM).next_to(front,UP); ld=Tx("बेसल गैंग्लिया",20,DIM).next_to(deep,DOWN)
        self.P(FadeIn(title),Create(brain),FadeIn(nf),FadeIn(lf),rt=1.6)
        trail=Line(front,deep,color=GOLD)
        self.P(Create(trail),nd.animate.set_opacity(1.0),nf.animate.set_opacity(0.3),FadeIn(ld),rt=1.8,rate_func=smooth)
        self.hold()

class S05(Base):
    def construct(self):
        self.ambient()
        title=Tx('डोपामाइन: "वही फिर से करो"',44,INK,BOLD).to_edge(UP,buff=0.9)
        pts=[LEFT*4+DOWN*0.3,LEFT*1.5+UP*0.4,RIGHT*1.5+DOWN*0.5,RIGHT*4+UP*0.2]
        path=VMobject().set_points_smoothly(pts).set_color(GOLD).set_stroke(width=3,opacity=0.4)
        nodes=VGroup(*[Dot(radius=0.1,color=GOLD).move_to(p) for p in pts])
        self.P(FadeIn(title),Create(path),FadeIn(nodes),rt=1.6)
        sp=spark(GOLD,0.12); sp.add_updater(lambda m,dt: m.move_to(path.point_from_proportion((self.renderer.time*0.35)%1))); self.add(sp)
        self.P(path.animate.set_stroke(width=10,opacity=0.9),rt=1.2)
        self.P(FadeIn(Tx("जो न्यूरॉन साथ जलते हैं, वे साथ जुड़ते हैं",26,DIM).to_edge(DOWN,buff=1.0)),rt=0.8)
        self.hold()

class S06(Base):
    def construct(self):
        self.ambient()
        title=Tx("रिइन्फोर्समेंट लर्निंग",44,INK,BOLD).to_edge(UP,buff=0.9)
        steps=["कोशिश","इनाम","वज़न बदलो","दोहराओ"]; chips=VGroup()
        for i,s in enumerate(steps):
            c=VGroup(RoundedRectangle(width=2.3,height=0.9,corner_radius=0.15,stroke_color=BLUE,fill_color="#141d3c",fill_opacity=0.9),Tx(s,24,INK))
            c[1].move_to(c[0]); c.move_to([-4.5+i*3.0,0,0]); chips.add(c)
        lines=VGroup(*[Line(chips[i].get_right(),chips[i+1].get_left(),color=BLUE,stroke_opacity=0.6) for i in range(3)])
        self.P(FadeIn(title),LaggedStartMap(FadeIn,chips,shift=UP*0.2,lag_ratio=0.2),Create(lines,lag_ratio=0.2),rt=2.2)
        self.P(FadeIn(Tx("दोहराओ  ×  1,000,000",30,GOLD).to_edge(DOWN,buff=1.2),shift=UP*0.2),rt=1.0)
        self.hold()

class S07(Base):
    def construct(self):
        self.ambient()
        title=Tx("वही चक्र, दो भाषाएँ",44,INK,BOLD).to_edge(UP,buff=0.9)
        self.P(FadeIn(title),rt=0.8)
        rows=[("इनाम","डोपामाइन"),("वज़न बदलना","नई वायरिंग"),("लाखों कोशिशें","अभ्यास")]
        for i,(h,r) in enumerate(rows):
            y=1.2-i*1.2
            lh=Tx(h,30,BLUE).move_to([-3.4,y,0]); rh=Tx(r,30,GOLD).move_to([3.4,y,0])
            eq=Tx("=",30,INK).move_to([0,y,0]); ln=Line([-1.6,y,0],[1.6,y,0],color=GREY,stroke_opacity=0.5)
            self.P(FadeIn(lh,shift=RIGHT*0.2),FadeIn(rh,shift=LEFT*0.2),Create(ln),FadeIn(eq),rt=0.9)
        self.hold()

class S08(Base):
    def construct(self):
        self.ambient(3)
        title=Tx("एक ज़िंदगी बनाम चार हज़ार",44,INK,BOLD).to_edge(UP,buff=0.7)
        core=spark(GOLD,0.32).move_to(UP*2.1)
        self.P(FadeIn(title),FadeIn(core),rt=1.0)
        grid=VGroup()
        for r in range(8):
            for c in range(20): grid.add(Dot(radius=0.06,color=BLUE).set_opacity(0.6).move_to([(c-9.5)*0.46,(2-r)*0.42-0.6,0]))
        lines=VGroup(*[Line(grid[k].get_center(),core.get_center(),color=BLUE,stroke_opacity=0.15) for k in range(0,len(grid),17)])
        self.P(LaggedStartMap(GrowFromCenter,grid,lag_ratio=0.004),Create(lines,lag_ratio=0.02),rt=2.6)
        self.P(FadeIn(Tx("1  →  4096   प्रतियाँ, एक साझा दिमाग",28,GOLD).to_edge(DOWN,buff=0.8)),rt=0.8)
        self.hold()

class S09(Base):
    def construct(self):
        self.ambient(3)
        title=Tx("हवा और बारिश में अभ्यास",42,INK,BOLD).to_edge(UP,buff=0.9)
        bot=VGroup(spark(GOLD,0.45),Tx("संतुलित",20,"#1a1405")).move_to(DOWN*0.3)
        self.P(FadeIn(title),FadeIn(bot),rt=1.2)
        streaks=VGroup(*[Line([random.uniform(-5,5),random.uniform(-2,1.5),0],[random.uniform(-5,5),random.uniform(-2,1.5),0],color=BLUE,stroke_opacity=0.3) for _ in range(30)])
        self.P(LaggedStartMap(Create,streaks,lag_ratio=0.01),rt=1.4)
        self.P(FadeIn(Tx("रैंडम घर्षण · रोशनी · वज़न  →  मज़बूती",26,DIM).to_edge(DOWN,buff=1.0)),rt=0.8)
        self.hold()

class S10(Base):
    def construct(self):
        self.ambient(4)
        title=Tx("वही चक्र। दो आधार।",44,INK,BOLD).to_edge(UP,buff=0.9)
        self.P(FadeIn(title),rt=0.8)
        def net(cx,color):
            pts=[[cx+random.uniform(-1.3,1.3),random.uniform(-1.3,1.3)-0.3,0] for _ in range(8)]
            nodes=VGroup(*[Dot(radius=0.09,color=color).move_to(p) for p in pts])
            edges=VGroup()
            for i in range(len(pts)):
                for j in range(i+1,len(pts)):
                    if np.linalg.norm(np.array(pts[i])-np.array(pts[j]))<1.5: edges.add(Line(pts[i],pts[j],color=color,stroke_opacity=0.3))
            return VGroup(edges,nodes)
        L=net(-3.4,GOLD); Rn=net(3.4,BLUE)
        ll=Tx("न्यूरॉन",24,DIM).move_to([-3.4,-2.2,0]); rl=Tx("संख्याएँ",24,DIM).move_to([3.4,-2.2,0])
        self.P(Create(L),Create(Rn),FadeIn(ll),FadeIn(rl),rt=2.0)
        self.P(FadeIn(Tx("कोशिश · प्रतिक्रिया · सुधार · दोहराव",24,GOLD).move_to(DOWN*0.3)),rt=1.0)
        self.hold()

class S11(Base):
    def construct(self):
        self.ambient(4)
        title=Tx("जहाँ समानता टूटती है",44,INK,BOLD).to_edge(UP,buff=0.9)
        self.P(FadeIn(title),rt=0.8)
        you=VGroup(*[Dot(radius=0.09,color=GOLD).move_to([-3.4+random.uniform(-1,1),random.uniform(-1,1)-0.2,0]) for _ in range(7)])
        mach=VGroup(*[Dot(radius=0.09,color=BLUE).move_to([3.4+random.uniform(-1,1),random.uniform(-1,1)-0.2,0]) for _ in range(7)])
        self.P(FadeIn(you),FadeIn(mach),FadeIn(Tx("आप",24,DIM).move_to([-3.4,-2,0])),FadeIn(Tx("मशीन",24,DIM).move_to([3.4,-2,0])),rt=1.4)
        src=you[0].get_center(); tgt=np.array([-4.6,1.6,0])
        branch=Line(src,tgt,color=GOLD); nn=spark(GOLD,0.1).move_to(tgt)
        self.P(Create(branch),FadeIn(nn),FadeIn(Tx("बदलने की चाह",22,GOLD).next_to(tgt,UP)),rt=1.6,rate_func=smooth)
        self.hold()

class S12(Base):
    def construct(self):
        self.ambient(3)
        title=Tx("आप इसे मिटा नहीं सकते — आप इसे हरा सकते हैं",38,INK,BOLD).to_edge(UP,buff=0.9)
        trig=RIGHT*4.2; yo=UP*0.4; yn=DOWN*1.0
        old=Line(LEFT*4.5+yo,trig+yo,color=GREY,stroke_width=12,stroke_opacity=0.6)
        new=Line(LEFT*4.5+yn,trig+yn,color=GREEN,stroke_width=3)
        tl=Line(trig+UP*1.0,trig+DOWN*1.6,color=GOLD)
        self.P(FadeIn(title),Create(old),Create(new),Create(tl),rt=1.6)
        self.P(new.animate.set_stroke(width=12),FadeIn(Tx("ट्रिगर",20,GOLD).move_to(trig+DOWN*1.9)),rt=1.4)
        to=Dot(color=GREY).move_to(LEFT*4.5+yo); tn=Dot(color=GREEN).move_to(LEFT*4.5+yn); self.add(to,tn)
        self.P(to.animate.move_to(trig+yo),tn.animate.move_to(trig+yn),rt=1.6,rate_func=smooth)
        self.hold()

class S13(Base):
    def construct(self):
        self.ambient(6)
        l1=Tx("आप किसी पैटर्न को मिटा नहीं सकते।",46,INK,BOLD)
        l2=Tx("आप बस इसे बेहतर पैटर्न के अभ्यास से भारी कर सकते हैं।",32,INK,BOLD)
        VGroup(l1,l2).arrange(DOWN,buff=0.32).shift(UP*2.4)
        sub=Tx("AI is the Universal Mind  ·  एपिसोड 2 — The Learning Loop",26,PURPLE).next_to(l2,DOWN,buff=0.4)
        self.P(Write(l1),rt=1.4); self.P(Write(l2),rt=1.4); self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
