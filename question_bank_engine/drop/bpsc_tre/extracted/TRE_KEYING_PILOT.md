# TRE answer-keying pilot — cross-source published-answer method (2026-08-14)

**Goal:** test whether BPSC TRE questions (which we hold legally from the official paper but have NO
official key for, since `bpsc.bih.nic.in` is down) can be reliably **keyed by sourcing published
answers** — especially the GK/GS category that an LLM can't safely *guess*.

**Sample:** 12 GK/current-affairs/Bihar-GK/science questions from TRE 1.0 Class 9-10 (Social Science +
General Studies), keyed via web search across independent published sources.

## Result: 9/12 confidently keyed, 3/12 correctly held (none served wrong)

| # | Q (abridged) | Keyed answer | Confidence | Source signal |
|---|---|---|---|---|
| Q23 | First floating solar plant — Bihar district | **A) Darbhanga** | HIGH | multi-source + **exact Q solved on Testbook** |
| Q22 | Chief Guest 74th Republic Day | **B) El-Sisi** | HIGH | multi-source + **exact Q on careers360** |
| Q17 | NGT established (year) | **A) 2010** | HIGH | Wikipedia/greentribunal.gov.in |
| Q21 | Booker 2022 "Tomb of Sand" | **A) Geetanjali Shree & Daisy Rockwell** | HIGH | Booker Prizes/PRH |
| Q24 | Bihar GI tag | **A) Maghai Paan** | HIGH | **exact Q on Testbook + Prepp** |
| Q27 | Likhapani glacier — state | **A) Arunachal Pradesh** | HIGH | **exact Q on Testbook + Sarthaks** |
| Q20 | U-17 girls wrestling silver | **B) Nirjala** | HIGH | Bihar news + **exact Q on Testbook** |
| Q11 | Gas forcing fruit ripening | **B) Ethylene** | HIGH | FSSAI + multi-source |
| Q9 | Photoelectric device for digital | **C) Photo-diode** | HIGH | **exact Q on Testbook** |
| Q18 | First under-water metro | **HELD** | — | correct answer (Kolkata) NOT in extracted options → likely "Water Metro"=Kochi variant OR a dropped option → extraction QA needed |
| Q19 | G20 Tourism Working Group meeting | **HELD** | — | multiple TWG meetings exist; stem too generic; Srinagar (B) plausible but needs official key |
| Q26 | Brahmaputra tributary not from north | **HELD (resolvable)** | — | exact answer IS on Testbook's solved page; generic search didn't resolve |

## Findings
1. **GK is keyable by SOURCING, not guessing.** The category I'd flagged as "unsafe for a model" keys
   cleanly when the model's job is *find + cross-verify the published answer* instead of recalling it.
2. **The exact BPSC TRE questions are already solved & published** on Testbook / Prepp / Sarthaks /
   careers360 — **per-question**, which sidesteps BOTH the dead government host AND the booklet-series
   matching problem (position-based official keys need series; per-question solved PYQs don't).
3. **Built-in safety valve.** The 3 holds were *flagged, never mis-served*. Two exposed an **extraction
   QA gap** (Q18's options don't contain the correct answer → an option was likely mis-/under-extracted).
   That is the real lesson: **run an extraction-QA pass before keying at scale** (the correctness of the
   key depends on the option text being right).
4. **Legitimacy:** we use the single correct-answer **letter** (a fact), cross-checked across ≥2 sources;
   we do NOT copy any site's explanation text; the questions themselves are ours from the official paper.

## Recommended scale-up
- **Spine = official key mirror** where obtainable (ForumIAS-style NB PDF); **fill/cross-check = exact-Q
  coaching solved-PYQ pages** (Testbook et al.) requiring ≥2-source agreement; **disagree/ambiguous → hold.**
- **Precede keying with an extraction-QA pass** (option completeness + math re-extract) so the key anchors
  to correct option text.
- Prefer the **FINAL** (post-objection) key; some questions were dropped/revised.
- Same pipeline unblocks the parallel session's stuck 66/67/68/69 Prelims papers.
