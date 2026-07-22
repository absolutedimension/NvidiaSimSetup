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
             goal: "", goal_deadline: "", goal_confirmed: false,   // Goal OS: articulated + student-confirmed goal
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
// Compute revise-mode signals from a student's profile.
// Triggers when shaky ratio > 0.6 OR overdue SRS items > 10 — i.e. student is drowning in backlog.
function computeReviseSignals(p) {
  const concepts = p.concepts || {};
  const shaky = Object.entries(concepts).filter(([, v]) => v === "shaky").map(([k]) => k);
  const solid = Object.entries(concepts).filter(([, v]) => v === "solid").map(([k]) => k);
  const total = shaky.length + solid.length;
  const shakyRatio = total > 0 ? shaky.length / total : 0;
  const todayIso = new Date().toISOString().slice(0, 10);
  const overdue = (p.srs || []).filter(item => {
    const due = (item.due || "").slice(0, 10);
    return due && due <= todayIso;
  });
  const shouldRevise = shakyRatio > 0.6 || overdue.length > 10;
  // pick top-3 concepts to focus on (shaky first, then earliest-due overdue not already listed)
  const focus = [
    ...shaky.slice(0, 3),
    ...overdue.map(x => x.concept).filter(c => c && !shaky.includes(c)),
  ].slice(0, 3);
  return { shaky, solid, shakyRatio, overdueCount: overdue.length, shouldRevise, focus };
}

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

  const sig = computeReviseSignals(p);
  const toneBlock =
    `[TONE — non-negotiable]\n` +
    `You are the TEACHER. The student is the LEARNER. NEVER address the student as "sir", "madam", "ji sir", or any honorific that treats them as your superior. Use "aap" (respectful you) or their first name, nothing more. If a phrase in these instructions contains "sir", drop that word when you speak. You are warm, patient, and firm — like a caring guru — not deferential.\n---\n`;

  const reviseBlock = sig.shouldRevise
    ? `[REVISE MODE — active because student has too many weak concepts]\n` +
      `stats: shaky=${sig.shaky.length}, solid=${sig.solid.length}, overdue_srs=${sig.overdueCount}\n` +
      `focus these first: ${sig.focus.join(", ") || "(none tracked yet)"}\n` +
      `RULE: DO NOT teach new material. If the student asks a new-concept question, GENTLY interrupt:\n` +
      `  "Ek moment — dekha maine aapke ${sig.shaky.length} concepts abhi shaky hain aur ${sig.overdueCount} revision items overdue hain. Aage badhne se pehle inhein pakka karte hain — 10 minute lagega. Chalein?"\n` +
      `If student explicitly insists on the new question, answer briefly (2-3 lines) then IMMEDIATELY loop back:\n` +
      `  "Chalo yeh answer ho gaya. Ab wapas revise mode par — ${sig.focus[0] || "top shaky concept"} se shuru karte hain."\n` +
      `Revise conversationally — recall question -> student answers -> you evaluate & correct. Never call the student "sir".\n---\n`
    : "";

  const imaginationBlock =
    `[IMAGINATION MODE — always available for abstract concepts]\n` +
    `Abstract concepts benefit from visualization (RAG, memory, orchestrator, react, self_correction, guardrails, decomposition, evaluation, etc.).\n` +
    `You have TWO delivery options for imagination:\n` +
    `  A) Text scenario (default — always safe): tell a short vivid story in Hindi/English that illustrates the concept.\n` +
    `     e.g. "Imagine kijiye: ek library hai jismein 10 lakh books hain. RAG ka kaam yeh hai ki jab koi sawaal aaye, pehle woh library se relevant book uthata hai, phir uss book ke content par based answer banata hai."\n` +
    `  B) Generated image (use SPARINGLY — max 1 per turn, only when a diagram truly clarifies). To trigger:\n` +
    `     Output this marker on its own line, exactly: [GENERATE_IMAGE: <one clear English sentence describing a minimalist diagram>]\n` +
    `     Keep the description under 200 chars, blueprint / line-art style, single concept per image.\n` +
    `     Example: [GENERATE_IMAGE: minimalist blueprint diagram of RAG — library shelf on left with books, document being retrieved and handed to a robot on right, thin line art, no text labels]\n` +
    `     The system will render the PNG and send it as a separate WhatsApp message. Your text reply continues normally around the marker; the marker itself is stripped from the text.\n` +
    `When a student asks about an abstract concept, OFFER first: "Kya main story se samjhaun ya diagram bhejun?" — let them pick. Never call the student "sir".\n---\n`;

  if (!known) return courseLine + toneBlock + reviseBlock + imaginationBlock + `---\n`;
  return courseLine + toneBlock + reviseBlock + imaginationBlock +
    `[STUDENT PROFILE — use silently to personalize; do NOT echo this back]\n` +
    `name: ${p.name || "?"} | byoa_goal: ${p.byoa_goal || "?"} | level: ${p.level || "?"}\n` +
    `goal_os: ${p.goal_confirmed
        ? `LOCKED → "${p.goal || "?"}"${p.goal_deadline ? ` (target: ${p.goal_deadline})` : ""} — open by tying today's ONE focused step to THIS goal`
        : `NOT SET → this turn you MUST run the Goal-OS gate FIRST: draft their goal from byoa_goal + course + current step, have them confirm it, before teaching (see gurukul-tutor skill)`}\n` +
    `mastery: ${JSON.stringify(p.concepts || {})}\n` +
    `misconceptions: ${(p.misconceptions || []).join("; ") || "none"} | streak: ${p.streak} | last_win: ${p.last_win || "-"}\n` +
    `interests: ${(p.interests || []).join(", ") || "?"} | background: ${p.background || "?"} | style: ${p.style || "?"}\n` +
    `(Use interests/background in examples & analogies. style = how they like to learn.)\n` +
    `---\n`;
}

// ---------- Image generation + WhatsApp media send (Acharya visualization mode) ----------
// Azure gpt-image-1.5 returns base64 PNG. We upload to Meta media API to get a media_id, then
// send an image message referencing that id. Async: never blocks the text reply path.
async function generateAcharyaImage(prompt) {
  const endpoint = process.env.AZURE_IMAGE_ENDPOINT;
  const key      = process.env.AZURE_IMAGE_KEY;
  const dep      = process.env.AZURE_IMAGE_DEPLOYMENT || "gpt-image-1.5";
  const ver      = process.env.AZURE_IMAGE_API_VERSION || "2025-04-01-preview";
  if (!endpoint || !key) return null;
  try {
    const r = await fetch(`${endpoint}/openai/deployments/${dep}/images/generations?api-version=${ver}`, {
      method: "POST",
      headers: { "api-key": key, "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt.slice(0, 900), n: 1, size: "1024x1024" }),
      signal: AbortSignal.timeout(30000),
    });
    if (!r.ok) { log("image-gen HTTP", r.status); return null; }
    const j = await r.json();
    const b64 = j.data?.[0]?.b64_json;
    return b64 || null;
  } catch (e) { log("image-gen error:", e.message); return null; }
}

async function uploadPngToMeta(b64Png) {
  const TOKEN = process.env.META_TOKEN;
  const PID   = process.env.PHONE_NUMBER_ID;
  const GV    = process.env.GRAPH_VERSION || "v21.0";
  if (!TOKEN || !PID || !b64Png) return null;
  // Build multipart body manually (no external form-data lib)
  const boundary = "----acharya" + Math.random().toString(36).slice(2, 10);
  const bin = Buffer.from(b64Png, "base64");
  const head = Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="messaging_product"\r\n\r\nwhatsapp\r\n` +
    `--${boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\nimage/png\r\n` +
    `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="acharya.png"\r\nContent-Type: image/png\r\n\r\n`,
    "utf8"
  );
  const tail = Buffer.from(`\r\n--${boundary}--\r\n`, "utf8");
  const body = Buffer.concat([head, bin, tail]);
  try {
    const r = await fetch(`https://graph.facebook.com/${GV}/${PID}/media`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        "Content-Type": `multipart/form-data; boundary=${boundary}`,
        "Content-Length": String(body.length),
      },
      body,
      signal: AbortSignal.timeout(30000),
    });
    if (!r.ok) { log("meta-media HTTP", r.status, (await r.text()).slice(0, 200)); return null; }
    const j = await r.json();
    return j.id || null;
  } catch (e) { log("meta-media error:", e.message); return null; }
}

async function sendWhatsAppImage(to, mediaId, caption = "") {
  const TOKEN = process.env.META_TOKEN;
  const PID   = process.env.PHONE_NUMBER_ID;
  const GV    = process.env.GRAPH_VERSION || "v21.0";
  const payload = {
    messaging_product: "whatsapp",
    to,
    type: "image",
    image: { id: mediaId, ...(caption ? { caption: caption.slice(0, 1024) } : {}) },
  };
  try {
    const r = await fetch(`https://graph.facebook.com/${GV}/${PID}/messages`, {
      method: "POST",
      headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15000),
    });
    return r.ok;
  } catch (e) { log("send-image error:", e.message); return false; }
}

// If Acharya's reply contains a [GENERATE_IMAGE: ...] marker, fire the image pipeline
// asynchronously (never blocks the text send). Returns the cleaned text with the marker removed.
async function maybeFireImageSideChannel(waId, replyText) {
  const m = replyText && replyText.match(/\[GENERATE_IMAGE:\s*([^\]\n]{5,900})\]/);
  if (!m) return replyText;
  const imgPrompt = m[1].trim();
  const cleaned = replyText.replace(m[0], "").replace(/\n{3,}/g, "\n\n").trim();
  // Async — do not await; the text goes out immediately, image follows.
  (async () => {
    log("image-gen: start", waId, imgPrompt.slice(0, 60));
    const b64 = await generateAcharyaImage(imgPrompt);
    if (!b64) { log("image-gen: failed to produce PNG"); return; }
    const mediaId = await uploadPngToMeta(b64);
    if (!mediaId) { log("image-gen: upload failed"); return; }
    const ok = await sendWhatsAppImage(waId, mediaId);
    log("image-gen:", ok ? "sent ✅" : "send failed", waId);
  })();
  return cleaned;
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

// ---------- teacher onboarding (Stage 1: WhatsApp-native question flow via onboarding_bot.py) ----------
// If sender is a teacher currently in the onboarding queue, forward the message to onboarding_bot.py
// on 127.0.0.1:7865 and return its {reply, stage} so this bridge can send the reply. Bot down or
// teacher-not-in-queue → returns null → falls through to the existing admin / Acharya paths (safe).
const TEACHER_ONBOARDING_QUEUE = `${HOME}/teacher_gtm/onboarding_queue.json`;
const ONBOARDING_ACTIVE_STAGES = new Set([
  "template_sent", "template_delivered", "template_read",
  "started", "collecting_details", "web_upload_pending",
]);
async function maybeHandleTeacherOnboarding(waNumber, text, buttonId) {
  let queue;
  try { queue = JSON.parse(fs.readFileSync(TEACHER_ONBOARDING_QUEUE, "utf8")); }
  catch { return null; }  // queue file missing — feature is dark, don't touch existing students
  const t = (queue.teachers || []).find(x => x.wa_number === waNumber);
  if (!t || !ONBOARDING_ACTIVE_STAGES.has(t.stage)) return null;
  try {
    const r = await fetch("http://127.0.0.1:7865/wa_incoming", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ wa_number: waNumber, text: text || "", button_id: buttonId || null }),
      signal: AbortSignal.timeout(15000),
    });
    return await r.json();
  } catch (e) {
    log("onboarding bot unreachable:", e.message, "— falling through to Acharya");
    return null;
  }
}

// One openclaw agent turn -> Acharya's reply text (or null).
// Post-processes the reply for [GENERATE_IMAGE: ...] markers → fires image side-channel + strips marker.
async function runAcharyaTurn(waId, message) {
  const stdout = await runOpenClaw([
    "agent", "--to", `+${waId}`, "--message", message, "--json", "--timeout", "120",
  ]);
  if (!stdout) return null;
  let reply = null;
  try {
    const j = JSON.parse(stdout);
    reply = (j.result?.payloads || []).map(p => p.text).filter(Boolean).join("\n").trim() || null;
  } catch { reply = stdout.trim() || null; }
  return reply ? await maybeFireImageSideChannel(waId, reply) : reply;
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
    `- Goal OS: if in THIS exchange the student CONFIRMED a goal Acharya articulated (e.g. "haan sahi hai", "yes", "perfect", "theek hai"), set top-level "goal" to that one-line goal, "goal_confirmed": true, and "goal_deadline" to any timeframe/date they gave (else ""). If Acharya proposed a goal but the student only tweaked it or hasn't agreed yet, set "goal" to the latest draft and keep "goal_confirmed": false. NEVER invent a goal the student did not engage with; if goal_confirmed is already true, keep it true.\n` +
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
  // Goal OS: a locked goal is permanent — never let a later extraction wipe/downgrade it.
  if (cur.goal_confirmed) {
    merged.goal_confirmed = true;
    merged.goal = cur.goal || merged.goal;
    merged.goal_deadline = cur.goal_deadline || merged.goal_deadline;
  }
  // Goal OS: deterministic confirmation backstop — LLM extraction of this flag is unreliable, so
  // when a goal is drafted-but-unconfirmed and the student affirms, lock it in code (not via the model).
  if (merged.goal && !merged.goal_confirmed &&
      /(^|\b)(haa+n?|ha+|yes+|yep|yup|sahi|bilkul|th?eek|th?ik|perfect|correct|confirm|lock|done|ok(ay)?|great|sahi hai|ji haan)(\b|$)/i.test((studentMsg || "").trim())) {
    merged.goal_confirmed = true;
  }
  // capture a rough deadline if the student mentioned one and none is stored yet
  if (merged.goal_confirmed && !merged.goal_deadline) {
    const dl = (studentMsg || "").match(/((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*'?\d{2,4}|20\d\d|\d+\s*(?:months?|weeks?|days?|mahin[ae]|hafte|saal|years?))/i);
    if (dl) merged.goal_deadline = dl[0].trim();
  }

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
  // Web path image handling: strip [GENERATE_IMAGE:] marker. If profile is linked to a WhatsApp
  // number (key is all digits), fire the image to WhatsApp; if key is an email (unlinked), just strip.
  if (reply) {
    const isPhone = /^\d{10,15}$/.test(key);
    if (isPhone) {
      reply = await maybeFireImageSideChannel(key, reply);
    } else {
      reply = reply.replace(/\[GENERATE_IMAGE:\s*[^\]\n]{5,900}\]/g, "").replace(/\n{3,}/g, "\n\n").trim();
    }
  }
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

/* ==================== WhatsApp native assessment (tap-button quiz) ====================
   Trigger: a student (or a demo number) texts "quiz" / "quiz <subject>". Acharya enters
   assessment mode and sends MCQ/True-False questions as native WhatsApp reply buttons.
   Taps are graded, next is sent, then a score + weak-topics report. State lives in
   profile.wa_quiz and NEVER touches the real learning mastery (safe for demos). */
const WA_QUIZ = {
 "neet-biology":{name:"NEET Biology",questions:[
   {topic:"Cell organelles",q:"Powerhouse of the cell?",opts:["Mitochondria","Ribosome","Nucleus"],correct:0},
   {topic:"Genetics",q:"In DNA, Adenine (A) pairs with which base?",opts:["Thymine","Guanine","Cytosine"],correct:0},
   {topic:"Chromosomes",q:"Chromosomes in a normal human (diploid) cell?",opts:["46","23","64"],correct:0},
   {topic:"Transport",q:"Osmosis is the movement of ___ across a membrane.",opts:["Water","Salt","Protein"],correct:0}]},
 "jee-physics":{name:"JEE Physics",questions:[
   {topic:"Newton's 2nd law",q:"Newton's second law: F = ?",opts:["m × a","m × v","m ÷ a"],correct:0},
   {topic:"Inertia",q:"An object at uniform velocity has zero net force on it.",opts:["True","False"],correct:0},
   {topic:"Units",q:"SI unit of Force?",opts:["Newton","Joule","Watt"],correct:0},
   {topic:"Force calc",q:"A 2 kg object at 5 m/s². Force = ?",opts:["10 N","7 N","2.5 N"],correct:0}]},
 "class10":{name:"Class 10 Science",questions:[
   {topic:"Chemistry",q:"Chemical formula of water?",opts:["H₂O","CO₂","O₂"],correct:0},
   {topic:"Acids",q:"An acid has pH less than 7.",opts:["True","False"],correct:0},
   {topic:"Math (Pythagoras)",q:"Right triangle sides 3 and 4. Hypotenuse = ?",opts:["5","6","7"],correct:0},
   {topic:"Biology",q:"Plants make food using sunlight in the process of?",opts:["Photosynthesis","Respiration","Digestion"],correct:0}]},
 "class12":{name:"Class 12 Board",questions:[
   {topic:"Ohm's Law",q:"Ohm's law: Voltage (V) = ?",opts:["I × R","I ÷ R","I + R"],correct:0},
   {topic:"Series circuits",q:"In a series circuit, current is the same at every point.",opts:["True","False"],correct:0},
   {topic:"Units",q:"SI unit of electric current?",opts:["Ampere","Volt","Ohm"],correct:0},
   {topic:"Current calc",q:"5 V across 10 Ω resistance. Current = ?",opts:["0.5 A","2 A","50 A"],correct:0}]},
 "commerce":{name:"Commerce",questions:[
   {topic:"Accounting equation",q:"Assets = Liabilities + ?",opts:["Capital","Income","Expense"],correct:0},
   {topic:"Journal vs Ledger",q:"The Journal is called the 'book of final entry'.",opts:["False","True"],correct:0},
   {topic:"Capital calc",q:"Assets ₹200, Liabilities ₹80. Capital = ?",opts:["₹120","₹280","₹80"],correct:0},
   {topic:"Terms",q:"Money the business OWES to others is called?",opts:["Liabilities","Assets","Capital"],correct:0}]},
 "agentic":{name:"Agentic AI Systems",questions:[
   {topic:"Agent loop",q:"First step of the agent loop?",opts:["Perceive","Act","Stop"],correct:0},
   {topic:"LLM core",q:"Inside an agent, the LLM's main job is to?",opts:["Decide the next action","Run the tools","Store the data"],correct:0},
   {topic:"Tools",q:"When the model 'calls a tool', who actually runs it?",opts:["The code / system","The LLM itself","The user"],correct:0},
   {topic:"RAG",q:"RAG stands for Retrieval + ?",opts:["Generation","Ranking","Regression"],correct:0}]}
};
async function sendWhatsAppButtons(to, body, buttons) {
  const url = `https://graph.facebook.com/${GRAPH_VERSION}/${PHONE_NUMBER_ID}/messages`;
  const res = await fetch(url, { method: "POST", headers: { Authorization: `Bearer ${META_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to, type: "interactive",
      interactive: { type: "button", body: { text: body.slice(0, 1024) },
        action: { buttons: buttons.slice(0, 3).map(b => ({ type: "reply", reply: { id: b.id.slice(0, 256), title: b.title.slice(0, 20) } })) } } }) });
  const j = await res.json().catch(() => ({})); if (!res.ok) log("wa buttons failed:", res.status, JSON.stringify(j));
}
const isTF = q => q.opts.length === 2 && q.opts.every(o => /^(true|false)$/i.test(o));
async function sendQuizQuestion(to, bank, idx) {
  const q = bank.questions[idx], n = bank.questions.length, L = ["A", "B", "C"];
  let body, buttons;
  if (isTF(q)) { body = `📝 *Q${idx + 1}/${n}* · ${bank.name}\n\n${q.q}`; buttons = q.opts.map((o, i) => ({ id: `QZ|${idx}|${i}`, title: o })); }
  else { body = `📝 *Q${idx + 1}/${n}* · ${bank.name}\n\n${q.q}\n\n` + q.opts.map((o, i) => `${L[i]}) ${o}`).join("\n"); buttons = q.opts.map((o, i) => ({ id: `QZ|${idx}|${i}`, title: L[i] })); }
  await sendWhatsAppButtons(to, body, buttons);
}
async function quizStart(from, p, subj) {
  const bank = WA_QUIZ[subj];
  p.wa_quiz = { subject: subj, idx: 0, score: 0, results: [] }; saveProfile(from, p);
  await sendWhatsApp(from, `🎯 *Assessment mode* — ${bank.name}. ${bank.questions.length} tap-questions. Just tap a button. Chalo!`);
  await sendQuizQuestion(from, bank, 0); return true;
}
async function quizAnswer(from, p, qi, oi) {
  const st = p.wa_quiz, bank = WA_QUIZ[st.subject];
  if (!bank) { delete p.wa_quiz; saveProfile(from, p); return true; }
  if (qi !== st.idx) return true;                        // stale/duplicate tap
  const q = bank.questions[qi], ok = oi === q.correct, L = ["A", "B", "C"];
  if (ok) st.score++; st.results.push({ topic: q.topic, ok });
  const cl = isTF(q) ? q.opts[q.correct] : `${L[q.correct]}) ${q.opts[q.correct]}`;
  await sendWhatsApp(from, ok ? "✅ *Sahi!*" : `❌ Sahi jawab: *${cl}*`);
  st.idx++;
  if (st.idx < bank.questions.length) { saveProfile(from, p); await sendQuizQuestion(from, bank, st.idx); }
  else { await quizFinish(from, p); }
  return true;
}
async function quizFinish(from, p) {
  const st = p.wa_quiz, bank = WA_QUIZ[st.subject], total = bank.questions.length;
  const weak = [...new Set(st.results.filter(r => !r.ok).map(r => r.topic))];
  let msg = `🎉 *Test complete!*\nScore: *${st.score}/${total}* · ${bank.name}`;
  msg += weak.length ? `\n\n⚠️ Weak topics: *${weak.join(", ")}*\n🎯 Suggestion: revise *${weak[0]}* first, then re-take.` : `\n\n💪 All correct — shabaash!`;
  msg += `\n\n👨‍🏫 Yeh report teacher ke dashboard par bhi dikhti hai — kaun kahan weak hai.\n\n_Dobara test: type *quiz*_`;
  delete p.wa_quiz; saveProfile(from, p);
  await sendWhatsApp(from, msg);
  try { logEvent({ type: "wa_quiz", student: from, subject: st.subject, score: st.score, total }); } catch {}
  return true;
}
async function maybeHandleQuiz(from, text, buttonId) {
  const p = loadProfile(from);
  if (p.wa_quiz && buttonId && buttonId.startsWith("QZ|")) {
    const [, qi, oi] = buttonId.split("|"); return await quizAnswer(from, p, Number(qi), Number(oi));
  }
  const m = (text || "").trim().match(/^(quiz|assessment|assess me|start quiz|take (?:a )?quiz|test me)\b\s*(.*)$/i);
  if (m && !p.wa_quiz) {
    const arg = (m[2] || "").trim().toLowerCase();
    const alias = { neet: "neet-biology", bio: "neet-biology", biology: "neet-biology", jee: "jee-physics", physics: "jee-physics",
      class10: "class10", "10": "class10", class12: "class12", "12": "class12", board: "class12",
      commerce: "commerce", accounts: "commerce", agentic: "agentic", ai: "agentic" };
    let subj = null;
    if (arg) for (const k in alias) if (arg.includes(k)) { subj = alias[k]; break; }
    if (!subj && WA_QUIZ[p.course]) subj = p.course;    // real student → their own course
    if (!subj) { await sendWhatsApp(from, "🎯 Kaunsa subject? Reply:\n*quiz neet* · *quiz jee* · *quiz class10* · *quiz class12* · *quiz commerce* · *quiz agentic*"); return true; }
    return await quizStart(from, p, subj);
  }
  return false;
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
            const from = msg.from;
            // Accept plain text AND interactive quick-reply button clicks (templates use buttons).
            let text = "", buttonId = null;
            if (msg.type === "text") {
              text = msg.text?.body || "";
            } else if (msg.type === "interactive" && msg.interactive?.type === "button_reply") {
              text = msg.interactive.button_reply.title || "";
              buttonId = msg.interactive.button_reply.id || null;
            } else {
              continue;  // unsupported types (image/audio/etc.) — same behaviour as before
            }
            if (msg.id) await sendTyping(msg.id);   // "typing…" while the right side thinks
            const isAdmin = ADMIN_NUMBERS.includes(from);
            log("inbound <-", from, isAdmin ? "[ADMIN]" : "", buttonId ? `[BTN:${buttonId}]` : "", JSON.stringify(text).slice(0, 80));

            // Teacher-onboarding path: forward to onboarding_bot.py if the number is in the queue.
            // Returns null when the sender isn't a queued teacher OR the bot is down — falls through cleanly.
            const onboarding = await maybeHandleTeacherOnboarding(from, text, buttonId);
            if (onboarding && onboarding.stage && onboarding.stage !== "not_in_queue") {
              if (onboarding.reply) await sendWhatsApp(from, onboarding.reply);
              continue;   // handled — do NOT fall through to admin/Acharya
            }

            // WhatsApp native assessment (tap-button quiz) — "quiz" starts it; button taps drive it.
            // Deterministic (no LLM, no mastery write) → safe for Rohan's demo number + real students.
            if (await maybeHandleQuiz(from, text, buttonId)) continue;

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
    try {
      res.writeHead(200, {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store, no-cache, must-revalidate",
      });
      return res.end(fs.readFileSync(`${HOME}/.openclaw/gurukul/chat.html`, "utf8"));
    } catch { res.writeHead(500); return res.end("chat unavailable"); }
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

  // ---- Student "Report & Improvement" page (served fresh; scp = live) ----
  if (req.method === "GET" && u.pathname === "/report") {
    try { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store, no-cache, must-revalidate" });
      return res.end(fs.readFileSync(`${HOME}/.openclaw/gurukul/report.html`, "utf8")); }
    catch { res.writeHead(500); return res.end("report unavailable"); }
  }
  // ---- Student "Report & Improvement": their real SWOT, read from their own profile ----
  if (req.method === "GET" && u.pathname === "/report/api") {
    const J = (code, obj) => { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); };
    try {
      const v = verifyToken(u.searchParams.get("t") || u.searchParams.get("token"));
      if (!v) return J(401, { error: "expired" });
      const idmap = loadIdentity();
      const key = idmap[v.email] || sanitizeEmail(v.email);
      const p = loadProfile(key);
      const bank = courseBank(p.course || v.course);
      const order = (bank.order && bank.order.length) ? bank.order : Object.keys(bank.concepts || {});
      const ACR = { llm:"LLM", rag:"RAG", api:"API", srs:"SRS", ai:"AI", fn:"Function", react:"ReAct", vs:"vs", is:"is", a:"a", of:"of", to:"to" };
      const nameOf = k => k.split("_").map(w => ACR[w.toLowerCase()] || (w.charAt(0).toUpperCase() + w.slice(1))).join(" ");
      const con = p.concepts || {}, dueMap = {}; (p.srs || []).forEach(s => dueMap[s.concept] = s.due);
      const strong = [], weak = [];
      order.forEach(k => { if (!bank.concepts[k]) return;
        const st = con[k] || "not_seen", base = { key: k, name: nameOf(k), module: bank.concepts[k].module };
        if (st === "solid") strong.push(base);
        else if (st === "shaky") weak.push({ ...base, recall: bank.concepts[k].recall, answer: bank.concepts[k].answer, due: dueMap[k] || null });
      });
      const suggestion = weak.length
        ? `Revise your ${weak.length} weak topic${weak.length > 1 ? "s" : ""} — start with “${weak[0].name}”. Take the quick test below.`
        : `Every concept is solid — you're ready for the next module! 🎯`;
      return J(200, { name: p.name || "", course: bank.name || v.course,
        total: order.filter(k => bank.concepts[k]).length, solid: strong.length, shaky: weak.length, streak: p.streak || 0,
        strong, weak, misconceptions: (p.misconceptions || []).slice(-4), suggestion });
    } catch (e) { log("report/api error:", e.message); return J(500, { error: "server" }); }
  }
  // ---- grade one self-review → update mastery on the real profile (minimal, never downgrades a solid) ----
  if (req.method === "POST" && u.pathname === "/report/grade") {
    const J = (code, obj) => { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); };
    try {
      const { token, concept, got } = JSON.parse(await readBody(req));
      const v = verifyToken(token); if (!v) return J(401, { error: "expired" });
      const idmap = loadIdentity();
      const key = idmap[v.email] || sanitizeEmail(v.email);
      const p = loadProfile(key);
      const bank = courseBank(p.course || v.course);
      if (!bank.concepts[concept]) return J(400, { error: "unknown concept" });
      p.concepts = p.concepts || {}; p.srs = Array.isArray(p.srs) ? p.srs : [];
      let item = p.srs.find(s => s.concept === concept);
      if (!item) { item = { concept, box: 0, due: DUE(1) }; p.srs.push(item); }
      if (got) { p.concepts[concept] = "solid"; item.box = Math.min((item.box || 0) + 1, SRS_INTERVALS.length - 1); item.due = DUE(SRS_INTERVALS[item.box]); }
      else { if (p.concepts[concept] !== "solid") p.concepts[concept] = "shaky"; item.box = 0; item.due = DUE(SRS_INTERVALS[0]); }
      p.updated = new Date().toISOString();
      saveProfile(key, p);
      try { logEvent({ type: "self_review", student: key, concept, got: !!got }); } catch {}
      return J(200, { ok: true, status: p.concepts[concept] });
    } catch (e) { log("report/grade error:", e.message); return J(500, { error: "server" }); }
  }

  if (u.pathname === "/health") { res.writeHead(200); return res.end("ok"); }
  res.writeHead(404); res.end("not found");
});

sanitizeAllProfiles();   // one-time cleanup: strip cross-course concept/SRS pollution on boot
server.listen(Number(PORT), "127.0.0.1", () =>
  log(`WA cloud bridge (profiles on, grounded mastery + SRS + event log) listening on 127.0.0.1:${PORT}`));
