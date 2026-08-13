# Current Affairs — manual-entry pipeline

Current Affairs is **time-sensitive → it cannot be generated** (unlike Reasoning/Quant/GK/English,
which are deterministic). So it comes from a **human filling a spreadsheet**, which this pipeline
loads into the live bank as REAL, dated questions that serve directly to students.

This is the ONLY subject in the SRB set that needs an ongoing human process. Do it **monthly**.

## The 3-step monthly workflow

**1. FILL** — copy `TEMPLATE_current_affairs.csv`, name it by month (e.g. `aug2026.csv`), and type
the month's current-affairs MCQs. Columns:

| column | what to put |
|---|---|
| `question` | the full question |
| `option_a`..`option_d` | the four options (text only, no "(A)") |
| `correct` | `A` / `B` / `C` / `D` |
| `exam` | `Current Affairs` (keep constant — it's shared across all govt exams) |
| `subject` | `Current Affairs` (keep constant) |
| `topic` | Sports / Economy / Polity / International / Awards / Science & Tech / Defence / … |
| `month` | `YYYY-MM` (e.g. `2026-08`) — used for freshness |

Anyone can fill it from a monthly CA magazine/PDF (reword into your own MCQ = copyright-clean).
50–100 questions a month is plenty. Google Sheets → File → Download → CSV.

**2. IMPORT** — on the live bank box (Gurukul), from `~/question_bank_engine`:
```bash
scp the filled CSV to ~/question_bank_engine/current_affairs/aug2026.csv     # (or edit there)
.venv/bin/python current_affairs/import_current_affairs.py --csv current_affairs/aug2026.csv          # dry-run: validates
cp data/qbank.sqlite backups/qbank.sqlite.pre_ca_$(date +%F)                                          # back up first
.venv/bin/python current_affairs/import_current_affairs.py --csv current_affairs/aug2026.csv --apply  # writes
sudo systemctl restart qbank-api
```
The importer is **idempotent** (re-importing the same CSV makes no duplicates) and validates every
row (correct∈A–D, all 4 options present). Stores as `generated=0, verified=1` (real, human-authored).

**3. VERIFY**:
```bash
curl -s "https://gurukul.trigunai.com/examgen/pool?exam=Current+Affairs&subject=Current+Affairs&count=5"
```

## How it serves
- Exam `Current Affairs`, subject `Current Affairs` is wired into the LMS SSC CGL goal
  (`examgen.RAG_SUBJECTS current-affairs`) → students pick "Current Affairs" and get these Qs.
- `storage.py` serving gate treats `Current Affairs` like the other real banks (BPSC/UPSC): serves
  `generated=0`, and skips the chapter + difficulty filters (CA is tagged by month, difficulty 2).
- `chapter` = the month, `concept` = the topic — so newer months accumulate and stay identifiable.

## Reusable for ANY manual entry
The same importer loads hand-typed MCQs for any exam/subject (e.g. deepening GK or English, or a gap
we can't generate) — just set the `exam`/`subject` columns accordingly. It's the general
manual-entry tool, not only for CA.

## Notes / next
- **Aging:** old CA stays in the bank (still valid practice). To prefer the latest, a future tweak
  can weight `/pool` by recent `month`; for now all served questions are correct, just spanning months.
- 4 seed examples (G20 2023, WC 2023, Olympics 2024, Chandrayaan-3) are already loaded as a starter +
  format demo — replace/extend with each month's real content.
