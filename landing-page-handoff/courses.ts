// ─────────────────────────────────────────────────────────────────────────────
// TrigunAI — course catalog data for the landing page.
// This is the single source the Courses section + course detail views render from.
// Human-readable twin: ../COURSE_INDEXES.md  ·  Strategy: ../COURSE_CATALOG.md
//
// Deepak fills REGISTER_URL_* once the forms/payment links exist (see bottom).
// Until then the Register buttons point at the Substack waitlist fallback.
// ─────────────────────────────────────────────────────────────────────────────

export type CourseStatus = 'flagship' | 'open' | 'waitlist';

export interface Module {
  n: number;
  title: string;
  brief: string;
}

export interface Course {
  id: string;
  badge: string;              // "FLAGSHIP" | "LAUNCHING JULY 18" | "COMING SOON"
  status: CourseStatus;       // drives the CTA: flagship/open => "Reserve your seat", waitlist => "Join the waitlist"
  accent: string;             // card accent color (brand tokens)
  title: string;
  tagline: string;
  fromEpisodes: string;       // funnel link back to the series
  level: string;
  modulesCount: number;
  hours: string;
  outcome: string;            // the one thing the student walks away with
  forWho: string;
  prerequisites: string;
  registerKey: 'VR' | 'AGENTIC' | 'ML' | 'ROBOTICS';  // maps to REGISTER_URLS below
  modules: Module[];
}

// Accent palette (matches HANDOFF.md §3)
const GOLD = '#f4c14b';
const INDIGO = '#7aa2ff';
const VIOLET = '#b88cff';
const TEAL = '#5fd0c5';

export const COURSES: Course[] = [
  // ── 1. VR/MR — flagship, fully complete ──────────────────────────────────
  {
    id: 'vr-mr-app',
    badge: 'FLAGSHIP',
    status: 'flagship',
    accent: GOLD,
    title: 'Build & Ship Your First VR/MR App',
    tagline:
      'Use AI coding agents (Claude Code) + Unity to build a real VR/MR app from scratch — hand tracking, passthrough MR, multiplayer — and submit it to Meta’s Store. No coding experience required.',
    fromEpisodes: 'The body to the series’ mind — where AI gets a world to live in.',
    level: 'Beginner → Shipped',
    modulesCount: 11,
    hours: '~14 hours',
    outcome:
      'A real VR/MR app running on your headset and submitted to Meta’s App Lab — something you can hand an interviewer.',
    forWho: 'Complete beginners, career-changers, indie creators. Coders 10x their speed; non-coders let the AI write the C#.',
    prerequisites: 'A Windows PC + a Meta Quest 2/3/Pro + a USB-C cable. No prior Unity or VR experience.',
    registerKey: 'VR',
    modules: [
      { n: 1, title: 'Setup — Unity, Quest & your dev environment', brief: 'Install Unity 6 + Meta XR SDK, configure for Quest, get a room running on your headset. (This module is the free YouTube teaser.)' },
      { n: 2, title: 'Your AI coding partner — building VR with Claude Code', brief: 'Describe it in English → the agent writes the C# → you test in VR → iterate. The 5-part VR prompt template. Unlocks non-coders.' },
      { n: 3, title: 'Hands & controllers — interacting with the world', brief: 'Hand tracking + controllers, grab/throw with physics, haptic feedback. Build grabbable meditation stones.' },
      { n: 4, title: 'VR UI — menus, buttons & panels that work', brief: 'World-space UI that doesn’t make people sick, poke + laser interaction, a working breathing-guide timer.' },
      { n: 5, title: 'Environment & audio — making VR feel like a place', brief: 'Skyboxes, Quest-friendly lighting, particles, spatial audio, free asset sources. Turn a demo into an experience.' },
      { n: 6, title: 'Locomotion — moving without getting sick', brief: 'Teleport, smooth move, snap turn, comfort vignette — and letting the user choose their comfort mode.' },
      { n: 7, title: 'Saving data & session logic', brief: 'PlayerPrefs + JSON persistence, a Menu→Session→Summary state machine, “welcome back” memory across sessions.' },
      { n: 8, title: 'Multiplayer basics — sharing VR with others', brief: 'Photon Fusion free tier, networked head+hands avatars, spatial voice chat, a shared room.' },
      { n: 9, title: 'Mixed reality & passthrough — VR meets your real room', brief: 'Quest 3 passthrough, Scene API, spatial anchors — place virtual objects in your real room. The skill most senior VR devs lack.' },
      { n: 10, title: 'Performance & polish — making it Quest-ready', brief: 'Profiler, draw-call batching, ASTC textures, holding 72fps, icon/splash/loading, the Meta VRC checklist.' },
      { n: 11, title: 'Ship it — from build to the Meta Store', brief: 'Developer account, keystore signing, release APK, store listing, privacy policy, age rating, submit for review. The module nobody else teaches.' },
    ],
  },

  // ── 2. Agentic Systems — drip-launch July 18 ─────────────────────────────
  {
    id: 'agentic-systems',
    badge: 'LAUNCHING JULY 18',
    status: 'open',
    accent: INDIGO,
    title: 'Build Agentic AI Systems',
    tagline:
      'Build real, working AI agents that do useful work — tool use, memory, planning, multi-step autonomy — on today’s APIs. From a single tool-calling agent to a multi-agent workflow for real tasks.',
    fromEpisodes: 'From Episode 6 — “Will”: wanting, and acting on it.',
    level: 'Beginner → Practitioner',
    modulesCount: 9,
    hours: '~10 hours',
    outcome: 'A deployed agent doing a real job on a schedule — and the patterns to build the next one.',
    forWho: 'Founders, operators, developers — anyone doing repetitive knowledge-work who wants to automate it. No ML PhD.',
    prerequisites: 'A laptop + an API key (Claude / OpenAI). Light Python helps, but the agent writes most of the code.',
    registerKey: 'AGENTIC',
    modules: [
      { n: 1, title: 'What an agent actually is', brief: 'LLM + a loop + tools + memory. The anatomy of “will” made concrete — goal in, actions out, when it stops.' },
      { n: 2, title: 'Your first tool-calling agent', brief: 'Function/tool calling, the agent loop, parsing the model’s tool requests, returning results, termination.' },
      { n: 3, title: 'Tools & integrations — giving it hands', brief: 'Connect web search, files, a database, a Google Sheet, email — turning an LLM into something that acts.' },
      { n: 4, title: 'Memory & context', brief: 'Short-term vs long-term memory, retrieval (RAG basics), managing the context window, what to remember and forget.' },
      { n: 5, title: 'Planning & multi-step reasoning', brief: 'Task decomposition, ReAct, reflection and self-correction — handling a job that takes 12 steps, not 1.' },
      { n: 6, title: 'Reliability & guardrails (the part tutorials skip)', brief: 'Structured/JSON output, validation, retries, human-in-the-loop checkpoints, and cost control so it doesn’t burn money.' },
      { n: 7, title: 'Multi-agent systems', brief: 'Orchestrator + worker agents, handoffs, when multiple agents genuinely help — and when they just add chaos.' },
      { n: 8, title: 'Deploy your agent', brief: 'Run it on a server/schedule, a minimal UI, logging and monitoring so you can see what it did and why.' },
      { n: 9, title: 'Ship a real business agent', brief: 'Package the Ops Agent with its playbook, hand it to a non-technical user, and measure that it actually saves time.' },
    ],
  },

  // ── 3. Machine Learning & Its Math — drip-launch, sequenced last ──────────
  {
    id: 'ml-and-math',
    badge: 'LAUNCHING JULY 18',
    status: 'open',
    accent: VIOLET,
    title: 'Machine Learning & Its Math',
    tagline:
      'Understand and build the core of modern ML — the math you actually need, then neural nets, embeddings, diffusion, and training. Intuition first, code second, math demystified.',
    fromEpisodes: 'From Episodes 3, 4, 5 & 7 — imagination, meaning, intuition, getting better.',
    level: 'Beginner → Builder',
    modulesCount: 10,
    hours: '~12 hours',
    outcome: 'You can read, build, and train a small model end-to-end — and you finally get what’s under the hood.',
    forWho: 'Developers and curious learners who want to understand ML, not just call an API — and were scared off by the math.',
    prerequisites: 'A laptop; we provide GPU access for the training modules. Comfortable with basic Python; high-school math, refreshed in-course.',
    registerKey: 'ML',
    modules: [
      { n: 1, title: 'The map', brief: 'What ML is, the faculties-of-mind frame, supervised / unsupervised / RL in one picture. Where everything fits.' },
      { n: 2, title: 'The math you actually need', brief: 'Vectors, matrices, dot products, and gradients — visual and intuitive, the 20% that powers everything. No fear.' },
      { n: 3, title: 'Intuition = function approximation', brief: 'A neuron, a layer, a network, the forward pass — building “knowing without reasoning” (Ep 5) by hand.' },
      { n: 4, title: 'Getting better = gradient descent', brief: 'Loss, backpropagation, the training loop — coded from scratch so you see how a model learns from error (Ep 7).' },
      { n: 5, title: 'From scratch → PyTorch', brief: 'The same network, now in a real framework, on a real GPU. Tensors, autograd, the modern workflow.' },
      { n: 6, title: 'Meaning = embeddings & vector space', brief: 'Word and image embeddings, similarity, and vector search — how machines hold meaning as geometry (Ep 4).' },
      { n: 7, title: 'Imagination = generative models', brief: 'Autoencoders → the intuition behind diffusion → a tiny generator that dreams new images (Ep 3).' },
      { n: 8, title: 'Attention & transformers', brief: 'Why attention won, and a minimal transformer block built up piece by piece (ties back to Ep 1).' },
      { n: 9, title: 'Training in practice', brief: 'Data, overfitting, regularization, evaluation, and the real GPU training workflow — on provided hardware.' },
      { n: 10, title: 'A real ML project, end-to-end', brief: 'Pick one — classifier, embedding search, or generator — train it, evaluate it, and show the result.' },
    ],
  },

  // ── 4. Physical AI / Robotics — post-launch, waitlist (the ₹50k tier) ─────
  {
    id: 'physical-ai',
    badge: 'COMING SOON',
    status: 'waitlist',
    accent: TEAL,
    title: 'Physical AI — Train a Robot in Simulation',
    tagline:
      'The embodiment half. Train reinforcement-learning policies in NVIDIA Isaac Sim, on provided GPU, and watch them learn inside a VR headset. Where the Mind gets a Body and a World.',
    fromEpisodes: 'From Episode 2 — “The Learning Loop”: RL in Isaac Sim.',
    level: 'Intermediate',
    modulesCount: 8,
    hours: '~10 hours',
    outcome: 'A control policy you trained yourself in simulation, plus the sim-to-real and teleoperation concepts behind real robots.',
    forWho: 'Developers and engineers ready to step from screen-AI into embodied AI / robotics.',
    prerequisites: 'The premium tier — provided NVIDIA GPU + Isaac Sim + live cohort. Some Python and ML basics help.',
    registerKey: 'ROBOTICS',
    modules: [
      { n: 1, title: 'Simulation & digital twins', brief: 'Why we train robots in sim first; what a physics simulator does; the digital-twin idea.' },
      { n: 2, title: 'Isaac Sim / Isaac Lab setup (provided)', brief: 'Get into the NVIDIA stack on provided GPU — the environment generic courses can’t give you.' },
      { n: 3, title: 'RL basics for control', brief: 'Agents, environments, rewards, episodes — reinforcement learning aimed at movement, not games.' },
      { n: 4, title: 'Designing the reward', brief: 'The craft that makes or breaks a policy — shaping behavior through what you reward.' },
      { n: 5, title: 'Training your first policy', brief: 'Run PPO, read the curves, get a robot that learns to reach its goal.' },
      { n: 6, title: 'Sim-to-real concepts', brief: 'Domain randomization, the reality gap, and what it takes to move a policy toward the real world.' },
      { n: 7, title: 'Teleoperation & VR embodiment', brief: 'Step inside the simulator — drive and watch the policy from a Quest headset (the VR-as-body link).' },
      { n: 8, title: 'Deploy & view your trained policy', brief: 'Export the policy, render it, and watch your trained robot run in VR.' },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Registration destinations. Deepak fills these once the forms/links exist.
// Recommended for launch: a free Tally / Google Form per course (name, email,
// course, "I have a Quest?"). Upgrade to a Razorpay/Gumroad payment link to take
// a paid reservation. Until set, all fall back to the Substack waitlist.
// ─────────────────────────────────────────────────────────────────────────────
export const SUBSTACK_URL = 'https://trigunai.substack.com/subscribe';

export const REGISTER_URLS: Record<Course['registerKey'], string> = {
  VR: SUBSTACK_URL,        // <- replace with VR/MR reserve form or payment link
  AGENTIC: SUBSTACK_URL,   // <- replace with Agentic reserve form
  ML: SUBSTACK_URL,        // <- replace with ML reserve form
  ROBOTICS: SUBSTACK_URL,  // <- replace with Robotics waitlist form
};

export function registerUrl(c: Course): string {
  return REGISTER_URLS[c.registerKey] ?? SUBSTACK_URL;
}

export function ctaLabel(c: Course): string {
  return c.status === 'waitlist' ? 'Join the waitlist' : 'Reserve your seat';
}
