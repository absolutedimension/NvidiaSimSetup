/* kids_voice.js — child-voice layer for the KIDS pool-driven test (assess.html).
 *
 * Decoupled: it does NOT touch assess.html's logic. It watches #log for each MCQ card the
 * shared pool renders, then speaks the question + options with the edge-tts child voice
 * (/kids/tts, en-US-AnaNeural), and lets the kid TAP or SPEAK the answer. Data + pool are the
 * common acharya path; this only adds the voice/kid experience. No-op unless window.__KIDS. */
(function () {
  if (!window.__KIDS) return;

  var VOICE_KEY = 'kidsVoiceOn';
  var voiceOn = localStorage.getItem(VOICE_KEY) !== '0';   // default ON
  var audio = null;          // current TTS <audio>
  var lastCard = null;       // dedupe: speak each question once

  /* ---- turn a maths stem into something a child voice reads naturally ---- */
  function speakable(s) {
    return (s || '')
      .replace(/₹/g, ' rupees ')          // ₹
      .replace(/×/g, ' times ')           // ×
      .replace(/÷/g, ' divided by ')      // ÷
      .replace(/[−]/g, ' minus ')         // −
      .replace(/ - /g, ' minus ')              // spaced hyphen = subtraction (keep "3-digit")
      .replace(/=/g, ' equals ')
      .replace(/\+/g, ' plus ')
      .replace(/>/g, ' is greater than ')
      .replace(/</g, ' is less than ')
      .replace(/%/g, ' percent ')
      .replace(/_{2,}/g, ' what ')
      .replace(/\?/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  var LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

  function stop() { if (audio) { try { audio.pause(); } catch (e) {} audio = null; } }

  function play(text) {
    stop();
    if (!text) return;
    audio = new Audio('/kids/tts?text=' + encodeURIComponent(text.slice(0, 580)));
    audio.play().catch(function () {/* autoplay blocked until a tap — ignore */});
  }

  function readCard(card) {
    var qt = card.querySelector('.qtext');
    var opts = [].slice.call(card.querySelectorAll('.opt'));
    if (!qt) return;
    var say = speakable(qt.textContent) + '. ';
    if (opts.length) {
      say += 'Your choices are. ';
      opts.forEach(function (b, i) {
        var span = b.querySelector('span:last-child');
        var txt = span ? span.textContent : b.textContent;
        say += LETTERS[i] + '. ' + speakable(txt) + '. ';
      });
    }
    if (voiceOn) play(say);
  }

  /* ---- speak-your-answer (browser speech recognition → click the option) ---- */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  function listen() {
    if (!SR) { alert('Speaking needs Chrome. You can tap your answer! 👆'); return; }
    var card = currentCard();
    if (!card) return;
    stop();
    var rec = new SR();
    rec.lang = 'en-IN'; rec.interimResults = false; rec.maxAlternatives = 3;
    setMic('🎙️ Listening…');
    rec.onresult = function (e) {
      var heard = (e.results[0][0].transcript || '').toLowerCase().trim();
      pickFromSpeech(card, heard);
    };
    rec.onerror = function () { setMic('🎤 Speak'); };
    rec.onend = function () { setMic('🎤 Speak'); };
    try { rec.start(); } catch (e) { setMic('🎤 Speak'); }
  }

  function pickFromSpeech(card, heard) {
    var opts = [].slice.call(card.querySelectorAll('.opt'));
    if (!opts.length) return;
    var letterMap = { a: 0, ay: 0, hey: 0, eh: 0, b: 1, bee: 1, be: 1, c: 2, cee: 2, see: 2, sea: 2, d: 3, dee: 3, the: 3 };
    var posMap = { first: 0, second: 1, third: 2, fourth: 3, one: 0, two: 1, three: 2, four: 3 };
    var idx = -1;
    var words = heard.split(/[^a-z0-9]+/).filter(Boolean);
    // 1) explicit letter/position word
    for (var i = 0; i < words.length && idx < 0; i++) {
      if (words[i] in letterMap) idx = letterMap[words[i]];
      else if (words[i] in posMap) idx = posMap[words[i]];
    }
    // 2) match the spoken NUMBER to an option's numeric value
    if (idx < 0) {
      var nums = (heard.match(/\d+/g) || []).map(Number);
      if (nums.length) {
        opts.forEach(function (b, i) {
          var span = b.querySelector('span:last-child');
          var v = parseInt((span ? span.textContent : b.textContent).replace(/[^0-9]/g, ''), 10);
          if (!isNaN(v) && nums.indexOf(v) >= 0) idx = i;
        });
      }
    }
    if (idx >= 0 && opts[idx]) { opts[idx].click(); }
    else if (voiceOn) { play("I didn't catch that. Try again, or tap your answer!"); }
  }

  function currentCard() {
    var cards = document.querySelectorAll('#log .qcard');
    for (var i = cards.length - 1; i >= 0; i--) {
      if (cards[i].querySelector('.opt')) return cards[i];
    }
    return null;
  }

  /* ---- floating kid control bar ---- */
  var micBtn;
  function setMic(t) { if (micBtn) micBtn.textContent = t; }
  function buildBar() {
    var bar = document.createElement('div');
    bar.className = 'kv-bar';
    bar.innerHTML =
      '<img class="kv-m" src="/static/kids/jj.png" alt="JJ">' +
      '<button class="kv-btn kv-toggle"></button>' +
      '<button class="kv-btn kv-replay">🔊 Hear again</button>' +
      '<button class="kv-btn kv-mic">🎤 Speak</button>' +
      '<img class="kv-m" src="/static/kids/mikey.png" alt="Mikey">';
    document.body.appendChild(bar);
    var toggle = bar.querySelector('.kv-toggle');
    micBtn = bar.querySelector('.kv-mic');
    function paintToggle() { toggle.textContent = voiceOn ? '🔈 Voice ON' : '🔇 Voice OFF'; toggle.classList.toggle('off', !voiceOn); }
    paintToggle();
    toggle.onclick = function () {
      voiceOn = !voiceOn; localStorage.setItem(VOICE_KEY, voiceOn ? '1' : '0'); paintToggle();
      if (!voiceOn) stop(); else { var c = currentCard(); if (c) readCard(c); }
    };
    bar.querySelector('.kv-replay').onclick = function () { var c = currentCard(); if (c) { var was = voiceOn; voiceOn = true; readCard(c); voiceOn = was; } };
    micBtn.onclick = listen;
  }

  /* ---- watch the pool render each question, then speak it ---- */
  function watch() {
    var log = document.getElementById('log');
    if (!log) { setTimeout(watch, 200); return; }
    var obs = new MutationObserver(function () {
      var card = currentCard();
      if (card && card !== lastCard) { lastCard = card; setTimeout(function () { readCard(card); }, 250); }
    });
    obs.observe(log, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { buildBar(); watch(); });
  else { buildBar(); watch(); }
})();
