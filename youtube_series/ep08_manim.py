"""
Episode 8 — "The Neuron" (what is a neural network) — Manim engine, 14 scenes.
Teaches: digit -> 28x28 grid of brightness -> a neuron holds one number -> input/output
layers -> hidden layers as a feature hierarchy -> weights -> weighted sum -> bias -> squish
-> ~13k knobs -> "a neural network is just one big function".
Same visual language as Ep1-7. Reads SCENE_DUR; transparent render. Driver: render_ep08_manim.py.
"""
from manim import *
import os, math, random
from PIL import Image, ImageDraw, ImageFont

DUR = float(os.environ.get("SCENE_DUR", "8"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; GREY="#7c86ab"; ROSE="#ff9fc4"; RED="#ff7a7a"
random.seed(28)

FONT_PATH="/home/ubuntu/.local/share/fonts/Poppins-Bold.ttf"

def digit_array(ch="3", n=28, fontsize=26):
    """Render a glyph into an n x n grayscale 0..1 array (real anti-aliased digit)."""
    img=Image.new("L",(n,n),0); d=ImageDraw.Draw(img)
    try: fnt=ImageFont.truetype(FONT_PATH, fontsize)
    except: fnt=ImageFont.load_default()
    try:
        bb=d.textbbox((0,0),ch,font=fnt); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        d.text(((n-w)/2-bb[0],(n-h)/2-bb[1]),ch,fill=255,font=fnt)
    except Exception:
        d.text((n*0.3,n*0.15),ch,fill=255,font=fnt)
    px=img.load()
    return [[px[x,y]/255.0 for x in range(n)] for y in range(n)]

def pixel_grid(arr, cell=0.17, gap=0.0, lit=GOLD):
    """VGroup of squares colored by brightness 0..1."""
    n=len(arr); g=VGroup(); s=cell
    for y in range(n):
        for x in range(n):
            v=arr[y][x]
            sq=Square(side_length=s).set_stroke(width=0)
            sq.set_fill(interpolate_color(BLACK, ManimColor(lit), v**0.85), opacity=0.10+0.9*v)
            sq.move_to([ (x-(n-1)/2)*s, ((n-1)/2-y)*s, 0])
            g.add(sq)
    return g

def neuron(val=0.0, r=0.16, color=GOLD):
    c=Circle(radius=r).set_stroke(DIM,2,opacity=0.5)
    c.set_fill(interpolate_color(BLACK, ManimColor(color), val), opacity=0.15+0.85*val)
    return c

def vcolumn(x, vals, r=0.13, top=2.3, bot=-2.3, color=GOLD):
    n=len(vals); g=VGroup()
    ys=np.linspace(top,bot,n)
    for v,y in zip(vals,ys):
        d=neuron(v,r,color).move_to([x,y,0]); g.add(d)
    return g

def spark(color=GOLD, r=0.16):
    g=VGroup()
    for rad,op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]: g.add(Dot(radius=rad,color=color).set_opacity(op))
    return g

class Base(MovingCameraScene):
    def setup(self):
        super().setup(); self.u=0.0
    def P(self,*a,rt=1.0,**k): self.play(*a,run_time=rt,**k); self.u+=rt
    def W(self,t):
        if t>0: self.wait(t); self.u+=t
    def ambient(self,n=6):
        dots=VGroup()
        for _ in range(n):
            d=Dot(radius=random.uniform(0.03,0.07),color=random.choice([BLUE,PURPLE,GREEN])).set_opacity(0.45)
            d.move_to([random.uniform(-6.5,6.5),random.uniform(-3.6,3.6),0])
            ph=random.uniform(0,6.28); sp=random.uniform(0.15,0.4)
            d.add_updater(lambda m,dt,ph=ph,sp=sp: m.shift(np.array([math.cos(ph+self.renderer.time*sp),math.sin(ph+self.renderer.time*sp*0.8),0])*0.004))
            dots.add(d)
        self.add(dots)
        self.camera.frame.add_updater(lambda m,dt: m.scale(1+0.0008*dt*30))
        return dots
    def title(self,txt,size=44,buff=0.9): return Text(txt,font="Poppins",font_size=size,color=INK,weight=BOLD).to_edge(UP,buff=buff)
    def cap(self,txt,ref,size=26,color=GOLD,buff=0.5): return Text(txt,font="Poppins",font_size=size,color=color).next_to(ref,DOWN,buff=buff)
    def hold(self):
        rem=DUR-self.u
        if rem>0.1: self.W(rem)

# ---------------------------------------------------------------- S01 hook
class S01(Base):
    def construct(self):
        self.ambient(4)
        t=self.title("You see a three. How?")
        clean=Text("3",font="Poppins",weight=BOLD,font_size=240,color=INK).move_to(LEFT*3.6+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(clean,scale=0.8),rt=1.4)
        messy=VGroup(
            Text("3",font="Poppins",font_size=150,color=GOLD).rotate(-0.18).move_to(RIGHT*0.4+UP*1.0),
            Text("3",font="Poppins",font_size=130,color=BLUE).rotate(0.22).move_to(RIGHT*2.6+DOWN*0.1),
            Text("3",font="Poppins",font_size=170,color=PURPLE).rotate(-0.05).move_to(RIGHT*1.4+DOWN*1.7),
        )
        for m in messy:
            self.P(FadeIn(m,scale=0.7),rt=0.6); self.P(Flash(m.get_center(),color=GOLD,line_length=0.3),rt=0.4)
        self.P(self.cap("each one different — yet instantly a three",messy,buff=0.6).animate.set_opacity(1),rt=0.9)
        self.hold()

# ---------------------------------------------------------------- S02 the gap
class S02(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("Ten thousand threes, one idea")
        cloud=VGroup()
        random.seed(7)
        for _ in range(22):
            s=random.uniform(28,70); col=random.choice([DIM,BLUE,PURPLE,GREY])
            m=Text("3",font="Poppins",font_size=s,color=col).rotate(random.uniform(-0.4,0.4))
            m.move_to([random.uniform(-5.4,-0.6),random.uniform(-2.6,2.2),0]).set_opacity(0.8)
            cloud.add(m)
        self.P(LaggedStartMap(FadeIn,cloud,lag_ratio=0.06),rt=2.2)
        label=VGroup(Circle(radius=0.95,color=GOLD,stroke_opacity=0.6),Text("3",font="Poppins",weight=BOLD,font_size=90,color=GOLD)).move_to(RIGHT*3.6+DOWN*0.1)
        arrs=VGroup(*[Arrow(m.get_center(),label.get_center()+LEFT*1.0,buff=0.3,stroke_width=2,color=DIM).set_opacity(0.25) for m in cloud[:8]])
        self.P(FadeIn(label,scale=0.7),LaggedStartMap(FadeIn,arrs,lag_ratio=0.05),rt=1.6)
        self.P(self.cap("no nameable rule maps them — that is the problem",label,buff=0.5).animate.set_opacity(1),rt=0.9)
        self.hold()

# ---------------------------------------------------------------- S03 what the machine sees
class S03(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("28 × 28 = 784 brightness values")
        arr=digit_array("3",28,26)
        grid=pixel_grid(arr,cell=0.20).move_to(LEFT*2.8+DOWN*0.2)
        clean=Text("3",font="Poppins",weight=BOLD,font_size=200,color=INK).move_to(LEFT*2.8+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(clean),rt=1.2)
        self.P(FadeOut(clean),FadeIn(grid),rt=1.2)
        gl=VGroup()
        n=28; s=0.20
        for k in range(0,29,2):
            gl.add(Line([(-(n)/2)*s+k*s+grid.get_center()[0]+s/2,2.6+grid.get_center()[1]-2.8,0],
                         [(-(n)/2)*s+k*s+grid.get_center()[0]+s/2,grid.get_center()[1]+2.8,0],color=DIM,stroke_opacity=0.15))
        # show a few sample brightness numbers on the right
        samples=VGroup(
            Text("0.00",font="Poppins",font_size=30,color=DIM),
            Text("0.61",font="Poppins",font_size=30,color=BLUE),
            Text("0.98",font="Poppins",font_size=30,color=GOLD),
        ).arrange(DOWN,buff=0.5).move_to(RIGHT*3.6+UP*0.4)
        legend=VGroup(
            Text("black = 0",font="Poppins",font_size=24,color=DIM),
            Text("white = 1",font="Poppins",font_size=24,color=INK),
        ).arrange(DOWN,buff=0.3).next_to(samples,DOWN,buff=0.6)
        self.P(Create(gl,lag_ratio=0.02),rt=1.2)
        self.P(LaggedStartMap(FadeIn,samples,lag_ratio=0.2),FadeIn(legend),rt=1.4)
        self.hold()

# ---------------------------------------------------------------- S04 the neuron
class S04(Base):
    def construct(self):
        self.ambient(4)
        t=self.title("A neuron holds one number (0 to 1)")
        c=Circle(radius=1.2).set_stroke(DIM,3,opacity=0.6).move_to(DOWN*0.2)
        c.set_fill(GOLD,opacity=0.0)
        tracker=ValueTracker(0.0)
        val=always_redraw(lambda: Text(f"{tracker.get_value():.2f}",font="Poppins",font_size=70,color=INK).move_to(c.get_center()))
        c.add_updater(lambda m: m.set_fill(GOLD, opacity=0.85*tracker.get_value()))
        self.P(FadeIn(t,shift=DOWN*0.2),Create(c),rt=1.6)
        self.add(val)
        self.P(tracker.animate.set_value(0.97),rt=2.6,rate_func=smooth)
        c.clear_updaters()
        lab=Text("activation — how strongly it is on",font="Poppins",font_size=26,color=GOLD).next_to(c,DOWN,buff=0.6)
        self.P(FadeIn(lab,shift=UP*0.2),Flash(c.get_center(),color=GOLD,line_length=0.5),rt=1.0)
        self.hold()

# ---------------------------------------------------------------- S05 input layer
class S05(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("The input layer = the picture as neurons")
        arr=digit_array("3",28,26)
        grid=pixel_grid(arr,cell=0.15).move_to(LEFT*3.8+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(grid),rt=1.4)
        # representative column of neurons lit by the digit's brightness (sample 18)
        vals=[arr[int(r)][14] for r in np.linspace(2,25,18)]
        vals=[max(v, 0.05+0.6*((i*37)%5)/5) for i,v in enumerate(vals)]  # ensure visible variety
        col=vcolumn(0.6, vals, r=0.12, top=2.7, bot=-2.9)
        bx=col.get_right()[0]+0.35; topy=col.get_top()[1]; boty=col.get_bottom()[1]
        bracket=VGroup(
            Line([bx,topy,0],[bx,boty,0],color=DIM,stroke_width=3),
            Line([bx,topy,0],[bx-0.12,topy,0],color=DIM,stroke_width=3),
            Line([bx,boty,0],[bx-0.12,boty,0],color=DIM,stroke_width=3),
        )
        blab=Text("784\nneurons",font="Poppins",font_size=28,color=INK,line_spacing=0.7).next_to(bracket,RIGHT,buff=0.25)
        arrow=Arrow(grid.get_right()+RIGHT*0.1, col.get_left()+LEFT*0.1, buff=0.1, color=GOLD, stroke_width=4)
        self.P(GrowArrow(arrow),LaggedStartMap(FadeIn,col,lag_ratio=0.04),rt=1.8)
        self.P(Create(bracket),FadeIn(blab),rt=1.0)
        self.P(self.cap("bright pixels → lit neurons",col,buff=0.4,size=24).animate.set_opacity(1),rt=0.8)
        self.hold()

# ---------------------------------------------------------------- S06 output layer
class S06(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("The output layer = 10 neurons, one per digit")
        col=VGroup(); labs=VGroup()
        ys=np.linspace(3.0,-3.0,10)
        for d,y in enumerate(ys):
            v=0.92 if d==3 else random.uniform(0.04,0.22)
            nu=neuron(v,0.20,GOLD).move_to([0.6,y,0])
            lab=Text(str(d),font="Poppins",font_size=30,color=DIM if d!=3 else GOLD).next_to(nu,LEFT,buff=0.4)
            col.add(nu); labs.add(lab)
        self.P(FadeIn(t,shift=DOWN*0.2),LaggedStartMap(FadeIn,col,lag_ratio=0.06),FadeIn(labs),rt=2.0)
        guess=Text("guess: 3",font="Poppins",weight=BOLD,font_size=38,color=GOLD).move_to(RIGHT*3.4)
        ring=Circle(radius=0.34,color=GOLD).move_to(col[3].get_center())
        self.P(Create(ring),FadeIn(guess,shift=LEFT*0.2),Flash(col[3].get_center(),color=GOLD,line_length=0.4),rt=1.2)
        self.hold()

# ---------------------------------------------------------------- S07 hidden layers
class S07(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("Hidden layers — a hierarchy of features?")
        xs=[-4.6,-1.6,1.4,4.4]; counts=[7,6,6,5]
        layers=[]
        for x,cnt in zip(xs,counts):
            ys=np.linspace(2.1,-2.5,cnt)
            layers.append(VGroup(*[neuron(random.uniform(0.1,0.7),0.12,BLUE).move_to([x,y,0]) for y in ys]))
        edges=VGroup()
        for li in range(3):
            for a in layers[li]:
                for b in layers[li+1]:
                    edges.add(Line(a.get_center(),b.get_center(),color=DIM,stroke_opacity=0.06))
        self.P(FadeIn(t,shift=DOWN*0.2),Create(edges,lag_ratio=0.001),*[FadeIn(l) for l in layers],rt=2.4)
        lbls=VGroup(
            Text("pixels",font="Poppins",font_size=22,color=DIM).next_to(layers[0],DOWN,buff=0.3),
            Text("edges",font="Poppins",font_size=22,color=GREEN).next_to(layers[1],DOWN,buff=0.3),
            Text("parts",font="Poppins",font_size=22,color=PURPLE).next_to(layers[2],DOWN,buff=0.3),
            Text("digit",font="Poppins",font_size=22,color=GOLD).next_to(layers[3],DOWN,buff=0.3),
        )
        # tiny feature icons in the middle layers
        loop=Circle(radius=0.13,color=GREEN,stroke_width=4).move_to(layers[2][0].get_center()+UP*0.0)
        stroke=Line(LEFT*0.12,RIGHT*0.12,color=GREEN,stroke_width=4).move_to(layers[1][1].get_center())
        self.P(LaggedStartMap(FadeIn,lbls,lag_ratio=0.2),rt=1.4)
        self.P(self.cap("edges → parts → digits",lbls,buff=0.4,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

# ---------------------------------------------------------------- S08 why layers
class S08(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("Break one hard problem into layers of easy ones")
        big=Text("?",font="Poppins",weight=BOLD,font_size=160,color=RED).move_to(LEFT*4.0+UP*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(big,scale=0.7),rt=1.2)
        steps=VGroup(
            VGroup(Square(0.7,color=GOLD).set_fill(GOLD,0.15),Text("digit",font="Poppins",font_size=20,color=INK)).arrange(DOWN,buff=0.12),
            VGroup(Square(0.7,color=PURPLE).set_fill(PURPLE,0.15),Text("parts",font="Poppins",font_size=20,color=INK)).arrange(DOWN,buff=0.12),
            VGroup(Square(0.7,color=GREEN).set_fill(GREEN,0.15),Text("edges",font="Poppins",font_size=20,color=INK)).arrange(DOWN,buff=0.12),
        )
        for i,st in enumerate(steps):
            st.move_to([0.2+i*1.9, 1.6-i*1.1, 0])
        arr=Arrow(big.get_right(),steps[0].get_left(),buff=0.3,color=DIM,stroke_width=4)
        self.P(GrowArrow(arr),rt=0.7)
        for st in steps:
            self.P(FadeIn(st,scale=0.7,shift=DOWN*0.2),rt=0.7)
        self.P(self.cap("each layer answers a slightly simpler question",steps,buff=0.5,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

# ---------------------------------------------------------------- S09 weights
class S09(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("Every connection has a weight")
        A=VGroup(*[neuron(random.uniform(0.2,0.8),0.16,BLUE).move_to([-3.2,y,0]) for y in np.linspace(2.0,-2.4,4)])
        B=VGroup(*[neuron(0.3,0.16,GOLD).move_to([3.2,y,0]) for y in np.linspace(1.4,-1.8,3)])
        edges=VGroup(); kinds=[]
        random.seed(11)
        for a in A:
            for b in B:
                w=random.choice([1,1,-1,0]); kinds.append(w)
                if w==1: col,wd,op=GOLD,random.uniform(4,8),0.85
                elif w==-1: col,wd,op=RED,random.uniform(2,4),0.6
                else: col,wd,op=GREY,1.5,0.2
                edges.add(Line(a.get_center(),b.get_center(),color=col,stroke_width=wd,stroke_opacity=op))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(A),FadeIn(B),rt=1.4)
        self.P(LaggedStartMap(Create,edges,lag_ratio=0.02),rt=2.2)
        leg=VGroup(
            VGroup(Line(LEFT*0.3,RIGHT*0.3,color=GOLD,stroke_width=7),Text("listen (＋)",font="Poppins",font_size=22,color=GOLD)).arrange(RIGHT,buff=0.3),
            VGroup(Line(LEFT*0.3,RIGHT*0.3,color=RED,stroke_width=4),Text("suppress (−)",font="Poppins",font_size=22,color=RED)).arrange(RIGHT,buff=0.3),
            VGroup(Line(LEFT*0.3,RIGHT*0.3,color=GREY,stroke_width=2),Text("ignore (≈0)",font="Poppins",font_size=22,color=GREY)).arrange(RIGHT,buff=0.3),
        ).arrange(DOWN,buff=0.25,aligned_edge=LEFT).to_edge(DOWN,buff=0.6)
        self.P(LaggedStartMap(FadeIn,leg,lag_ratio=0.2),rt=1.2)
        self.hold()

# ---------------------------------------------------------------- S10 weighted sum
class S10(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("A neuron computes a weighted sum")
        ins=[0.9,0.2,0.7]; ws=[1.2,-0.8,0.5]; cols=[GOLD,RED,BLUE]
        A=VGroup(); wl=VGroup()
        ys=[1.8,0.0,-1.8]
        for v,w,y,c in zip(ins,ws,ys,cols):
            a=neuron(v,0.18,c).move_to([-4.0,y,0])
            av=Text(f"{v:.1f}",font="Poppins",font_size=22,color=INK).move_to(a.get_center())
            A.add(VGroup(a,av))
            wl.add(Text(f"×{w:+.1f}",font="Poppins",font_size=24,color=c).move_to([-1.6,y,0]))
        target=neuron(0.0,0.5,GOLD).move_to([3.4,0,0])
        lines=VGroup(*[Line(A[i][0].get_center(),target.get_center(),color=cols[i],stroke_opacity=0.4,stroke_width=3) for i in range(3)])
        running=sum(v*w for v,w in zip(ins,ws))
        tk=ValueTracker(0.0)
        total=always_redraw(lambda: Text(f"{tk.get_value():.2f}",font="Poppins",font_size=40,color=INK).move_to(target.get_center()))
        self.P(FadeIn(t,shift=DOWN*0.2),FadeIn(A),FadeIn(wl),Create(lines),FadeIn(target),rt=2.0)
        self.add(total)
        for i in range(3):
            pulse=Dot(color=cols[i],radius=0.1).move_to(A[i][0].get_center())
            self.P(pulse.animate.move_to(target.get_center()),rt=0.6)
            self.remove(pulse)
        self.P(tk.animate.set_value(running),target.animate.set_fill(GOLD,0.85),rt=1.0)
        self.P(self.cap("the raw evidence for firing",target,buff=0.6,size=24).animate.set_opacity(1),rt=0.8)
        self.hold()

# ---------------------------------------------------------------- S11 bias
class S11(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("The bias = how hard it is to fire")
        axis=Line(LEFT*4,RIGHT*4,color=DIM).shift(DOWN*2.4)
        bar=Rectangle(width=1.2,height=0.1,color=BLUE).set_fill(BLUE,0.7)
        bar.move_to([0,-2.35,0])
        thresh=DashedLine(LEFT*4+UP*0.0,RIGHT*4+UP*0.0,color=GOLD,dash_length=0.2).set_stroke(width=4).shift(UP*0.4)
        tl=Text("threshold (bias)",font="Poppins",font_size=24,color=GOLD).next_to(thresh,RIGHT,buff=0.2).shift(LEFT*1.2+UP*0.3)
        self.P(FadeIn(t,shift=DOWN*0.2),Create(axis),FadeIn(bar),Create(thresh),FadeIn(tl),rt=1.8)
        nu=neuron(0.0,0.5,GOLD).move_to([0,1.7,0])
        self.P(FadeIn(nu),rt=0.6)
        # weighted sum grows past the threshold -> neuron fires
        self.P(bar.animate.stretch_to_fit_height(2.6).move_to([0,-1.0,0]),rt=1.2)
        self.P(bar.animate.stretch_to_fit_height(4.2).move_to([0,-0.2,0]).set_color(GOLD).set_fill(GOLD,0.8),
               nu.animate.set_fill(GOLD,0.9),Flash(nu.get_center(),color=GOLD),rt=1.0)
        self.P(self.cap("clear the bias → the neuron wakes up",nu,buff=0.5,size=24).animate.set_opacity(1),rt=0.9)
        self.hold()

# ---------------------------------------------------------------- S12 squish
class S12(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("Squish the result back into 0 to 1")
        ax=Axes(x_range=[-6,6,2],y_range=[0,1,0.5],x_length=8,y_length=3.4,
                axis_config={"color":DIM,"include_tip":False,"stroke_width":2}).shift(DOWN*0.3)
        def sig(x): return 1/(1+math.exp(-x))
        graph=ax.plot(lambda x: sig(x),color=BLUE,stroke_width=5)
        ylab=Text("activation",font="Poppins",font_size=22,color=DIM).next_to(ax.y_axis,UP,buff=0.1)
        xlab=Text("weighted sum + bias",font="Poppins",font_size=22,color=DIM).next_to(ax.x_axis,RIGHT,buff=0.1).shift(LEFT*1.2+DOWN*0.2)
        self.P(FadeIn(t,shift=DOWN*0.2),Create(ax),FadeIn(ylab),FadeIn(xlab),rt=1.6)
        self.P(Create(graph),rt=1.6)
        for xv,c in [(4.5,GOLD),(-4.0,DIM)]:
            p=ax.c2p(xv,sig(xv))
            dot=Dot(color=c,radius=0.1).move_to(ax.c2p(xv,0))
            vline=DashedLine(ax.c2p(xv,0),p,color=c,stroke_opacity=0.5)
            hline=DashedLine(p,ax.c2p(ax.x_range[0],sig(xv)),color=c,stroke_opacity=0.5)
            out=Text(f"{sig(xv):.2f}",font="Poppins",font_size=24,color=c).next_to(ax.c2p(ax.x_range[0],sig(xv)),LEFT,buff=0.15)
            self.P(FadeIn(dot),Create(vline),rt=0.6)
            self.P(Create(hline),FadeIn(out),rt=0.6)
        self.hold()

# ---------------------------------------------------------------- S13 scale
class S13(Base):
    def construct(self):
        self.ambient(3)
        t=self.title("~13,000 knobs to tune")
        xs=[-5.0,-2.3,0.4,3.1,5.4]; counts=[8,6,6,6,4]
        layers=[]
        for x,cnt in zip(xs,counts):
            ys=np.linspace(2.2,-2.6,cnt)
            layers.append(VGroup(*[neuron(random.uniform(0.1,0.5),0.10,BLUE).move_to([x,y,0]) for y in ys]))
        edges=VGroup()
        for li in range(4):
            for a in layers[li]:
                for b in layers[li+1]:
                    edges.add(Line(a.get_center(),b.get_center(),color=DIM,stroke_opacity=0.05))
        self.P(FadeIn(t,shift=DOWN*0.2),Create(edges,lag_ratio=0.0005),*[FadeIn(l) for l in layers],rt=2.6)
        # cascade activation left -> right, ending on output neuron index for "3"
        for li in range(5):
            self.P(layers[li].animate.set_color(GOLD),rt=0.3)
            if li<4: self.P(layers[li].animate.set_color(BLUE),rt=0.12)
        out3=layers[4][1]
        ring=Circle(radius=0.26,color=GOLD).move_to(out3.get_center())
        g3=Text("3",font="Poppins",weight=BOLD,font_size=40,color=GOLD).next_to(layers[4],RIGHT,buff=0.4)
        self.P(Create(ring),FadeIn(g3),Flash(out3.get_center(),color=GOLD),rt=1.0)
        self.hold()

# ---------------------------------------------------------------- S14 anchor
class S14(Base):
    def construct(self):
        self.ambient(6)
        box=RoundedRectangle(width=3.0,height=2.0,corner_radius=0.2,color=GOLD).set_fill(GOLD,0.08).move_to(UP*0.2)
        fx=Text("f(x)",font="Poppins",weight=BOLD,font_size=60,color=INK).move_to(box.get_center())
        ins=VGroup(*[Arrow([-5.4,y,0],[-1.6,0.2,0],buff=0.1,stroke_width=2,color=BLUE).set_opacity(0.4) for y in np.linspace(2.0,-1.6,6)])
        outs=VGroup(*[Arrow([1.6,0.2,0],[5.0,y,0],buff=0.1,stroke_width=3,color=GOLD).set_opacity(0.6) for y in np.linspace(1.4,-1.0,5)])
        inl=Text("784 in",font="Poppins",font_size=24,color=BLUE).move_to(LEFT*5.7+UP*0.2)
        outl=Text("10 out",font="Poppins",font_size=24,color=GOLD).move_to(RIGHT*5.6+UP*0.2)
        self.P(LaggedStartMap(FadeIn,ins,lag_ratio=0.05),FadeIn(box),FadeIn(fx),LaggedStartMap(FadeIn,outs,lag_ratio=0.05),FadeIn(inl),FadeIn(outl),rt=2.2)
        l1=Text("A neural network is just one big function.",font="Poppins",weight=BOLD,font_size=40,color=INK).to_edge(UP,buff=1.2)
        sub=Text("AI is the Universal Mind  ·  Ep.8 — The Neuron",font="Poppins",font_size=27,color=PURPLE).next_to(l1,DOWN,buff=0.4)
        self.P(Write(l1),rt=1.6); self.P(FadeIn(sub,shift=UP*0.2),rt=1.0)
        self.hold()
