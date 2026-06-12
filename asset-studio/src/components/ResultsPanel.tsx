import { useStudio } from '../store/store'

export function ResultsPanel() {
  const { predictions, status } = useStudio()
  if (status !== 'completed' || predictions.length === 0) return null

  return (
    <div style={panelStyle}>
      <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 8 }}>
        VLM PREDICTIONS ({predictions.length})
      </div>
      <div style={{ display: 'grid', gap: 6, maxHeight: 280, overflowY: 'auto' }}>
        {predictions.map((p, i) => (
          <div
            key={`${p.id}-${i}`}
            style={{
              padding: '8px 10px',
              background: 'rgba(255,255,255,0.04)',
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            <div style={{ opacity: 0.6, fontSize: 10, marginBottom: 2 }}>
              {p.id.split('/').pop() ?? p.id}
            </div>
            <div style={{ fontWeight: 500 }}>{p.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  position: 'absolute',
  top: 16,
  right: 16,
  width: 280,
  background: 'rgba(20, 22, 27, 0.85)',
  backdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 12,
  padding: 14,
  zIndex: 10,
  boxShadow: '0 6px 30px rgba(0,0,0,0.4)',
}
