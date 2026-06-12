import { useProjectStore } from '../store/projectStore';
import { TONES, TEMPLATES, type Scene } from '../types/project';

const SAMPLE_SCENES: Omit<Scene, 'id'>[] = [
  {
    title: "Hook",
    text: "What if I told you, that by the end of today, your first VR scene will be running on your Quest headset? Not a tutorial someone else built. YOUR scene, running on YOUR headset.",
    tone: "female_confident", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_01_hook.wav", voiceDuration: 11.2,
    slideUrl: "/samples/slides/slide_02.png",
  },
  {
    title: "The Promise",
    text: "By the end of this course, you will have built a complete VR and Mixed Reality application. With hand tracking. With spatial audio. With Mixed Reality passthrough. With multiplayer. And you will have submitted it to Meta's Store.",
    tone: "female_confident", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_02_promise.wav", voiceDuration: 18.5,
    slideUrl: "/samples/slides/slide_03.png",
  },
  {
    title: "AI Coding Reveal",
    text: "Here's what makes this course different. You won't be typing code by hand! We use AI coding agents like Claude Code to write our C sharp scripts. You describe what you want in plain English. The AI writes the code. You test it in VR. Even if you've never coded before, you can build a real VR app.",
    tone: "female_excited", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_03_ai_reveal.wav", voiceDuration: 28.4,
    slideUrl: "/samples/slides/slide_05.png",
  },
  {
    title: "The Journey",
    text: "Here's the journey. Module One, setup. Module Two, your AI coding partner. Modules Three through Eight, hands, UI, audio, movement, saving, and multiplayer. Module Nine, Mixed Reality and passthrough. Module Ten, performance polish. And Module Eleven, we ship it to Meta's Store.",
    tone: "female_friendly", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_04_journey.wav", voiceDuration: 35.1,
    slideUrl: "/samples/slides/slide_09.png",
  },
  {
    title: "Credibility",
    text: "This course is built by TrigunAI Innovations. We built GuruLok, A Spiritual Multiverse, currently live on the Meta Quest Store. Every bug we hit, every fix we found, that's in this course. Not theory. Real experience from a real shipped app.",
    tone: "female_calm", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_05_credibility.wav", voiceDuration: 22.8,
    slideUrl: "/samples/slides/slide_13.png",
  },
  {
    title: "For You",
    text: "This course is for CS students who want a real portfolio piece. For working developers adding XR to their skillset. For creators with ideas who need the technical skills. No coding experience needed. The AI handles the code. You handle the vision.",
    tone: "female_friendly", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_06_students.wav", voiceDuration: 19.3,
    slideUrl: "/samples/slides/slide_15.png",
  },
  {
    title: "Let's Build",
    text: "Are you ready? Unity is free. Claude Code is free. Your Quest headset is waiting. Let's build.",
    tone: "female_excited", gender: "female", speed: 0.75, template: "T6",
    voiceUrl: "/samples/voice/scene_07_cta.wav", voiceDuration: 10.2,
    slideUrl: "/samples/slides/slide_17.png",
  },
];

export default function ScriptEditor() {
  const { scenes, setScenes, addScene, removeScene, updateScene, setStep, projectName, setProjectName } = useProjectStore();

  const loadSample = () => {
    const sampleWithIds = SAMPLE_SCENES.map((s, i) => ({
      ...s,
      id: `sample_${Date.now()}_${i}`,
    }));
    setScenes(sampleWithIds);
    setProjectName("VR/MR Course — Welcome Video");
  };

  const wordCount = (text: string) => text.split(/\s+/).filter(Boolean).length;
  const estDuration = (text: string) => Math.round(wordCount(text) / 2.2); // ~2.2 words/sec at 0.75 speed

  const totalWords = scenes.reduce((sum, s) => sum + wordCount(s.text), 0);
  const totalDuration = scenes.reduce((sum, s) => sum + estDuration(s.text), 0);

  return (
    <div className="max-w-5xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="text-3xl font-bold bg-transparent border-none outline-none text-white flex-1 placeholder-gray-600"
            placeholder="Project Name"
          />
          <button
            onClick={loadSample}
            className="px-4 py-2 bg-purple-600/20 border border-purple-700 hover:bg-purple-600/40 text-purple-300 rounded-lg text-sm transition whitespace-nowrap"
          >
            Load Sample Project
          </button>
        </div>
        <p className="text-gray-500 mt-2">
          {scenes.length} scenes · {totalWords} words · ~{Math.floor(totalDuration / 60)}m {totalDuration % 60}s estimated
        </p>
      </div>

      {/* Scenes */}
      <div className="space-y-4">
        {scenes.map((scene, index) => (
          <div key={scene.id} className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
            {/* Scene header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </span>
                <input
                  type="text"
                  value={scene.title}
                  onChange={(e) => updateScene(scene.id, { title: e.target.value })}
                  className="bg-transparent border-none outline-none text-white font-semibold text-lg placeholder-gray-600"
                  placeholder={`Scene ${index + 1} title`}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {wordCount(scene.text)} words · ~{estDuration(scene.text)}s
                </span>
                {scenes.length > 1 && (
                  <button
                    onClick={() => removeScene(scene.id)}
                    className="text-red-500 hover:text-red-400 text-sm px-2"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>

            {/* Text */}
            <textarea
              value={scene.text}
              onChange={(e) => updateScene(scene.id, { text: e.target.value })}
              rows={4}
              className="w-full bg-gray-800/50 border border-gray-700 rounded-lg p-3 text-gray-200 text-sm resize-y outline-none focus:border-blue-600 transition"
              placeholder="Write the script for this scene..."
            />

            {/* Controls row */}
            <div className="flex flex-wrap gap-3 mt-3">
              {/* Tone */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 uppercase tracking-wider">Tone</label>
                <select
                  value={scene.tone}
                  onChange={(e) => {
                    const tone = TONES.find(t => t.value === e.target.value);
                    updateScene(scene.id, {
                      tone: e.target.value,
                      gender: (tone?.gender as 'male' | 'female') || 'female',
                    });
                  }}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 outline-none"
                >
                  <optgroup label="Female">
                    {TONES.filter(t => t.gender === 'female').map(t => (
                      <option key={t.value} value={t.value}>{t.emoji} {t.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Male">
                    {TONES.filter(t => t.gender === 'male').map(t => (
                      <option key={t.value} value={t.value}>{t.emoji} {t.label}</option>
                    ))}
                  </optgroup>
                </select>
              </div>

              {/* Speed */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 uppercase tracking-wider">Speed</label>
                <input
                  type="range"
                  min="0.65"
                  max="1.0"
                  step="0.05"
                  value={scene.speed}
                  onChange={(e) => updateScene(scene.id, { speed: parseFloat(e.target.value) })}
                  className="w-20"
                />
                <span className="text-xs text-gray-400 w-8">{scene.speed}</span>
              </div>

              {/* Template */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500 uppercase tracking-wider">Visual</label>
                <select
                  value={scene.template}
                  onChange={(e) => updateScene(scene.id, { template: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 outline-none"
                >
                  {TEMPLATES.map(t => (
                    <option key={t.value} value={t.value}>{t.icon} {t.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Scene + Import */}
      <div className="flex gap-3 mt-4">
        <button
          onClick={addScene}
          className="flex-1 py-3 border-2 border-dashed border-gray-700 rounded-xl text-gray-500 hover:border-blue-600 hover:text-blue-400 transition"
        >
          + Add Scene
        </button>
        <label className="py-3 px-6 border border-gray-700 rounded-xl text-gray-500 hover:border-blue-600 hover:text-blue-400 transition cursor-pointer text-center">
          Import JSON
          <input
            type="file"
            accept=".json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const reader = new FileReader();
              reader.onload = (ev) => {
                try {
                  const project = JSON.parse(ev.target?.result as string);
                  if (project.scenes) {
                    setScenes(project.scenes);
                    if (project.name) setProjectName(project.name);
                  }
                } catch { alert('Invalid project JSON'); }
              };
              reader.readAsText(file);
            }}
          />
        </label>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-8">
        <div />
        <button
          onClick={() => setStep(2)}
          disabled={scenes.some(s => !s.text.trim())}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl font-semibold transition"
        >
          Next: Generate Voice →
        </button>
      </div>
    </div>
  );
}
