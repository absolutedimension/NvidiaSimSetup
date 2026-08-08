// Standalone read-only admin dashboard — reads ~/.openclaw/students/*.json and serves a live
// progress view. Independent of the bridge/gateway (never restarts them). Own systemd service.
//
// Env: DASH_PORT (default 8790), ADMIN_KEY (required to fetch data).
import http from "node:http";
import fs from "node:fs";

const HOME = process.env.HOME;
const STUDENTS_DIR = `${HOME}/.openclaw/students`;
const PORT = Number(process.env.DASH_PORT || 8790);
const KEY = process.env.ADMIN_KEY || "";

function students() {
  let files = [];
  try { files = fs.readdirSync(STUDENTS_DIR); } catch {}
  const out = [];
  for (const f of files) {
    if (!f.endsWith(".json") || f.startsWith("_")) continue;
    try {
      const p = JSON.parse(fs.readFileSync(`${STUDENTS_DIR}/${f}`, "utf8"));
      const concepts = p.concepts || {};
      out.push({
        name: p.name || "", id: p.wa_id || f.replace(/\.json$/, ""),
        channel: f.startsWith("web_") ? "web" : "whatsapp",
        course: p.course || "agentic",
        module: p.current_module || 2,
        solid: Object.values(concepts).filter(v => v === "solid").length,
        shaky: Object.values(concepts).filter(v => v === "shaky").length,
        touched: Object.keys(concepts).length,
        misconceptions: p.misconceptions || [],
        // Dhyan calibration signal — the "confidently wrong" concepts (highest-value teacher flag).
        // Acharya writes these as it teaches (SOUL law 8); may be a flat list or under `calibration`.
        confidently_wrong: p.confidently_wrong || (p.calibration && p.calibration.confidently_wrong) || [],
        streak: p.streak || 0, goal: p.byoa_goal || "", level: p.level || "",
        interests: p.interests || [], background: p.background || "",
        last_win: p.last_win || "", updated: p.updated || p.created || "",
        greeted: !!p.greeted,
      });
    } catch {}
  }
  return out.sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  if (u.pathname === "/admin" || u.pathname === "/admin/") {
    try { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(fs.readFileSync(`${HOME}/.openclaw/gurukul/admin.html`, "utf8")); }
    catch { res.writeHead(500); return res.end("dashboard unavailable"); }
  }
  if (u.pathname === "/admin/api") {
    if (KEY && u.searchParams.get("k") !== KEY) { res.writeHead(401); return res.end("unauthorized"); }
    const list = students(), now = Date.now();
    const active = list.filter(s => s.updated && (now - Date.parse(s.updated)) < 86400000).length;
    res.writeHead(200, { "Content-Type": "application/json" });
    return res.end(JSON.stringify({ total: list.length, active, inactive: list.length - active,
      generatedAt: new Date().toISOString(), students: list }));
  }
  res.writeHead(404); res.end("not found");
});
server.listen(PORT, "127.0.0.1", () => console.log("gurukul admin dashboard on 127.0.0.1:" + PORT));
