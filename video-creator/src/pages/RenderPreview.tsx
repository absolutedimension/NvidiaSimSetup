import { useState, useEffect, useRef } from 'react';
import { useProjectStore } from '../store/projectStore';
import { createVideoProject, getProjectStatus, connectProjectWS } from '../api/client';

interface JobInfo {
  id: string;
  type: string;
  status: string;
  progress: number;
  step: string;
  result?: any;
  error?: string;
}

const JOB_ICONS: Record<string, string> = {
  voice: '🎙️',
  slide: '🎨',
  music: '🎵',
  avatar: '👤',
  render: '🎬',
};

const STATUS_COLORS: Record<string, string> = {
  queued: 'bg-gray-700 text-gray-400',
  processing: 'bg-blue-900/50 text-blue-400 border-blue-700',
  completed: 'bg-green-900/30 text-green-400 border-green-800',
  failed: 'bg-red-900/30 text-red-400 border-red-800',
};

export default function RenderPreview() {
  const { scenes, music, setStep, apiUrl, projectName, exportProject, backgroundShader } = useProjectStore();
  const [projectId, setProjectId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [finalVideo, setFinalVideo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const totalDuration = scenes.reduce((sum, s) => sum + (s.voiceDuration || 15), 0);

  // Poll project status when we have a project ID
  useEffect(() => {
    if (!projectId) return;

    const poll = setInterval(async () => {
      try {
        const data = await getProjectStatus(projectId);
        setJobs(data.jobs || []);
        setSummary(data.summary);
        if (data.final_video) {
          setFinalVideo(`${apiUrl}${data.final_video}`);
        }
        // Stop polling when all done
        if (data.summary?.queued === 0 && data.summary?.processing === 0) {
          clearInterval(poll);
        }
      } catch (e) {
        // continue polling
      }
    }, 3000);

    return () => clearInterval(poll);
  }, [projectId, apiUrl]);

  // Connect WebSocket for real-time updates
  useEffect(() => {
    if (!projectId) return;

    const ws = connectProjectWS(projectId, (data) => {
      if (data.type === 'status') {
        setJobs(data.jobs || []);
      } else if (data.job_id) {
        // Update individual job
        setJobs(prev => prev.map(j =>
          j.id === data.job_id
            ? { ...j, progress: data.progress, step: data.step, status: data.status || j.status }
            : j
        ));
      }
    });

    wsRef.current = ws;
    return () => ws.close();
  }, [projectId]);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    setFinalVideo(null);
    setJobs([]);

    try {
      const input = {
        project_name: projectName,
        scenes: scenes.map(s => ({
          id: s.id,
          title: s.title,
          text: s.text,
          tone: s.tone,
          speed: s.speed,
          template: s.template,
          slide_title: s.slideConfig?.title || s.title,
          slide_body: s.slideConfig?.body || '',
          slide_accent: s.slideConfig?.accentColor || 'blue',
          slide_layout: s.slideConfig?.layout || 'center',
        })),
        music_prompt: music.prompt,
        music_volume: music.volume,
        generate_avatar: false,
        ...(backgroundShader ? { background_shader: backgroundShader } : {}),
      };

      const result = await createVideoProject(input);
      setProjectId(result.project_id);

      // Initialize job list
      const initialJobs = [
        ...result.voice_jobs.map((id: string, i: number) => ({
          id, type: 'voice', status: 'queued', progress: 0, step: `Scene ${i+1} voice`,
        })),
        ...result.slide_jobs.map((id: string, i: number) => ({
          id, type: 'slide', status: 'queued', progress: 0, step: `Scene ${i+1} slide`,
        })),
        { id: result.music_job, type: 'music', status: 'queued', progress: 0, step: 'Background music' },
        { id: result.render_job, type: 'render', status: 'queued', progress: 0, step: 'Final assembly' },
      ];
      setJobs(initialJobs);
    } catch (e: any) {
      setError(e.message);
    }
    setSubmitting(false);
  };

  const handleExport = () => {
    const project = exportProject();
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project.name.replace(/\s+/g, '_')}.json`;
    a.click();
  };

  const overallProgress = summary?.overall_progress || (jobs.length > 0
    ? Math.round(jobs.reduce((s, j) => s + j.progress, 0) / jobs.length)
    : 0);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">Render & Deliver</h2>
        <p className="text-gray-500 mt-1">Submit to queue — watch it build in real-time</p>
      </div>

      {/* Project summary */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 mb-6">
        <h3 className="text-white font-semibold mb-3">Project Summary</h3>
        <div className="grid grid-cols-4 gap-4 text-center mb-4">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-400">{scenes.length}</div>
            <div className="text-xs text-gray-500">Scenes</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-400">{Math.floor(totalDuration / 60)}:{String(Math.round(totalDuration % 60)).padStart(2, '0')}</div>
            <div className="text-xs text-gray-500">Est. Duration</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-purple-400">{scenes.filter(s => s.voiceUrl).length}/{scenes.length}</div>
            <div className="text-xs text-gray-500">Voice Previews</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-amber-400">{scenes.filter(s => s.slideUrl).length}/{scenes.length}</div>
            <div className="text-xs text-gray-500">Slide Previews</div>
          </div>
        </div>

        {/* Slide thumbnails */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {scenes.map((s, i) => (
            <div key={s.id} className="w-32 h-18 flex-shrink-0 bg-gray-950 rounded border border-gray-800 overflow-hidden">
              {s.slideUrl ? (
                <img src={s.slideUrl} alt={`S${i+1}`} className="w-full h-full object-contain" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-700 text-xs">{i+1}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Submit / Status */}
      {!projectId ? (
        <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-8 text-center mb-6">
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-12 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-700 disabled:to-gray-700 text-white rounded-2xl font-bold text-lg transition shadow-lg shadow-blue-600/20"
          >
            {submitting ? '⏳ Submitting...' : '🎬 Submit to Render Queue'}
          </button>
          <p className="text-gray-600 text-sm mt-3">
            Creates {scenes.length * 2 + 2} jobs: {scenes.length} voice + {scenes.length} slides + 1 music + 1 final render
          </p>
        </div>
      ) : (
        <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 mb-6">
          {/* Overall progress */}
          <div className="flex items-center justify-between mb-3">
            <span className="text-white font-semibold">
              {finalVideo ? '✅ Video Ready!' : '🔄 Processing...'}
            </span>
            <span className="text-sm text-gray-400">
              {summary?.completed || 0}/{summary?.total || jobs.length} jobs complete · {overallProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden mb-4">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-green-500 rounded-full transition-all duration-700"
              style={{ width: `${overallProgress}%` }}
            />
          </div>

          {/* Job list */}
          <div className="space-y-2">
            {jobs.map(job => (
              <div
                key={job.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${STATUS_COLORS[job.status] || 'border-gray-800'}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{JOB_ICONS[job.type] || '📦'}</span>
                  <div>
                    <span className="text-sm font-medium capitalize">{job.type}</span>
                    {job.step && (
                      <span className="text-xs text-gray-500 ml-2">{job.step}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {job.status === 'processing' && (
                    <div className="w-24 bg-gray-700 rounded-full h-1.5">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  )}
                  <span className={`text-xs font-medium capitalize px-2 py-0.5 rounded ${
                    job.status === 'completed' ? 'text-green-400' :
                    job.status === 'processing' ? 'text-blue-400' :
                    job.status === 'failed' ? 'text-red-400' :
                    'text-gray-500'
                  }`}>
                    {job.status === 'processing' ? `${job.progress}%` : job.status}
                  </span>
                  {job.error && (
                    <span className="text-xs text-red-400" title={job.error}>❌</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Final video */}
      {finalVideo && (
        <div className="bg-green-900/10 border border-green-800 rounded-xl p-5 mb-6">
          <h3 className="text-green-400 font-semibold text-lg mb-3">🎉 Your Video is Ready</h3>
          <video controls src={finalVideo} className="w-full rounded-lg border border-gray-700 mb-4" />
          <div className="flex gap-3">
            <a
              href={finalVideo}
              download
              className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-xl font-semibold transition"
            >
              ⬇️ Download MP4
            </a>
            <button
              onClick={() => { setProjectId(null); setJobs([]); setFinalVideo(null); }}
              className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition"
            >
              🔄 Start New Render
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 mb-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Export + Queue stats */}
      <div className="flex gap-3 mt-4">
        <button onClick={handleExport} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg text-sm transition">
          📦 Export Project JSON
        </button>
        {projectId && (
          <span className="text-xs text-gray-600 self-center">
            Project: {projectId}
          </span>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <button onClick={() => setStep(4)} className="px-6 py-3 text-gray-400 hover:text-white transition">
          ← Back to Music
        </button>
      </div>
    </div>
  );
}
