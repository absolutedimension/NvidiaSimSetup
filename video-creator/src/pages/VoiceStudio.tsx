import { useState } from 'react';
import { useProjectStore } from '../store/projectStore';
import { generateVoice, generateAllVoices, getJobStatus } from '../api/client';
import { TONES } from '../types/project';

export default function VoiceStudio() {
  const { scenes, updateScene, setStep, apiUrl } = useProjectStore();
  const [generating, setGenerating] = useState<string | null>(null);
  const [, setBatchJobId] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateOne = async (sceneId: string) => {
    const scene = scenes.find(s => s.id === sceneId);
    if (!scene) return;

    setGenerating(sceneId);
    setError(null);
    try {
      const result = await generateVoice(scene.text, scene.tone, scene.speed);
      updateScene(sceneId, {
        voiceUrl: `${apiUrl}${result.audio_url}`,
        voiceDuration: result.duration,
      });
    } catch (e: any) {
      setError(e.message);
    }
    setGenerating(null);
  };

  const handleGenerateAll = async () => {
    setGenerating('all');
    setError(null);
    try {
      const result = await generateAllVoices(
        scenes.map(s => ({ id: s.id, text: s.text, tone: s.tone, speed: s.speed }))
      );
      setBatchJobId(result.job_id);

      // Poll for completion
      const poll = setInterval(async () => {
        const status = await getJobStatus(result.job_id);
        setBatchProgress(status.progress || 0);

        if (status.status === 'completed') {
          clearInterval(poll);
          // Update scenes with voice URLs
          for (const seg of status.segments || []) {
            updateScene(seg.id, {
              voiceUrl: `${apiUrl}${seg.audio_url}`,
              voiceDuration: seg.duration,
            });
          }
          setGenerating(null);
          setBatchJobId(null);
        }
      }, 2000);
    } catch (e: any) {
      setError(e.message);
      setGenerating(null);
    }
  };

  const allGenerated = scenes.every(s => s.voiceUrl);
  const someGenerated = scenes.some(s => s.voiceUrl);
  const tone = (t: string) => TONES.find(x => x.value === t);

  const totalDuration = scenes.reduce((sum, s) => sum + (s.voiceDuration || 0), 0);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white">Voice Studio</h2>
          <p className="text-gray-500 mt-1">Generate AI voices for each scene with tone control</p>
        </div>
        <button
          onClick={handleGenerateAll}
          disabled={generating !== null}
          className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-white rounded-xl font-semibold transition flex items-center gap-2"
        >
          {generating === 'all' ? (
            <>
              <span className="animate-spin">⏳</span>
              Generating {batchProgress}/{scenes.length}...
            </>
          ) : (
            <>🎙️ Generate All Voices</>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 mb-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {someGenerated && (
        <div className="bg-green-900/20 border border-green-800 rounded-lg p-3 mb-4 flex items-center justify-between">
          <span className="text-green-400 text-sm">
            {scenes.filter(s => s.voiceUrl).length}/{scenes.length} voices ready ·
            Total: {Math.floor(totalDuration / 60)}m {Math.round(totalDuration % 60)}s
          </span>
          {allGenerated && (
            <span className="text-green-300 text-sm font-semibold">All voices generated ✓</span>
          )}
        </div>
      )}

      <div className="space-y-3">
        {scenes.map((scene, i) => (
          <div key={scene.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="w-7 h-7 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs font-bold">
                    {i + 1}
                  </span>
                  <span className="text-white font-medium">{scene.title || `Scene ${i + 1}`}</span>
                  <span className="px-2 py-0.5 rounded-full text-xs bg-gray-800 text-gray-400">
                    {tone(scene.tone)?.emoji} {tone(scene.tone)?.label}
                  </span>
                  <span className="text-xs text-gray-600">speed: {scene.speed}</span>
                </div>
                <p className="text-gray-400 text-sm line-clamp-2">{scene.text}</p>
              </div>

              <div className="flex items-center gap-3 ml-4">
                {scene.voiceUrl ? (
                  <div className="flex items-center gap-2">
                    <audio controls src={scene.voiceUrl} className="h-8 w-48" />
                    <span className="text-xs text-green-400">{scene.voiceDuration?.toFixed(1)}s</span>
                  </div>
                ) : (
                  <span className="text-xs text-gray-600">Not generated</span>
                )}
                <button
                  onClick={() => handleGenerateOne(scene.id)}
                  disabled={generating !== null}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 rounded-lg text-sm transition"
                >
                  {generating === scene.id ? '⏳' : '🔄'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button onClick={() => setStep(1)} className="px-6 py-3 text-gray-400 hover:text-white transition">
          ← Back to Script
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={!someGenerated}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-semibold transition"
        >
          Next: Visuals →
        </button>
      </div>
    </div>
  );
}
