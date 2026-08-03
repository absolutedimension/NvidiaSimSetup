# Kids Curriculum Skeleton (K/Class 1–5) — authentic, source-traced

Machine-readable taxonomy: **board → class → subject → chapter → subtopic**, every branch
traced to an OFFICIAL public syllabus (NCERT for CBSE, CISCE for ICSE, SCERT for Bihar).
Content (questions/worksheets) is generated later; the *skeleton is the authentic anchor*.
See `../CURRICULUM_AUTHENTIC_HANDOFF.md` for the method + acceptance criteria.

## Files
- `<board>_class<N>_<subject>.json` — one cell. Schema:
  `{board, class, subject, source:{name,url,verified_on,also_verified?}, confidence, status, live_questions?, chapters:[{id,name,subtopics:[...]}]}`
- `index.json` — master coverage matrix (auto-generated).
- `build_index.py` — regenerate the index: `python3 build_index.py` (run after any cell change).

## Rules
- Topic lists are FACT (not copyrightable) — safe to structure; never copy a private publisher's book.
- Every cell records its official source URL + `verified_on`. Mark `confidence` honestly
  (high = pulled from the official page; medium = reputable secondary; low = unverified baseline).
- Do NOT clobber a `status:"complete"` cell built from a real book (e.g. ICSE Class-3 Maths).
