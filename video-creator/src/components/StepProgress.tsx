import { useProjectStore } from '../store/projectStore';

const STEPS = [
  { num: 1, label: 'Script', icon: '📝' },
  { num: 2, label: 'Voice', icon: '🎙️' },
  { num: 3, label: 'Visuals', icon: '🎨' },
  { num: 4, label: 'Music', icon: '🎵' },
  { num: 5, label: 'Render', icon: '🎬' },
];

export default function StepProgress() {
  const { step, setStep } = useProjectStore();

  return (
    <div className="flex items-center justify-center gap-2 py-4 px-6 bg-gray-900/80 border-b border-gray-800">
      {STEPS.map((s, i) => (
        <div key={s.num} className="flex items-center">
          <button
            onClick={() => setStep(s.num)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all
              ${step === s.num
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                : step > s.num
                  ? 'bg-green-900/40 text-green-400 border border-green-800'
                  : 'bg-gray-800/50 text-gray-500 border border-gray-700'
              }`}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
            {step > s.num && <span className="text-green-400">✓</span>}
          </button>
          {i < STEPS.length - 1 && (
            <div className={`w-8 h-0.5 mx-1 ${step > s.num ? 'bg-green-700' : 'bg-gray-800'}`} />
          )}
        </div>
      ))}
    </div>
  );
}
