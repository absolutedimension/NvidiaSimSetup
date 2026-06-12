import axios from 'axios'
import type { AgentKind } from '../store/store'

const baseFor = (agent: AgentKind): string => {
  switch (agent) {
    case 'material':
      return 'http://localhost:8000'
    case 'physics':
      return 'http://localhost:8002'
    case 'texture':
      return 'http://localhost:8004'
    case 'composer':
      return 'http://localhost:8005'
  }
}

export async function uploadUsd(
  agent: AgentKind,
  file: File,
): Promise<string> {
  const form = new FormData()
  form.append('usd_file', file)
  const { data } = await axios.post(
    `${baseFor(agent)}/pipeline/upload-usd`,
    form,
  )
  return data.session_id as string
}

export interface StartOptions {
  userEmail?: string
  vlmModel?: string
  materialLibrary?: string
  userPrompt?: string
}

export async function startPipeline(
  agent: AgentKind,
  sessionId: string,
  opts: StartOptions = {},
): Promise<void> {
  const form = new FormData()
  form.append('session_id', sessionId)
  if (agent === 'material') {
    form.append('user_email', opts.userEmail ?? 'studio@trigunai.com')
    form.append('vlm_model', opts.vlmModel ?? 'gpt-4o-mini')
    form.append('material_library', opts.materialLibrary ?? 'default')
  } else if (agent === 'texture') {
    if (opts.userPrompt) form.append('user_prompt', opts.userPrompt)
  }
  await axios.post(`${baseFor(agent)}/pipeline`, form)
}

export interface PipelineStatusBody {
  session_id: string
  status: string
  current_step: any
  completed_steps: any[]
  overall_progress: { current_step: number; total_steps: number; percent: number }
  elapsed_seconds: number
}

export async function pollStatus(
  agent: AgentKind,
  sessionId: string,
): Promise<PipelineStatusBody> {
  const { data } = await axios.get(
    `${baseFor(agent)}/pipeline/${sessionId}/status`,
  )
  return data
}

export function renderUrl(agent: AgentKind, sessionId: string): string {
  return `${baseFor(agent)}/artifacts/${sessionId}/final-render`
}

export interface ComposerSubmit {
  lat: number
  lon: number
  radius: number
  name: string
  prompt: string
}

export interface ComposerPreset {
  id: string
  label: string
  lat: number
  lon: number
  radius: number
}

export async function startComposerPipeline(
  s: ComposerSubmit,
): Promise<string> {
  const { data } = await axios.post(`${baseFor('composer')}/pipeline`, s, {
    headers: { 'content-type': 'application/json' },
  })
  return data.session_id as string
}

export function composerArtifactUrl(
  sessionId: string,
  kind: 'usd' | 'textures' | 'meta' | 'preview-glb' = 'preview-glb',
): string {
  return `${baseFor('composer')}/artifacts/${sessionId}/${kind}`
}

export async function getComposerPresets(): Promise<ComposerPreset[]> {
  try {
    const { data } = await axios.get(`${baseFor('composer')}/pipeline/presets`, {
      timeout: 3000,
    })
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

export async function getPredictions(
  agent: AgentKind,
  sessionId: string,
): Promise<any[]> {
  try {
    const { data } = await axios.get(
      `${baseFor(agent)}/artifacts/${sessionId}/predictions`,
    )
    if (Array.isArray(data)) return data
    if (typeof data === 'string') {
      return data
        .split('\n')
        .filter(Boolean)
        .map((l) => JSON.parse(l))
    }
    if (data?.predictions) return data.predictions
    return [data]
  } catch {
    return []
  }
}

export async function healthCheck(agent: AgentKind): Promise<boolean> {
  try {
    const { data } = await axios.get(`${baseFor(agent)}/health`, { timeout: 3000 })
    return data?.status === 'healthy'
  } catch {
    return false
  }
}
