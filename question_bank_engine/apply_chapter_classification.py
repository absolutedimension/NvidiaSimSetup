"""Apply the agent chapter classification to the mixed buckets.
 - classified  -> set that chapter
 - UNCLEAR     -> the question isn't really this subject (it's the Part-I General Studies section
                  that every TRE paper carries, inherited the paper's dimension label). Move it to
                  the combined "General Studies" subject and re-tag with the GS_GENERAL keywords.
"""
import json, sqlite3, sys
sys.path.insert(0, ".")
from qbank import syllabus
from tag_gs_questions import classify

res = json.load(open("/tmp/cls_all.json"))
con = sqlite3.connect("data/qbank.sqlite"); con.row_factory = sqlite3.Row
gs_tax = syllabus.get_taxonomy("BPSC TRE", "General Studies")
set_ch = moved = 0
for qid, ch in res.items():
    row = con.execute("SELECT exam, subject, stem FROM questions WHERE id=?", (qid,)).fetchone()
    if not row:
        continue
    if ch and ch != "UNCLEAR":
        con.execute("UPDATE questions SET chapter=? WHERE id=?", (ch, qid)); set_ch += 1
    else:
        newch, _ = classify(row["stem"], gs_tax)
        con.execute("UPDATE questions SET subject='General Studies', chapter=? WHERE id=?",
                    (newch or "General Studies (mixed)", qid)); moved += 1
con.commit()
print(f"chapters set: {set_ch} | re-subjected to General Studies: {moved}")
print("\n=== TRE subject depth after cleanup ===")
for s in ["GS Polity","GS History","GS Geography","GS Economics","General Studies"]:
    n = con.execute("SELECT COUNT(*) FROM questions WHERE exam='BPSC TRE' AND subject=? AND verified=1 AND duplicate_of IS NULL",(s,)).fetchone()[0]
    mixed = con.execute("SELECT COUNT(*) FROM questions WHERE exam='BPSC TRE' AND subject=? AND verified=1 AND chapter LIKE '%(mixed)%'",(s,)).fetchone()[0]
    print(f"   {s:18s} {n:5d}   still-mixed: {mixed}")
