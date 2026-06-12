import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Screen IDs
type Screen = 'loading' | 'intro' | 'choose' |
  'c1_problem' | 'c2_solution' | 'c3_how' | 'c4_pricing' |
  's1_vision' | 's2_course' | 's3_modules' | 's4_coaching' | 's5_proof';

// Particles background component
function Particles({ count = 60 }) {
  const particles = useRef(
    Array.from({ length: count }, () => ({
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 0.3 + 0.1,
      opacity: Math.random() * 0.5 + 0.1,
      delay: Math.random() * 5,
    }))
  ).current;

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {particles.map((p, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-white animate-pulse"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            opacity: p.opacity,
            animationDuration: `${3 + p.delay}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

// Navigation overlay
function Nav({ screen, onNavigate, onToggleMenu, menuOpen }: {
  screen: Screen;
  onNavigate: (s: Screen) => void;
  onToggleMenu: () => void;
  menuOpen: boolean;
}) {
  const isCreator = screen.startsWith('c');
  const isStudent = screen.startsWith('s');

  return (
    <>
      {/* Top bar */}
      <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4">
        <button onClick={() => onNavigate('choose')} className="flex items-center gap-2 opacity-80 hover:opacity-100 transition">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500 via-white to-blue-500 opacity-80" />
          <span className="text-white font-bold text-lg tracking-tight hidden sm:block">TrigunAI</span>
        </button>

        <div className="flex items-center gap-4">
          {(isCreator || isStudent) && (
            <button
              onClick={() => onNavigate('choose')}
              className="text-white/50 hover:text-white text-sm transition"
            >
              ← Back
            </button>
          )}
          <button
            onClick={onToggleMenu}
            className="text-white/60 hover:text-white text-2xl transition"
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Full-screen menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/90 backdrop-blur-xl flex items-center justify-center"
          >
            <div className="grid grid-cols-2 gap-12 max-w-2xl">
              <div>
                <h3 className="text-blue-400 text-sm uppercase tracking-wider mb-4">For Creators</h3>
                <div className="space-y-3">
                  {[
                    { label: 'The Problem', screen: 'c1_problem' as Screen },
                    { label: 'Video Creator Tool', screen: 'c2_solution' as Screen },
                    { label: 'How It Works', screen: 'c3_how' as Screen },
                    { label: 'Pricing', screen: 'c4_pricing' as Screen },
                  ].map(item => (
                    <button
                      key={item.screen}
                      onClick={() => { onNavigate(item.screen); onToggleMenu(); }}
                      className="block text-white/70 hover:text-white text-lg transition"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-purple-400 text-sm uppercase tracking-wider mb-4">For Students</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Why Learn With Us', screen: 's1_vision' as Screen },
                    { label: 'VR/MR App Course', screen: 's2_course' as Screen },
                    { label: 'Curriculum', screen: 's3_modules' as Screen },
                    { label: 'Live Coaching', screen: 's4_coaching' as Screen },
                    { label: 'Our Story', screen: 's5_proof' as Screen },
                  ].map(item => (
                    <button
                      key={item.screen}
                      onClick={() => { onNavigate(item.screen); onToggleMenu(); }}
                      className="block text-white/70 hover:text-white text-lg transition"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// === SCREEN COMPONENTS ===

function LoadingScreen({ onDone }: { onDone: () => void }) {
  useEffect(() => { const t = setTimeout(onDone, 3000); return () => clearTimeout(t); }, [onDone]);
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black flex items-center justify-center"
    >
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
        className="text-center"
      >
        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-red-500 via-white/80 to-blue-500 animate-spin" style={{ animationDuration: '3s' }} />
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-3xl font-bold bg-gradient-to-r from-red-400 via-white to-blue-400 bg-clip-text text-transparent"
        >
          TRIGUN AI
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.5 }}
          transition={{ delay: 1.5 }}
          className="text-sm text-white/40 mt-2"
        >
          INNOVATIONS
        </motion.p>
      </motion.div>
    </motion.div>
  );
}

function ChooseScreen({ onChoose }: { onChoose: (path: 'creator' | 'student') => void }) {
  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-950 via-[#0a0a1a] to-gray-950 flex items-center justify-center">
      <Particles count={80} />
      <div className="relative z-10 text-center max-w-4xl px-6">
        <motion.p
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 0.6, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-white/50 text-lg mb-4 tracking-wide"
        >
          The future of learning is immersive
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-5xl md:text-7xl font-bold text-white mb-4"
        >
          Where do you
          <br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            want to go?
          </span>
        </motion.h1>

        <div className="flex flex-col sm:flex-row gap-6 justify-center mt-16">
          <motion.button
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.0 }}
            whileHover={{ scale: 1.05, boxShadow: '0 0 40px rgba(59,130,246,0.3)' }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onChoose('creator')}
            className="group relative w-72 h-48 rounded-2xl border border-blue-500/30 bg-blue-950/20 backdrop-blur-sm overflow-hidden cursor-pointer"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 h-full flex flex-col items-center justify-center p-6">
              <span className="text-4xl mb-3">🎬</span>
              <span className="text-white font-bold text-xl">I Create</span>
              <span className="text-blue-300/60 text-sm mt-2">I'm a teacher, creator, or educator</span>
            </div>
          </motion.button>

          <motion.button
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.2 }}
            whileHover={{ scale: 1.05, boxShadow: '0 0 40px rgba(168,85,247,0.3)' }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onChoose('student')}
            className="group relative w-72 h-48 rounded-2xl border border-purple-500/30 bg-purple-950/20 backdrop-blur-sm overflow-hidden cursor-pointer"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 h-full flex flex-col items-center justify-center p-6">
              <span className="text-4xl mb-3">📚</span>
              <span className="text-white font-bold text-xl">I Learn</span>
              <span className="text-purple-300/60 text-sm mt-2">I'm a student, developer, or curious mind</span>
            </div>
          </motion.button>
        </div>
      </div>
    </div>
  );
}

// === CREATOR SCREENS ===

function CreatorProblem({ onNext }: { onNext: () => void }) {
  const lines = [
    { text: 'You have expertise.', delay: 0.3 },
    { text: 'You want to teach.', delay: 1.0 },
    { text: 'But creating professional learning videos takes...', delay: 2.0 },
    { text: '', delay: 3.0 },
    { text: 'Recording studios. Video editors. Voice artists.', delay: 3.5 },
    { text: 'Animators. Weeks of work. Thousands of dollars.', delay: 4.5 },
  ];

  useEffect(() => { const t = setTimeout(onNext, 10000); return () => clearTimeout(t); }, [onNext]);

  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center">
      <Particles count={30} />
      <div className="relative z-10 max-w-2xl px-6">
        {lines.map((line, i) => (
          <motion.p
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: line.text ? 0.8 : 0, x: 0 }}
            transition={{ delay: line.delay, duration: 0.6 }}
            className="text-white/80 text-2xl md:text-3xl font-light mb-3 font-mono"
          >
            {line.text}
          </motion.p>
        ))}
        <motion.p
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 6.0, duration: 0.8 }}
          className="text-3xl md:text-4xl font-bold text-blue-400 mt-12"
        >
          What if you could do it in clicks?
        </motion.p>
      </div>
      <button onClick={onNext} className="fixed bottom-8 right-8 text-white/30 hover:text-white/60 text-sm transition z-20">
        Skip →
      </button>
    </div>
  );
}

function CreatorSolution({ onNext, onTry }: { onNext: () => void; onTry: () => void }) {
  const steps = [
    { icon: '📝', label: 'Script', desc: 'Write your content', color: 'blue' },
    { icon: '🎙️', label: 'Voice', desc: 'AI generates the voice', color: 'purple' },
    { icon: '🎨', label: 'Visuals', desc: 'Auto-designed slides', color: 'green' },
    { icon: '🎵', label: 'Music', desc: 'AI background score', color: 'amber' },
    { icon: '🎬', label: 'Video', desc: 'Rendered & ready', color: 'red' },
  ];

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0a0a1a] to-[#0a0a0f] flex items-center justify-center">
      <Particles count={40} />
      <div className="relative z-10 text-center max-w-5xl px-6">
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl md:text-5xl font-bold text-white mb-4"
        >
          TrigunAI Video Creator
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ delay: 0.3 }}
          className="text-white/50 text-lg mb-16"
        >
          Script → Voice → Visuals → Music → Video. In clicks.
        </motion.p>

        <div className="flex flex-wrap justify-center gap-4 mb-16">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.2 }}
              whileHover={{ scale: 1.08, y: -5 }}
              className="w-36 h-44 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm flex flex-col items-center justify-center p-4 cursor-pointer hover:border-blue-500/50 transition-colors"
            >
              <span className="text-3xl mb-2">{step.icon}</span>
              <span className="text-white font-semibold">{step.label}</span>
              <span className="text-white/40 text-xs mt-1">{step.desc}</span>
              {i < steps.length - 1 && (
                <span className="absolute -right-3 text-white/20 text-lg hidden md:block">→</span>
              )}
            </motion.div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <motion.a
            href="https://learn.trigunai.com"
            target="_blank"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            whileHover={{ scale: 1.05 }}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg transition shadow-lg shadow-blue-600/20 inline-block"
          >
            🚀 Try It Free
          </motion.a>
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.7 }}
            whileHover={{ scale: 1.05 }}
            onClick={onNext}
            className="px-8 py-4 border border-white/20 hover:border-white/40 text-white/70 hover:text-white rounded-xl font-semibold text-lg transition"
          >
            How It Works →
          </motion.button>
        </div>
      </div>
    </div>
  );
}

function CreatorHow({ onNext }: { onNext: () => void }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const steps = [
    { icon: '📝', title: 'Write Your Script', desc: 'Type or paste your content. Break it into scenes. Pick a tone for each — confident, excited, calm, friendly. The AI adapts its voice to match.', color: 'from-blue-600 to-blue-400' },
    { icon: '🎙️', title: 'AI Generates Voice', desc: '8 pre-built voices — 4 female, 4 male, each with 4 emotional tones. F5-TTS clones natural Indian English speech. Studio quality, zero recording.', color: 'from-purple-600 to-purple-400' },
    { icon: '🎨', title: 'Auto-Design Visuals', desc: 'Motion graphics slides with animated particles, text reveals, and Ken Burns effects. Choose colors, layouts, upload screenshots. Or let AI design it all.', color: 'from-green-600 to-green-400' },
    { icon: '🎵', title: 'AI Background Music', desc: 'ACE-Step generates custom background music from a text prompt. "Calm ambient piano" or "Energetic tech startup" — your choice.', color: 'from-amber-600 to-amber-400' },
    { icon: '🎬', title: 'Render & Download', desc: 'GPU renders your video with voice + visuals + music. Progress tracked in real-time. Download your MP4 or share directly.', color: 'from-red-600 to-red-400' },
  ];

  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center overflow-y-auto">
      <Particles count={30} />
      <div className="relative z-10 max-w-3xl px-6 py-20">
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-3xl font-bold text-white text-center mb-12"
        >
          How It Works
        </motion.h2>

        <div className="space-y-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.15 }}
              onClick={() => setExpanded(expanded === i ? null : i)}
              className="rounded-xl border border-white/10 bg-white/5 p-5 cursor-pointer hover:border-white/20 transition"
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center text-xl`}>
                  {step.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-white font-semibold text-lg">{step.title}</h3>
                </div>
                <span className="text-white/30">{expanded === i ? '−' : '+'}</span>
              </div>
              <AnimatePresence>
                {expanded === i && (
                  <motion.p
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 0.7 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="text-white/60 mt-3 pl-16 text-sm overflow-hidden"
                  >
                    {step.desc}
                  </motion.p>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="text-center mt-12"
        >
          <button onClick={onNext} className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition">
            View Pricing →
          </button>
        </motion.div>
      </div>
    </div>
  );
}

function CreatorPricing() {
  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center">
      <Particles count={30} />
      <div className="relative z-10 text-center max-w-4xl px-6">
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-3xl font-bold text-white mb-3"
        >
          Start creating for free
        </motion.h2>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 0.2 }} className="text-white/50 mb-12">
          No credit card required
        </motion.p>

        <div className="flex flex-col sm:flex-row gap-6 justify-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="w-72 rounded-2xl border border-white/10 bg-white/5 p-8 text-left"
          >
            <p className="text-white/50 text-sm uppercase tracking-wider">Free</p>
            <p className="text-4xl font-bold text-white mt-2">₹0</p>
            <p className="text-white/40 text-sm mt-1">forever</p>
            <ul className="mt-6 space-y-3 text-white/60 text-sm">
              <li>✓ 3 videos per month</li>
              <li>✓ 8 AI voices</li>
              <li>✓ Animated slides</li>
              <li>✓ 720p rendering</li>
              <li>✓ Background music</li>
            </ul>
            <a href="https://learn.trigunai.com" target="_blank" className="mt-8 block w-full py-3 border border-white/20 hover:border-white/40 text-white text-center rounded-xl font-semibold transition">
              Get Started
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="w-72 rounded-2xl border border-blue-500/30 bg-blue-950/20 p-8 text-left relative"
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-blue-600 rounded-full text-xs text-white font-semibold">
              Popular
            </div>
            <p className="text-blue-400 text-sm uppercase tracking-wider">Pro</p>
            <p className="text-4xl font-bold text-white mt-2">₹999<span className="text-lg text-white/40">/mo</span></p>
            <p className="text-white/40 text-sm mt-1">cancel anytime</p>
            <ul className="mt-6 space-y-3 text-white/60 text-sm">
              <li>✓ Unlimited videos</li>
              <li>✓ 8 AI voices + custom</li>
              <li>✓ 1080p + 4K rendering</li>
              <li>✓ Priority GPU queue</li>
              <li>✓ Talking avatar (Hallo2)</li>
              <li>✓ Export project files</li>
            </ul>
            <a href="https://learn.trigunai.com" target="_blank" className="mt-8 block w-full py-3 bg-blue-600 hover:bg-blue-500 text-white text-center rounded-xl font-semibold transition shadow-lg shadow-blue-600/20">
              Start Pro
            </a>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

// === STUDENT SCREENS ===

function StudentVision({ onNext }: { onNext: () => void }) {
  useEffect(() => { const t = setTimeout(onNext, 8000); return () => clearTimeout(t); }, [onNext]);
  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center">
      <Particles count={50} />
      <div className="relative z-10 text-center max-w-3xl px-6">
        {[
          { text: 'Learn by building.', delay: 0.3, size: 'text-4xl md:text-6xl' },
          { text: 'Not watching. Building.', delay: 1.5, size: 'text-3xl md:text-5xl' },
          { text: 'Real apps. Real skills. Real portfolio.', delay: 3.0, size: 'text-2xl md:text-3xl' },
        ].map((line, i) => (
          <motion.p
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: line.delay, duration: 0.8 }}
            className={`${line.size} font-bold text-white mb-6`}
          >
            {line.text}
          </motion.p>
        ))}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 5.0 }}
          className="text-purple-400 text-xl mt-8"
        >
          Using AI coding agents — no experience needed.
        </motion.p>
      </div>
      <button onClick={onNext} className="fixed bottom-8 right-8 text-white/30 hover:text-white/60 text-sm transition z-20">
        Skip →
      </button>
    </div>
  );
}

function StudentCourse({ onNext }: { onNext: () => void }) {
  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0a0a1a] to-[#0a0a0f] flex items-center justify-center overflow-y-auto">
      <Particles count={30} />
      <div className="relative z-10 max-w-5xl px-6 py-20">
        <div className="text-center mb-10">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-block px-3 py-1 rounded-full bg-purple-600/20 border border-purple-500/30 text-purple-300 text-sm mb-4"
          >
            Featured Course
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-3xl md:text-4xl font-bold text-white"
          >
            Build & Ship Your First VR/MR App
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            transition={{ delay: 0.4 }}
            className="text-white/50 mt-2"
          >
            AI-Powered Development with Unity & Meta Quest
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-wrap justify-center gap-3 mb-10"
        >
          {['Hand Tracking', 'Mixed Reality', 'Multiplayer', 'AI Coding Agents', 'Ship to Meta Store'].map(tag => (
            <span key={tag} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/60 text-sm">
              ✅ {tag}
            </span>
          ))}
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-center text-purple-300 text-lg mb-12"
        >
          "No coding experience needed. The AI handles the code. You handle the vision."
        </motion.p>

        {/* Pricing cards */}
        <div className="flex flex-col sm:flex-row gap-6 justify-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 }}
            className="w-80 rounded-2xl border border-white/10 bg-white/5 p-8"
          >
            <p className="text-white/50 text-sm uppercase tracking-wider">Self-Paced</p>
            <p className="text-4xl font-bold text-white mt-2">₹999</p>
            <p className="text-white/40 text-sm mt-1">one-time · lifetime access</p>
            <ul className="mt-6 space-y-3 text-white/60 text-sm">
              <li>✓ All 11 modules (14 hours)</li>
              <li>✓ Lifetime access</li>
              <li>✓ Build ZenSpace — a real VR app</li>
              <li>✓ Certificate of completion</li>
              <li>✓ AI coding workflow included</li>
            </ul>
            <button className="mt-8 w-full py-3 border border-white/20 hover:border-white/40 text-white rounded-xl font-semibold transition">
              Enroll Now
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.0 }}
            className="w-80 rounded-2xl border border-purple-500/30 bg-purple-950/20 p-8 relative"
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-purple-600 rounded-full text-xs text-white font-semibold">
              Recommended
            </div>
            <p className="text-purple-400 text-sm uppercase tracking-wider">Live Coaching</p>
            <p className="text-4xl font-bold text-white mt-2">₹4,999</p>
            <p className="text-white/40 text-sm mt-1">one-time · includes everything</p>
            <ul className="mt-6 space-y-3 text-white/60 text-sm">
              <li>✓ Everything in Self-Paced</li>
              <li>✓ Weekly live VR classes</li>
              <li>✓ 1-on-1 doubt clearing (WhatsApp)</li>
              <li>✓ Community access</li>
              <li>✓ Instructor builds alongside you</li>
            </ul>
            <button className="mt-8 w-full py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-semibold transition shadow-lg shadow-purple-600/20">
              Enroll with Coaching
            </button>
          </motion.div>
        </div>

        <div className="text-center mt-8">
          <button onClick={onNext} className="text-white/40 hover:text-white/60 text-sm transition">
            View full curriculum →
          </button>
        </div>
      </div>
    </div>
  );
}

function StudentModules({ onNext }: { onNext: () => void }) {
  const modules = [
    { num: '01', title: 'Setup', desc: 'Unity + Meta SDK + first build on Quest', color: 'border-blue-500/30' },
    { num: '02', title: 'AI Partner', desc: 'Claude Code — your coding copilot', color: 'border-purple-500/30' },
    { num: '03', title: 'Hands', desc: 'Hand tracking + grab + throw + haptics', color: 'border-blue-500/30' },
    { num: '04', title: 'VR UI', desc: 'World-space menus + poke interaction', color: 'border-blue-500/30' },
    { num: '05', title: 'Audio & Env', desc: 'Spatial audio + skybox + particles', color: 'border-blue-500/30' },
    { num: '06', title: 'Locomotion', desc: 'Teleport + smooth move + comfort', color: 'border-blue-500/30' },
    { num: '07', title: 'Save Data', desc: 'Persistent sessions + state machine', color: 'border-blue-500/30' },
    { num: '08', title: 'Multiplayer', desc: 'Photon + voice chat + synced world', color: 'border-blue-500/30' },
    { num: '09', title: 'Mixed Reality', desc: 'Passthrough + spatial anchors', color: 'border-purple-500/50' },
    { num: '10', title: 'Polish', desc: '72fps + VRC checklist + app icon', color: 'border-blue-500/30' },
    { num: '11', title: 'Ship It', desc: 'Submit to Meta Quest Store', color: 'border-green-500/50' },
  ];

  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center overflow-y-auto">
      <Particles count={20} />
      <div className="relative z-10 max-w-4xl px-6 py-20">
        <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-3xl font-bold text-white text-center mb-10">
          11 Modules · 14 Hours · 1 Shipped App
        </motion.h2>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {modules.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.08 }}
              whileHover={{ scale: 1.05, borderColor: 'rgba(255,255,255,0.3)' }}
              className={`rounded-xl border ${m.color} bg-white/5 p-4 cursor-pointer transition-colors`}
            >
              <span className="text-white/30 text-xs font-mono">Module {m.num}</span>
              <h3 className="text-white font-semibold mt-1">{m.title}</h3>
              <p className="text-white/40 text-xs mt-1">{m.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="text-center mt-10">
          <button onClick={onNext} className="px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-semibold transition">
            Learn about Live Coaching →
          </button>
        </div>
      </div>
    </div>
  );
}

function StudentCoaching({ onNext }: { onNext: () => void }) {
  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center">
      <Particles count={30} />
      <div className="relative z-10 max-w-4xl px-6">
        <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-3xl md:text-4xl font-bold text-white text-center mb-4">
          Learn Inside <span className="text-purple-400">VR</span>
        </motion.h2>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 0.2 }} className="text-white/50 text-center mb-12">
          Your instructor is in the virtual world with you
        </motion.p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { icon: '🥽', title: 'Weekly Live VR Classes', desc: 'Join via Meta Quest. Learn VR development while INSIDE VR. Ask questions in real-time.' },
            { icon: '💬', title: 'WhatsApp Doubt Clearing', desc: 'Stuck on a bug? Send a message. Get a voice note or video reply within hours.' },
            { icon: '📺', title: 'YouTube Live Sessions', desc: "Don't have a Quest? Join live on YouTube. Same content, different screen." },
            { icon: '👥', title: 'Builder Community', desc: 'Connect with fellow VR developers. Share progress. Get feedback. Find collaborators.' },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.2 }}
              className="rounded-xl border border-white/10 bg-white/5 p-6"
            >
              <span className="text-3xl">{item.icon}</span>
              <h3 className="text-white font-semibold mt-3">{item.title}</h3>
              <p className="text-white/50 text-sm mt-2">{item.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }} className="text-center mt-10">
          <button className="px-10 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold text-lg transition shadow-lg shadow-purple-600/20">
            Start Learning — ₹4,999
          </button>
          <p className="text-white/30 text-sm mt-3">
            No Quest? Self-paced works on any device. <button className="text-purple-400 hover:underline">₹999 →</button>
          </p>
        </motion.div>

        <div className="text-center mt-6">
          <button onClick={onNext} className="text-white/30 hover:text-white/50 text-sm transition">Our story →</button>
        </div>
      </div>
    </div>
  );
}

function StudentProof() {
  return (
    <div className="fixed inset-0 bg-[#0a0a0f] flex items-center justify-center">
      <Particles count={30} />
      <div className="relative z-10 text-center max-w-3xl px-6">
        <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-3xl font-bold text-white mb-4">
          Built by people who shipped
        </motion.h2>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 0.2 }} className="text-white/50 mb-12">
          Not from documentation. From a real app on the Meta Quest Store.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-8 text-left max-w-md mx-auto"
        >
          <h3 className="text-xl font-bold text-white">GuruLok: A Spiritual Multiverse</h3>
          <p className="text-purple-400 text-sm mt-1">Live on Meta Quest Store · Early Access</p>
          <p className="text-white/50 text-sm mt-4">
            A VR meditation and spiritual experience built with Unity + Meta SDK — the same tools we teach in this course. Every module comes from real lessons learned building and shipping this app.
          </p>
          <div className="flex items-center gap-4 mt-6">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 via-white/80 to-blue-500" />
            <div>
              <p className="text-white font-semibold text-sm">TrigunAI Innovations Pvt Ltd</p>
              <p className="text-white/40 text-xs">DPIIT Recognized Startup · Patna & Mumbai</p>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.0 }} className="mt-12">
          <button className="px-10 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold text-lg transition shadow-lg shadow-purple-600/20">
            Start Your VR Journey
          </button>
        </motion.div>
      </div>
    </div>
  );
}

// === MAIN APP ===

function App() {
  const [screen, setScreen] = useState<Screen>('loading');
  const [menuOpen, setMenuOpen] = useState(false);

  const navigate = useCallback((s: Screen) => {
    setScreen(s);
    setMenuOpen(false);
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') navigate('choose');
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate]);

  return (
    <div className="w-full h-screen overflow-hidden bg-black">
      {screen !== 'loading' && (
        <Nav
          screen={screen}
          onNavigate={navigate}
          onToggleMenu={() => setMenuOpen(!menuOpen)}
          menuOpen={menuOpen}
        />
      )}

      <AnimatePresence mode="wait">
        {screen === 'loading' && <LoadingScreen key="loading" onDone={() => navigate('choose')} />}
        {screen === 'choose' && <ChooseScreen key="choose" onChoose={(p) => navigate(p === 'creator' ? 'c1_problem' : 's1_vision')} />}

        {/* Creator journey */}
        {screen === 'c1_problem' && <CreatorProblem key="c1" onNext={() => navigate('c2_solution')} />}
        {screen === 'c2_solution' && <CreatorSolution key="c2" onNext={() => navigate('c3_how')} onTry={() => {}} />}
        {screen === 'c3_how' && <CreatorHow key="c3" onNext={() => navigate('c4_pricing')} />}
        {screen === 'c4_pricing' && <CreatorPricing key="c4" />}

        {/* Student journey */}
        {screen === 's1_vision' && <StudentVision key="s1" onNext={() => navigate('s2_course')} />}
        {screen === 's2_course' && <StudentCourse key="s2" onNext={() => navigate('s3_modules')} />}
        {screen === 's3_modules' && <StudentModules key="s3" onNext={() => navigate('s4_coaching')} />}
        {screen === 's4_coaching' && <StudentCoaching key="s4" onNext={() => navigate('s5_proof')} />}
        {screen === 's5_proof' && <StudentProof key="s5" />}
      </AnimatePresence>
    </div>
  );
}

export default App;
