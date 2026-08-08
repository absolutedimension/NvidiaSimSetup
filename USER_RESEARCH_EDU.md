# TrigunAI — Education User Research (living knowledge base)

> Maintained by the **user-research-education-trigunai** skill. Every insight traces to a real user.
> Small-N is stated honestly. Objections are data. Numbers = counts of real conversations.

_Last updated: 2026-07-04 (loop run #2)_

---

## 0. Demand signal so far (real, from Maya calls)

**2026-07-04 — first live calling day (NEET/JEE focus):** _(unchanged since loop #1 — no new
dials since; the 52 transcript files are the same batch)._
- Unique teachers dialed: **50** · answered (real conversation): **29** · interested (yes): **4**
- **Interested ≈ 14% of answered (4/29)** — encouraging first-day cold-outreach signal
- Answer rate ~58% of dialed (29/50) — Indian +91 caller-ID + Hindi AI is getting picked up and engaged

**Interested institutes (warm leads, expecting follow-up):**
| Institute | City | Segment | Call dur | Phone |
|---|---|---|---|---|
| Catalyzers Institute | Kota | NEET/JEE | 60s | 917737976414 |
| Goal Institute | Patna | NEET/JEE | 49s | 917564902125 |
| Perfect Mathematics Classes | Patna | Maths/JEE | 55s | 919155962008 |
| Physics for IIT-JEE (Er. M.K. Thakur) | Patna | Physics | 63s | 917004179675 |

**NEW warm lead — self-onboarded via Acharya WhatsApp (not in the call CSV):**
| "Jain" — biology, Class 11–12, **20–25 students** | via WhatsApp | `role: teacher_pending`, onboarding done | 919801070457 |
> This is a real independent subject-specialist teacher who came inbound and asked to set up a teacher
> account. Verbatim self-description: _"My name is Jain, biology class 11 and 12, 20-25 Students"_.
> Matches the early pattern below. **Action: Deepak follow-up owed (profile says "within 1 working day").**

Early pattern (small N): **subject-specialist independents (physics / maths / biology) + Patna/Kota
exam-prep** are the most responsive. All 4 phone-yeses + the 1 inbound are subject specialists or Patna/Kota.
Big chains excluded by design (competition, not buyers).

---

## 1. Pain points — TEACHERS (evidence-linked)

> ⚠️ **BLOCKER PERSISTS (loop #2 confirms):** across **52 call transcripts**, only Maya's side
> transcribes. Teacher audio is essentially never captured as text (1 file had teacher lines, and they
> were garbled Hindi/Urdu ASR — unusable). **We have ZERO verbatim teacher pain quotes.** The `interested`
> flag in `call_results.csv` is the only teacher-side signal we're capturing today.
>
> **This is the #1 thing blocking teacher research.** Two fixes, either unblocks us:
> 1. Run the **discovery-mode Maya batch** (skill §5) — 15–20 calls that ask 1–2 open pain questions and
>    let the teacher talk; then mine the **Plivo recordings** (audio) for their words, since text ASR fails.
> 2. Improve teacher-side Hindi ASR / diarization in the transcript writer (content-marketing-bot §6.5).

| Pain tag | Count | Evidence / verbatim quotes (source) | Intensity |
|---|---|---|---|
| after-hours doubts | – | _no quote yet — Maya's pitch assumes it; teachers haven't said it in captured text_ | – |
| too many students / can't scale attention | – | _pending discovery-call quotes_ | – |
| cost / ROI sensitivity | – | _pending_ | – |
| tech-shyness / setup fear | – | _pending_ | – |
| student engagement & retention | – | _pending_ | – |
| admissions & follow-up load | – | _pending_ | – |

### 1a. Hypothesis pain-anchors (desk research 2026-07-04 — used as Maya discovery examples, NOT yet validated by our own teachers)
> These are the discovery-question memory-joggers, grounded in coaching-software "problems we solve"
> pages (Classplus/Teachmint/myClassCampus/Classpro) + teacher/student first-person threads (Quora,
> Reddit). They are **hypotheses to test**, not our teachers' validated pains — the discovery calls
> confirm or replace them. The 4 marked ⭐ appeared in BOTH vendor copy and first-person complaints.

**A. Running-the-business (non-teaching), most universal first:**
1. Getting new admissions / filling batches (lead-flow, not word-of-mouth) — U
2. ⭐ Fee collection & follow-up (manual, memory-dependent, quiet revenue leak) — U
3. Admin overload past ~50 students ("managing instead of teaching") — U
4. ⭐ Parent communication / progress updates — U
5. Student retention / mid-term dropouts — scales with size
6. Hiring/retaining teachers — only for multi-teacher institutes

**B. Inside the teaching process, most universal first:**
1. ⭐ Students don't practice / can't solve on their own — U
2. ⭐ Can't track each student's weak topics — U
3. Mixed-ability batch (fast vs slow in one room) — U
4. Rote learning, no conceptual understanding — U
5. Doubt-solving doesn't scale after class — bigger batches
6. Syllabus-completion vs depth pressure — sharpest for exam-prep

> **Honest note:** Maya currently *leads with our solution* ("AI se kam mehnat mein zyada bachchon tak
> pahunch") rather than *discovering the teacher's own stated pain*. So even a perfect transcript would
> capture reactions-to-our-pitch, not the teacher's unprompted #1 problem. Discovery mode fixes both.

## 2. Pain points — STUDENTS / LEARNERS (from Acharya learner profiles — REAL, loop #2)

> Source: `~/.openclaw/students/*.json` on the Gurukul VM (Acharya per-student Learner Profiles).
> **Population caveat (important):** the learners currently on Acharya are TrigunAI's **own-course
> students** (courses: `agentic`, `ai-music-factory`, `remote-swe`) — **NOT** the NEET/JEE exam-prep
> students of the coaching teachers Maya is calling. Valid student-struggle data, but a *different
> segment*. Exam-prep student pains will only appear once a coaching teacher's cohort is on Acharya.
> N = 7 real learners (24 profiles total; 17 are test/dev/web-test accounts, excluded).

| Pain tag | Count | Evidence (verbatim / concrete, source profile) | Intensity |
|---|---|---|---|
| **weak-concept loops (same concept stays "shaky")** | 4 of 7 | `agent_loop` = "shaky" for Kritansh (mod 3, 30 logged misconceptions), Priyanshu/917070 (streak 22), adityamittal (streak 14), 919431043629 (new). Concept doesn't consolidate across modules. | **High** |
| **the "observe" step of the agent loop is the sticking point** | 3+ | Priyanshu/917070: _"Confused the concept of 'observe' with 'minutes of meeting'"_, _"Misunderstood the difference between 'Act' and 'Observe'"_. Kritansh: _"After my agent gives an answer, what should it observe to decide the next step?"_. adityamittal: repeated observe-phase corrections. | **High — single fixable concept** |
| **"agent vs chatbot" boundary unclear** | 2–3 | Kritansh: _"I'm not sure how to transition my helper from acting like a chatbot to functioning as an agent"_; _"I'm not sure which part of my agent is a chatbot and which part is an agent."_ adityamittal: multiple agent-vs-chatbot corrections. | Med-High |
| **tool boundary / who-actually-runs-the-tool** | 2 | Kritansh: _"If the LLM only produces text, how can the agent actually update a sheet or send a message?"_, _"When the model 'calls a tool', who actually runs the function?"_ | Med |
| **clarity-vs-loudness & vague prompts (music learners)** | 1 (deep) | Priyanshu Jain (ai-music-factory, streak 67, 30 misconceptions): _"Chasing maximum loudness rather than clarity"_, _"Making music too cinematic and drowning the shloka"_, _"Using vague prompts instead of clear, detailed instructions."_ | Med |
| **Big-O / complexity intuition (SWE learner)** | 1 | Priyanshu/918454 (remote-swe): O(n) vs O(n²), constants in Big-O, nested-loop confusion. | Low |

**Positive signal:** engagement is real — streaks of **56, 67, 22, 20, 14** days. These learners keep
coming back to a WhatsApp tutor. That's the retention proof the coaching-teacher pitch rests on.

---

## 3. Insight → agentic solution → execution

| Validated pain | Agentic solution hypothesis | Maya / product tweak | Marketing hook (real → copy) |
|---|---|---|---|
| Learners stay "shaky" on the **same concept** across modules (4/7) | Acharya's SRS + mastery-gate should **block module advance** until the shaky concept is re-passed, and re-teach with a *fresh analogy*, not the same one | Feeds **project-learning-loop / project-tutor-rl** — this is exactly the loop-hardening signal | "पढ़ता तो है, पर वही concept बार-बार अटकता है — Acharya तब तक नहीं छोड़ता जब तक समझ न आए" |
| The **"observe" step** is the universal sticking point in agentic course | Author a dedicated micro-lesson + a concrete non-tech analogy ("observe = did the food actually arrive?"); add a targeted recall card | Content/pedagogy fix in the agentic concept bank (`add-trigunai-course`) | — (internal pedagogy, not outbound) |
| Music learners over-produce & drown the vocal | Acharya should surface the "voice loudest & clearest" rule as a checkable step before publish | ai-music-factory concept bank | "सुंदर music नहीं — साफ़ आवाज़ बिकती है" |
| _Teacher after-hours-doubt pain (Maya's core pitch)_ | Acharya auto-answers after-hours under teacher's brand (already the product) | ⚠️ **still un-validated by a real teacher quote** — get one via discovery mode before leaning on it in copy | "9 बजे रात को doubt आए तो पढ़ाई रुकनी नहीं चाहिए" _(our hypothesis, not yet a teacher's words)_ |

---

## 4. Next research actions (priority order)

1. **🟢 ARMED (2026-07-04): Discovery mode is deployed and ready to run.** Root cause of the missing
   teacher quotes found: the bridge only transcribes the caller *while Maya is silent* (half-duplex), and
   the screener has Maya talking most of the call — so teacher audio is dropped. Discovery Maya asks open
   questions then goes silent to listen → captures teacher words AND yields real pains. Deployed as a
   non-breaking `MAYA_MODE=discovery` gate + plain-text `maya_discovery_prompt.txt` on the Gurukul VM.
   **To run: follow [research_batch/DISCOVERY_MODE_RUNBOOK.md](research_batch/DISCOVERY_MODE_RUNBOOK.md)**
   (stop screener → `start_discovery.sh` → dial 15–20 → revert). Then mine transcripts/recordings into §1.
2. **🟠 Follow up the inbound teacher "Jain" (919801070457)** — biology, 20–25 students, `teacher_pending`,
   promised contact within 1 working day. A real teacher who *came to us* is worth more than a cold dial;
   his onboarding call is also a free discovery interview — capture his workflow/pains.
3. **🟡 Fix teacher-side transcription** (or standardize on recordings) so future calls capture quotes.
4. **🟢 Re-mine Acharya profiles weekly** — the concept-shakiness pattern is a live signal; watch whether
   the same concepts stay shaky (pedagogy isn't working) or clear (loop is working). Feed to
   project-learning-loop.
5. Once a coaching teacher's *own students* are on Acharya, mine those profiles — that's when real
   **exam-prep student** pains (§2's intended segment) become visible.
