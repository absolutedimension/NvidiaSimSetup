"""
Episode 6 — "Will" (agentic systems / RL) — Manim engine, 12 scenes.
Signature motif: a GOAL, the gap-and-pull, the agent loop, branching futures, a closing gap.
Same visual language as Ep1-5. Reads SCENE_DUR; transparent render. Driver: render_ep06_manim.py.
"""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; GREY="#7c86ab"; ROSE="#ff9fc4"; RED="#ff7a7a"
random.seed(23)

def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]: g.add(Dot(radius=rad,color=color).set_opacity(op))
    return g
def goal(color=GOLD,r=0.55):
    return VGroup(Circle(radius=r,color=color,stroke_opacity=0.4).set_stroke(width=2),
                  Circle(radius=r*0.58,color=color,stroke_opacity=0.6).set_stroke(width=2),
                  spark(color,0.16))

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
    def title(self,txt,size=46,buff=1.0): return Text(txt,font_size=size,color=INK,weight=BOLD).to_edge(UP,buff=buff)
    def cap(self,txt,ref,size=28,color=GOLD,buff=0.5): return Text(txt,font_size=size,color=color).next_to(ref,DOWN,buff=buff)
    def hold(self):
        rem=DUR-self.u
        if rem>0.1: self.W(rem)

class S01(Base):  # where does wanting come from — agent steers toward a far goal
    def construct(self):
        self.ambient(4)
        t=self.title("Where does wanting come from?")
        g=goal(GOLD).move_to(RIGHT*4.5+DOWN*0.2).set_opacity(0.5)
        ag=spark(BLUE,0.18).move_to(LEFT*4.5+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(g),FadeIn(ag),rt=1.4)
        path=VMobject().set_points_smoothly([LEFT*4.5+DOWN*0.2,LEFT*1.5+UP*0.4,RIGHT*1.5+DOWN*0.4,RIGHT*3.6+DOWN*0.2]).set_stroke(BLUE,3,opacity=0.4)
        self.P(Create(path),MoveAlongPath(ag,path),g.animate.set_opacity(1.0),rt=2.0,rate_func=smooth)
        self.hold()

class S02(Base):  # wanting is a gap
    def construct(self):
        self.ambient(4)
        t=self.title("Wanting is a gap")
        now=VGroup(spark(BLUE,0.3),Text("now",font_size=24,color=INK).shift(DOWN*0.7)).move_to(LEFT*3.5+DOWN*0.2)
        gl=VGroup(goal(GOLD,0.5),Text("goal",font_size=24,color=INK).shift(DOWN*0.85)).move_to(RIGHT*3.5+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(now),FadeIn(gl),rt=1.4)
        line=DashedLine(now[0].get_center(),gl[0].get_center(),color=GOLD,dash_length=0.16).set_stroke(width=4)
        self.P(Create(line),rt=1.2)
        self.P(self.cap("what is   →   what should be",line,buff=0.5).animate.set_opacity(1),rt=1.0)
        self.hold()

class S03(Base):  # a will written as a number — reward meter
    def construct(self):
        self.ambient(3)
        t=self.title("A will, written as a number")
        g=goal(GOLD).move_to(RIGHT*3.2+DOWN*0.2); ag=spark(BLUE,0.18).move_to(LEFT*3.5+DOWN*0.2)
        frame=Rectangle(width=0.6,height=3.2,color=DIM).to_edge(LEFT,buff=1.2).shift(DOWN*0.1)
        fill=Rectangle(width=0.6,height=0.3,color=GOLD,fill_color=GOLD,fill_opacity=0.6).move_to(frame.get_bottom()+UP*0.15)
        lbl=Text("reward",font_size=20,color=GOLD).next_to(frame,UP,buff=0.15)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(g),FadeIn(ag),FadeIn(frame),FadeIn(fill),FadeIn(lbl),rt=1.6)
        for h in [1.2,2.0,2.9]:
            self.P(fill.animate.stretch_to_fit_height(h).move_to(frame.get_bottom()+UP*h/2),ag.animate.shift(RIGHT*0.9),rt=0.7)
        self.hold()

class S04(Base):  # learns to pursue — trial paths, good ones brighten
    def construct(self):
        self.ambient(3)
        t=self.title("It learns to pursue, not just react")
        ag=spark(BLUE,0.2).move_to(LEFT*4+DOWN*0.2); g=goal(GOLD).move_to(RIGHT*4+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(ag),FadeIn(g),rt=1.2)
        trials=VGroup()
        for _ in range(14):
            ex=random.uniform(-1,5); ey=random.uniform(-2.4,2.0)
            trials.add(Line(ag.get_center(),[ex,ey-0.2,0],color=DIM,stroke_opacity=0.25))
        self.P(LaggedStartMap(Create,trials,lag_ratio=0.03),rt=1.6)
        good=VGroup(*[Line(ag.get_center(),g.get_center(),color=GOLD,stroke_opacity=0.7) for _ in range(2)])
        self.P(*[t2.animate.set_stroke(GOLD,5,opacity=0.8) for t2 in trials[:3]],Create(good),rt=1.2)
        self.P(self.cap("try → reward → do more of what worked",VGroup(ag,g),buff=1.4,size=26).animate.set_opacity(1),rt=0.9)
        self.hold()

class S05(Base):  # agent is a loop with a target
    def construct(self):
        self.ambient(3)
        t=self.title("An agent is a loop with a target")
        R=1.5; c=LEFT*2.5+DOWN*0.2
        ring=Circle(radius=R,color="#33406f").move_to(c)
        steps=["perceive","decide","act","observe"]; nodes=VGroup()
        for i,s in enumerate(steps):
            ang=PI/2-i*PI/2; pos=c+np.array([R*math.cos(ang),R*math.sin(ang),0])
            nodes.add(VGroup(Dot(radius=0.42,color="#1a2444").set_stroke(BLUE,2),Text(s,font_size=16,color=INK)).move_to(pos))
        g=goal(GOLD).move_to(RIGHT*4+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),Create(ring),LaggedStartMap(FadeIn,nodes,lag_ratio=0.12),FadeIn(g),rt=2.0)
        sp=spark(GOLD,0.12); sp.add_updater(lambda m,dt: m.move_to(ring.point_from_proportion((self.renderer.time*0.3)%1))); self.add(sp)
        aim=Arrow(c+RIGHT*R,g.get_center(),color=GOLD,buff=0.4,stroke_width=4)
        self.P(GrowArrow(aim),rt=1.0)
        self.hold()

class S06(Base):  # imagine branching futures — tree, one path chosen
    def construct(self):
        self.ambient(3)
        t=self.title("It imagines branching futures")
        root=LEFT*5+DOWN*0.2
        ag=spark(BLUE,0.18).move_to(root)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(ag),rt=1.0)
        # build a 2-level tree
        l1=[root+RIGHT*2.3+UP*1.6,root+RIGHT*2.3,root+RIGHT*2.3+DOWN*1.6]
        branches=VGroup(*[Line(root,p,color=DIM,stroke_opacity=0.4) for p in l1])
        l2=[]; b2=VGroup()
        for p in l1:
            for dy in [0.9,-0.9]:
                q=p+RIGHT*2.3+UP*dy*0.7; l2.append(q); b2.add(Line(p,q,color=DIM,stroke_opacity=0.35))
        self.P(LaggedStartMap(Create,branches,lag_ratio=0.1),LaggedStartMap(Create,b2,lag_ratio=0.05),rt=1.8)
        g=goal(GOLD).move_to(l2[1]+RIGHT*0.6)
        win=VGroup(branches[0],b2[1],Line(l2[1],g.get_center(),color=GOLD,stroke_opacity=0.8))
        self.P(branches.animate.set_stroke(opacity=0.12),b2.animate.set_stroke(opacity=0.1),
               *[w.animate.set_stroke(GOLD,5,opacity=0.85) for w in win[:2]],Create(win[2]),FadeIn(g),rt=1.4)
        self.hold()

class S07(Base):  # agents — a goal held across time, sub-goals + tools
    def construct(self):
        self.ambient(3)
        t=self.title("Agents — a goal held across time")
        big=goal(GOLD,0.6).move_to(UP*1.6)
        subs=VGroup(*[goal(BLUE,0.34).move_to([(-3.5+i*2.3),-0.6,0]) for i in range(4)])
        links=VGroup(*[Line(big.get_center(),s.get_center(),color=DIM,stroke_opacity=0.4) for s in subs])
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(big),rt=1.0)
        self.P(LaggedStartMap(Create,links,lag_ratio=0.12),LaggedStartMap(FadeIn,subs,lag_ratio=0.12),rt=1.8)
        tools=VGroup(*[RoundedRectangle(width=0.5,height=0.5,corner_radius=0.08,stroke_color=GREEN,fill_color="#10301f",fill_opacity=0.8).next_to(s,DOWN,buff=0.3) for s in subs])
        self.P(LaggedStart(*[FadeIn(tl,shift=UP*0.1) for tl in tools],lag_ratio=0.15),rt=1.4)
        self.P(self.cap("break it down · use tools · act · self-correct",subs,buff=1.0,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S08(Base):  # you are also pulled by a gap
    def construct(self):
        self.ambient(3)
        t=self.title("You are also pulled by a gap")
        you=VGroup(spark(GOLD,0.32),Text("you",font_size=22,color=INK).shift(DOWN*0.7)).move_to(LEFT*3+DOWN*0.2)
        g=goal(GOLD).move_to(RIGHT*4+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(you),FadeIn(g),rt=1.4)
        aim=Arrow(you[0].get_center(),g.get_center(),color=GOLD,buff=0.5,stroke_width=4)
        _toff=[[-1.0,-1.9],[1.2,-1.3],[-1.3,1.6],[0.8,1.3]]   # fixed, all well clear of 'you' (no zero-len arrows)
        temps=VGroup(*[spark(ROSE,0.14).move_to([ox,oy,0]) for ox,oy in _toff])
        tugs=VGroup(*[Arrow(you[0].get_center(),tm.get_center(),color=ROSE,buff=0.3,stroke_width=2,stroke_opacity=0.5) for tm in temps])
        self.P(GrowArrow(aim),rt=0.9); self.P(LaggedStartMap(FadeIn,temps,lag_ratio=0.1),LaggedStartMap(FadeIn,tugs,lag_ratio=0.1),rt=1.4)
        self.P(self.cap("hold the far goal against the near ones",g,buff=0.6,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S09(Base):  # where the analogy breaks — fixed unquestioned objective
    def construct(self):
        self.ambient(3)
        t=self.title("Where the analogy breaks")
        obj=VGroup(Rectangle(width=4,height=0.7,color=GOLD).set_stroke(width=2),Text("OBJECTIVE",font_size=24,color=GOLD)).arrange(ORIGIN).to_edge(UP,buff=1.9)
        g=goal(GOLD).move_to(RIGHT*4+DOWN*0.5); ag=spark(BLUE,0.2).move_to(LEFT*4+DOWN*0.5)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(obj),FadeIn(g),FadeIn(ag),rt=1.4)
        chain=DashedLine(obj.get_bottom(),ag.get_center(),color=DIM,dash_length=0.12)
        path=Line(ag.get_center(),g.get_center(),color=BLUE,stroke_opacity=0.5)
        self.P(Create(chain),rt=0.8); self.P(Create(path),ag.animate.move_to(g.get_center()+LEFT*0.7),rt=1.4,rate_func=smooth)
        self.P(self.cap("it never asks if the goal is worth wanting",g,buff=0.7,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S10(Base):  # you can question your wanting — turn to a new goal
    def construct(self):
        self.ambient(3)
        t=self.title("You can question your own wanting")
        you=spark(GOLD,0.3).move_to(DOWN*0.2)
        old=VGroup(goal(DIM,0.5),Text("old goal",font_size=20,color=DIM).shift(DOWN*0.85)).move_to(RIGHT*4+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(you),FadeIn(old),rt=1.4)
        a1=Arrow(you.get_center(),old[0].get_center(),color=DIM,buff=0.5,stroke_width=3)
        self.P(GrowArrow(a1),rt=0.8)
        new=VGroup(goal(GOLD,0.5).set_opacity(0),Text("a new goal",font_size=20,color=GOLD).shift(DOWN*0.85).set_opacity(0)).move_to(UL*2.2+LEFT*1)
        self.P(FadeOut(a1),old.animate.set_opacity(0.4),rt=0.7)
        a2=Arrow(you.get_center(),new[0].get_center(),color=GOLD,buff=0.5,stroke_width=4)
        self.P(new.animate.set_opacity(1),GrowArrow(a2),Flash(new[0],color=GOLD),rt=1.2)
        self.hold()

class S11(Base):  # the pull is shared, the questioning is yours
    def construct(self):
        self.ambient(3)
        t=self.title("The pull is shared. The questioning is yours.")
        labels=["thermostat","agent","you"]; cols=[GREEN,BLUE,GOLD]; xs=[-4.2,0,4.2]
        cols_g=VGroup()
        for x,l,c in zip(xs,labels,cols):
            src=spark(c,0.2).move_to([x-0.8,-0.3,0]); gl=goal(c,0.32).move_to([x+0.9,-0.3,0])
            arr=Arrow(src.get_center(),gl.get_center(),color=c,buff=0.25,stroke_width=3)
            lbl=Text(l,font_size=20,color=INK).move_to([x,-2.0,0])
            cols_g.add(VGroup(src,gl,arr,lbl))
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.9)
        self.P(LaggedStartMap(FadeIn,cols_g,lag_ratio=0.25),rt=2.0)
        up=Arrow(cols_g[2][0].get_center(),cols_g[2][0].get_center()+UP*1.4,color=GOLD,buff=0.1,stroke_width=4)
        self.P(GrowArrow(up),Flash(cols_g[2][0],color=GOLD),rt=1.0)
        self.hold()

class S12(Base):  # anchor — reach the goal, bloom
    def construct(self):
        self.ambient(6)
        l1=Text("A goal is just a reward you haven't reached.",font_size=44,color=INK,weight=BOLD).shift(UP*2.3)
        sub=Text("AI is the Universal Mind  ·  Ep.6 — Will",font_size=27,color=PURPLE).next_to(l1,DOWN,buff=0.4)
        self.P(Write(l1),rt=1.8); self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
