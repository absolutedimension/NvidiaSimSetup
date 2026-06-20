const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup";
const LOGO_DIR = "/Users/deepakkumarrai/Documents/01_Active/Blender-Antigravity/trigun-logo-output";
const LOGO_LIGHT = path.join(LOGO_DIR, "trigun_2k_transparent.png"); // official tri-guna logo (glow on transparent → for dark bg)
const LOGO_DARK  = path.join(LOGO_DIR, "trigun_2k_transparent.png");

// ---- Palette (TrigunAI: deep navy + gold) ----
const NAVY   = "0B1B2E"; // dark bg
const NAVY2  = "13314F"; // panel on dark
const GOLD   = "C9A227"; // accent
const INK    = "1A2333"; // dark text on light
const MUTED  = "667085"; // muted text
const LIGHT  = "F6F8FB"; // light bg
const CARD   = "FFFFFF"; // card on light
const LINE   = "E3E8EF"; // hairline
const GREEN  = "76B900"; // NVIDIA green — used ONLY to reference NVIDIA tech

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "TrigunAI Innovations";
pres.company = "TrigunAI Innovations Pvt Ltd";
pres.title = "TrigunAI — Company Pitch (NVIDIA Inception)";

const W = 13.33, H = 7.5, M = 0.7;
const shadow = () => ({ type: "outer", color: "000000", blur: 9, offset: 3, angle: 90, opacity: 0.10 });

// ---------- helpers ----------
function pageFooter(slide, n, dark) {
  const c = dark ? "9FB3C8" : MUTED;
  slide.addText("TrigunAI Innovations", { x: M, y: H - 0.5, w: 4, h: 0.3, fontSize: 9, color: c, align: "left", margin: 0 });
  slide.addText(`${n} / 12`, { x: W - M - 2, y: H - 0.5, w: 2, h: 0.3, fontSize: 9, color: c, align: "right", margin: 0 });
}

function lightHeader(slide, kicker, title) {
  slide.background = { color: LIGHT };
  slide.addText("TRIGUNAI", { x: M, y: 0.45, w: 4, h: 0.3, fontSize: 11, bold: true, color: INK, charSpacing: 3, margin: 0 });
  slide.addShape(pres.shapes.RECTANGLE, { x: M, y: 1.15, w: 0.45, h: 0.09, fill: { color: GOLD }, line: { type: "none" } });
  slide.addText(kicker, { x: M, y: 0.95, w: 8, h: 0.3, fontSize: 12, bold: true, color: GOLD, charSpacing: 2, margin: 0 });
  slide.addText(title, { x: M, y: 1.32, w: W - 2 * M, h: 0.85, fontSize: 32, bold: true, color: INK, fontFace: "Georgia", margin: 0 });
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill || CARD }, line: { color: LINE, width: 1 }, shadow: shadow() });
}

// ============================================================= SLIDE 1 — TITLE
let s = pres.addSlide();
s.background = { color: NAVY };
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.18, fill: { color: GOLD }, line: { type: "none" } });
s.addImage({ path: LOGO_LIGHT, x: M, y: 1.0, w: 1.5, h: 1.5, sizing: { type: "contain", w: 1.5, h: 1.5 } });
s.addText("TrigunAI Innovations", { x: M, y: 2.7, w: W - 2 * M, h: 0.9, fontSize: 46, bold: true, color: "FFFFFF", fontFace: "Georgia", margin: 0 });
s.addText("Two engines, one company — AI education that ships, and physical-AI research.",
  { x: M, y: 3.65, w: 10.5, h: 0.6, fontSize: 18, color: "CFE0F0", margin: 0 });
// credential chips
const chips = ["NVIDIA Inception Member", "Google Android XR Catalyst"];
let cx = M;
chips.forEach(t => {
  const cw = 0.28 + t.length * 0.092;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: 4.5, w: cw, h: 0.42, fill: { color: NAVY2 }, line: { color: GOLD, width: 1 }, rectRadius: 0.08 });
  s.addText(t, { x: cx, y: 4.5, w: cw, h: 0.42, fontSize: 11.5, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
  cx += cw + 0.25;
});
s.addText("Patna · Mumbai, India     |     CIN U86909BR2025PTC078945     |     Incorporated 2025",
  { x: M, y: 6.55, w: W - 2 * M, h: 0.4, fontSize: 12, color: "8FA6BD", margin: 0 });

// ============================================================= SLIDE 2 — WHY NOW
s = pres.addSlide();
lightHeader(s, "WHY NOW", "Two pressures, one company built for both");
const colW = (W - 2 * M - 0.5) / 2;
card(s, M, 2.35, colW, 2.7);
card(s, M + colW + 0.5, 2.35, colW, 2.7);
s.addText("India needs an AI workforce", { x: M + 0.35, y: 2.65, w: colW - 0.7, h: 0.5, fontSize: 19, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "The world's #1 AI-learning market — 1.3M+ learners and rising (NASSCOM–Deloitte).", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "But the talent pipeline is fragmented and theory-heavy.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "We teach by shipping — learners leave with a published app or a trained policy.", options: { bullet: true } },
], { x: M + 0.35, y: 3.25, w: colW - 0.7, h: 1.6, fontSize: 13.5, color: INK });
s.addText("Physical AI is the next decade", { x: M + colW + 0.85, y: 2.65, w: colW - 0.7, h: 0.5, fontSize: 19, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Robotics & embodied AI is where value compounds next.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "India has minimal indigenous capability and little founder-accessible Isaac-grade infra.", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "We build that capability in-house on the NVIDIA stack.", options: { bullet: true } },
], { x: M + colW + 0.85, y: 3.25, w: colW - 0.7, h: 1.6, fontSize: 13.5, color: INK });
s.addText("Our bet: build the human-capital pipeline for India's physical-AI workforce — and own a piece of the stack while we do it.",
  { x: M, y: 5.4, w: W - 2 * M, h: 0.7, fontSize: 15, italic: true, bold: true, color: NAVY2, align: "center", margin: 0 });
pageFooter(s, 2, false);

// ============================================================= SLIDE 3 — TWO-ENGINE MODEL
s = pres.addSlide();
lightHeader(s, "THE MODEL", "One company, two coupled engines");
const ew = (W - 2 * M - 0.5) / 2;
// Engine A
card(s, M, 2.4, ew, 2.5);
s.addShape(pres.shapes.RECTANGLE, { x: M, y: 2.4, w: ew, h: 0.12, fill: { color: GOLD }, line: { type: "none" } });
s.addText("ENGINE A", { x: M + 0.35, y: 2.7, w: ew - 0.7, h: 0.3, fontSize: 12, bold: true, color: GOLD, charSpacing: 2, margin: 0 });
s.addText("Learning Engine", { x: M + 0.35, y: 3.0, w: ew - 0.7, h: 0.5, fontSize: 22, bold: true, color: INK, margin: 0 });
s.addText("Courses that teach by shipping. Free content → paid live cohort. Run by Deepak. The revenue engine — funds everything.",
  { x: M + 0.35, y: 3.6, w: ew - 0.7, h: 1.1, fontSize: 13.5, color: INK, margin: 0 });
// Engine B
card(s, M + ew + 0.5, 2.4, ew, 2.5);
s.addShape(pres.shapes.RECTANGLE, { x: M + ew + 0.5, y: 2.4, w: ew, h: 0.12, fill: { color: NAVY2 }, line: { type: "none" } });
s.addText("ENGINE B", { x: M + ew + 0.85, y: 2.7, w: ew - 0.7, h: 0.3, fontSize: 12, bold: true, color: NAVY2, charSpacing: 2, margin: 0 });
s.addText("Physical AI Engine", { x: M + ew + 0.85, y: 3.0, w: ew - 0.7, h: 0.5, fontSize: 22, bold: true, color: INK, margin: 0 });
s.addText("Embodied-AI research → IP, course material, and (when funded) hardware products. Avinash leads; Deepak co-leads the drone.",
  { x: M + ew + 0.85, y: 3.6, w: ew - 0.7, h: 1.1, fontSize: 13.5, color: INK, margin: 0 });
// coupling strip
s.addShape(pres.shapes.RECTANGLE, { x: M, y: 5.35, w: W - 2 * M, h: 0.95, fill: { color: NAVY }, line: { type: "none" } });
s.addText("Revenue funds research   ·   Research makes the teaching credible   ·   Both feed talent",
  { x: M, y: 5.35, w: W - 2 * M, h: 0.95, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
pageFooter(s, 3, false);

// ============================================================= SLIDE 4 — ENGINE A
s = pres.addSlide();
lightHeader(s, "ENGINE A — LEARNING", "Teach by shipping");
s.addText("Recorded videos are free (the funnel). The paid product is a live cohort.",
  { x: M, y: 2.25, w: W - 2 * M, h: 0.4, fontSize: 14, italic: true, color: MUTED, margin: 0 });
const rows = [
  ["Live courses platform", "learn.trigunai.com — magic-link auth, student + admin dashboards. In production."],
  ["Flagship course", "Build & Ship a VR/MR App — 9 of 11 modules produced and public (EN + HI)."],
  ["Course lineup", "VR/MR (flagship) + Agentic AI + ML & Math, with Physical AI / Robotics in development."],
  ["Free funnel", '"AI is the Universal Mind" — 7 animated episodes, bilingual, on YouTube.'],
  ["Proof of shipping", "GuruLok — a meditation VR app live on the Meta Quest store."],
];
let ry = 2.8;
rows.forEach(([h1, h2]) => {
  card(s, M, ry, W - 2 * M, 0.74);
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: ry, w: 0.1, h: 0.74, fill: { color: GOLD }, line: { type: "none" } });
  s.addText(h1, { x: M + 0.3, y: ry, w: 3.3, h: 0.74, fontSize: 13.5, bold: true, color: INK, valign: "middle", margin: 0 });
  s.addText(h2, { x: M + 3.7, y: ry, w: W - 2 * M - 4.0, h: 0.74, fontSize: 12.5, color: INK, valign: "middle", margin: 0 });
  ry += 0.84;
});
pageFooter(s, 4, false);

// ============================================================= SLIDE 5 — ENGINE B
s = pres.addSlide();
lightHeader(s, "ENGINE B — PHYSICAL AI", "Simulation-trained intelligence, deployed to the edge");
const tw = (W - 2 * M - 0.5) / 2;
card(s, M, 2.4, tw, 3.4);
s.addShape(pres.shapes.RECTANGLE, { x: M, y: 2.4, w: tw, h: 0.12, fill: { color: GREEN }, line: { type: "none" } });
s.addText("TRACK 1", { x: M + 0.35, y: 2.7, w: tw - 0.7, h: 0.3, fontSize: 12, bold: true, color: GREEN, charSpacing: 2, margin: 0 });
s.addText("Drone Cinematography Policy", { x: M + 0.35, y: 3.0, w: tw - 0.7, h: 0.5, fontSize: 19, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "PPO trained in NVIDIA Isaac Sim / Isaac Lab (4096 envs, A10G).", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Exported to ONNX (~80 KB), runs on-device at 50 Hz; VR-validated in our Quest app.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Target hardware: Modal AI Starling 2 + GoPro Hero 12.", options: { bullet: true } },
], { x: M + 0.35, y: 3.55, w: tw - 0.7, h: 2.0, fontSize: 13, color: INK });
card(s, M + tw + 0.5, 2.4, tw, 3.4);
s.addShape(pres.shapes.RECTANGLE, { x: M + tw + 0.5, y: 2.4, w: tw, h: 0.12, fill: { color: GREEN }, line: { type: "none" } });
s.addText("TRACK 2", { x: M + tw + 0.85, y: 2.7, w: tw - 0.7, h: 0.3, fontSize: 12, bold: true, color: GREEN, charSpacing: 2, margin: 0 });
s.addText("ModusXR — AR Attention Guidance", { x: M + tw + 0.85, y: 3.0, w: tw - 0.7, h: 0.5, fontSize: 19, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Three additive focus modes for optical see-through AR.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Participant in Google's Android XR Catalyst program.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Target hardware: XREAL Project Aura; prototyped on Quest 3 passthrough.", options: { bullet: true } },
], { x: M + tw + 0.85, y: 3.55, w: tw - 0.7, h: 2.0, fontSize: 13, color: INK });
pageFooter(s, 5, false);

// ============================================================= SLIDE 6 — FLYWHEEL (roadmap)
s = pres.addSlide();
lightHeader(s, "THE FLYWHEEL WE'RE BUILDING", "Students learn inside the real research");
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 2.2, w: 4.6, h: 0.42, fill: { color: "FFF4D6" }, line: { color: GOLD, width: 1 }, rectRadius: 0.08 });
s.addText("Roadmap thesis — not yet operational", { x: M, y: 2.2, w: 4.6, h: 0.42, fontSize: 11.5, bold: true, color: "8A6D1A", align: "center", valign: "middle", margin: 0 });
const steps = [
  ["1", "The Robotics course's labs ARE the real drone-policy pipeline."],
  ["2", "Students learn RL on real NVIDIA hardware — not a toy copy."],
  ["3", "Graduates become collaborators, hires, or customers."],
  ["4", "We sit at the center of India's physical-AI talent flow."],
];
let sy = 2.95;
steps.forEach(([n, t]) => {
  s.addShape(pres.shapes.OVAL, { x: M, y: sy, w: 0.55, h: 0.55, fill: { color: NAVY }, line: { type: "none" } });
  s.addText(n, { x: M, y: sy, w: 0.55, h: 0.55, fontSize: 18, bold: true, color: GOLD, align: "center", valign: "middle", margin: 0 });
  s.addText(t, { x: M + 0.8, y: sy, w: W - 2 * M - 0.8, h: 0.55, fontSize: 15, color: INK, valign: "middle", margin: 0 });
  sy += 0.72;
});
s.addText("Honest today: the two engines run independently; the robotics course is in development. The coupling is the plan, not a current claim.",
  { x: M, y: 6.0, w: W - 2 * M, h: 0.5, fontSize: 12.5, italic: true, color: MUTED, margin: 0 });
pageFooter(s, 6, false);

// ============================================================= SLIDE 7 — NVIDIA STACK (dark)
s = pres.addSlide();
s.background = { color: NAVY };
s.addText("TRIGUNAI", { x: M, y: 0.45, w: 4, h: 0.3, fontSize: 11, bold: true, color: "9FB3C8", charSpacing: 3, margin: 0 });
s.addText("NVIDIA TECH", { x: M, y: 0.95, w: 8, h: 0.3, fontSize: 12, bold: true, color: GREEN, charSpacing: 2, margin: 0 });
s.addText("NVIDIA, end to end", { x: M, y: 1.3, w: W - 2 * M, h: 0.8, fontSize: 32, bold: true, color: "FFFFFF", fontFace: "Georgia", margin: 0 });
const tech = ["Isaac Sim", "Isaac Lab", "Omniverse", "CUDA Toolkit", "NVIDIA PyTorch", "ONNX → edge"];
let tx = M, tyy = 2.7, perRow = 3, gap = 0.4;
const bw = (W - 2 * M - gap * (perRow - 1)) / perRow;
tech.forEach((t, i) => {
  const col = i % perRow, row = Math.floor(i / perRow);
  const bx = M + col * (bw + gap), by = tyy + row * 1.1;
  s.addShape(pres.shapes.RECTANGLE, { x: bx, y: by, w: bw, h: 0.9, fill: { color: NAVY2 }, line: { color: GREEN, width: 1 } });
  s.addText(t, { x: bx, y: by, w: bw, h: 0.9, fontSize: 17, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
});
s.addText("Member of NVIDIA Inception. Policies train on A10G GPUs; edge target is Jetson-class. Not locked in — the ONNX policy ports anywhere.",
  { x: M, y: 5.7, w: W - 2 * M, h: 0.7, fontSize: 14, color: "CFE0F0", align: "center", margin: 0 });
pageFooter(s, 7, true);

// ============================================================= SLIDE 8 — TRACTION (honest)
s = pres.addSlide();
lightHeader(s, "TRACTION", "Where we actually are");
const hw = (W - 2 * M - 0.5) / 2;
// Shipped
card(s, M, 2.4, hw, 3.5);
s.addShape(pres.shapes.RECTANGLE, { x: M, y: 2.4, w: hw, h: 0.12, fill: { color: GOLD }, line: { type: "none" } });
s.addText("Shipped & live", { x: M + 0.35, y: 2.6, w: hw - 0.7, h: 0.45, fontSize: 18, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "GuruLok VR app live on the Meta Quest store", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "7 bilingual episodes published (EN + HI)", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Courses platform + 9 VR/MR modules live", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Drone policy trained + VR-validated", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "ModusXR in Google Android XR Catalyst", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "5 hostnames in production (Azure, India)", options: { bullet: true } },
], { x: M + 0.35, y: 3.15, w: hw - 0.7, h: 2.6, fontSize: 13, color: INK });
// Honest stage
card(s, M + hw + 0.5, 2.4, hw, 3.5);
s.addShape(pres.shapes.RECTANGLE, { x: M + hw + 0.5, y: 2.4, w: hw, h: 0.12, fill: { color: NAVY2 }, line: { type: "none" } });
s.addText("Honest stage", { x: M + hw + 0.85, y: 2.6, w: hw - 0.7, h: 0.45, fontSize: 18, bold: true, color: INK, margin: 0 });
s.addText([
  { text: "Pre-revenue. Founding-cohort phase.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Paid wall opens with the first live cohort.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "~₹4,000/mo infrastructure. Bootstrapped.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "2 founders, no outside capital raised.", options: { bullet: true } },
], { x: M + hw + 0.85, y: 3.15, w: hw - 0.7, h: 1.7, fontSize: 13, color: INK });
s.addText("We show the real stage on purpose — pre-seed, built, and ready to validate willingness-to-pay.",
  { x: M + hw + 0.85, y: 5.0, w: hw - 0.7, h: 0.8, fontSize: 12, italic: true, color: MUTED, margin: 0 });
pageFooter(s, 8, false);

// ============================================================= SLIDE 9 — BUSINESS MODEL
s = pres.addSlide();
lightHeader(s, "BUSINESS MODEL", "Free to understand · paid to transform");
const ladder = [
  ["Free series", "Funnel + email capture"],
  ["Community", "Recurring bridge"],
  ["Recorded courses", "Proof + passive floor"],
  ["Live cohort + GPU + VR", "THE PROFIT ENGINE"],
  ["B2B AI-literacy", "Later"],
];
const lw = (W - 2 * M - 0.4 * 4) / 5;
ladder.forEach(([t, d], i) => {
  const lx = M + i * (lw + 0.4);
  const hot = i === 3;
  s.addShape(pres.shapes.RECTANGLE, { x: lx, y: 2.7, w: lw, h: 2.0, fill: { color: hot ? NAVY : CARD }, line: { color: hot ? NAVY : LINE, width: 1 }, shadow: shadow() });
  s.addText(`0${i + 1}`, { x: lx, y: 2.85, w: lw, h: 0.4, fontSize: 15, bold: true, color: hot ? GOLD : MUTED, align: "center", margin: 0 });
  s.addText(t, { x: lx + 0.12, y: 3.3, w: lw - 0.24, h: 0.9, fontSize: 13, bold: true, color: hot ? "FFFFFF" : INK, align: "center", valign: "middle", margin: 0 });
  s.addText(d, { x: lx + 0.12, y: 4.15, w: lw - 0.24, h: 0.45, fontSize: 10.5, color: hot ? GOLD : MUTED, align: "center", margin: 0 });
});
s.addText("One self-run cohort (₹35–49k × ~20) ≈ ₹7–8 L. The moat — provided GPU + VR + \"we shipped it\" — is uncopyable.",
  { x: M, y: 5.3, w: W - 2 * M, h: 0.7, fontSize: 14.5, bold: true, italic: true, color: NAVY2, align: "center", margin: 0 });
pageFooter(s, 9, false);

// ============================================================= SLIDE 10 — TEAM
s = pres.addSlide();
lightHeader(s, "FOUNDERS", "Two founders, two engines");
const fw = (W - 2 * M - 0.5) / 2;
card(s, M, 2.45, fw, 3.0);
s.addText("Deepak Kumar", { x: M + 0.35, y: 2.7, w: fw - 0.7, h: 0.45, fontSize: 20, bold: true, color: INK, margin: 0 });
s.addText("CEO · Mumbai", { x: M + 0.35, y: 3.15, w: fw - 0.7, h: 0.35, fontSize: 13, bold: true, color: GOLD, margin: 0 });
s.addText([
  { text: "Runs the Learning Engine; co-leads the drone policy.", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Shipped a Quest app to Meta alpha; built the full video + RL training pipeline.", options: { bullet: true } },
], { x: M + 0.35, y: 3.6, w: fw - 0.7, h: 1.6, fontSize: 13, color: INK });
card(s, M + fw + 0.5, 2.45, fw, 3.0);
s.addText("Avinash", { x: M + fw + 0.85, y: 2.7, w: fw - 0.7, h: 0.45, fontSize: 20, bold: true, color: INK, margin: 0 });
s.addText("CTO · Patna", { x: M + fw + 0.85, y: 3.15, w: fw - 0.7, h: 0.35, fontSize: 13, bold: true, color: GOLD, margin: 0 });
s.addText([
  { text: "Leads the Physical AI Engine — ModusXR (Android XR Catalyst).", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
  { text: "Deep-learning depth; maintains the shipped Quest apps.", options: { bullet: true } },
], { x: M + fw + 0.85, y: 3.6, w: fw - 0.7, h: 1.6, fontSize: 13, color: INK });
s.addText("Bootstrapped. NVIDIA Inception member. Google Android XR Catalyst participant.",
  { x: M, y: 5.7, w: W - 2 * M, h: 0.4, fontSize: 13, color: MUTED, align: "center", margin: 0 });
pageFooter(s, 10, false);

// ============================================================= SLIDE 11 — THE ASK (dark)
s = pres.addSlide();
s.background = { color: NAVY };
s.addText("TRIGUNAI", { x: M, y: 0.45, w: 4, h: 0.3, fontSize: 11, bold: true, color: "9FB3C8", charSpacing: 3, margin: 0 });
s.addText("THE ASK", { x: M, y: 0.95, w: 8, h: 0.3, fontSize: 12, bold: true, color: GOLD, charSpacing: 2, margin: 0 });
s.addText("Seed capital for hardware — operations are self-funded", { x: M, y: 1.3, w: W - 2 * M, h: 1.2, fontSize: 30, bold: true, color: "FFFFFF", fontFace: "Georgia", margin: 0 });
const asks = [
  ["Drone hardware", "Modal AI Starling 2 + GoPro Hero 12 (~$2.5–3K) + a 6-month flight-test runway."],
  ["AR hardware", "XREAL Aura developer kits + sustained ModusXR build bandwidth."],
];
let ay = 2.95;
asks.forEach(([h1, h2]) => {
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: ay, w: W - 2 * M, h: 1.0, fill: { color: NAVY2 }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: ay, w: 0.1, h: 1.0, fill: { color: GOLD }, line: { type: "none" } });
  s.addText(h1, { x: M + 0.3, y: ay, w: 3.2, h: 1.0, fontSize: 16, bold: true, color: GOLD, valign: "middle", margin: 0 });
  s.addText(h2, { x: M + 3.6, y: ay, w: W - 2 * M - 3.9, h: 1.0, fontSize: 14, color: "FFFFFF", valign: "middle", margin: 0 });
  ay += 1.15;
});
s.addText("The software pipeline is ready. Hardware procurement is the only bottleneck to closing the sim-to-real gap. The Learning Engine funds day-to-day operations.",
  { x: M, y: 5.5, w: W - 2 * M, h: 0.8, fontSize: 13.5, italic: true, color: "CFE0F0", align: "center", margin: 0 });
pageFooter(s, 11, true);

// ============================================================= SLIDE 12 — CONTACT (dark)
s = pres.addSlide();
s.background = { color: NAVY };
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: H - 0.18, w: W, h: 0.18, fill: { color: GOLD }, line: { type: "none" } });
s.addImage({ path: LOGO_LIGHT, x: (W - 1.3) / 2, y: 1.2, w: 1.3, h: 1.3, sizing: { type: "contain", w: 1.3, h: 1.3 } });
s.addText("Let's build the physical-AI workforce.", { x: M, y: 2.8, w: W - 2 * M, h: 0.8, fontSize: 30, bold: true, color: "FFFFFF", fontFace: "Georgia", align: "center", margin: 0 });
s.addText("trigunai.com     ·     learn.trigunai.com     ·     physical-ai.trigunai.com",
  { x: M, y: 3.75, w: W - 2 * M, h: 0.4, fontSize: 15, color: "CFE0F0", align: "center", margin: 0 });
s.addText([
  { text: "deepak@trigunai.com", options: { bold: true, color: "FFFFFF" } },
  { text: "   —   subject: \"Investor enquiry — Physical AI\"", options: { color: "8FA6BD" } },
], { x: M, y: 4.4, w: W - 2 * M, h: 0.4, fontSize: 15, align: "center", margin: 0 });
s.addText("NVIDIA Inception Member   ·   Google Android XR Catalyst",
  { x: M, y: 5.4, w: W - 2 * M, h: 0.4, fontSize: 12, color: GOLD, align: "center", margin: 0 });

pres.writeFile({ fileName: path.join(REPO, "outreach/Trigunai_Company_Pitch_v2.pptx") }).then(f => {
  console.log("✓ wrote", f);
});
