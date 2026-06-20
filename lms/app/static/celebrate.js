/* Shared celebration engine: coin pops, confetti, balloon-burst.
   Usage: celebrate('coin'|'lesson'|'bring'|'week'|'badge', {text}) */
(function () {
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function layer() {
    let l = document.getElementById('fxLayer');
    if (!l) {
      l = document.createElement('div');
      l.id = 'fxLayer';
      l.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:9999;overflow:hidden;';
      document.body.appendChild(l);
    }
    return l;
  }

  const COLORS = ['#5b63e6', '#22c55e', '#f5b301', '#ff6b9d', '#36c5f0', '#a06bff'];

  function confetti(n) {
    const l = layer();
    for (let i = 0; i < n; i++) {
      const c = document.createElement('div');
      const size = 7 + Math.random() * 7;
      c.style.cssText = `position:absolute;top:-20px;left:${Math.random() * 100}%;
        width:${size}px;height:${size * 0.6}px;background:${COLORS[i % COLORS.length]};
        border-radius:2px;opacity:.95;transform:rotate(${Math.random() * 360}deg);`;
      l.appendChild(c);
      const dur = 1100 + Math.random() * 900, drift = (Math.random() - 0.5) * 240;
      c.animate(
        [{ transform: c.style.transform, top: '-20px' },
         { transform: `translateX(${drift}px) rotate(${720 + Math.random() * 360}deg)`, top: '108vh' }],
        { duration: dur, easing: 'cubic-bezier(.2,.6,.4,1)' }
      ).onfinish = () => c.remove();
    }
  }

  function balloons(n) {
    const l = layer();
    for (let i = 0; i < n; i++) {
      const x = 6 + Math.random() * 88;
      const b = document.createElement('div');
      const hue = [263, 142, 45, 330, 199][i % 5];
      b.style.cssText = `position:absolute;bottom:-90px;left:${x}%;width:38px;height:48px;
        background:hsl(${hue} 80% 62%);border-radius:50% 50% 48% 48%;opacity:.96;`;
      const str = document.createElement('div');
      str.style.cssText = 'position:absolute;top:48px;left:50%;width:1px;height:34px;background:rgba(0,0,0,.18);';
      b.appendChild(str);
      l.appendChild(b);
      const rise = 1100 + Math.random() * 700, sway = (Math.random() - 0.5) * 90;
      const a = b.animate(
        [{ bottom: '-90px', transform: 'translateX(0)' },
         { bottom: `${45 + Math.random() * 35}vh`, transform: `translateX(${sway}px)` }],
        { duration: rise, easing: 'ease-out', fill: 'forwards' }
      );
      a.onfinish = () => { pop(b); };
    }
    setTimeout(() => confetti(60), 1300);
  }

  function pop(b) {
    const r = b.getBoundingClientRect();
    b.remove();
    const l = layer();
    for (let i = 0; i < 8; i++) {
      const p = document.createElement('div');
      p.style.cssText = `position:absolute;left:${r.left + r.width / 2}px;top:${r.top + r.height / 2}px;
        width:6px;height:6px;border-radius:50%;background:${COLORS[i % COLORS.length]};`;
      l.appendChild(p);
      const ang = (i / 8) * Math.PI * 2, dist = 40 + Math.random() * 40;
      p.animate(
        [{ transform: 'translate(0,0)', opacity: 1 },
         { transform: `translate(${Math.cos(ang) * dist}px,${Math.sin(ang) * dist}px)`, opacity: 0 }],
        { duration: 500, easing: 'ease-out' }
      ).onfinish = () => p.remove();
    }
  }

  function banner(text) {
    if (!text) return;
    const l = layer();
    const card = document.createElement('div');
    card.style.cssText = `position:absolute;left:50%;top:34%;transform:translate(-50%,-50%) scale(.4);
      background:#fff;border-radius:18px;padding:18px 26px;box-shadow:0 12px 40px rgba(30,30,60,.22);
      font-family:Poppins,sans-serif;font-weight:600;font-size:18px;color:#2b2b33;text-align:center;`;
    card.textContent = text;
    l.appendChild(card);
    card.animate(
      [{ transform: 'translate(-50%,-50%) scale(.4)', opacity: 0 },
       { transform: 'translate(-50%,-50%) scale(1)', opacity: 1, offset: .25 },
       { transform: 'translate(-50%,-50%) scale(1)', opacity: 1, offset: .8 },
       { transform: 'translate(-50%,-50%) scale(.9)', opacity: 0 }],
      { duration: 2200, easing: 'cubic-bezier(.3,1.4,.5,1)' }
    ).onfinish = () => card.remove();
  }

  function coinPop() {
    const l = layer();
    const c = document.createElement('div');
    c.textContent = '🪙';
    c.style.cssText = 'position:absolute;left:50%;top:62%;font-size:30px;transform:translate(-50%,0);';
    l.appendChild(c);
    c.animate([{ transform: 'translate(-50%,0) scale(.6)', opacity: 0 },
               { transform: 'translate(-50%,-60px) scale(1.3)', opacity: 1, offset: .4 },
               { transform: 'translate(-50%,-120px) scale(1)', opacity: 0 }],
      { duration: 900, easing: 'ease-out' }).onfinish = () => c.remove();
  }

  window.celebrate = function (type, payload) {
    payload = payload || {};
    if (reduce) { banner(payload.text); return; }
    if (type === 'coin') coinPop();
    else if (type === 'lesson') { confetti(90); banner(payload.text || 'Lesson complete! 🎉'); }
    else if (type === 'bring') { confetti(70); banner(payload.text || 'Friday-ready! 🚀'); }
    else if (type === 'badge') { confetti(60); banner(payload.text || 'Badge unlocked!'); }
    else if (type === 'week') { balloons(16); banner(payload.text || 'Week complete!'); }
    else confetti(50);
  };
})();
