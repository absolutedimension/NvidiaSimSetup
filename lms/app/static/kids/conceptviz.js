/* conceptviz.js — portable concept-animation engine (extracted from kids_quiz_live.html /
 * kids_web/viz_test.html so the WORKSHEET can reuse it without editing the quiz template).
 * KEEP IN SYNC with the copy in kids_quiz_live.html. Global: window.ConceptViz.
 * ConceptViz.render(box, q) — q = { q|stem, correct }. First matching detector owns the panel;
 * none match → box gets .hidden (graceful). */
(function () {
  function el(t, c) { var e = document.createElement(t); if (c) e.className = c; return e; }
  function cell(txt, cls) { var c = el('div', 'vcell' + (cls ? ' ' + cls : '')); c.textContent = txt; return c; }
  function cap(box, t) { var c = el('div', 'viz-cap'); c.innerHTML = t; box.appendChild(c); return c; }
  function result(box, html) { var r = el('div', 'viz-result'); r.innerHTML = '&rarr; <span class="n">' + html + '</span>'; box.appendChild(r); setTimeout(function () { r.classList.add('show'); }, 1200); return r; }
  function countUp(node, to, ms) { var t0 = null; function s(t) { t0 = t0 || t; var p = Math.min(1, (t - t0) / ms); node.textContent = Math.round(to * p); if (p < 1) requestAnimationFrame(s); } requestAnimationFrame(s); }
  function nums(s) { return (s.match(/\d+/g) || []).map(Number); }

  function placeValue(box, q, s) {
    var m = s.match(/In\s+(\d[\d,]*)\s*,?\s*what is the\s+(PLACE|FACE)\s+VALUE\s+of the\s+(ones|tens|hundreds|thousands|ten\s*thousands)\s+digit/i);
    if (!m) return false;
    var n = m[1].replace(/,/g, ''), kind = m[2].toUpperCase(), place = m[3].toLowerCase().replace(/\s+/g, ' ');
    var order = ['ones', 'tens', 'hundreds', 'thousands', 'ten thousands'], mult = [1, 10, 100, 1000, 10000];
    var pi = order.indexOf(place); if (pi < 0) return false;
    var digs = n.split(''); var idx = digs.length - 1 - pi; if (idx < 0) return false;
    var digit = parseInt(digs[idx]); var val = (kind === 'FACE') ? digit : digit * mult[pi];
    cap(box, kind === 'FACE' ? ('FACE value = just the digit itself') : ('PLACE value = digit &times; its place'));
    var row = el('div', 'viz-row');
    digs.forEach(function (d, i) { row.appendChild(cell(d, i === idx ? 'hit' : 'dim')); });
    box.appendChild(row);
    result(box, kind === 'FACE' ? String(val) : (digit + ' &times; ' + mult[pi] + ' = ' + val));
    return true;
  }
  function succPred(box, q, s) {
    var m = s.match(/\b(SUCCESSOR|PREDECESSOR)\b\s+of\s+(\d+)/i); if (!m) return false;
    var kind = m[1].toUpperCase(), n = parseInt(m[2]); var ans = kind === 'SUCCESSOR' ? n + 1 : n - 1;
    cap(box, kind === 'SUCCESSOR' ? 'Successor = the number just AFTER (add 1)' : 'Predecessor = the number just BEFORE (take 1)');
    var row = el('div', 'viz-row');
    [n - 1, n, n + 1].forEach(function (v) { row.appendChild(cell(v, v === n ? '' : (v === ans ? 'hit' : 'dim'))); });
    box.appendChild(row); result(box, String(ans)); return true;
  }
  function compareSign(box, q, s) {
    if (!/sign/i.test(s)) return false;
    var m = s.match(/(\d+)\s*(?:_{2,}|_+)\s*(\d+)/); if (!m) return false;
    var a = parseInt(m[1]), b = parseInt(m[2]); var sign = a > b ? '>' : a < b ? '<' : '=';
    cap(box, 'Which is bigger? The open side points to the BIGGER number');
    var row = el('div', 'viz-row'); row.appendChild(cell(a));
    var sc = cell('?', 'op'); row.appendChild(sc); row.appendChild(cell(b)); box.appendChild(row);
    setTimeout(function () { sc.textContent = sign; sc.classList.add('ans'); sc.classList.remove('op'); }, 900);
    result(box, a + ' ' + sign + ' ' + b); return true;
  }
  function orderFirst(box, q, s) {
    var m = s.match(/Arrange in\s+(ascending|descending)\s+order[:\s]+([\d,\s]+?)\.?\s*Which/i); if (!m) return false;
    var asc = /ascending/i.test(m[1]); var list = nums(m[2]); if (list.length < 2) return false;
    var sorted = list.slice().sort(function (x, y) { return asc ? x - y : y - x; });
    cap(box, asc ? 'Ascending = smallest first' : 'Descending = biggest first');
    var row = el('div', 'viz-row'); var cells = list.map(function (v) { var c = cell(v); row.appendChild(c); return c; });
    box.appendChild(row);
    setTimeout(function () { cells.forEach(function (c) { var v = parseInt(c.textContent); if (v === sorted[0]) c.classList.add('hit'); else c.classList.add('dim'); }); }, 900);
    result(box, 'First: ' + sorted[0]); return true;
  }
  function sequence(box, q, s) {
    var m = s.match(/:\s*([\d,\s]+?),\s*\?/); if (!m) return false;
    var seq = nums(m[1]); if (seq.length < 2) return false;
    var step = seq[1] - seq[0]; var nxt = seq[seq.length - 1] + step;
    cap(box, step > 0 ? ('The pattern adds ' + step + ' each time') : ('The pattern changes by ' + step));
    var row = el('div', 'viz-row'); seq.forEach(function (v) { row.appendChild(cell(v)); });
    var qc = cell('?', 'op'); row.appendChild(qc); box.appendChild(row);
    setTimeout(function () { qc.textContent = nxt; qc.classList.remove('op'); qc.classList.add('ans'); }, 900);
    result(box, String(nxt)); return true;
  }
  function formNumber(box, q, s) {
    if (!(/\b(smallest|largest|greatest|biggest)\b/i.test(s) && /\bnumber\b/i.test(s) && /\busing|from|with\b/i.test(s))) return false;
    var mm = s.match(/\b(?:using|from|with)\b\s*(.*)$/i); var tail = (mm ? mm[1] : s).split(/[\(\.]/)[0];
    var digits = (tail.match(/\b\d\b/g) || []).map(Number); if (digits.length < 2 || digits.length > 6) return false;
    var largest = /\b(largest|greatest|biggest)\b/i.test(s); var sorted = digits.slice().sort(function (a, b) { return largest ? b - a : a - b; });
    cap(box, largest ? 'Biggest number &rarr; put the BIGGEST digit first!' : 'Smallest number &rarr; put the SMALLEST digit first!');
    var stage = el('div', 'viz-stage'), step = 56; stage.style.width = (step * digits.length) + 'px';
    var tiles = digits.map(function (d, i) { var t = el('div', 'vtile'); t.textContent = d; t.style.transform = 'translateX(' + (i * step) + 'px)'; stage.appendChild(t); return t; });
    box.appendChild(stage);
    var used = {};
    setTimeout(function () { tiles.forEach(function (t) { var d = parseInt(t.textContent); var pos = sorted.indexOf(d, used[d] || 0); used[d] = pos + 1; t.style.transform = 'translateX(' + (pos * step) + 'px)'; if (pos === 0) t.classList.add('lead'); }); }, 650);
    result(box, sorted.join('')); return true;
  }
  function arithmetic(box, q, s) {
    var t = s.replace(/₹/g, '').replace(/[−–]/g, '-').replace(/×/g, 'x').replace(/÷/g, '/');
    var m = t.match(/(-?\d+)\s*([+\-x\/])\s*(-?\d+)(?:\s*([+\-x\/])\s*(-?\d+))?\s*=/);
    if (!m) return false;
    var money = /₹/.test(s);
    function ap(acc, op, v) { return op === '+' ? acc + v : op === '-' ? acc - v : op === 'x' ? acc * v : Math.round(acc / v); }
    var res = parseInt(m[1]); res = ap(res, m[2], parseInt(m[3])); if (m[4]) res = ap(res, m[4], parseInt(m[5]));
    var pre = money ? '₹' : '';
    var capTxt = { '+': 'Put them together and count!', '-': 'Take away, then count what is left', 'x': 'Equal groups added up', '/': 'Share equally into groups' }[m[2]] || 'Let’s work it out!';
    cap(box, capTxt);
    var row = el('div', 'viz-row');
    row.appendChild(cell(pre + m[1])); row.appendChild(cell(m[2] === 'x' ? '×' : m[2] === '/' ? '÷' : m[2], 'op')); row.appendChild(cell(pre + m[3]));
    if (m[4]) { row.appendChild(cell(m[4] === 'x' ? '×' : m[4] === '/' ? '÷' : m[4], 'op')); row.appendChild(cell(pre + m[5])); }
    row.appendChild(cell('=', 'op'));
    var ansc = cell(pre + '0', 'ans'); row.appendChild(ansc); box.appendChild(row);
    setTimeout(function () { if (money) ansc.textContent = '₹' + res; else countUp(ansc, res, 700); }, 700);
    return true;
  }
  function expandedForm(box, q, s) {
    var m = s.match(/write the number\s*:?\s*([\d\s+]+?)\s*=/i); if (!m) return false;
    var parts = (m[1].match(/\d+/g) || []).map(Number); if (parts.length < 2) return false;
    var sum = parts.reduce(function (a, b) { return a + b; }, 0);
    cap(box, 'Add each place value to build the number');
    var row = el('div', 'viz-row');
    parts.forEach(function (p, i) { row.appendChild(cell(p)); if (i < parts.length - 1) row.appendChild(cell('+', 'op')); });
    row.appendChild(cell('=', 'op')); var a = cell('0', 'ans'); row.appendChild(a); box.appendChild(row);
    setTimeout(function () { countUp(a, sum, 700); }, 700); return true;
  }
  function estimateRound(box, q, s) {
    var sum = /estimate the sum/i.test(s), diff = /estimate the difference/i.test(s); if (!sum && !diff) return false;
    var m = s.match(/(\d+)\s*[+\-−]\s*(\d+)/); if (!m) return false;
    var a = parseInt(m[1]), b = parseInt(m[2]), ra = Math.round(a / 10) * 10, rb = Math.round(b / 10) * 10, est = sum ? ra + rb : ra - rb;
    cap(box, 'Round to the nearest 10:  ' + a + '&rarr;' + ra + ',  ' + b + '&rarr;' + rb);
    var row = el('div', 'viz-row'); row.appendChild(cell(ra, 'hit')); row.appendChild(cell(sum ? '+' : '−', 'op')); row.appendChild(cell(rb, 'hit'));
    row.appendChild(cell('=', 'op')); var ac = cell('0', 'ans'); row.appendChild(ac); box.appendChild(row);
    setTimeout(function () { countUp(ac, est, 700); }, 700); return true;
  }
  function missingBox(box, q, s) {
    var m = s.match(/(\d+|_{2,})\s*([+\-−])\s*(\d+|_{2,})\s*=\s*(\d+)/); if (!m) return false;
    var op = m[2].replace('−', '-'), L = m[1], R = m[3], tot = parseInt(m[4]), missL = /_/.test(L), missR = /_/.test(R);
    if (!missL && !missR) return false; var known = parseInt(missL ? R : L);
    var ans = op === '+' ? tot - known : (missL ? tot + known : known - tot);
    cap(box, 'Find the missing number that makes it true');
    var row = el('div', 'viz-row');
    var lc = cell(missL ? '?' : L, missL ? 'ans' : ''); row.appendChild(lc); row.appendChild(cell(op, 'op'));
    var rc = cell(missR ? '?' : R, missR ? 'ans' : ''); row.appendChild(rc); row.appendChild(cell('=', 'op')); row.appendChild(cell(tot)); box.appendChild(row);
    setTimeout(function () { (missL ? lc : rc).textContent = ans; }, 900); result(box, String(ans)); return true;
  }
  function numberName(box, q, s) {
    var m = s.match(/which number is\s*['"]([^'"]+)['"]/i); if (!m) return false;
    var ans = (q && q.correct) ? String(q.correct).replace(/[^\d]/g, '') : '';
    cap(box, 'Read the number name, then write the digits');
    var row = el('div', 'viz-row'); var nc = el('div', 'vcell'); nc.style.fontSize = '15px'; nc.style.minWidth = 'auto'; nc.textContent = m[1]; row.appendChild(nc);
    row.appendChild(cell('=', 'op')); row.appendChild(cell(ans || '?', 'ans')); box.appendChild(row);
    result(box, ans || m[1]); return true;
  }
  function wordProblem(box, q, s) {
    if (!/how many/i.test(s)) return false; var ns = nums(s); if (ns.length !== 2) return false;
    var sub = /(left|remain|fewer|spent|gave away|lost|how many more)/i.test(s), add = /(in all|altogether|in total|combined)/i.test(s);
    if (!add && !sub) return false;
    var x = sub ? Math.max(ns[0], ns[1]) : ns[0], y = sub ? Math.min(ns[0], ns[1]) : ns[1], res = sub ? x - y : x + y;
    cap(box, sub ? '&ldquo;how many left&rdquo; &rarr; SUBTRACT' : '&ldquo;in all&rdquo; &rarr; ADD them together');
    var row = el('div', 'viz-row'); row.appendChild(cell(x)); row.appendChild(cell(sub ? '−' : '+', 'op')); row.appendChild(cell(y));
    row.appendChild(cell('=', 'op')); var ac = cell('0', 'ans'); row.appendChild(ac); box.appendChild(row);
    setTimeout(function () { countUp(ac, res, 700); }, 700); return true;
  }

  var DETECTORS = [placeValue, succPred, compareSign, orderFirst, sequence, formNumber, expandedForm, estimateRound, missingBox, numberName, arithmetic, wordProblem];
  window.ConceptViz = {
    render: function (box, q) {
      var s = (q && (q.q || q.stem)) || '';
      for (var i = 0; i < DETECTORS.length; i++) { box.classList.remove('hidden'); box.innerHTML = ''; try { if (DETECTORS[i](box, q, s)) return true; } catch (e) {} }
      box.classList.add('hidden'); box.innerHTML = ''; return false;
    }
  };
})();
