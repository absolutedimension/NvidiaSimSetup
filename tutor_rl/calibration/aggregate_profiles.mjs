#!/usr/bin/env node
// Flywheel — Stage 5 calibration source.
// Runs ON THE GURUKUL VM. Reads the structured Learner Profiles (~/.openclaw/students/*.json)
// and emits a DE-IDENTIFIED aggregate to stdout. NO names, NO transcripts, NO wa_ids leave the
// box — only counts, concept-state distributions, misconception frequencies, and SRS-interval
// stats. Privacy red-line respected: raw student data stays on the VM.
//
// Usage (on VM):  node aggregate_profiles.mjs > /tmp/real_aggregate.json
// or from Mac, capturing stdout:  ssh ... 'node ~/agg.mjs' > tutor_rl/calibration/real_aggregate.json
import fs from "fs";
import os from "os";
import path from "path";

const dir = path.join(os.homedir(), ".openclaw", "students");
const files = fs.readdirSync(dir).filter(f => /^[0-9].*\.json$/.test(f) && !f.includes(".bak"));
const EVENTS = path.join(os.homedir(), ".openclaw", "gurukul", "events.jsonl");

const conceptStates = {};      // concept_id -> {state: count}
const miscFreq = {};           // misconception phrase -> count
const srsBoxes = [];           // Leitner box levels seen (spacing/retention evidence)
const srsBoxByConcept = {};    // concept -> [box levels]
const moduleDist = {}, streaks = [];
let nStudents = 0, nWithConcepts = 0, nWithMisc = 0;
const activeDays = [];

const norm = s => String(s).toLowerCase().trim().replace(/\s+/g, " ").slice(0, 80);

for (const f of files) {
  let d;
  try { d = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")); } catch { continue; }
  if (!d || !d.wa_id) continue;
  nStudents++;
  // concept states (value may be a string like "solid" or an object {state})
  const cs = d.concepts || {};
  const keys = Object.keys(cs);
  if (keys.length) nWithConcepts++;
  for (const k of keys) {
    const st = typeof cs[k] === "string" ? cs[k] : (cs[k] && cs[k].state) || "unknown";
    (conceptStates[k] ||= {})[st] = (conceptStates[k][st] || 0) + 1;
  }
  // misconceptions (free-text phrases the tutor logged)
  const ms = d.misconceptions || [];
  if (ms.length) nWithMisc++;
  for (const m of ms) {
    const phrase = typeof m === "string" ? m : (m && (m.text || m.id)) || "";
    if (phrase) miscFreq[norm(phrase)] = (miscFreq[norm(phrase)] || 0) + 1;
  }
  // SRS Leitner boxes — evidence for spacing/retention calibration (higher box =
  // survived more successful spaced recalls = stronger consolidation)
  for (const s of (d.srs || [])) {
    const box = s && (s.box ?? s.interval ?? s.days);
    if (typeof box === "number") {
      srsBoxes.push(box);
      if (s.concept) (srsBoxByConcept[s.concept] ||= []).push(box);
    }
  }
  moduleDist[d.current_module] = (moduleDist[d.current_module] || 0) + 1;
  if (typeof d.streak === "number") streaks.push(d.streak);
  if (d.created && d.updated) {
    activeDays.push((new Date(d.updated) - new Date(d.created)) / 86400000);
  }
}

// ---- events.jsonl: the append-only learning-event stream (richer than snapshots) ----
// Each line: {ts, type:"profile", student, course, concepts, recall:{concept, verdict}}.
// We aggregate recall verdicts per concept (real P(correct) = difficulty + learning signal)
// and how often each concept was discussed. De-identified: concept ids + counts only.
const recallByConcept = {};    // concept -> {correct, wrong}
const discussedByConcept = {}; // concept -> times marked shaky/solid in an event
let nEvents = 0;
if (fs.existsSync(EVENTS)) {
  for (const line of fs.readFileSync(EVENTS, "utf8").split("\n")) {
    if (!line.trim()) continue;
    let e; try { e = JSON.parse(line); } catch { continue; }
    if (e.type !== "profile") continue;
    nEvents++;
    if (e.recall && e.recall.concept && e.recall.verdict) {
      const r = (recallByConcept[e.recall.concept] ||= { correct: 0, wrong: 0 });
      if (e.recall.verdict === "correct") r.correct++; else r.wrong++;
    }
    for (const [k, v] of Object.entries(e.concepts || {}))
      if (v === "shaky" || v === "solid") discussedByConcept[k] = (discussedByConcept[k] || 0) + 1;
  }
}

const out = {
  generated_utc: new Date().toISOString(),
  n_students: nStudents,
  n_events: nEvents,
  recall_by_concept: recallByConcept,
  discussed_by_concept: discussedByConcept,
  n_with_concepts: nWithConcepts,
  n_with_misconceptions: nWithMisc,
  concept_states: conceptStates,
  misconception_frequency: Object.fromEntries(
    Object.entries(miscFreq).sort((a, b) => b[1] - a[1])),
  srs_boxes: srsBoxes,
  srs_box_by_concept: srsBoxByConcept,
  module_distribution: moduleDist,
  streak: { n: streaks.length, mean: streaks.reduce((a, b) => a + b, 0) / (streaks.length || 1),
            max: Math.max(0, ...streaks) },
  active_days: { mean: activeDays.reduce((a, b) => a + b, 0) / (activeDays.length || 1) },
};
process.stdout.write(JSON.stringify(out, null, 2));
