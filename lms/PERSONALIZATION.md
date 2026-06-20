# TrigunAI LMS — Personalization (learner context)

> How we get to know each learner **gradually** (never a big form) and use it to explain things
> in *their* world — examples from their work, tools, and hobbies. Research-backed; see sources.

---

## 1. The principle (from the research)

Modern personalized learning treats the learner profile as a **recurrent cycle**:
*deliver → capture evidence → recalibrate the profile → personalize the next delivery* — it
**evolves over time**, it isn't a one-shot diagnosis at signup. The best systems gather context
**conversationally and from interaction traces**, not from a questionnaire, and feed it into an
LLM to ground explanations in the learner's interests, background, and prior experiences.

Two evidence streams matter:
1. **Stated context** — what the learner tells us (work, why, interests, tools, comfort).
2. **Behavioural context** — what they do (which steps they retry, where they get stuck, pace,
   time-of-day, lesson scores).

We capture stated context now (low-friction) and lay the schema to add behavioural later.

---

## 2. How we capture it (no questionnaire)

Three low-friction channels, all writing to one `learner_facts` key/value store:

| Channel | Where | How it feels |
|---|---|---|
| **Micro-questions** | Dashboard "Help us teach you better" card | ONE casual question at a time, optional, skippable, +5💎 each. Rotates to the next unanswered one. (`personalize.MICRO_QUESTIONS`) |
| **In-lesson reflects** | `reflect` steps with `capture:true` | Natural "tell us about you" / "make it yours" moments inside lessons post straight to the profile (`source:"lesson"`). |
| **Behavioural (future)** | `events` + `lesson_progress` | Retries, stuck points, pace, scores → inferred facts (`source:"inferred"`). Schema is ready; inference is a follow-up. |

Priority order of micro-questions: `name → work → why → interest → tools → experience → routine`.
Each answered fact awards gems and never blocks anything.

---

## 3. How it personalizes (the payoff)

`personalize.build_learner_context(facts)` produces a compact natural-language brief, e.g.:

```
PERSONALIZATION CONTEXT — use this to ground examples and analogies in THIS learner's world…
The learner's name is Priya. They work/study in: running a small Shopify store.
They joined to: automate daily lead follow-ups. A hobby they love: cooking.
Apps they use daily: Gmail, Google Sheets. Coding comfort: a little.
```

This string is injected in two places:

1. **The tutor ("TrigunAI guide")** — when wired to the LiteLLM proxy (Azure GPT-4o-mini), the
   system prompt = `tutor rules + build_learner_context(facts)`. So when Priya is stuck, the
   guide reaches for a Shopify/Gmail example, not a generic one, and pitches difficulty to
   "a little" coding comfort.
2. **Example generation** — lesson steps can carry a `personalize:true` flag; at serve time the
   LLM rewrites the example/scenario text using the learner context (e.g. the inbox-agent
   example becomes an order-confirmation-agent for a Shopify owner). The fallback is always the
   authored generic example, so it degrades gracefully when we know nothing.

Already live (no LLM needed): the **dashboard greeting** ("Welcome back, Priya — let's build
agents for running a small Shopify store.") and the gem-rewarded capture loop.

---

## 4. Data model

```
learner_facts(student_id, key, value, source, updated_at)   # one row per fact, upserted
  key ∈ {name, work, why, interest, tools, experience, routine, goal, stop, …}
  source ∈ {prompt, lesson, inferred}
```
Flexible key/value so new signals don't need migrations. `goal`/`stop` from the lesson reflect
also land here — they're both personalization context *and* the student's project definition.

## 5. API

- `POST /api/profile/capture` `{key, value, source}` → upsert, +5💎 on first capture, returns next question
- `GET  /api/profile` → `{facts, context}` (context = the injectable brief)

## 6. Privacy / trust

- Used only to shape examples and tutoring; never sold or shown to other students.
- The capture card says why ("so your lessons use examples from your world") and is always skippable.
- A learner can see/edit their facts (planned settings page).

## 7. Build status

- ✅ `learner_facts` model · capture + read APIs · micro-question engine · dashboard card · greeting
- ✅ in-lesson reflect capture (`capture:true` steps post to the profile)
- ✅ `build_learner_context()` ready for injection
- ⏳ wire the brief into the LLM tutor (LiteLLM proxy) — turns the guide conversational + personalized
- ⏳ `personalize:true` lesson steps → LLM example rewriting at serve time
- ⏳ behavioural inference (retries/pace/scores → inferred facts)

---

**Sources:** [Human-centered adaptive e-learning (Frontiers, 2026)](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2026.1826488/full) ·
[Context-based learning: contextual indicators (Frontiers, 2023)](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2023.1210968/full) ·
[Learning in Context: Personalizing Content with LLMs (arXiv 2509.15068)](https://arxiv.org/pdf/2509.15068) ·
[Learning Context: framework for context-aware AI in education (arXiv 2512.24362)](https://arxiv.org/pdf/2512.24362) ·
[Learner profiling guide (VerifyEd)](https://www.verifyed.io/blog/complete-learner-profiling-guide)
