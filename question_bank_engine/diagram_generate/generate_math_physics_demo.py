#!/usr/bin/env python3
"""Figure-first diagram-question generation for MATHS and PHYSICS — same principle as chemistry.

  define a parametric figure -> render deterministically -> COMPUTE the answer (SymPy / physics
  equations) -> phrase an MCQ. Figure correct because we drew it; answer correct because we
  computed it. Renderers per domain: matplotlib (graphs/geometry), schemdraw (circuits), SymPy
  (exact algebra). CPU only, copyright-clean, unlimited.
"""
import os
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/tmp/genq"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 12, "axes.linewidth": 1.0})
Q = []


def mcq(subject, stem, correct, distractors, solution, figure):
    opts = [str(correct)] + [str(d) for d in distractors]
    rot = sum(map(ord, stem)) % len(opts)
    opts = opts[rot:] + opts[:rot]
    labels = ["A", "B", "C", "D"][:len(opts)]
    ans = labels[opts.index(str(correct))]
    Q.append({"subject": subject, "stem": stem,
              "options": [{"label": l, "text": t} for l, t in zip(labels, opts)],
              "correct_answer": ans, "solution": solution, "figure": figure,
              "answer_source": "computed (SymPy / physics equations)"})


# ---------- MATHS 1: quadratic graph -> roots (SymPy exact) ----------
x = sp.symbols("x")
a, b, c = 1, -5, 6                      # y = x^2 - 5x + 6
expr = a * x**2 + b * x + c
roots = sorted(sp.solve(expr, x))       # [2, 3]  <- ground truth
xs = np.linspace(-1, 6, 400); ys = a * xs**2 + b * xs + c
fig, ax = plt.subplots(figsize=(4.3, 3.4))
ax.plot(xs, ys, lw=2, color="#a9791f"); ax.axhline(0, color="#888", lw=.8); ax.axvline(0, color="#888", lw=.8)
ax.grid(alpha=.25); ax.set_xlabel("x"); ax.set_ylabel("y"); fig.tight_layout()
f = f"{OUT}/mp_quad.png"; fig.savefig(f, dpi=140); plt.close(fig)
mcq("Maths", "The curve shown intersects the x-axis at:",
    f"x = {roots[0]}, {roots[1]}", ["x = -2, -3", "x = 1, 6", "x = 2, -3"],
    f"The curve is y=x²−5x+6; solving x²−5x+6=0 gives x={roots[0]}, {roots[1]}.", f)

# ---------- MATHS 2: coordinate-geometry triangle -> area (exact) ----------
A, B, C = (0, 0), (6, 0), (0, 8)
area = abs((B[0]-A[0])*(C[1]-A[1]) - (C[0]-A[0])*(B[1]-A[1])) / 2   # 24
fig, ax = plt.subplots(figsize=(4.3, 3.4))
tri = plt.Polygon([A, B, C], fill=True, facecolor="#f3ead6", edgecolor="#a9791f", lw=2)
ax.add_patch(tri)
for p, nm in [(A, "A"), (B, "B"), (C, "C")]:
    ax.plot(*p, "o", color="#a9791f"); ax.annotate(f"{nm}{p}", p, textcoords="offset points", xytext=(6, 6))
ax.set_xlim(-1, 7); ax.set_ylim(-1, 9); ax.grid(alpha=.25); ax.set_aspect("equal"); fig.tight_layout()
f = f"{OUT}/mp_tri.png"; fig.savefig(f, dpi=140); plt.close(fig)
mcq("Maths", "The area of the triangle with the vertices shown is (square units):",
    int(area), [12, 48, 20],
    f"Area = ½|x_B·y_C − x_C·y_B| = ½×|6×8| = {int(area)} sq units.", f)

# ---------- PHYSICS 1: velocity-time graph -> acceleration & displacement ----------
t = [0, 4, 8]; v = [0, 20, 20]          # accel 0-4s then constant
accel = (v[1] - v[0]) / (t[1] - t[0])   # 5 m/s^2
disp = 0.5 * (t[1]-t[0]) * v[1] + (t[2]-t[1]) * v[1]   # area = 120 m
fig, ax = plt.subplots(figsize=(4.3, 3.4))
ax.plot(t, v, lw=2.2, color="#2e6f9e", marker="o"); ax.fill_between(t, v, alpha=.12, color="#2e6f9e")
ax.set_xlabel("time (s)"); ax.set_ylabel("velocity (m/s)"); ax.grid(alpha=.25)
ax.set_xlim(0, 8.4); ax.set_ylim(0, 24); fig.tight_layout()
f = f"{OUT}/mp_vt.png"; fig.savefig(f, dpi=140); plt.close(fig)
mcq("Physics", "From the velocity–time graph shown, the acceleration during the first 4 s is (m/s²):",
    int(accel), [4, 10, 2],
    f"Acceleration = slope = Δv/Δt = 20/4 = {int(accel)} m/s².", f)
mcq("Physics", "From the velocity–time graph shown, the total displacement in 8 s is (m):",
    int(disp), [80, 160, 100],
    f"Displacement = area under graph = ½×4×20 + 4×20 = {int(disp)} m.", f)

# ---------- PHYSICS 2: resistor network -> equivalent resistance (schemdraw) ----------
try:
    import schemdraw, schemdraw.elements as elm
    R1, R2, R3 = 6, 3, 4
    Req = round(1/(1/R1 + 1/R2) + R3, 1)      # (6||3)=2, +4 = 6.0
    Req = int(Req) if Req == int(Req) else Req
    with schemdraw.Drawing(file=f"{OUT}/mp_circuit.png", show=False) as d:
        d.config(unit=2.2)
        d += elm.Dot().label("A", "left")
        d += (top := elm.Line().right().length(1))
        d.push()
        d += elm.Resistor().right().label(f"{R1}Ω")
        d += (bot := elm.Line().right().length(1))
        d.pop()
        d += elm.Line().down().length(2)
        d += elm.Resistor().right().label(f"{R2}Ω")
        d += elm.Line().up().length(2)
        d += elm.Resistor().right().label(f"{R3}Ω")
        d += elm.Dot().label("B", "right")
    f2 = f"{OUT}/mp_circuit.png"
    mcq("Physics", "The equivalent resistance between A and B in the network shown is (Ω):",
        Req, [9, 4, 13],
        f"{R1}Ω ∥ {R2}Ω = 2Ω, in series with {R3}Ω → 2+4 = {Req}Ω.", f2)
except Exception as ex:
    print("circuit skipped:", ex)

import json
json.dump(Q, open(f"{OUT}/mp_questions.json", "w"), indent=1)
for q in Q:
    print(f"[{q['subject']}] {q['stem'][:64]}  ans={q['correct_answer']} "
          f"({[o['text'] for o in q['options']]})")
print(f"\nwrote {len(Q)} maths/physics questions + figures")
