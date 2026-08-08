"""Banking-exam Quantitative Aptitude taxonomy — the IBPS/SBI/RRB shared PRELIMS pattern.

Unlike JEE/NEET, banking exams have NO large pre-tagged/pre-keyed question bank on HF, and
their quant section is not an academic syllabus but a fixed set of TEMPLATABLE problem types
whose answer is COMPUTABLE in Python. So this subject is GENERATION-first: `qbank.quantgen`
draws each of these chapters deterministically (compute-the-answer, like figure-first chem),
and the taxonomy below just names the topics so `/chapters` can list them and batch-fill can
walk the cells. Keywords are kept for the (later) case where real PYQ exemplars are ingested
and tagged into these chapters.

One shared taxonomy covers IBPS PO/Clerk, SBI PO/Clerk and RRB Prelims — they share the same
Quant pattern; questions are tagged by `exam` at generation time, not by a separate taxonomy."""

BANKING_QUANT = {
    "Simplification & Approximation": {
        "keywords": ["simplify", "approximate", "value of", "bodmas", "nearest value",
                     "wrong value", "what will come in place of"],
        "concepts": {
            "Simplification (BODMAS)": ["simplify", "bodmas", "value of"],
            "Approximation": ["approximate", "nearest value"],
        },
    },
    "Number Series": {
        "keywords": ["series", "next term", "missing number", "wrong number",
                     "what comes next", "find the missing"],
        "concepts": {
            "Missing-Term Series": ["missing number", "next term"],
            "Wrong-Term Series": ["wrong number", "wrong term"],
        },
    },
    "Quadratic Equations": {
        "keywords": ["quadratic", "two equations", "relation between x and y",
                     "x and y", "compare"],
        "concepts": {
            "x vs y Comparison": ["relation between x and y", "compare"],
        },
    },
    "Data Interpretation": {
        "keywords": ["table", "chart", "following data", "study the", "pie chart",
                     "bar graph", "caselet", "data interpretation"],
        "concepts": {
            "Tabular DI": ["table", "following table"],
            "Caselet DI": ["caselet", "following information"],
        },
    },
    "Percentage": {
        "keywords": ["percent", "percentage", "%", "increased by", "decreased by"],
        "concepts": {
            "Percentage Change": ["increased by", "decreased by"],
            "Percentage of a Number": ["percent of", "% of"],
        },
    },
    "Profit, Loss & Discount": {
        "keywords": ["cost price", "selling price", "profit", "loss", "marked price",
                     "discount", "gain"],
        "concepts": {
            "Profit / Loss %": ["profit", "loss", "gain"],
            "Marked Price & Discount": ["marked price", "discount"],
        },
    },
    "Simple & Compound Interest": {
        "keywords": ["simple interest", "compound interest", "principal", "rate of interest",
                     "per annum", "amount", "compounded"],
        "concepts": {
            "Simple Interest": ["simple interest"],
            "Compound Interest": ["compound interest", "compounded"],
        },
    },
    "Ratio, Proportion & Partnership": {
        "keywords": ["ratio", "proportion", "in the ratio", "partnership", "invested",
                     "share of profit"],
        "concepts": {
            "Ratio & Proportion": ["ratio", "proportion"],
            "Partnership": ["partnership", "invested", "share of profit"],
        },
    },
    "Averages & Ages": {
        "keywords": ["average", "mean", "present age", "years old", "age of"],
        "concepts": {
            "Averages": ["average", "mean"],
            "Problems on Ages": ["present age", "age of", "years old"],
        },
    },
    "Time & Work": {
        "keywords": ["work", "days", "pipe", "cistern", "fill the tank", "alone",
                     "together", "efficiency"],
        "concepts": {
            "Time & Work": ["work", "days", "efficiency", "together"],
            "Pipes & Cisterns": ["pipe", "cistern", "fill the tank"],
        },
    },
    "Speed, Time & Distance": {
        "keywords": ["speed", "distance", "km/hr", "train", "crosses", "boat",
                     "stream", "downstream", "upstream", "km/h"],
        "concepts": {
            "Speed / Time / Distance": ["speed", "distance", "km/hr"],
            "Trains": ["train", "crosses", "platform"],
            "Boats & Streams": ["boat", "stream", "downstream", "upstream"],
        },
    },
    "Mixtures & Alligations": {
        "keywords": ["mixture", "alligation", "mixed", "milk and water", "concentration",
                     "replaced"],
        "concepts": {
            "Alligation": ["alligation", "mixed", "concentration"],
            "Replacement": ["replaced", "milk and water"],
        },
    },
    "Mensuration": {
        "keywords": ["area", "perimeter", "volume", "radius", "circle", "rectangle",
                     "cylinder", "cube", "surface area"],
        "concepts": {
            "2D Mensuration": ["area", "perimeter", "circle", "rectangle"],
            "3D Mensuration": ["volume", "cylinder", "cube", "surface area"],
        },
    },
    "Permutation, Combination & Probability": {
        "keywords": ["ways", "arrange", "selected", "probability", "balls", "committee",
                     "at random"],
        "concepts": {
            "Permutation & Combination": ["ways", "arrange", "selected", "committee"],
            "Probability": ["probability", "at random"],
        },
    },
}
