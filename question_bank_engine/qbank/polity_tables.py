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
}

# Amendment -> what it did. Distinct subjects, so a swap is always genuinely false.
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

# Amendment -> year of enactment.
AMENDMENT_YEAR = {
    "42nd": "1976", "44th": "1978", "52nd": "1985", "61st": "1989",
    "73rd": "1992", "74th": "1992", "86th": "2002", "101st": "2016",
}

# Hindi for the keys and values these tables use, hand-written on the same all-or-nothing terms
# as staticgk_hi: a question goes bilingual only when every part of it is present here.
HI = {
    "समानता": "समानता",
}
