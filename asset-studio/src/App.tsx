import { Viewport } from './components/Viewport'
import { AgentControls } from './components/AgentControls'
import { StatusPanel } from './components/StatusPanel'
import { ResultsPanel } from './components/ResultsPanel'

export function App() {
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <Viewport />
      <AgentControls />
      <StatusPanel />
      <ResultsPanel />
      <div
        style={{
          position: 'absolute',
          bottom: 12,
          right: 16,
          fontSize: 10,
          opacity: 0.4,
          fontFamily: 'monospace',
        }}
      >
        powered by TrigunAI · Azure OpenAI · NVIDIA Content Agents
      </div>
    </div>
  )
}
