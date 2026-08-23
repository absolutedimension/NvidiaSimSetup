/* worksheet.js — KIDS WORKSHEET component (non-MCQ archetypes from WORKSHEET_GRAMMAR.md).
 *
 * Companion to kids_voice.js (which handles the MCQ pool test). This one RENDERS the worksheet
 * item types the pool engine doesn't — trace, count-write, match, sort, order, fill, compare,
 * true/false, colour-by-number, and open WRITE answers (keyboard + voice input).
 *
 * Self-contained + framework-free (matches the vanilla-JS house style). Exposes one global:
 *
 *     KidsWorksheet.render(mountEl, item, { onDone, voice })
 *
 *   item  = a WORKSHEET_GRAMMAR object: { type, instruction, voice, payload, answer, explain }
 *   onDone(result) → { correct:bool, item, answerGiven }  (fires when the child checks/answers)
 *   voice = speak instruction + feedback via /kids/tts (default: window.__KIDS ? true : false)
 *
 * Every archetype maps to ONE input FAMILY, so the input handling is a small, testable set. */
(function (global) {
  'use strict';

  /* ---------------- input FAMILY per archetype type ---------------- */
  var FAMILY = {
    // tap one option
    mcq: 'tap', compare_symbol: 'tap', true_false: 'tap', odd_one_out: 'tap',
    choose_good: 'tap', rhyme_match: 'tap', begin_sound: 'tap', pattern_next: 'tap',
    // number / text pad
    count_write: 'pad', fill_sequence: 'pad', neighbour_number: 'pad', arith: 'pad',
    count_money: 'pad', read_clock: 'pad',
    // connect two columns
    match_quantity: 'match', match_case: 'match', match_word_picture: 'match', match_following: 'match',
    // items into bins
    shape_sort: 'sort', sort_groups: 'sort',
    // arrange in order
    order_steps: 'order', order_words: 'order',
    // fill blanks (tile bank)
    fill_letter: 'fill', cloze: 'fill', wordbank_fill: 'fill',
    // open answer: keyboard + voice
    opposite: 'write', word_problem_text: 'write', describe: 'write',
    // canvas practice
    trace_number: 'trace', trace_letter: 'trace',
    // colour by number
    color_by_number: 'color'
  };

  /* ---------------- tiny helpers ---------------- */
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function norm(s) { return String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9अ-ह]+/gi, ' ').trim(); }
  var PAIR_COLORS = ['#ff5aa5', '#3aa0ff', '#ffb300', '#22b07d', '#9b6bff', '#ff7847', '#00b4d8', '#e63946'];

  /* render a token as generated pool art (KidsAssets) if available, else emoji/text — backward compatible */
  function mkVisual(token, size) {
    if (global.KidsAssets && global.KidsAssets.get) return global.KidsAssets.node(token, size || 40);
    var s = document.createElement('span'); s.textContent = (token && token.emoji) || token; return s;
  }
  /* an option/answer label → its PICTURE above the WORD when the pool has art for that entity
     (English OR Hindi, via the manifest word-index), else just the word. Keeps the label so
     reading/vocab questions still read. This is how pooled assets attach to knowledge questions. */
  function entityLabel(text, size) {
    var t = String(text == null ? '' : text);
    if (global.KidsAssets && global.KidsAssets.idFor && global.KidsAssets.idFor(t)) {
      var wrap = el('span', 'ws-ent');
      wrap.appendChild(global.KidsAssets.node(t, size || 46));
      wrap.appendChild(el('span', 'ws-ent-lbl', t));
      return wrap;
    }
    return el('span', null, t);
  }

  /* speak a math/word stem the way a child voice reads it (mirrors kids_voice.js) */
  function speakable(s) {
    return (s || '').replace(/₹/g, ' rupees ').replace(/×/g, ' times ').replace(/÷/g, ' divided by ')
      .replace(/[−]/g, ' minus ').replace(/=/g, ' equals ').replace(/\+/g, ' plus ')
      .replace(/>/g, ' greater than ').replace(/</g, ' less than ').replace(/\s*[—–]\s*/g, ' goes with ')
      .replace(/_{2,}/g, ' blank ').replace(/\?/g, ' ').replace(/\s+/g, ' ').trim();
  }
  /* ---- language: Hindi content gets a Hindi voice (hi-IN-SwaraNeural), not the English child voice ---- */
  var DEVANAGARI = /[ऀ-ॿ]/;
  function hasHindi(s) { return DEVANAGARI.test(String(s == null ? '' : s)); }
  function itemIsHindi(item) {
    var p = item.payload || {};
    return hasHindi(item.instruction) || hasHindi(p.sentence) || hasHindi(p.statement) ||
      hasHindi((p.bank || []).join(' ')) || hasHindi((p.options || []).join(' ')) ||
      hasHindi(JSON.stringify(p.pairs || [])) || hasHindi(String(item.answer == null ? '' : item.answer));
  }
  /* light cleanup for Hindi (keep Devanagari; drop blanks/question marks) */
  function hindiSpeakable(s) { return String(s || '').replace(/_{2,}|▢/g, ' ').replace(/\s*[—–]\s*/g, ' से ').replace(/[?]/g, ' ').replace(/\s+/g, ' ').trim(); }
  var HI_VOICE = 'hi-IN-SwaraNeural', EN_VOICE = 'en-US-AnaNeural';

  /* Hindi task-instructions per archetype — so a Hindi worksheet reads FULLY in Hindi even when
     the generated `instruction` came back in English (the content/options are already Hindi). */
  var HI_INSTR = {
    odd_one_out: 'इनमें से कौन सा अलग है?', true_false: 'क्या यह सही है?', cloze: 'रिक्त स्थान भरिए।',
    match_following: 'सही जोड़ी मिलाइए।', sort_groups: 'इन्हें सही समूह में रखिए।', mcq: 'सही उत्तर चुनिए।',
    compare_symbol: 'सही चिन्ह लगाइए।', arith: 'हल कीजिए।', count_write: 'गिनकर लिखिए।',
    fill_sequence: 'छूटी हुई संख्या भरिए।', neighbour_number: 'सही संख्या लिखिए।', pattern_next: 'आगे क्या आएगा?'
  };
  /* the instruction to SHOW/READ: keep it if already in the item's language; for a Hindi item whose
     instruction slipped out in English, use the Hindi template so nothing is mixed-language. */
  function localizedInstruction(item) {
    var instr = item.instruction || '';
    if (itemIsHindi(item) && !hasHindi(instr)) return HI_INSTR[item.type] || instr;
    return instr;
  }

  var _audio = null;
  // tts(text, on, onEnd): speak `text`; onEnd() fires exactly ONCE, when the audio truly FINISHES
  // (or fails, or — voice off — after reading time). The safety net is armed from the audio's REAL
  // duration (not a length estimate), so a long/Hindi clip is never cut short and advanced early.
  function tts(text, on, onEnd) {
    var fired = false, durTimer = null, hardTimer = null;
    function fin() {
      if (fired) return; fired = true;
      if (durTimer) clearTimeout(durTimer);
      if (hardTimer) clearTimeout(hardTimer);
      if (onEnd) onEnd();
    }
    if (!text) { fin(); return; }
    if (!on) { setTimeout(fin, Math.min(7000, speechMs(text))); return; }   // voice off → reading time
    var hindi = hasHindi(text);
    var voice = hindi ? HI_VOICE : EN_VOICE;
    var say = (hindi ? hindiSpeakable(text) : speakable(text)).slice(0, 580);
    // strip emoji / pictographs / symbols so the voice never reads "party popper" etc. aloud
    say = say.replace(/[\u{1F000}-\u{1FAFF}\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{2190}-\u{21FF}\u{FE00}-\u{FE0F}\u{200D}]/gu, ' ').replace(/\s+/g, ' ').trim();
    if (!say) { fin(); return; }
    try { if (_audio) { _audio.onended = _audio.onerror = _audio.onloadedmetadata = null; _audio.pause(); } } catch (e) {}
    _audio = new Audio('/kids/tts?text=' + encodeURIComponent(say) + '&voice=' + encodeURIComponent(voice));
    _audio.onended = fin;                       // PRIMARY: fire when playback actually completes
    _audio.onerror = fin;                        // audio failed to load → don't hang
    _audio.onloadedmetadata = function () {       // BACKUP net tied to the real length (+ buffer)
      var d = _audio.duration;
      if (isFinite(d) && d > 0) { if (durTimer) clearTimeout(durTimer); durTimer = setTimeout(fin, d * 1000 + 1800); }
    };
    _audio.play().catch(fin);
    hardTimer = setTimeout(fin, 30000);          // absolute backstop against a permanent stall
  }
  /* what to READ for the question: prefer an explicit voice line; for Hindi content whose
     instruction is English, read the Hindi payload (sentence/statement) so the child hears Hindi */
  /* What the voice actually reads. For a true/false or a cloze the SENTENCE is the question —
     "सही या ग़लत?" on its own tells a child nothing. This used to return item.voice (which the
     KB sets to the instruction) and short-circuit before ever reaching the statement, so the
     one line that mattered was the one line never spoken. */
  function promptSpeak(item) {
    var p = item.payload || {};
    var content = p.statement || p.sentence || '';
    var lead = (item.voice && hasHindi(item.voice) === itemIsHindi(item))
      ? item.voice : (localizedInstruction(item) || '');
    // only read content that's in the item's own language, so nothing comes out half-translated
    if (content && hasHindi(content) === itemIsHindi(item)) {
      // a cloze blank must be SAID, not spelled out as underscores
      content = String(content).replace(/_{2,}|▢/g, itemIsHindi(item) ? ' रिक्त स्थान ' : ' blank ')
                               .replace(/\s{2,}/g, ' ').trim();
      if (!lead) return content;
      if (lead.indexOf(content) !== -1) return lead;     // the lead already says it
      // don't end up with "…true or false?. The cat…"
      return lead + (/[.?!।]\s*$/.test(lead) ? ' ' : '. ') + content;
    }
    return lead || content;
  }
  var SR = global.SpeechRecognition || global.webkitSpeechRecognition;

  /* the correct answer, spoken/shown the way a child hears it (for the "explain when wrong" feedback).
     Match/sort/order carry the answer as pairs/map/sequence — spell those out too, not just scalars. */
  function answerSpoken(item) {
    var t = item.type, a = item.answer, p = item.payload || {};
    if (t === 'true_false') return (a === true || a === 'True') ? 'True' : 'False';
    if (t === 'compare_symbol') return ({ '<': 'less than', '>': 'greater than', '=': 'equal to' })[a] || String(a);
    if (t === 'match_following') {
      var prs = p.pairs || [];
      if (!prs.length && a && typeof a === 'object') prs = Object.keys(a).map(function (k) { return [k, a[k]]; });
      if (prs.length) return prs.map(function (pr) { return pr[0] + ' — ' + pr[1]; }).join(', ');
    }
    if (t === 'sort_groups' && a && typeof a === 'object') {
      return Object.keys(a).map(function (k) { return k + ' — ' + a[k]; }).join(', ');
    }
    if (t === 'order_steps' || t === 'order_words') {
      var seq = p.steps || p.words || (Array.isArray(a) ? a : []);
      if (seq.length) return seq.join(', ');
    }
    if (Array.isArray(a)) return a.filter(function (x) { return x != null; }).join(', ');
    if (a && typeof a === 'object') return '';
    return (a == null) ? '' : String(a);
  }
  function _isPairing(t) { return t === 'match_following' || t === 'sort_groups' || t === 'order_steps' || t === 'order_words'; }
  /* full spoken correction: name the right answer, then the reason (item.explain).
     Hindi items get a Hindi correction (English explain is dropped to avoid a language mash-up). */
  function correctionSpoken(item) {
    var a = answerSpoken(item), pairing = _isPairing(item.type);
    if (itemIsHindi(item)) {
      if (!a) return 'कोई बात नहीं, चलो इसे साथ में देखते हैं।';
      return pairing ? ('अरे नहीं! सही जोड़ियाँ हैं — ' + a + '।') : ('अरे नहीं! सही उत्तर है — ' + a + '।');
    }
    var ex = item.explain ? (' ' + item.explain) : '';
    if (item.type === 'arith') {
      var p = item.payload || {};
      return 'Not quite. ' + p.a + ' ' + (p.op || '+') + ' ' + p.b + ' is ' + a + '.' + ex;
    }
    if (pairing && a) return 'Not quite. The correct matches are — ' + a + '.';
    if (a) return 'Not quite. The correct answer is ' + a + '.' + ex;
    return 'Not quite. Let us look at it together.' + ex;
  }
  /* rough time the child-voice needs to read `text`, so the flow waits before advancing */
  function speechMs(text) { return Math.min(9000, Math.max(1600, 650 + (text || '').length * 68)); }

  /* ---------------- public entry ---------------- */
  function render(mount, item, opts) {
    opts = opts || {};
    var voice = opts.voice != null ? opts.voice : !!global.__KIDS;
    var card = el('div', 'ws-card');

    // header: instruction + hear-again
    var head = el('div', 'ws-head');
    head.appendChild(el('div', 'ws-instr', localizedInstruction(item)));
    var hear = el('button', 'ws-hear', '🔊'); hear.title = 'Hear it again';
    hear.onclick = function () { tts(promptSpeak(item), true); };
    head.appendChild(hear);
    card.appendChild(head);

    var body = el('div', 'ws-body');
    card.appendChild(body);
    mount.innerHTML = '';
    mount.appendChild(card);

    var ctx = {
      body: body, card: card, item: item, voice: voice,
      done: function (correct, answerGiven) {
        // On a WRONG answer, the voice explains the correct answer; on a right answer, brief praise.
        // The PARENT triggers the speech via result.speak(cb) and advances only when cb fires (i.e.
        // once the explanation has been fully read out) — so questions never get cut short.
        var fbText = correct
          ? (itemIsHindi(item) ? 'सही! शाबाश! 🎉' : 'Correct! Well done! 🎉')
          : correctionSpoken(item);
        if (opts.onDone) opts.onDone({
          correct: !!correct, item: item, answerGiven: answerGiven,
          feedbackText: fbText,
          speak: function (cb) { tts(fbText, voice, cb); }
        });
      },
      foot: function (checkFn) { return buildFoot(card, checkFn); }
    };

    var fam = FAMILY[item.type] || item.family || 'tap';
    (RENDER[fam] || RENDER.tap)(body, item, ctx);

    if (voice) setTimeout(function () { tts(promptSpeak(item), true); }, 250);
    return card;
  }

  /* shared footer with a Check button + feedback line */
  function buildFoot(card, onCheck) {
    var foot = el('div', 'ws-foot');
    var btn = el('button', 'ws-check', 'Check ✅');
    var fb = el('div', 'ws-fb', '');
    btn.onclick = function () { onCheck(fb, btn); };
    foot.appendChild(btn); foot.appendChild(fb);
    card.appendChild(foot);
    return { btn: btn, fb: fb };
  }
  function say(fb, ok, msg) { fb.className = 'ws-fb ' + (ok ? 'ok' : 'no'); fb.textContent = msg; }

  /* ================= RENDERERS (one per input family) ================= */
  var RENDER = {};

  /* ---- TAP: pick one option (mcq, compare, true/false, odd-one-out, choose, rhyme…) ---- */
  RENDER.tap = function (body, item, ctx) {
    var p = item.payload || {};
    var opts = p.options || (item.type === 'true_false' ? ['True', 'False'] : []);
    if (item.type === 'compare_symbol') {
      body.appendChild(el('div', 'ws-entry', p.a + '  ◻  ' + p.b));
      opts = ['<', '=', '>'];
    }
    // A true/false question is the STATEMENT — without it the child sees only "Is this true or
    // false?" and two buttons, which is unanswerable. The KB puts it in payload.statement.
    if (item.type === 'true_false' && p.statement) {
      body.appendChild(el('div', 'ws-entry ws-statement', String(p.statement)));
    }
    var ans = item.answer;
    if (item.type === 'true_false' && typeof ans === 'boolean') ans = ans ? 'True' : 'False';
    // The BUTTON LABEL is localised; the value compared against the answer stays canonical.
    var TF_HI = { 'True': 'सही', 'False': 'ग़लत' };
    var hiTF = item.type === 'true_false' && itemIsHindi(item);
    var wrap = el('div', 'ws-opts');
    opts.forEach(function (o) {
      var b = el('button', 'ws-opt ws-big');
      b.appendChild(entityLabel(hiTF ? (TF_HI[o] || o) : o, 46));
      b.onclick = function () {
        if (b.classList.contains('right') || b.classList.contains('wrong')) return;
        var ok = String(o) === String(ans);
        b.classList.add(ok ? 'right' : 'wrong');
        ctx.done(ok, o);
      };
      wrap.appendChild(b);
    });
    body.appendChild(wrap);
  };

  /* ---- PAD: number/text entry (count-write, sequence, arith, money, clock…) ---- */
  RENDER.pad = function (body, item, ctx) {
    var p = item.payload || {};
    var prompt = p.display || p.stem || '';
    if (item.type === 'arith') prompt = p.a + ' ' + (p.op || '+') + ' ' + p.b + ' = ?';
    if (item.type === 'fill_sequence') prompt = (p.seq || []).map(function (x) { return x == null ? '▢' : x; }).join('  ');
    if (item.type === 'count_write' && (p.emoji || p.asset)) {
      var strip = el('div', 'ws-entry');
      strip.style.display = 'flex'; strip.style.flexWrap = 'wrap'; strip.style.gap = '6px';
      strip.style.justifyContent = 'center'; strip.style.alignItems = 'center';
      for (var ci = 0; ci < (p.n || 0); ci++) strip.appendChild(mkVisual(p.asset || p.emoji, 36));
      body.appendChild(strip);
    } else if (prompt) { var pe = el('div', 'ws-entry'); pe.textContent = prompt; body.appendChild(pe); }

    var entry = el('div', 'ws-entry', '&nbsp;'); entry.style.color = 'var(--ws-blue)';
    body.appendChild(entry);
    var val = '';
    function paint() { entry.textContent = val || ' '; }
    var pad = el('div', 'ws-pad');
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '⌫', '0', '✓'].forEach(function (k) {
      var key = el('button', 'ws-key', k);
      key.onclick = function () {
        if (k === '⌫') val = val.slice(0, -1);
        else if (k === '✓') return check();
        else if (val.length < 7) val += k;
        paint();
      };
      pad.appendChild(key);
    });
    body.appendChild(pad);
    // physical keyboard too
    global.addEventListener('keydown', function onKey(e) {
      if (!body.isConnected) { global.removeEventListener('keydown', onKey); return; }
      if (/[0-9]/.test(e.key)) { if (val.length < 7) { val += e.key; paint(); } }
      else if (e.key === 'Backspace') { val = val.slice(0, -1); paint(); }
      else if (e.key === 'Enter') check();
    });
    var f = ctx.foot(function () { check(); });
    function check() {
      if (val === '') { say(f.fb, false, 'Type your answer 👆'); return; }
      var ans = Array.isArray(item.answer) ? String(item.answer[0]) : String(item.answer);
      var ok = norm(val) === norm(ans);
      say(f.fb, ok, ok ? 'Correct! 🎉' : 'Try again 💪');
      entry.parentElement && entry.classList.toggle('right', ok);
      ctx.done(ok, val);
    }
  };

  /* ---- MATCH: tap a left item then a right item to connect them ---- */
  RENDER.match = function (body, item, ctx) {
    var p = item.payload || {};
    var left = p.left || (p.pairs || []).map(function (x) { return x[0]; });
    var right = p.right || (p.pairs || []).map(function (x) { return x[1]; });
    // truth: index in left -> value it should connect to
    var truth = {};
    if (p.pairs) p.pairs.forEach(function (pr, i) { truth[i] = pr[1]; });
    else if (Array.isArray(item.answer)) item.answer.forEach(function (v, i) { truth[i] = v; });
    else left.forEach(function (l, i) { truth[i] = right[i]; });
    right = shuffle(right);

    var grid = el('div', 'ws-match');
    var colL = el('div', 'ws-col'), colR = el('div', 'ws-col');
    var sel = { side: null, idx: -1 }, pairs = {}, nColor = 0;
    function mkItem(txt, side, idx) {
      var it = el('div', 'ws-col-item'); it.appendChild(entityLabel(txt, 34));
      var dot = el('span', 'ws-dot'); dot.style.background = 'transparent'; it.appendChild(dot);
      it._dot = dot; it._txt = txt;
      it.onclick = function () {
        if (side === 'L') { clearSel(); sel = { side: 'L', idx: idx, e: it }; it.classList.add('sel'); }
        else if (sel.side === 'L') { connect(sel.idx, sel.e, it); clearSel(); }
      };
      return it;
    }
    function clearSel() { [].forEach.call(grid.querySelectorAll('.sel'), function (n) { n.classList.remove('sel'); }); sel = { side: null, idx: -1 }; }
    function connect(li, le, re) {
      var c = PAIR_COLORS[(nColor++) % PAIR_COLORS.length];
      le._dot.style.background = c; re._dot.style.background = c;
      pairs[li] = re._txt;
    }
    left.forEach(function (l, i) { colL.appendChild(mkItem(l, 'L', i)); });
    right.forEach(function (r, i) { colR.appendChild(mkItem(r, 'R', i)); });
    grid.appendChild(colL); grid.appendChild(colR);
    body.appendChild(grid);
    body.appendChild(el('div', 'ws-hint', 'Tap a picture, then tap its match 👆'));
    var f = ctx.foot(function () {
      var all = Object.keys(truth), ok = all.length > 0;
      all.forEach(function (i) { if (norm(pairs[i]) !== norm(truth[i])) ok = false; });
      say(f.fb, ok, ok ? 'All matched! 🎉' : 'Check the lines again 💪');
      ctx.done(ok, pairs);
    });
  };

  /* ---- SORT: tap a chip then tap a bin to drop it ---- */
  RENDER.sort = function (body, item, ctx) {
    var p = item.payload || {};
    var items = p.items || [], bins = p.bins || [];
    var truth = item.answer || {}; // item value -> bin name
    var tray = el('div', 'ws-tray');
    var sel = null, placed = {};
    items.forEach(function (v) {
      var c = el('button', 'ws-chip'); c.appendChild(entityLabel(v, 30)); c._val = v;
      c.onclick = function () {
        if (sel) sel.classList.remove('sel');
        if (sel === c) { sel = null; return; }
        sel = c; c.classList.add('sel');
      };
      tray.appendChild(c);
    });
    body.appendChild(tray);
    var binWrap = el('div', 'ws-bins');
    bins.forEach(function (b) {
      var bin = el('div', 'ws-bin');
      bin.appendChild(el('div', 'ws-bin-label', b));
      var drop = el('div', 'ws-bin-drop');
      bin.appendChild(drop);
      bin.onclick = function () {
        if (!sel) return;
        placed[sel._val != null ? sel._val : sel.textContent] = b;
        drop.appendChild(sel); sel.classList.remove('sel'); sel = null;
      };
      binWrap.appendChild(bin);
    });
    body.appendChild(binWrap);
    var f = ctx.foot(function () {
      var keys = Object.keys(truth), ok = keys.length > 0 && Object.keys(placed).length >= items.length;
      keys.forEach(function (k) { if (norm(placed[k]) !== norm(truth[k])) ok = false; });
      say(f.fb, ok, ok ? 'Sorted! 🎉' : 'Some are in the wrong home 💪');
      ctx.done(ok, placed);
    });
  };

  /* ---- ORDER: tap tiles in the right order (assigns 1,2,3…) ---- */
  RENDER.order = function (body, item, ctx) {
    var p = item.payload || {};
    var truth = p.steps || p.words || item.answer || [];
    var display = item.type === 'order_words' ? shuffle(truth) : shuffle(truth);
    var picks = [];
    var wrap = el('div', 'ws-order');
    display.forEach(function (v) {
      var t = el('button', 'ws-tile');
      var no = el('span', 'ws-seqno'); t.appendChild(no);
      t.appendChild(el('span', null, String(v)));
      t._val = v;
      t.onclick = function () {
        if (t.classList.contains('numbered')) { // un-pick + renumber
          picks.splice(picks.indexOf(t), 1); t.classList.remove('numbered');
        } else { picks.push(t); t.classList.add('numbered'); }
        picks.forEach(function (x, i) { x.querySelector('.ws-seqno').textContent = i + 1; });
      };
      wrap.appendChild(t);
    });
    body.appendChild(wrap);
    body.appendChild(el('div', 'ws-hint', 'Tap them in the right order 🔢'));
    var f = ctx.foot(function () {
      var got = picks.map(function (t) { return t._val; });
      var ok = got.length === truth.length && got.every(function (v, i) { return norm(v) === norm(truth[i]); });
      say(f.fb, ok, ok ? 'Perfect order! 🎉' : 'Not quite — try again 💪');
      ctx.done(ok, got);
    });
  };

  /* ---- FILL: sentence with blanks, filled from a tap-able word/letter bank ---- */
  RENDER.fill = function (body, item, ctx) {
    var p = item.payload || {};
    var ans = Array.isArray(item.answer) ? item.answer : [item.answer];
    var sentence = p.sentence || p.word || '';
    // build sentence with blanks marked by ___ or a single letter blank
    var parts, blanks = [];
    if (item.type === 'fill_letter') {
      var w = (p.word || '').split(''), bl = p.blanks || [];
      var s = el('div', 'ws-sentence');
      if (p.emoji) s.appendChild(el('span', null, p.emoji + '  '));
      w.forEach(function (ch, i) {
        if (bl.indexOf(i) >= 0) { var b = el('span', 'ws-blank', '＿'); b._i = blanks.length; blanks.push(b); s.appendChild(b); }
        else s.appendChild(el('span', null, ch));
      });
      body.appendChild(s);
    } else {
      parts = sentence.split(/_{2,}/);
      var s2 = el('div', 'ws-sentence');
      parts.forEach(function (seg, i) {
        s2.appendChild(el('span', null, seg));
        if (i < parts.length - 1) { var b = el('span', 'ws-blank', '＿＿'); b._i = blanks.length; blanks.push(b); s2.appendChild(b); }
      });
      body.appendChild(s2);
    }
    var target = null;
    blanks.forEach(function (b) { b.onclick = function () { target = b; blanks.forEach(function (x) { x.style.outline = ''; }); b.style.outline = '3px solid var(--ws-blue)'; }; });
    if (blanks.length === 1) target = blanks[0];
    var bankVals = p.bank || p.options || (item.type === 'fill_letter' ? ('abcdefghij'.split('')) : []);
    var bank = el('div', 'ws-bank');
    shuffle(bankVals).forEach(function (v) {
      var c = el('button', 'ws-chip'); c.textContent = v;
      c.onclick = function () { if (!target) target = blanks[0]; if (!target) return; target.textContent = v; target.classList.add('filled'); target._val = v; };
      bank.appendChild(c);
    });
    body.appendChild(bank);
    var f = ctx.foot(function () {
      var got = blanks.map(function (b) { return b._val || ''; });
      var ok = got.length === ans.length && got.every(function (v, i) { return norm(v) === norm(ans[i]); });
      blanks.forEach(function (b, i) { b.classList.toggle('filled', norm(b._val) === norm(ans[i])); });
      say(f.fb, ok, ok ? 'Correct! 🎉' : 'Look again 💪');
      ctx.done(ok, got);
    });
  };

  /* ---- WRITE: open answer via KEYBOARD + VOICE (the descriptive-answer path) ---- */
  RENDER.write = function (body, item, ctx) {
    var wrap = el('div', 'ws-write-wrap');
    var ta = el('textarea', 'ws-write'); ta.placeholder = 'Type your answer, or tap 🎤 to speak…';
    wrap.appendChild(ta);
    var tools = el('div', 'ws-write-tools');
    var mic = el('button', 'ws-mic', '🎤 Speak your answer');
    tools.appendChild(mic); wrap.appendChild(tools);
    body.appendChild(wrap);

    mic.onclick = function () {
      if (!SR) { ta.focus(); mic.textContent = '⌨️ Type it (mic needs Chrome)'; return; }
      var rec = new SR(); rec.lang = 'en-IN'; rec.interimResults = false; rec.maxAlternatives = 1;
      mic.classList.add('live'); mic.textContent = '🎙️ Listening…';
      rec.onresult = function (e) { ta.value = (ta.value ? ta.value + ' ' : '') + (e.results[0][0].transcript || ''); };
      rec.onerror = rec.onend = function () { mic.classList.remove('live'); mic.textContent = '🎤 Speak your answer'; };
      try { rec.start(); } catch (e) { mic.classList.remove('live'); }
    };

    var accept = item.answer; // array of acceptable answers, or null = open (parent/self-check)
    var f = ctx.foot(function () {
      var v = ta.value.trim();
      if (!v) { say(f.fb, false, 'Write or speak your answer 👆'); return; }
      if (!accept) { say(f.fb, true, 'Answer saved ✍️ (grown-up can check)'); ctx.done(true, v); return; }
      var list = Array.isArray(accept) ? accept : [accept];
      var ok = list.some(function (a) { return norm(v).indexOf(norm(a)) >= 0 || norm(a) === norm(v); });
      say(f.fb, ok, ok ? 'Great answer! 🎉' : 'Hmm, try again 💪');
      ctx.done(ok, v);
    });
  };

  /* ---- TRACE: canvas finger-trace over a ghost glyph (practice → self-check) ---- */
  RENDER.trace = function (body, item, ctx) {
    var p = item.payload || {};
    var glyph = p.glyph != null ? p.glyph : (p.letter != null ? p.letter : '');
    var wrap = el('div', 'ws-trace-wrap');
    wrap.appendChild(el('div', 'ws-trace-ghost', String(glyph)));
    var cv = el('canvas', 'ws-canvas');
    wrap.appendChild(cv); body.appendChild(wrap);
    if (p.cue_emoji) body.appendChild(el('div', 'ws-hint', p.cue_emoji + ' ' + (p.cue || '')));
    // size canvas to element
    function fit() { var r = cv.getBoundingClientRect(); cv.width = r.width; cv.height = r.height; }
    setTimeout(fit, 0);
    var g = cv.getContext('2d'); g.lineWidth = 10; g.lineCap = 'round'; g.strokeStyle = '#3aa0ff';
    var drawing = false, drew = false;
    function pos(e) { var r = cv.getBoundingClientRect(); var t = e.touches ? e.touches[0] : e; return [t.clientX - r.left, t.clientY - r.top]; }
    function down(e) { drawing = true; drew = true; var q = pos(e); g.beginPath(); g.moveTo(q[0], q[1]); e.preventDefault(); }
    function move(e) { if (!drawing) return; var q = pos(e); g.lineTo(q[0], q[1]); g.stroke(); e.preventDefault(); }
    function up() { drawing = false; }
    cv.addEventListener('mousedown', down); cv.addEventListener('mousemove', move); global.addEventListener('mouseup', up);
    cv.addEventListener('touchstart', down, { passive: false }); cv.addEventListener('touchmove', move, { passive: false }); cv.addEventListener('touchend', up);
    var f = ctx.foot(function () {
      if (!drew) { say(f.fb, false, 'Trace the shape first ✏️'); return; }
      say(f.fb, true, 'Nice writing! ✍️🎉'); ctx.done(true, 'traced');
    });
    f.btn.textContent = 'Done ✏️';
    var clr = el('button', 'ws-mic', '↺ Clear'); clr.style.background = '#9aa3ad';
    clr.onclick = function () { g.clearRect(0, 0, cv.width, cv.height); drew = false; };
    f.btn.parentElement.appendChild(clr);
  };

  /* ---- COLOR: solve each region's fact, tap a colour by the key ---- */
  RENDER.color = function (body, item, ctx) {
    var p = item.payload || {}, legend = p.legend || {}, regions = p.regions || [];
    var truth = {}; // region index -> correct colour
    regions.forEach(function (r, i) { truth[i] = legend[String(r.key)]; });
    var grid = el('div', 'ws-color-grid'); var chosen = {}; var selColor = null; var regs = [];
    regions.forEach(function (r, i) {
      var reg = el('div', 'ws-region', r.fact); reg._i = i;
      reg.onclick = function () { if (!selColor) return; reg.style.background = selColor; chosen[i] = selColor; };
      regs.push(reg); grid.appendChild(reg);
    });
    body.appendChild(grid);
    var pal = el('div', 'ws-palette');
    Object.keys(legend).forEach(function (k) {
      var c = legend[k];
      var sw = el('button', 'ws-swatch'); sw.style.background = c; sw.title = c;
      sw.onclick = function () { [].forEach.call(pal.children, function (n) { n.classList.remove('sel'); }); sw.classList.add('sel'); selColor = c; };
      pal.appendChild(sw);
    });
    body.appendChild(el('div', 'ws-hint', 'Pick a colour, then tap the boxes that solve to it 🎨'));
    body.appendChild(pal);
    var f = ctx.foot(function () {
      var keys = Object.keys(truth), ok = keys.length > 0;
      keys.forEach(function (i) { if (chosen[i] !== truth[i]) ok = false; });
      say(f.fb, ok, ok ? 'Beautiful! 🎉' : 'Some colours are off 💪');
      ctx.done(ok, chosen);
    });
  };

  /* ---------------- export ---------------- */
  function stop() { try { if (_audio) { _audio.onended = _audio.onerror = null; _audio.pause(); } } catch (e) {} }
  global.KidsWorksheet = { render: render, FAMILY: FAMILY, stop: stop };
})(window);
