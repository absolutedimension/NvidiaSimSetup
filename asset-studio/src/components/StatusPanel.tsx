import { useStudio } from '../store/store'

export function StatusPanel() {
  const { status, currentStep, percent, elapsedSec, completedSteps, errorMessage } =
    useStudio()

  if (status === 'idle') return null

  const friendlyStatus =
    status === 'uploading'
      ? 'Uploading USD…'
      : status === 'queued'
        ? 'Queued'
        : status === 'running'
          ? `Running · ${currentStep ?? '…'}`
          : status === 'completed'
            ? 'Completed ✓'
            : 'Failed'

  return (
    <div style={panelStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 600 }}>{friendlyStatus}</span>
        <span style={{ fontSize: 11, opacity: 0.6 }}>{elapsedSec}s</span>
      </div>

      {status === 'running' && (
        <div style={progressTrack}>
          <div style={{ ...progressFill, width: `${percent}%` }} />
        </div>
      )}

      {errorMessage && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#ff5470' }}>
          {errorMessage}
        </div>
      )}

      {completedSteps.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 6 }}>
            COMPLETED STEPS
          </div>
          <div style={{ display: 'grid', gap: 4 }}>
            {completedSteps.map((s) => (
              <div
                key={s.name}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 11,
                  opacity: 0.75,
                }}
              >
                <span>✓ {s.displayName ?? s.name}</span>
                <span style={{ opacity: 0.6 }}>{s.durationSeconds ?? 0}s</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 16,
  left: 16,
  width: 280,
  background: 'rgba(20, 22, 27, 0.85)',
  backdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 12,
  padding: 14,
  zIndex: 10,
  boxShadow: '0 6px 30px rgba(0,0,0,0.4)',
}

const progressTrack: React.CSSProperties = {
  marginTop: 10,
  height: 4,
  background: 'rgba(255,255,255,0.1)',
  borderRadius: 2,
  overflow: 'hidden',
}

const progressFill: React.CSSProperties = {
  height: '100%',
  background: 'linear-gradient(90deg, #4a9eff, #6ec1ff)',
  transition: 'width 0.4s ease',
}
