# Kids Worksheet Grammar — the archetype library (K / Class 1–5)

*Owner: Deepak · Started 2026-08-02 · Companion to `KIDS_QUIZ_ICSE_G3_PLAN.md` (curriculum),
`gen_content.py` (Maths generator), `KIDS_ASSESSMENT_PLAN.md`, and the `trigunai-kids-education` skill.*

---

## 0. Why this file exists (the thesis)

> **The questions are a commodity; the moat is (curriculum fidelity) × (authentic delivery format).**

Any LLM can write "3 + 4 = ?". What a parent recognises as *real school work* is the **format** — trace
the number, match the column, colour-by-number, fill the missing letter. This file is the reusable core:
a **grammar** of the ~30 worksheet *archetypes* a Class 1–5 child actually meets, each defined precisely
enough to (a) prompt the LLM to fill it with curriculum-locked content and (b) render it in the app
(interactive) and on paper (printable).

We do **not** fine-tune a model on scraped worksheets. We do what `learn-dj-style` does: reverse-engineer
the **grammar**, then *generate fresh* inside it. K–5 worksheet styles are a **finite, small set** —
capture the archetypes and you cover ~90% of every sheet in the school bag.

---

## 1. Copyright stance — why this is clean by construction

- **A *format* is an idea, not copyrightable.** "Match the following", "trace the letter", "odd one out"
  belong to nobody. The archetype library below is therefore copyright-clean on its face.
- **We generate the *content* fresh** per curriculum node — never reproduce a specific publisher's sheet.
- **We sample only from open / government sources** to calibrate tone, wording, and edge cases:

| Source | What it gives | Licence / status |
|---|---|---|
| **DIKSHA** — `diksha.gov.in` | Govt (MoE) energised textbooks + worksheets, NCERT + state boards | CC-BY-SA 4.0 / GoI open — **safe to sample & adapt** |
| **NCERT / ePathshala** — `ncert.nic.in`, `epathshala.nic.in` | Textbooks (Math-Magic, Marigold, EVS), **Exemplar** problems | Free for education; formats not copyrightable |
| **NROER** — `nroer.gov.in` | National Repository of Open Educational Resources | CC-licensed |
| **CISCE** — `cisce.org` | ICSE "Classes I–V" curriculum document | Official — **index/scope reference** |
| State **SCERT / DIKSHA state nodes** | Bihar Board etc. scope + worksheets | Govt open |

> ⚠️ Most foreign "free worksheet" sites (k5learning, education.com, etc.) are **copyrighted** — learn the
> archetype, never copy the sheet. When in doubt: govt/CC source to calibrate, LLM to generate.

---

## 2. How the grammar drives generation (the pipeline)

```
curriculum node            archetype              LLM fills             render
(taxonomy: exam→class   →  pick the fitting   →   content locked to  →  interactive (app)
 →subject→chapter→subtopic) worksheet type        that node             + printable (PDF)
```

Every generated item is a JSON object with a common envelope; the `type` selects the renderer:

```json
{
  "type":       "<archetype id, e.g. fill_sequence>",
  "subject":    "maths | english | evs | hindi",
  "chapter":    "<curriculum node this is locked to>",
  "band":       "1-2 | 3-5",
  "instruction":"child-facing line, warm + 1 emoji",
  "voice":      "TTS narration (edge-tts child voice)",
  "payload":    { …type-specific fields… },
  "answer":     "…type-specific…",
  "explain":    "one-line kind reveal"
}
```

This **extends** today's `gen_content.py` item (`{type:"mcq", …}`) — `mcq` becomes one archetype among ~30.

---

## 3. The Archetype Library

Each block: **id · machine `type` · subject · band · curriculum fit**, then what the child does, the
layout, instruction + voice tone, the `payload`/`answer` JSON shape, app vs print input, validation, and a
free source to calibrate against.

### 3A · Mathematics

Maths is largely **computable** — most of these plug straight into the existing `gen_content.py` templates;
the grammar just adds the *non-MCQ delivery formats* around the same computed values.

---

#### M01 · Number Tracing & Writing
**type** `trace_number` · Maths · band 1–2 · **fits** writing numerals (1–100)
**Child does:** traces dotted numerals, then writes them freehand.
**Layout:** row of large dotted glyphs → blank practice boxes; a themed count-strip beside them.
**Instruction:** "Trace the number 5, then write it yourself! ✏️"  **Voice:** "This is five. Trace it… now you try!"
**payload/answer:** `{"glyph":5,"repeats":4,"count_theme":"apples"}` · answer = stroke-match / self-check
**App:** finger-trace canvas · **Print:** dotted glyph + boxes
**Calibrate:** DIKSHA G1 Maths; NCERT Math-Magic-1

#### M02 · Count and Write
**type** `count_write` · Maths · band 1–2 · **fits** counting, cardinality
**Child does:** counts pictured objects, writes the numeral.
**Layout:** cluster of objects (🍎×7) → a blank box.  **Instruction:** "Count the apples and write the number! 🍎"
**payload/answer:** `{"emoji":"🍎","n":7}` · answer `7`
**App:** number pad · **Print:** blank box · **Validate:** exact
**Calibrate:** DIKSHA G1; NCERT Math-Magic-1

#### M03 · Match Quantity ↔ Numeral
**type** `match_quantity` · Maths · band 1–2 · **fits** number sense
**Child does:** draws a line from each object-group to its numeral.
**Layout:** two columns — groups on the left, numerals shuffled on the right.  **Instruction:** "Match the group to its number! ✏️"
**payload/answer:** `{"left":[{"emoji":"⭐","n":3},{"emoji":"🐟","n":5}],"right":[5,3]}` · answer = pairing map
**App:** drag-connect · **Print:** draw-a-line · **Validate:** pair set
**Calibrate:** DIKSHA G1

#### M04 · Fill the Missing Number
**type** `fill_sequence` · Maths · band 1–5 · **fits** number sequences, skip counting, before/after
**Child does:** writes the missing number(s) in a sequence.
**Layout:** row of boxes (train cars / stepping stones), 1–3 blank.  **Instruction:** "Fill in the missing number! 🚂"
**payload/answer:** `{"seq":[10,20,null,40],"step":10}` · answer `[30]`
**App:** number pad · **Print:** blank box · **Validate:** exact
**Calibrate:** DIKSHA; NCERT Math-Magic (skip counting)

#### M05 · Before / After / Between
**type** `neighbour_number` · Maths · band 1–3 · **fits** successor/predecessor
**Child does:** writes the number that comes before / after / between.
**Layout:** `__ , 47 , __` style with labelled slots.  **Instruction:** "What comes just after 47? ➡️"
**payload/answer:** `{"mode":"after","n":47}` · answer `48`
**App:** number pad · **Print:** box · **Validate:** exact
**Calibrate:** NCERT Math-Magic-2/3

#### M06 · Compare Quantities (>, <, =)
**type** `compare_symbol` · Maths · band 1–4 · **fits** comparing numbers
**Child does:** writes/taps the correct symbol between two numbers or groups.
**Layout:** `34 ◻ 43`, a symbol tray `< > =`.  **Instruction:** "Which is bigger? Put the right sign! 🐊"
**payload/answer:** `{"a":34,"b":43}` · answer `"<"`
**App:** tap symbol · **Print:** write symbol · **Validate:** exact
**Calibrate:** NCERT (the "hungry crocodile" motif is public/idea)

#### M07 · Colour by Number
**type** `color_by_number` · Maths · band 1–3 · **fits** number recognition, addition facts
**Child does:** solves each region's tiny sum, colours by the answer's key.
**Layout:** a simple picture split into regions, each labelled with a fact; a colour key.  **Instruction:** "Solve, then colour! 🎨"
**payload/answer:** `{"regions":[{"fact":"2+1","key":3}],"legend":{"3":"red","4":"blue"}}` · answer = region→colour map
**App:** tap-to-fill palette · **Print:** colour-in · **Validate:** self-check (app can auto-verify tapped colour)
**Calibrate:** DIKSHA art-integrated Maths

#### M08 · Addition / Subtraction (picture · vertical · horizontal)
**type** `arith` · Maths · band 1–5 · **fits** add/sub (carry/borrow scale by band)
**Child does:** solves; picture form for band 1–2, column form for 3–5.
**Layout:** band 1–2 = objects to count-on/take-away; band 3–5 = vertical sum with carry boxes.  **Instruction:** "Add it up! ➕"
**payload/answer:** `{"op":"+","a":234,"b":158,"carry_boxes":true}` · answer `392`
**App:** number pad (+ optional per-digit boxes) · **Print:** column · **Validate:** exact
**Calibrate:** NCERT Math-Magic; existing `gen_content.py g_add/g_sub`

#### M09 · Pattern Completion
**type** `pattern_next` · Maths · band 1–4 · **fits** patterns
**Child does:** picks/draws what comes next in a shape/colour/number pattern.
**Layout:** a repeating strip 🔺🔵🔺🔵❓ + an option tray.  **Instruction:** "What comes next? 🔁"
**payload/answer:** `{"seq":["🔺","🔵","🔺","🔵"],"options":["🔺","🔵","🟢"]}` · answer `"🔺"`
**App:** tap option · **Print:** circle/draw · **Validate:** exact
**Calibrate:** NCERT (Patterns chapter)

#### M10 · Shape Sort / Identify
**type** `shape_sort` · Maths · band 1–4 · **fits** geometry
**Child does:** names a shape, or sorts shapes into named bins.
**Layout:** a shape (or scatter of shapes) + labelled bins/options.  **Instruction:** "Sort the shapes into their homes! 🔷"
**payload/answer:** `{"items":["🔺","⬜","🔺"],"bins":["triangle","square"]}` · answer = item→bin map
**App:** drag-to-bin · **Print:** draw-a-line · **Validate:** set
**Calibrate:** NCERT (Shapes/Geometry)

#### M11 · Picture Word-Problem (one-step)
**type** `word_problem` · Maths · band 2–5 · **fits** add/sub/mul/div word problems
**Child does:** reads a short illustrated story, writes the answer.
**Layout:** 1–2 line story + supporting picture + answer box.  **Instruction:** "Read and solve! 🧺"
**payload/answer:** `{"story":"3 baskets, each has 4 apples. How many apples?","op":"*","a":3,"b":4}` · answer `12`
**App:** number pad · **Print:** box + working space · **Validate:** exact
**Calibrate:** NCERT Exemplar; existing `g_mul_word`

#### M12 · Clock & Calendar
**type** `read_clock` · Maths · band 2–5 · **fits** Time
**Child does:** reads the clock face, writes the time (or draws hands for a given time).
**Layout:** analog clock (or blank face).  **Instruction:** "What time is it? 🕐"
**payload/answer:** `{"mode":"read","h":3,"m":30}` · answer `"3:30"`
**App:** tap/drag hands · **Print:** write / draw hands · **Validate:** exact
**Calibrate:** NCERT (Time chapter)

#### M13 · Money (coins & bills)
**type** `count_money` · Maths · band 2–5 · **fits** Money (₹)
**Child does:** adds coins/notes, or makes an amount / a simple bill.
**Layout:** coin/note images + a total box (or a mini shop bill).  **Instruction:** "How much money? 🪙"
**payload/answer:** `{"coins":[10,5,2,2]}` · answer `19`
**App:** number pad / drag coins · **Print:** total box · **Validate:** exact
**Calibrate:** NCERT (Money chapter); existing `g_money`

---

### 3B · English

English band 1–2 is **phonics + tracing**; band 3–5 adds vocabulary, grammar, comprehension.
Content here is **generated fresh** (grounded on NCERT Marigold word lists), never copied.

---

#### E01 · Letter Tracing (upper / lower)
**type** `trace_letter` · English · band 1 · **fits** alphabet writing
**Child does:** traces dotted letters, then writes freehand; a picture cues the sound.
**Layout:** dotted `A a` glyphs + practice boxes + a cue picture (🍎 for A).  **Instruction:** "Trace A for Apple! 🍎"
**payload/answer:** `{"letter":"A","cue":"apple","cue_emoji":"🍎","repeats":4}` · answer = stroke-match
**App:** trace canvas · **Print:** dotted glyph · **Calibrate:** DIKSHA G1 English; NCERT Marigold-1

#### E02 · Match Upper ↔ Lower Case
**type** `match_case` · English · band 1 · **fits** letter recognition
**Child does:** connects each capital to its small letter.
**Layout:** two shuffled columns.  **Instruction:** "Match the big letter to the small one! 🔤"
**payload/answer:** `{"left":["A","B","C"],"right":["c","a","b"]}` · answer = pair map
**App:** drag-connect · **Print:** draw-a-line · **Validate:** set

#### E03 · Fill the Missing Letter
**type** `fill_letter` · English · band 1–3 · **fits** spelling, phonics
**Child does:** writes the missing letter(s) in a pictured word.
**Layout:** picture + `c _ t` with blank tiles.  **Instruction:** "Fill the missing letter! 🐱"
**payload/answer:** `{"word":"cat","blanks":[1],"emoji":"🐱"}` · answer `["a"]`
**App:** letter keys · **Print:** blank tile · **Validate:** exact
**Calibrate:** NCERT Marigold word lists

#### E04 · Picture ↔ Word Match
**type** `match_word_picture` · English · band 1–3 · **fits** vocabulary
**Child does:** connects each picture to its word.
**Layout:** pictures column + words column (shuffled).  **Instruction:** "Match the picture to its word! 🖼️"
**payload/answer:** `{"pairs":[["🐘","elephant"],["🌞","sun"]]}` · answer = pair map
**App:** drag-connect · **Print:** line · **Validate:** set

#### E05 · Rhyming Pairs
**type** `rhyme_match` · English · band 1–3 · **fits** phonological awareness
**Child does:** matches / picks the word that rhymes.
**Layout:** a target word + options (or two columns).  **Instruction:** "Which word rhymes with cat? 🎵"
**payload/answer:** `{"target":"cat","options":["hat","dog","sun"]}` · answer `"hat"`
**App:** tap · **Print:** circle · **Validate:** exact

#### E06 · Sight-Word Fill (cloze)
**type** `cloze` · English · band 2–5 · **fits** grammar, sight words, articles
**Child does:** fills the blank in a sentence from a word bank.
**Layout:** sentence with a blank + a small word bank.  **Instruction:** "Choose the right word! ✏️"
**payload/answer:** `{"sentence":"The cat is ___ the mat.","bank":["on","under","in"]}` · answer `"on"`
**App:** tap/drag word · **Print:** write · **Validate:** exact (accept synonyms via list)
**Calibrate:** NCERT Marigold sentences

#### E07 · Opposites (antonyms)
**type** `opposite` · English · band 2–5 · **fits** vocabulary
**Child does:** matches / writes the opposite word.
**Layout:** two columns or `big → ___`.  **Instruction:** "Write the opposite! ↔️"
**payload/answer:** `{"word":"big"}` · answer `["small","little"]`
**App:** tap/type · **Print:** write · **Validate:** answer-list

#### E08 · Beginning Sound
**type** `begin_sound` · English · band 1–2 · **fits** phonics
**Child does:** picks the letter a pictured word starts with.
**Layout:** picture + 3 letter options.  **Instruction:** "Which sound does it start with? 🔊"
**payload/answer:** `{"emoji":"🐟","word":"fish","options":["f","s","b"]}` · answer `"f"`
**App:** tap (voice reads the word) · **Print:** circle · **Validate:** exact

#### E09 · Sentence Ordering
**type** `order_words` · English · band 3–5 · **fits** sentence formation
**Child does:** arranges jumbled words into a correct sentence.
**Layout:** word tiles to sequence.  **Instruction:** "Put the words in order! 🧩"
**payload/answer:** `{"words":["is","cat","the","sleeping"]}` · answer `"the cat is sleeping"`
**App:** drag-reorder · **Print:** number the words · **Validate:** ordered match (accept valid variants)

---

### 3C · EVS / GK / Values (knowledge subjects)

Not computable → the LLM **RAG-generates fresh** grounded on the NCERT EVS chapter text (copyright-safe to
build on). These archetypes are the *delivery formats* that content flows into.

---

#### G01 · Match the Following
**type** `match_following` · EVS/GK · band 1–5 · **fits** any relational fact (animal→home, festival→month)
**Child does:** connects each item in column A to its match in column B.
**Layout:** two columns, B shuffled.  **Instruction:** "Match them correctly! ✏️"
**payload/answer:** `{"left":["Cow","Bird"],"right":["Nest","Shed"]}` · answer = pair map
**App:** drag-connect · **Print:** line · **Validate:** set
**Calibrate:** NCERT EVS "Looking Around"

#### G02 · Odd One Out
**type** `odd_one_out` · EVS/GK · band 1–5 · **fits** categorisation
**Child does:** picks the item that doesn't belong.
**Layout:** 4 pictures/words + tap.  **Instruction:** "Which one does not belong? 🔍"
**payload/answer:** `{"items":["🍎","🍌","🐶","🍇"],"category":"fruits"}` · answer `"🐶"`
**App:** tap · **Print:** cross out · **Validate:** exact

#### G03 · Label the Picture
**type** `label_picture` · EVS/GK · band 2–5 · **fits** parts of body/plant/map
**Child does:** drags/writes labels onto pointed parts of a diagram.
**Layout:** a diagram with lead-lines + a label bank.  **Instruction:** "Label the parts of the plant! 🌱"
**payload/answer:** `{"image":"plant","points":["root","stem","leaf"]}` · answer = point→label map
**App:** drag label · **Print:** write on the line · **Validate:** set
**Calibrate:** NCERT EVS diagrams (redraw, don't copy the image)

#### G04 · True / False
**type** `true_false` · EVS/GK · band 1–5 · **fits** factual recall
**Child does:** marks each statement ✓ or ✗.
**Layout:** statement + two buttons.  **Instruction:** "Is it true or false? 🤔"
**payload/answer:** `{"statement":"The sun rises in the west."}` · answer `false`
**App:** tap ✓/✗ · **Print:** write T/F · **Validate:** exact

#### G05 · Word-Bank Fill
**type** `wordbank_fill` · EVS/GK · band 2–5 · **fits** vocabulary recall
**Child does:** completes sentences using a given word bank.
**Layout:** 3–4 sentences + a shared word bank.  **Instruction:** "Fill in using the word box! 📦"
**payload/answer:** `{"sentence":"We breathe in ___.","bank":["oxygen","water","sand"]}` · answer `"oxygen"`
**App:** tap/drag · **Print:** write · **Validate:** exact

#### G06 · Sort into Groups
**type** `sort_groups` · EVS/GK · band 1–5 · **fits** classification (living/non-living, wild/domestic)
**Child does:** sorts items into named groups.
**Layout:** scatter of items + labelled bins.  **Instruction:** "Sort them into the right group! 🗂️"
**payload/answer:** `{"items":["Dog","Chair","Tree"],"bins":["Living","Non-living"]}` · answer = item→bin map
**App:** drag-to-bin · **Print:** write column · **Validate:** set

#### G07 · Sequencing / Life-Cycle Order
**type** `order_steps` · EVS/GK · band 2–5 · **fits** processes, life cycles, daily routine
**Child does:** numbers pictures into the correct order.
**Layout:** 3–4 shuffled picture cards + number slots.  **Instruction:** "Put them in the right order! 🔢"
**payload/answer:** `{"steps":["egg","caterpillar","cocoon","butterfly"]}` · answer = ordered list
**App:** drag-reorder · **Print:** number the boxes · **Validate:** ordered

#### G08 · Good Habit / Choose Right (values)
**type** `choose_good` · EVS/Values · band 1–4 · **fits** manners, safety, hygiene
**Child does:** picks the correct/kind/safe action.
**Layout:** a tiny scenario + 2–3 picture options.  **Instruction:** "What is the right thing to do? 💛"
**payload/answer:** `{"scenario":"Before eating, you should…","options":["wash hands","watch TV"]}` · answer `"wash hands"`
**App:** tap · **Print:** circle · **Validate:** exact

---

### 3D · Hindi (extension — band 1–4)

Same grammar, Devanagari content. Generate fresh; calibrate on DIKSHA Hindi + NCERT **Rimjhim**.

- **H01 · Akshar Tracing** — `type trace_letter` (Devanagari varnamala क ख ग …), cue picture.
- **H02 · Matra Fill** — `type fill_letter` on मात्रा (क + ी = की), pictured word.
- **H03 · Chitra–Shabd Match** — `type match_word_picture` (picture ↔ Hindi word).
- **H04 · Vachan / Ling** — `type cloze` (singular↔plural, gender) from a word bank.

---

## 4. Age-band coverage map (which archetypes per class)

| Band | Maths | English | EVS/GK |
|---|---|---|---|
| **Class 1–2** (trace, count, match, phonics) | M01 M02 M03 M04 M05 M06 M07 M08(pic) M09 M10 | E01 E02 E03 E04 E05 E08 | G01 G02 G04 G06 G08 |
| **Class 3–5** (compute, comprehend, classify) | M04 M05 M06 M08(col) M09 M10 M11 M12 M13 | E03 E04 E06 E07 E09 | G01 G02 G03 G04 G05 G06 G07 |

Rule: an archetype is offered for a node only if the **curriculum taxonomy** (Layer-1 index) says that
node belongs to that class — the grammar never invents scope, it only chooses the *format*.

---

## 5. The delivery layer (where "how we deliver" lives)

Each `type` needs two renderers, built once:

- **Interactive (app)** — extends the current kids quiz UI + voice quiz. Input widgets by family:
  *trace-canvas* (M01/E01/H01), *number-pad* (M02/M04/M08…), *drag-connect* (match family), *drag-to-bin*
  (sort family), *drag-reorder* (ordering family), *tap-option* (compare/choose/odd-one-out),
  *colour-palette* (M07). Voice narration on every item (edge-tts child voice, already in `voice_quiz.html`).
- **Printable (PDF)** — the "worksheet in the school bag" artefact for parents. Same JSON → a print
  template per archetype (dotted glyphs, boxes, draw-a-line columns). This is the trust-builder.

Same content JSON drives both — author the item once, render twice.

---

## 6. Build order (next steps)

1. **Freeze this grammar** as the source of truth for kids item types (this file).
2. **Extend the item schema** in `gen_content.py` beyond `mcq` → emit the archetypes above (start with the
   Maths ones that reuse existing computed values: M04, M06, M08, M09, M11).
3. **Build the render widgets** — one per input family (§5), interactive first (the app is live), print next.
4. **RAG generators** for E/G archetypes grounded on NCERT Marigold / EVS chapter text.
5. **Calibrate tone** from ~100–150 open sheets (DIKSHA + NCERT Exemplar + son's school + one parent-group
   ask) — fills wording/edge-cases, does not expand the archetype list.
6. **Wire to taxonomy** — node → eligible archetypes (§4) → LLM content → render → into the `ICSE Class N`
   pool (Gurukul qbank, WAL live-read, no api restart).

---

*Grammar first, content generated, delivered like real school. ~30 archetypes ≈ the whole K–5 worksheet
world. Extend the library only when a genuinely new format appears — otherwise just add curriculum nodes.*
