import { useEffect, useState } from 'react'
import { useStore } from '../store/store'
import { loadShowcaseManifest } from '../api/showcases'

export function HUD({
  isXR,
  onEnterVR,
}: {
  isXR: boolean
  onEnterVR: () => void
}) {
  const { showcases, selectedId, select, setShowcases, loadError, loaded } = useStore()
  const [supportsXR, setSupportsXR] = useState<boolean | null>(null)

  useEffect(() => {
    loadShowcaseManifest().then(setShowcases)
  }, [setShowcases])

  useEffect(() => {
    if (typeof navigator === 'undefined') return
    const xr = (navigator as any).xr
    if (!xr) {
      setSupportsXR(false)
      return
    }
    xr.isSessionSupported('immersive-vr').then((s: boolean) => setSupportsXR(s))
  }, [])

  useEffect(() => {
    if (!selectedId && showcases.length) select(showcases[0].id)
  }, [showcases, selectedId, select])

  if (isXR) return null

  return (
    <div style={overlay}>
      <div style={panel}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
          TrigunAI WebXR Showcase
        </div>
        <div style={{ fontSize: 11, opacity: 0.55, marginBottom: 18 }}>
          OpenUSD scenes · WebXR for Quest 3
        </div>

        <div style={sectionLabel}>SHOWCASE</div>
        <div style={{ display: 'grid', gap: 6, marginBottom: 18 }}>
          {showcases.map((s) => (
            <button
              key={s.id}
              onClick={() => select(s.id)}
              style={showcaseButton(s.id === selectedId)}
            >
              <div style={{ fontWeight: 600 }}>{s.label}</div>
              {s.description && (
                <div style={{ fontSize: 10, opacity: 0.6, marginTop: 3 }}>
                  {s.description}
                </div>
              )}
            </button>
          ))}
          {!showcases.length && (
            <div style={{ fontSize: 11, opacity: 0.55 }}>Loading showcases…</div>
          )}
        </div>

        {loadError && (
          <div style={errorBox}>Load error: {loadError}</div>
        )}

        <div style={sectionLabel}>VR</div>
        {supportsXR === null && (
          <div style={{ fontSize: 11, opacity: 0.55 }}>Detecting WebXR…</div>
        )}
        {supportsXR === false && (
          <div style={{ fontSize: 11, opacity: 0.7, lineHeight: 1.4 }}>
            WebXR not available in this browser. Open this URL in the
            Quest&nbsp;Browser to enter VR.
          </div>
        )}
        {supportsXR && (
          <button onClick={onEnterVR} style={primaryButton}>
            ▶ Enter VR
          </button>
        )}

        <div
          style={{
            marginTop: 14,
            padding: '8px 10px',
            borderRadius: 6,
            background: loaded
              ? 'rgba(74,255,158,0.08)'
              : 'rgba(74,158,255,0.12)',
            border: `1px solid ${
              loaded ? 'rgba(74,255,158,0.35)' : 'rgba(74,158,255,0.4)'
            }`,
            fontSize: 12,
            color: loaded ? '#9af0c2' : '#9ec7ff',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          {loaded ? (
            <>
              <span>✓</span>
              <span>asset loaded — ready to enter VR</span>
            </>
          ) : (
            <>
              <span className="hud-spin" aria-hidden>◐</span>
              <span>loading… large GLBs can take 30–60 s</span>
            </>
          )}
        </div>
        <style>{`
          @keyframes hud-spin-anim { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
          .hud-spin { display: inline-block; animation: hud-spin-anim 1.2s linear infinite; }
        `}</style>
      </div>

      <div style={hint}>
        <strong>Desktop:</strong> drag to orbit, scroll to zoom · <strong>Quest:</strong> tap "Enter VR"
      </div>
    </div>
  )
}

const overlay: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  pointerEvents: 'none',
  zIndex: 10,
}

const panel: React.CSSProperties = {
  position: 'absolute',
  top: 16,
  left: 16,
  width: 280,
  background: 'rgba(15, 17, 22, 0.85)',
  backdropFilter: 'blur(14px)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 12,
  padding: 18,
  pointerEvents: 'auto',
  boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
}

const sectionLabel: React.CSSProperties = {
  fontSize: 10,
  opacity: 0.55,
  letterSpacing: 1,
  marginBottom: 6,
  fontWeight: 600,
}

const showcaseButton = (active: boolean): React.CSSProperties => ({
  padding: '10px 12px',
  background: active ? 'rgba(74,158,255,0.16)' : 'rgba(255,255,255,0.03)',
  border: `1px solid ${active ? 'rgba(74,158,255,0.55)' : 'rgba(255,255,255,0.08)'}`,
  borderRadius: 8,
  color: '#e4e6eb',
  textAlign: 'left',
  cursor: 'pointer',
  width: '100%',
  transition: 'all 0.15s',
})

const primaryButton: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  background: '#4a9eff',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  fontWeight: 700,
  fontSize: 15,
  cursor: 'pointer',
  letterSpacing: 0.3,
}

const hint: React.CSSProperties = {
  position: 'absolute',
  bottom: 16,
  left: '50%',
  transform: 'translateX(-50%)',
  fontSize: 11,
  opacity: 0.45,
  textAlign: 'center',
  fontFamily: 'monospace',
  pointerEvents: 'none',
}

const errorBox: React.CSSProperties = {
  padding: 8,
  background: 'rgba(255, 70, 90, 0.1)',
  border: '1px solid rgba(255, 84, 112, 0.4)',
  borderRadius: 6,
  fontSize: 11,
  color: '#ffaab5',
  marginBottom: 12,
}
