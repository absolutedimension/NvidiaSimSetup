"""Idempotent curriculum seed for Cohort 1 — 'Build Agentic AI Systems'.
Source of truth: Agentic_AI_Cohort_Welcome.pdf. Run: python -m app.seed"""
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Lesson, Module, Student, WorkbookTask

# week -> (code, title, session_date, summary)
MODULES = [
    (0, "Kickoff", "Kickoff", "26 Jun", "Orientation · API key live · fork the starter repo · pick your use-case"),
    (1, "M1", "What an agent actually is", "03 Jul", "Map your use-case to goal → actions → stop; the loop"),
    (2, "M2", "Your first tool-calling agent", "10 Jul", "Live-code the agent loop; land your first tool call"),
    (3, "M3", "Tools & integrations", "17 Jul", "Connect YOUR real tool — inbox, sheet, files, web search"),
    (4, "M4", "Memory & context", "24 Jul", "Add memory to your agent; retrieval (RAG) basics on your docs"),
    (5, "M5", "Planning & multi-step", "31 Jul", "Task decomposition, ReAct, reflection & self-correction"),
    (6, "M-INT", "Catch-up & integration", "07 Aug", "No new module — get your agent doing a real 5-step job end-to-end"),
    (7, "M6", "Reliability & guardrails", "14 Aug", "JSON validation, retries, human checkpoints, cost control"),
    (8, "M7", "Multi-agent systems", "21 Aug", "Orchestrator + worker agents; when multiple agents truly help"),
    (9, "M8", "Deploy your agent", "28 Aug", "Run it on a schedule on a server, with logging you can read"),
    (10, "M9", "Ship a real business agent", "04 Sep", "Package it, hand it to a non-technical user, measure time saved"),
    (11, "CAP", "Capstone build", "11 Sep", "Office-hours format — polish your own agent for Demo Day"),
    (12, "DEMO", "Demo Day + certificates", "18 Sep", "Each student demos their working agent · certificates awarded"),
]

# week -> { days: [(day, date, focus, task, minutes)], bring: str }
WORKBOOK = {
    1: {"days": [
        ("Sat", "27 Jun", "Watch", "Watch Module 1. Note: what are the 4 parts of an agent?", 45),
        ("Sun", "28 Jun", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "29 Jun", "Build", "Fork the starter repo, install it, add your API key to .env.", 40),
        ("Tue", "30 Jun", "Build", "Run python run.py \"hello\". Open agent/loop.py and comment each step.", 40),
        ("Wed", "01 Jul", "Make it yours", "Write your use-case (the real job) into config.py and the README.", 45),
        ("Thu", "02 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent saying hello in the terminal (screenshot) + your one-sentence use-case."},
    2: {"days": [
        ("Sat", "04 Jul", "Watch", "Watch Module 2. Note: how does the model ask for a tool, and how do we answer?", 45),
        ("Sun", "05 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "06 Jul", "Build", "Run a goal that triggers a tool: python run.py \"what is today's date?\".", 40),
        ("Tue", "07 Jul", "Build", "Add a print inside the loop to show every tool call + result.", 40),
        ("Wed", "08 Jul", "Make it yours", "List the 2–3 tools YOUR agent will need (names + one line each).", 45),
        ("Thu", "09 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A run log showing a tool call and its result."},
    3: {"days": [
        ("Sat", "11 Jul", "Watch", "Watch Module 3. Note: which of your tools is easiest to add first?", 45),
        ("Sun", "12 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "13 Jul", "Build", "Add one new tool to agent/tools.py (schema + function). Test it in isolation.", 40),
        ("Tue", "14 Jul", "Build", "Wire it into the loop; have the agent call it. Office hours if stuck.", 40),
        ("Wed", "15 Jul", "Make it yours", "Point it at YOUR data — your sheet, a CSV export, your files.", 45),
        ("Thu", "16 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent doing something useful with your own data."},
    4: {"days": [
        ("Sat", "18 Jul", "Watch", "Watch Module 4. Note: what should your agent remember between runs?", 45),
        ("Sun", "19 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "20 Jul", "Build", "Use agent/memory.py: have the agent write a note at the end of a run.", 40),
        ("Tue", "21 Jul", "Build", "On the next run, load that note into the prompt so it 'remembers'.", 40),
        ("Wed", "22 Jul", "Make it yours", "Decide the 1–2 things your agent should remember for your use-case.", 45),
        ("Thu", "23 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Two runs where run #2 clearly uses what run #1 remembered."},
    5: {"days": [
        ("Sat", "25 Jul", "Watch", "Watch Module 5. Note: what is ReAct, in one sentence?", 45),
        ("Sun", "26 Jul", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "27 Jul", "Build", "Give the agent a task needing 3+ tool calls. Watch how it sequences them.", 40),
        ("Tue", "28 Jul", "Build", "Add a reflection step: let it check its own work before finishing.", 40),
        ("Wed", "29 Jul", "Make it yours", "Write the real 5-step version of YOUR workflow as a single goal.", 45),
        ("Thu", "30 Jul", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A transcript of your agent completing a multi-step task."},
    6: {"days": [
        ("Sat", "01 Aug", "Watch", "No new module. Re-watch any part you were shaky on.", 45),
        ("Sun", "02 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "03 Aug", "Build", "Connect the pieces: tools + memory + planning in one run.", 40),
        ("Tue", "04 Aug", "Build", "Run your real workflow's happy path start to finish. Fix what breaks.", 40),
        ("Wed", "05 Aug", "Make it yours", "Tidy: name things clearly, remove dead code, note remaining gaps.", 45),
        ("Thu", "06 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your agent doing the real job, start to finish (rough is fine)."},
    7: {"days": [
        ("Sat", "08 Aug", "Watch", "Watch Module 6. Note: where could your agent do something costly or wrong?", 45),
        ("Sun", "09 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "10 Aug", "Build", "Add JSON validation + one retry on a tool that can fail.", 40),
        ("Tue", "11 Aug", "Build", "Set a cost cap in config.py (MAX_USD); add a human confirm before any 'send'.", 40),
        ("Wed", "12 Aug", "Make it yours", "Add the confirm-before-acting checkpoint that fits YOUR workflow.", 45),
        ("Thu", "13 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A run where a tool fails and your agent recovers (or stops) — plus your cost cap."},
    8: {"days": [
        ("Sat", "15 Aug", "Watch", "Watch Module 7. Note: when do multiple agents help vs. add chaos?", 45),
        ("Sun", "16 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "17 Aug", "Build", "Split a job into a planner agent + a worker agent; pass one handoff.", 40),
        ("Tue", "18 Aug", "Build", "Compare: is the 2-agent version actually better than one? Be honest.", 40),
        ("Wed", "19 Aug", "Make it yours", "Decide if YOUR use-case needs multi-agent — and write why / why not.", 45),
        ("Thu", "20 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Either a 2-agent handoff working, OR a clear reason one agent is enough."},
    9: {"days": [
        ("Sat", "22 Aug", "Watch", "Watch Module 8. Note: cron vs. GitHub Actions vs. a server — which fits you?", 45),
        ("Sun", "23 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "24 Aug", "Build", "Add logging so every run records what it did and why.", 40),
        ("Tue", "25 Aug", "Build", "Schedule it (cron or GitHub Actions). Trigger one scheduled run.", 40),
        ("Wed", "26 Aug", "Make it yours", "Pick the schedule YOUR job needs (daily? hourly? on an event?).", 45),
        ("Thu", "27 Aug", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A log from a run that fired on a schedule, not by you."},
    10: {"days": [
        ("Sat", "29 Aug", "Watch", "Watch Module 9. Note: what would confuse a non-technical user?", 45),
        ("Sun", "30 Aug", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "31 Aug", "Build", "Write your agent's playbook: what it does, how to run it, what it needs.", 40),
        ("Tue", "01 Sep", "Build", "Package the config + a one-line run command. Remove anything fragile.", 40),
        ("Wed", "02 Sep", "Make it yours", "Hand it to ONE non-technical person and watch them try it.", 45),
        ("Thu", "03 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Feedback from your first real user + a rough 'time saved' number."},
    11: {"days": [
        ("Sat", "05 Sep", "Watch", "No new module. Re-watch the part most relevant to your capstone.", 45),
        ("Sun", "06 Sep", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "07 Sep", "Build", "Fix your top 3 rough edges. Clean the README so it's obvious how to run.", 40),
        ("Tue", "08 Sep", "Build", "Do a full dry-run of the real job. Time it.", 40),
        ("Wed", "09 Sep", "Make it yours", "Write your demo story: the problem → your agent → the result.", 45),
        ("Thu", "10 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "A near-final agent + a 2-minute demo plan."},
    12: {"days": [
        ("Sat", "12 Sep", "Watch", "No new module. Watch a peer's clip shared in the WhatsApp group for ideas.", 45),
        ("Sun", "13 Sep", "Rest", "Catch up if you're behind. Otherwise — recharge.", 0),
        ("Mon", "14 Sep", "Build", "Rehearse the live run twice. Note where it's slow or risky.", 40),
        ("Tue", "15 Sep", "Build", "Record a 1-min backup video in case the live run hiccups.", 40),
        ("Wed", "16 Sep", "Make it yours", "Prepare your before/after: how much time your agent saves you.", 45),
        ("Thu", "17 Sep", "Test & show", "Run it, fix one bug, post a screenshot, write your #1 question.", 30),
    ], "bring": "Your FINAL working agent — ready to demo on Demo Day."},
}

# week, slug, title, gems, available, sort  (sort orders multiple lessons within a week)
LESSONS = [
    (1,  "goal-to-agent",                 "The big idea: from a goal to an agent", 100, True, 0),
    (1,  "what-is-an-agent",              "Anatomy: brain, tools & the loop",      100, True, 1),
    (2,  "first-tool-calling-agent",      "Your first tool-calling agent", 100, True, 0),
    (3,  "tools-and-integrations",        "Tools & integrations",          100, True, 0),
    (4,  "memory-and-context",            "Memory & context",              100, True, 0),
    (5,  "planning-and-multi-step",       "Planning & multi-step",         100, True, 0),
    (7,  "reliability-and-guardrails",    "Reliability & guardrails",      100, True, 0),
    (8,  "multi-agent-systems",           "Multi-agent systems",           100, True, 0),
    (9,  "deploy-your-agent",             "Deploy your agent",             100, True, 0),
    (10, "ship-a-real-business-agent",    "Ship a real business agent",    100, True, 0),
]

# ---- Course 2: Command the Coding Agent — Crack the Remote SWE Job ----
SWE_MODULES = [
    (0,  "Start", "Setup + the Job Machine starts", "", "Tools, résumé rebuild, application tracker — the machine starts Week 1"),
    (1,  "W1", "Complexity + arrays & hashing",     "", "Big-O, arrays/strings, hashing, two pointers, sliding window"),
    (2,  "W2", "Linear structures, search & trees", "", "Stacks/queues, binary search, linked lists, trees, tries"),
    (3,  "W3", "Recursion, backtracking & graphs",  "", "Subsets/permutations, BFS/DFS, topological sort, union-find"),
    (4,  "W4", "Advanced DP, greedy & heaps",        "", "DP patterns, greedy, heaps/top-K, intervals + first mock"),
    (5,  "W5", "Low-Level Design (LLD)",             "", "OOP, SOLID, the top-5 patterns, API/class design"),
    (6,  "W6", "High-Level Design I",                "", "HLD frame, estimation, caching, databases, load balancing, CAP"),
    (7,  "W7", "High-Level Design II",               "", "Queues/streaming, sharding, replication, rate limiting, reliability"),
    (8,  "W8", "HLD case studies (the canon)",       "", "Design end-to-end with tradeoffs spoken aloud"),
    (9,  "W9", "The AI-command interview round",     "", "Direct the coding agent & verify its output — the TrigunAI signature"),
    (10, "W10","AI pair-programming under pressure", "", "Command AI in final rounds without losing correctness"),
    (11, "W11","Targeted revision + your stack",     "", "Close the gaps; the offer stage"),
    (12, "W12","Capstone + close the offer",         "", "Full-loop polish, demo, negotiate, accept"),
]
SWE_LESSONS = [
    (1,  "swe-complexity",     "Complexity & the operator's eye", 100, True, 0),
    (5,  "swe-lld",            "Low-Level Design essentials",     100, True, 0),
    (6,  "swe-hld",            "High-Level Design foundations",   100, True, 0),
    (9,  "swe-command-agent",  "Commanding the coding agent",     100, True, 0),
]

# ---- Course 3: Machine Learning & Its Math — The Faculties of Mind, Made Buildable ----
ML_MODULES = [
    (1,  "M1", "The map",                            "", "What ML is · the faculties-of-mind frame · supervised / unsupervised / RL"),
    (2,  "M2", "The math you actually need",          "", "Vectors, matrices, dot products, gradients — visual & intuitive"),
    (3,  "M3", "Intuition = function approximation",  "", "A neuron, a layer, a network, the forward pass — by hand"),
    (4,  "M4", "Getting better = gradient descent",   "", "Loss, backpropagation, the training loop — coded from scratch"),
    (5,  "M5", "From scratch → PyTorch",              "", "Tensors, autograd, the modern GPU workflow"),
    (6,  "M6", "Meaning = embeddings & vector space", "", "Word/image embeddings, similarity, vector search"),
    (7,  "M7", "Imagination = generative models",     "", "Autoencoders → diffusion intuition → a tiny generator"),
    (8,  "M8", "Attention & transformers",            "", "Why attention won + a minimal transformer block"),
    (9,  "M9", "Training in practice",                "", "Data, overfitting, regularization, evaluation, GPU training"),
    (10, "M10","A real ML project, end-to-end",       "", "Train, evaluate & show a classifier / embedding-search / generator"),
]
ML_LESSONS = [
    (1,  "ml-map",              "The map: what ML really is",        100, True, 0),
    (2,  "ml-math",             "The math you actually need",        100, True, 0),
    (4,  "ml-gradient-descent", "Getting better: gradient descent",  100, True, 0),
    (6,  "ml-embeddings",       "Meaning: embeddings & vector space",100, True, 0),
    (8,  "ml-transformers",     "Attention & transformers",          100, True, 0),
]
PHYS_LESSONS = [
    (1,  "phys-sim",            "Why train in simulation",           100, True, 0),
    (3,  "phys-rl",             "RL basics for control",             100, True, 0),
    (4,  "phys-reward",         "Designing the reward",              100, True, 0),
    (8,  "phys-deploy",         "Deploy & watch your policy",        100, True, 0),
]
VRMR_LESSONS = [
    (1,  "vrmr-setup",          "Setup: Unity, Quest & your dev world", 100, True, 0),
    (2,  "vrmr-ai-partner",     "Building VR with your AI coding partner", 100, True, 0),
    (3,  "vrmr-interaction",    "Hands & controllers",               100, True, 0),
    (11, "vrmr-ship",           "Ship it to the Meta Store",         100, True, 0),
]
VRGAME_LESSONS = [
    (1,  "vrg-loop",            "Setup & the game loop",             100, True, 0),
    (2,  "vrg-mechanic",        "Core mechanic & physics",           100, True, 0),
    (3,  "vrg-enemy-ai",        "Enemy AI",                          100, True, 0),
    (9,  "vrg-ship",            "Ship your VR game",                 100, True, 0),
]
SCRGAME_LESSONS = [
    (1,  "sg-stack",            "The three-tool stack",              100, True, 0),
    (3,  "sg-import",           "Blender -> Unity import pipeline",  100, True, 0),
    (5,  "sg-mechanic",         "Core mechanic & game loop",         100, True, 0),
    (11, "sg-publish",          "Publish your game",                 100, True, 0),
]
AIVID_LESSONS = [
    (1,  "vid-stack",           "The AI video stack",                100, True, 0),
    (3,  "vid-voices",          "AI voices (TTS)",                   100, True, 0),
    (6,  "vid-captions",        "Word-synced kinetic captions",      100, True, 0),
    (10, "vid-publish",         "Publish at scale",                  100, True, 0),
]
AIMUS_LESSONS = [
    (1,  "mus-stack",           "The AI music stack",                100, True, 0),
    (3,  "mus-lyrics",          "Lyrics to song",                    100, True, 0),
    (5,  "mus-singer",          "Build your AI singer",              100, True, 0),
    (7,  "mus-master",          "Mixing & mastering",                100, True, 0),
]

# ---- Courses 4-9 (journeys; lessons drip later) ----
VRMR_MODULES = [
    (1,"M1","Setup — Unity, Quest & your dev environment","","Unity 6 + Meta XR SDK, a room running on your headset"),
    (2,"M2","Your AI coding partner — building VR with Claude Code","","Describe it in English -> the agent writes the C# -> test in VR"),
    (3,"M3","Hands & controllers — interacting with the world","","Hand tracking, grab/throw with physics, haptics"),
    (4,"M4","VR UI — menus, buttons & panels that work","","World-space UI, poke + laser interaction"),
    (5,"M5","Environment & audio — making VR feel like a place","","Skyboxes, Quest lighting, particles, spatial audio"),
    (6,"M6","Locomotion — moving without getting sick","","Teleport, smooth move, snap turn, comfort vignette"),
    (7,"M7","Saving data & session logic","","PlayerPrefs + JSON, a Menu->Session->Summary state machine"),
    (8,"M8","Multiplayer basics — sharing VR with others","","Photon Fusion, networked avatars, spatial voice"),
    (9,"M9","Mixed reality & passthrough","","Quest 3 passthrough, Scene API, spatial anchors"),
    (10,"M10","Performance & polish — Quest-ready","","Profiler, batching, ASTC textures, 72fps, the VRC checklist"),
    (11,"M11","Ship it — from build to the Meta Store","","Dev account, keystore, release APK, store listing, submit"),
]
PHYSAI_MODULES = [
    (1,"M1","Simulation & digital twins","","Why train in sim first; the digital-twin idea"),
    (2,"M2","Isaac Sim / Isaac Lab setup (provided)","","Into the NVIDIA stack on provided GPU"),
    (3,"M3","RL basics for control","","Agents, environments, rewards, episodes — aimed at movement"),
    (4,"M4","Designing the reward","","Shaping behavior through what you reward"),
    (5,"M5","Training your first policy","","Run PPO, read the curves, reach the goal"),
    (6,"M6","Sim-to-real concepts","","Domain randomization, the reality gap"),
    (7,"M7","Teleoperation & VR embodiment","","Drive & watch the policy from a Quest headset"),
    (8,"M8","Deploy & view your trained policy","","Export, render, watch your robot run in VR"),
]
AIVID_MODULES = [
    (1,"M1","The AI video stack","","Script -> voice -> visuals -> captions -> music -> render"),
    (2,"M2","Scripting for TTS","","Write for the ear — pacing, phrasing, punctuation"),
    (3,"M3","AI voices (F5-TTS)","","Natural narration from text, many voices/languages"),
    (4,"M4","Motion graphics (Manim)","","Animated graphics synced to narration"),
    (5,"M5","Contextual AI backgrounds","","Per-scene visuals that match the words"),
    (6,"M6","Word-synced kinetic captions","","Word-by-word highlight for retention + accessibility"),
    (7,"M7","Music + focus-audio beds","","A soft bed that sets emotion under the voice"),
    (8,"M8","Compositing & GPU render","","Layer it all on one timeline, render the MP4"),
    (9,"M9","Bilingual / localization","","Re-narrate + re-caption over the same visuals"),
    (10,"M10","Publishing & channel craft","","Copyright-clean, at scale, to your channel"),
]
VRGAME_MODULES = [
    (1,"M1","Setup & the game loop","","Unity + Meta XR + the per-frame loop"),
    (2,"M2","Core mechanics & physics","","Your central verb + grab/throw/collide with physics"),
    (3,"M3","Enemy AI","","State machines + pathfinding toward the player"),
    (4,"M4","Game feel / juice","","Hit-stop, particles, haptics, sound, shake"),
    (5,"M5","Levels & spawning","","Prefabs, spawners, a difficulty curve"),
    (6,"M6","Audio","","Spatial SFX + music for immersion"),
    (7,"M7","Score & saving","","Scoring + persistence across sessions"),
    (8,"M8","Performance","","Hold 72fps — batching, textures"),
    (9,"M9","Ship to the Meta Store","","Dev account, signed APK, listing, submit"),
]
SCRGAME_MODULES = [
    (1,"M1","Setup — Blender + Unity + AI","","The three-tool stack for a flat-screen game"),
    (2,"M2","Modeling in Blender","","Models, characters, props — then export"),
    (3,"M3","Import pipeline to Unity","","FBX/GLTF + textures, materials, colliders"),
    (4,"M4","AI-assisted coding","","Describe behavior in English -> the agent writes C#"),
    (5,"M5","Core mechanic & game loop","","The central verb run every frame"),
    (6,"M6","Character movement","","Input (keyboard/touch) -> a controller"),
    (7,"M7","Camera systems","","Follow + frame the player"),
    (8,"M8","UI / HUD","","Menus, score/health, pause on a canvas"),
    (9,"M9","Audio","","SFX + music for feedback and mood"),
    (10,"M10","Mobile build & performance","","Touch controls, frame budget, Android/iOS"),
    (11,"M11","Publish","","Build for the platform, list it, release"),
]
AIMUS_MODULES = [
    (1,"M1","The AI music stack","","Prompt/lyrics -> generate -> mix -> master"),
    (2,"M2","Prompt to music","","Steer style/genre/mood/instruments/BPM"),
    (3,"M3","Lyrics to song","","Feed lyrics + a style, the model sings them"),
    (4,"M4","Styles — beats, lofi, focus, meditation","","One engine, many genres"),
    (5,"M5","Build your AI singer (RVC)","","Train a voice, apply it to the vocals"),
    (6,"M6","Mixing","","Balance levels / EQ / panning"),
    (7,"M7","Mastering","","Loudness / EQ / limiting — pro + consistent"),
    (8,"M8","Focus / binaural audio","","Isochronic/binaural tones for focus + calm"),
    (9,"M9","Copyright-clean","","A permissive model so it's safe to monetize"),
    (10,"M10","Deliver & publish","","A mastered MP3/WAV ready to ship"),
]

AIPM_LESSONS = [
    (1, "ai-pm-mindset",             "The AI PM mindset",                               100, True, 0),
    (2, "ai-landscape-paradigms",    "AI vs ML vs DL, and the learning paradigms",      100, True, 0),
    (4, "ai-data-foundations",       "Data foundations & feasibility",                  100, True, 0),
    (5, "responsible-ai-gate",       "Ship it responsibly: drift, fairness & the gate", 100, True, 0),
    (6, "generative-ai-for-product", "Generative AI for product",                       100, True, 0),
    (8, "the-aipm-one-pager",        "The AIPM one-pager",                              100, True, 0),
]

AIPM_MODULES = [
    (1,"M1","The AI PM mindset","","PM as translator between value, user need & what data makes possible · the 5 shifts"),
    (2,"M2","AI landscape I","","AI vs ML vs DL vs Data Science · supervised / unsupervised / RL · is this even an ML problem?"),
    (3,"M3","AI landscape II + AI-first","","Problem shape -> model family · design for the wrong answer · cold-start · the feedback loop"),
    (4,"M4","AI/ML strategy I — data foundations","","Value x feasibility · build/buy/API · the non-ML baseline · data quality, splits, leakage, bias"),
    (5,"M5","AI/ML strategy II — ship it responsibly","","MLOps lifecycle · drift · latency/cost · fairness, privacy, explainability, human-in-the-loop"),
    (6,"M6","Generative AI for product","","Generative vs discriminative · LLMs, hallucination, context window · prompt -> RAG -> fine-tune · prompt engineering"),
    (7,"M7","Reading a model — linear regression","","Features, fitting, error · R-squared / MAE / RMSE · overfitting vs underfitting · trust the test set"),
    (8,"M8","Capstone — the AIPM one-pager","","Scope a real AI product end to end: problem -> data -> approach -> metrics -> responsible-AI -> ops"),
]


def _migrate():
    """Add the course columns to existing Postgres tables (no-op if already there / on SQLite)."""
    from sqlalchemy import text
    for stmt in (
        "ALTER TABLE modules ADD COLUMN IF NOT EXISTS course VARCHAR(40) DEFAULT 'agentic'",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS teacher_id INTEGER NULL",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS course VARCHAR(40) DEFAULT 'agentic'",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS phone VARCHAR(20) DEFAULT ''",
        "ALTER TABLE course_requests ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'whatsapp'",
        # subscription columns — sub_status added WITHOUT a server default so existing rows
        # are NULL exactly once (the grandfather step below keys on that). New ORM inserts
        # get 'none' from the model-side default.
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS sub_status VARCHAR(20)",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS rzp_customer_id VARCHAR(40) DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS rzp_subscription_id VARCHAR(40) DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS trial_end TIMESTAMP NULL",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP NULL",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS data_loop_consent BOOLEAN DEFAULT TRUE",
        # student assessment plan (₹199) — a SEPARATE track. DEFAULT 'none' (NOT NULL), and NO
        # grandfather UPDATE below — the assessment plan is a fresh paid track even for the existing
        # cohort (auto-comping it to everyone would be the footgun). Trial starts lazily on first
        # gated access (see has_assessment_access), so no one is retroactively expired when it's enabled.
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS assess_status VARCHAR(20) DEFAULT 'none'",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS rzp_assess_customer_id VARCHAR(40) DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS rzp_assess_subscription_id VARCHAR(40) DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS assess_trial_end TIMESTAMP NULL",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS assess_period_end TIMESTAMP NULL",
        # exam-prep test history: the full paper as sat, so a student can reopen a past test
        "ALTER TABLE topic_attempts ADD COLUMN IF NOT EXISTS detail JSON DEFAULT '[]'::json",
        # teacher/institute (B2B): a Student row can also be a teacher who creates class tests
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS is_teacher BOOLEAN DEFAULT FALSE",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS institute VARCHAR(120) DEFAULT ''",
        # self-serve white-label branding (teacher /teacher/branding): colour, logo (data-URL), watermark
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS brand_color VARCHAR(9) DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS brand_logo TEXT DEFAULT ''",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS brand_watermark BOOLEAN DEFAULT FALSE",
        # institute classroom (B2B2C) — batch-scoping + account-linked results:
        #  batch_id  = which TeacherInvite (batch) a linked student joined through
        #  invite_id = which batch an Assignment targets (NULL = all the teacher's batches)
        #  student_id on a ClassSitting = the logged-in linked student who took it (else anonymous name)
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS batch_id INTEGER NULL",
        "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS invite_id INTEGER NULL",
        "ALTER TABLE class_sittings ADD COLUMN IF NOT EXISTS student_id INTEGER NULL",
        # per-question answer record so the teacher can review what each student answered
        "ALTER TABLE class_sittings ADD COLUMN IF NOT EXISTS detail JSON DEFAULT '[]'::json",
        # kids product: class + board on students (set at join, locks self-generated worksheets) and on
        # the batch (TeacherInvite); a frozen worksheet pack for a FIXED kids test (kind=kidstest).
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS grade INTEGER NULL",
        "ALTER TABLE students ADD COLUMN IF NOT EXISTS board VARCHAR(24) DEFAULT ''",
        "ALTER TABLE teacher_invites ADD COLUMN IF NOT EXISTS grade INTEGER NULL",
        "ALTER TABLE teacher_invites ADD COLUMN IF NOT EXISTS board VARCHAR(24) DEFAULT ''",
        "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS pack JSON NULL",
        # GRANDFATHER (one-time): every student that exists when the column is first added is
        # NULL → mark grandfathered (full access forever, never paywalled). Re-running matches
        # nothing because new signups are 'none' (not NULL), so it's idempotent.
        "UPDATE students SET sub_status='grandfathered' WHERE sub_status IS NULL",
    ):
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            print(f"[migrate] skip: {exc}")


def run():
    _migrate()
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        mod_by_key = {}
        for course, mods in (("agentic", MODULES), ("remote-swe", SWE_MODULES), ("ml-and-math", ML_MODULES),
                             ("vr-mr-app", VRMR_MODULES), ("physical-ai", PHYSAI_MODULES), ("ai-video-factory", AIVID_MODULES),
                             ("vr-game", VRGAME_MODULES), ("screen-game", SCRGAME_MODULES), ("ai-music-factory", AIMUS_MODULES),
                             ("ai-pm", AIPM_MODULES)):
            for week, code, title, sdate, summary in mods:
                m = db.query(Module).filter_by(course=course, week=week).first()
                if not m:
                    m = Module(course=course, week=week, code=code, title=title,
                               session_date=sdate, summary=summary, sort=week)
                    db.add(m)
                    db.flush()
                else:
                    m.course, m.code, m.title, m.summary = course, code, title, summary
                mod_by_key[(course, week)] = m

        for course, lessons in (("agentic", LESSONS), ("remote-swe", SWE_LESSONS), ("ml-and-math", ML_LESSONS),
                                ("physical-ai", PHYS_LESSONS), ("vr-mr-app", VRMR_LESSONS), ("vr-game", VRGAME_LESSONS),
                                ("screen-game", SCRGAME_LESSONS), ("ai-video-factory", AIVID_LESSONS), ("ai-music-factory", AIMUS_LESSONS),
                                ("ai-pm", AIPM_LESSONS)):
            for week, slug, title, gems, available, sort in lessons:
                l = db.query(Lesson).filter_by(slug=slug).first()
                if not l:
                    db.add(Lesson(module_id=mod_by_key[(course, week)].id, slug=slug, title=title,
                                  max_gems=gems, available=available, sort=sort))
                else:
                    l.module_id = mod_by_key[(course, week)].id
                    l.title = title
                    l.sort = sort
                    l.available = available

        for week, data in WORKBOOK.items():
            existing = db.query(WorkbookTask).filter_by(week=week).count()
            if existing:
                continue
            sort = 0
            for day, ddate, focus, task, minutes in data["days"]:
                db.add(WorkbookTask(week=week, day=day, day_date=ddate, focus=focus,
                                    task=task, minutes=minutes, is_bring=False, sort=sort))
                sort += 1
            db.add(WorkbookTask(week=week, day="Fri", day_date="", focus="Bring to Friday",
                                task=data["bring"], minutes=0, is_bring=True, sort=sort))

        # demo accounts (email, name, admin, course)
        for email, name, admin, course in [
            ("deepak@trigunai.com", "Deepak", True, "agentic"),
            ("student@example.com", "Test Student", False, "agentic"),
            ("swe@example.com", "SWE Test Student", False, "remote-swe"),
        ]:
            if not db.query(Student).filter_by(email=email).first():
                db.add(Student(email=email, name=name, is_admin=admin, course=course))

        db.commit()
        print(f"Seeded {len(MODULES)} modules, {len(LESSONS)} lessons, "
              f"{sum(len(w['days']) + 1 for w in WORKBOOK.values())} workbook tasks.")
        print(f"DB: {settings.DATABASE_URL}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
