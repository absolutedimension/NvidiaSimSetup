#!/usr/bin/env node
// One-time WhatsApp template setup for the Gurukul channel. Idempotent.
// Resolves the WABA id from the token, lists existing templates, and creates any
// REQUIRED template that's missing (submits for Meta approval — Utility templates
// usually approve in minutes). Does NOT send any message to any student.
//
// Run ON THE VM (keeps META_TOKEN on the box):  node wa_setup_templates.mjs
// Add  --create  to actually create missing templates (default is dry-run / status only).
import fs from "node:fs";

const HOME = process.env.HOME;
const DO_CREATE = process.argv.includes("--create");
const env = {};
for (const l of fs.readFileSync(`${HOME}/.openclaw/wa_cloud.env`, "utf8").split("\n")) {
  const m = l.match(/^([A-Z_]+)=(.*)$/); if (m) env[m[1]] = m[2];
}
const { META_TOKEN, PHONE_NUMBER_ID, GRAPH_VERSION = "v21.0" } = env;
let WABA_ID = env.WABA_ID || env.WHATSAPP_BUSINESS_ACCOUNT_ID || "";
const G = `https://graph.facebook.com/${GRAPH_VERSION}`;
const api = async (url, opts) => {
  const r = await fetch(url, opts);
  let j; try { j = await r.json(); } catch { j = {}; }
  return { ok: r.ok, status: r.status, j };
};

// --- resolve WABA id from the token's granular scopes if not in env ---
if (!WABA_ID) {
  const dbg = await api(`${G}/debug_token?input_token=${META_TOKEN}&access_token=${META_TOKEN}`);
  const scopes = dbg.j?.data?.granular_scopes || [];
  for (const s of scopes) {
    if (/whatsapp_business_(messaging|management)/.test(s.scope) && s.target_ids?.length) {
      WABA_ID = s.target_ids[0]; break;
    }
  }
}
if (!WABA_ID) {
  console.error("Could not resolve WABA_ID. Add WABA_ID=... to ~/.openclaw/wa_cloud.env and retry.");
  process.exit(1);
}
console.log(`WABA: ${WABA_ID}  |  phone: ${PHONE_NUMBER_ID}  |  ${GRAPH_VERSION}\n`);

// --- required templates (match TEMPLATES.md + the bridge/srs_cron expectations) ---
const REQUIRED = [
  { name: "gurukul_recall", category: "UTILITY", language: "en_US",
    body: "🪔 Quick recall, no peeking: {{1}}\n\nReply with your answer — Acharya",
    sample: "Name the 4 steps of the agent loop, in order." },
  { name: "gurukul_announce", category: "UTILITY", language: "en_US",
    body: "🪔 TrigunAI Gurukul\n\n{{1}}",
    sample: "Live class tonight at 5pm. Bring your agent.py." },
];

// --- list existing ---
const existing = {};
let url = `${G}/${WABA_ID}/message_templates?fields=name,status,language,category&limit=100&access_token=${META_TOKEN}`;
while (url) {
  const { ok, j } = await api(url);
  if (!ok) { console.error("list failed:", JSON.stringify(j).slice(0, 300)); break; }
  for (const t of j.data || []) (existing[t.name] ||= []).push(`${t.language}:${t.status}`);
  url = j.paging?.next || "";
}
console.log("Existing templates:");
for (const [n, v] of Object.entries(existing)) console.log(`  ${n.padEnd(20)} ${v.join(", ")}`);
if (!Object.keys(existing).length) console.log("  (none)");
console.log("");

// --- create missing ---
for (const t of REQUIRED) {
  const have = (existing[t.name] || []).some(v => v.startsWith(t.language));
  if (have) { console.log(`= ${t.name} (${t.language}) already exists [${existing[t.name].join(", ")}] — skip`); continue; }
  if (!DO_CREATE) { console.log(`+ ${t.name} (${t.language}) MISSING — would create (re-run with --create)`); continue; }
  const body = {
    name: t.name, language: t.language, category: t.category,
    components: [{ type: "BODY", text: t.body, example: { body_text: [[t.sample]] } }],
  };
  const { ok, status, j } = await api(`${G}/${WABA_ID}/message_templates`, {
    method: "POST",
    headers: { Authorization: `Bearer ${META_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (ok) console.log(`✓ created ${t.name} (${t.language}) — id ${j.id}, status ${j.status || "PENDING"}`);
  else console.log(`✗ ${t.name} failed [${status}]: ${JSON.stringify(j.error || j).slice(0, 240)}`);
}
console.log("\nDone. Approval is async (Utility: usually minutes). Re-run without --create to check status.");
