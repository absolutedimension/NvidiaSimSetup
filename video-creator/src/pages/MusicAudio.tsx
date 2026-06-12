import { useState } from 'react';
import { useProjectStore } from '../store/projectStore';
import { generateMusic, getJobStatus } from '../api/client';
import { MUSIC_PRESETS } from '../types/project';

export default function MusicAudio() {
  const { music, setMusic, setStep, apiUrl } = useProjectStore();
  const [generating, setGenerating] = useState(false);
  const [musicUrl, setMusicUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const totalVoiceDuration = useProjectStore(s =>
    s.scenes.reduce((sum, sc) => sum + (sc.voiceDuration || 15), 0)
  );

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const duration = Math.max(music.durationSeconds, Math.ceil(totalVoiceDuration) + 10);
      const result = await generateMusic(music.prompt, duration);

      // Poll for completion
      const poll = setInterval(async () => {
        const status = await getJobStatus(result.job_id);
        if (status.status === 'completed') {
          clearInterval(poll);
          const url = `${apiUrl}${status.audio_url}`;
          setMusicUrl(url);
          setMusic({ audioUrl: url });
          setGenerating(false);
        } else if (status.status === 'failed') {
          clearInterval(poll);
          setError('Music generation failed');
          setGenerating(false);
        }
      }, 3000);
    } catch (e: any) {
      setError(e.message);
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">Background Music</h2>
        <p className="text-gray-500 mt-1">Generate AI background music or use silence</p>
      </div>

      {/* Presets */}
      <div className="mb-6">
        <label className="text-xs text-gray-500 uppercase tracking-wider block mb-3">Quick Presets</label>
        <div className="grid grid-cols-3 gap-2">
          {MUSIC_PRESETS.map(preset => (
            <button
              key={preset.label}
              onClick={() => setMusic({ prompt: preset.prompt })}
              className={`p-3 rounded-lg border text-left text-sm transition ${
                music.prompt === preset.prompt
                  ? 'border-purple-500 bg-purple-900/20 text-purple-300'
                  : 'border-gray-800 bg-gray-900/40 text-gray-400 hover:border-gray-700'
              }`}
            >
              <span className="font-medium">{preset.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Custom prompt */}
      <div className="mb-6">
        <label className="text-xs text-gray-500 uppercase tracking-wider block mb-2">Music Prompt</label>
        <textarea
          value={music.prompt}
          onChange={(e) => setMusic({ prompt: e.target.value })}
          rows={3}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 outline-none focus:border-purple-600 resize-none"
          placeholder="Describe the music mood, genre, instruments, tempo..."
        />
      </div>

      {/* Controls */}
      <div className="flex gap-6 mb-6">
        <div>
          <label className="text-xs text-gray-500 uppercase tracking-wider block mb-2">Volume (vs voice)</label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0.03"
              max="0.2"
              step="0.01"
              value={music.volume}
              onChange={(e) => setMusic({ volume: parseFloat(e.target.value) })}
              className="w-40"
            />
            <span className="text-sm text-gray-400">{Math.round(music.volume * 100)}%</span>
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-500 uppercase tracking-wider block mb-2">Duration</label>
          <span className="text-sm text-gray-400">
            Auto: {Math.ceil(totalVoiceDuration)}s (matches voice) + 10s buffer
          </span>
        </div>
      </div>

      {/* Generate */}
      <button
        onClick={handleGenerate}
        disabled={generating}
        className="px-6 py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-white rounded-xl font-semibold transition flex items-center gap-2"
      >
        {generating ? (
          <><span className="animate-spin">⏳</span> Generating music...</>
        ) : (
          <>🎵 Generate Background Music</>
        )}
      </button>

      {error && (
        <div className="mt-4 bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Preview */}
      {(musicUrl || music.audioUrl) && (
        <div className="mt-6 bg-gray-900/60 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-green-400">✓</span>
            <span className="text-white font-medium">Background Music Generated</span>
          </div>
          <audio controls src={musicUrl || music.audioUrl} className="w-full" />
        </div>
      )}

      {/* No music option */}
      <button
        onClick={() => { setMusic({ audioUrl: undefined }); setMusicUrl(null); }}
        className="mt-4 text-sm text-gray-600 hover:text-gray-400 transition"
      >
        Skip — no background music
      </button>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button onClick={() => setStep(3)} className="px-6 py-3 text-gray-400 hover:text-white transition">
          ← Back to Visuals
        </button>
        <button
          onClick={() => setStep(5)}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition"
        >
          Next: Render →
        </button>
      </div>
    </div>
  );
}
