"""
Episode 2 — "The Learning Loop" — Manim engine (dynamic rebuild).
All motion-graphics. Reads SCENE_DUR per scene; ambient drift + camera push keep it alive.
Transparent render → composite over reactive circuit_mind shader + frozen audio.
"""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; ROSE="#ff9fc4"; GREY="#9aa6cc"
random.seed(11)

def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]:
        g.add(Dot(radius=rad,color=color).set_opacity(op))
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
    g=VGroup(spark(color,0.14), Text(label,font_size=26,color=INK).shift(DOWN*0.55),
             Text(sub,font_size=18,color=DIM).shift(DOWN*0.95))
    return g

class S01(Base):  # what do they share — three icons + thread
    def construct(self):
        self.ambient()
        title=Text("What do they share?",font_size=46,color=INK).to_edge(UP,buff=1.0)
        a=tnode("a child","learning to walk").move_to(LEFT*4.5)
        b=tnode("a discipline","held for years").move_to(ORIGIN)
        c=tnode("a robot","learning to balance").move_to(RIGHT*4.5)
        self.P(FadeIn(title,shift=DOWN*0.2),rt=1.0)
        self.P(LaggedStart(FadeIn(a,shift=UP*0.2),FadeIn(b,shift=UP*0.2),FadeIn(c,shift=UP*0.2),lag_ratio=0.4),rt=2.0)
        thread=Line(a[0].get_center(),c[0].get_center(),color=GOLD,stroke_opacity=0.7)
        sp=spark(GOLD,0.1)
        self.P(Create(thread),MoveAlongPath(sp,thread),rt=1.8,rate_func=smooth)
        self.hold()

class S02(Base):  # nobody writes the skill down — rules dissolve into a web
    def construct(self):
        self.ambient()
        title=Text("Nobody writes the skill down",font_size=44,color=INK).to_edge(UP,buff=1.0)
        rules=VGroup(*[Text(t,font_size=26,color=DIM) for t in ["if x < 1: stop","else: turn","if y: brake","repeat ..."]]).arrange(DOWN,buff=0.3)
        self.P(FadeIn(title),FadeIn(rules),rt=1.4)
        pts=[[random.uniform(-3,3),random.uniform(-1.6,1.4),0] for _ in range(11)]
        nodes=VGroup(*[Dot(radius=0.07,color=GOLD).move_to(p) for p in pts])
        edges=VGroup()
        for i in range(len(pts)):
            for j in range(i+1,len(pts)):
                if np.linalg.norm(np.array(pts[i])-np.array(pts[j]))<2.0:
                    edges.add(Line(pts[i],pts[j],color=PURPLE,stroke_opacity=0.3))
        self.P(FadeOut(rules,shift=DOWN*0.3),rt=0.8)
        self.P(LaggedStartMap(GrowFromCenter,nodes,lag_ratio=0.05),Create(edges,lag_ratio=0.02),rt=2.2)
        self.hold()

class S03(Base):  # the learning loop — spinning ring + traveling spark
    def construct(self):
        self.ambient(4)
        title=Text("The Learning Loop",font_size=44,color=INK).to_edge(UP,buff=0.9)
        R=2.0; cy=DOWN*0.4
        circle=Circle(radius=R,color="#33406f").move_to(cy)
        labels=["TRY","FEEDBACK","UPDATE","REPEAT"]; nodes=VGroup()
        for i,l in enumerate(labels):
            ang=PI/2 - i*PI/2
            pos=cy+np.array([R*math.cos(ang),R*math.sin(ang),0])
            nd=VGroup(Dot(radius=0.5,color="#1a2444").set_stroke(BLUE,2),
                      Text(l,font_size=20,color=INK))
            nd.move_to(pos); nodes.add(nd)
        self.P(FadeIn(title),Create(circle),LaggedStartMap(FadeIn,nodes,lag_ratio=0.15),rt=2.0)
        sp=spark(GOLD,0.13)
        sp.add_updater(lambda m,dt: m.move_to(circle.point_from_proportion((self.renderer.time*0.28)%1)))
        self.add(sp)
        self.hold()

class S04(Base):  # effort -> autopilot
    def construct(self):
        self.ambient()
        title=Text("From effort to autopilot",font_size=44,color=INK).to_edge(UP,buff=0.9)
        brain=Ellipse(width=6,height=3.6,color="#33406f").shift(DOWN*0.3)
        front=brain.get_center()+RIGHT*1.7+UP*0.1
        deep=brain.get_center()+LEFT*1.2+DOWN*0.3
        nf=spark(GOLD,0.4).move_to(front); nd=spark(GOLD,0.4).set_opacity(0.3).move_to(deep)
        lf=Text("prefrontal cortex",font_size=20,color=DIM).next_to(front,UP)
        ld=Text("basal ganglia",font_size=20,color=DIM).next_to(deep,DOWN)
        self.P(FadeIn(title),Create(brain),FadeIn(nf),FadeIn(lf),rt=1.6)
        trail=Line(front,deep,color=GOLD)
        self.P(Create(trail),nd.animate.set_opacity(1.0),nf.animate.set_opacity(0.3),FadeIn(ld),rt=1.8,rate_func=smooth)
        self.hold()

class S05(Base):  # dopamine path
    def construct(self):
        self.ambient()
        title=Text('Dopamine: "do that again"',font_size=44,color=INK).to_edge(UP,buff=0.9)
        pts=[LEFT*4+DOWN*0.3,LEFT*1.5+UP*0.4,RIGHT*1.5+DOWN*0.5,RIGHT*4+UP*0.2]
        path=VMobject().set_points_smoothly(pts).set_color(GOLD).set_stroke(width=3,opacity=0.4)
        nodes=VGroup(*[Dot(radius=0.1,color=GOLD).move_to(p) for p in pts])
        self.P(FadeIn(title),Create(path),FadeIn(nodes),rt=1.6)
        sp=spark(GOLD,0.12)
        sp.add_updater(lambda m,dt: m.move_to(path.point_from_proportion((self.renderer.time*0.35)%1)))
        self.add(sp)
        self.P(path.animate.set_stroke(width=10,opacity=0.9),rt=1.2)
        cap=Text("neurons that fire together, wire together",font_size=26,color=DIM).to_edge(DOWN,buff=1.0)
        self.P(FadeIn(cap),rt=0.8)
        self.hold()

class S06(Base):  # RL loop chips + counter
    def construct(self):
        self.ambient()
        title=Text("Reinforcement learning",font_size=44,color=INK).to_edge(UP,buff=0.9)
        steps=["try","reward","nudge weights","repeat"]; chips=VGroup()
        for i,s in enumerate(steps):
            c=VGroup(RoundedRectangle(width=2.3,height=0.9,corner_radius=0.15,stroke_color=BLUE,fill_color="#141d3c",fill_opacity=0.9),Text(s,font_size=24,color=INK))
            c[1].move_to(c[0]); c.move_to([-4.5+i*3.0,0,0]); chips.add(c)
        lines=VGroup(*[Line(chips[i].get_right(),chips[i+1].get_left(),color=BLUE,stroke_opacity=0.6) for i in range(3)])
        self.P(FadeIn(title),LaggedStartMap(FadeIn,chips,shift=UP*0.2,lag_ratio=0.2),Create(lines,lag_ratio=0.2),rt=2.2)
        cnt=Text("repeat  ×  1,000,000",font_size=30,color=GOLD).to_edge(DOWN,buff=1.2)
        self.P(FadeIn(cnt,shift=UP*0.2),rt=1.0)
        self.hold()

class S07(Base):  # mapping rows
    def construct(self):
        self.ambient()
        title=Text("Same loop, two languages",font_size=44,color=INK).to_edge(UP,buff=0.9)
        self.P(FadeIn(title),rt=0.8)
        rows=[("reward","dopamine"),("weight update","rewiring"),("millions of tries","practice")]
        for i,(h,r) in enumerate(rows):
            y=1.2-i*1.2
            lh=Text(h,font_size=30,color=BLUE).move_to([-3.4,y,0]); rh=Text(r,font_size=30,color=GOLD).move_to([3.4,y,0])
            eq=Text("=",font_size=30,color=INK).move_to([0,y,0])
            ln=Line([-1.6,y,0],[1.6,y,0],color=GREY,stroke_opacity=0.5)
            self.P(FadeIn(lh,shift=RIGHT*0.2),FadeIn(rh,shift=LEFT*0.2),Create(ln),FadeIn(eq),rt=0.9)
        self.hold()

class S08(Base):  # one life vs four thousand — grid streams to a core
    def construct(self):
        self.ambient(3)
        title=Text("One life vs. four thousand",font_size=44,color=INK).to_edge(UP,buff=0.7)
        core=spark(GOLD,0.32).move_to(UP*2.1)
        self.P(FadeIn(title),FadeIn(core),rt=1.0)
        grid=VGroup()
        for r in range(8):
            for c in range(20):
                d=Dot(radius=0.06,color=BLUE).set_opacity(0.6).move_to([(c-9.5)*0.46,(2-r)*0.42-0.6,0])
                grid.add(d)
        lines=VGroup(*[Line(grid[k].get_center(),core.get_center(),color=BLUE,stroke_opacity=0.15) for k in range(0,len(grid),17)])
        self.P(LaggedStartMap(GrowFromCenter,grid,lag_ratio=0.004),Create(lines,lag_ratio=0.02),rt=2.6)
        cap=Text("1  →  4096   copies, one shared brain",font_size=28,color=GOLD).to_edge(DOWN,buff=0.8)
        self.P(FadeIn(cap),rt=0.8)
        self.hold()

class S09(Base):  # domain randomization — robot stays balanced amid chaos
    def construct(self):
        self.ambient(3)
        title=Text("Practice in the wind and the rain",font_size=42,color=INK).to_edge(UP,buff=0.9)
        bot=VGroup(spark(GOLD,0.45),Text("balanced",font_size=20,color="#1a1405")).move_to(DOWN*0.3)
        self.P(FadeIn(title),FadeIn(bot),rt=1.2)
        streaks=VGroup(*[Line([random.uniform(-5,5),random.uniform(-2,1.5),0],[random.uniform(-5,5),random.uniform(-2,1.5),0],color=BLUE,stroke_opacity=0.3) for _ in range(30)])
        self.P(LaggedStartMap(Create,streaks,lag_ratio=0.01),rt=1.4)
        cap=Text("random friction · lighting · weights  →  robustness",font_size=26,color=DIM).to_edge(DOWN,buff=1.0)
        self.P(FadeIn(cap),rt=0.8)
        self.hold()

class S10(Base):  # same loop, two substrates synced
    def construct(self):
        self.ambient(4)
        title=Text("Same loop. Two substrates.",font_size=44,color=INK).to_edge(UP,buff=0.9)
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
        ll=Text("neurons",font_size=24,color=DIM).move_to([-3.4,-2.2,0]); rl=Text("numbers",font_size=24,color=DIM).move_to([3.4,-2.2,0])
        self.P(Create(L),Create(Rn),FadeIn(ll),FadeIn(rl),rt=2.0)
        beat=Text("TRY  ·  FEEDBACK  ·  UPDATE  ·  REPEAT",font_size=24,color=GOLD).move_to(DOWN*0.3)
        self.P(FadeIn(beat),rt=1.0)
        self.hold()

class S11(Base):  # where the analogy breaks
    def construct(self):
        self.ambient(4)
        title=Text("Where the analogy breaks",font_size=44,color=INK).to_edge(UP,buff=0.9)
        self.P(FadeIn(title),rt=0.8)
        you=VGroup(*[Dot(radius=0.09,color=GOLD).move_to([-3.4+random.uniform(-1,1),random.uniform(-1,1)-0.2,0]) for _ in range(7)])
        mach=VGroup(*[Dot(radius=0.09,color=BLUE).move_to([3.4+random.uniform(-1,1),random.uniform(-1,1)-0.2,0]) for _ in range(7)])
        self.P(FadeIn(you),FadeIn(mach),FadeIn(Text("you",font_size=24,color=DIM).move_to([-3.4,-2,0])),FadeIn(Text("the machine",font_size=24,color=DIM).move_to([3.4,-2,0])),rt=1.4)
        src=you[0].get_center(); tgt=np.array([-4.6,1.6,0])
        branch=Line(src,tgt,color=GOLD); nn=spark(GOLD,0.1).move_to(tgt)
        self.P(Create(branch),FadeIn(nn),FadeIn(Text("a wish to change",font_size=22,color=GOLD).next_to(tgt,UP)),rt=1.6,rate_func=smooth)
        self.hold()

class S12(Base):  # you can't delete it — you outvote it
    def construct(self):
        self.ambient(3)
        title=Text("You can't delete it — you outvote it",font_size=42,color=INK).to_edge(UP,buff=0.9)
        trig=RIGHT*4.2; yo=UP*0.4; yn=DOWN*1.0
        old=Line(LEFT*4.5+yo,trig+yo,color=GREY,stroke_width=12,stroke_opacity=0.6)
        new=Line(LEFT*4.5+yn,trig+yn,color=GREEN,stroke_width=3)
        tl=Line(trig+UP*1.0,trig+DOWN*1.6,color=GOLD)
        self.P(FadeIn(title),Create(old),Create(new),Create(tl),rt=1.6)
        self.P(new.animate.set_stroke(width=12),FadeIn(Text("trigger",font_size=20,color=GOLD).move_to(trig+DOWN*1.9)),rt=1.4)
        to=Dot(color=GREY).move_to(LEFT*4.5+yo); tn=Dot(color=GREEN).move_to(LEFT*4.5+yn)
        self.add(to,tn)
        self.P(to.animate.move_to(trig+yo),tn.animate.move_to(trig+yn),rt=1.6,rate_func=smooth)
        self.hold()

class S13(Base):  # anchor
    def construct(self):
        self.ambient(6)
        l1=Text("You can't delete a pattern.",font_size=50,color=INK)
        l2=Text("You can only outweigh it with reps of a better one.",font_size=34,color=INK)
        VGroup(l1,l2).arrange(DOWN,buff=0.35).shift(UP*0.3)
        sub=Text("AI is the Universal Mind  ·  Ep.2 — The Learning Loop",font_size=26,color=PURPLE).next_to(l2,DOWN,buff=0.7)
        eth=Text("Look closely at one — and you understand the other.",font_size=24,color=DIM).next_to(sub,DOWN,buff=0.3)
        self.P(Write(l1),rt=1.4); self.P(Write(l2),rt=1.4)
        self.P(FadeIn(sub,shift=UP*0.2),rt=1.0); self.P(FadeIn(eth),rt=0.9)
        self.hold()
