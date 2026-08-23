# reasoning-gym audit vs `qbank/reasoninggen.py` — run 2026-08-22

Method: installed `reasoning-gym` (Apache-2.0) in a clean venv, enumerated the live registry,
**generated real samples from every candidate task** and compared them against our builders'
actual output format — not against their names.

## Headline

| | |
|---|---|
| reasoning-gym tasks in registry | **106** |
| Our item builders | **20**, across **16 chapters** (not 62 — that count included helpers) |
| Our builders that should be **deleted** as duplicated | **0** |
| RG tasks directly usable as BSSC exam items | **0** |
| RG tasks worth adopting as **new** chapters (after adding an MCQ layer) | **4** |
| RG tasks useful as **differential-test oracles** for builders we keep | **3** |

**The structural finding that decides everything else:**

```
TASKS EXPOSING MCQ OPTIONS: NONE — all free-response
ENTRY KEYS: ['question', 'answer', 'metadata']
```

**0 of 106 reasoning-gym tasks emit answer options.** reasoning-gym is built for RL with
verifiable rewards — a policy emits a string, a scorer grades it. An exam item is
stem + key + **3 modelled distractors** + Hindi. Our `mistakes()` / `mistake_distance()` /
`order_mistakes()` layer — which encodes *the specific error a student makes* — has no
counterpart anywhere in reasoning-gym.

So the earlier estimate ("~8 of 14 families already open-source and solver-verified") was
**wrong**. It was name-matching. Generating the samples changed the answer.

## Chapter-by-chapter

| # | Our chapter | Builders | Closest RG task | Verdict |
|---|---|---|---|---|
| 1 | Coding-Decoding | `_b_coding_shift`, `_b_coding_number` | `caesar_cipher` | ❌ **False friend.** RG decrypts a sentence ("YT YMNX BTWP" → "TO THIS WORK"). Ours is the exam form: *TABLE→UBCMF, so CHAIR→?* **Keep ours.** |
| 2 | Series | `_b_letter_series`, `_b_alnum_series` | `number_sequence` | ⚠️ **Complement — and it exposes a gap.** RG does pure number series (`-8, -4, 4, 20, ?` → 52). We do letter and alphanumeric series but **have no pure number-series builder**. |
| 3 | Analogy | `_b_number_analogy`, `_b_letter_analogy` | — | ✅ Ours only. RG has nothing. |
| 4 | Classification (Odd One Out) | `_b_odd_square`, `_b_odd_prime` | — | ✅ Ours only. |
| 5 | Ranking & Ordering | `_b_ranking`, `_b_ranking_pos` | `number_sorting` | ❌ **False friend.** RG sorts a list. Ours is *"A is 7th from top, 11th from bottom, how many students?"* **Keep ours.** |
| 6 | Direction Sense | `_b_direction_distance`, `_b_direction_final` | — | ✅ Ours only. |
| 7 | Blood Relations | `_b_blood_relation` | `family_relationships` | ⚠️ **Partial.** RG narrates a tree then asks one word ("grandfather"). Ours is the *"pointing to a photograph"* form, bilingual, with mistake-modelled distractors. **Keep ours; use RG as an oracle.** |
| 8 | Syllogism | `_b_syllogism` | `syllogism` | ⚠️ **Ours is stronger.** RG asks one conclusion, Yes/No. Ours does the exam form — two conclusions, 4 options — over a real model checker (`_syl_sat`, `_syl_follows`). **Keep ours; use RG as an oracle.** |
| 9 | Seating Arrangement | `_b_seating` | `zebra_puzzles` | ⚠️ **Strongest genuine overlap.** RG generalises to 4 attribute categories (name × animal × flower × colour); ours is names-only. That multi-attribute form is a **harder variant we don't generate.** |
| 10 | Coded Inequality | `_b_coded_inequality` | — | ✅ Ours only. Banking staple, RG has nothing. |
| 11 | Calendar | `_b_calendar` | `calendar_arithmetic` | ⚠️ **True overlap.** RG is good and correct. Ours is bilingual (`_DAYS_HI`, `_MONTHS_HI`). **Keep ours; use RG as an oracle.** |
| 12 | Dice | `_b_dice` | `dice` | ❌ **False friend.** RG's `dice` is *probability of dice sums* ("odds of rolling 21+" → 781/960). Ours is the spatial which-face-is-opposite type. Name collision only. |
| 13 | Symbol Substitution | `_b_symbol_substitution` | — | ✅ Ours only. |
| 14 | Word Formation | `_b_word_formation` | `word_ladder`, `group_anagrams` | ✅ Adjacent but not the exam type. Ours only. |
| 15 | Number Grid | `_b_number_grid`, `_b_number_grid_powers` | `survo`, `kakurasu`, `modulo_grid` | ✅ Those are standalone puzzles, not *find the missing number in the 3×3 grid*. Ours only. |
| 16 | — | — | `color_cube_rotation` | 🆕 **Adopt.** Genuine spatial cube rotation — the real analogue of the Indian Dice/Cube chapter, which our `_b_dice` only partly covers. |
| 17 | — | — | `knights_knaves` | 🆕 **Adopt.** Truth-teller/liar. A legitimate SSC/banking type we do not generate at all. |

## The correction I owe on uniqueness

The research memo said solution uniqueness was *"likely our largest silent quality risk."*
**That was wrong.** Reading `_b_seating` (line 1543): it already requires
`len(_seat_solutions(clues, names, n, circular)) == 1` before accepting an item, **and** then
trims any clue the remaining clues already imply, with the comment *"a redundant clue makes the
question look harder while giving the answer away twice."* The uniqueness gate exists and is
stricter than I assumed. `_syl_sat` does the same job for syllogism.

## What reasoning-gym is actually worth to us

1. **As a differential-test oracle (highest value, ~1 day).** RG's `syllogism`,
   `calendar_arithmetic` and `family_relationships` are independent implementations of logic we
   also implement. Generate matched cases, run both engines, and any disagreement is a bug in one
   of them. That is a real correctness check on `_syl_follows` and `_weekday` that we cannot get
   from our own tests, which share our own assumptions.
2. **4 new chapters:** pure number series, multi-attribute seating (zebra form),
   `color_cube_rotation`, `knights_knaves` — each needs our MCQ + distractor + Hindi layer bolted on.
3. **The interface, still worth adopting:** `create_dataset(name, size, seed, **cfg)` +
   `score_answer(answer, entry)` + a `metadata.difficulty` field. Seeded reproducibility and a
   cascade scorer (string → numeric → symbolic) are the parts we hand-roll per builder today.

## What it is not worth

Replacing anything. Not one of the 20 builders should be deleted. The distractor layer is where
the exam value lives, and reasoning-gym does not have one.

---

# Differential-test harness — built and run 2026-08-22

`tools/difftest_reasoning.py`. Checks our engines against **independent** implementations of the
same logic (our own unit tests share our own assumptions; these do not). reasoning-gym is an
optional dependency — its suites skip cleanly, so this runs in CI unchanged.

```bash
python3 tools/difftest_reasoning.py                # all suites
python3 tools/difftest_reasoning.py --suite b      # one suite
```

| Suite | Our engine | Independent oracle | Result |
|---|---|---|---|
| A1 | `_weekday` / `_leap` / `_daynum` | stdlib `datetime` + `calendar`, **every date 1583–2400** | ✅ 298,769 checked, 0 mismatched |
| A2 | `_weekday` | reasoning-gym `calendar_arithmetic` | ✅ 201 checked, 0 mismatched |
| B | `_syl_follows` | reasoning-gym `syllogism` (`is_valid`) | ⚠️ 506/4,000 disagreed — **upstream bug, see below** |
| B2 | `_syl_follows` | brute-force enumeration of every model, all 3-term forms | ✅ **13,824 checked, 0 mismatched** |
| C1 | `_KIN` | concrete genealogy graph with parent-slot unification | ✅ 40 checked, 0 mismatched |
| C2 | `_KIN_HI` (route-aware) | same graph, tracking the linking relative's sex | ✅ 32 checked, 0 mismatched |
| C3 | `_INV` | involution property | ✅ 14 checked, 0 mismatched |

**Our engines are clean.** The century rule in `_daynum` is exact across 818 years. `_KIN_HI`'s
route distinctions all hold — पोता (son's son) vs नाती (daughter's son), चाचा vs मामा, भतीजी vs भांजी.

## The bug the harness found is in reasoning-gym, not in us

Suite B disagreed on 506 of 4,000 items. Suite B2 settles who is right: `_syl_follows` agrees with
brute-force model enumeration on **all 13,824 three-term forms**, so our engine is correct and
**reasoning-gym's `syllogism` generator mislabels 18.1% of its `type=syllogism` items.**

Breakdown — the error is exactly two quantifier forms, both textbook fallacies of the
**undistributed middle**:

| Form reasoning-gym marks valid | Count | Reality |
|---|---|---|
| `All X are Y` ; `Some Y are Z` ⊢ `Some X are Z` | 266 | **Invalid** |
| `All X are Y` ; `Some Y are not Z` ⊢ `Some X are not Z` | 240 | **Invalid** |

Countermodel for the first, produced by the harness:

```
occupied regions = ['XY', 'YZ']
→ every X is a Y; the Ys that are Z are not X. Conclusion fails.
```

Concretely: *All elephants are teachers. Some teachers are animals.* It does **not** follow that
some elephants are animals — the teachers who are animals need not be the elephants.

reasoning-gym's `type=inversion` items (simple E/I conversion) are **100% correct**, 1,198/1,198.
The defect is confined to the syllogism generator's validity labelling.

The harness segregates these two forms in `_RG_KNOWN_BAD` so a known upstream defect does not
redden our build, while **any new divergence still fails it**. Full run is green, exit 0.

## Two things worth acting on

1. **Do not adopt reasoning-gym's syllogism task, and do not use it as a training or grading
   signal.** Because it ships as RLVR reward data, anything trained on it is being *rewarded* for
   committing the undistributed middle. Our `_b_syllogism` should stay exactly as it is.
2. **Worth reporting upstream** (Apache-2.0, NeurIPS 2025 spotlight). The countermodel above is a
   complete bug report on its own.
