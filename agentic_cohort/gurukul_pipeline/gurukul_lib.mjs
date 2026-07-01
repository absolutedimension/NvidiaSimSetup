// Shared helpers for the Gurukul pipeline (roster, profiles, WhatsApp sends, concepts).
import fs from "node:fs";

const HOME = process.env.HOME;
export const STUDENTS_DIR = `${HOME}/.openclaw/students`;
const GURUKUL_DIR = `${HOME}/.openclaw/gurukul`;

// Load wa_cloud.env (META_TOKEN, PHONE_NUMBER_ID, GRAPH_VERSION) into an object.
export function env() {
  const e = {};
  for (const line of fs.readFileSync(`${HOME}/.openclaw/wa_cloud.env`, "utf8").split("\n")) {
    const m = line.match(/^([A-Z_]+)=(.*)$/);
    if (m) e[m[1]] = m[2];
  }
  return e;
}

export const log = (...a) => console.log(new Date().toISOString(), ...a);

// Roster = every student profile on disk (skip roster.json itself).
export function roster() {
  try {
    return fs.readdirSync(STUDENTS_DIR)
      .filter(f => f.endsWith(".json") && f !== "roster.json")
      .map(f => f.replace(/\.json$/, ""));
  } catch { return []; }
}

export function loadProfile(waId) {
  try { return JSON.parse(fs.readFileSync(`${STUDENTS_DIR}/${waId}.json`, "utf8")); }
  catch {
    return { wa_id: waId, name: "", byoa_goal: "", level: "", current_module: 2,
             concepts: {}, misconceptions: [], srs: [], streak: 0, last_win: "", notes: [] };
  }
}
export function saveProfile(waId, p) {
  p.wa_id = waId; p.updated = new Date().toISOString();
  fs.writeFileSync(`${STUDENTS_DIR}/${waId}.json`, JSON.stringify(p, null, 2));
}

// Per-course concept bank: courses/<id>.json. Falls back to agentic.
export function courseBank(course) {
  const id = (course || "agentic").replace(/[^a-z0-9-]/gi, "");
  for (const c of [id, "agentic"]) {
    try { return JSON.parse(fs.readFileSync(`${GURUKUL_DIR}/courses/${c}.json`, "utf8")); } catch {}
  }
  return { concepts: {}, order: [], name: "" };
}

// Free-form text (only valid inside a student's 24h window).
export async function sendText(to, body) {
  const e = env();
  const r = await fetch(`https://graph.facebook.com/${e.GRAPH_VERSION}/${e.PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${e.META_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to, type: "text", text: { body: body.slice(0, 4096) } }),
  });
  return { ok: r.ok, body: await r.json().catch(() => ({})) };
}

// Approved template (required for business-initiated / out-of-window messages).
// params = array of strings filling {{1}}, {{2}}, ... in the template body.
export async function sendTemplate(to, name, params = [], lang = "en_US") {
  const e = env();
  const components = params.length
    ? [{ type: "body", parameters: params.map(t => ({ type: "text", text: String(t) })) }]
    : [];
  const r = await fetch(`https://graph.facebook.com/${e.GRAPH_VERSION}/${e.PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${e.META_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messaging_product: "whatsapp", to, type: "template",
      template: { name, language: { code: lang }, components } }),
  });
  return { ok: r.ok, body: await r.json().catch(() => ({})) };
}
