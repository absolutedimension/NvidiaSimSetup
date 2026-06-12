"""
Episode 1 — "Attention" — Manim engine (the dynamic motion-graphics rebuild).
Each scene reads SCENE_DUR (seconds) from env, plays its animations, then holds —
but ambient drift + camera push keep motion alive the whole time. Rendered TRANSPARENT
(-t) so the reactive circuit_mind shader shows behind. Driver: render_ep01_manim.py.
"""
from manim import *
import os, math, random

DUR = float(os.environ.get("SCENE_DUR", "6"))
GOLD="#ffc850"; PURPLE="#b48cff"; BLUE="#6e96eb"; GREEN="#7fd6a0"; INK="#e9edfb"; DIM="#9aa6cc"; ROSE="#ff9fc4"
random.seed(7)

def spark(color=GOLD, r=0.16):
    g = VGroup()
    for rad, op in [(r*3.2,0.08),(r*2.0,0.16),(r,1.0)]:
        g.add(Dot(radius=rad, color=color).set_opacity(op))
    return g

class Base(MovingCameraScene):
    def setup(self):
        super().setup()
        self.u = 0.0  # time used
    def P(self, *anims, rt=1.0, **kw):
        self.play(*anims, run_time=rt, **kw); self.u += rt
    def W(self, t):
        self.wait(t); self.u += t
    def ambient(self, n=7):
        """drifting faint dots + slow camera push — keeps the frame alive."""
        dots = VGroup()
        for _ in range(n):
            d = Dot(radius=random.uniform(0.03,0.07),
                    color=random.choice([BLUE,PURPLE,GREEN])).set_opacity(0.5)
            d.move_to([random.uniform(-6.5,6.5), random.uniform(-3.6,3.6), 0])
            ph = random.uniform(0,6.28); sp = random.uniform(0.15,0.4)
            d.add_updater(lambda m,dt,ph=ph,sp=sp: m.shift(np.array([math.cos(ph+self.renderer.time*sp), math.sin(ph+self.renderer.time*sp*0.8),0])*0.004))
            dots.add(d)
        self.add(dots)
        self.camera.frame.add_updater(lambda m,dt: m.scale(1+0.0009*dt*30))  # slow push
        return dots
    def hold(self):
        rem = DUR - self.u
        if rem > 0.1: self.W(rem)

# ---- the sentence used across scenes ----
SENT = ["The","animal","didn't","cross","the","street","because","it","was","tired"]
def sentence(hi=None):
    g = VGroup(*[Text(w, font_size=34,
        color=GOLD if w==hi else INK, weight=BOLD if w==hi else NORMAL) for w in SENT])
    g.arrange(RIGHT, buff=0.22)
    if g.width > 12.5: g.scale(12.5/g.width)
    return g

class S01(Base):  # the question + arc it->animal
    def construct(self):
        self.ambient()
        title = Text('Which word does "it" mean?', font_size=46, color=INK).to_edge(UP, buff=1.1)
        s = sentence(); s.shift(UP*0.2)
        self.P(FadeIn(title, shift=DOWN*0.3), rt=1.0)
        self.P(LaggedStartMap(FadeIn, s, shift=UP*0.2, lag_ratio=0.12), rt=1.6)
        it = s[7]; animal = s[1]
        self.P(Indicate(it, color=GOLD, scale_factor=1.5), rt=0.9)
        arc = ArcBetweenPoints(it.get_top(), animal.get_top(), angle=-PI/2.2, color=GOLD)
        sp = spark(GOLD, 0.12)
        self.P(Create(arc), MoveAlongPath(sp, arc), rt=1.6, rate_func=smooth)
        self.P(Indicate(animal, color=GOLD, scale_factor=1.4), Flash(animal, color=GOLD), rt=0.9)
        self.hold()

class S02(Base):  # "Attention Is All You Need" -> branching models
    def construct(self):
        self.ambient()
        yr = Text("2017", font_size=30, color=DIM).to_edge(UP, buff=1.0)
        card = RoundedRectangle(width=6.2, height=1.5, corner_radius=0.18,
            stroke_color=BLUE, fill_color="#141d3c", fill_opacity=0.9).shift(UP*0.6)
        lbl = Text("Attention Is All You Need", font_size=34, color=INK).move_to(card)
        self.P(FadeIn(yr), GrowFromCenter(card), rt=1.0)
        self.P(Write(lbl), rt=1.0)
        names = ["ChatGPT","Claude","Gemini","Llama"]
        chips = VGroup()
        for i,n in enumerate(names):
            x = -4.2 + i*2.8
            c = VGroup(RoundedRectangle(width=2.1,height=0.7,corner_radius=0.14,
                    stroke_color=PURPLE, fill_color="#1a1430", fill_opacity=0.9),
                    Text(n, font_size=26, color=INK))
            c[1].move_to(c[0]); c.move_to([x,-2.3,0]); chips.add(c)
        lines = VGroup(*[Line(card.get_bottom(), ch.get_top(), color=BLUE, stroke_opacity=0.6) for ch in chips])
        self.P(LaggedStartMap(Create, lines, lag_ratio=0.15),
               LaggedStartMap(FadeIn, chips, shift=UP*0.2, lag_ratio=0.15), rt=2.2)
        self.hold()

class S03(Base):  # cocktail party — the IMAGE carries it; manim adds title + caption + life
    def construct(self):
        self.ambient(4)
        title = Text("The cocktail party", font_size=46, color=INK).to_edge(UP, buff=0.9)
        cap = Text("one voice cuts through — your name", font_size=30, color=GOLD).next_to(title, DOWN, buff=0.25)
        self.P(FadeIn(title, shift=DOWN*0.2), rt=1.0)
        self.P(FadeIn(cap, shift=UP*0.2), rt=0.9)
        # a soft highlight ring breathing over the glowing figure in the image (center-right)
        rings = VGroup(*[Circle(radius=r, color=GOLD, stroke_opacity=0.0) for r in [0.5,0.9]]).move_to([1.1,-0.2,0])
        for ring in rings:
            self.P(ring.animate.set_stroke(opacity=0.5).scale(1.5), rt=0.6, rate_func=there_and_back)
        self.hold()

class S04(Base):  # spotlight — the IMAGE carries it; manim adds title + caption + life
    def construct(self):
        self.ambient(3)
        title = Text("A spotlight that chooses what to ignore", font_size=42, color=INK).to_edge(UP, buff=0.9)
        cap = Text("your mind is always choosing what to ignore", font_size=28, color=GOLD).next_to(title, DOWN, buff=0.25)
        self.P(FadeIn(title, shift=DOWN*0.2), rt=1.0)
        self.P(FadeIn(cap, shift=UP*0.2), rt=0.9)
        self.hold()

class S05(Base):  # how does a machine look back — scanning pulse
    def construct(self):
        self.ambient()
        title = Text('How does a machine "look back"?', font_size=44, color=INK).to_edge(UP, buff=1.0)
        s = sentence(hi="it")
        self.P(FadeIn(title), FadeIn(s), rt=1.2)
        it = s[7]
        sp = spark(GOLD,0.1).move_to(it)
        self.add(sp)
        for w in [s[5],s[1],s[9],s[1]]:
            beam = Line(it.get_center(), w.get_center(), color=BLUE, stroke_opacity=0.5)
            self.P(Create(beam), sp.animate.move_to(w), rt=0.7, rate_func=smooth)
            self.P(FadeOut(beam), sp.animate.move_to(it), rt=0.5)
        self.hold()

class S06(Base):  # the attention grid
    def construct(self):
        self.ambient(4)
        W6 = ["animal","crossed","the","street","because","it","tired"]; n=len(W6)
        IT, AN, ST = 5, 0, 3
        title = Text("Every word scores every other word", font_size=40, color=INK).to_edge(UP, buff=0.7)
        cells = VGroup(); cell=0.62
        grid = VGroup()
        for i in range(n):
            for j in range(n):
                sq = Square(side_length=cell, stroke_width=1, stroke_color="#2c3666",
                            fill_color="#2a3a68", fill_opacity=0.15)
                sq.move_to([(j-n/2)*cell, (n/2-i)*cell -0.3, 0]); grid.add(sq); cells.add(sq)
        rowlabels = VGroup(*[Text(W6[i], font_size=18, color=DIM).next_to(grid[i*n], LEFT, buff=0.15) for i in range(n)])
        self.P(FadeIn(title), Create(grid, lag_ratio=0.01), FadeIn(rowlabels), rt=2.0)
        # shimmer: random weights
        random.seed(3)
        self.P(*[c.animate.set_fill(GOLD, opacity=random.uniform(0.1,0.7)) for c in cells], rt=1.4)
        # isolate "it" row
        nonit = VGroup(*[cells[i*n+j] for i in range(n) for j in range(n) if i!=IT])
        self.P(nonit.animate.set_fill("#2a3a68", opacity=0.06), rt=1.0)
        itrow = [cells[IT*n+j] for j in range(n)]
        weights = {AN:0.97, ST:0.12, 6:0.55, 4:0.3}
        self.P(*[itrow[j].animate.set_fill(GOLD, opacity=weights.get(j,0.12)) for j in range(n)], rt=1.2)
        # lock on
        lock = itrow[AN]
        self.P(lock.animate.set_fill(GOLD, opacity=1).set_stroke(GOLD,3), Flash(lock, color=GOLD), rt=0.9)
        cap = Text('"it"  →  "animal"   not "street"', font_size=28, color=GOLD).next_to(grid, DOWN, buff=0.35)
        self.P(FadeIn(cap, shift=UP*0.2), rt=0.8)
        self.hold()

class S07(Base):  # query / key / value
    def construct(self):
        self.ambient()
        title = Text("Query · Key · Value", font_size=44, color=INK).to_edge(UP, buff=1.0)
        it = VGroup(spark(BLUE,0.5), Text('"it"', font_size=30, color=INK)).move_to(LEFT*3.5)
        an = VGroup(spark(GOLD,0.5), Text('"animal"', font_size=28, color=INK)).move_to(RIGHT*3.5)
        self.P(FadeIn(title), FadeIn(it, shift=RIGHT*0.3), FadeIn(an, shift=LEFT*0.3), rt=1.2)
        q = spark(BLUE,0.1).move_to(it)
        self.add(q)
        self.P(q.animate.move_to(an), rt=1.2, rate_func=smooth)
        link = Line(it.get_right(), an.get_left(), color=GOLD)
        self.P(Create(link), Flash(an, color=GOLD), rt=0.9)
        cap = Text("question meets answer — attention fires", font_size=26, color=GOLD).next_to(link, DOWN, buff=0.6)
        self.P(FadeIn(cap), rt=0.8)
        self.hold()

class S08(Base):  # multiply into a lattice
    def construct(self):
        self.ambient(3)
        title = Text("One move, repeated billions of times", font_size=40, color=INK).to_edge(UP, buff=0.8)
        self.P(FadeIn(title), rt=0.8)
        layers = VGroup()
        for L in range(7):
            g = VGroup(*[Dot(radius=0.05, color=BLUE).set_opacity(0.5-L*0.05) for _ in range(36)])
            for k,d in enumerate(g):
                d.move_to([(k%6-2.5)*0.5 + L*0.22, (k//6-2.5)*0.4 + L*0.16 -0.5, 0])
            layers.add(g)
        self.P(LaggedStartMap(FadeIn, layers, shift=UP*0.2, lag_ratio=0.18), rt=2.4)
        self.P(layers.animate.shift(UP*0.3).set_opacity(0.7), rt=1.2, rate_func=there_and_back)
        self.hold()

class S09(Base):  # tool -> mirror — the brain-network IMAGE carries it; manim adds the title
    def construct(self):
        self.ambient(4)
        title = Text("We built a tool. We got a mirror.", font_size=46, color=INK).to_edge(UP, buff=0.9)
        cap = Text("attention — made visible for the first time", font_size=28, color=GOLD).next_to(title, DOWN, buff=0.25)
        self.P(FadeIn(title, shift=DOWN*0.2), rt=1.0)
        self.P(FadeIn(cap, shift=UP*0.2), rt=0.9)
        self.hold()

class S10(Base):  # anchor
    def construct(self):
        self.ambient(6)
        l1 = Text("Intelligence isn't knowing everything.", font_size=46, color=INK)
        l2 = Text("It's knowing what to ignore.", font_size=46, color=INK)
        VGroup(l1,l2).arrange(DOWN, buff=0.3).shift(UP*1.7)
        sub = Text("AI is the Universal Mind  ·  Ep.1 — Attention", font_size=28, color=PURPLE).next_to(l2, DOWN, buff=0.5)
        self.P(Write(l1), rt=1.4)
        self.P(Write(l2), rt=1.4)
        self.P(FadeIn(sub, shift=UP*0.2), rt=1.0)
        self.hold()
