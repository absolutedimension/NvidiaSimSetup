# General Science — biology fact review sheet

Chemistry is machine-verified against PubChem (NIH) and is not listed here.
**VITAMIN_CHEMICAL_NAME is not listed here either, as of 2026-08-23.** Vitamin ->
chemical name is a set of CHEMICAL IDENTITIES, and the same NIH oracle answers
those: all 6 rows are confirmed against PubChem's synonym list for that vitamin,
matched exactly rather than by substring, and sabotage-tested (7 of 8 slips caught;
the miss is written up in `verify_vitamin_names.__doc__`). It is gated separately
on `BIO_NAMES_REVIEWED`, which is already True. **That is 6 rows you do not have
to read.** One row was NOT machine-earnable and is below with the others.

**Everything remaining is hand-written, facts and Hindi both.** Tick or correct
each row. None of it is used by the paper builder until `BIO_REVIEWED` is set to
True in `qbank/science_tables.py`.

⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:

1. `BIO_REVIEWED = True` in `qbank/science_tables.py`
2. add these to `concepts` for **Biology** in `drop/bssc/SYLLABUS_MAP.json`,
   alongside the `VITAMIN_CHEMICAL_NAME` already there:

   `["VITAMIN_DEFICIENCY", "HORMONE_GLAND", "DISEASE_PATHOGEN"]`

A topic with `concepts` counts as GENERATABLE, so listing it before the flag is
set promises questions the gate then refuses, and the section pads from elsewhere.

## VITAMIN_DEFICIENCY

- [ ] **Vitamin A** → **night blindness**   ·   हिंदी: विटामिन A → रतौंधी
      > Decreasing night blindness requires the improvement of vitamin A status in at-risk populations.
      > Vitamin A plays a major role in phototransduction, so this deficiency impairs vision, often presenting with nyctalopia (night blindness).

- [ ] **Vitamin B1** → **beriberi**   ·   हिंदी: विटामिन B1 → बेरी-बेरी
      > He called this "the anti-beriberi factor", which was later identified as vitamin B1, thiamine.
      > With no knowledge of vitamins, the etiology of beriberi was among the most hotly debated subjects in Victorian medicine.

- [ ] **Vitamin B3** → **pellagra**   ·   हिंदी: विटामिन B3 → पेलाग्रा
      > Pellagra  is a disease caused by a lack of the vitamin niacin (vitamin B3).
      > Though he identified that a missing nutritional element was responsible for pellagra, he did not discover the specific vitamin responsible.

- [ ] **Vitamin B12** → **pernicious anaemia**   ·   हिंदी: विटामिन B12 → घातक रक्ताल्पता
      > Causes are usually related to conditions that give rise to malabsorption of vitamin B12, particularly autoimmune gastritis in pernicious anemia.
      > Murphy and George Minot for discovery of an effective treatment for pernicious anemia using liver concentrate, later found to contain a large amount of vitamin B12.

- [ ] **Vitamin C** → **scurvy**   ·   हिंदी: विटामिन C → स्कर्वी
      > It was the acid, not the (then-unknown) Vitamin C that was believed to cure scurvy.
      > Rates of scurvy in the developed world are low due to the greater access to vitamin C-rich foods.

- [ ] **Vitamin D** → **rickets**   ·   हिंदी: विटामिन D → रिकेट्स
      > Vitamin D-related rickets
      > Vitamin D-resistant rickets

- [ ] **Vitamin K** → **delayed blood clotting**   ·   हिंदी: विटामिन K → रक्त का देर से जमना
      > The primary cause of congenital rickets is vitamin D deficiency in the mother's blood.
      > Vitamin A deficiency (VAD) or hypovitaminosis A is a lack of vitamin A in blood and tissues.

- [ ] **Iron** → **anaemia**   ·   हिंदी: लोहा → रक्ताल्पता
      > NPS News 70: Iron deficiency anaemia: NPS – Better choices, Better health – From the National Prescribing Service

- [ ] **Iodine** → **goitre**   ·   हिंदी: आयोडीन → घेंघा
      > Worldwide, over 90% of goitre cases are caused by iodine deficiency.
      > David Marine conducted substantial research on the treatment of goitre with iodine.

## HORMONE_GLAND

- [ ] **Insulin** → **the pancreas**   ·   हिंदी: इंसुलिन → अग्न्याशय
      > By December, they had also succeeded in extracting insulin from the adult cow pancreas.
      > Type 1 diabetes – autoimmune-mediated destruction of insulin-producing β-cells in the pancreas, resulting in absolute insulin deficiency

- [ ] **Thyroxine** → **the thyroid gland**   ·   हिंदी: थायरॉक्सिन → थायरॉइड ग्रंथि
      > T4, thyroxine (3,5,3′,5′-tetraiodothyronine), is produced by follicular cells of the thyroid gland.
      > Thyroid hormones are two hormones produced and released by the thyroid gland: triiodothyronine (T3) and thyroxine (T4).

- [ ] **Adrenaline** → **the adrenal gland**   ·   हिंदी: एड्रिनेलिन → अधिवृक्क ग्रंथि
      > Adrenaline is normally produced by the adrenal glands and by a small number of neurons in the medulla oblongata.
      > The adrenal glands produce a variety of hormones including adrenaline and the steroids aldosterone  cortisol and Dehydroepiandrosterone sulfate (DHEA).

- [ ] **Growth hormone** → **the pituitary gland**   ·   हिंदी: वृद्धि हार्मोन → पीयूष ग्रंथि
      > Prior to its production by recombinant DNA technology, growth hormone used to treat deficiencies was extracted from the pituitary glands of cadavers.
      > The intermediate lobe of the pituitary gland secretes only one enzyme that is melanocyte stimulating hormone.

- [ ] **Parathormone** → **the parathyroid gland**   ·   हिंदी: पैराथॉर्मोन → पैराथायरॉइड ग्रंथि
      > Parathyroid hormone (PTH), also known as parathormone or parathyrin, is a peptide hormone secreted by the parathyroid glands.
      > == Parathyroid glands ==

## DISEASE_PATHOGEN

- [ ] **Malaria** → **a protozoan (Plasmodium)**   ·   हिंदी: मलेरिया → एक प्रोटोजोआ (प्लाज्मोडियम)
      > In humans, malaria is caused by six Plasmodium species: P.
      > Severe malaria occurs when the Plasmodium infection causes damage to vital organs such as the kidney, liver, lungs or brain.

- [ ] **Tuberculosis** → **a bacterium (Mycobacterium tuberculosis)**   ·   हिंदी: क्षय रोग → एक जीवाणु (माइकोबैक्टीरियम ट्यूबरकुलोसिस)
      > The species Mycobacterium tuberculosis, though, is rarely present in wild animals.
      > The principal microbial cause of TB is Mycobacterium tuberculosis (MTB), a small, aerobic, non-motile and rod-shaped bacillus.

- [ ] **Dengue** → **a virus spread by the Aedes mosquito**   ·   हिंदी: डेंगू → एडीज मच्छर से फैलने वाले एक विषाणु
      > Dengue is spread by several species of female mosquitoes of the Aedes genus, principally Aedes aegypti.
      > Dengue virus is most frequently transmitted by the bite of mosquitos in the Aedes genus, particularly A.

- [ ] **Cholera** → **a bacterium (Vibrio cholerae)**   ·   हिंदी: हैजा → एक जीवाणु (विब्रियो कॉलेरी)
      > Cholera () is an infection of the small intestine by some strains of the bacterium Vibrio cholerae.
      > Cholera – Vibrio cholerae infection – Centers for Disease Control and Prevention

- [ ] **Ringworm** → **a fungus**   ·   हिंदी: दाद → एक कवक
      > Misdiagnosis and treatment of ringworm with a topical steroid, a standard treatment of the superficially similar pityriasis rosea, can result in tinea incognito, a condition where ringworm fungus grows without typical features, such as a distinctive raised bor

- [ ] **Kala-azar** → **a protozoan spread by the sandfly**   ·   हिंदी: कालाजार → बालू-मक्खी से फैलने वाले एक प्रोटोजोआ
      > Visceral Leishmaniasis/kala-azar samples from India revealed the presence of not only the primary causative protozoan parasite, i.e., Leishmania donovani (LD), but also co-infection with another protozoan member called Leptomonas seymouri (LS).
      > In the words of Jill Seaman, the doctor who led relief efforts in the Upper Nile for the French organization Médecins Sans Frontières, "Where else in the world could 50% of a population die without anyone knowing?" Due to the South Sudanese Civil War, kala-aza

## VITAMIN_CHEMICAL_NAME (the one row PubChem could not settle)

PubChem's `Calciferol` record IS ergocalciferol — vitamin **D2** — while
"vitamin D" names a group that also contains D3 (cholecalciferol). The row
is what Class-10 texts teach and what the commission would ask, but that is
a teacher's call, not an oracle's.

- [ ] **Vitamin D** → **calciferol**   ·   हिंदी: विटामिन D → कैल्सिफेरॉल
      > Vitamin D3 (cholecalciferol) is the preferred form since it is more readily absorbed than vitamin D2.
      > Vitamin D2 (ergocalciferol) is produced in a similar way using ergosterol from yeast as a starting material.
