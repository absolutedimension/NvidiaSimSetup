#!/usr/bin/env python3
"""One-page tick-sheet for One Step's owner. TICK ONLY — no writing anywhere.

Why this exists. The owner has given three rounds of feedback, all of it correct and all of it in
six words: "ye basic ka bhi basic hai", "very basic questions and only one topic", "GS me question
ek type ke jo ja rahe hai". Every round we have guessed what he meant, rebuilt, and guessed again.
Our own difficulty tag has now disagreed with him twice, so the tag is not the instrument. He is.

The design rules, which matter more than the questions:
  - EVERY answer is a tick. No line asks him to write a sentence. He is a busy man on WhatsApp.
  - Hindi first, English under it — the way his own papers read.
  - It asks how HE makes a paper today, not whether he likes ours. What we need is his method, not
    a rating.
  - Twelve questions. A twenty-question form comes back blank, and a blank form is worse than no form
    because it also costs the relationship.
  - He can tick on paper and send a photo, or reply on WhatsApp with just the letters.

Build:  python3 build_owner_questionnaire.py --logo onestep_logo.png --out OneStep_Questionnaire.pdf
"""
import argparse
import base64
import os
import pathlib
import subprocess

Q = [
    ("यह प्रश्न-पत्र आप किस काम में लेंगे?",
     "What will you use this paper for?",
     ["साप्ताहिक टेस्ट (हर हफ़्ते) / Weekly test",
      "पूरा मॉक टेस्ट (परीक्षा जैसा) / Full mock test",
      "अध्याय-वार टेस्ट (एक चैप्टर का) / Chapter-wise test",
      "घर के लिए अभ्यास / Home practice"], False),

    ("अभी आप अपना प्रश्न-पत्र कैसे बनाते हैं?",
     "How do you make your question papers today?",
     ["किताब से चुनकर / Picked from a book",
      "पिछले वर्षों के प्रश्न-पत्रों से / From previous-year papers",
      "शिक्षक स्वयं बनाते हैं / Teachers write them",
      "किसी और सॉफ़्टवेयर से / From other software"], False),

    ("हमारे प्रश्न-पत्र का स्तर कैसा लगा?",
     "The level of our paper is —",
     ["बहुत आसान / Too easy",
      "थोड़ा आसान / A little easy",
      "बिल्कुल सही / Just right",
      "बहुत कठिन / Too hard"], False),

    # NOT "what instructions do you want?". The owner's "complete instructions dena hoga" was him
    # assuming we prompt an LLM and telling us to write a better prompt — he is diagnosing our
    # METHOD, not asking for a rubric. Asking him to specify instructions would have confirmed a
    # wrong picture of how the paper is built. What is actually worth learning is what would make
    # him TRUST an answer key he did not compile himself, which is the real thing behind it.
    ("इस प्रश्न-पत्र पर भरोसा करने के लिए आपको क्या चाहिए?",
     "What would make you trust this paper's answer key?",
     ["हर प्रश्न का हल दिया हो / A worked solution for every question",
      "उत्तर कहाँ से आया, वह लिखा हो / The source of each answer shown",
      "किसी शिक्षक ने जाँचा हो / Checked by a subject teacher",
      "पिछले वर्षों के असली प्रश्न हों / Real previous-year questions only"], False),

    ("एक प्रश्न-पत्र में कितने प्रश्न और कितना समय रखते हैं?",
     "How many questions and how much time do you set?",
     ["150 प्रश्न · 2 घं 15 मि (BSSC जैसा) / 150 Q · 2h 15m",
      "100 प्रश्न · 1 घं 30 मि / 100 Q · 1h 30m",
      "50 प्रश्न · 45 मिनट / 50 Q · 45 min",
      "25–30 प्रश्न · 20 मिनट / 25–30 Q · 20 min"], False),

    ("गणित (भाग-II) में सबसे बड़ी समस्या क्या है?",
     "The main problem in the Maths section is —",
     ["एक ही तरह के प्रश्न बार-बार / The same type repeated again and again",
      "हिंदी में प्रश्न साफ़ नहीं है / The Hindi wording is not clear",
      "प्रश्न सिलेबस से बाहर हैं / Questions are outside the syllabus",
      "उत्तर या विकल्प गलत हैं / An answer or option is wrong"], False),

    ("सामान्य अध्ययन (भाग-I) में सबसे बड़ी समस्या क्या है?",
     "The main problem in the General Studies section is —",
     ["एक ही तरह से पूछा गया है / Asked the same way every time",
      "विषय कम हैं, बार-बार वही / Too few topics, same ones repeat",
      "प्रश्न बहुत लंबे हैं / The questions are too long",
      "सीधे-सरल प्रश्न चाहिए / We want simple one-line questions"], False),

    ("GS में कौन-से विषय ज़रूर होने चाहिए? (कितने भी चुनें)",
     "Which GS topics MUST be there? (tick as many as you like)",
     ["इतिहास / History", "स्वतंत्रता आंदोलन / Freedom movement",
      "बिहार विशेष / Bihar special", "भूगोल / Geography",
      "संविधान–राजव्यवस्था / Polity", "अर्थव्यवस्था / Economy",
      "करेंट अफेयर्स / Current affairs", "खेल–पुरस्कार / Sports & awards"], True),

    ("गणित में कौन-से अध्याय ज़रूर होने चाहिए? (कितने भी चुनें)",
     "Which Maths chapters MUST be there? (tick as many as you like)",
     ["प्रतिशत / Percentage", "अनुपात–समानुपात / Ratio",
      "औसत / Average", "लाभ–हानि / Profit & loss",
      "ब्याज / Interest", "संख्या पद्धति / Number system",
      "समय–कार्य / Time & work", "चाल–दूरी / Speed & distance"], True),

    ("प्रश्न पूछने का तरीका आप कैसा चाहते हैं?",
     "How should the questions be asked?",
     ["सीधा एक-लाइन का प्रश्न / Simple one-line questions",
      "कथन पढ़कर सही चुनना / Statement-based",
      "मिलान (Match) वाले / Match-the-pairs",
      "सब मिलाकर / A mixture of all"], False),

    ("प्रश्न-पत्र के साथ और क्या चाहिए? (कितने भी चुनें)",
     "What else should come with the paper? (tick as many as you like)",
     ["उत्तर कुंजी / Answer key", "हल सहित (solution) / Worked solutions",
      "OMR शीट / OMR sheet", "कठिनाई स्तर लिखा हो / Difficulty marked",
      "अलग हिंदी और अंग्रेज़ी प्रति / Separate Hindi & English copies"], True),

    ("यदि यह सब ठीक हो जाए, तो आप —",
     "If all of this is fixed, would you —",
     ["अभी बच्चों को दे देंगे / Give it to students right away",
      "पहले एक बैच में आज़माएँगे / Try it with one batch first",
      "और बदलाव चाहिए / Still want more changes"], False),
]


# ── MODE: method ────────────────────────────────────────────────────────────────
# A different instrument from the feedback sheet, and a better one.
#
# The owner is himself a teacher who sets papers. Asking him to critique OUR paper puts him in the
# customer's chair and gets six words back. Asking him HOW HE WOULD SET THIS PAPER puts him in the
# chair he actually occupies, where he has twenty years of method to describe — and every answer
# maps onto a knob this generator already has:
#
#   Q1  -> what the blueprint should be built from        Q7  -> the failure modes to gate on
#   Q2  -> how per-topic quotas are decided               Q8  -> real PYQ vs generated ratio
#   Q3  -> the easy/medium/hard mix                       Q9  -> where an answer key comes from
#   Q4  -> ORDERING, which we do not do at all today      Q10 -> who reviews before it ships
#   Q5  -> distractor policy (we use named mistakes)      Q11 -> the hours we would save him
#   Q6  -> his definition of a good question              Q12 -> the per-topic cap (ours is 4)
#
# It also sidesteps the thing that derailed the last round. He believes we prompt an LLM; a form
# that asks about HIS craft never raises the question, and his answers give us the specification
# either way.
METHOD_Q = [
    # ── A. What "difficult" actually MEANS to him ────────────────────────────────
    # The whole line has stalled twice on this. He said "basic ka bhi basic" and later "very basic",
    # while our own tag said 32 of 50 questions were difficulty 4. The tag is not wrong about step
    # count — it is measuring the wrong thing. These five questions ask him to define the word,
    # per section, in terms we can actually set a dial to.
    ("When you call a question DIFFICULT, which of these do you mean?", "",
     ["The student simply does not know the fact",
      "The student knows it but must think through steps",
      "The options are close, so a careless student gets it wrong",
      "It takes too long to finish in the time given"], False),

    ("In GENERAL STUDIES, what makes a question hard? (pick the MAIN one)", "",
     ["A less-known / rarer fact",
      "Several statements to judge in one question (3–4)",
      "All four options look correct",
      "Two different topics combined in one question"], False),

    ("In MATHS, what makes a question hard? (pick the MAIN one)", "",
     ["More steps in the solution",
      "Awkward numbers — fractions, decimals, large values",
      "Options very close to each other",
      "Two chapters combined in one question"], False),

    ("In REASONING, what makes a question hard? (pick the MAIN one)", "",
     ["More conditions to hold in the head at once",
      "A longer chain — more links to follow",
      "Asked in reverse (given the answer, find the start)",
      "A question type the student has not seen before"], False),

    ("Out of 100 students, how many SHOULD get a hard question right?", "",
     ["Fewer than 20", "20–40", "40–60", "More than 60"], False),

    # ── B. Control over the level ────────────────────────────────────────────────
    ("In a 150-question paper, how many should be genuinely hard?", "",
     ["About 20", "About 40", "About 70", "More than 100"], False),

    ("What average score should a well-prepared student get on your paper?", "",
     ["Below 40%", "40–55%", "55–70%", "Above 70%"], False),

    ("Should the hard questions be —", "",
     ["Spread evenly through the paper", "Kept at the end of each section",
      "Grouped in one hard section", "Easy first, then steadily harder"], False),

    # ── C. Uniqueness across batches ─────────────────────────────────────────────
    ("If you make 4 papers for 4 batches, they should be —", "",
     ["Completely different questions",
      "Same pattern, only numbers/names changed",
      "About half common, half new",
      "The same paper is fine"], False),

    ("At most how many questions from ONE topic in a 50-question section?", "",
     ["2", "3–4", "5–6", "No limit"], False),

    # ── D. The setter's own method ───────────────────────────────────────────────
    ("How do you write the WRONG options?", "",
     ["The mistakes students actually make",
      "Numbers close to the correct answer",
      "Taken from the book",
      "Anything that looks different"], False),

    ("What is the FIRST thing you check in a finished paper?", "",
     ["That no answer in the key is wrong",
      "That nothing is outside the syllabus",
      "That the level is right",
      "That it can be finished in the time"], False),

    ("Which section decides whether the whole paper is good?", "",
     ["General Studies", "Maths & Science", "Reasoning", "All equally"], False),

    ("How long does it take you to make one full paper today?", "",
     ["Under an hour", "2–3 hours", "Half a day", "More than a day"], False),
]

MODES = {"feedback": Q, "method": METHOD_Q}


CSS = """
@page { size: A4; margin: 12mm 12mm 10mm; }
body { font-family: 'Noto Sans Devanagari','Nirmala UI','Inter',sans-serif; color:#1a1c24;
       font-size: 9.1pt; line-height: 1.32; }
.head { display:flex; align-items:center; gap:12px; border-bottom:2px solid #c9a227;
        padding-bottom:7px; margin-bottom:9px; }
.head img { height:44px; }
.co { font-weight:800; font-size:13pt; letter-spacing:.4px; }
.sub { color:#6b6f7c; font-size:8.4pt; }
.intro { background:#fdfaf0; border:1px solid #c9a227; border-radius:5px; padding:7px 10px;
         font-size:8.6pt; margin-bottom:9px; }
.q { margin:0 0 7px; page-break-inside:avoid; }
.qt { font-weight:700; }
.qe { color:#5a5f6e; font-size:8.2pt; margin-bottom:2px; }
.opts { display:flex; flex-wrap:wrap; gap:2px 10px; margin-left:4px; }
.op { display:flex; align-items:flex-start; gap:5px; width:47%; font-size:8.6pt; }
.box { display:inline-block; width:10px; height:10px; border:1.4px solid #8a6d1a;
       border-radius:2px; flex:none; margin-top:2px; }
.n { color:#8a6d1a; font-weight:800; margin-right:4px; }
.foot { border-top:1px solid #ddd8c8; margin-top:8px; padding-top:5px; font-size:7.8pt;
        color:#6b6f7c; }
"""


def build(logo, out, mode="feedback"):
    logo_html = ""
    if logo and os.path.exists(logo):
        b64 = base64.b64encode(open(logo, "rb").read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}">'
    qs = []
    for i, (hi, en, opts, multi) in enumerate(MODES[mode], 1):
        note = (" (tick as many as you like)" if (multi and mode == "method")
                else (" (एक से ज़्यादा चुन सकते हैं)" if multi else ""))
        rows = "".join(
            f'<div class="op"><span class="box"></span><span>{chr(96+j)}) {o}</span></div>'
            for j, o in enumerate(opts, 1))
        sub = f'<div class="qe">{en}</div>' if en else ""
        qs.append(f'<div class="q"><div class="qt"><span class="n">{i}.</span>{hi}{note}</div>'
                  f'{sub}<div class="opts">{rows}</div></div>')
    SUBTITLE = ("BSSC इंटर स्तरीय अभ्यास प्रश्न-पत्र &mdash; आपकी राय / Your feedback"
                if mode == "feedback" else
                "Setting the difficulty &mdash; how you build a paper")
    LEAD = ("" if mode == "feedback" else
            "<b>This is not about our paper.</b> You set papers yourself, so you know what makes "
            "one hard and what makes one easy. We want <b>your</b> definition of \u2018difficult\u2019 "
            "&mdash; section by section &mdash; so the system can be set to it exactly.<br>")
    html = f"""<meta charset="utf-8"><style>{CSS}</style>
<div class="head">{logo_html}<div>
  <div class="co">ONE STEP EDUCATION &middot; PATNA</div>
  <div class="sub">{SUBTITLE}</div>
</div></div>
<div class="intro">{LEAD}<b>Just tick &mdash; nothing to write.</b> 14 questions, 2 minutes.
Tick and send a photo, or reply on WhatsApp with only the letters &mdash; like
<b>1-a, 2-b, 3-c</b> &hellip;</div>
{''.join(qs)}
<div class="foot">{{FOOT}}</div>"""
    FOOT = ("आपका एक-एक जवाब सीधे अगले प्रश्न-पत्र में लागू होगा। &mdash; Acharya, TrigunAI"
            if mode == "feedback" else
            "Every answer here becomes a setting in the paper generator. "
            "&mdash; Acharya, TrigunAI Innovations Pvt Ltd")
    html = html.replace("{FOOT}", FOOT)
    out_html = pathlib.Path(str(out).replace(".pdf", ".html")).resolve()
    out_html.write_text(html, encoding="utf-8")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pathlib.Path(out).resolve()}", out_html.as_uri()],
                       capture_output=True, timeout=120)
    print(f"{len(Q)} tick-only questions -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", default="onestep_logo.png")
    ap.add_argument("--out", default="OneStep_Questionnaire.pdf")
    ap.add_argument("--mode", choices=["feedback", "method"], default="feedback",
                    help="feedback = what he thinks of our paper; "
                         "method = how HE sets a paper (the better instrument)")
    a = ap.parse_args()
    build(a.logo, a.out, a.mode)
