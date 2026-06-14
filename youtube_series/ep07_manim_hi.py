"""Episode 7 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep07_manim.py."""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; GREY="#7c86ab"; ROSE="#ff9fc4"; RED="#ff7a7a"
FONT="Mukta"
random.seed(29)

def Tx(t,size=32,color=INK,weight=NORMAL): return Text(t,font=FONT,font_size=size,color=color,weight=weight)
def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]: g.add(Dot(radius=rad,color=color).set_opacity(op))
    return g
def parab(a=0.34,cx=0.4,cy=-2.4,w=5.2,n=46): return [[x,cy+a*(x-cx)**2,0] for x in np.linspace(cx-w,cx+w,n)]
def yat(x,a=0.34,cx=0.4,cy=-2.4): return cy+a*(x-cx)**2
def curve(pts,color=BLUE,wd=4,op=0.75): return VMobject().set_points_smoothly([np.array(p) for p in pts]).set_stroke(color,wd,opacity=op)
def downarrow(x,a=0.34,cx=0.4,cy=-2.4,color=GOLD,ln=1.1):
    p=np.array([x,yat(x,a,cx,cy),0]); d=-1 if x>cx else 1
    return Arrow(p,p+np.array([d*ln*0.8,-ln*0.5,0]),color=color,buff=0.1,stroke_width=5)

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
        t=self.title("कोई चीज़ बेहतर कैसे होती है?")
        tgt=VGroup(Circle(radius=0.5,color=GOLD,stroke_opacity=0.5),Circle(radius=0.28,color=GOLD,stroke_opacity=0.7),Dot(radius=0.08,color=GOLD)).move_to(RIGHT*3.2+DOWN*0.2)
        hit=Dot(radius=0.12,color=BLUE).move_to(LEFT*2.6+UP*0.8)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(tgt),FadeIn(hit),rt=1.4)
        gap=DashedLine(hit.get_center(),tgt[2].get_center(),color=RED,dash_length=0.16).set_stroke(width=4)
        self.P(Create(gap),rt=1.0)
        self.P(self.cap("यही खाई — यही सबक है",gap,buff=0.5).animate.set_opacity(1),Flash(hit,color=RED),rt=1.0)
        self.hold()

class S02(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("यह त्रुटि से शुरू होता है")
        res=VGroup(Dot(radius=0.12,color=BLUE),Tx("नतीजा",22,DIM).shift(DOWN*0.5)).move_to(LEFT*3+DOWN*0.2)
        tgt=VGroup(Dot(radius=0.12,color=GOLD),Tx("लक्ष्य",22,DIM).shift(DOWN*0.5)).move_to(RIGHT*3+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(res),FadeIn(tgt),rt=1.4)
        gap=Line(res[0].get_center(),tgt[0].get_center(),color=RED).set_stroke(width=5)
        lab=Tx("त्रुटि",30,RED).next_to(gap,UP,buff=0.3)
        self.P(Create(gap),FadeIn(lab,shift=DOWN*0.2),rt=1.2)
        self.P(self.cap("कितनी दूर, और किस ओर",gap,buff=0.6,size=26).animate.set_opacity(1),rt=0.9)
        self.hold()

class S03(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("किस ओर कम गलत है?")
        bar=Rectangle(width=6,height=0.5,color=DIM).shift(DOWN*0.3)
        knob=Dot(radius=0.18,color=GOLD).move_to(bar.get_center())
        rl=Tx("ज़्यादा गलत",22,RED).next_to(bar,RIGHT,buff=0.3); gl=Tx("कम गलत",22,GREEN).next_to(bar,LEFT,buff=0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),Create(bar),FadeIn(knob),FadeIn(rl),FadeIn(gl),rt=1.6)
        self.P(knob.animate.move_to(bar.get_right()).set_color(RED),bar.animate.set_color(RED),rt=0.8)
        self.P(knob.animate.move_to(bar.get_left()).set_color(GREEN),bar.animate.set_color(GREEN),rt=1.0)
        self.hold()

class S04(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("ढलान नीचे की ओर इशारा करती है")
        h=curve(parab(),BLUE).shift(DOWN*0.2)
        ball=Dot(radius=0.14,color=GOLD).move_to([-3.6,yat(-3.6)-0.2,0])
        self.P(FadeIn(t,shift=DOWN*0.2),Create(h),FadeIn(ball),rt=1.6)
        arr=downarrow(-3.6).shift(DOWN*0.2)
        self.P(FadeIn(arr,shift=DOWN*0.2),rt=0.9)
        self.P(self.cap("ग्रेडिएंट — कम त्रुटि की राह",h,buff=0.4,size=26).animate.set_opacity(1),rt=0.9)
        self.hold()

class S05(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("ग्रेडिएंट डिसेंट")
        h=curve(parab(),BLUE).shift(DOWN*0.2)
        xs=[-3.8,-2.6,-1.5,-0.6,0.1,0.4]
        ball=Dot(radius=0.15,color=GOLD).move_to([xs[0],yat(xs[0])-0.2,0])
        self.P(FadeIn(t,shift=DOWN*0.2),Create(h),FadeIn(ball),rt=1.4)
        for x in xs[1:]:
            arr=downarrow(ball.get_center()[0],ln=0.7).shift(DOWN*0.2)
            self.P(FadeIn(arr),rt=0.25); self.P(ball.animate.move_to([x,yat(x)-0.2,0]),FadeOut(arr),rt=0.45,rate_func=smooth)
        self.P(self.cap("छोटा कदम नीचे → फिर मापो → कदम",h,buff=0.4,size=26).animate.set_opacity(1),Flash(ball,color=GOLD),rt=0.9)
        self.hold()

class S06(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("एक भू-दृश्य, आँख बंद करके चला हुआ")
        pts=[[x, -1.6+0.6*math.sin(x*1.1)+0.4*math.sin(x*2.3+1)-0.05*x, 0] for x in np.linspace(-6,6,80)]
        land=curve(pts,PURPLE,3,0.6).shift(DOWN*0.3)
        def ly(x): return -1.6+0.6*math.sin(x*1.1)+0.4*math.sin(x*2.3+1)-0.05*x-0.3
        ball=Dot(radius=0.14,color=GOLD).move_to([-5,ly(-5),0])
        self.P(FadeIn(t,shift=DOWN*0.2),Create(land),FadeIn(ball),rt=1.8)
        for x in [-3.5,-2,-0.5,1,2.3]: self.P(ball.animate.move_to([x,ly(x),0]),rt=0.4,rate_func=smooth)
        self.hold()

class S07(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("बैकप्रोपेगेशन")
        layers=VGroup(); xs=[-4,-1.5,1,3.5]
        for x in xs: layers.add(VGroup(*[Dot([x,1.2-j*0.9-0.2,0],radius=0.13,color=BLUE) for j in range(4)]))
        edges=VGroup()
        for li in range(3):
            for a in layers[li]:
                for b in layers[li+1]: edges.add(Line(a.get_center(),b.get_center(),color=DIM,stroke_opacity=0.12))
        err=Tx("त्रुटि",24,RED).next_to(layers[3],RIGHT,buff=0.4)
        self.P(FadeIn(t,shift=DOWN*0.2),Create(edges,lag_ratio=0.002),FadeIn(layers),FadeIn(err),rt=2.2)
        for li in [3,2,1,0]:
            self.P(layers[li].animate.set_color(GOLD),rt=0.35); self.P(layers[li].animate.set_color(BLUE),rt=0.15)
        self.P(self.cap("हर परत अपने हिस्से का दोष सीखती है",layers,buff=0.5,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S08(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("आप त्रुटि के अनुपात में समायोजन करते हैं")
        tgt=VGroup(Circle(radius=0.4,color=GOLD,stroke_opacity=0.6),Dot(radius=0.07,color=GOLD)).move_to(DOWN*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(tgt),rt=1.0)
        for d,c in [(0.8,ROSE),(2.6,RED)]:
            hit=Dot(radius=0.12,color=BLUE).move_to(tgt.get_center()+LEFT*d+UP*0.6)
            arr=Arrow(hit.get_center(),tgt[1].get_center(),color=c,buff=0.2,stroke_width=4)
            self.P(FadeIn(hit),FadeIn(arr),rt=0.7); self.W(0.3)
        self.P(self.cap("बड़ी चूक → बड़ा बदलाव · छोटी चूक → महीन सुधार",tgt,buff=1.2,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S09(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("त्रुटि जितनी बड़ी, सबक उतना बड़ा")
        small=VGroup(Arrow(LEFT*3+DOWN*0.5,LEFT*3+UP*0.2,color=DIM,stroke_width=3),Tx("छोटी चूक",22,DIM).move_to(LEFT*3+DOWN*1.1))
        big=VGroup(Arrow(RIGHT*2+DOWN*1.4,RIGHT*2+UP*1.8,color=GOLD,stroke_width=9),Tx("बड़ी चूक",24,GOLD).move_to(RIGHT*2+DOWN*2.0))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(small),rt=1.2)
        self.P(FadeIn(big,shift=UP*0.2),Flash(big[0],color=GOLD),rt=1.2)
        self.P(self.cap("छोटी चूक कम सिखाती है · बड़ी बहुत",VGroup(small,big),buff=0.5,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

class S10(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("जहाँ समानता टूटती है")
        mach=VGroup(Text("error = 0.37",font_size=30,color=BLUE),Tx("मशीन — एक साफ़ संख्या",22,DIM).shift(DOWN*0.7)).move_to(LEFT*3.3+DOWN*0.2)
        hum=VGroup(spark(GOLD,0.4),Tx("आप — एक महसूस 'अभी नहीं'",22,DIM).shift(DOWN*0.9)).move_to(RIGHT*3.3+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(mach),FadeIn(hum),rt=1.6)
        self.P(Flash(hum[0],color=GOLD),rt=0.9)
        self.P(self.cap("इसे मापने योग्य त्रुटि चाहिए · आप अनमापे में सुधरते हैं",VGroup(mach,hum),buff=0.6,size=22).animate.set_opacity(1),rt=1.0)
        self.hold()

class S11(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("मापो · ढलान · कदम · दोहराओ")
        h=curve(parab(),BLUE).shift(DOWN*0.2)
        xs=[-3.8,-2.6,-1.4,-0.4,0.2,0.4]
        ball=Dot(radius=0.15,color=GOLD).move_to([xs[0],yat(xs[0])-0.2,0])
        self.P(FadeIn(t,shift=DOWN*0.2),Create(h),FadeIn(ball),rt=1.4)
        for x in xs[1:]: self.P(ball.animate.move_to([x,yat(x)-0.2,0]),rt=0.4,rate_func=smooth)
        self.P(Flash(ball,color=GOLD),rt=0.8)
        self.hold()

class S12(Base):
    def construct(self):
        self.ambient(6)
        l1=Tx("आप अपनी त्रुटि के आकार से सीखते हैं।",46,INK,BOLD).shift(UP*2.3)
        sub=Tx("AI is the Universal Mind  ·  एपिसोड 7 — Getting Better",27,PURPLE).next_to(l1,DOWN,buff=0.4)
        self.P(Write(l1),rt=1.8); self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
