/* worksheet_viz.js — bridges a WORKSHEET item → the concept-animation engine (ConceptViz).
 * ConceptViz matches on a question STEM string; worksheet items are {type,payload,answer}, so
 * this synthesizes the stem the detectors expect and mounts the animation in the #viz slot.
 * Numeric concepts animate (arith, compare, before/after, money, numeric patterns); the rest
 * hide gracefully (the worksheet itself already shows them). Global: KidsWorksheetViz. */
(function (g) {
  'use strict';

  function stemFor(item) {
    var p = item.payload || {}, t = item.type;
    if (t === 'arith') return p.a + ' ' + (p.op || '+') + ' ' + p.b + ' = ?';
    if (t === 'compare_symbol') return 'Fill in the correct sign: ' + p.a + ' ___ ' + p.b;
    if (t === 'neighbour_number') return 'What is the ' + (p.mode === 'before' ? 'PREDECESSOR' : 'SUCCESSOR') + ' of ' + p.n + '?';
    if (t === 'count_money') return (p.coins || []).map(function (c) { return '₹' + c; }).join(' + ') + ' = ?';
    if (t === 'pattern_next') {
      var seq = p.seq || [];
      var allNum = seq.length >= 2 && seq.every(function (x) { return /^\d+$/.test(String(x)); });
      return allNum ? ('pattern: ' + seq.join(', ') + ', ?') : '';
    }
    return '';  // count_write / fill_sequence / match / trace… → no concept animation (graceful)
  }

  g.KidsWorksheetViz = {
    show: function (box, item) {
      if (!box) return false;
      if (!g.ConceptViz) { box.classList.add('hidden'); return false; }
      var stem = stemFor(item);
      if (!stem) { box.classList.add('hidden'); box.innerHTML = ''; return false; }
      return g.ConceptViz.render(box, { q: stem, correct: item.answer });
    }
  };
})(window);
