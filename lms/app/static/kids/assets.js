/* assets.js — KIDS ASSET POOL, runtime resolver.
 *
 * The "fills into worksheets" half of the asset-pooling system. Loads the pool manifest
 * (asset_manifest.json) once, then resolves an asset id → a real generated web asset if it's
 * `ready`, else falls back to the emoji. Worksheet items reference assets by id:
 *
 *     { "asset": "cow" }          // resolves to the generated cow image, or 🐄 until generated
 *     { "emoji": "🍎" }           // still works — plain emoji, no pool lookup
 *
 * So the pool fills in progressively: every worksheet keeps working, and swaps emoji → real art
 * the moment the offline generator (asset_pool.py / gen_assets.py) marks that asset `ready`.
 *
 * Global: window.KidsAssets  (auto-loads the manifest on first use). */
(function (global) {
  'use strict';

  var BASE = '/static/kids/';
  var MANIFEST_URL = BASE + 'asset_manifest.json';
  var manifest = null;
  var loading = null;
  var emojiIndex = {};   // emoji glyph -> asset id (so a raw 🍎 resolves to the apple art)

  function buildIndex() {
    emojiIndex = {};
    var a = (manifest && manifest.assets) || {};
    Object.keys(a).forEach(function (k) { if (a[k].emoji) emojiIndex[a[k].emoji] = k; });
  }

  function load() {
    if (manifest) return Promise.resolve(manifest);
    if (loading) return loading;
    loading = fetch(MANIFEST_URL)
      .then(function (r) { return r.ok ? r.json() : { assets: {} }; })
      .then(function (m) { manifest = m || { assets: {} }; buildIndex(); return manifest; })
      .catch(function () { manifest = { assets: {} }; return manifest; });
    return loading;
  }

  function get(id) { return (manifest && manifest.assets && manifest.assets[id]) || null; }
  function isReady(a) { return a && a.status === 'ready' && a.web && (a.web.anim || a.web.static); }
  function url(a) { return BASE + (a.web.anim || a.web.static); }

  /* Build a DOM node for a token. A token can be:
   *   - an asset id string ("cow")            → generated art if ready, else its emoji
   *   - a raw emoji/text ("🍎", "Cow")         → shown as-is
   *   - {asset:"cow"} or {emoji:"🍎",asset:"cow"} object from an item payload
   * `size` px sets the rendered art height (default 40). */
  function node(token, size) {
    size = size || 40;
    var id = null, emoji = null, text = null;
    if (token && typeof token === 'object') { id = token.asset || null; emoji = token.emoji || null; }
    else if (typeof token === 'string') {
      if (get(token)) id = token;                 // it's a known asset id
      else if (emojiIndex[token]) { id = emojiIndex[token]; emoji = token; }   // a raw emoji → its asset
      else { text = token; }                       // plain text / label
    }
    var a = id ? get(id) : null;
    if (a && isReady(a)) {
      var img = document.createElement('img');
      img.className = 'ka-asset'; img.src = url(a); img.alt = a.label || id;
      img.style.height = size + 'px'; img.style.width = 'auto'; img.style.verticalAlign = 'middle';
      return img;
    }
    var span = document.createElement('span');
    span.className = 'ka-emoji';
    span.textContent = emoji || (a && a.emoji) || text || '❓';
    return span;
  }

  /* Convenience: resolve a token to an inline HTML string (for templating). */
  function html(token, size) {
    var n = node(token, size);
    var wrap = document.createElement('div'); wrap.appendChild(n); return wrap.innerHTML;
  }

  global.KidsAssets = {
    load: load,
    ready: function () { return !!manifest; },
    get: get,
    isReady: function (id) { return isReady(get(id)); },
    node: node,          // → DOM element (art or emoji)
    html: html,          // → HTML string
    // pool stats for a quick on-page badge / debugging
    stats: function () {
      var a = (manifest && manifest.assets) || {}, r = 0, n = 0;
      Object.keys(a).forEach(function (k) { a[k].status === 'ready' ? r++ : n++; });
      return { ready: r, needed: n, total: r + n };
    }
  };

  // warm the manifest immediately (non-blocking)
  load();
})(window);
