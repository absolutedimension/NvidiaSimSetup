"""FORM layer — re-ask a solved item in a different SHAPE, without touching how it was solved.

Why this file exists, measured rather than assumed:

    Reasoning: 21 builders -> 19 concepts x 1 form each = 19 question types
    General Studies: 5 fact tables x 7 forms = 35 question types from 7 form functions

General Studies gets nearly twice the variety from a third of the code, and the only difference
is architectural: `staticgk_forms` keeps CONTENT (the verified tables) separate from FORM (how the
question is put), so every new form multiplies across every table. In `reasoninggen` the two are
FUSED — one builder is one concept asked exactly one way — so variety costs a whole new builder
with its own bands, its own distractors, its own Hindi and its own independent solver.

This module is the missing layer for reasoning. A form takes what a builder ALREADY produced (the
stem, the computed answer, and the named mistakes with the reason each one is wrong) and re-asks
it. Nothing here recomputes an answer, so no form can introduce an arithmetic error that the
builder did not already have.

FORMS
  as_error_spot  A student's wrong answer is shown; the question is WHICH MISTAKE produced it.
                 The options are the reasons, not the numbers.

                 This is a genuine step up the Bloom ladder rather than a reskin — "apply" becomes
                 "evaluate". A candidate cannot work backwards from the options, because the
                 options are not answers; and they cannot recognise the answer without actually
                 performing the wrong procedure and seeing that it lands on the number shown. It
                 is also the form that costs least to add and gains most, because the diagnosis is
                 something we ALREADY compute for every distractor and currently throw away.

WHAT THIS FORM'S INDEPENDENT CHECK CAN AND CANNOT DO — read before trusting it.
  `test_papers.solve_error_spot` re-solves the ORIGINAL question embedded in the stem using the
  ordinary solvers, and confirms (a) that the answer shown to the student is NOT the correct one,
  and (b) that exactly one option is the "no mistake" option and it is not the keyed one. That is
  a real check of the half that can go wrong silently.
  It does NOT independently re-derive WHICH named mistake produces the shown number — doing so
  would mean reimplementing every buggy procedure, which is the builder's own logic. That half is
  guaranteed instead by construction plus the injectivity gate below: an item is refused unless
  each named mistake lands on a DIFFERENT number, so the shown number can only have come from one
  of them. This is a weaker guarantee than the direct forms carry, and it is the honest reason
  this form is not simply applied to everything.
"""

_CORRECT_EN = "There is no mistake — the answer is correct"
_CORRECT_HI = "कोई त्रुटि नहीं — उत्तर सही है"


def can_error_spot(built) -> bool:
    """An item can be re-asked as an error-spot only if all four options are available in BOTH
    languages and the numbers they sit on are distinct.

    The distinctness is not fussiness. If two named mistakes produce the same number, the question
    "which mistake did he make?" has two correct answers and the paper cannot say which it means.
    """
    # Some items are only unambiguous because of the numbers they print as options — an analogy
    # is the standard case. A form that replaces those options cannot inherit that protection, so
    # the builder flags them and every form refuses them. Found by sabotaging a built paper, not by
    # reading the code: the item was correctly keyed and still unanswerable for a candidate who
    # read the other defensible rule.
    if built.get("ambiguous_without_options"):
        return False
    mis = [m for m in (built.get("mistakes") or []) if m.get("why_hi")]
    if len(mis) < 3 or not built.get("stem_hi"):
        return False
    vals = [m["text"] for m in mis] + [str(built["correct"])]
    if len(set(vals)) != len(vals):
        return False                      # two procedures land on one number — not answerable
    whys = [m["why"] for m in mis] + [_CORRECT_EN]
    whys_hi = [m["why_hi"] for m in mis] + [_CORRECT_HI]
    return len(set(whys)) == len(whys) and len(set(whys_hi)) == len(whys_hi)


def as_error_spot(built, rng):
    """-> a new `built` dict asking which mistake produced a shown answer, or None.

    One in four items shows the CORRECT answer and keys "there is no mistake". Without that a
    candidate learns the shown value is always wrong and never checks it — which removes exactly
    the verification step the form exists to test.
    """
    if not can_error_spot(built):
        return None
    mis = [m for m in built["mistakes"] if m.get("why_hi")][:3]
    show_correct = rng.random() < 0.25
    if show_correct:
        shown, correct_en, correct_hi = str(built["correct"]), _CORRECT_EN, _CORRECT_HI
    else:
        picked = rng.choice(mis)
        shown, correct_en, correct_hi = picked["text"], picked["why"], picked["why_hi"]
    opts_en = [m["why"] for m in mis] + [_CORRECT_EN]
    opts_hi = [m["why_hi"] for m in mis] + [_CORRECT_HI]
    # A form must not quietly re-order the option pair. hi_opts maps English text -> Hindi text and
    # _make_question applies it AFTER the shuffle, so the two halves stay in step.
    hi_map = dict(zip(opts_en, opts_hi))
    q_en = built["stem"].strip()
    q_hi = built["stem_hi"].strip()
    stem = (f"A student was asked the following question.\n{q_en}\n"
            f"The student answered: {shown}.\n"
            f"Which of the following describes what the student did?")
    stem_hi = (f"एक विद्यार्थी से निम्नलिखित प्रश्न पूछा गया।\n{q_hi}\n"
               f"विद्यार्थी ने उत्तर दिया: {shown}।\n"
               f"निम्नलिखित में से कौन-सा कथन बताता है कि विद्यार्थी ने क्या किया?")
    sol = (f"The correct answer is {built['correct']}. " +
           (f"The student's answer matches it, so nothing went wrong."
            if show_correct else
            f"The student answered {shown}, which is what you get if you {correct_en[0].lower()}"
            f"{correct_en[1:]}.") +
           " " + (built.get("solution") or ""))
    sol_hi = (f"सही उत्तर {built['correct']} है। " +
              ("विद्यार्थी का उत्तर इसी के बराबर है, अतः कोई त्रुटि नहीं हुई।"
               if show_correct else
               f"विद्यार्थी का उत्तर {shown} है, जो तब मिलता है जब — {correct_hi}।") +
              " " + (built.get("solution_hi") or ""))
    return {
        "stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
        "correct": correct_en, "options": opts_en, "hi_opts": hi_map,
        "concept": built.get("concept"), "form": "error_spot",
        # carried through so an independent solver can re-solve the embedded original and check
        # that the number shown to the student really is not the answer
        "_origin": {"stem": q_en, "answer": str(built["correct"]), "shown": shown},
    }


FORMS = {"error_spot": as_error_spot}
