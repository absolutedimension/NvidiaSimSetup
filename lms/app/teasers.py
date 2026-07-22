"""3-question teaser packs (easy → medium → hard) for the ad landing funnel.

Real, curated, correct MCQs — served INSTANTLY (no LLM) so the ad landing loads fast.
The visitor answers all 3 before the email/One-Tap gate, then continues into the full
dynamic assessment. Keyed by exam id (matches EXAMS in main.py); DEFAULT is a general set.
"""

TEASERS = {
    "neet": {"title": {"en": "NEET Biology", "hi": "NEET Biology"}, "questions": [
        {"level": "Easy", "correct": 1,
         "en": {"q": "Which organelle is the 'powerhouse of the cell'?", "opts": ["Ribosome", "Mitochondria", "Nucleus", "Golgi body"], "explain": "Mitochondria make ATP — the cell's energy."},
         "hi": {"q": "कोशिका का 'powerhouse' कौन-सा अंगक है?", "opts": ["राइबोसोम", "माइटोकॉन्ड्रिया", "केंद्रक", "गॉल्जी बॉडी"], "explain": "माइटोकॉन्ड्रिया ATP (ऊर्जा) बनाता है।"}},
        {"level": "Medium", "correct": 2,
         "en": {"q": "In DNA, Adenine (A) always pairs with —", "opts": ["Guanine", "Cytosine", "Thymine", "Uracil"], "explain": "A–T and G–C is the base-pairing rule (Uracil is RNA)."},
         "hi": {"q": "DNA में Adenine (A) हमेशा किससे जुड़ता है?", "opts": ["ग्वानिन", "साइटोसिन", "थाइमिन", "यूरैसिल"], "explain": "A–T और G–C नियम (यूरैसिल RNA में)।"}},
        {"level": "Hard", "correct": 1,
         "en": {"q": "Crossing over during meiosis occurs in —", "opts": ["Metaphase I", "Prophase I", "Anaphase II", "Telophase I"], "explain": "Crossing over happens in Prophase I (pachytene)."},
         "hi": {"q": "अर्धसूत्री विभाजन में crossing over किस अवस्था में होता है?", "opts": ["मेटाफ़ेज़ I", "प्रोफ़ेज़ I", "एनाफ़ेज़ II", "टीलोफ़ेज़ I"], "explain": "Crossing over प्रोफ़ेज़ I (pachytene) में होता है।"}},
    ]},
    "jee": {"title": {"en": "JEE Physics", "hi": "JEE Physics"}, "questions": [
        {"level": "Easy", "correct": 1,
         "en": {"q": "Newton's second law gives which formula?", "opts": ["F = m·v", "F = m·a", "F = m/a", "F = m·g"], "explain": "Force = mass × acceleration."},
         "hi": {"q": "न्यूटन का दूसरा नियम कौन-सा सूत्र देता है?", "opts": ["F = m·v", "F = m·a", "F = m/a", "F = m·g"], "explain": "बल = द्रव्यमान × त्वरण।"}},
        {"level": "Medium", "correct": 1,
         "en": {"q": "A 2 kg body accelerates at 5 m/s². The force is —", "opts": ["7 N", "10 N", "2.5 N", "20 N"], "explain": "F = m·a = 2 × 5 = 10 N."},
         "hi": {"q": "2 kg की वस्तु 5 m/s² से त्वरित है। बल कितना है?", "opts": ["7 N", "10 N", "2.5 N", "20 N"], "explain": "F = m·a = 2 × 5 = 10 N।"}},
        {"level": "Hard", "correct": 1,
         "en": {"q": "A ball is thrown up at 20 m/s. Time to reach the top? (g = 10 m/s²)", "opts": ["1 s", "2 s", "4 s", "20 s"], "explain": "t = u/g = 20/10 = 2 s."},
         "hi": {"q": "एक गेंद 20 m/s से ऊपर फेंकी गई। शीर्ष तक पहुँचने का समय? (g = 10)", "opts": ["1 s", "2 s", "4 s", "20 s"], "explain": "t = u/g = 20/10 = 2 s।"}},
    ]},
    "class10": {"title": {"en": "Class 10 · Science + Math", "hi": "Class 10 · विज्ञान + गणित"}, "questions": [
        {"level": "Easy", "correct": 1,
         "en": {"q": "The chemical formula of water is —", "opts": ["CO₂", "H₂O", "O₂", "H₂O₂"], "explain": "Two hydrogen + one oxygen = H₂O."},
         "hi": {"q": "पानी का रासायनिक सूत्र क्या है?", "opts": ["CO₂", "H₂O", "O₂", "H₂O₂"], "explain": "दो हाइड्रोजन + एक ऑक्सीजन = H₂O।"}},
        {"level": "Medium", "correct": 1,
         "en": {"q": "The pH of a neutral solution is —", "opts": ["0", "7", "14", "1"], "explain": "Neutral = 7; acid < 7, base > 7."},
         "hi": {"q": "उदासीन (neutral) विलयन का pH मान होता है —", "opts": ["0", "7", "14", "1"], "explain": "उदासीन = 7; अम्ल < 7, क्षार > 7।"}},
        {"level": "Hard", "correct": 0,
         "en": {"q": "A right triangle has legs 6 and 8. The hypotenuse is —", "opts": ["10", "12", "14", "48"], "explain": "√(6² + 8²) = √100 = 10."},
         "hi": {"q": "एक समकोण त्रिभुज की भुजाएँ 6 और 8 हैं। कर्ण = —", "opts": ["10", "12", "14", "48"], "explain": "√(6² + 8²) = √100 = 10।"}},
    ]},
    "class12": {"title": {"en": "Class 12 · Physics", "hi": "Class 12 · भौतिकी"}, "questions": [
        {"level": "Easy", "correct": 1,
         "en": {"q": "By Ohm's law, Voltage (V) equals —", "opts": ["I / R", "I × R", "I + R", "I × R²"], "explain": "V = I × R (current × resistance)."},
         "hi": {"q": "ओम के नियम से वोल्टेज (V) = —", "opts": ["I / R", "I × R", "I + R", "I × R²"], "explain": "V = I × R (धारा × प्रतिरोध)।"}},
        {"level": "Medium", "correct": 1,
         "en": {"q": "A 5 V source across 10 Ω. The current is —", "opts": ["2 A", "0.5 A", "50 A", "5 A"], "explain": "I = V/R = 5/10 = 0.5 A."},
         "hi": {"q": "10 Ω पर 5 V स्रोत। धारा कितनी है?", "opts": ["2 A", "0.5 A", "50 A", "5 A"], "explain": "I = V/R = 5/10 = 0.5 A।"}},
        {"level": "Hard", "correct": 2,
         "en": {"q": "Two 6 Ω resistors in parallel give an equivalent resistance of —", "opts": ["12 Ω", "6 Ω", "3 Ω", "36 Ω"], "explain": "Parallel: (6×6)/(6+6) = 3 Ω."},
         "hi": {"q": "दो 6 Ω प्रतिरोध समांतर (parallel) में — तुल्य प्रतिरोध =", "opts": ["12 Ω", "6 Ω", "3 Ω", "36 Ω"], "explain": "समांतर: (6×6)/(6+6) = 3 Ω।"}},
    ]},
    "default": {"title": {"en": "Quick Aptitude", "hi": "Quick Aptitude"}, "questions": [
        {"level": "Easy", "correct": 2,
         "en": {"q": "Which of these is a prime number?", "opts": ["9", "15", "7", "21"], "explain": "7 has only 1 and itself as factors."},
         "hi": {"q": "इनमें से कौन-सी अभाज्य (prime) संख्या है?", "opts": ["9", "15", "7", "21"], "explain": "7 के केवल 1 और स्वयं गुणनखंड हैं।"}},
        {"level": "Medium", "correct": 1,
         "en": {"q": "25% of 200 is —", "opts": ["25", "50", "75", "100"], "explain": "25% × 200 = 50."},
         "hi": {"q": "200 का 25% कितना है?", "opts": ["25", "50", "75", "100"], "explain": "25% × 200 = 50।"}},
        {"level": "Hard", "correct": 1,
         "en": {"q": "A train covers 60 km in 45 minutes. Its speed is —", "opts": ["75 km/h", "80 km/h", "90 km/h", "45 km/h"], "explain": "60 km ÷ 0.75 h = 80 km/h."},
         "hi": {"q": "एक ट्रेन 45 मिनट में 60 km चलती है। इसकी चाल = —", "opts": ["75 km/h", "80 km/h", "90 km/h", "45 km/h"], "explain": "60 km ÷ 0.75 घंटा = 80 km/h।"}},
    ]},
}


def teaser_for(exam_id: str) -> dict:
    return TEASERS.get(exam_id, TEASERS["default"])
