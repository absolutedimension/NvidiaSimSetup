# Kids Quiz Video Engine — ICSE Grade 3 (Children's Academy, Thane West)

---

## ✅ AUTHENTIC BOOK CURRICULUM (supersedes the web-baseline below) — Maths

**Book (confirmed from his actual scans, 2026-08-01):** *New Guided Mathematics — Class 3.*
The book's real spine is **10 chapters** (not the 11-chapter web baseline; **no Roman-numerals
and no Ordinal-numbers chapter** in this book):

1. **Numbers** — numbers up to **5 digits (Ten-Thousands / TTh)**, numbers on an abacus, place
   value & face value, number comparison (successor/predecessor, `> < =`), number arrangement
   (ascending/descending), building numbers (greatest/smallest from digits), expanded form, number names.
2. **Addition** — addition of **3-digit** numbers (with & without carrying), adding **more than two**
   3-digit numbers, estimating sums (round to nearest 10), currency & **adding money (₹)**, word problems.
3. Subtraction · 4. Multiplication · 5. Division · 6. Geometry · 7. Patterns · 8. Measurement ·
   9. Time · 10. Data Handling.  ← *Ch 3–10 pending his next book scans.*

### Live pool status (qbank `ICSE Class 3` / `Mathematics`)
- **Ch 1 & Ch 2 DONE (2026-08-01):** generated **228** book-faithful, compute-correct MCQs
  (generated=1, verified=1, difficulty 1–2) via **`kids_quiz/gen_qbank_g3.py`** and upserted into the
  live Gurukul `qbank.sqlite` (backup taken; WAL live-read, **no api restart**). Pool: **540 → 768**.
  Mapped onto the existing live tiles (non-destructive): `Numbers & Place Value` (114), `Comparing
  Numbers` (54), `Skip Counting` (42), `Number Patterns` (42), `Addition` (126). Verified serving via
  `/pool`.
- **Chapter-tile cleanup (pending Deepak's call):** the pre-book baseline still shows two tiles his
  book does NOT have — **Roman Numerals** and **Ordinal Numbers** (30 each). Leave, or fold/retire when
  mirroring the book's 10-chapter spine. Non-urgent; decide during the taxonomy pass.
- To regenerate/extend: `cd question_bank_engine && python3 gen_qbank_g3.py --dry|--commit --per N`
  (script lives at `kids_quiz/gen_qbank_g3.py`, scp'd to the VM repo root).

---


> **Goal.** Interactive, cartoon, story/treasure-hunt YouTube quiz videos for my son (ICSE Grade 3).
> He already loves solving quizzes on screen — the more he plays, the more the *correct answer*
> gets reinforced in his mind. We reuse our existing **RAG question engine + quiz-video renderer +
> YouTube uploader**; the only new work is (a) a Grade-3 kids question bank grounded on his real
> books, and (b) a **kid-themed** video look (mascot, story, softer voice, pictures, celebration).
>
> **Board confirmed:** Children's Academy Thane West = **ICSE, Nursery–Grade 5.** Exact textbooks not
> published online → we ground the RAG on **scans of his actual books** for chapter-exact fidelity.

---

## Part 1 — Authentic ICSE Grade 3 curriculum map (topic → subtopic)

This is the standard ICSE Class 3 scope (CISCE framework). It is the **baseline taxonomy**; the
*exact* chapter names/order come from his school books once we scan them. Subjects best suited to
quiz videos are marked ⭐.

### ⭐ Mathematics (~11 chapters)
1. **Numbers up to 9999** — reading & writing numbers, place value & face value, expanded form, comparing & ordering, successor/predecessor, forming smallest/largest numbers, **Roman numerals I–XX**
2. **Addition** — up to 4 digits, with & without carrying, properties (order, adding zero), estimation, word problems
3. **Subtraction** — up to 4 digits, with & without borrowing, checking by addition, word problems
4. **Multiplication** — tables 2–12, multiply 2–3 digit × 1 digit, multiply by 10/100, properties, word problems
5. **Division** — meaning, division as repeated subtraction, division facts, divide by 1 digit, remainder, word problems
6. **Fractions** — half / one-third / one-quarter, equal parts, like fractions, fraction of a collection
7. **Money** — rupees & paise, converting ₹↔paise, add/subtract money, making bills, amounts
8. **Measurement** — length (m, cm), weight (kg, g), capacity (l, ml), conversions, comparison
9. **Time** — clock (hour / half / quarter / minutes), a.m./p.m., calendar, days & months, duration
10. **Geometry & Shapes** — plane shapes (circle, triangle, square, rectangle), solid shapes (cube, cuboid, sphere, cone, cylinder), sides & corners, straight/curved lines, patterns
11. **Data Handling** — pictographs, tally marks, reading & making simple charts

### ⭐ EVS / General Science
- **Living & Non-living things** — features of living things
- **Plants** — parts of a plant, types (trees/shrubs/herbs/creepers/climbers), uses of plants, seeds & how plants grow
- **Animals** — wild / domestic / pets, habitats, food habits (herbivore/carnivore/omnivore), how they move, animal babies, birds & insects
- **The Human Body** — body parts, the 5 sense organs, teeth, bones & muscles (basic), staying healthy
- **Food & Nutrition** — food from plants & animals, balanced diet, healthy vs junk food
- **Health & Hygiene** — cleanliness, good habits, safety, basic first aid
- **Air & Water** — sources & uses of water, saving water, air around us
- **Weather & Seasons** — types of weather, Indian seasons, clothes for each season
- **Our Environment** — surroundings, cleanliness, plants & trees around us, pollution (basic)
- **Shelter** — types of houses & materials

### ⭐ Social Studies / "Our World" (EVS social side)
- **Our Family** — nuclear vs joint family, relationships, family tree
- **Community Helpers** — doctor, teacher, farmer, police, postman, etc.
- **Our Country India** — national symbols (flag, emblem, anthem, animal, bird, flower, game), festivals
- **Maps & Directions** — the four directions (N/S/E/W), simple maps, globe
- **The Earth & Solar System** — sun, moon, stars, planets, day & night
- **Means of Transport** — land / water / air, then vs now
- **Means of Communication** — letters, phone, internet, mass media
- **Continents & Oceans** — basic introduction
- **Festivals of India** — national & religious

### ⭐ English
- **Grammar** — nouns (common/proper/collective, gender, singular↔plural), pronouns, articles (a/an/the), adjectives, verbs, tenses (simple present/past/future, present continuous), adverbs, prepositions, conjunctions, punctuation & capitals, question words
- **Vocabulary** — synonyms, antonyms (opposites), rhyming words, one-word substitution, spellings
- **Comprehension** — passages, stories, poems (recall questions)
- **Writing** — sentence making, picture composition, paragraph, informal letter, story (not quiz-friendly; skip for video)

### ⭐ General Knowledge (GK) — *the easiest to make fun*
- **India** — national symbols, states & capitals (basic), monuments, leaders
- **World** — continents, famous countries & places, wonders
- **Nature & Science** — animals, plants, human-body facts, space
- **Sports, festivals, inventions, famous personalities, abbreviations**

### Hindi (हिंदी)
- वर्णमाला (स्वर/व्यंजन), मात्राएँ, शब्द रचना
- संज्ञा, सर्वनाम, विशेषण, क्रिया, लिंग, वचन, विलोम शब्द, पर्यायवाची, गिनती, वाक्य रचना
- अपठित गद्यांश (comprehension), vocabulary

### Computer Studies
- What is a computer & its uses; parts (CPU, monitor, keyboard, mouse)
- Input vs output devices; types of computers
- Keyboard keys & mouse operations; desktop, icons, starting/shutting down
- Intro to MS Paint / drawing; good computer habits

> **Quiz-friendliness ranking** (start here): **Maths → GK → EVS/Science → Social Studies → English grammar → Computers → Hindi.**
> Maths & GK give the cleanest, most objective MCQs and the fastest "did I get it right?!" feedback loop a 8-yr-old loves.

---

## Part 2 — What we already have (reuse, don't rebuild)

| Asset | Where | Reuse for kids |
|---|---|---|
| **RAG question engine** | `question_bank_engine/` (`qbank/` = collector→tagger→generator, novelty gate, taxonomy files like `syllabus.py`) | New **Grade-3 taxonomy** + **kids exemplar bank grounded on book scans**; same generate→validate→novelty loop → age-appropriate MCQs |
| **Quiz-video renderer** | `quiz_video/make_quiz_video.py` (vertical 1080×1920, countdown→reveal→celebration→CTA, EN+HI, PIL+edge-tts+ffmpeg, CPU-only ~7–10 min/render) | **Fork into a kids theme:** mascot host, story frame, bright palette, softer voice, picture options, slower timer, sound effects |
| **YouTube uploader** | `youtube_series/yt_upload.py` + manifests | New **kids channel or playlist**, own token; child-safe titles/description, "Made for Kids" flag |
| **Vision PDF/image extraction** | `question_bank_engine` image path (Qwen2.5-VL on EC2) + the `exact-question-making-pipeline-from-pdf` skill | Turn **book-page scans** → grounded context chunks / exemplars for the RAG |

**The moat is the same as the exam engine: the DATA.** Here the data = a clean, chapter-tagged
Grade-3 question bank grounded on his real books. Copyright-clean posture holds: we don't republish
the book — we *generate fresh* questions grounded in the concepts, novelty-gated.

---

## Part 3 — What's new for a KIDS audience (the design deltas)

The exam engine is austere (JEE/NEET, timers, pressure). A Grade-3 audience flips almost every choice:

| Dimension | Exam engine (now) | Kids engine (new) |
|---|---|---|
| **Framing** | Bare question card | **Story / adventure wrapper** — a treasure hunt, each correct answer unlocks the next step |
| **Host** | None | **Recurring cartoon mascot** who asks, reacts, cheers |
| **Palette** | Dark/cream, exam-serious | Bright, playful, high-contrast primary colors |
| **Voice** | Neurja/Prabhat (news-reader) | Warm, playful, slower; expressive SSML; lots of "Wooo! You got it!" |
| **Answer options** | Text A/B/C/D | **Pictures + emoji** wherever possible (esp. Maths objects, animals, shapes) |
| **Timer** | 5 s, tense | **8–12 s**, friendly countdown with a fun sound, no scary music |
| **Wrong answer** | Just reveal | **Never shaming** — "Ooh, close! The answer is… let's remember it together!" then the correct answer is repeated & celebrated (this is the *learning-reinforcement* the brief wants) |
| **Set size** | Many | **5 questions per adventure** (attention span) |
| **SFX** | Minimal | ding (correct), gentle "aww" (wrong), tada/celebration, whoosh transitions, drumroll |
| **Ending** | CTA to exam-prep | Celebration + "come back for the next adventure!" (no sales CTA — this is for him, not marketing) |

### Flagship recurring format (proposal)
**"Treasure Trackers"** — a mascot (e.g., **Bittu the Explorer Fox** 🦊 + a friendly parrot sidekick)
follows a treasure map. Each video = **one topic = one island/mountain**. Five questions = five steps;
each correct answer reveals a piece of the map / a gem; the 5th unlocks the treasure + a celebration.
Recurring characters + a collectible arc = the "excited to solve" hook. Series examples:
- *Multiplication Mountain* (tables), *Fraction Falls*, *Shape Island*, *Money Market*
- *Animal Kingdom Safari* (EVS), *Space Rocket GK*, *Grammar Garden* (English)

---

## Part 4 — Build plan (phased, small first)

### Phase 0 — Scope + grounding (this week)
- Pick **pilot subject** (recommend **Maths**) and **2–3 chapters** he's currently on.
- **You scan** those chapters of his actual school book (phone photos are fine) → I run them through
  the vision extractor to build the grounded context. (If we can't get the book, we proceed on the
  ICSE baseline above and tune later.)
- Lock the mascot + series name + look (1 mood-board frame).

### Phase 1 — Kids question bank (RAG)
- Author `qbank/kids_g3_maths.py` taxonomy (chapters→concepts, Grade-3 difficulty band = **1–2**).
- Build exemplar set grounded on the scans; run the generator → **age-appropriate MCQs with picture
  hints**; **you review** a batch of ~30 (accuracy + reading level) before any render.

### Phase 2 — Kids video theme (fork the renderer)
- Copy `make_quiz_video.py` → `kids_quiz/make_kids_quiz_video.py`; add: mascot frames + reactions,
  story intro/outro, bright theme, picture-option layout, SFX bed, slower timer, playful voice (SSML).
- Render **1 pilot adventure** end-to-end (5 Qs). Watch it *with him*.

### Phase 3 — Iterate on HIS reaction
- The real test is his face. Tune pacing, difficulty, character, celebration based on what excites him.

### Phase 4 — Scale + schedule
- Expand to GK + EVS; batch-produce; optional daily/weekly cron (reuse the content-engine cron pattern).
- Organize as **playlists per subject** on a dedicated **kids YouTube channel** (Made-for-Kids compliant).

---

## Part 5 — Open decisions (need your call)
1. **Pilot subject** — recommend **Maths** (cleanest MCQs, fastest feedback). GK is the funniest alt.
2. **Grounding** — will you **scan his current book chapters** (chapter-exact), or start on the ICSE
   baseline and refine later?
3. **Channel** — new **dedicated kids channel** (recommended; keeps Made-for-Kids + algorithm separate
   from TrigunAI's exam content) vs a playlist on an existing channel.
4. **Language** — English first, or **English + Hindi** dual (engine already supports HI)?

---

## Appendix — Sources (ICSE Class 3 baseline)
- [EuroSchool — ICSE Syllabus Class 3](https://www.euroschoolindia.com/icse-syllabus/class-3/)
- [BYJU'S — ICSE Class 3 Maths Syllabus](https://byjus.com/icse-class-3-maths-syllabus/)
- [Children's Academy — Thane West Ghodbunder Campus](https://www.childrens-academy.in/thane-west-ghodbunder-campus/) (board = ICSE, Nursery–Grade 5)
- Exact chapter names/order to be confirmed from the school's prescribed textbooks (scans).
