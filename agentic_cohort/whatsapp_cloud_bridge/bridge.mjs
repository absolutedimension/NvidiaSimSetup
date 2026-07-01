// WhatsApp Cloud API ↔ OpenClaw bridge (direct Meta, robust — no logouts).
// Meta webhook -> [load Learner Profile] -> openclaw agent (per-student session, profile-injected)
//   -> reply via Graph API -> [background: update + save the profile].
//
// Env (~/.openclaw/wa_cloud.env): META_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN, PORT, GRAPH_VERSION
// Per-student profiles: ~/.openclaw/students/<wa_id>.json

import http from "node:http";
import fs from "node:fs";
import crypto from "node:crypto";
import { execFile } from "node:child_process";

const {
  META_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN,
  PORT = "8788", GRAPH_VERSION = "v21.0",
} = process.env;

const HOME = process.env.HOME;
const STUDENTS_DIR = `${HOME}/.openclaw/students`;
fs.mkdirSync(STUDENTS_DIR, { recursive: true });
// Per-course concept bank. courses/<id>.json = { name, order, assessments, concepts }. Falls back to agentic.
function courseBank(course) {
  const id = (course || "agentic").replace(/[^a-z0-9-]/gi, "");
  for (const c of [id, "agentic"]) {
    try { return JSON.parse(fs.readFileSync(`${HOME}/.openclaw/gurukul/courses/${c}.json`, "utf8")); } catch {}
  }
  return { concepts: {}, order: [], name: "Building Agentic AI Systems" };
}
function loadConcepts(course) { return courseBank(course).concepts || {}; }

const log = (...a) => console.log(new Date().toISOString(), ...a);
const TUTOR_MODEL = "microsoft-foundry/gpt-5.5";
const EXTRACT_MODEL = "microsoft-foundry/gpt-4o-mini";
// Numbers in ADMIN_NUMBERS route to the Sutradhaar admin agent (ops/coding), not Acharya.
const ADMIN_NUMBERS = (process.env.ADMIN_NUMBERS || "").split(",").map(s => s.trim()).filter(Boolean);
// Shared secret with the LMS — signs web-chat tokens so students can't impersonate each other.
const CHAT_SECRET = process.env.CHAT_SECRET || "";

// ---------- Learner Profile store ----------
const profilePath = (waId) => `${STUDENTS_DIR}/${waId}.json`;

function loadProfile(waId) {
  try { return JSON.parse(fs.readFileSync(profilePath(waId), "utf8")); }
  catch {
    return { wa_id: waId, name: "", byoa_goal: "", level: "", current_module: 2,
             concepts: {}, misconceptions: [], srs: [], streak: 0, last_win: "", notes: [],
             interests: [], background: "", style: "", course: "agentic" };   // course + personal context
  }
}
function saveProfile(waId, p) {
  p.wa_id = waId; p.updated = new Date().toISOString();
  fs.writeFileSync(profilePath(waId), JSON.stringify(p, null, 2));
}

// ---------- SRS schedule + append-only event log (ML training fuel) ----------
const SRS_INTERVALS = [1, 2, 4, 8, 16];                 // box -> days until next due
const DUE = (days) => { const d = new Date(); d.setDate(d.getDate() + days); return d.toISOString(); };
const EVENTS = `${HOME}/.openclaw/gurukul/events.jsonl`;
// Every learning event, append-only. Raw "turn" events are captured at reply time regardless of
// whether the (best-effort) profile extraction succeeds — so the dataset is never lost.
function logEvent(e) {
  try { fs.appendFileSync(EVENTS, JSON.stringify({ ts: new Date().toISOString(), ...e }) + "\n"); }
  catch (err) { log("event log failed:", err.message); }
}
// One-time/idempotent: drop concept keys (and SRS items) not in each student's enrolled course bank.
// Fixes the cross-course pollution (e.g. music concepts on an agentic student).
function sanitizeAllProfiles() {
  let fixed = 0;
  for (const f of fs.readdirSync(STUDENTS_DIR)) {
    if (!f.endsWith(".json") || f.startsWith("_")) continue;
    const waId = f.replace(/\.json$/, "");
    try {
      const p = loadProfile(waId);
      const valid = new Set(Object.keys(courseBank(p.course).concepts || {}));
      const before = JSON.stringify([p.concepts || {}, p.srs || []]);
      const clean = {};
      for (const [k, v] of Object.entries(p.concepts || {})) if (valid.has(k)) clean[k] = v;
      const srs = (Array.isArray(p.srs) ? p.srs : []).filter(s => valid.has(s.concept));
      if (JSON.stringify([clean, srs]) !== before) { p.concepts = clean; p.srs = srs; saveProfile(waId, p); fixed++; }
    } catch { /* skip unreadable */ }
  }
  if (fixed) log(`sanitized ${fixed} profile(s): removed cross-course concept/SRS keys`);
}
// Compact context block Acharya reads silently before replying.
function profilePreamble(p) {
  const bank = courseBank(p.course);
  const order = bank.order || [];
  const current = order.find(k => (p.concepts || {})[k] !== "solid") || order[order.length - 1] || "";
  const courseLine =
    `[COURSE — teach ONLY this course, in this exact order, no skipping]\n` +
    `course: ${bank.name}\n` +
    `concept order: ${order.join(" -> ") || "(see your skill)"}\n` +
    `current step (teach next; don't advance until mastered): ${current || "start at the beginning"}\n`;
  const known = p.byoa_goal || p.level || Object.keys(p.concepts || {}).length;
  if (!known) return courseLine + `---\n`;
  return courseLine +
    `[STUDENT PROFILE — use silently to personalize; do NOT echo this back]\n` +
    `name: ${p.name || "?"} | goal: ${p.byoa_goal || "?"} | level: ${p.level || "?"}\n` +
    `mastery: ${JSON.stringify(p.concepts || {})}\n` +
    `misconceptions: ${(p.misconceptions || []).join("; ") || "none"} | streak: ${p.streak} | last_win: ${p.last_win || "-"}\n` +
    `interests: ${(p.interests || []).join(", ") || "?"} | background: ${p.background || "?"} | style: ${p.style || "?"}\n` +
    `(Use interests/background in examples & analogies. style = how they like to learn.)\n` +
    `---\n`;
}

// ---------- OpenClaw calls ----------
function runOpenClaw(args, timeoutMs = 130000) {
  return new Promise((resolve) => {
    execFile("openclaw", args, { timeout: timeoutMs, maxBuffer: 8 * 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err) { log("openclaw error:", (stderr || err.message).slice(0, 200)); return resolve(null); }
        resolve(stdout);
      });
  });
}

// One Sutradhaar (admin) turn — ops/coding, no student profile, longer timeout (can run commands).
async function askAdmin(waId, text) {
  const stdout = await runOpenClaw([
    "agent", "--agent", "admin", "--to", `+${waId}`, "--message", text, "--json", "--timeout", "300",
  ], 320000);
  if (!stdout) return null;
  try {
    const j = JSON.parse(stdout);
    return (j.result?.payloads || []).map(p => p.text).filter(Boolean).join("\n").trim() || null;
  } catch { return stdout.trim() || null; }
}

// ---------- cold-inbound onboarding: introduce TrigunAI + course menu (no silent agentic default) ----------
const COURSE_MENU = [
  ["agentic",          "Build Agentic AI Systems"],
  ["ml-and-math",      "Machine Learning & its Math"],
  ["ai-pm",            "AI Product Management"],
  ["remote-swe",       "Command the Coding Agent — crack a remote SWE job"],
  ["physical-ai",      "Physical AI — train a robot in simulation"],
  ["vr-mr-app",        "Build & ship your first VR/MR app"],
  ["vr-game",          "Build a fully immersive VR game"],
  ["screen-game",      "Build a game with Blender + Unity"],
  ["ai-video-factory", "Build your AI Video Factory"],
  ["ai-music-factory", "Build your AI Music Factory"],
];
function courseListText() {
  return COURSE_MENU.map(([, name], i) => `${i + 1}. ${name}`).join("\n") +
         `\n11. ✍️ *Something else* — I'll build it for you`;
}
function courseMenuText() {
  return `🪔 Namaste! I'm *Acharya*, TrigunAI's AI guide — I teach you to *build* with AI, one-on-one.\n\n` +
         `What do you want to learn? Reply with a number:\n\n${courseListText()}\n\n` +
         `👨‍🏫 *Are you a teacher?* Reply *TEACHER* to run your own class with Acharya.\n\n` +
         `…or just tell me in your own words.`;
}
function switchMenuText(current) {
  return `🔁 Sure — here's everything you can learn. Reply with a number to switch` +
         `${current ? ` (or *cancel* to stay on ${current})` : ""}:\n\n${courseListText()}`;
}
function customPromptText() {
  return `🎯 Love it — tell me what you want to learn and I'll prepare a course for you!\n\n` +
         `Popular requests:\n` +
         `• Govt-exam prep with AI (UPSC / SSC / Banking)\n` +
         `• Data Analytics & dashboards\n` +
         `• Cybersecurity & ethical hacking\n` +
         `• Full-stack web development\n` +
         `• Digital marketing & growth with AI\n` +
         `• Cloud & DevOps (AWS / Azure)\n` +
         `• Data Science with Python\n\n` +
         `…or just type your own topic 👇`;
}
// Log a custom course request to the LMS (Deepak builds it, then notifies the learner on this number).
async function requestCourse(topic, email, waId) {
  const base = process.env.LMS_SIGNUP_URL, key = process.env.LMS_BRIDGE_KEY;
  if (!base || !key) { log("requestCourse skipped — LMS env not set"); return; }
  const url = base.replace(/\/signup$/, "/course-request");
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "X-Bridge-Key": key, "Content-Type": "application/json" },
      body: JSON.stringify({ topic, email: email || "", phone: waId }),
    });
    log("requestCourse", JSON.stringify(topic).slice(0, 60), "->", r.status);
  } catch (e) { log("requestCourse failed:", e.message); }
}
// Finalize a custom request: log it, mark onboarded, and tell the learner to wait ~2 working days.
async function submitCustom(waId, profile, topic) {
  await requestCourse(topic, profile.email || "", waId);
  profile.custom_topic = topic;
  profile.onboarding = "done";
  profile.onboarded = true;
  profile.greeted = true;
  saveProfile(waId, profile);
  return `🙏 Thank you! Your course on *${topic}* will be ready in about *2 working days*. ` +
         `I'll message you right here on WhatsApp the moment it's live. 🪔`;
}
// ---------- teacher onboarding request (Stage 0: capture the lead, Deepak onboards offline) ----------
function isTeacherIntent(text) {
  return /^(0|teacher|teach|i (want|wish) to teach|become a teacher|i ?am a teacher|i'?m a teacher|tutor|start (my|a) (class|coaching|tuition))\b/i.test((text || "").trim());
}
function teacherPromptText() {
  return `👨‍🏫 Wonderful — you want to teach *with* Acharya!\n\n` +
         `You bring your students; Acharya teaches them one-on-one on WhatsApp in English & हिंदी, and you get a dashboard to manage them.\n\n` +
         `Tell me in *one message*: your *name*, your *subject*, and roughly *how many students* you have (or want to start with).`;
}
// Log a teacher onboarding request through the SAME course-request pipeline (admin alert + /admin table). No LMS change needed.
async function submitTeacher(waId, profile, info) {
  await requestCourse(`🎓 TEACHER ONBOARDING — ${info}`, profile.email || "", waId);
  profile.role = "teacher_pending";
  profile.teacher_info = info;
  profile.onboarding = "done";
  profile.onboarded = true;
  profile.greeted = true;
  saveProfile(waId, profile);
  return `🙏 Thank you! Your teacher request is in. *Deepak from TrigunAI* will reach out on this number within *1 working day* ` +
         `to set up your teacher account and your students' join link. 🪔`;
}
const COURSE_KW = [
  [/music|song|singer|audio/, "ai-music-factory"],
  [/video|film|reel|movie|youtube/, "ai-video-factory"],
  [/product manage|product manager|\bai ?pm\b|\bpm\b/, "ai-pm"],
  [/robot|physical ai|isaac|drone|reinforcement/, "physical-ai"],
  [/blender|unity/, "screen-game"],
  [/(vr|mr|xr)[^a-z]{0,12}game|immersive[^a-z]{0,12}game/, "vr-game"],
  [/\bvr\b|\bmr\b|\bxr\b|quest|headset|immersive|mixed reality/, "vr-mr-app"],
  [/\bgame\b/, "screen-game"],
  [/job|remote|\bswe\b|software eng|coding agent|leetcode|\bdsa\b|interview|hired/, "remote-swe"],
  [/machine learning|\bml\b|\bmaths?\b|neural|deep learning|gradient/, "ml-and-math"],
  [/agent|tool use|autonom|workflow|automation/, "agentic"],
];
function matchCourse(text) {
  const t = (text || "").toLowerCase();
  const n = t.match(/\b([1-9]|10)\b/);
  if (n) { const i = parseInt(n[1], 10) - 1; if (i >= 0 && i < COURSE_MENU.length) return COURSE_MENU[i][0]; }
  for (const [re, id] of COURSE_KW) if (re.test(t)) return id;
  return null;
}
function courseName(id) { const r = COURSE_MENU.find(([cid]) => cid === id); return r ? r[1] : id; }
function extractEmail(text) {
  const m = (text || "").match(/[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}/i);
  return m ? m[0].toLowerCase() : null;
}
// Sign the learner up on the LMS (same account they can later log into on the web) — server-to-server.
async function lmsSignup(email, course, waId, name) {
  const url = process.env.LMS_SIGNUP_URL, key = process.env.LMS_BRIDGE_KEY;
  if (!url || !key) { log("lmsSignup skipped — LMS_SIGNUP_URL / LMS_BRIDGE_KEY not set"); return; }
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "X-Bridge-Key": key, "Content-Type": "application/json" },
      body: JSON.stringify({ email, course, phone: waId, name: name || "" }),
    });
    log("lmsSignup", email, course, "->", r.status);
  } catch (e) { log("lmsSignup failed:", e.message); }
}

// ---------- per-number daily rate limit (bounds LLM cost / abuse on the open WhatsApp number) ----------
const RL_CAP = parseInt(process.env.RATE_LIMIT_PER_DAY || "60", 10);
function bumpRate(profile) {
  const today = new Date().toISOString().slice(0, 10);
  if (profile.rl_day !== today) { profile.rl_day = today; profile.rl_count = 0; }
  profile.rl_count = (profile.rl_count || 0) + 1;
  return profile.rl_count;
}
function rateCapText() {
  return `🪔 You've reached today's free message limit on WhatsApp. Let's pick this up tomorrow — ` +
         `or keep going right now, unlimited, on the web 👉 acharya.trigunai.com`;
}

// One openclaw agent turn -> Acharya's reply text (or null).
async function runAcharyaTurn(waId, message) {
  const stdout = await runOpenClaw([
    "agent", "--to", `+${waId}`, "--message", message, "--json", "--timeout", "120",
  ]);
  if (!stdout) return null;
  try {
    const j = JSON.parse(stdout);
    return (j.result?.payloads || []).map(p => p.text).filter(Boolean).join("\n").trim() || null;
  } catch { return stdout.trim() || null; }
}

// One Acharya teaching turn for a student (profile-injected, per-student session).
async function askAcharya(waId, text) {
  const profile = loadProfile(waId);

  // Cold-inbound onboarding: a brand-new number is introduced to TrigunAI and PICKS a course from the
  // menu before any teaching (instead of being silently dropped into agentic). Existing students have
  // greeted=true and skip this whole block. The menu + parsing are pure code — no LLM cost.
  if (!profile.onboarded && !profile.greeted) {
    const st = profile.onboarding;
    // Step 1 — intro + course menu (or route a teacher straight to the teacher-request flow).
    if (!["awaiting_course", "awaiting_email", "awaiting_custom_topic", "awaiting_teacher_info"].includes(st)) {
      if (isTeacherIntent(text)) {
        profile.onboarding = "awaiting_teacher_info";
        saveProfile(waId, profile);
        return teacherPromptText();
      }
      profile.onboarding = "awaiting_course";
      saveProfile(waId, profile);                 // greeted stays false until they finish onboarding
      return courseMenuText();
    }
    // Step 2 — pick a course (-> email signup) OR ask for something we don't offer (-> "I'll build it").
    if (st === "awaiting_course") {
      if (isTeacherIntent(text)) {
        profile.onboarding = "awaiting_teacher_info";
        saveProfile(waId, profile);
        return teacherPromptText();
      }
      const chosen = matchCourse(text);
      if (chosen) {
        profile.course = chosen;
        profile.current_module = 2;
        profile.onboarding = "awaiting_email";
        saveProfile(waId, profile);
        return `Great choice — *${courseName(chosen)}*! 🎓\n\n` +
               `One last step to save your progress: *what's your email?*\n` +
               `(Same account you can log in with on the web — acharya.trigunai.com)`;
      }
      // not one of the 10 courses → custom-request path
      const t = text.trim();
      if (/^(11|others?|something( else)?|custom|none|not (here|listed))\b/i.test(t) || t.length < 3) {
        profile.onboarding = "awaiting_custom_topic";
        saveProfile(waId, profile);
        return customPromptText();
      }
      return await submitCustom(waId, profile, t);   // they typed a real topic → log the request
    }
    // Step 2b — they described their custom topic.
    if (st === "awaiting_custom_topic") {
      const t = text.trim();
      if (t.length < 3) return `Just type the topic you'd like to learn 🙂 (e.g. "govt exam prep", "cybersecurity").`;
      return await submitCustom(waId, profile, t);
    }
    // Step 2c — a prospective TEACHER described their class → log the onboarding request (Deepak takes it offline).
    if (st === "awaiting_teacher_info") {
      const t = text.trim();
      if (t.length < 3) return `Just tell me your *name, subject, and how many students* 🙂 (e.g. "Ravi, Class 10 Maths, 20 students").`;
      return await submitTeacher(waId, profile, t);
    }
    // Step 3 — capture email, create the LMS account, then start teaching the chosen course.
    if (st === "awaiting_email") {
      const email = extractEmail(text);
      if (!email) {
        return `Hmm, that doesn't look like an email 🤔 — please send a valid one (e.g. *you@gmail.com*).`;
      }
      await lmsSignup(email, profile.course, waId, profile.name || "");
      profile.email = email;
      profile.onboarding = "done";
      profile.onboarded = true;
      profile.greeted = true;
      saveProfile(waId, profile);
      const welcome = `[The student just signed up (email captured) and chose this course. Open EXACTLY per ` +
        `your skill: a warm one-line welcome to their COURSE (named in the course context) + ONE line asking ` +
        `why they want to learn it — no syllabus, no jumping ahead.]\n` + profilePreamble(profile);
      return await runAcharyaTurn(waId, welcome + text);
    }
  }

  // Course switch (onboarded learners): "menu" / "switch" / "change course" → re-pick from the menu.
  const tt = (text || "").trim();
  if (profile.onboarding === "switching") {
    if (/^(cancel|stay|back|no)\b/i.test(tt)) {
      profile.onboarding = "done"; saveProfile(waId, profile);
      return `👍 Staying on *${courseName(profile.course)}*. Let's continue!`;
    }
    const chosen = matchCourse(tt);
    if (chosen) {
      profile.course = chosen; profile.current_module = 2; profile.onboarding = "done";
      saveProfile(waId, profile);
      const welcome = `[The student just SWITCHED to this course. Open with a warm one-line welcome to the NEW ` +
        `course (named in the course context) + ONE line asking what they want from it — no syllabus, no recap ` +
        `of the old course.]\n` + profilePreamble(profile);
      return await runAcharyaTurn(waId, welcome + text);
    }
    if (tt.length >= 3) return await submitCustom(waId, profile, tt);   // they asked for a topic we don't have yet
    return `Reply with a *number 1–10* to switch, or *cancel* to stay on ${courseName(profile.course)}.`;
  }
  if (/^(menu|switch|switch course|change course|change my course|courses|change topic|other course)\s*[?.!]*$/i.test(tt)) {
    profile.onboarding = "switching"; saveProfile(waId, profile);
    return switchMenuText(courseName(profile.course));
  }

  // Normal teaching turn.
  let preamble = profilePreamble(profile);
  if (!profile.greeted) {   // safety net for any legacy profile that predates onboarding
    preamble = `[FIRST CONTACT — student's FIRST message ever. Do NOT assume who they are. Open EXACTLY per ` +
      `your skill: a warm one-line welcome to their COURSE (named in the course context) + ONE line asking ` +
      `why they want to learn it — nothing before it, no syllabus, no jumping ahead.]\n` + preamble;
    profile.greeted = true; saveProfile(waId, profile);
  }
  return await runAcharyaTurn(waId, preamble + text);
}

// Background: merge what we learned about this student into their profile (cheap model proposes
// soft fields + which concepts were *discussed*; the CODE owns mastery + SRS so the chatty model
// can't invent concept keys or rubber-stamp "solid" without a graded recall).
async function updateProfile(waId, studentMsg, acharyaReply) {
  const cur = loadProfile(waId);
  const bank = courseBank(cur.course);
  const validKeys = new Set(Object.keys(bank.concepts || {}));
  const orderList = (bank.order || []).join(", ") || "(none defined)";

  // Grading context: only the model judges the *semantic* match; the box/due math is done in code.
  const pending = cur.pending_recall || "";
  let gradeBlock = "";
  if (pending && bank.concepts[pending]) gradeBlock =
    `\nRECALL GRADING: the student was just asked to recall the concept "${pending}". ` +
    `Expected answer gist: "${bank.concepts[pending].answer}". ` +
    `Add a top-level "recall_verdict": "correct" if their reply matches the gist unaided, else "wrong".\n`;

  const prompt =
    `You maintain a learner profile for the course "${bank.name}". Update it from the new exchange. ` +
    `Return ONLY one JSON object, no prose.\n` +
    `CURRENT PROFILE (JSON):\n${JSON.stringify(cur)}\n` + gradeBlock + `\n` +
    `NEW EXCHANGE:\nSTUDENT: ${studentMsg}\nACHARYA: ${acharyaReply}\n\n` +
    `RULES (follow exactly):\n` +
    `- "concepts": keys MUST come ONLY from this exact list — never invent or rename keys: ${orderList}.\n` +
    `  Mark a concept "shaky" ONLY when it was actually taught/discussed in THIS exchange. ` +
    `Do NOT mark anything "solid" — mastery is decided elsewhere. Leave untouched concepts as they are.\n` +
    `- Keep every existing field. Merge in name/byoa_goal/level only if the student revealed them.\n` +
    `- Append any genuine NEW misconception. Set last_win on a clear win. Bump "streak" by 1 if the student engaged.\n` +
    `- Personal context when revealed: hobbies/likes → "interests"; job/field/domain → "background"; ` +
    `how they like to learn → "style".\n` +
    (gradeBlock ? `- Include "recall_verdict" as instructed above.\n` : ``) +
    `JSON only.`;

  const out = await runOpenClaw(["infer", "model", "run", "--model", EXTRACT_MODEL, "--prompt", prompt], 60000);
  if (!out) { log("profile extract no-output:", waId); return; }
  let next;
  try { next = JSON.parse(out.slice(out.indexOf("{"), out.lastIndexOf("}") + 1)); }
  catch { log("profile extract parse failed:", waId); return; }
  if (!next || typeof next !== "object") return;

  // Start from the model's soft-field merge, but CODE owns concepts + srs (don't trust the model with them).
  const merged = { ...cur, ...next };
  const verdict = next.recall_verdict;
  delete merged.recall_verdict;                                 // not a profile field

  // 1) Mastery: start from trusted prior; overlay model's marks, whitelisted to the bank, never granting solid.
  const concepts = { ...(cur.concepts || {}) };
  for (const [k, v] of Object.entries(next.concepts || {})) {
    if (!validKeys.has(k)) continue;                            // drop invented / cross-course keys
    if (concepts[k] === "solid") continue;                      // never downgrade an earned solid
    if (v === "solid") concepts[k] = "shaky";                   // model is not allowed to grant solid
    else if (v === "shaky" || v === "not_seen") concepts[k] = v;
  }
  merged.concepts = concepts;

  // 2) SRS owned by code: seed an item the first time a concept becomes shaky/solid.
  const srs = Array.isArray(cur.srs) ? cur.srs.map(s => ({ ...s })) : [];
  const tracked = new Set(srs.map(s => s.concept));
  for (const [k, v] of Object.entries(concepts))
    if ((v === "shaky" || v === "solid") && !tracked.has(k)) { srs.push({ concept: k, box: 0, due: DUE(1) }); tracked.add(k); }

  // 3) Deterministic recall grading — the ONLY path that grants "solid".
  if (pending && verdict) {
    const item = srs.find(s => s.concept === pending);
    if (verdict === "correct") {
      concepts[pending] = "solid";
      if (item) { item.box = Math.min((item.box || 0) + 1, SRS_INTERVALS.length - 1); item.due = DUE(SRS_INTERVALS[item.box]); }
    } else {
      concepts[pending] = "shaky";
      if (item) { item.box = 0; item.due = DUE(SRS_INTERVALS[0]); }
    }
    merged.pending_recall = "";
  }
  merged.srs = srs;

  saveProfile(waId, merged);
  logEvent({ type: "profile", student: waId, course: cur.course,
             concepts, recall: pending ? { concept: pending, verdict: verdict || null } : null });
  log("profile updated:", waId);
}

// ---------- Web chat (LMS) ----------
// Verify an LMS-issued token => the student's email, or null. Token = base64url("email|expiryMs|hmac").
function verifyToken(token) {
  try {
    const parts = Buffer.from(token, "base64url").toString("utf8").split("|");
    let email, course = "agentic", exp, sig;
    if (parts.length === 4) [email, course, exp, sig] = parts;       // email|course|exp|sig
    else [email, exp, sig] = parts;                                   // legacy email|exp|sig
    if (!email || !exp || !sig || Date.now() > Number(exp)) return null;
    const signed = parts.length === 4 ? `${email}|${course}|${exp}` : `${email}|${exp}`;
    const expect = crypto.createHmac("sha256", CHAT_SECRET).update(signed).digest("hex");
    return crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expect)) ? { email, course } : null;
  } catch { return null; }
}

// --- Identity link (sync web<->WhatsApp by mapping email -> phone, one shared profile) ---
const IDMAP = `${STUDENTS_DIR}/_identity.json`;
const loadIdentity = () => { try { return JSON.parse(fs.readFileSync(IDMAP, "utf8")); } catch { return {}; } };
const saveIdentity = (m) => fs.writeFileSync(IDMAP, JSON.stringify(m, null, 2));
const sanitizeEmail = (e) => "web_" + e.replace(/[^a-z0-9._@-]/gi, "_");

// Find a WhatsApp number in a message (India-friendly). Returns digits like 919135255107 or null.
function detectPhone(text) {
  for (let d of (text.match(/\+?\d[\d\s-]{8,15}\d/g) || []).map(s => s.replace(/\D/g, ""))) {
    if (d.length === 10) d = "91" + d;
    if (d.length >= 11 && d.length <= 13) return d;
  }
  return null;
}
// Merge the web profile into the phone (canonical) profile — keep the best of each.
function mergeProfiles(phoneKey, webKey) {
  const a = loadProfile(phoneKey), b = loadProfile(webKey), rank = { not_seen: 0, shaky: 1, solid: 2 };
  const concepts = { ...(b.concepts || {}) };
  for (const [k, v] of Object.entries(a.concepts || {}))
    if ((rank[v] ?? 0) >= (rank[concepts[k]] ?? -1)) concepts[k] = v;
  saveProfile(phoneKey, {
    ...b, ...a,
    byoa_goal: a.byoa_goal || b.byoa_goal, level: a.level || b.level, name: a.name || b.name,
    background: a.background || b.background, style: a.style || b.style,
    current_module: Math.max(a.current_module || 2, b.current_module || 2),
    streak: Math.max(a.streak || 0, b.streak || 0), last_win: a.last_win || b.last_win, concepts,
    interests: [...new Set([...(a.interests || []), ...(b.interests || [])])],
    misconceptions: [...new Set([...(a.misconceptions || []), ...(b.misconceptions || [])])],
    srs: (a.srs && a.srs.length) ? a.srs : (b.srs || []), greeted: true,
  });
  try { fs.unlinkSync(`${STUDENTS_DIR}/${webKey}.json`); } catch {}
}

// Web-chat turn — same Acharya. Resolves to the SHARED phone profile once linked; else web_<email>
// and asks for the WhatsApp number once to sync.
async function askAcharyaWeb(email, course, text) {
  const idmap = loadIdentity();
  let key, askPhone = false;
  if (idmap[email]) {
    key = idmap[email];                                  // linked -> shared profile with WhatsApp
  } else {
    const phone = detectPhone(text);
    if (phone) {                                          // student gave their number -> link + merge
      idmap[email] = phone; saveIdentity(idmap);
      mergeProfiles(phone, sanitizeEmail(email));
      key = phone; log("linked", email, "->", phone);
    } else {
      key = sanitizeEmail(email);
      const p = loadProfile(key);
      if (!p.asked_phone) { askPhone = true; p.asked_phone = true; saveProfile(key, p); }
    }
  }
  const profile = loadProfile(key);
  if (course && profile.course !== course) { profile.course = course; saveProfile(key, profile); }  // LMS course wins
  let preamble = profilePreamble(profile);
  if (!profile.greeted) {
    preamble = `[FIRST CONTACT — first message. Open per your skill: a warm welcome to their COURSE (named ` +
      `in the course context) + ONE line asking why they want to learn it.]\n` + preamble;
    profile.greeted = true; saveProfile(key, profile);
  }
  if (askPhone) preamble = `[SYNC: this is the WEB chat. Warmly ask the student for their WhatsApp number ` +
    `ONCE so progress follows them across WhatsApp and here — e.g. "Quick — what's your WhatsApp number? ` +
    `So your progress syncs across WhatsApp and the web." Then carry on.]\n` + preamble;
  const stdout = await runOpenClaw(["agent", "--session-key", "web:" + key, "--message", preamble + text,
    "--json", "--timeout", "120"]);
  let reply = null;
  if (stdout) { try { reply = (JSON.parse(stdout).result?.payloads || []).map(p => p.text).filter(Boolean).join("\n").trim() || null; } catch { reply = stdout.trim() || null; } }
  if (reply) {
    logEvent({ type: "turn", channel: "web", student: key, course: profile.course, student_msg: text, tutor_msg: reply });
    updateProfile(key, text, reply);
  }
  return reply;
}

// ---------- Graph API send ----------
async function sendWhatsApp(toNumber, body) {
  const url = `https://graph.facebook.com/${GRAPH_VERSION}/${PHONE_NUMBER_ID}/messages`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${META_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to: toNumber, type: "text", text: { body: body.slice(0, 4096) } }),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok) log("graph send failed:", res.status, JSON.stringify(j));
  else log("sent ->", toNumber, j.messages?.[0]?.id || "");
}

// Show the WhatsApp "typing…" bubble (also marks the message read) while we generate the reply.
// Lasts up to ~25s or until our reply is sent.
async function sendTyping(messageId) {
  try {
    await fetch(`https://graph.facebook.com/${GRAPH_VERSION}/${PHONE_NUMBER_ID}/messages`, {
      method: "POST",
      headers: { Authorization: `Bearer ${META_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ messaging_product: "whatsapp", status: "read",
        message_id: messageId, typing_indicator: { type: "text" } }),
    });
  } catch { /* best-effort */ }
}

function readBody(req) {
  return new Promise((resolve) => { let d = ""; req.on("data", c => (d += c)); req.on("end", () => resolve(d)); });
}

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, "http://x");

  if (req.method === "GET" && u.pathname === "/webhook") {
    const token = u.searchParams.get("hub.verify_token");
    const challenge = u.searchParams.get("hub.challenge");
    if (u.searchParams.get("hub.mode") === "subscribe" && token === VERIFY_TOKEN) {
      log("webhook verified"); res.writeHead(200); return res.end(challenge);
    }
    res.writeHead(403); return res.end("forbidden");
  }

  if (req.method === "POST" && u.pathname === "/webhook") {
    res.writeHead(200); res.end("ok");   // ack Meta immediately
    try {
      const data = JSON.parse(await readBody(req));
      for (const entry of data.entry || [])
        for (const ch of entry.changes || []) {
          // Delivery receipts: sent -> delivered -> read, or failed with a reason.
          for (const st of ch.value?.statuses || [])
            log("status:", st.status, st.recipient_id, st.errors?.[0]?.title ? `(FAILED: ${st.errors[0].title})` : "");
          for (const msg of ch.value?.messages || []) {
            if (msg.type !== "text") continue;
            const from = msg.from, text = msg.text?.body || "";
            if (msg.id) await sendTyping(msg.id);   // "typing…" while Acharya/Sutradhaar thinks
            const isAdmin = ADMIN_NUMBERS.includes(from);
            log("inbound <-", from, isAdmin ? "[ADMIN]" : "", JSON.stringify(text).slice(0, 80));
            if (isAdmin) {
              const reply = await askAdmin(from, text);          // Sutradhaar — no profile
              await sendWhatsApp(from, reply || "🛠️ hit a snag — resend that.");
            } else {
              // Per-number daily cap — counted BEFORE any LLM call so abuse can't run up cost.
              const rp = loadProfile(from);
              const n = bumpRate(rp); saveProfile(from, rp);
              if (n > RL_CAP) {
                log("rate-limited", from, `${n}/${RL_CAP}`);
                if (n <= RL_CAP + 2) await sendWhatsApp(from, rateCapText());  // a couple of notices, then go quiet
                continue;                                          // no LLM, skip to next message
              }
              const reply = await askAcharya(from, text);        // Acharya — with Learner Profile
              await sendWhatsApp(from, reply || "🪔 one sec — I hit a snag, please resend that.");
              if (reply) {
                logEvent({ type: "turn", channel: "whatsapp", student: from,
                           course: loadProfile(from).course, student_msg: text, tutor_msg: reply });
                updateProfile(from, text, reply);                // background, don't await
              }
            }
          }
        }
    } catch (e) { log("inbound parse error:", e.message); }
    return;
  }

  // --- Web chat (served behind Caddy at gurukul.trigunai.com/chat) ---
  if (req.method === "GET" && u.pathname === "/chat") {
    try { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(fs.readFileSync(`${HOME}/.openclaw/gurukul/chat.html`, "utf8")); }
    catch { res.writeHead(500); return res.end("chat unavailable"); }
  }
  if (req.method === "GET" && u.pathname === "/chat/logo.png") {
    try { res.writeHead(200, { "Content-Type": "image/png" }); return res.end(fs.readFileSync(`${HOME}/gurukul_icon.png`)); }
    catch { res.writeHead(404); return res.end(); }
  }
  if (req.method === "POST" && u.pathname === "/chat/api") {
    const J = (code, obj) => { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); };
    try {
      const { token, message } = JSON.parse(await readBody(req));
      const v = verifyToken(token);
      if (!v) return J(401, { reply: "⚠️ Your session expired — reopen the chat from the LMS." });
      if (!message) return J(200, { reply: "" });
      log("web <-", v.email, `[${v.course}]`, JSON.stringify(message).slice(0, 50));
      const reply = await askAcharyaWeb(v.email, v.course, message);
      return J(200, { reply: reply || "🪔 one sec — try that again." });
    } catch { return J(200, { reply: "Connection hiccup — please resend." }); }
  }

  if (u.pathname === "/health") { res.writeHead(200); return res.end("ok"); }
  res.writeHead(404); res.end("not found");
});

sanitizeAllProfiles();   // one-time cleanup: strip cross-course concept/SRS pollution on boot
server.listen(Number(PORT), "127.0.0.1", () =>
  log(`WA cloud bridge (profiles on, grounded mastery + SRS + event log) listening on 127.0.0.1:${PORT}`));
