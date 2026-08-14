import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_tre import extract

BASE = os.path.join(HERE, "drop", "bpsc_tre")
OUT = os.path.join(BASE, "extracted")
os.makedirs(OUT, exist_ok=True)

# Curated high-value set: GS/GK/Science/Social/English across TRE 1/2/3.
# Rare-language + subject-specialist booklets (Botany, Music, Sanskrit, Urdu...)
# are intentionally excluded — noise for a govt-job GS bank.
CURATED = {
    # TRE 1.0 (2023) — class 9-10 GS-bearing subject booklets + pure GS Paper-2 + Language
    "TRE1.0/General_Studies_Paper_2_1st_Sitting__General_Studies_Paper_2.pdf": ("BPSC TRE", "TRE1.0", "General Studies"),
    "TRE1.0/General_Studies_Paper_2_2nd_Sitting__General_Studies_Paper_2.pdf": ("BPSC TRE", "TRE1.0", "General Studies"),
    "TRE1.0/For_Class_09_10__General_Studies_And_Science.pdf": ("BPSC TRE", "TRE1.0", "General Studies + Science"),
    "TRE1.0/For_Class_09_10__General_Studies_And_Social_Science.pdf": ("BPSC TRE", "TRE1.0", "General Studies + Social Science"),
    "TRE1.0/For_Class_09_10__General_Studies_And_Mathematics.pdf": ("BPSC TRE", "TRE1.0", "General Studies + Mathematics"),
    "TRE1.0/For_Class_09_10__General_Studies_And_English.pdf": ("BPSC TRE", "TRE1.0", "General Studies + English"),
    "TRE1.0/Language_Paper_1_1st_Sitting__Language_Paper_1.pdf": ("BPSC TRE", "TRE1.0", "Language"),
    # TRE 2.0 (2023)
    "TRE2.0/For_Class_01_05_Examination_dated_14_12_2023__Language_And_General_Studies.pdf": ("BPSC TRE", "TRE2.0", "Language + General Studies"),
    "TRE2.0/For_Class_06_08_Examination_dated_10_12_2023__Language_General_Studies_And_English.pdf": ("BPSC TRE", "TRE2.0", "GS + English"),
    # TRE 3.0 (2024) — most recent
    "TRE3.0/For_Class_09_10_Examination_dated_21_07_2024__Language_General_Studies_And_Science.pdf": ("BPSC TRE", "TRE3.0", "GS + Science"),
    "TRE3.0/For_Class_06_08_Examination_dated_19_07_2024__Language_General_Studies_And_English.pdf": ("BPSC TRE", "TRE3.0", "GS + English"),
    "TRE3.0/For_Class_01_05_Examination_dated_20_07_2024__Language_And_General_Studies.pdf": ("BPSC TRE", "TRE3.0", "Language + General Studies"),
}

staged = []
summary = []
for rel, (exam, ed, subj) in CURATED.items():
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        summary.append((rel, "MISSING", 0)); continue
    qs = extract(p)
    for q in qs:
        staged.append({
            "exam": exam, "edition": ed, "subject_group": subj,
            "source_pdf": rel, "q_no": q["q_no"],
            "stem": q["stem"], "options": q["options"],
            "answer": None,            # <-- NO official key available (bih.nic.in firewalled)
            "generated": 0, "verified": 0, "held_reason": "awaiting_official_answer_key",
        })
    summary.append((rel, "ok", len(qs)))

outfile = os.path.join(OUT, "tre_staged_questions.json")
json.dump(staged, open(outfile, "w"), ensure_ascii=False, indent=1)
print(f"{'PAPER':70s} {'STATUS':8s} {'Q':>4s}")
for rel, st, n in summary:
    print(f"{rel:70s} {st:8s} {n:4d}")
print(f"\nTOTAL staged questions: {len(staged)}  ->  {outfile}")
