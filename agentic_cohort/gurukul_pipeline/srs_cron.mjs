// Daily spaced-repetition engine. For each student, sends the most-overdue recall
// question for a concept they've already been taught. Run once/day via systemd timer.
//
// Pedagogy: only concepts the student has SEEN (shaky|solid) enter the queue — you recall
// what you've learned, on an expanding schedule (1 → 3 → 7 → 16 → 30 days).
//
// Send path: a business-initiated message => requires an approved template `gurukul_recall`
// with a {{1}} body variable (see TEMPLATES.md). The recall question fills {{1}}.
// On the student's reply, the bridge grades it (pending_recall) and advances/ resets the box.

import { roster, loadProfile, saveProfile, courseBank, sendTemplate, log } from "./gurukul_lib.mjs";
import { execFile } from "node:child_process";

const BOX_DAYS = [1, 3, 7, 16, 30];
const TEMPLATE = process.env.RECALL_TEMPLATE || "gurukul_recall";
const EXTRACT_MODEL = "microsoft-foundry/gpt-4o-mini";
const today = new Date().toISOString().slice(0, 10);
const addDays = (n) => { const d = new Date(); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };

// Quick cheap LLM call (parses openclaw infer plain-text output).
function runInfer(prompt) {
  return new Promise((resolve) => {
    execFile("openclaw", ["infer", "model", "run", "--model", EXTRACT_MODEL, "--prompt", prompt],
      { timeout: 45000, maxBuffer: 1024 * 1024 }, (err, stdout) => {
        if (err) return resolve(null);
        const i = stdout.lastIndexOf("outputs:");
        const txt = i >= 0 ? stdout.slice(stdout.indexOf("\n", i) + 1) : stdout;
        resolve(txt.trim() || null);
      });
  });
}

// Reword the recall question with a light touch of the student's world. Question stays intact.
async function personalize(p, recall) {
  const ctx = [
    p.interests?.length ? `interests: ${p.interests.join(", ")}` : "",
    p.background ? `work: ${p.background}` : "",
  ].filter(Boolean).join("; ");
  if (!ctx) return recall;
  const out = await runInfer(
    `Personalize this spaced-repetition recall question for a student (${ctx}). Add a LIGHT, brief touch ` +
    `of their world (a few words), but KEEP the actual question and meaning fully intact and answerable. ` +
    `One short line. If no natural fit, return it unchanged. Output ONLY the question.\n\nQuestion: ${recall}`);
  return out && out.length <= 300 ? out : recall;
}

const students = roster();
log(`SRS run for ${students.length} student(s); template=${TEMPLATE}`);

for (const waId of students) {
  const p = loadProfile(waId);
  const { concepts } = courseBank(p.course);   // each student's own course bank
  p.srs = p.srs || [];
  const seen = Object.entries(p.concepts || {})
    .filter(([k, v]) => concepts[k] && (v === "shaky" || v === "solid")).map(([k]) => k);

  // Ensure every seen concept has an SRS entry (new ones due tomorrow).
  for (const k of seen) if (!p.srs.find(s => s.concept === k))
    p.srs.push({ concept: k, box: 0, due: addDays(1) });

  // Pick the most-overdue due item.
  const due = p.srs.filter(s => s.due <= today).sort((a, b) => a.due.localeCompare(b.due));
  if (!due.length) { log(`  ${waId}: nothing due`); continue; }
  const item = due[0];
  const c = concepts[item.concept];

  const question = await personalize(p, c.recall);     // flavor it with their interests/work
  const res = await sendTemplate(waId, TEMPLATE, [question]);
  if (res.ok) {
    p.pending_recall = item.concept;                 // bridge grades the reply against this
    item.due = addDays(BOX_DAYS[item.box] || 30);    // tentative; reset on a miss
    saveProfile(waId, p);
    log(`  ${waId}: pinged '${item.concept}'`);
  } else {
    const msg = res.body?.error?.message || JSON.stringify(res.body);
    log(`  ${waId}: send failed — ${String(msg).slice(0, 140)}`);
    if (String(msg).includes(TEMPLATE)) log(`     (create+approve the '${TEMPLATE}' template — see TEMPLATES.md)`);
  }
}
log("SRS run complete");
