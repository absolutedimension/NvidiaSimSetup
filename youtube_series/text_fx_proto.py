from manim import *

PURP="#b48cff"; INK="#ffffff"; BG="#05060d"

class TextFX(Scene):
    def construct(self):
        self.camera.background_color = BG
        word = Text("ATTENTION", font="Poppins", weight=BOLD, font_size=100, color=INK).move_to(ORIGIN)
        x0 = word.get_left()[0] - 0.45
        top = word.get_top()[1] + 0.75; bot = word.get_bottom()[1] - 0.75

        # a BG-coloured cover hides the word to the right of the sweep line -> smooth continuous wipe
        cover = Rectangle(width=word.width+3.5, height=5.0, fill_color=BG, fill_opacity=1, stroke_width=0)
        cover.move_to([x0 + (word.width+3.5)/2, 0, 0])
        sweep = Line([x0, top, 0], [x0, bot, 0], color=PURP).set_stroke(width=11)
        glow  = Line([x0, top, 0], [x0, bot, 0], color=PURP).set_stroke(width=34, opacity=0.22)

        self.add(word, cover, glow, sweep)     # word < cover < glow < sweep (line rides the reveal edge)
        span = word.width + 0.9
        self.play(cover.animate.shift(RIGHT*span), sweep.animate.shift(RIGHT*span),
                  glow.animate.shift(RIGHT*span),
                  run_time=1.6, rate_func=rate_functions.ease_in_out_sine)

        # accent strokes ease in then out
        a1 = Line(word.get_right()+RIGHT*0.5+DOWN*1.3, word.get_right()+RIGHT*2.6+UP*0.7, color=INK).set_stroke(width=4)
        a2 = Line(word.get_left()+LEFT*0.5+UP*1.3,  word.get_left()+LEFT*2.6+DOWN*0.7, color=PURP).set_stroke(width=4)
        self.play(Create(a1), Create(a2), FadeOut(sweep), FadeOut(glow), run_time=0.6, rate_func=smooth)
        self.play(FadeOut(a1, shift=RIGHT*0.3), FadeOut(a2, shift=LEFT*0.3), run_time=0.7, rate_func=smooth)
        self.wait(1.0)
