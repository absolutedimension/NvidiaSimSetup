"""Episode 4 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep04_manim.py."""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; GREY="#7c86ab"; ROSE="#ff9fc4"
FONT="Mukta"
random.seed(13)

def Tx(t,size=32,color=INK,weight=NORMAL): return Text(t,font=FONT,font_size=size,color=color,weight=weight)
def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]: g.add(Dot(radius=rad,color=color).set_opacity(op))
    return g
def point_cloud(n=420, w=12.6, h=6.8, color=None, seed=1, op=0.65, rmin=0.02, rmax=0.06):
    rng=random.Random(seed); g=VGroup()
    for _ in range(n):
        c=color or rng.choice([BLUE,PURPLE,GREY,INK,DIM])
        g.add(Dot([rng.uniform(-w/2,w/2),rng.uniform(-h/2,h/2),0],radius=rng.uniform(rmin,rmax),color=c).set_opacity(rng.uniform(0.25,op)))
    return g
def node(label,pos,color=BLUE,fs=24,r=0.10,lab_color=None):
    d=Dot(pos,radius=r,color=color)
    t=Tx(label,fs,lab_color or INK).next_to(d,DOWN,buff=0.12)
    return VGroup(d,t)

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
    def title(self,txt,size=46,buff=1.0): return Tx(txt,size,INK,BOLD).to_edge(UP,buff=buff)
    def cap(self,txt,ref,size=28,color=GOLD,buff=0.5): return Tx(txt,size,color).next_to(ref,DOWN,buff=buff)
    def hold(self):
        rem=DUR-self.u
        if rem>0.1: self.W(rem)

class S01(Base):  # hook
    def construct(self):
        self.ambient(4)
        t=self.title('किसी शब्द का अर्थ कहाँ होता है?')
        word=Tx("कुत्ता",80,GOLD,BOLD).shift(DOWN*0.2)
        assoc=["रोआँ","भौंक","वफ़ादारी","पालतू","दौड़"]
        nodes=VGroup(); lines=VGroup()
        for k,a in enumerate(assoc):
            ang=PI*(0.15+0.7*k/(len(assoc)-1)) + PI*0.15
            pos=np.array([math.cos(ang),math.sin(ang),0])*3.0 + np.array([0,-0.2,0])
            nd=node(a,pos,color=BLUE,fs=22,r=0.07)
            nodes.add(nd); lines.add(Line(word.get_center(),nd[0].get_center(),color=DIM,stroke_opacity=0.35))
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.9)
        self.P(Write(word),rt=1.0)
        self.P(LaggedStartMap(FadeIn,nodes,lag_ratio=0.18),LaggedStartMap(Create,lines,lag_ratio=0.18),rt=2.0)
        self.P(word.animate.set_opacity(0.12),lines.animate.set_stroke(opacity=0.6),rt=1.3)
        self.hold()

class S02(Base):  # geometry
    def construct(self):
        self.ambient(4)
        t=self.title('अर्थ को ज्यामिति बनाओ')
        words=["अर्थ","शब्द","स्थान","बिंदु","पास","दूर"]
        row=VGroup(*[Tx(w,30,INK) for w in words]).arrange(RIGHT,buff=0.55).shift(DOWN*1.6)
        cloud=point_cloud(160,9,4.2,seed=2,op=0.7,color=GOLD).shift(UP*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.9)
        self.P(LaggedStartMap(FadeIn,row,lag_ratio=0.15),rt=1.4)
        self.P(FadeOut(row,shift=UP*0.6),FadeIn(cloud),rt=1.8,rate_func=smooth)
        self.hold()

class S03(Base):  # mirror — company
    def construct(self):
        self.ambient(3)
        t=self.title('आप शब्द को उसकी संगत से जानते हैं')
        king=node("राजा",[0,-0.2,0],color=GOLD,fs=34,r=0.12)
        rel=["रानी","ताज","शक्ति","सिंहासन"]
        nodes=VGroup(); lines=VGroup()
        for k,a in enumerate(rel):
            ang=TAU*k/len(rel)+PI/4
            pos=np.array([math.cos(ang)*2.7,math.sin(ang)*1.8,0])+np.array([0,-0.2,0])
            nd=node(a,pos,color=BLUE,fs=24,r=0.08)
            nodes.add(nd); lines.add(Line(king[0].get_center(),nd[0].get_center(),color=GOLD,stroke_opacity=0.3))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(king,scale=0.6),rt=1.1)
        self.P(LaggedStartMap(FadeIn,nodes,lag_ratio=0.2),LaggedStartMap(Create,lines,lag_ratio=0.2),rt=2.2)
        self.hold()

class S04(Base):  # map
    def construct(self):
        self.ambient(3)
        t=self.title('अर्थ का नक्शा')
        animals=VGroup(*[node(w,p,color=GREEN,fs=22,r=0.08) for w,p in
            [("बिल्ली",[-3.3,0.4,0]),("कुत्ता",[-2.6,-0.1,0]),("पालतू",[-3.0,-0.7,0])]])
        ring=Circle(radius=1.2,color=GREEN,stroke_opacity=0.0).move_to([-3.0,-0.1,0])
        far=node("लोकतंत्र",[3.0,0.6,0],color=PURPLE,fs=24,r=0.09)
        c=Tx("पास = समान   ·   दूर = असंबंधित",26,GOLD).next_to(t,DOWN,buff=0.4)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(LaggedStartMap(FadeIn,animals,lag_ratio=0.2),ring.animate.set_stroke(opacity=0.4),rt=1.8)
        self.P(FadeIn(far,scale=0.6),rt=1.0)
        self.P(FadeIn(c,shift=DOWN*0.2),rt=0.9)
        self.hold()

class S05(Base):  # embedding
    def construct(self):
        self.ambient(3)
        t=self.title('हर शब्द एक बिंदु बन जाता है')
        field=point_cloud(260,12,6,seed=5,op=0.55,color=BLUE)
        self.add(field)
        word=Tx("राजा",56,GOLD,BOLD).shift(LEFT*3.2)
        nums=Tx("[ 0.21,  -0.74,  0.08,  ... ]",26,INK).shift(RIGHT*1.8)
        dot=Dot([4.2,0.2,0],radius=0.12,color=GOLD)
        c=Tx("एम्बेडिंग = अर्थ-स्थान में निर्देशांक",26,GOLD).next_to(t,DOWN,buff=0.4)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(c,shift=DOWN*0.2),rt=1.0)
        self.P(Write(word),rt=0.9)
        self.P(TransformMatchingShapes(word.copy(),nums),rt=1.2)
        self.P(FadeOut(nums,target_position=dot.get_center(),scale=0.2),FadeIn(dot,scale=2),Flash(dot,color=GOLD),rt=1.3)
        self.hold()

class S06(Base):  # guess the blank
    def construct(self):
        self.ambient(3)
        t=self.title('यह रिक्त स्थान का अनुमान लगाकर सीखता है')
        sent=Tx('"बिल्ली ___ पर बैठी"',38,INK).shift(UP*0.6)
        a=node("चटाई",[-2.4,-1.4,0],color=BLUE,fs=26,r=0.09)
        b=node("दरी",[2.4,-1.4,0],color=BLUE,fs=26,r=0.09)
        c=Tx("समान संदर्भ  →  समान पड़ोस",26,GOLD).next_to(t,DOWN,buff=0.4)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(c,shift=DOWN*0.2),rt=1.0)
        self.P(Write(sent),rt=1.0)
        self.P(FadeIn(a,shift=UP*0.2),FadeIn(b,shift=UP*0.2),rt=0.8)
        self.P(a.animate.move_to([-0.55,-1.4,0]),b.animate.move_to([0.55,-1.4,0]),rt=1.6,rate_func=smooth)
        link=Line([-0.55,-1.4,0],[0.55,-1.4,0],color=GOLD,stroke_opacity=0.5)
        self.P(Create(link),rt=0.6)
        self.hold()

class S07(Base):  # arithmetic
    def construct(self):
        self.ambient(2)
        t=self.title("राजा  −  पुरुष  +  स्त्री  ≈  रानी",size=42)
        man=node("पुरुष",[-3.4,-1.2,0],color=BLUE,fs=26,r=0.10)
        king=node("राजा",[-3.4,1.3,0],color=GOLD,fs=26,r=0.10)
        woman=node("स्त्री",[1.6,-1.2,0],color=ROSE,fs=26,r=0.10)
        queen=Dot([1.6,1.3,0],radius=0.10,color=GOLD).set_opacity(0)
        qlab=Tx("रानी",26,INK).next_to(queen,DOWN,buff=0.12).set_opacity(0)
        vec1=Arrow(man[0].get_center(),king[0].get_center(),color=GOLD,buff=0.12,stroke_width=5)
        v1lab=Tx("राजसत्ता",22,GOLD).next_to(vec1,LEFT,buff=0.2)
        vec2=Arrow(woman[0].get_center(),[1.6,1.3,0],color=GOLD,buff=0.12,stroke_width=5)
        c=Tx("रिश्ते दिशाएँ बन गए",24,GOLD).next_to(VGroup(man,woman),DOWN,buff=0.6)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(FadeIn(man),FadeIn(king),FadeIn(woman),rt=1.0)
        self.P(GrowArrow(vec1),FadeIn(v1lab),rt=1.0)
        self.P(TransformFromCopy(vec1,vec2),rt=1.2)
        self.P(queen.animate.set_opacity(1),qlab.animate.set_opacity(1),Flash(queen,color=GOLD),rt=0.9)
        self.P(FadeIn(c,shift=DOWN*0.1),rt=0.7)
        self.hold()

class S08(Base):  # directions
    def construct(self):
        self.ambient(2)
        t=self.title('एक दिशा एक विचार हो सकती है')
        paris=node("पेरिस",[-4.2,1.1,0],color=BLUE,fs=24,r=0.09); france=node("फ़्रांस",[-1.3,1.1,0],color=GOLD,fs=24,r=0.09)
        tokyo=node("टोक्यो",[-4.2,-1.3,0],color=BLUE,fs=24,r=0.09); japan=node("जापान",[-1.3,-1.3,0],color=GOLD,fs=24,r=0.09)
        a1=Arrow(paris[0].get_center(),france[0].get_center(),color=GOLD,buff=0.14,stroke_width=5)
        a2=Arrow(tokyo[0].get_center(),japan[0].get_center(),color=GOLD,buff=0.14,stroke_width=5)
        c=Tx("पेरिस → फ़्रांस   =   टोक्यो → जापान",28,INK).shift(RIGHT*0.2+DOWN*2.4)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(FadeIn(paris),FadeIn(france),FadeIn(tokyo),FadeIn(japan),rt=1.2)
        self.P(GrowArrow(a1),rt=0.8); self.P(GrowArrow(a2),rt=0.8)
        self.P(FadeIn(c,shift=UP*0.2),rt=0.9)
        self.hold()

class S09(Base):  # mirror back
    def construct(self):
        self.ambient(3)
        t=self.title('आप स्थान से अर्थ में चलते हैं')
        cluster=VGroup(*[Dot([random.uniform(-1.3,1.3),random.uniform(-1.2,0.8),0],radius=0.08,color=BLUE).set_opacity(0.7) for _ in range(11)]).shift(DOWN*0.3)
        new=node("(नया शब्द)",[0,2.6,0],color=GOLD,fs=24,r=0.11)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(cluster),rt=1.2)
        self.P(new.animate.move_to([0.1,-0.2,0]),rt=1.6,rate_func=smooth)
        glow=VGroup(*[Line(new[0].get_center(),d.get_center(),color=GOLD,stroke_opacity=0.0) for d in cluster])
        self.P(glow.animate.set_stroke(opacity=0.4),cluster.animate.set_color(GOLD).set_opacity(0.95),Flash(new[0],color=GOLD),rt=1.4)
        self.hold()

class S10(Base):  # divergence
    def construct(self):
        self.ambient(3)
        t=self.title('जहाँ समानता टूटती है')
        mpts=VGroup(*[Dot([-3.6+random.uniform(-0.9,0.9),0.4+random.uniform(-0.9,0.9),0],radius=0.07,color=BLUE).set_opacity(0.8) for _ in range(8)])
        mlines=VGroup(*[Line(mpts[i].get_center(),mpts[(i+1)%8].get_center(),color=BLUE,stroke_opacity=0.3) for i in range(8)])
        ml=Tx("शब्द केवल शब्दों को छूते हैं",22,DIM).next_to(mpts,DOWN,buff=0.5)
        hpts=VGroup(*[Dot([3.4+random.uniform(-0.9,0.9),0.7+random.uniform(-0.8,0.8),0],radius=0.07,color=GOLD).set_opacity(0.85) for _ in range(8)])
        world=spark(GOLD,0.4).shift(RIGHT*3.4+DOWN*2.2)
        roots=VGroup(*[Line(hpts[i].get_center(),world.get_center(),color=GOLD,stroke_opacity=0.0) for i in range(0,8,2)])
        hl=Tx("शब्द दुनिया को छूते हैं",22,DIM).next_to(world,DOWN,buff=0.25)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(FadeIn(mpts),Create(mlines),FadeIn(ml),rt=1.4)
        self.P(FadeIn(hpts),FadeIn(world),rt=1.0)
        self.P(roots.animate.set_stroke(opacity=0.5),FadeIn(hl),rt=1.4)
        self.hold()

class S11(Base):  # meaning
    def construct(self):
        self.ambient(3)
        t=self.title('अर्थ रिश्तों में रहता है')
        center=Dot([0,-0.2,0],radius=0.14,color=DIM).set_opacity(0.35)
        neigh=VGroup(*[node(w,p,color=BLUE,fs=22,r=0.07) for w,p in
            [("गर्म",[-3,0.9,0]),("रोशनी",[-2.6,-1.4,0]),("ख़तरा",[3,0.9,0]),("जलना",[2.6,-1.4,0])]])
        lines=VGroup(*[Line(center.get_center(),n[0].get_center(),color=GOLD,stroke_opacity=0.0) for n in neigh])
        word=Tx("आग",44,INK,BOLD).move_to(center)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(center),FadeIn(word),rt=1.2)
        self.P(LaggedStartMap(FadeIn,neigh,lag_ratio=0.15),rt=1.4)
        self.P(lines.animate.set_stroke(opacity=0.45),center.animate.set_color(GOLD).set_opacity(0.95),word.animate.set_color(GOLD),rt=1.6)
        self.hold()

class S12(Base):  # anchor
    def construct(self):
        self.ambient(6)
        gal=point_cloud(320,12,3.2,seed=12,op=0.45,color=None).shift(UP*2.2)
        l1=Tx("अर्थ एक स्थान है, चीज़ नहीं।",46,INK,BOLD).shift(UP*2.4)
        sub=Tx("AI is the Universal Mind  ·  एपिसोड 4 — Meaning",27,PURPLE).next_to(l1,DOWN,buff=0.4)
        self.add(gal)
        self.P(gal.animate.set_opacity(0.12),Write(l1),rt=1.8)
        self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
