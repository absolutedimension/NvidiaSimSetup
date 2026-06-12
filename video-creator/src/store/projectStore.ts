import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Scene, MusicConfig, Project } from '../types/project';

interface ProjectState {
  // Current step (1-5)
  step: number;
  setStep: (step: number) => void;

  // Project data
  projectName: string;
  setProjectName: (name: string) => void;

  scenes: Scene[];
  setScenes: (scenes: Scene[]) => void;
  addScene: () => void;
  removeScene: (id: string) => void;
  updateScene: (id: string, updates: Partial<Scene>) => void;

  music: MusicConfig;
  setMusic: (music: Partial<MusicConfig>) => void;

  presenterImage: string;
  setPresenterImage: (url: string) => void;

  // Background shader (id from /api/shaders, incl. pasted Shader Studio GLSL)
  backgroundShader: string | null;
  setBackgroundShader: (id: string | null) => void;

  // API base URL
  apiUrl: string;
  setApiUrl: (url: string) => void;

  // Export/Import
  exportProject: () => Project;
  importProject: (project: Project) => void;

  // Global render status
  renderJobId: string | null;
  setRenderJobId: (id: string | null) => void;
}

const defaultScene = (): Scene => ({
  id: `scene_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
  title: '',
  text: '',
  tone: 'female_confident',
  gender: 'female',
  speed: 0.75,
  template: 'T6',
});

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      step: 1,
      setStep: (step) => set({ step }),

      projectName: 'Untitled Video',
      setProjectName: (name) => set({ projectName: name }),

      scenes: [defaultScene()],
      setScenes: (scenes) => set({ scenes }),
      addScene: () => set((s) => ({ scenes: [...s.scenes, defaultScene()] })),
      removeScene: (id) => set((s) => ({
        scenes: s.scenes.filter((sc) => sc.id !== id),
      })),
      updateScene: (id, updates) => set((s) => ({
        scenes: s.scenes.map((sc) => sc.id === id ? { ...sc, ...updates } : sc),
      })),

      music: {
        prompt: 'Ambient electronic, inspiring, warm, subtle build, professional presentation, corporate background music',
        durationSeconds: 300,
        volume: 0.08,
      },
      setMusic: (music) => set((s) => ({ music: { ...s.music, ...music } })),

      presenterImage: '',
      setPresenterImage: (url) => set({ presenterImage: url }),

      backgroundShader: null,
      setBackgroundShader: (id) => set({ backgroundShader: id }),

      apiUrl: 'http://localhost:8010',
      setApiUrl: (apiUrl) => set({ apiUrl }),

      exportProject: () => {
        const s = get();
        return {
          name: s.projectName,
          scenes: s.scenes,
          music: s.music,
          presenterImage: s.presenterImage,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
      },

      importProject: (project) => set({
        projectName: project.name,
        scenes: project.scenes,
        music: project.music,
        presenterImage: project.presenterImage || '',
      }),

      renderJobId: null,
      setRenderJobId: (id) => set({ renderJobId: id }),
    }),
    {
      name: 'trigunai-video-creator',
    }
  )
);
