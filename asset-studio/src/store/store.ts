import { create } from 'zustand'

export type AgentKind = 'material' | 'physics' | 'texture' | 'composer'

export type PipelineStatus =
  | 'idle'
  | 'uploading'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'

export type StepInfo = {
  name: string
  displayName?: string
  durationSeconds?: number
}

export type Prediction = {
  id: string
  label: string
  raw?: any
}

export interface StudioState {
  // Backend
  backendUrl: {
    material: string
    physics: string
    texture: string
    composer: string
  }

  // Session
  sessionId: string | null
  agent: AgentKind
  fileName: string | null
  status: PipelineStatus
  errorMessage: string | null

  // Progress
  currentStep: string | null
  percent: number
  elapsedSec: number
  completedSteps: StepInfo[]
  predictions: Prediction[]
  outputRenderUrl: string | null
  outputGlbUrl: string | null

  // Actions
  setAgent: (a: AgentKind) => void
  setSession: (id: string | null, fileName?: string | null) => void
  setStatus: (s: PipelineStatus, error?: string | null) => void
  patchStatus: (p: Partial<StudioState>) => void
  reset: () => void
}

const initial = {
  sessionId: null,
  fileName: null,
  status: 'idle' as PipelineStatus,
  errorMessage: null,
  currentStep: null,
  percent: 0,
  elapsedSec: 0,
  completedSteps: [] as StepInfo[],
  predictions: [] as Prediction[],
  outputRenderUrl: null,
  outputGlbUrl: null,
}

export const useStudio = create<StudioState>((set) => ({
  backendUrl: {
    material: 'http://localhost:8000',
    physics: 'http://localhost:8002',
    texture: 'http://localhost:8004',
    composer: 'http://localhost:8005',
  },
  agent: 'material',
  ...initial,

  setAgent: (agent) => set({ agent }),
  setSession: (id, fileName = null) => set({ sessionId: id, fileName }),
  setStatus: (status, error = null) => set({ status, errorMessage: error }),
  patchStatus: (p) => set(p as any),
  reset: () => set({ ...initial }),
}))
