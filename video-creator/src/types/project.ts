export interface Scene {
  id: string;
  title: string;
  text: string;
  tone: string;
  gender: 'female' | 'male';
  speed: number;
  template: string;
  // Generated assets
  voiceUrl?: string;
  voiceDuration?: number;
  slideUrl?: string;
  slideConfig?: SlideConfig;
}

export interface SlideConfig {
  title: string;
  body: string;
  accentColor: string;
  layout: 'center' | 'left' | 'split' | 'bullets' | 'screenshot';
  subtitle?: string;
  bulletPoints?: string[];
  screenshotPath?: string;
}

export interface MusicConfig {
  prompt: string;
  durationSeconds: number;
  volume: number;
  audioUrl?: string;
}

export interface Project {
  name: string;
  scenes: Scene[];
  music: MusicConfig;
  presenterImage?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Voice {
  name: string;
  gender: string;
  tone: string;
  use_when: string;
  tags: string[];
  preview_url: string;
}

export interface JobStatus {
  status: 'processing' | 'completed' | 'failed' | 'not_found';
  progress?: number;
  step?: string;
  segments?: any[];
  audio_url?: string;
  video_url?: string;
  duration?: number;
  size_mb?: number;
}

export const TONES = [
  { value: 'female_confident', label: 'Confident (F)', gender: 'female', emoji: '💪' },
  { value: 'female_excited', label: 'Excited (F)', gender: 'female', emoji: '🎉' },
  { value: 'female_calm', label: 'Calm (F)', gender: 'female', emoji: '🧘' },
  { value: 'female_friendly', label: 'Friendly (F)', gender: 'female', emoji: '😊' },
  { value: 'male_confident', label: 'Confident (M)', gender: 'male', emoji: '💪' },
  { value: 'male_excited', label: 'Excited (M)', gender: 'male', emoji: '🎉' },
  { value: 'male_calm', label: 'Calm (M)', gender: 'male', emoji: '🧘' },
  { value: 'male_friendly', label: 'Friendly (M)', gender: 'male', emoji: '😊' },
];

export const TEMPLATES = [
  { value: 'T1', label: 'Talking Head', desc: 'Presenter on camera', icon: '🎤' },
  { value: 'T2', label: 'Screen Recording', desc: 'Software walkthrough', icon: '🖥️' },
  { value: 'T3', label: 'Tablet Annotation', desc: 'Khan Academy style drawing', icon: '✏️' },
  { value: 'T4', label: 'Live Demo + PiP', desc: 'Hardware + screen', icon: '📹' },
  { value: 'T5', label: 'Diagram', desc: 'Architecture/flow diagram', icon: '📊' },
  { value: 'T6', label: 'Motion Graphics', desc: 'Animated slides', icon: '✨' },
  { value: 'T7', label: 'Workshop', desc: 'Extended build-along', icon: '🔧' },
];

export const MUSIC_PRESETS = [
  { label: 'Inspiring Corporate', prompt: 'Ambient electronic, inspiring, warm, subtle build, professional presentation, corporate background music' },
  { label: 'Calm Ambient', prompt: 'Soft ambient pads, gentle piano, peaceful, meditation, warm, no drums, relaxing background' },
  { label: 'Energetic Tech', prompt: 'Upbeat electronic, tech startup energy, synth, modern, motivating, medium tempo' },
  { label: 'Emotional Piano', prompt: 'Solo piano, emotional, reflective, gentle, cinematic, minimal, touching' },
  { label: 'Lo-fi Study', prompt: 'Lo-fi hip hop beats, chill, study music, vinyl crackle, mellow jazz chords, relaxing' },
  { label: 'Epic Cinematic', prompt: 'Epic orchestral, building tension, cinematic, dramatic, strings, brass, powerful' },
];
