# Interactive lesson — STEP authoring schema

A lesson = `{ "slug", "title", "steps": [ ... ] }` saved as JSON in `lesson_src/<course>/<slug>.json`.
The builder injects `steps` into the shared engine. **First step must be `intro`, last must be `done`.**
A good lesson is **8–13 steps**, mixes types, opens a curiosity gap, builds one idea, ends with a reflect.

Pedagogy (mirror the agentic lessons): teach ONE concept, concretely, with the learner's own world.
Every gradable step has `hints` (1–2, escalating) and `why` (the explanation shown after answering).
Keep copy tight and warm. Use real examples, not abstractions. Emoji sparingly for `art`/cards.

## Step types

```jsonc
{ "type":"intro", "art":"🤖 → 🔁", "prompt":"Big question?", "sub":"1–2 sentences of hook + what they'll be able to do.", "cta":"Start" }

{ "type":"mcq", "prompt":"Question?", "sub":"Pick one, then check.",
  "options":[{"t":"option A"},{"t":"option B"},{"t":"option C"}],
  "correct":1, "why":"Why the right one is right and others aren't.",
  "hints":["nudge 1","nudge 2"] }

{ "type":"multi", "prompt":"Tap ALL that apply.", "sub":"…",
  "chips":["a","b","c","d"], "correct":[0,1,3], "why":"…", "hints":["…"] }

{ "type":"classify", "prompt":"Sort each into the right bin.", "sub":"Tap an item, then a bin.",
  "buckets":["Bin A","Bin B"], "items":[{"t":"thing","b":0},{"t":"thing2","b":1}],
  "constraints":["All sorted","Every one correct"], "hints":["…"] }

{ "type":"reveal", "prompt":"The N parts.", "sub":"Tap each card.",
  "cards":[{"em":"🎯","h":"Title","b":"short body"}, … ] }      // no grading; teaching cards

{ "type":"order", "prompt":"Tap the steps in order.", "sub":"…",
  "chips":["step text A","step text B","step text C"], "correct":[1,0,2],   // correct = order of chip indices
  "constraints":["Order is correct"], "hints":["…"] }

{ "type":"trace", "prompt":"Walk it through a real run.", "sub":"Pick the next move at each turn.",
  "goal":"the goal line shown above the log",
  "turns":[ {"situation":"what's happening","q":"what next?","options":["a","b","c"],"correct":0,"log":"📒 line added to the run log"}, … ],
  "hints":["…"] }

{ "type":"tf", "prompt":"True or false?", "sub":"Then check all at once.",
  "statements":[{"t":"claim","answer":true,"why":"…"},{"t":"claim2","answer":false,"why":"…"}],
  "hints":["…"] }

{ "type":"reflect", "capture":true, "prompt":"Tell us about you / make it yours.", "sub":"Not graded.",
  "fields":[{"k":"work","label":"question","ph":"placeholder eg"}, … ] }   // k is a profile key: work|interest|goal|stop|tools|why|experience|...

{ "type":"done" }
```

## Rules
- Indices (`correct`, `b`) are 0-based and must point at real options/buckets.
- `order.correct` is the sequence of chip indices in the right order.
- Put exactly one `reflect` near the end that ties the lesson to the learner's real project (`capture:true`).
- Award flow is automatic (the engine gives gems per correct step + a completion bonus). Don't add scoring.
- Keep `why`/`hints` specific to the content — they are the teaching, not filler.
