import { useEffect, useState } from 'react'
import { useStudio } from '../store/store'
import {
  startComposerPipeline,
  pollStatus,
  composerArtifactUrl,
  getComposerPresets,
  type ComposerPreset,
} from '../api/agents'

const DEFAULT_PROMPT =
  'modern glass office tower façade, photoreal, daylight, sharp PBR'

export function ComposerControls({ disabled }: { disabled: boolean }) {
  const { setStatus, setSession, patchStatus, reset } = useStudio()
  const [presets, setPresets] = useState<ComposerPreset[]>([])
  const [presetId, setPresetId] = useState<string | 'custom'>('manhattan_times_sq')
  const [lat, setLat] = useState(40.7580)
  const [lon, setLon] = useState(-73.9855)
  const [radius, setRadius] = useState(500)
  const [name, setName] = useState('manhattan_times_sq')
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT)

  useEffect(() => {
    getComposerPresets().then((p) => {
      if (p.length) setPresets(p)
    })
  }, [])

  const onPreset = (id: string) => {
    setPresetId(id)
    if (id === 'custom') return
    const p = presets.find((x) => x.id === id)
    if (!p) return
    setLat(p.lat)
    setLon(p.lon)
    setRadius(p.radius)
    setName(p.id)
  }

  const onBuild = async () => {
    if (disabled) return
    if (!/^[a-zA-Z0-9_-]{1,40}$/.test(name)) {
      setStatus('failed', 'Name must be 1–40 chars, alphanumeric/_/-')
      return
    }
    reset()
    setSession(null, `${name} (OSM ${radius}m)`)
    setStatus('queued')
    try {
      const id = await startComposerPipeline({ lat, lon, radius, name, prompt })
      setSession(id, `${name} (OSM ${radius}m)`)
      setStatus('running')
      pollLoop(id)
    } catch (err: any) {
      const msg =
        err?.response?.data?.error ??
        err?.message ??
        'Failed to start composer pipeline'
      setStatus('failed', msg)
    }
  }

  const pollLoop = async (id: string) => {
    let errs = 0
    while (true) {
      try {
        const s = await pollStatus('composer', id)
        errs = 0
        patchStatus({
          currentStep: s.current_step?.display_name ?? s.current_step?.name ?? null,
          percent: s.overall_progress?.percent ?? 0,
          elapsedSec: s.elapsed_seconds ?? 0,
          completedSteps: (s.completed_steps ?? []).map((c: any) => ({
            name: c.name,
            displayName: c.display_name,
            durationSeconds: c.duration_seconds,
          })),
        })
        if (s.status === 'completed') {
          patchStatus({ outputGlbUrl: composerArtifactUrl(id, 'preview-glb') })
          setStatus('completed')
          return
        }
        if (s.status === 'failed' || s.status === 'cancelled') {
          setStatus('failed', (s as any).error ?? `Pipeline ${s.status}`)
          return
        }
      } catch {
        errs++
        if (errs > 5) {
          setStatus('failed', 'Lost connection to composer bridge')
          return
        }
      }
      await new Promise((r) => setTimeout(r, 3000))
    }
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div>
        <div style={labelStyle}>PRESET</div>
        <select
          value={presetId}
          disabled={disabled}
          onChange={(e) => onPreset(e.target.value)}
          style={selectStyle}
        >
          {(presets.length
            ? presets
            : [{ id: 'manhattan_times_sq', label: 'Manhattan / Times Sq', lat, lon, radius }]
          ).map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
          <option value="custom">Custom lat/lon…</option>
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <NumField
          label="LAT"
          value={lat}
          step={0.0001}
          disabled={disabled}
          onChange={(v) => { setLat(v); setPresetId('custom') }}
        />
        <NumField
          label="LON"
          value={lon}
          step={0.0001}
          disabled={disabled}
          onChange={(v) => { setLon(v); setPresetId('custom') }}
        />
      </div>

      <div>
        <div style={{ ...labelStyle, display: 'flex', justifyContent: 'space-between' }}>
          <span>RADIUS</span>
          <span style={{ opacity: 0.5 }}>{radius} m</span>
        </div>
        <input
          type="range"
          min={100}
          max={1500}
          step={50}
          value={radius}
          disabled={disabled}
          onChange={(e) => { setRadius(Number(e.target.value)); setPresetId('custom') }}
          style={{ width: '100%' }}
        />
      </div>

      <div>
        <div style={labelStyle}>NAME</div>
        <input
          type="text"
          value={name}
          disabled={disabled}
          onChange={(e) => setName(e.target.value)}
          style={textInputStyle}
          spellCheck={false}
        />
      </div>

      <div>
        <div style={labelStyle}>FAÇADE PROMPT</div>
        <textarea
          value={prompt}
          rows={3}
          disabled={disabled}
          onChange={(e) => setPrompt(e.target.value)}
          style={textareaStyle}
        />
      </div>

      <button onClick={onBuild} disabled={disabled} style={primaryButton(disabled)}>
        {disabled ? 'Working…' : 'Build City'}
      </button>
    </div>
  )
}

function NumField({
  label, value, step, disabled, onChange,
}: {
  label: string
  value: number
  step: number
  disabled: boolean
  onChange: (v: number) => void
}) {
  return (
    <div>
      <div style={labelStyle}>{label}</div>
      <input
        type="number"
        value={value}
        step={step}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        style={textInputStyle}
      />
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  opacity: 0.7,
  marginBottom: 6,
}

const selectStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 6,
  color: '#e4e6eb',
  padding: '8px 10px',
  fontFamily: 'inherit',
  fontSize: 12,
}

const textInputStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 6,
  color: '#e4e6eb',
  padding: '8px 10px',
  fontFamily: 'inherit',
  fontSize: 12,
  boxSizing: 'border-box',
}

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
