import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// TrigunAI RTX Variant Studio
// Browser front-end for the EC2 OVRTX render proxy (viewer-backend/render_proxy.py).
// Pick a USD showcase, flip its authored variant sets (carpaint, wheels, decals,
// lights…), choose an angle + quality, get a photoreal RTX frame back.
// Endpoint: set it in the panel, or open #/viewer?api=https://your-host
// ─────────────────────────────────────────────────────────────────────────────

const GOLD = '#f4c14b';
const NV = '#76b900';
const LS_KEY = 'trigunai_viewer_api';

// variant option name → swatch colour (best-effort; non-colours fall back to chips)
const COLORS: Record<string, string> = {
  Black: '#1a1a1d', Blue: '#1d4ed8', Dark_Grey: '#4b5563', Green: '#15803d',
  Nvidia_Green: NV, Olive: '#5b6b2f', Orange: '#ea580c', Red: '#d61f26',
  Silver: '#cbd5e1', Tan: '#d2b48c', White: '#f1f5f9', Wine_Blue: '#34306b',
  Blue_Chroma: '#2563eb', Carbon_Fiber: '#26292e', Gold: '#d4af37',
  Red_Chroma: '#ef4444', Rose_Gold: '#b76e79', Yellow: '#eab308', Metal: '#9ca3af',
  Rose: '#b76e79', Dark_Metal: '#374151', Full_Color: NV, Cyan: '#06b6d4',
  Magenta: '#d946ef', Light_Blue: '#7dd3fc', Pink: '#ec4899', Noir: '#0a0a0a',
  Mocha: '#6f4e37', Cream_Cappuccino: '#e7d3b3', Blue_Shock: '#1e90ff',
  Red_Sport: '#b91c1c', Red_Velvet: '#7f1d1d', Warm_Leather: '#a0522d',
  Yellow_Sport: '#facc15', Orange_Black: '#c2410c',
};

type VSet = { id: string; prim: string; set: string; current: string; options: string[] };
type Scan = {
  id: string; label: string; variant_sets: VSet[]; cameras: string[];
  center: number[]; size: number; suggest_dist: number;
  hero: { az: number; el: number; focal: number }; has_variants: boolean;
};
type AssetMeta = { id: string; label: string; available: boolean };

const PRESETS: Record<string, { az: number; el: number }> = {
  Hero: { az: 40, el: 8 }, Front: { az: 0, el: 6 }, Side: { az: 90, el: 4 },
  Rear: { az: 200, el: 10 }, Top: { az: 35, el: 55 },
};

function readApi(): string {
  const q = new URLSearchParams(window.location.hash.split('?')[1] || '');
  return q.get('api') || localStorage.getItem(LS_KEY) || '';
}
const pretty = (s: string) => s.replace(/_Variant$/, '').replace(/_/g, ' ');

export default function Viewer() {
  const [api, setApi] = useState(readApi);
  const [assets, setAssets] = useState<AssetMeta[]>([]);
  const [assetId, setAssetId] = useState('ragnarok');
  const [scan, setScan] = useState<Scan | null>(null);
  const [sel, setSel] = useState<Record<string, string>>({});
  const [ovrtx, setOvrtx] = useState<boolean | null>(null);

  const [az, setAz] = useState(40);
  const [el, setEl] = useState(8);
  const [dist, setDist] = useState(1000);
  const [focal, setFocal] = useState(35);
  const [quality, setQuality] = useState<'rt' | 'pt'>('rt');
  const [res, setRes] = useState({ w: 1280, h: 720 });

  const [frame, setFrame] = useState('');
  const [busy, setBusy] = useState(false);
  const [renderMs, setRenderMs] = useState<number | null>(null);
  const [err, setErr] = useState('');
  const [spin, setSpin] = useState(false);

  // grid / cut-sheet
  const [mode, setMode] = useState<'single' | 'grid'>('single');
  const [sweepId, setSweepId] = useState('');
  const [cells, setCells] = useState<{ option: string; png: string }[]>([]);
  const [gridBusy, setGridBusy] = useState(false);
  const [gridProg, setGridProg] = useState({ done: 0, total: 0 });
  const gridCancel = useRef(false);

  const base = api.replace(/\/$/, '');
  const drag = useRef<{ x: number; y: number } | null>(null);
  const reqId = useRef(0);
  const debounce = useRef<number | null>(null);

  // ── connect + load an asset's variant schema ───────────────────────────────
  const loadAsset = useCallback(async (b: string, id: string) => {
    setErr('');
    try {
      const h = await fetch(`${b}/viewer/health`).then((r) => r.json());
      setOvrtx(!!h.ovrtx);
      fetch(`${b}/viewer/assets`).then((r) => r.json()).then((a) => setAssets(a.assets || [])).catch(() => {});
      const s: Scan = await fetch(`${b}/viewer/scan?asset=${id}`).then((r) => r.json());
      setScan(s);
      const initial: Record<string, string> = {};
      s.variant_sets.forEach((v) => { initial[v.id] = v.current; });
      setSel(initial);
      setAz(s.hero.az); setEl(s.hero.el); setFocal(s.hero.focal);
      setDist(Math.round(s.suggest_dist));
      const carpaint = s.variant_sets.find((v) => v.set.includes('Carpaint_Color'));
      setSweepId(carpaint?.id || s.variant_sets[0]?.id || '');
      setCells([]); setMode('single');
    } catch {
      setOvrtx(null); setScan(null);
      setErr('Could not reach the studio API. Is the EC2 proxy up?');
    }
  }, []);

  const connect = () => { localStorage.setItem(LS_KEY, api); loadAsset(base, assetId); };
  useEffect(() => { if (base) loadAsset(base, assetId); /* eslint-disable-next-line */ }, []);
  useEffect(() => { if (base) loadAsset(base, assetId); /* eslint-disable-next-line */ }, [assetId]);

  // ── render the current configuration ───────────────────────────────────────
  const render = useCallback(async () => {
    if (!base || !scan) return;
    const id = ++reqId.current;
    setBusy(true); setErr('');
    try {
      const r = await fetch(`${base}/viewer/render`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset: assetId, variants: sel, az, el, dist, focal,
          width: res.w, height: res.h, samples: quality === 'pt' ? 128 : 24,
        }),
      });
      if (!r.ok) throw new Error((await r.json()).detail || `HTTP ${r.status}`);
      const d = await r.json();
      if (id === reqId.current) { setFrame(d.png); setRenderMs(d.render_ms); }
    } catch (e) {
      if (id === reqId.current) setErr(String((e as Error).message));
    } finally {
      if (id === reqId.current) setBusy(false);
    }
  }, [base, scan, assetId, sel, az, el, dist, focal, res, quality]);

  // auto-render (debounced) whenever the configuration settles — single mode only
  useEffect(() => {
    if (!base || !scan || mode !== 'single') return;
    if (debounce.current) window.clearTimeout(debounce.current);
    debounce.current = window.setTimeout(render, 350);
    return () => { if (debounce.current) window.clearTimeout(debounce.current); };
  }, [sel, az, el, dist, focal, res, quality, render, base, scan, mode]);

  // turntable: advance azimuth after each render settles
  useEffect(() => {
    if (!spin || busy) return;
    const t = window.setTimeout(() => setAz((a) => (a + 30) % 360), 400);
    return () => window.clearTimeout(t);
  }, [spin, busy, frame]);

  // ── orbit controls (render fires on settle via the debounce) ───────────────
  const onDown = (e: React.PointerEvent) => {
    drag.current = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId); setSpin(false);
  };
  const onMove = (e: React.PointerEvent) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x, dy = e.clientY - drag.current.y;
    drag.current = { x: e.clientX, y: e.clientY };
    setAz((a) => (a + dx * 0.3 + 360) % 360);
    setEl((v) => Math.max(-20, Math.min(80, v - dy * 0.3)));
  };
  const onUp = () => { drag.current = null; };
  const onWheel = (e: React.WheelEvent) =>
    setDist((d) => Math.max(scan ? scan.size * 0.6 : 50, Math.min((scan?.size || 100) * 6, d * (1 + e.deltaY * 0.0012))));

  const download = () => {
    if (!frame) return;
    const a = document.createElement('a');
    a.href = frame; a.download = `trigunai_${assetId}_${Date.now()}.png`; a.click();
  };

  // ── grid sweep: render each option of the chosen set, holding the rest fixed ─
  const sweepSet = useMemo(() => scan?.variant_sets.find((v) => v.id === sweepId), [scan, sweepId]);
  const renderGrid = useCallback(async () => {
    if (!base || !scan || !sweepSet) return;
    setMode('grid'); setCells([]); setErr(''); gridCancel.current = false;
    const opts = sweepSet.options;
    setGridBusy(true); setGridProg({ done: 0, total: opts.length });
    const out: { option: string; png: string }[] = [];
    for (let i = 0; i < opts.length; i++) {
      if (gridCancel.current) break;
      try {
        const r = await fetch(`${base}/viewer/render`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            asset: assetId, variants: { ...sel, [sweepId]: opts[i] },
            az, el, dist, focal, width: res.w, height: res.h,
            samples: quality === 'pt' ? 128 : 24,
          }),
        });
        if (r.ok) { const d = await r.json(); out.push({ option: opts[i], png: d.png }); setCells([...out]); }
      } catch { /* skip a failed cell */ }
      setGridProg({ done: i + 1, total: opts.length });
    }
    setGridBusy(false);
  }, [base, scan, sweepSet, sweepId, assetId, sel, az, el, dist, focal, res, quality]);

  // compose the labeled cut sheet on a canvas and download it
  const makeCutSheet = useCallback(async () => {
    if (!cells.length || !scan || !sweepSet) return;
    const cols = Math.min(cells.length, Math.ceil(Math.sqrt(cells.length)));
    const rows = Math.ceil(cells.length / cols);
    const cw = 480, ch = 270, pad = 12, lab = 30, title = 56;
    const W = cols * cw + (cols + 1) * pad;
    const H = title + rows * (ch + lab) + (rows + 1) * pad;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const x = cv.getContext('2d')!;
    x.fillStyle = '#0a0a0b'; x.fillRect(0, 0, W, H);
    x.fillStyle = GOLD; x.font = 'bold 24px sans-serif';
    x.fillText(`${scan.label} — ${pretty(sweepSet.set)}`, pad, 36);
    x.fillStyle = '#ffffff66'; x.font = '13px sans-serif';
    x.fillText('TrigunAI · RTX Variant Studio · OVRTX / OpenUSD', W - 360, 36);
    await Promise.all(cells.map((cell, i) => new Promise<void>((res) => {
      const img = new Image();
      img.onload = () => {
        const col = i % cols, row = Math.floor(i / cols);
        const px = pad + col * (cw + pad), py = title + pad + row * (ch + lab + pad);
        x.fillStyle = '#000'; x.fillRect(px, py, cw, ch);
        x.drawImage(img, px, py, cw, ch);
        x.fillStyle = '#16161a'; x.fillRect(px, py + ch, cw, lab);
        x.fillStyle = '#fff'; x.font = '15px sans-serif';
        x.fillText(cell.option.replace(/_/g, ' '), px + 10, py + ch + 20);
        res();
      };
      img.src = cell.png;
    })));
    const a = document.createElement('a');
    a.href = cv.toDataURL('image/png'); a.download = `cutsheet_${assetId}_${sweepSet.set}.png`; a.click();
  }, [cells, scan, sweepSet, assetId]);

  const colorSets = useMemo(() => new Set(
    (scan?.variant_sets || []).filter((v) => v.options.every((o) => COLORS[o])).map((v) => v.id)
  ), [scan]);

  return (
    <div className="min-h-screen w-full bg-[#0a0a0b] text-white">
      {/* header */}
      <nav className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-black/70 px-5 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          <a href="#/" className="text-sm text-white/60 hover:text-white">← TrigunAI</a>
          <span className="h-4 w-px bg-white/15" />
          <span className="text-sm font-semibold tracking-wide">RTX Variant Studio</span>
          {scan && <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-white/50">{scan.label}</span>}
        </div>
        <div className="flex items-center gap-4 text-xs">
          {renderMs !== null && <span className="font-mono text-white/45">{(renderMs / 1000).toFixed(1)}s / frame</span>}
          <span className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${ovrtx ? 'bg-[#76b900]' : ovrtx === false ? 'bg-yellow-400' : 'bg-red-500'}`} />
            {ovrtx ? 'OVRTX live' : ovrtx === false ? 'proxy up' : 'offline'}
          </span>
        </div>
      </nav>

      <div className="mx-auto grid max-w-[1500px] gap-5 p-5 lg:grid-cols-[1fr_330px]">
        {/* ── viewport ── */}
        <div>
          {/* mode tabs */}
          <div className="mb-3 flex flex-wrap items-center gap-2">
            {(['single', 'grid'] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition ${mode === m ? 'text-black' : 'bg-white/5 text-white/60 hover:bg-white/10'}`}
                style={mode === m ? { background: GOLD } : {}}>{m === 'grid' ? 'Grid / Cut Sheet' : 'Single'}</button>
            ))}
            {mode === 'grid' && (
              <div className="ml-auto flex items-center gap-2 text-xs">
                {gridBusy && <span className="font-mono text-white/50">{gridProg.done}/{gridProg.total}</span>}
                {gridBusy
                  ? <button onClick={() => { gridCancel.current = true; }} className="rounded-md bg-white/10 px-2.5 py-1 text-white/70 hover:bg-white/20">Stop</button>
                  : <button onClick={renderGrid} disabled={!sweepSet} className="rounded-md px-2.5 py-1 font-semibold text-black disabled:opacity-40" style={{ background: NV }}>Render Grid</button>}
                <button onClick={makeCutSheet} disabled={!cells.length} className="rounded-md bg-white/10 px-2.5 py-1 text-white/80 hover:bg-white/20 disabled:opacity-40">⤓ Cut Sheet</button>
              </div>
            )}
          </div>

          {mode === 'single' && (
          <div
            className="relative aspect-video w-full select-none overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-[#141416] to-[#070708]"
            style={{ cursor: drag.current ? 'grabbing' : 'grab' }}
            onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={onUp} onWheel={onWheel}
          >
            {frame ? (
              <img src={frame} alt="RTX render" className="h-full w-full object-contain transition-opacity duration-300" draggable={false} />
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-white/40">
                <div className="text-5xl">🏎️</div>
                <p className="text-sm">{base ? 'Loading studio…' : 'Set the studio API on the right →'}</p>
              </div>
            )}

            {/* tech badges */}
            <div className="pointer-events-none absolute left-3 top-3 flex gap-1.5">
              {['OpenUSD', 'RTX', 'OVRTX', 'A10G'].map((t) => (
                <span key={t} className="rounded bg-black/55 px-2 py-0.5 text-[10px] font-medium text-white/55 backdrop-blur">{t}</span>
              ))}
            </div>
            {busy && (
              <div className="absolute right-3 top-3 flex items-center gap-2 rounded-full bg-black/70 px-3 py-1 text-xs backdrop-blur" style={{ color: GOLD }}>
                <span className="h-2 w-2 animate-ping rounded-full" style={{ background: GOLD }} /> rendering…
              </div>
            )}
            <div className="pointer-events-none absolute bottom-3 left-3 rounded bg-black/55 px-2 py-1 font-mono text-[11px] text-white/55 backdrop-blur">
              az {az.toFixed(0)}°  el {el.toFixed(0)}°  d {Math.round(dist)}
            </div>

            {/* floating control bar */}
            <div className="absolute bottom-3 right-3 flex flex-wrap items-center justify-end gap-1.5">
              {Object.keys(PRESETS).map((p) => (
                <button key={p} onClick={() => { setSpin(false); setAz(PRESETS[p].az); setEl(PRESETS[p].el); }}
                  className="rounded-md bg-black/55 px-2.5 py-1 text-[11px] text-white/70 backdrop-blur transition hover:bg-white/15">{p}</button>
              ))}
              <button onClick={() => setSpin((s) => !s)}
                className={`rounded-md px-2.5 py-1 text-[11px] backdrop-blur transition ${spin ? 'text-black' : 'bg-black/55 text-white/70 hover:bg-white/15'}`}
                style={spin ? { background: GOLD } : {}}>↻ Turntable</button>
              <button onClick={download} disabled={!frame}
                className="rounded-md bg-black/55 px-2.5 py-1 text-[11px] text-white/70 backdrop-blur transition hover:bg-white/15 disabled:opacity-40">⤓ Save</button>
            </div>
          </div>
          )}

          {mode === 'grid' && (
            <div className="rounded-2xl border border-white/10 bg-[#070708] p-3">
              {cells.length === 0 && !gridBusy && (
                <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-white/40">
                  <div className="text-4xl">▦</div>
                  <p className="text-sm">Sweep <span className="text-white/70">{sweepSet ? pretty(sweepSet.set) : 'a variant set'}</span> — render every option into one labeled sheet.</p>
                  <p className="text-xs text-white/30">{sweepSet?.options.length || 0} options · ~{Math.round((sweepSet?.options.length || 0) * 18)}s total</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {cells.map((c) => (
                  <figure key={c.option} className="overflow-hidden rounded-lg border border-white/10 bg-black">
                    <img src={c.png} alt={c.option} className="aspect-video w-full object-contain" />
                    <figcaption className="truncate bg-white/[0.04] px-2 py-1 text-[11px] text-white/70">{c.option.replace(/_/g, ' ')}</figcaption>
                  </figure>
                ))}
                {gridBusy && Array.from({ length: Math.max(0, gridProg.total - cells.length) }).slice(0, 6).map((_, i) => (
                  <div key={i} className="flex aspect-video items-center justify-center rounded-lg border border-white/5 bg-white/[0.02] text-xs text-white/30">
                    {i === 0 ? 'rendering…' : 'queued'}
                  </div>
                ))}
              </div>
            </div>
          )}

          {err && <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">{err}</p>}
          <p className="mt-3 text-xs leading-relaxed text-white/40">
            Photoreal RTX rendered live on a single NVIDIA A10G via <span className="text-white/60">OVRTX</span>. Variant selections compose
            in an OpenUSD overlay layer; each change re-renders one frame. Drag to orbit · scroll to zoom.
          </p>
        </div>

        {/* ── config panel ── */}
        <aside className="space-y-5 text-sm">
          {/* asset + endpoint */}
          <Panel title="Asset">
            <select value={assetId} onChange={(e) => setAssetId(e.target.value)} className="w-full rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 text-xs outline-none focus:border-white/40">
              {assets.length === 0 && <option value="ragnarok">Koenigsegg Ragnarok</option>}
              {assets.map((a) => <option key={a.id} value={a.id} disabled={!a.available} className="bg-neutral-900">{a.label}{a.available ? '' : ' (offline)'}</option>)}
            </select>
            <div className="mt-2 flex gap-2">
              <input value={api} onChange={(e) => setApi(e.target.value)} placeholder="https://…trycloudflare.com or http://localhost:8010"
                className="min-w-0 flex-1 rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 text-[11px] outline-none focus:border-white/40" />
              <button onClick={connect} className="rounded-lg px-3 py-1.5 text-xs font-semibold text-black" style={{ background: GOLD }}>Set</button>
            </div>
          </Panel>

          {/* quality */}
          <Panel title="Quality & Output">
            <div className="grid grid-cols-2 gap-1.5">
              <Seg active={quality === 'rt'} onClick={() => setQuality('rt')} label="Real-Time" />
              <Seg active={quality === 'pt'} onClick={() => setQuality('pt')} label="Path Tracing" />
            </div>
            <div className="mt-2">
              <label className="mb-1 block text-[10px] uppercase tracking-wide text-white/40">Resolution</label>
              <select value={`${res.w}x${res.h}`} onChange={(e) => { const [w, h] = e.target.value.split('x').map(Number); setRes({ w, h }); }}
                className="w-full rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 text-xs outline-none focus:border-white/40">
                {['960x540', '1280x720', '1600x900', '1920x1080'].map((r) => <option key={r} value={r} className="bg-neutral-900">{r}</option>)}
              </select>
            </div>
          </Panel>

          {/* variant sets */}
          {scan?.has_variants && (
            <Panel title={`Variants · ${scan.variant_sets.length}`}>
              <div className="max-h-[42vh] space-y-3 overflow-y-auto pr-1">
                {scan.variant_sets.map((v) => (
                  <div key={v.id}>
                    <label className="mb-1 block text-[10px] uppercase tracking-wide text-white/40">{pretty(v.set)}</label>
                    {colorSets.has(v.id) ? (
                      <div className="flex flex-wrap gap-1.5">
                        {v.options.map((o) => (
                          <button key={o} title={o.replace(/_/g, ' ')} onClick={() => setSel((s) => ({ ...s, [v.id]: o }))}
                            className="h-6 w-6 rounded-full border transition hover:scale-110"
                            style={{ background: COLORS[o], borderColor: sel[v.id] === o ? GOLD : 'rgba(255,255,255,0.2)', boxShadow: sel[v.id] === o ? `0 0 0 2px ${GOLD}` : 'none' }} />
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {v.options.map((o) => (
                          <button key={o} onClick={() => setSel((s) => ({ ...s, [v.id]: o }))}
                            className={`rounded-md px-2 py-1 text-[11px] transition ${sel[v.id] === o ? 'text-black' : 'bg-white/5 text-white/60 hover:bg-white/15'}`}
                            style={sel[v.id] === o ? { background: GOLD } : {}}>{o.replace(/_/g, ' ')}</button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* camera */}
          <Panel title="Camera">
            <Slider label="Azimuth" v={az} min={0} max={360} step={1} set={(x) => { setSpin(false); setAz(x); }} unit="°" />
            <Slider label="Elevation" v={el} min={-20} max={80} step={1} set={setEl} unit="°" />
            <Slider label="Distance" v={dist} min={scan ? Math.round(scan.size * 0.6) : 50} max={scan ? Math.round(scan.size * 6) : 600} step={1} set={setDist} />
            <Slider label="Focal length" v={focal} min={18} max={85} step={1} set={setFocal} unit="mm" />
          </Panel>

          {scan?.has_variants && (
            <Panel title="Grid / Cut Sheet">
              <label className="mb-1 block text-[10px] uppercase tracking-wide text-white/40">Sweep variant set</label>
              <select value={sweepId} onChange={(e) => setSweepId(e.target.value)}
                className="w-full rounded-lg border border-white/15 bg-white/5 px-2 py-1.5 text-xs outline-none focus:border-white/40">
                {scan.variant_sets.map((v) => <option key={v.id} value={v.id} className="bg-neutral-900">{pretty(v.set)} ({v.options.length})</option>)}
              </select>
              <button onClick={() => { setMode('grid'); renderGrid(); }} disabled={gridBusy || !sweepSet}
                className="mt-2 w-full rounded-lg py-2 text-xs font-semibold text-black transition hover:brightness-110 disabled:opacity-40" style={{ background: NV }}>
                {gridBusy ? `Rendering ${gridProg.done}/${gridProg.total}…` : `Render grid (${sweepSet?.options.length || 0})`}
              </button>
              <p className="mt-1.5 text-[10px] leading-relaxed text-white/35">Renders each option holding the rest fixed, then composes a labeled cut sheet.</p>
            </Panel>
          )}

          <button onClick={render} disabled={busy || !scan}
            className="w-full rounded-lg py-2.5 text-sm font-semibold text-black transition hover:brightness-110 disabled:opacity-40" style={{ background: GOLD }}>
            {busy ? 'Rendering…' : 'Render'}
          </button>
        </aside>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3.5">
      <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-white/45">{title}</h3>
      {children}
    </div>
  );
}

function Seg({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button onClick={onClick}
      className={`rounded-lg py-1.5 text-xs font-medium transition ${active ? 'text-black' : 'bg-white/5 text-white/60 hover:bg-white/10'}`}
      style={active ? { background: GOLD } : {}}>{label}</button>
  );
}

function Slider({ label, v, min, max, step, set, unit = '' }: {
  label: string; v: number; min: number; max: number; step: number; set: (n: number) => void; unit?: string;
}) {
  return (
    <div className="mb-2.5 last:mb-0">
      <div className="mb-1 flex justify-between text-[11px]">
        <span className="uppercase tracking-wide text-white/40">{label}</span>
        <span className="font-mono text-white/65">{v.toFixed(0)}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={v} onChange={(e) => set(Number(e.target.value))} className="w-full accent-[#f4c14b]" />
    </div>
  );
}
