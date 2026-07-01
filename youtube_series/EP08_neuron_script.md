---
title: "AI is the Universal Mind — Ep.8: The Neuron"
subtitle: "What is a neural network? — how a machine learns to see a number"
video_type: youtube_episode
length_target_sec: 620                      # ~10.3 min, 14 scenes (extendable)
mode: C                                     # Manim engine + contextual bg + captions + focus bed
voice: { name: male_confident, speed: 0.75 }
background_shader: circuit_mind             # neuron/mind feel
presenter: none                             # 3B1B / Kurzgesagt style — voice + motion graphics, no face
music: focus_bed                            # 12 Hz isochronic bed, sidechain-ducked
aspect: 16:9
notes: |
  ORIGINAL teaching of the same topic as 3Blue1Brown "Deep learning ch.1".
  Not a copy — original narration, original visual design, TrigunAI series voice.
  Pedagogy arc: a scrawled digit you read instantly → the machine sees only a grid of
  brightness numbers → a neuron is a thing holding one number → 784 input neurons →
  10 output neurons → hidden layers as a hopeful hierarchy of features → a connection
  is a weight → a neuron computes a weighted sum → a bias is a threshold → squish to
  keep it 0..1 → ~13,000 knobs → "learning" = finding the knobs (teaser for next ep) →
  anchor: a neural network is just one function, a big stack of weighted sums and squishes.
---

## scenes

### scene_01_hook
narration: |
  Look at this number.
  You know it is a three. Instantly. Without effort.
  Now look at this one. Scrawled, lopsided, barely closed.
  Still a three. You did not even hesitate.
  Your brain just did something staggering, and it felt like nothing.
  Here is the question I want to chase.
  What would it take to build a machine that can do the same thing?
on_screen:
  title: You see a three. How?
  body: "3"
  layout: center
visual: a clean digit "3" fades up; then three messier hand-drawn threes appear beside it, each pulsing softly as it is recognized
duration_hint_sec: 32

### scene_02_the_gap
narration: |
  This feels easy, so we never notice how hard it is.
  You can recognize a three written ten thousand different ways.
  Thin, fat, slanted, shaky.
  No two are the same picture, yet you map them all to one idea.
  Three.
  Write down the rule you used. You can't. There isn't one you can name.
  And that is exactly the problem we have to solve.
on_screen:
  title: Ten thousand threes, one idea
  layout: center
visual: a grid fills with wildly varied handwritten threes; they all flow toward a single glowing label "3"
duration_hint_sec: 30

### scene_03_what_machine_sees
narration: |
  So let's start where the machine starts.
  To a computer, this image is not a number at all.
  It is a tiny grid. Twenty-eight pixels across, twenty-eight down.
  Seven hundred and eighty-four little squares.
  And each square is just one value. How bright it is.
  Zero for pure black. One for pure white. A gray is somewhere in between.
  That's the whole input. Seven hundred and eighty-four brightness numbers.
  No threes. No shapes. Just numbers.
on_screen:
  title: 28 × 28 = 784 brightness values
  body: "black = 0   ·   white = 1"
  layout: center
visual: the digit zooms into a 28x28 pixel grid; gridlines appear; each cell flips to show its 0..1 value; the shape dissolves into a field of numbers
duration_hint_sec: 34

### scene_04_the_neuron
narration: |
  Now meet the one idea this whole thing is built from.
  The neuron.
  Forget biology for a second. In a network, a neuron is almost embarrassingly simple.
  It is just a container that holds a single number, between zero and one.
  We call that number its activation.
  Zero means the neuron is quiet. One means it is lit up, firing.
  That's it. A neuron is a thing that holds how strongly it is on.
on_screen:
  title: A neuron holds one number (0 to 1)
  subtitle: its activation
  layout: center
visual: a single circle appears; a value 0.00 ticks up toward 0.97 as the circle brightens from dark to glowing
duration_hint_sec: 30

### scene_05_input_layer
narration: |
  So take those seven hundred and eighty-four brightness values,
  and pour each one into its own neuron.
  Now we have seven hundred and eighty-four neurons,
  one per pixel, each holding how bright that pixel is.
  Bright pixels, lit neurons. Dark pixels, quiet ones.
  This is the first layer of the network. The input.
  It is literally just the picture, turned into a column of lights.
on_screen:
  title: The input layer = the picture as neurons
  layout: center
visual: the 28x28 grid unrolls into a tall column of 784 small circles; circles light up matching the digit's bright pixels
duration_hint_sec: 30

### scene_06_output_layer
narration: |
  Now jump to the other end. The answer.
  At the far side we put just ten neurons.
  One for each possible digit. Zero through nine.
  When the network runs, each of these lights up a little.
  The one that lights up brightest is the network's guess.
  If the ten-neuron lights up to nearly one, the machine is saying,
  I think this is a three.
  Input on one side. Ten answers on the other. Now we need what goes between.
on_screen:
  title: The output layer = 10 neurons, one per digit
  body: "0 1 2 3 4 5 6 7 8 9"
  layout: center
visual: ten circles labeled 0-9 in a column; the "3" circle pulses brightest while others stay dim
duration_hint_sec: 30

### scene_07_hidden_layers
narration: |
  Between the input and the answer, we stack a couple more layers.
  We call them hidden layers, because we never look at them directly.
  And here is the hope. The beautiful, unproven hope.
  Maybe the first hidden layer learns to spot tiny edges.
  Little strokes of light. A short curve here, a straight bit there.
  Maybe the next layer assembles those edges into pieces.
  A loop at the top. A vertical line. The fork of a three.
  And the last layer puts the pieces together into a whole digit.
  Edges, into parts, into numbers.
on_screen:
  title: Hidden layers — a hierarchy of features?
  bullets: ["pixels → edges", "edges → parts", "parts → digits"]
  layout: bullets
visual: four columns of neurons appear left to right; faint links between them; a small loop and stroke icons glow inside the middle layers
duration_hint_sec: 36

### scene_08_why_layers
narration: |
  Why build it in layers like that?
  Because that is how hard problems come apart.
  Recognizing a loop is easier than recognizing a whole three.
  Recognizing an edge is easier than recognizing a loop.
  Each layer solves a slightly simpler question and hands its answer up.
  So if the machine could learn to detect edges,
  then parts from edges,
  then digits from parts,
  the impossible task becomes a stack of possible ones.
  That is the bet. Now, how does one layer actually talk to the next?
on_screen:
  title: Break one hard problem into layers of easy ones
  layout: center
visual: a single big question mark splits into three smaller, simpler shapes stacked in a staircase rising to the right
duration_hint_sec: 32

### scene_09_weights
narration: |
  Here is the machinery. Every neuron in one layer
  connects to every neuron in the next.
  And every one of those connections carries a number. A weight.
  A weight is just how much this neuron cares about that one.
  A big positive weight says, if you are lit up, I want to light up too.
  A negative weight says, if you are on, push me down.
  A weight near zero says, I don't care about you at all.
  The whole intelligence of the network lives in these weights.
on_screen:
  title: Every connection has a weight
  body: "weight = how much one neuron listens to another"
  layout: center
visual: two layers of neurons fully connected; lines vary in thickness and color — thick gold for strong positive, thin red for negative, faint gray for near-zero
duration_hint_sec: 34

### scene_10_weighted_sum
narration: |
  So what does a single neuron actually do?
  It looks at every neuron feeding into it.
  It multiplies each one's activation by the weight on that connection.
  And it adds them all up.
  Strong connections from lit neurons pull the total up.
  Negative ones drag it down.
  One neuron, one weighted sum.
  That number is the raw evidence for whether this neuron should fire.
on_screen:
  title: A neuron computes a weighted sum
  body: "(a₁·w₁) + (a₂·w₂) + (a₃·w₃) + …"
  layout: center
visual: one target neuron highlighted; incoming activations and weights multiply along each line and stream into a running total counter
duration_hint_sec: 32

### scene_11_bias
narration: |
  But sometimes a neuron should stay quiet unless the evidence is really strong.
  So we add one more number. A bias.
  Think of it as a threshold the sum has to clear before the neuron wakes up.
  A high bias makes a neuron hard to convince. Skeptical.
  A low one makes it eager to fire.
  So now every neuron has its own weights, and its own bias.
  Its own little opinion about what it takes to light up.
on_screen:
  title: The bias = how hard it is to fire
  body: "weighted sum  +  bias"
  layout: center
visual: a horizontal threshold line sits across the neuron; the weighted-sum bar must rise past the line (the bias shifts the line up or down) before the neuron glows
duration_hint_sec: 30

### scene_12_squish
narration: |
  One last touch. That weighted sum could be anything. Wildly big, wildly negative.
  But a neuron's activation has to stay between zero and one.
  So we squeeze the number through a little squishing function.
  Huge positive numbers get pressed toward one. Lit.
  Huge negative numbers get pressed toward zero. Quiet.
  And the in-between gets a smooth, gentle middle.
  Weighted sum, plus bias, squished into an activation.
  That is the complete life of a single neuron.
on_screen:
  title: Squish the result back into 0 to 1
  body: "activation = squish( weighted sum + bias )"
  layout: center
visual: an S-shaped curve draws itself; a wild input value far on the axis slides in and maps onto the curve, snapping out to a value between 0 and 1
duration_hint_sec: 32

### scene_13_scale
narration: |
  Now zoom out and feel the size of this.
  Just one small network for our little digits
  has around thirteen thousand weights and biases.
  Thirteen thousand knobs.
  Every single one a dial that can be turned, nudged, tuned.
  Turn them one way, the machine sees noise.
  Turn them just right, and a column of seven hundred and eighty-four lights
  flows through the layers and lands, cleanly, on three.
  The whole question of intelligence becomes one question.
  What setting of the knobs makes it work?
on_screen:
  title: ~13,000 knobs to tune
  layout: center
visual: the full network lights up end to end; a digit's activations cascade left to right and resolve at the "3" output; thousands of weight-lines shimmer
duration_hint_sec: 34

### scene_14_anchor
narration: |
  So step back and see what a neural network really is.
  Not a brain. Not magic.
  It is one function. A very large one.
  Pour in seven hundred and eighty-four numbers, and out come ten.
  And everything in between is just weighted sums and gentle squishes,
  repeated, layer after layer.
  We did not tell it what a three looks like.
  We built a machine with thirteen thousand knobs,
  and the only thing left to do is teach it to tune itself.
  That tuning has a name. Learning.
  And that is where we go next.
on_screen:
  title: "A neural network is just one big function."
  subtitle: "AI is the Universal Mind · Ep.8 — The Neuron"
  layout: center
visual: the whole network collapses into a single glowing box labeled f(x); 784 arrows in, 10 arrows out; the anchor line resolves; soft fade to series card
duration_hint_sec: 34
