from manim import *
import os, json

PURP="#b48cff"; INK="#ffffff"
DUR=float(os.environ.get("SCENE_DUR","30"))
PH=json.load(open("/tmp/cap_phrases.json"))   # [{"text","start","end"}]

class Caps(MovingCameraScene):
    def construct(self):
        t=0.0; prev=None
        Y=DOWN*2.85                              # fixed lower position (text-safe zone)
        for p in PH:
            s=float(p["start"])
            if s>t+0.02:
                self.wait(s-t); t=s
            g=Text(p["text"].strip(), font="Poppins", weight=BOLD, font_size=46, color=INK).move_to(Y)
            if g.width>16: g.scale(16/g.width)
            x0=g.get_left()[0]-0.3; topy=g.get_top()[1]+0.22; boty=g.get_bottom()[1]-0.22
            ln  =Line([x0,topy,0],[x0,boty,0],color=PURP).set_stroke(width=8)
            glow=Line([x0,topy,0],[x0,boty,0],color=PURP).set_stroke(width=24,opacity=0.25)
            self.add(glow,ln)
            anims=[LaggedStartMap(FadeIn,g,lag_ratio=0.10,rate_func=smooth),
                   ln.animate.shift(RIGHT*(g.width+0.5)), glow.animate.shift(RIGHT*(g.width+0.5))]
            if prev is not None: anims.append(FadeOut(prev))
            self.play(*anims, run_time=0.5, rate_func=smooth)
            self.play(FadeOut(ln),FadeOut(glow), run_time=0.12)
            t+=0.62; prev=g
        if DUR>t: self.wait(DUR-t)
