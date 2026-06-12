const getApiUrl = () => {
  try {
    const stored = JSON.parse(localStorage.getItem('trigunai-video-creator') || '{}');
    if (stored?.state?.apiUrl) return stored.state.apiUrl;
  } catch {}
  // In production (same-origin), API is proxied by nginx — use empty string
  if (window.location.hostname !== 'localhost') return '';
  return import.meta.env.VITE_API_URL || 'http://localhost:8010';
};

async function apiFetch(path: string, options: RequestInit = {}) {
  const url = `${getApiUrl()}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return res.json();
}

// ============================================================
// Project (queue-based)
// ============================================================

export interface CreateVideoInput {
  project_name: string;
  scenes: {
    id: string;
    title: string;
    text: string;
    tone: string;
    speed: number;
    template: string;
    slide_title?: string;
    slide_body?: string;
    slide_accent?: string;
    slide_layout?: string;
  }[];
  music_prompt: string;
  music_volume: number;
  presenter_image?: string;
  generate_avatar?: boolean;
  background_shader?: string;
}

export const createVideoProject = (input: CreateVideoInput) =>
  apiFetch('/api/project/create', {
    method: 'POST',
    body: JSON.stringify(input),
  });

// ============================================================
// Shaders — backgrounds, incl. GLSL pasted from Shader Studio
// ============================================================

export interface ShaderInfo {
  id: string;
  name: string;
  desc: string;
  category: string;
  custom: boolean;
  preview_url: string | null;
}

export const listShaders = (): Promise<{ shaders: ShaderInfo[] }> =>
  apiFetch('/api/shaders');

// Paste raw Shader Studio GLSL -> auto-translated, validated, registered.
export const addCustomShader = (name: string, glsl: string) =>
  apiFetch('/api/shader/custom', {
    method: 'POST',
    body: JSON.stringify({ name, glsl }),
  });

export const renderShaderBg = (shader: string, duration: number, audio_url?: string) =>
  apiFetch('/api/shader/render-bg', {
    method: 'POST',
    body: JSON.stringify({ shader, duration, audio_url }),
  });

export const getProjectStatus = (projectId: string) =>
  apiFetch(`/api/project/${projectId}`);

export const getJobStatus = (jobId: string) =>
  apiFetch(`/api/job/${jobId}`);

export const getQueueStats = () =>
  apiFetch('/api/queue/stats');

export const listProjects = () =>
  apiFetch('/api/projects');

// ============================================================
// Voice (direct preview — bypasses queue)
// ============================================================

export const generateVoice = (text: string, tone: string, speed: number) =>
  apiFetch('/api/voice/generate', {
    method: 'POST',
    body: JSON.stringify({ text, tone, speed }),
  });

export const getVoices = () => apiFetch('/api/voices');

// ============================================================
// Upload
// ============================================================

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const url = `${getApiUrl()}/api/upload`;
  const res = await fetch(url, { method: 'POST', body: formData });
  return res.json();
};

// ============================================================
// Slides (preview + generate)
// ============================================================

export const previewSlide = (config: { title: string; body?: string; accent_color?: string; layout?: string }) =>
  apiFetch('/api/slides/preview', { method: 'POST', body: JSON.stringify(config) });

export const generateSlides = (scenes: any[]) =>
  apiFetch('/api/slides/generate', { method: 'POST', body: JSON.stringify({ scenes }) });

// ============================================================
// Music
// ============================================================

export const generateMusic = (prompt: string, durationSeconds: number) =>
  apiFetch('/api/music/generate', { method: 'POST', body: JSON.stringify({ prompt, duration_seconds: durationSeconds }) });

// ============================================================
// Batch voice
// ============================================================

export const generateAllVoices = (scenes: { id: string; text: string; tone: string; speed: number }[]) =>
  apiFetch('/api/voice/generate-all', { method: 'POST', body: JSON.stringify({ scenes }) });

// ============================================================
// Upload image
// ============================================================

export const uploadImage = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const url = `${getApiUrl()}/api/upload`;
  const res = await fetch(url, { method: 'POST', body: formData });
  return res.json();
};

// ============================================================
// Health
// ============================================================

export const getHealth = () => apiFetch('/api/health');

// ============================================================
// WebSocket — real-time project progress
// ============================================================

export function connectProjectWS(
  projectId: string,
  onMessage: (data: any) => void,
  onError?: (err: Event) => void
): WebSocket {
  const apiUrl = getApiUrl();
  const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
  const ws = new WebSocket(`${wsUrl}/ws/project/${projectId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.warn('WS parse error:', event.data);
    }
  };

  ws.onerror = (err) => {
    console.error('WS error:', err);
    onError?.(err);
  };

  // Request initial status
  ws.onopen = () => {
    ws.send('status');
  };

  return ws;
}
