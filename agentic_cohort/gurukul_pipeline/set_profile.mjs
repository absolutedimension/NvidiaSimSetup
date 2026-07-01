// Set the WhatsApp Business profile: photo + about + description + website.
// Usage: APP_ID=.. APP_SECRET=.. node set_profile.mjs /path/to/icon.png
// Reads META_TOKEN + PHONE_NUMBER_ID from ~/.openclaw/wa_cloud.env.
import fs from "node:fs";

const HOME = process.env.HOME;
const env = {};
for (const l of fs.readFileSync(`${HOME}/.openclaw/wa_cloud.env`, "utf8").split("\n")) {
  const m = l.match(/^([A-Z_]+)=(.*)$/); if (m) env[m[1]] = m[2];
}
const { META_TOKEN, PHONE_NUMBER_ID, GRAPH_VERSION = "v21.0" } = env;
const APP_ID = process.env.APP_ID, APP_SECRET = process.env.APP_SECRET;
const APP_TOKEN = `${APP_ID}|${APP_SECRET}`;
const iconPath = process.argv[2];
const buf = fs.readFileSync(iconPath);

const ABOUT = "🪔 Your AI guru — build real AI agents, step by step.";
const DESCRIPTION = "TrigunAI Gurukul: a personal AI tutor (Acharya) that teaches you to build working " +
  "AI agents from scratch — one step at a time, on your own project. TrigunAI · Building Agentic Systems cohort.";

// 1) create resumable upload session
const sess = await (await fetch(
  `https://graph.facebook.com/${GRAPH_VERSION}/${APP_ID}/uploads?file_name=gurukul.png&file_length=${buf.length}&file_type=image/png&access_token=${APP_TOKEN}`,
  { method: "POST" })).json();
if (!sess.id) { console.log("upload session failed:", JSON.stringify(sess)); process.exit(1); }
console.log("upload session:", sess.id);

// 2) upload the bytes -> get handle
const up = await (await fetch(`https://graph.facebook.com/${GRAPH_VERSION}/${sess.id}`, {
  method: "POST",
  headers: { Authorization: `OAuth ${APP_TOKEN}`, file_offset: "0" },
  body: buf,
})).json();
if (!up.h) { console.log("upload failed:", JSON.stringify(up)); process.exit(1); }
console.log("got picture handle");

// 3) set the business profile (photo + about + description + website)
const res = await (await fetch(`https://graph.facebook.com/${GRAPH_VERSION}/${PHONE_NUMBER_ID}/whatsapp_business_profile`, {
  method: "POST",
  headers: { Authorization: `Bearer ${META_TOKEN}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    messaging_product: "whatsapp",
    profile_picture_handle: up.h,
    about: ABOUT,
    description: DESCRIPTION,
    websites: ["https://trigunai.com", "https://lms.trigunai.com"],
    vertical: "EDU",
  }),
})).json();
console.log("profile update:", JSON.stringify(res));
