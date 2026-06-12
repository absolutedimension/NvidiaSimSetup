import { useEffect, useState } from 'react';
import { useProjectStore } from '../store/projectStore';
import { listShaders, addCustomShader, type ShaderInfo } from '../api/client';

/**
 * Background Shader picker for the Visual Builder.
 * - Lists built-in + custom shader backgrounds.
 * - "Paste from Shader Studio" accepts raw GLSL copied from studio.trigunai.com,
 *   which the backend auto-translates, validates on the GPU, and registers.
 */
export default function ShaderBackgroundPanel() {
  const { backgroundShader, setBackgroundShader, apiUrl } = useProjectStore();
  const [shaders, setShaders] = useState<ShaderInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [showPaste, setShowPaste] = useState(false);

  // paste modal state
  const [name, setName] = useState('');
  const [glsl, setGlsl] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<any>(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await listShaders();
      setShaders(r.shaders);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const handleAdd = async () => {
    if (!name.trim() || !glsl.trim()) return;
    setAdding(true);
    setError(null);
    setReport(null);
    try {
      const res = await addCustomShader(name.trim(), glsl);
      if (res.ok) {
        await refresh();
        setBackgroundShader(res.id);
        setReport(res.report);
        setShowPaste(false);
        setName('');
        setGlsl('');
      } else {
        setError(res.error || 'Shader failed to compile.');
        setReport(res.report);
      }
    } catch (e: any) {
      setError(e.message);
    }
    setAdding(false);
  };

  const px = (u: string | null) => (u ? `${apiUrl}${u}` : null);

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">🎨 Background Shader</h3>
          <p className="text-gray-500 text-sm mt-0.5">
            Audio-reactive background behind your video. Paste any shader from{' '}
            <span className="text-blue-400">studio.trigunai.com</span>.
          </p>
        </div>
        <button
          onClick={() => setShowPaste(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition"
        >
          ＋ Paste from Shader Studio
        </button>
      </div>

      {loading && <div className="text-gray-500 text-sm">Loading shaders…</div>}

      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
        {/* None */}
        <button
          onClick={() => setBackgroundShader(null)}
          className={`aspect-video rounded-lg border-2 flex items-center justify-center text-xs ${
            !backgroundShader ? 'border-blue-500 bg-blue-500/10 text-blue-300' : 'border-gray-700 text-gray-500 hover:border-gray-600'
          }`}
        >
          None
        </button>

        {shaders.map((s) => {
          const selected = backgroundShader === s.id;
          const thumb = px(s.preview_url);
          return (
            <button
              key={s.id}
              onClick={() => setBackgroundShader(s.id)}
              title={s.desc}
              className={`relative aspect-video rounded-lg border-2 overflow-hidden group ${
                selected ? 'border-blue-500' : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              {thumb ? (
                <img src={thumb} alt={s.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gray-800" />
              )}
              <span className="absolute inset-x-0 bottom-0 bg-black/60 text-[10px] text-white px-1 py-0.5 truncate text-left">
                {s.name}
              </span>
              {s.custom && (
                <span className="absolute top-0.5 right-0.5 bg-purple-600 text-white text-[8px] px-1 rounded">
                  studio
                </span>
              )}
            </button>
          );
        })}
      </div>

      {report && report.warnings?.length === 0 && (
        <p className="text-green-400 text-xs mt-3">
          ✓ Imported & validated on GPU — selected as background.
        </p>
      )}

      {/* Paste modal */}
      {showPaste && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-6">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-2xl">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-semibold text-lg">Paste GLSL from Shader Studio</h4>
              <button onClick={() => setShowPaste(false)} className="text-gray-500 hover:text-gray-300">✕</button>
            </div>
            <p className="text-gray-500 text-sm mb-3">
              In Shader Studio, hit <span className="text-gray-300">Copy GLSL Source</span> and paste it below.
              It's auto-translated to the pipeline and made voice-reactive.
            </p>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Shader name (e.g. Vocal Melt)"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-600 mb-3"
            />
            <textarea
              value={glsl}
              onChange={(e) => setGlsl(e.target.value)}
              placeholder="Paste GLSL fragment source here…"
              rows={12}
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs font-mono text-gray-300 outline-none focus:border-blue-600 resize-none"
            />
            {error && (
              <div className="mt-3 text-red-400 text-xs bg-red-500/10 border border-red-500/30 rounded-lg p-2">
                {error}
                {report?.warnings?.length > 0 && (
                  <div className="text-amber-400 mt-1">Warnings: {report.warnings.join('; ')}</div>
                )}
              </div>
            )}
            <div className="flex items-center justify-end gap-3 mt-4">
              <button onClick={() => setShowPaste(false)} className="px-4 py-2 text-gray-400 hover:text-gray-200 text-sm">
                Cancel
              </button>
              <button
                onClick={handleAdd}
                disabled={adding || !name.trim() || !glsl.trim()}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white rounded-lg text-sm font-semibold transition"
              >
                {adding ? '⏳ Validating on GPU…' : 'Add & Validate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
