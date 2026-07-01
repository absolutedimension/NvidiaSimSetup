// Add students to the cohort roster by phone number (so broadcasts + SRS reach them).
//
//   node add_student.mjs 919876543210 918454964893 "Aditya:919812345678"
//
// Accepts bare numbers (digits, country code, no +) or "Name:number". Creates a profile
// stub for each if one doesn't exist. The roster = all profiles on disk.
//
// NOTE: to actually message a student who has NOT messaged you first, WhatsApp requires
// (a) they opted in, and (b) an approved template (gurukul_announce / gurukul_recall).
// The cleanest onboarding is still: student texts the number once ("JOIN") — that opens
// their 24h window AND auto-creates their profile. Use this tool to pre-load known numbers.

import fs from "node:fs";
const STUDENTS_DIR = `${process.env.HOME}/.openclaw/students`;
fs.mkdirSync(STUDENTS_DIR, { recursive: true });

// --course <id> sets the course they registered for (default agentic). Rest are numbers / "Name:number".
const all = process.argv.slice(2);
const ci = all.indexOf("--course");
const course = ci !== -1 ? all[ci + 1] : "agentic";
const args = all.filter((a, i) => a !== "--course" && (ci === -1 || i !== ci + 1));
if (!args.length) { console.log('usage: node add_student.mjs [--course agentic|remote-swe] <number> ["Name:number"] ...'); process.exit(1); }

let added = 0, existed = 0;
for (const a of args) {
  const [maybeName, maybeNum] = a.includes(":") ? a.split(":") : ["", a];
  const num = (maybeNum || maybeName).replace(/[^\d]/g, "");
  const name = a.includes(":") ? maybeName.trim() : "";
  if (num.length < 10) { console.log("  skip (bad number):", a); continue; }
  const path = `${STUDENTS_DIR}/${num}.json`;
  if (fs.existsSync(path)) { existed++; console.log("  exists:", num); continue; }
  fs.writeFileSync(path, JSON.stringify({
    wa_id: num, name, course, byoa_goal: "", level: "", current_module: 2,
    concepts: {}, misconceptions: [], srs: [], streak: 0, last_win: "", notes: [],
    interests: [], background: "", style: "", created: new Date().toISOString(),
  }, null, 2));
  added++; console.log("  added:", num, name ? `(${name})` : "", `[${course}]`);
}
console.log(`roster: +${added} added, ${existed} already present. course=${course}`);
