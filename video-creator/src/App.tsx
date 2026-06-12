import { useState } from 'react';
import { useProjectStore } from './store/projectStore';
import StepProgress from './components/StepProgress';
import ScriptEditor from './pages/ScriptEditor';
import VoiceStudio from './pages/VoiceStudio';
import VisualBuilder from './pages/VisualBuilder';
import MusicAudio from './pages/MusicAudio';
import RenderPreview from './pages/RenderPreview';

function App() {
  const { step, apiUrl, setApiUrl } = useProjectStore();
  const [showSettings, setShowSettings] = useState(false);

  const pages: Record<number, React.ReactNode> = {
    1: <ScriptEditor />,
    2: <VoiceStudio />,
    3: <VisualBuilder />,
    4: <MusicAudio />,
    5: <RenderPreview />,
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-200">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-gray-900/80 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            TrigunAI Video Creator
          </span>
          <span className="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded">v1.0</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="text-gray-500 hover:text-gray-300 text-sm transition"
          >
            Settings
          </button>
        </div>
      </header>

      {/* Settings panel */}
      {showSettings && (
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
          <div className="max-w-5xl mx-auto flex items-center gap-4">
            <label className="text-xs text-gray-500">API URL:</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-gray-300 w-80 outline-none"
              placeholder="http://EC2_IP:8010"
            />
            <span className="text-xs text-gray-600">
              Point to your EC2 backend (SSH tunnel: ssh -L 8010:localhost:8010 ubuntu@EC2_IP)
            </span>
          </div>
        </div>
      )}

      {/* Step progress */}
      <StepProgress />

      {/* Page content */}
      <main className="pb-20">
        {pages[step] || <ScriptEditor />}
      </main>
    </div>
  );
}

export default App;
