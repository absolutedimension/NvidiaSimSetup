/**
 * Acharya — Teacher/Institute Setup Intake Form  (Google Apps Script)
 * ------------------------------------------------------------------
 * Builds the complete onboarding form to send a teacher AFTER they say yes,
 * so we collect everything needed to stand up their branded Acharya tutor +
 * list their course on acharya.trigunai.com + enrol their students.
 *
 * HOW TO USE (one time, ~30 seconds):
 *   1. Go to  https://script.google.com  → New project.
 *   2. Delete the sample code, paste ALL of this file.
 *   3. Click  Run  (the ▶ button) → authorize when Google asks (your account).
 *   4. Open  View → Logs (or Execution log). It prints two links:
 *        • EDIT link  (you customise/brand it)
 *        • SHARE link (this is what you send the teacher on WhatsApp/email)
 *   5. Responses collect under the form's "Responses" tab → link a Google Sheet.
 *
 * Each answer maps to a field in  tenants/<slug>.json  +  the course concept-bank
 * (see the // -> comments). File-upload questions are added as "share a link /
 * send on WhatsApp" text fields, because Apps Script can't create native file-
 * upload items; add those manually in the editor if you want true uploads
 * (note: uploads force the teacher to sign in with a Google account).
 */
function createAcharyaSetupForm() {
  var form = FormApp.create('Acharya Setup — Your AI Tutor for Your Students')
    .setDescription(
      'Welcome to Acharya! Fill this once and we set up your own AI tutor — under YOUR coaching\'s ' +
      'name, on WhatsApp + web — so your students get 24×7 doubt-solving, daily practice and revision ' +
      'in your subjects. Takes ~5 minutes. Your free 14-day trial starts once we set it up. ' +
      'Any file we ask for, you can also just send us on WhatsApp.')
    .setCollectEmail(true)
    .setProgressBar(true)
    .setAllowResponseEdits(true);

  // ---------- SECTION 1 — About you & your coaching ----------
  form.addSectionHeaderItem().setTitle('1. About you & your coaching');

  form.addTextItem().setTitle('Coaching / Institute name')            // -> tenant.name / brand
    .setHelpText('Exactly as you want it to appear — your tutor will introduce itself as "<this>\'s tutor".')
    .setRequired(true);

  form.addTextItem().setTitle('Your name (main contact)').setRequired(true);   // -> tenant contact

  form.addTextItem().setTitle('Your WhatsApp number')                 // -> tenant contact / weekly report
    .setHelpText('With country code, e.g. +91 98XXXXXXXX. We send your weekly student-progress report here.')
    .setRequired(true);

  form.addTextItem().setTitle('City').setRequired(false);

  form.addTextItem().setTitle('Short name for your tutor branding (optional)')  // -> tenant.slug
    .setHelpText('A short one-word handle, e.g. "catalyzers". Leave blank and we\'ll create one.');

  // ---------- SECTION 2 — What you teach ----------
  form.addPageBreakItem().setTitle('2. What you teach')
    .setHelpText('This becomes your tutor\'s syllabus — it will teach ONLY what you teach.');

  form.addTextItem().setTitle('Subject(s) / exam you teach')          // -> tenant.subject / course.name
    .setHelpText('e.g. NEET Physics & Chemistry, JEE Maths, Class 10 Science, Foundation Science.')
    .setRequired(true);

  var classes = form.addCheckboxItem().setTitle('Which classes / levels?');   // -> curriculum scoping
  classes.setChoices([
    classes.createChoice('Class 9'), classes.createChoice('Class 10'),
    classes.createChoice('Class 11'), classes.createChoice('Class 12'),
    classes.createChoice('Droppers / repeaters'), classes.createChoice('Foundation (6–8)')
  ]).setRequired(true);

  var board = form.addCheckboxItem().setTitle('Board / target exam');
  board.setChoices([
    board.createChoice('CBSE'), board.createChoice('ICSE'), board.createChoice('State board'),
    board.createChoice('NEET'), board.createChoice('JEE'), board.createChoice('Other')
  ]);

  var lang = form.addMultipleChoiceItem().setTitle('Language your students prefer');  // -> tutor language
  lang.setChoices([
    lang.createChoice('Hindi'), lang.createChoice('English'),
    lang.createChoice('Hinglish (mix)'), lang.createChoice('Other')
  ]).showOtherOption(true).setRequired(true);

  form.addParagraphTextItem()                                          // -> course.order (concept bank)
    .setTitle('Your syllabus — chapters/topics in the ORDER you teach them')
    .setHelpText('One topic per line, top = taught first. e.g.\nUnits & Measurement\nKinematics\nLaws of Motion\n... ' +
                 'Rough is fine — we turn this into the tutor\'s lessons. Or share a link / send your syllabus PDF on WhatsApp.')
    .setRequired(true);

  form.addTextItem().setTitle('Link to your syllabus / notes (optional)')
    .setHelpText('Google Drive / any link. Or just WhatsApp us the file — either works.');

  form.addParagraphTextItem()                                          // -> course.intro / persona
    .setTitle('Anything about HOW you teach we should match? (optional)')
    .setHelpText('Your style, examples you use, tone (strict / friendly), anything that makes your teaching yours.');

  // ---------- SECTION 3 — Your students (to enrol them) ----------
  form.addPageBreakItem().setTitle('3. Your students')
    .setHelpText('We\'ll enrol these students so they can start with your tutor.');

  form.addTextItem().setTitle('Total number of students you teach')   // -> pricing tier
    .setRequired(true);

  form.addTextItem().setTitle('How many students for the FREE 14-day trial? (up to 10)')  // -> trial roster
    .setHelpText('Pick your most active 10 — that\'s the best test.')
    .setRequired(true);

  form.addParagraphTextItem()                                          // -> tenant.students[]
    .setTitle('Trial student list — one per line: Name, WhatsApp number')
    .setHelpText('e.g.\nAarav Sharma, +91 98XXXXXXXX\nPriya Verma, +91 97XXXXXXXX\n' +
                 'Or send this list on WhatsApp / upload a sheet link below.')
    .setRequired(true);

  form.addTextItem().setTitle('OR link to a student list sheet (optional)');

  var phones = form.addMultipleChoiceItem().setTitle('Do your students have WhatsApp on a smartphone?');
  phones.setChoices([
    phones.createChoice('Yes, almost all'), phones.createChoice('About half'),
    phones.createChoice('Only some')
  ]).setRequired(true);

  // ---------- SECTION 4 — Your branding (applied during the trial) ----------
  form.addPageBreakItem().setTitle('4. Your branding')
    .setHelpText('So the tutor + your web page look like YOUR coaching. Optional — we start with your name and add these as we go.');

  form.addTextItem().setTitle('Link to your logo (or send it on WhatsApp)')   // -> tenant.brand.logo
    .setHelpText('PNG preferred. We put it on your students\' web page.');

  form.addTextItem().setTitle('Your brand colours (optional)')        // -> tenant.brand.colors
    .setHelpText('Hex codes or just describe, e.g. "royal blue and gold".');

  form.addTextItem().setTitle('One-line tagline for your coaching (optional)')  // -> course detail tagline
    .setHelpText('e.g. "Kota\'s trusted NEET foundation since 2015."');

  form.addTextItem().setTitle('Do you have your own website/domain? (optional)')  // -> web.custom_domain
    .setHelpText('If yes, paste it. We can put the tutor on your domain later in the trial.');

  // ---------- SECTION 5 — Go-live & consent ----------
  form.addPageBreakItem().setTitle('5. Go-live');

  var whichNumber = form.addMultipleChoiceItem().setTitle('Which WhatsApp number should your students message?'); // -> whatsapp.mode
  whichNumber.setChoices([
    whichNumber.createChoice('Use your shared Acharya number for now (fastest — start today)'),
    whichNumber.createChoice('I want my own dedicated number (we set it up during the trial)')
  ]).setRequired(true);

  form.addTextItem().setTitle('When would you like to start?')        // -> trial.start
    .setHelpText('A date, or "as soon as possible".');

  var consent = form.addMultipleChoiceItem()
    .setTitle('Free 14-day trial, then ₹4,999/month (cancel anytime). OK to proceed?');  // -> offer consent
  consent.setChoices([
    consent.createChoice('Yes — set up my free trial'),
    consent.createChoice('I have a question first')
  ]).setRequired(true);

  form.addParagraphTextItem().setTitle('Anything else you\'d like your tutor to do? (optional)');

  // ---------- output the links ----------
  Logger.log('✅ Form created.');
  Logger.log('SEND THIS TO THE TEACHER (share link): ' + form.getPublishedUrl());
  Logger.log('EDIT IT YOURSELF (edit link):          ' + form.getEditUrl());
}
