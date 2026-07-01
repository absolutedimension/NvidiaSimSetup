"""Stage 0 — Knowledge graph + misconception bank for the `agentic-systems` course.

Grounded in the real LMS curriculum (lms/app/seed.py LESSONS).  This is the
domain the student simulator lives in: the skills, their prerequisite edges, and
the specific wrong mental models real learners hold.  Everything downstream
(student_env, tutors, training) reads from here.

A simulator can only contain mistakes you put in it — so the misconception bank
is the part that MUST be calibrated against real Acharya logs once the flywheel
runs.  These entries are seeded from learning-science priors + the lesson content.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Skills  (one node per real lesson, in curriculum order)
# ---------------------------------------------------------------------------
SKILLS = [
    "goal-to-agent",            # 0  the big idea: goal -> agent
    "what-is-an-agent",         # 1  brain, tools & the loop
    "first-tool-calling-agent", # 2  your first tool-calling agent
    "tools-and-integrations",   # 3  tools & integrations
    "memory-and-context",       # 4  memory & context
    "planning-and-multi-step",  # 5  planning & multi-step
    "reliability-and-guardrails", # 6 reliability & guardrails
    "multi-agent-systems",      # 7  multi-agent systems
    "deploy-your-agent",        # 8  deploy your agent
    "ship-a-real-business-agent", # 9 ship a real business agent
]
K = len(SKILLS)
SKILL_IDX = {s: i for i, s in enumerate(SKILLS)}

# Prerequisite edges: prereq -> dependent.  A learner can't really master a
# dependent skill until its prereqs are up.  Drawn from the week ordering.
PREREQS = {
    "goal-to-agent": [],
    "what-is-an-agent": ["goal-to-agent"],
    "first-tool-calling-agent": ["what-is-an-agent"],
    "tools-and-integrations": ["first-tool-calling-agent"],
    "memory-and-context": ["first-tool-calling-agent"],
    "planning-and-multi-step": ["tools-and-integrations", "memory-and-context"],
    "reliability-and-guardrails": ["planning-and-multi-step"],
    "multi-agent-systems": ["planning-and-multi-step"],
    "deploy-your-agent": ["reliability-and-guardrails"],
    "ship-a-real-business-agent": ["deploy-your-agent", "multi-agent-systems"],
}
# Adjacency for transfer (mastery spills to graph neighbours a little)
NEIGHBORS = {s: set(PREREQS[s]) for s in SKILLS}
for s, ps in PREREQS.items():
    for p in ps:
        NEIGHBORS[p].add(s)

PREREQ_IDX = {SKILL_IDX[s]: [SKILL_IDX[p] for p in ps] for s, ps in PREREQS.items()}
NEIGHBOR_IDX = {SKILL_IDX[s]: [SKILL_IDX[n] for n in ns] for s, ns in NEIGHBORS.items()}

# ---------------------------------------------------------------------------
# Misconception bank
# ---------------------------------------------------------------------------
# repaired_by / reinforced_by reference MOVE TYPES (see student_env.MOVES).
# repair_difficulty in [0,1]: how sticky the wrong model is.
MISCONCEPTIONS = [
    dict(id="agent-eq-chatbot", skill="what-is-an-agent", repair_difficulty=0.6,
         desc="Thinks an agent is just a chatbot with a personality — ignores the action loop.",
         repaired_by=["worked_example", "ask_recall", "practice"],
         reinforced_by=["explain"]),
    dict(id="tools-are-magic", skill="tools-and-integrations", repair_difficulty=0.5,
         desc="Believes 'tools' work by magic; doesn't grasp they're typed function calls the model emits.",
         repaired_by=["worked_example", "practice"],
         reinforced_by=["explain"]),
    dict(id="memory-eq-bigger-prompt", skill="memory-and-context", repair_difficulty=0.55,
         desc="Thinks more memory just means a bigger prompt; misses retrieval / state.",
         repaired_by=["worked_example", "ask_recall"],
         reinforced_by=["explain"]),
    dict(id="planning-is-one-shot", skill="planning-and-multi-step", repair_difficulty=0.65,
         desc="Assumes the model plans the whole task in one shot; misses the observe-act loop.",
         repaired_by=["worked_example", "practice", "ask_recall"],
         reinforced_by=["explain"]),
    dict(id="guardrails-optional", skill="reliability-and-guardrails", repair_difficulty=0.45,
         desc="Treats reliability/guardrails as optional polish, not core to a real agent.",
         repaired_by=["worked_example", "practice"],
         reinforced_by=["explain"]),
    dict(id="more-agents-better", skill="multi-agent-systems", repair_difficulty=0.5,
         desc="Thinks multi-agent always beats single-agent; misses coordination cost.",
         repaired_by=["worked_example", "ask_recall"],
         reinforced_by=["explain"]),
    dict(id="deploy-eq-run-locally", skill="deploy-your-agent", repair_difficulty=0.4,
         desc="Equates 'deploy' with running it on the laptop; misses serving/state/secrets.",
         repaired_by=["worked_example", "practice"],
         reinforced_by=["explain"]),
]
MISC_BY_ID = {m["id"]: m for m in MISCONCEPTIONS}
MISC_BY_SKILL: dict[int, list[dict]] = {}
for _m in MISCONCEPTIONS:
    MISC_BY_SKILL.setdefault(SKILL_IDX[_m["skill"]], []).append(_m)

# Real-world prevalence (used by domain randomization at reset)
MISC_PREVALENCE = {
    "agent-eq-chatbot": 0.55, "tools-are-magic": 0.45, "memory-eq-bigger-prompt": 0.40,
    "planning-is-one-shot": 0.45, "guardrails-optional": 0.35, "more-agents-better": 0.30,
    "deploy-eq-run-locally": 0.30,
}
