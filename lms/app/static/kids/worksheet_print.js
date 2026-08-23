/* worksheet_print.js — PENCIL-AND-PAPER renderer (Phase 4).
 *
 * Takes the SAME worksheet item JSON as the interactive component and lays it out static, with
 * blank boxes/lines for writing by hand. One call:
 *
 *     KidsWorksheetPrint.render(mount, items, { title, subtitle })
 *
 * Reuses KidsAssets for pool art (emoji fallback). Print via the button (window.print) or the page's
 * own control. No dependency on worksheet.js. */
(function (global) {
  'use strict';

  function el(t, c, h) { var e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; }
  function box(sm) { return '<span class="wp-box' + (sm ? ' sm' : '') + '"></span>'; }

  /* one visual token → art (if pool ready) or emoji/text */
  function vis(token, size) {
    if (global.KidsAssets && global.KidsAssets.node) return global.KidsAssets.node(token, size || 32);
    var s = document.createElement('span'); s.textContent = (token && token.emoji) || token; return s;
  }
  function strip(token, n, size) {
    var w = el('span', 'wp-visual');
    for (var i = 0; i < n; i++) w.appendChild(vis(token, size || 32));
    return w;
  }
  /* pool art (img) for an EN/HI word, or null — same resolver the digital worksheet uses */
  function artFor(text, size) {
    if (global.KidsAssets && global.KidsAssets.node) {
      var n = global.KidsAssets.node(text, size || 34);
      if (n && n.tagName === 'IMG') { n.style.display = 'block'; n.style.margin = '0 auto 2px'; return n; }
    }
    return null;
  }
  /* an option cell that shows the PICTURE above the WORD when the pool has art for it (print-friendly) */
  function entityOpt(text, cls) {
    var d = el('div', cls || 'wp-opt'), img = artFor(text, 34);
    if (img) d.appendChild(img);
    d.appendChild(el('span', null, String(text)));
    return d;
  }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor((i + 1) * ((i * 9301 + 49297) % 233280) / 233280); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }

  /* per-archetype STATIC print body */
  var PRINT = {
    count_write: function (body, p) {
      body.appendChild(strip(p.asset || p.emoji, p.n || 0, 34));
      body.appendChild(el('div', 'wp-expr', 'How many?  ' + box()));
    },
    arith: function (body, p) {
      body.appendChild(el('div', 'wp-expr', p.a + ' ' + (p.op || '+') + ' ' + p.b + '  =  ' + box()));
      body.appendChild(el('div', 'wp-work'));
    },
    fill_sequence: function (body, p) {
      var s = (p.seq || []).map(function (x) { return x == null ? box(true) : '<b>' + x + '</b>'; }).join('&nbsp;&nbsp;&nbsp;');
      body.appendChild(el('div', 'wp-expr', s));
    },
    compare_symbol: function (body, p) {
      body.appendChild(el('div', 'wp-expr', p.a + '&nbsp;&nbsp;' + box(true) + '&nbsp;&nbsp;' + p.b + '<span style="font-size:.8rem;font-weight:600;color:#8a8397"> &nbsp;(&lt; &gt; =)</span>'));
    },
    neighbour_number: function (body, p) {
      body.appendChild(el('div', 'wp-expr', (p.display || (p.mode === 'before' ? p.n + ' , ▢' : '▢ , ' + p.n)).replace(/_{2,}|▢/g, box(true))));
    },
    count_money: function (body, p) {
      body.appendChild(el('div', 'wp-expr', (p.display || (p.coins || []).map(function (c) { return '₹' + c; }).join(' + ')) + '  =  ₹' + box()));
    },
    pattern_next: function (body, p) {
      body.appendChild(el('div', 'wp-expr', (p.seq || []).join('&nbsp;&nbsp;') + '&nbsp;&nbsp;' + box(true)));
      if (p.options) { var o = el('div', 'wp-opts'); (p.options).forEach(function (x) { o.appendChild(el('div', 'wp-opt', x)); }); body.appendChild(el('div', null, L('Circle the answer:', 'उत्तर पर गोला लगाइए:'))); body.appendChild(o); }
    },
    match_following: function (body, p) {
      var pairs = p.pairs || [], left = pairs.map(function (x) { return x[0]; }), right = shuffle(pairs.map(function (x) { return x[1]; }));
      var m = el('div', 'wp-match'), cl = el('div', 'wp-mcol left'), cr = el('div', 'wp-mcol');
      left.forEach(function (v) { var it = el('div', 'wp-mi'); var im = artFor(v, 30); if (im) it.appendChild(im); it.appendChild(el('span', null, String(v))); it.appendChild(el('span', 'wp-dot')); cl.appendChild(it); });
      right.forEach(function (v) { var it = el('div', 'wp-mi r'); it.appendChild(el('span', 'wp-dot')); var im = artFor(v, 30); if (im) it.appendChild(im); it.appendChild(el('span', null, String(v))); cr.appendChild(it); });
      m.appendChild(cl); m.appendChild(cr); body.appendChild(el('div', null, L('Draw a line to match:', 'जोड़ी मिलाने के लिए रेखा खींचिए:'))); body.appendChild(m);
    },
    true_false: function (body, p) {
      if (p.statement) body.appendChild(el('div', 'wp-expr', String(p.statement)));
      var o = el('div', 'wp-opts');
      o.appendChild(el('div', 'wp-opt', L('◯ True', '◯ सही'))); o.appendChild(el('div', 'wp-opt', L('◯ False', '◯ ग़लत')));
      body.appendChild(el('div', null, L('Circle one:', 'सही या ग़लत पर गोला लगाइए:'))); body.appendChild(o);
    },
    cloze: function (body, p) {
      var s = String(p.sentence || '').replace(/_{2,}|▢/g, box(true));
      body.appendChild(el('div', 'wp-expr', s));
      if (p.bank && p.bank.length) {
        var o = el('div', 'wp-opts'); p.bank.forEach(function (w) { o.appendChild(entityOpt(w)); });
        body.appendChild(el('div', null, L('Word bank:', 'शब्द-भंडार:'))); body.appendChild(o);
      }
    },
    odd_one_out: function (body, p) {
      var o = el('div', 'wp-opts'); (p.options || []).forEach(function (x) { o.appendChild(entityOpt(x)); });
      body.appendChild(el('div', null, L('Circle the one that does not belong:', 'जो अलग है उस पर गोला लगाइए:'))); body.appendChild(o);
    },
    sort_groups: function (body, p) {
      if (p.bins && p.bins.length) body.appendChild(el('div', 'wp-expr', L('Groups:  ', 'समूह:  ') + p.bins.map(function (b) { return '<b>' + b + '</b>'; }).join('&nbsp;&nbsp;/&nbsp;&nbsp;')));
      (p.items || []).forEach(function (v) {
        var row = el('div', 'wp-expr'); var im = artFor(v, 30);
        if (im) { im.style.display = 'inline-block'; im.style.verticalAlign = 'middle'; im.style.margin = '0 6px 0 0'; row.appendChild(im); }
        row.appendChild(el('span', null, String(v) + '  →  ' + box()));
        body.appendChild(row);
      });
    }
  };

  var HI_INSTR = { odd_one_out: 'इनमें से कौन सा अलग है?', true_false: 'क्या यह सही है?', cloze: 'रिक्त स्थान भरिए।',
    match_following: 'सही जोड़ी मिलाइए।', sort_groups: 'इन्हें सही समूह में रखिए।', mcq: 'सही उत्तर चुनिए।' };
  function instrOf(item) {
    var s = item.instruction || '', dev = /[ऀ-ॿ]/;
    var hindi = dev.test(JSON.stringify(item.payload || {})) || dev.test(s) || dev.test(String(item.answer || ''));
    if (hindi && !dev.test(s)) return HI_INSTR[item.type] || s;   // Hindi item, English instruction → Hindi
    return s;
  }

  // A Hindi worksheet was printing English scaffolding ("Circle one:", "Word bank:") around
  // Devanagari questions. The render functions only receive a payload, so the language is
  // detected from the item just before rendering and read back through L().
  var LANG = 'en';
  function L(en, hi) { return LANG === 'hi' ? hi : en; }
  function detectLang(item) {
    var s = JSON.stringify(item && item.payload || '') + String((item && item.instruction) || '');
    return /[\u0900-\u097F]/.test(s) ? 'hi' : 'en';
  }

  function questionBlock(item, i) {
    var q = el('div', 'wp-q');
    var head = el('div');
    head.appendChild(el('span', 'n', String(i + 1)));
    head.appendChild(el('span', 'wp-instr', instrOf(item)));
    q.appendChild(head);
    var body = el('div');
    LANG = detectLang(item);
    (PRINT[item.type] || function (b) { b.appendChild(el('div', 'wp-expr', box())); })(body, item.payload || {});
    q.appendChild(body);
    return q;
  }

  function render(mount, items, opts) {
    opts = opts || {};
    var sheet = el('div', 'wp-sheet');
    var bar = el('div', 'wp-topbar');
    var pb = el('button', 'wp-print', '🖨️ Print worksheet'); pb.onclick = function () { global.print(); };
    bar.appendChild(pb); sheet.appendChild(bar);

    var head = el('div', 'wp-head');
    head.appendChild(el('h1', 'wp-title', opts.title || 'Maths Worksheet'));
    if (opts.subtitle) head.appendChild(el('div', 'wp-sub', opts.subtitle));
    // the sheet-level language comes from the items, since this line is drawn before any of them
    LANG = (items || []).length ? detectLang(items[0]) : 'en';
    head.appendChild(el('div', 'wp-meta', L('Name: <span class="fill"></span> Date: <span class="fill"></span>',
                                            'नाम: <span class="fill"></span> दिनांक: <span class="fill"></span>')));
    sheet.appendChild(head);

    var grid = el('div', 'wp-grid');
    (items || []).forEach(function (it, i) { grid.appendChild(questionBlock(it, i)); });
    sheet.appendChild(grid);
    sheet.appendChild(el('div', 'wp-foot', 'Acharya Kids · practise with pencil & paper ✏️'));

    mount.innerHTML = ''; mount.appendChild(sheet);
    return sheet;
  }

  global.KidsWorksheetPrint = { render: render };
})(window);
