import { useEffect, useRef, useState } from 'react'
import { useStudio, type AgentKind } from '../store/store'
import {
  healthCheck,
  uploadUsd,
  startPipeline,
  pollStatus,
  renderUrl,
  getPredictions,
} from '../api/agents'
import { ComposerControls } from './ComposerControls'

const AGENTS: { kind: AgentKind; label: string; tagline: string }[] = [
  { kind: 'material', label: 'Material', tagline: 'Assign PBR materials' },
  { kind: 'physics', label: 'Physics', tagline: 'Tag mass / friction / collision' },
  { kind: 'texture', label: 'Texture', tagline: 'Generate texture maps' },
  { kind: 'composer', label: 'Scene Composer', tagline: 'OSM → AI-textured city' },
]

export function AgentControls() {
  const {
    agent,
    setAgent,
    status,
    setSession,
    setStatus,
    patchStatus,
    sessionId,
    fileName,
    reset,
  } = useStudio()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [userPrompt, setUserPrompt] = useState('worn, slightly weathered surface')
  const [health, setHealth] = useState<Record<AgentKind, boolean | null>>({
    material: null,
    physics: null,
    texture: null,
    composer: null,
  })

  useEffect(() => {
    let mounted = true
    const refresh = async () => {
      for (const a of ['material', 'physics', 'texture', 'composer'] as AgentKind[]) {
        const ok = await healthCheck(a)
        if (!mounted) return
        setHealth((h) => ({ ...h, [a]: ok }))
      }
    }
    refresh()
    const interval = setInterval(refresh, 15000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const onUpload = async (file: File) => {
    reset()
    setSession(null, file.name)
    setStatus('uploading')
    try {
      const id = await uploadUsd(agent, file)
      setSession(id, file.name)
      setStatus('queued')
      await startPipeline(agent, id, { userPrompt })
      setStatus('running')
      pollLoop(agent, id)
    } catch (err: any) {
      setStatus('failed', err?.message ?? 'Upload failed')
    }
  }

  const pollLoop = async (a: AgentKind, id: string) => {
    let consecutiveErrors = 0
    while (true) {
      try {
        const s = await pollStatus(a, id)
        consecutiveErrors = 0
        patchStatus({
          currentStep: s.current_step?.name ?? null,
          percent: s.overall_progress?.percent ?? 0,
          elapsedSec: s.elapsed_seconds ?? 0,
          completedSteps: (s.completed_steps ?? []).map((c: any) => ({
            name: c.name,
            displayName: c.display_name,
            durationSeconds: c.duration_seconds,
          })),
        })
        if (s.status === 'completed') {
          const preds = await getPredictions(a, id)
          patchStatus({
            predictions: preds.map((p: any) => ({
              id: p.id ?? '?',
              label:
                p?.materials?.material ??
                p?.classification?.material ??
                p?.classification?.classification ??
                JSON.stringify(p).slice(0, 80),
              raw: p,
            })),
            outputRenderUrl: renderUrl(a, id),
          })
          setStatus('completed')
          return
        }
        if (s.status === 'failed' || s.status === 'cancelled') {
          setStatus('failed', `Pipeline ${s.status}`)
          return
        }
      } catch (err: any) {
        consecutiveErrors++
        if (consecutiveErrors > 5) {
          setStatus('failed', `Lost connection to ${a} agent`)
          return
        }
      }
      await new Promise((r) => setTimeout(r, 3000))
    }
  }

  const busy = status === 'uploading' || status === 'queued' || status === 'running'

  return (
    <div style={panelStyle}>
      <h2 style={{ margin: '0 0 12px', fontSize: 18, fontWeight: 600 }}>
        TrigunAI Asset Studio
      </h2>
      <div style={{ opacity: 0.6, fontSize: 12, marginBottom: 20 }}>
        Phase A — Material / Physics / Texture
      </div>

      <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 6 }}>AGENT</div>
      <div style={{ display: 'grid', gap: 8, marginBottom: 18 }}>
        {AGENTS.map((a) => (
          <button
            key={a.kind}
            disabled={busy}
            onClick={() => setAgent(a.kind)}
            style={tabButtonStyle(agent === a.kind, busy)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600 }}>{a.label}</span>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  background:
                    health[a.kind] === null
                      ? '#666'
                      : health[a.kind]
                        ? '#3ee07a'
                        : '#ff5470',
                }}
                title={
                  health[a.kind] === null
                    ? 'unknown'
                    : health[a.kind]
                      ? 'healthy'
                      : 'unreachable'
                }
              />
            </div>
            <div style={{ fontSize: 11, opacity: 0.65, marginTop: 4 }}>
              {a.tagline}
            </div>
          </button>
        ))}
      </div>

      {agent === 'texture' && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 6 }}>
            STYLE PROMPT
          </div>
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            rows={2}
            disabled={busy}
            style={textareaStyle}
          />
        </div>
      )}

      {agent === 'composer' ? (
        <ComposerControls disabled={busy} />
      ) : (
        <>
          <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 6 }}>ASSET</div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".usd,.usda,.usdz,.usdc"
            style={{ display: 'none' }}
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) onUpload(f)
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
            style={primaryButton(busy)}
          >
            {busy ? 'Working…' : 'Upload USD'}
          </button>
        </>
      )}

      {fileName && (
        <div style={{ fontSize: 12, opacity: 0.65, marginTop: 10 }}>
          {agent === 'composer' ? '🌆' : '📄'} {fileName}
        </div>
      )}
      {sessionId && (
        <div style={{ fontSize: 11, opacity: 0.45, marginTop: 4 }}>
          session: {sessionId.slice(0, 8)}…
        </div>
      )}
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  position: 'absolute',
  top: 16,
  left: 16,
  width: 280,
  background: 'rgba(20, 22, 27, 0.85)',
  backdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 12,
  padding: 18,
  zIndex: 10,
  boxShadow: '0 6px 30px rgba(0,0,0,0.4)',
}

const tabButtonStyle = (active: boolean, disabled: boolean): React.CSSProperties => ({
  padding: '10px 12px',
  background: active ? 'rgba(74,158,255,0.15)' : 'rgba(255,255,255,0.04)',
  border: `1px solid ${active ? 'rgba(74,158,255,0.6)' : 'rgba(255,255,255,0.08)'}`,
  borderRadius: 8,
  color: '#e4e6eb',
  textAlign: 'left',
  cursor: disabled ? 'not-allowed' : 'pointer',
  opacity: disabled ? 0.4 : 1,
  transition: 'all 0.15s',
})

const textareaStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 6,
  color: '#e4e6eb',
  padding: 8,
  fontFamily: 'inherit',
  fontSize: 12,
  resize: 'vertical',
  boxSizing: 'border-box',
}

const primaryButton = (disabled: boolean): React.CSSProperties => ({
  width: '100%',
  padding: '11px 14px',
  background: disabled ? '#1f2937' : '#4a9eff',
  color: disabled ? '#666' : '#fff',
  border: 'none',
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: disabled ? 'not-allowed' : 'pointer',
  transition: 'background 0.15s',
})
