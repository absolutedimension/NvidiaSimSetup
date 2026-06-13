"""Episode 3 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep03_manim.py."""
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
def noise_field(n=420, w=12.6, h=6.8, color=None, seed=1, op=0.65):
    rng=random.Random(seed); g=VGroup()
    for _ in range(n):
        c=color or rng.choice([BLUE,PURPLE,GREY,INK,DIM])
        g.add(Dot([rng.uniform(-w/2,w/2),rng.uniform(-h/2,h/2),0],radius=rng.uniform(0.014,0.04),color=c).set_opacity(rng.uniform(0.2,op)))
    return g
def face_glyph(color=GOLD, s=1.0):
    eyes=VGroup(Dot(LEFT*0.5+UP*0.3,color=color,radius=0.11),Dot(RIGHT*0.5+UP*0.3,color=color,radius=0.11))
    mouth=Arc(radius=0.7,start_angle=PI+0.6,angle=PI-1.2,color=color).set_stroke(width=4).shift(UP*0.15)
    outline=Circle(radius=1.35,color=color,stroke_opacity=0.55).set_stroke(width=3)
    return VGroup(outline,eyes,mouth).scale(s)

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

class S01(Base):
    def construct(self):
        self.ambient(4)
        t=self.title("कोई नई चीज़ कहाँ से आती है?")
        nz=noise_field(260,8,4.5,seed=1,op=0.5).shift(DOWN*0.3)
        face=face_glyph(GOLD,1.1).set_opacity(0).shift(DOWN*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=1.0); self.P(FadeIn(nz),rt=1.0)
        self.P(nz.animate.set_opacity(0.18),face.animate.set_opacity(0.7),rt=1.6)
        self.P(face.animate.set_opacity(0.0),nz.animate.set_opacity(0.45),rt=1.4)
        self.hold()

class S02(Base):
    def construct(self):
        self.ambient(4)
        t=self.title("सृजन जोड़ना नहीं है")
        canvas=RoundedRectangle(width=4.4,height=2.8,corner_radius=0.1,stroke_color=INK,fill_color="#e9edfb",fill_opacity=0.85).shift(DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),GrowFromCenter(canvas),rt=1.2)
        crack=Line(canvas.get_top(),canvas.get_bottom(),color="#0b0f24").set_stroke(width=3)
        self.P(Create(crack),rt=0.6)
        lh=canvas.copy(); rh=canvas.copy()
        self.P(lh.animate.shift(LEFT*0.6+DOWN*2.5).rotate(-0.3).set_opacity(0),
               rh.animate.shift(RIGHT*0.6+DOWN*2.5).rotate(0.3).set_opacity(0),FadeOut(canvas),FadeOut(crack),rt=1.6)
        self.hold()

class S03(Base):
    def construct(self):
        t=self.title("यह शुद्ध शोर से शुरू होता है")
        nz=noise_field(620,13,7.2,seed=3,op=0.7); self.add(nz)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=1.0)
        for s in [5,7,9,11]: self.P(Transform(nz,noise_field(620,13,7.2,seed=s,op=0.7)),rt=0.5)
        self.hold()

class S04(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("मूर्ति हमेशा से संगमरमर में थी")
        block=noise_field(380,4.2,4.2,seed=4,op=0.7).shift(DOWN*0.3)
        form=face_glyph(GOLD,1.0).set_opacity(0).shift(DOWN*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(block),rt=1.2)
        self.P(LaggedStart(*[d.animate.shift([random.uniform(-3,3),random.uniform(-2,2),0]).set_opacity(0) for d in block],lag_ratio=0.002),
               form.animate.set_opacity(0.85),rt=2.2)
        self.P(self.cap("सृजन घटाने से, जोड़ने से नहीं",form,buff=0.6).animate.set_opacity(1),Flash(form,color=GOLD),rt=1.0)
        self.hold()

class S05(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("पहले — व्यवस्था को घुलते देखो")
        xs=[-4.8,-1.6,1.6,4.8]; stages=VGroup()
        for i,x in enumerate(xs):
            base=spark(GOLD,0.42); nz=noise_field(40+i*55,1.5,1.5,seed=20+i,op=0.2+i*0.22)
            stages.add(VGroup(base.set_opacity(max(0,1-i*0.32)),nz).move_to([x,0,0]))
        arrows=VGroup(*[Tx("→",40,DIM).move_to([(-3.2+j*3.2),0,0]) for j in range(3)])
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(LaggedStartMap(FadeIn,stages,lag_ratio=0.25),LaggedStartMap(FadeIn,arrows,lag_ratio=0.25),rt=2.4)
        self.P(self.cap("साफ़ छवि  →  +शोर  →  +शोर  →  स्थैतिक",stages,buff=0.7,size=26).animate.set_opacity(1),rt=1.0)
        self.hold()

class S06(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("फिर — इसे उल्टा चलाना सीखो")
        noisy=noise_field(300,4,3.4,seed=6,op=0.65).shift(DOWN*0.2)
        clean=spark(GOLD,0.5).shift(DOWN*0.2).set_opacity(0)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(noisy),rt=1.2)
        lbl=Tx("शोर का अनुमान लगाओ",24,BLUE).next_to(noisy,UP,buff=0.3)
        layer=noisy.copy(); self.P(FadeIn(lbl),rt=0.6)
        self.P(layer.animate.shift(UP*3).set_opacity(0),noisy.animate.set_opacity(0.25),clean.animate.set_opacity(0.7),rt=1.8)
        self.P(self.cap("इसे हटाओ → थोड़ा साफ़",clean,buff=0.6).animate.set_opacity(1),rt=0.9)
        self.hold()

class S07(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("शोर से — एक चीज़ जो कभी थी ही नहीं")
        nz=noise_field(560,11,6,seed=7,op=0.7); self.add(nz)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        face=face_glyph(GOLD,1.4).set_opacity(0)
        for k,op in enumerate([0.55,0.4,0.25,0.12]):
            self.P(Transform(nz,noise_field(560,11,6,seed=30+k,op=op)),face.animate.set_opacity(0.2+k*0.2),rt=0.55)
        self.P(nz.animate.set_opacity(0.06),face.animate.set_opacity(0.95),Flash(face,color=GOLD),rt=1.0)
        self.hold()

class S08(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("आपके शब्द ही गुरुत्वाकर्षण हैं")
        prompt=Tx('"एक बिल्ली, स्पेससूट में"',30,BLUE).shift(UP*1.4)
        nz=noise_field(360,9,3.4,seed=8,op=0.6).shift(DOWN*0.6)
        core=spark(GOLD,0.45).shift(DOWN*0.6).set_opacity(0)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(prompt,shift=DOWN*0.2),FadeIn(nz),rt=1.4)
        self.P(LaggedStart(*[d.animate.move_to([random.uniform(-1.2,1.2),random.uniform(-1.2,0),0]+np.array([0,-0.6,0])).set_opacity(0.3) for d in nz],lag_ratio=0.002),
               core.animate.set_opacity(0.8),rt=2.0)
        self.P(self.cap("शोर मिट्टी है · शब्द उसे आकार देते हैं",core,buff=0.6,size=26).animate.set_opacity(1),rt=0.9)
        self.hold()

class S09(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("आप भी कोहरे से आकार खींचते हैं")
        fog=VGroup(*[Dot([random.uniform(-2,2),random.uniform(-1.5,1),0],radius=random.uniform(0.05,0.13),color=PURPLE).set_opacity(0.3) for _ in range(120)]).shift(DOWN*0.2)
        word=Tx("विचार",72,INK,BOLD).set_opacity(0).shift(DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(fog),rt=1.2)
        self.P(fog.animate.scale(0.5).set_opacity(0.1),word.animate.set_opacity(1),rt=1.8,rate_func=smooth)
        self.P(self.cap("एक अंदेशा → एक विचार → एक वाक्य",word,buff=0.6).animate.set_opacity(1),rt=0.9)
        self.hold()

class S10(Base):
    def construct(self):
        self.ambient(4)
        t=self.title("जहाँ समानता टूटती है")
        machine=VGroup(Square(1.8,color=BLUE).set_stroke(width=2),face_glyph(BLUE,0.5)).move_to(LEFT*3.4+DOWN*0.2)
        human=face_glyph(GOLD,0.9).move_to(RIGHT*3.4+DOWN*0.2)
        ml=Tx("मशीन",22,DIM).next_to(machine,DOWN,buff=0.3); hl=Tx("आप",22,DIM).next_to(human,DOWN,buff=0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(machine),FadeIn(human),FadeIn(ml),FadeIn(hl),rt=1.6)
        self.P(Flash(human,color=GOLD),human.animate.scale(1.12),rt=0.9); self.P(human.animate.scale(1/1.12),rt=0.4)
        self.P(self.cap("यह आदेश पर सुधारता है — अपनी रचना से कभी चौंकता नहीं",VGroup(machine,human),buff=0.7,size=24).animate.set_opacity(1),rt=1.0)
        self.hold()

class S11(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("नवीनता अराजकता से खींची गई संरचना है")
        nz=noise_field(300,7,4,seed=11,op=0.6).shift(DOWN*0.2)
        lat=VGroup()
        for i in range(5):
            for j in range(7): lat.add(Dot([(j-3)*0.9,(2-i)*0.7-0.6,0],radius=0.06,color=GOLD))
        edges=VGroup()
        for k in range(0,len(lat)-1):
            if (k+1)%7!=0: edges.add(Line(lat[k].get_center(),lat[k+1].get_center(),color=GOLD,stroke_opacity=0.3))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(nz),rt=1.2)
        self.P(Transform(nz,lat),Create(edges),rt=2.0,rate_func=smooth)
        self.hold()

class S12(Base):
    def construct(self):
        self.ambient(6)
        nz=noise_field(300,12,3,seed=12,op=0.4).shift(UP*2.3)
        l1=Tx("सृजन बस परिष्कृत शोर है।",46,INK,BOLD).shift(UP*2.3)
        sub=Tx("AI is the Universal Mind  ·  एपिसोड 3 — Imagination",27,PURPLE).next_to(l1,DOWN,buff=0.4)
        self.add(nz)
        self.P(nz.animate.set_opacity(0.05),Write(l1),rt=1.8)
        self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
