import { useState } from 'react';
import { useProjectStore } from '../store/projectStore';
import { previewSlide, generateSlides, uploadImage } from '../api/client';
import { TEMPLATES } from '../types/project';
import ShaderBackgroundPanel from '../components/ShaderBackgroundPanel';

const ACCENT_COLORS = [
  { value: 'blue', label: 'Blue', hex: '#3b82f6' },
  { value: 'green', label: 'Green', hex: '#4ade80' },
  { value: 'purple', label: 'Purple', hex: '#a855f7' },
  { value: 'amber', label: 'Amber', hex: '#fbbf24' },
  { value: 'red', label: 'Red', hex: '#f87171' },
];

const LAYOUTS = [
  { value: 'center', label: 'Center', desc: 'Title centered with glow' },
  { value: 'left', label: 'Left aligned', desc: 'Title + body left' },
  { value: 'bullets', label: 'Bullet list', desc: 'Title + bullet points' },
  { value: 'split', label: 'Split', desc: 'Text left, image right' },
  { value: 'screenshot', label: 'Screenshot', desc: 'Full screenshot with title' },
];

export default function VisualBuilder() {
  const { scenes, updateScene, setStep, apiUrl } = useProjectStore();
  const [previewing, setPreviewing] = useState<string | null>(null);
  const [generatingAll, setGeneratingAll] = useState(false);

  const handlePreview = async (sceneId: string) => {
    const scene = scenes.find(s => s.id === sceneId);
    if (!scene) return;

    setPreviewing(sceneId);
    try {
      const config = scene.slideConfig || {
        title: scene.title || `Scene`,
        body: scene.text.slice(0, 200),
        accentColor: 'blue',
        layout: 'center',
      };
      const result = await previewSlide({
        title: config.title,
        body: config.body,
        accent_color: config.accentColor,
        layout: config.layout,
      });
      updateScene(sceneId, { slideUrl: `${apiUrl}${result.image_url}` });
    } catch (e) {
      console.error(e);
    }
    setPreviewing(null);
  };

  const handleGenerateAll = async () => {
    setGeneratingAll(true);
    try {
      const slideScenes = scenes.map(s => ({
        title: s.slideConfig?.title || s.title || 'Scene',
        body: s.slideConfig?.body || '',
        accent_color: s.slideConfig?.accentColor || 'blue',
        layout: s.slideConfig?.layout || 'center',
      }));
      const result = await generateSlides(slideScenes);
      result.slides.forEach((slide: any, i: number) => {
        if (scenes[i]) {
          updateScene(scenes[i].id, { slideUrl: `${apiUrl}${slide.image_url}` });
        }
      });
    } catch (e) {
      console.error(e);
    }
    setGeneratingAll(false);
  };

  const handleScreenshotUpload = async (sceneId: string, file: File) => {
    try {
      const result = await uploadImage(file);
      updateScene(sceneId, {
        slideConfig: {
          ...scenes.find(s => s.id === sceneId)?.slideConfig!,
          screenshotPath: result.file_path,
        },
      });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white">Visual Builder</h2>
          <p className="text-gray-500 mt-1">Design slides and visuals for each scene</p>
        </div>
        <button
          onClick={handleGenerateAll}
          disabled={generatingAll}
          className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-white rounded-xl font-semibold transition"
        >
          {generatingAll ? '⏳ Generating...' : '🎨 Generate All Slides'}
        </button>
      </div>

      <ShaderBackgroundPanel />

      <div className="space-y-6">
        {scenes.map((scene, i) => {
          const config = scene.slideConfig || {
            title: scene.title || `Scene ${i + 1}`,
            body: '',
            accentColor: 'blue',
            layout: 'center' as const,
          };
          const tmpl = TEMPLATES.find(t => t.value === scene.template);

          return (
            <div key={scene.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-4">
                <span className="w-7 h-7 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                <span className="text-white font-medium">{scene.title || `Scene ${i + 1}`}</span>
                <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 text-gray-400">
                  {tmpl?.icon} {tmpl?.label}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Left: Config */}
                <div className="space-y-3">
                  {/* Slide title */}
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Slide Title</label>
                    <input
                      type="text"
                      value={config.title}
                      onChange={(e) => updateScene(scene.id, {
                        slideConfig: { ...config, title: e.target.value },
                      })}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-600"
                      placeholder="Slide heading"
                    />
                  </div>

                  {/* Body text */}
                  <div>
                    <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Body / Bullets</label>
                    <textarea
                      value={config.body}
                      onChange={(e) => updateScene(scene.id, {
                        slideConfig: { ...config, body: e.target.value },
                      })}
                      rows={3}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 resize-y outline-none focus:border-blue-600"
                      placeholder="Body text or bullet points (one per line)"
                    />
                  </div>

                  {/* Color + Layout row */}
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Accent</label>
                      <div className="flex gap-1">
                        {ACCENT_COLORS.map(c => (
                          <button
                            key={c.value}
                            onClick={() => updateScene(scene.id, {
                              slideConfig: { ...config, accentColor: c.value },
                            })}
                            className={`w-8 h-8 rounded-full border-2 transition ${
                              config.accentColor === c.value ? 'border-white scale-110' : 'border-transparent'
                            }`}
                            style={{ backgroundColor: c.hex }}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="flex-1">
                      <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Layout</label>
                      <select
                        value={config.layout}
                        onChange={(e) => updateScene(scene.id, {
                          slideConfig: { ...config, layout: e.target.value as any },
                        })}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 outline-none"
                      >
                        {LAYOUTS.map(l => (
                          <option key={l.value} value={l.value}>{l.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Screenshot upload (for split/screenshot layouts) */}
                  {(config.layout === 'split' || config.layout === 'screenshot') && (
                    <div>
                      <label className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Screenshot</label>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          if (e.target.files?.[0]) {
                            handleScreenshotUpload(scene.id, e.target.files[0]);
                          }
                        }}
                        className="text-sm text-gray-400"
                      />
                    </div>
                  )}

                  <button
                    onClick={() => handlePreview(scene.id)}
                    disabled={previewing === scene.id}
                    className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition"
                  >
                    {previewing === scene.id ? '⏳ Previewing...' : '👁️ Preview Slide'}
                  </button>
                </div>

                {/* Right: Preview */}
                <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
                  {scene.slideUrl ? (
                    <img
                      src={scene.slideUrl}
                      alt={`Slide ${i + 1}`}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <span className="text-gray-700 text-sm">Click "Preview" to see slide</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button onClick={() => setStep(2)} className="px-6 py-3 text-gray-400 hover:text-white transition">
          ← Back to Voice
        </button>
        <button
          onClick={() => setStep(4)}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition"
        >
          Next: Music →
        </button>
      </div>
    </div>
  );
}
