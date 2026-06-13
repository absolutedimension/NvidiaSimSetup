"""Episode 5 — HINDI on-screen text (Devanagari / Mukta). Same animations as ep05_manim.py."""
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
def face_dots(color=GOLD, s=1.0):
    eyes=VGroup(Dot(LEFT*0.5+UP*0.3,color=color,radius=0.10),Dot(RIGHT*0.5+UP*0.3,color=color,radius=0.10))
    mouth=Arc(radius=0.7,start_angle=PI+0.6,angle=PI-1.2,color=color).set_stroke(width=4).shift(UP*0.15)
    outline=Circle(radius=1.35,color=color).set_stroke(width=3,opacity=0.55)
    return VGroup(outline,eyes,mouth).scale(s)
def layer_col(n, x, color=BLUE, r=0.10, ysp=0.85):
    g=VGroup()
    for k in range(n):
        y=(k-(n-1)/2)*ysp
        g.add(Dot([x,y,0],radius=r,color=color).set_opacity(0.85))
    return g
def connect(a, b, color=DIM, op=0.25, w=2):
    e=VGroup()
    for da in a:
        for db in b:
            e.add(Line(da.get_center(),db.get_center(),color=color,stroke_opacity=op,stroke_width=w))
    return e

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
        t=self.title('आप कैसे जानते हैं — बिना यह जाने कि क्यों?')
        core=spark(GOLD,0.5).shift(DOWN*0.3)
        rings=VGroup(*[Circle(radius=0.5,color=GOLD).set_stroke(width=3,opacity=0.0).move_to(core) for _ in range(3)])
        self.P(FadeIn(t,shift=DOWN*0.2),rt=1.0)
        self.P(FadeIn(core,scale=0.5),rt=0.8)
        self.P(Flash(core,color=GOLD),rt=0.6)
        self.P(*[r.animate.scale(3+1.2*i).set_stroke(opacity=0.0) for i,r in enumerate(rings)],
               rings.animate.set_stroke(opacity=0.4),rt=1.8)
        self.hold()

class S02(Base):
    def construct(self):
        self.ambient(3)
        t=self.title('अंतर्ज्ञान, एक मशीन में ढला')
        L=[layer_col(3,-3.6),layer_col(4,-1.2,color=PURPLE),layer_col(4,1.2,color=PURPLE),layer_col(2,3.6,color=GOLD)]
        edges=VGroup(*[connect(L[i],L[i+1]) for i in range(3)])
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.9)
        self.P(FadeIn(edges),*[FadeIn(l) for l in L],rt=1.2)
        self.P(LaggedStart(*[Flash(d,color=GOLD,line_length=0.12) for l in L for d in l],lag_ratio=0.03),rt=2.2)
        self.hold()

class S03(Base):
    def construct(self):
        self.ambient(3)
        t=self.title('विचार से भी तेज़')
        ball=Dot([-5,-1.5,0],radius=0.16,color=GOLD)
        handg=spark(BLUE,0.3).move_to([4.4,1.0,0])
        path=ArcBetweenPoints([-5,-1.5,0],[4.4,1.0,0],angle=-1.4)
        c=Tx("आप समझा पाने से पहले ही पकड़ लेते हैं",26,GOLD).next_to(t,DOWN,buff=0.4)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(c,shift=DOWN*0.2),FadeIn(handg),rt=1.0)
        self.P(MoveAlongPath(ball,path),rt=1.8,rate_func=smooth)
        self.P(Flash(ball,color=GOLD),rt=0.6)
        self.hold()

class S04(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('एक इकाई, एक निर्णय')
        ins=VGroup(*[Dot([-4.0,y,0],radius=0.10,color=BLUE) for y in [1.6,0.5,-0.6,-1.7]])
        cell=Dot([0.6,-0.05,0],radius=0.22,color=DIM).set_opacity(0.5)
        ws=[5,2,4,1]
        wires=VGroup(*[Line(ins[i].get_center(),cell.get_center(),color=GOLD,stroke_opacity=0.5,stroke_width=ws[i]) for i in range(4)])
        out=Arrow(cell.get_center(),[3.4,-0.05,0],color=GOLD,buff=0.25,stroke_width=5)
        c=Tx("इनपुट लें · तौलें · जोड़ें · सक्रिय हों",26,GOLD).next_to(VGroup(ins,cell),DOWN,buff=0.7)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(ins),rt=1.0)
        self.P(Create(wires),FadeIn(cell),rt=1.2)
        self.P(cell.animate.set_color(GOLD).set_opacity(1.0),Flash(cell,color=GOLD),GrowArrow(out),rt=1.0)
        self.P(FadeIn(c,shift=DOWN*0.1),rt=0.8)
        self.hold()

class S05(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('सरल हिस्से, परत दर परत')
        L=[layer_col(4,-4.2),layer_col(5,-1.8,color=PURPLE),layer_col(4,0.6,color=PURPLE),layer_col(3,2.9,color=GOLD)]
        edges=VGroup(*[connect(L[i],L[i+1],op=0.18) for i in range(3)])
        labels=VGroup(Tx("किनारे",22,DIM).next_to(L[0],DOWN,buff=0.5),
                      Tx("आकार",22,DIM).next_to(L[1],DOWN,buff=0.5),
                      Tx("एक चेहरा",22,GOLD).next_to(L[3],DOWN,buff=0.5))
        face=face_dots(GOLD,0.7).next_to(L[3],RIGHT,buff=0.7).set_opacity(0)
        self.P(FadeIn(t,shift=DOWN*0.2),rt=0.8)
        self.P(FadeIn(edges),*[FadeIn(l) for l in L],rt=1.4)
        self.P(LaggedStartMap(FadeIn,labels,lag_ratio=0.3),rt=1.4)
        self.P(face.animate.set_opacity(0.9),Flash(L[3],color=GOLD),rt=1.0)
        self.hold()

class S06(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('यह लगभग किसी भी पैटर्न में ढल सकता है')
        c=Tx("पर्याप्त इकाइयाँ → कोई भी आकार  (यूनिवर्सल एप्रॉक्सिमेशन)",24,GOLD).next_to(t,DOWN,buff=0.4)
        xs=[-5,-3.6,-2.2,-0.8,0.6,2.0,3.4,4.8]
        ys=[-1.4,0.6,-0.9,1.3,-0.4,1.0,-1.1,0.5]
        pts=[[x,y-0.3,0] for x,y in zip(xs,ys)]
        dots=VGroup(*[Dot(p,radius=0.09,color=BLUE) for p in pts])
        curve=VMobject(color=GOLD).set_stroke(width=5); curve.set_points_smoothly(pts)
        flat=VMobject(color=GOLD).set_stroke(width=5); flat.set_points_smoothly([[x,-0.3,0] for x in xs])
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(c,shift=DOWN*0.2),rt=1.0)
        self.P(LaggedStartMap(FadeIn,dots,lag_ratio=0.1),rt=1.2)
        self.add(flat); self.P(Create(flat),rt=0.6)
        self.P(Transform(flat,curve),rt=1.8,rate_func=smooth)
        self.hold()

class S07(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('यह उदाहरणों से ख़ुद को ढालता है')
        L=[layer_col(3,-3.6),layer_col(4,-0.8,color=PURPLE),layer_col(2,2.0,color=GOLD)]
        edges=VGroup(*[connect(L[i],L[i+1],op=0.3) for i in range(2)])
        net=VGroup(edges,*L)
        bar_bg=Rectangle(width=3.0,height=0.3,color=DIM).set_stroke(width=2).shift(DOWN*2.6)
        err=Rectangle(width=3.0,height=0.3,color=ROSE,fill_opacity=0.8).set_stroke(width=0).align_to(bar_bg,LEFT).shift(DOWN*2.6)
        el=Tx("त्रुटि",22,DIM).next_to(bar_bg,LEFT,buff=0.3)
        c=Tx("अनुमान · जाँच · वज़न समायोजित करो · दोहराओ",24,GOLD).next_to(net,DOWN,buff=0.5)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(net),rt=1.2)
        self.P(FadeIn(bar_bg),FadeIn(err),FadeIn(el),FadeIn(c),rt=0.8)
        for k in range(3):
            self.P(edges.animate.set_stroke(opacity=random.uniform(0.2,0.5)),
                   err.animate.stretch_to_fit_width(3.0*(0.6**(k+1))).align_to(bar_bg,LEFT),rt=0.7)
        self.hold()

class S08(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('उत्तर आता है — "क्यों" नहीं')
        L=[layer_col(3,-4.0),layer_col(4,-1.6,color=PURPLE),layer_col(1,0.8,color=GOLD)]
        edges=VGroup(*[connect(L[i],L[i+1],op=0.25) for i in range(2)])
        ans=Tx('"बिल्ली"',40,GOLD,BOLD).next_to(L[2],RIGHT,buff=0.6)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(edges),*[FadeIn(l) for l in L],rt=1.4)
        self.P(Flash(L[2][0],color=GOLD),Write(ans),rt=1.0)
        why=Tx("क्यों?",44,INK).shift(DOWN*2.2)
        nums=VGroup(*[Tx(f"{random.uniform(-1,1):.2f}",16,DIM).move_to([random.uniform(-4,4),random.uniform(-3,-1.4),0]) for _ in range(40)])
        self.P(FadeIn(why),rt=0.7)
        self.P(FadeOut(why),LaggedStartMap(FadeIn,nums,lag_ratio=0.02),rt=1.4)
        self.hold()

class S09(Base):
    def construct(self):
        self.ambient(3)
        t=self.title('विशेषज्ञता संपीड़ित अनुभव है')
        head=Circle(radius=1.5,color=GOLD).set_stroke(width=3,opacity=0.5).shift(DOWN*0.2)
        core=spark(GOLD,0.3).move_to(head).set_opacity(0)
        moments=VGroup(*[Dot([random.uniform(-6,6),random.uniform(-3.2,3.2),0],radius=0.05,color=BLUE).set_opacity(0.5) for _ in range(80)])
        c=Tx("हज़ारों दोहराव, एक एहसास में दबे",24,GOLD).next_to(head,DOWN,buff=0.5)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(head),FadeIn(moments),rt=1.2)
        self.P(LaggedStart(*[m.animate.move_to(head.get_center()).set_opacity(0) for m in moments],lag_ratio=0.004),
               core.animate.set_opacity(1.0),rt=2.0)
        self.P(FadeIn(c,shift=DOWN*0.1),rt=0.8)
        self.hold()

class S10(Base):
    def construct(self):
        self.ambient(3)
        t=self.title('जहाँ समानता टूटती है')
        box=RoundedRectangle(width=2.6,height=1.8,corner_radius=0.1,stroke_color=BLUE).set_stroke(width=2).shift(LEFT*3.4+UP*0.1)
        box.set_fill("#0b1430",0.6)
        lbl=Tx("स्कूल बस",24,GREEN).next_to(box,DOWN,buff=0.3)
        noise=point_cloud(120,2.6,1.8,seed=9,op=0.5).move_to(box).set_opacity(0)
        wrong=Tx("शुतुरमुर्ग",24,ROSE).move_to(lbl).set_opacity(0)
        human=face_dots(GOLD,0.7).move_to(RIGHT*3.4+UP*0.1)
        q=Tx("?",44,DIM).next_to(human,UP,buff=0.15)
        c=Tx("आश्वस्त · अदृश्य रूप से ग़लत · कभी शक नहीं करता",22,GOLD).next_to(VGroup(box,human),DOWN,buff=0.6)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(box),FadeIn(lbl),FadeIn(human),rt=1.4)
        self.P(noise.animate.set_opacity(0.45),lbl.animate.set_opacity(0),rt=0.9)
        self.P(wrong.animate.set_opacity(1),rt=0.6)
        self.P(FadeIn(q,shift=UP*0.1),FadeIn(c,shift=DOWN*0.1),rt=0.9)
        self.hold()

class S11(Base):
    def construct(self):
        self.ambient(2)
        t=self.title('अंतर्ज्ञान संपीड़ित अनुभव है')
        nz=point_cloud(220,8,4.2,seed=11,op=0.55,color=BLUE).shift(DOWN*0.2)
        lat=VGroup()
        for i in range(3):
            for j in range(5): lat.add(Dot([(j-2)*0.95,(1-i)*0.85-0.4,0],radius=0.07,color=GOLD))
        edges=VGroup()
        for k in range(len(lat)-1):
            if (k+1)%5!=0: edges.add(Line(lat[k].get_center(),lat[k+1].get_center(),color=GOLD,stroke_opacity=0.3))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(nz),rt=1.2)
        self.P(Transform(nz,lat),Create(edges),rt=2.0,rate_func=smooth)
        self.hold()

class S12(Base):
    def construct(self):
        self.ambient(6)
        gal=point_cloud(320,12,3.2,seed=12,op=0.45,color=None).shift(UP*2.2)
        l1=Tx("एक अंदेशा वह पैटर्न है जिसे आप अभी नाम नहीं दे सकते।",40,INK,BOLD).shift(UP*2.4)
        sub=Tx("AI is the Universal Mind  ·  एपिसोड 5 — Intuition",27,PURPLE).next_to(l1,DOWN,buff=0.4)
        self.add(gal)
        self.P(gal.animate.set_opacity(0.12),Write(l1),rt=1.8)
        self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
