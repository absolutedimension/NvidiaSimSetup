import sqlite3, sys
sys.path.insert(0, ".")
from qbank.models import references_figure
apply = "--apply" in sys.argv
c = sqlite3.connect("data/qbank.sqlite"); c.execute("PRAGMA busy_timeout=30000")
# ADDITIVE only: turn needs_figure ON where the text references a figure and no image is
# attached. Never turns a flag off. Covers the whole real bank (all exams), since a
# figure-less "as shown in figure" question is incomplete regardless of source.
rows = c.execute("""SELECT id, stem, COALESCE(needs_figure,0), COALESCE(figure_url,'')
   FROM questions WHERE generated=0 AND duplicate_of IS NULL""").fetchall()
to_flag = [qid for qid, stem, nf, furl in rows
           if not nf and not furl and references_figure(stem)]
print("real questions scanned:", len(rows))
print("newly flagged needs_figure (fig-referenced, no image):", len(to_flag))
if apply:
    c.executemany("UPDATE questions SET needs_figure=1 WHERE id=?", [(q,) for q in to_flag])
    c.commit()
    print("APPLIED")
