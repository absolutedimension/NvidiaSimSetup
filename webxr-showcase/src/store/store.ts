import { create } from 'zustand'

export interface Showcase {
  id: string
  label: string
  /** Either glbUrl (static or animated glTF) OR trajectoryUrl (stick figure) must be set. */
  glbUrl?: string
  /** When set, render via StickFigureAnimation instead of useGLTF (AMP-style trajectories). */
  trajectoryUrl?: string
  description?: string
  scale?: number
  yOffset?: number
  recommendedSpawn?: [number, number, number]
  /** Optional second renderer for side-by-side comparison (e.g. stick figure
   * next to a retargeted character). When set, both are rendered together. */
  compareTrajectoryUrl?: string
  compareGlbUrl?: string
  compareXOffset?: number
  compareLabel?: string
}

interface State {
  showcases: Showcase[]
  selectedId: string | null
  loaded: boolean
  loadError: string | null
  setShowcases: (s: Showcase[]) => void
  select: (id: string | null) => void
  setLoaded: (l: boolean) => void
  setError: (e: string | null) => void
}

export const useStore = create<State>((set) => ({
  showcases: [],
  selectedId: null,
  loaded: false,
  loadError: null,
  setShowcases: (showcases) => set({ showcases }),
  select: (selectedId) => set({ selectedId, loaded: false, loadError: null }),
  setLoaded: (loaded) => set({ loaded }),
  setError: (loadError) => set({ loadError, loaded: false }),
}))
