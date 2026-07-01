// Broadcast a message to every student on the roster (Channel 2, Option A fan-out).
//
//   node broadcast.mjs "Class tonight 5pm — bring your agent.py"     # free-form (24h window only)
//   node broadcast.mjs --template gurukul_announce --param "Class tonight 5pm"   # template (any time)
//
// Free-form reaches only students messaged in the last 24h. For business-initiated
// announcements use an approved template (see TEMPLATES.md).

import { roster, sendText, sendTemplate, log } from "./gurukul_lib.mjs";

const args = process.argv.slice(2);
const tIdx = args.indexOf("--template");
const pIdx = args.indexOf("--param");
const useTemplate = tIdx !== -1;
const templateName = useTemplate ? args[tIdx + 1] : null;
const param = pIdx !== -1 ? args[pIdx + 1] : null;
const text = useTemplate ? null : args.filter(a => !a.startsWith("--")).join(" ");

const students = roster();
if (!students.length) { log("roster empty — no students yet"); process.exit(0); }
if (!useTemplate && !text) { log("usage: node broadcast.mjs \"message\"  OR  --template <name> --param \"...\""); process.exit(1); }

log(`broadcasting to ${students.length} student(s) via ${useTemplate ? "template " + templateName : "free-form text"}`);
let ok = 0, fail = 0;
for (const to of students) {
  const res = useTemplate
    ? await sendTemplate(to, templateName, param ? [param] : [])
    : await sendText(to, text);
  if (res.ok) { ok++; log("  ✓", to); }
  else { fail++; log("  ✗", to, JSON.stringify(res.body?.error?.message || res.body).slice(0, 120)); }
}
log(`done: ${ok} sent, ${fail} failed`);
