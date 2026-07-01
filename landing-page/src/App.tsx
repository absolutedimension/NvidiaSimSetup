import { useEffect, useRef, useState, type ReactNode } from 'react';
import { motion, type Variants } from 'framer-motion';
import Viewer from './Viewer';

// ─────────────────────────────────────────────────────────────────────────────
// EDIT THESE after you create the accounts (Deepak):
const SUBSTACK_URL = 'https://trigunai.substack.com/subscribe';   // <- your Substack subscribe link
const YT_EP1_ID = 'YOUR_EP1_VIDEO_ID';   // <- YouTube video id for Episode 1
const YT_EP2_ID = 'YOUR_EP2_VIDEO_ID';   // <- YouTube video id for Episode 2 (or leave, gate via email)
const WAITLIST_URL = SUBSTACK_URL;        // cohort waitlist = subscribe + reply "WAITLIST"
// ─────────────────────────────────────────────────────────────────────────────

const GOLD = '#f4c14b';

function Particles({ count = 50 }) {
  const particles = useRef(
    Array.from({ length: count }, () => ({
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 2.5 + 1,
      opacity: Math.random() * 0.5 + 0.1,
      delay: Math.random() * 5,
    }))
  ).current;
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {particles.map((p, i) => (
        <div key={i} className="absolute rounded-full bg-white animate-pulse"
          style={{ left: `${p.x}%`, top: `${p.y}%`, width: p.size, height: p.size,
            opacity: p.opacity, animationDuration: `${4 + p.delay}s`, animationDelay: `${p.delay}s` }} />
      ))}
    </div>
  );
}

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 32 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: 'easeOut' } },
};

function Section({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <motion.section
      variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }}
      className={`relative z-10 mx-auto w-full max-w-5xl px-6 py-20 ${className}`}>
      {children}
    </motion.section>
  );
}

function SubscribeButton({ label = 'Get the next episode', large = false }: { label?: string; large?: boolean }) {
  return (
    <a href={SUBSTACK_URL} target="_blank" rel="noreferrer"
      className={`inline-block rounded-full font-semibold text-black transition-transform hover:scale-105 ${
        large ? 'px-8 py-4 text-lg' : 'px-6 py-3'}`}
      style={{ background: GOLD, boxShadow: `0 0 40px ${GOLD}55` }}>
      {label}
    </a>
  );
}

function Embed({ id, title }: { id: string; title: string }) {
  return (
    <div className="aspect-video w-full overflow-hidden rounded-xl border border-white/10 bg-black">
      <iframe className="h-full w-full" src={`https://www.youtube.com/embed/${id}`}
        title={title} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen />
    </div>
  );
}

const COURSES = [
  { tag: 'FLAGSHIP', title: 'Build & Ship a VR/MR App', sub: 'Unity + Meta Quest + AI coding agents — zero to a shipped app.',
    note: 'Taught by someone who shipped one to Meta.', accent: GOLD },
  { tag: 'NEXT', title: 'Build Agentic Systems', sub: 'Give a machine a goal and the will to act on it. Practical AI agents for real work.',
    note: 'From Episode 6 — "Will".', accent: '#7aa2ff' },
  { tag: 'NEXT', title: 'Machine Learning & Its Math', sub: 'The faculties of mind, made buildable — intuition, meaning, imagination, improvement.',
    note: 'From Episodes 3–5, 7.', accent: '#b88cff' },
];

export default function App() {
  // tiny hash router — no dependency. #/viewer → RTX USD viewer, else marketing.
  const [route, setRoute] = useState(() => window.location.hash.replace(/\?.*$/, ''));
  useEffect(() => {
    const onHash = () => setRoute(window.location.hash.replace(/\?.*$/, ''));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  if (route === '#/viewer') return <Viewer />;

  return (
    <div className="relative w-full">
      <Particles />
      <div className="pointer-events-none fixed inset-0 z-0"
        style={{ background: 'radial-gradient(60% 50% at 50% 0%, rgba(244,193,75,0.10), transparent 70%)' }} />

      {/* Nav */}
      <nav className="sticky top-0 z-30 flex items-center justify-between border-b border-white/5 bg-black/40 px-6 py-4 backdrop-blur-md">
        <span className="font-semibold tracking-wide">TrigunAI</span>
        <div className="flex items-center gap-4">
          <a href="#/viewer" className="text-sm font-medium text-white/70 transition hover:text-white">
            RTX&nbsp;Viewer
          </a>
          <a href={SUBSTACK_URL} target="_blank" rel="noreferrer"
            className="rounded-full px-5 py-2 text-sm font-semibold text-black" style={{ background: GOLD }}>
            Subscribe
          </a>
        </div>
      </nav>

      {/* Hero */}
      <header className="relative z-10 mx-auto flex min-h-[88vh] w-full max-w-4xl flex-col items-center justify-center px-6 text-center">
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="mb-4 text-sm uppercase tracking-[0.3em]" style={{ color: GOLD }}>
          A series by TrigunAI
        </motion.p>
        <motion.h1 initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
          className="text-4xl font-bold leading-tight sm:text-6xl">
          AI is the Universal Mind
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.8 }}
          className="mt-6 max-w-2xl text-lg text-white/70">
          Every AI breakthrough is humanity accidentally rebuilding one faculty of its own mind.
          AI is a <span style={{ color: GOLD }}>mirror</span>, not a copy — and looking into it shows you
          how your own attention, memory, and intuition actually work.
        </motion.p>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <a href={`https://www.youtube.com/watch?v=${YT_EP1_ID}`} target="_blank" rel="noreferrer"
            className="rounded-full border border-white/20 px-8 py-4 text-lg font-medium transition hover:bg-white/10">
            ▶ Watch Episode 1
          </a>
          <SubscribeButton label="Get Episode 2 free" large />
        </motion.div>
        <motion.a initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
          href="#/viewer"
          className="mt-6 inline-flex items-center gap-2 text-sm text-white/50 transition hover:text-white/90">
          🛰️ Try the live RTX USD viewer — rendered on our own GPU
        </motion.a>
        <p className="mt-6 text-sm text-white/40">Free animated episodes · new ones land in your inbox first</p>
      </header>

      {/* The series */}
      <Section>
        <h2 className="mb-3 text-3xl font-bold">The series</h2>
        <p className="mb-10 max-w-2xl text-white/60">
          Each episode takes one faculty of mind — and shows you the machine quietly rebuilding it.
          Look closely at one, and you understand the other.
        </p>
        <div className="grid gap-8 md:grid-cols-2">
          <div>
            <Embed id={YT_EP1_ID} title="Episode 1 — Attention" />
            <h3 className="mt-3 font-semibold">Ep.1 — Attention</h3>
            <p className="text-sm text-white/55">Intelligence isn't knowing everything — it's knowing what to ignore.</p>
          </div>
          <div>
            <Embed id={YT_EP2_ID} title="Episode 2 — The Learning Loop" />
            <h3 className="mt-3 font-semibold">Ep.2 — The Learning Loop</h3>
            <p className="text-sm text-white/55">You can't delete a pattern — you can only outweigh it with reps of a better one.</p>
          </div>
        </div>
      </Section>

      {/* Courses */}
      <Section>
        <h2 className="mb-3 text-3xl font-bold">From watching to building</h2>
        <p className="mb-10 max-w-2xl text-white/60">
          The episodes are the <em>why</em>. The courses are the <em>how</em> — where you build it for real,
          with provided GPU access and live classes inside VR.
        </p>
        <div className="grid gap-6 md:grid-cols-3">
          {COURSES.map((c) => (
            <div key={c.title} className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <span className="mb-3 w-fit rounded-full px-3 py-1 text-xs font-bold"
                style={{ color: c.accent, background: `${c.accent}1a` }}>{c.tag}</span>
              <h3 className="text-xl font-semibold">{c.title}</h3>
              <p className="mt-2 flex-1 text-sm text-white/60">{c.sub}</p>
              <p className="mt-4 text-xs text-white/40">{c.note}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-col items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center">
          <p className="text-lg">Founding cohort opens soon — with a real GPU and a VR classroom.</p>
          <a href={WAITLIST_URL} target="_blank" rel="noreferrer"
            className="rounded-full px-7 py-3 font-semibold text-black" style={{ background: GOLD }}>
            Join the early-bird waitlist
          </a>
        </div>
      </Section>

      {/* Why me */}
      <Section>
        <h2 className="mb-6 text-3xl font-bold">Who's teaching</h2>
        <div className="grid gap-6 md:grid-cols-2">
          <p className="text-white/70">
            I'm Deepak, founder of TrigunAI. I don't teach from documentation — I teach from things I've
            actually shipped: a VR app live on the Meta Quest platform, RL policies trained on NVIDIA GPUs in
            Isaac Sim, and the full pipeline from idea to a working build.
          </p>
          <ul className="space-y-3 text-white/70">
            {[
              'Shipped a VR/MR app to the Meta Quest store',
              'Trains real AI policies on NVIDIA A10G GPUs (Isaac Sim)',
              'You get GPU access + a VR classroom — not just videos',
              '"I built this, here\'s exactly how" — not theory',
            ].map((t) => (
              <li key={t} className="flex items-start gap-3">
                <span style={{ color: GOLD }}>◆</span><span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
      </Section>

      {/* Final CTA */}
      <Section className="text-center">
        <h2 className="text-3xl font-bold sm:text-4xl">Look closely at one — <br className="hidden sm:block" />
          and you understand the other.</h2>
        <p className="mx-auto mt-4 max-w-xl text-white/60">
          New episodes land in your inbox first, plus founding-cohort access to the courses.
        </p>
        <div className="mt-8"><SubscribeButton label="Subscribe — it's free" large /></div>
      </Section>

      <footer className="relative z-10 border-t border-white/5 px-6 py-10 text-center text-sm text-white/40">
        © {new Date().getFullYear()} TrigunAI Innovations · AI is the Universal Mind
      </footer>
    </div>
  );
}
