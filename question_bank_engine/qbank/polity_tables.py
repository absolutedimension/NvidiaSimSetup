"""Constitution articles and amendments as TABLES — the shape the statement forms actually need.

Why these and not NCERT prose. The statement forms make a false claim by pairing a key with a
different value from the same table, which is only false when the table is a function with mutually
exclusive values. A narrative textbook does not yield that: 1,206 verified NCERT facts produced two
matches and zero usable tables, because "banks charge a higher interest rate on loans" has no closed
value domain to swap within. The Constitution does. Article 21A is education and nothing else;
the 73rd Amendment is Panchayati Raj and nothing else. Article-to-subject is a function by
construction, which is exactly what makes a derived-false statement safe.

These are also what the official syllabus asks for. Advt 02/23(A) names भारत का संविधान एवं राज्य
व्यवस्था, पंचायती राज and पंचवर्षीय योजना — none of which our capitals-and-dances tables touch.

HAND-WRITTEN, like staticgk_hi and for the same reason: a wrong article number is not a bad
question, it is a confidently wrong one, and it is invisible from the English side. These are the
articles and amendments that recur in Bihar commission papers, held to the ones whose subject is
unambiguous — Article 19 covers six freedoms, so it is stated as "freedoms" rather than picking
one and inviting a dispute. Anything contested was left out rather than guessed.

VERIFIED 2026-08-20 against the official Constitution PDF from the Government of India CDN
(cdnbbsr.s3waas.gov.in, 848,000 characters of extracted text): all 19 article subjects confirmed,
with the article number sitting immediately before its marginal heading in the official text.

One wording note kept deliberately. Article 356's official heading is "Provisions in case of
failure of constitutional machinery in States"; we say "President's Rule in a State", which is the
name every candidate and every commission paper uses. Accurate in substance, colloquial in form —
recorded here so nobody later mistakes it for a transcription error.

Verify before extending: read the bare Act text, not a coaching summary. The PDF is at
cdnbbsr.s3waas.gov.in (legislative.gov.in itself serves only a landing page).
"""

# Article -> the single subject it deals with. One subject per article, no subject repeated.
ARTICLE_SUBJECT = {
    "14": "equality before the law",
    "19": "the six fundamental freedoms",
    "21": "protection of life and personal liberty",
    "21A": "free and compulsory education for children aged 6 to 14",
    "24": "prohibition of employment of children in factories",
    "32": "the right to constitutional remedies",
    "40": "organisation of village panchayats",
    "44": "a uniform civil code for citizens",
    "51A": "the fundamental duties of citizens",
    "72": "the pardoning power of the President",
    "110": "the definition of a Money Bill",
    "112": "the annual financial statement, or Union Budget",
    "148": "the Comptroller and Auditor General of India",
    "155": "the appointment of the Governor of a State",
    "280": "the Finance Commission",
    "324": "the Election Commission of India",
    "352": "the proclamation of a National Emergency",
    "356": "President's Rule in a State",
    "368": "the power of Parliament to amend the Constitution",
    # Added 2026-08-20 from the parsed official ToC (CONSTITUTION_ARTICLES.json), not from recall.
    # Wording is the Constitution's own marginal heading, lightly trimmed where the extraction
    # left artefacts — 124 came through as "ofthe Supreme Court" and 226 with a stray bracket, so
    # anything needing repair was read against the text rather than patched blind. Articles whose
    # heading is uninformative on its own ("243. Definitions") were left out: a question needs a
    # subject a candidate can reason about.
    "15": "prohibition of discrimination on grounds of religion, race, caste, sex or place of birth",
    "16": "equality of opportunity in matters of public employment",
    "17": "the abolition of untouchability",
    "18": "the abolition of titles",
    "23": "prohibition of traffic in human beings and forced labour",
    "25": "freedom of conscience and free profession, practice and propagation of religion",
    "50": "separation of the judiciary from the executive",
    "108": "a joint sitting of both Houses in certain cases",
    "124": "the establishment and constitution of the Supreme Court",
    "315": "Public Service Commissions for the Union and for the States",
    "343": "the official language of the Union",
    "360": "provisions as to a financial emergency",
}

# Amendment -> what it did. Distinct subjects, so a swap is always genuinely false.
#
# VERIFIED 2026-08-20 against the official Constitution text, each by the effect it left behind:
# the Preamble's "SOVEREIGN SOCIALIST SECULAR" and "unity and integrity" (42nd); the omission
# footnote on the right to property (44th); the Tenth Schedule on defection (52nd); Article 326
# reading "not less than 2[eighteen years]", where footnote 2 is "(Sixty-first Amendment) Act,
# 1988, s. 2, for 'twenty-one years'" (61st); Part IX THE PANCHAYATS (73rd); THE MUNICIPALITIES
# (74th); Article 21A Right to education (86th); goods and services tax (101st).
AMENDMENT_DID = {
    "42nd": "added the words Socialist, Secular and Integrity to the Preamble",
    "44th": "removed the right to property from the Fundamental Rights",
    "52nd": "added the Tenth Schedule on defection",
    "61st": "lowered the voting age from 21 to 18",
    "73rd": "gave constitutional status to Panchayati Raj institutions",
    "74th": "gave constitutional status to urban local bodies",
    "86th": "made education a fundamental right for children aged 6 to 14",
    "101st": "introduced the Goods and Services Tax",
}

# Amendment -> the year in the ACT'S OWN NAME, which is what an exam asks for.
#
# The 61st was wrong here: written as 1989, which is when it came into FORCE. The Constitution's
# own footnote settles it — "(Sixty-first Amendment) Act, 1988, s. 2, for 'twenty-one years'
# (w.e.f. 28-3-1989)". The Act is 1988; 28 March 1989 is commencement. Both dates are real and
# they are a year apart, which is exactly the trap this table would otherwise have set: a student
# answering 1988 from the bare Act — which this open-book exam lets them carry — would have been
# marked wrong by us.
#
# Verified 2026-08-20 against the official Constitution PDF: all eight years match the Act names in
# its amendment footnotes.
AMENDMENT_YEAR = {
    "42nd": "1976", "44th": "1978", "52nd": "1985", "61st": "1988",
    "73rd": "1992", "74th": "1992", "86th": "2002", "101st": "2016",
}

# Hindi for the keys and values these tables use, hand-written on the same all-or-nothing terms
# as staticgk_hi: a question goes bilingual only when every part of it is present here.
HI = {
    "समानता": "समानता",
}
