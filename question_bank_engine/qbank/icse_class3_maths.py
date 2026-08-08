"""ICSE Class 3 Mathematics taxonomy — grounded on *New Guided Mathematics Class 3*
(Children's Academy, Thane West), the pupil's actual textbook.

Chapters here are the kid-facing tiles the picker/chat offers for Grade-3 Maths; they
are keyed to the EXACT `chapter` strings used by the generated pool so `/chapters` reports
real exemplar counts and `/pool` serves them. The off-book topics from the earlier generic
baseline (Roman Numerals, Ordinal Numbers) are intentionally omitted so the app mirrors his
book. `concepts` map to the book's subtopics; `keywords` drive keyword-tagging of any real
questions later ingested. Registered in syllabus.TAXONOMIES under ("ICSE Class 3","Mathematics").
"""

ICSE_CLASS3_MATHS = {
    # ---- Chapter 1: Numbers (book Ch1) ----
    "Numbers & Place Value": {
        "keywords": ["place value", "face value", "expanded form", "number name",
                     "successor", "predecessor", "ten thousand", "thousands", "greatest",
                     "smallest", "digit"],
        "concepts": {
            "Place Value & Face Value": ["place value", "face value", "digit in the"],
            "Expanded Form": ["expanded form", "thousands +", "ten thousand"],
            "Number Names": ["number name", "in words", "write the number"],
            "Successor & Predecessor": ["successor", "predecessor", "comes after", "comes before"],
            "Forming Numbers": ["greatest", "smallest", "using the digits"],
        },
    },
    "Comparing Numbers": {
        "keywords": ["greater", "smaller", "compare", "ascending", "descending",
                     "biggest", "smallest", "order", "greatest"],
        "concepts": {
            "Greater / Smaller / Equal": ["greater", "smaller", "compare", "fill in the sign"],
            "Ascending & Descending Order": ["ascending", "descending", "arrange", "order"],
        },
    },
    "Skip Counting": {
        "keywords": ["skip count", "count ahead", "count in", "count by", "in 10s",
                     "in 100s", "in 1000s"],
        "concepts": {
            "Count in 10s / 100s / 1000s": ["count in", "count ahead", "skip count"],
        },
    },
    "Number Patterns": {
        "keywords": ["pattern", "next number", "next in the pattern", "series", "sequence"],
        "concepts": {
            "Growing Patterns": ["pattern", "next number", "what comes next"],
        },
    },
    # ---- Chapter 2: Addition (book Ch2) ----
    "Addition": {
        "keywords": ["add", "sum", "plus", "total", "altogether", "carry over",
                     "estimate the sum", "adding money"],
        "concepts": {
            "3-digit Addition": ["+", "add", "carry over", "sum of"],
            "Adding Three Numbers": ["+ ", "three numbers"],
            "Estimating Sums": ["estimate the sum", "rounding to the nearest"],
            "Adding Money": ["₹", "rupees", "adding money"],
            "Word Problems": ["altogether", "in all", "how many", "total"],
        },
    },
    # ---- Later book chapters already carrying a generic Grade-3 pool (kept working;
    #      refine to his exact book when those scans arrive). ----
    "Subtraction": {
        "keywords": ["subtract", "minus", "take away", "difference", "borrow", "left",
                     "estimate the difference", "add and subtract"],
        "concepts": {
            "3-digit Subtraction": ["subtract", "minus", "take away", "borrow"],
            "Estimating Differences": ["estimate the difference", "taking the tens"],
            "Add & Subtract Together": ["+", "−", "add and subtract"],
            "Subtracting Money": ["₹", "rupees"],
            "Word Problems": ["how many left", "how much more", "remaining", "still"],
        },
    },
    "Multiplication": {
        "keywords": ["multiply", "times", "product", "table of", "×"],
        "concepts": {
            "Multiplication Tables": ["table of", "times", "×"],
            "Multiplying Numbers": ["multiply", "product"],
        },
    },
    "Multiplication Word Problems": {
        "keywords": ["each", "groups of", "rows of", "boxes of", "altogether", "in all"],
        "concepts": {
            "Word Problems": ["each has", "groups of", "in all", "altogether"],
        },
    },
    "Division": {
        "keywords": ["divide", "shared", "equal groups", "quotient", "remainder", "÷"],
        "concepts": {
            "Division Facts": ["divide", "÷", "quotient"],
            "Sharing Equally": ["shared", "equal groups", "each group"],
        },
    },
    "Fractions": {
        "keywords": ["fraction", "half", "one-third", "one-quarter", "equal parts", "part of"],
        "concepts": {
            "Halves, Thirds, Quarters": ["half", "one-third", "one-quarter", "equal parts"],
            "Fraction of a Collection": ["fraction of", "part of"],
        },
    },
    "Money": {
        "keywords": ["rupees", "paise", "₹", "cost", "price", "buy", "spend", "change"],
        "concepts": {
            "Rupees & Paise": ["rupees", "paise", "₹"],
            "Money Word Problems": ["cost", "spend", "buy", "change"],
        },
    },
    "Measurement - Length": {
        "keywords": ["length", "metre", "centimetre", "cm", "m", "long", "tall", "distance"],
        "concepts": {
            "Metres & Centimetres": ["metre", "centimetre", "cm", "convert"],
            "Length Word Problems": ["long", "tall", "distance"],
        },
    },
    "Measurement - Weight": {
        "keywords": ["weight", "mass", "kilogram", "gram", "kg", "g", "heavy", "light"],
        "concepts": {
            "Kilograms & Grams": ["kilogram", "gram", "kg", "convert"],
            "Weight Word Problems": ["heavy", "light", "weighs"],
        },
    },
    "Time": {
        "keywords": ["time", "clock", "hour", "minute", "o'clock", "half past",
                     "quarter", "a.m.", "p.m.", "calendar", "days", "months"],
        "concepts": {
            "Reading the Clock": ["clock", "o'clock", "half past", "quarter"],
            "Calendar, Days & Months": ["calendar", "days", "months", "a.m.", "p.m."],
        },
    },
    "Shapes & Geometry": {
        "keywords": ["shape", "sides", "corners", "circle", "triangle", "square",
                     "rectangle", "solid", "flat", "line"],
        "concepts": {
            "Flat Shapes": ["circle", "triangle", "square", "rectangle", "sides", "corners"],
            "Solid Shapes": ["cube", "cuboid", "sphere", "cone", "cylinder"],
        },
    },
    "Data Handling": {
        "keywords": ["pictograph", "tally", "chart", "data", "how many", "table"],
        "concepts": {
            "Pictographs & Tally Marks": ["pictograph", "tally", "chart", "data"],
        },
    },
}
