#!/usr/bin/env python3
"""grammar_extract.py — read a DJ's per-track arrangement JSONs (from
dj_arrangement_analysis.py) and learn the SHARED arrangement grammar:
section structure, element-entry order, breakdown/peak signatures, energy arc,
section-type transitions. Output = grammar.json + a readable summary.

Usage: python3 grammar_extract.py --dir analysis/ --out grammar.json --md GRAMMAR.md
"""
import argparse, glob, json, os, numpy as np

ELS = ["sub", "kick+bass", "bassline", "drone", "stab", "hats"]
ACT = 0.35  # element "active" threshold

def sectype(label):
    l = label.lower()
    if l.startswith("intro/breakdown"): return "intro/ambient"
    if l.startswith("breakdown"): return "breakdown"
    if l.startswith("peak"): return "peak"
    if l.startswith("build"): return "build"
    return "groove"

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--out", default=None)
ap.add_argument("--md", default=None)
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.dir, "*.json")))
tracks = []
for fp in files:
    d = json.load(open(fp))
    if d.get("sections"): tracks.append(d)
N = len(tracks)
print(f"loaded {N} tracks")

# --- aggregates ---
sec_durs = {t: [] for t in ["intro/ambient","breakdown","build","peak","groove"]}
n_sections, durations = [], []
el_active_frac = {e: [] for e in ELS}      # fraction of track-time each element active
entry_rank = {e: [] for e in ELS}          # order each element first appears
trans = {}                                  # section-type transition counts
energy_curves = []                          # resampled energy arc per track
breakdowns_per_hr, breakdown_durs, breakdown_keep = [], [], {e:0 for e in ELS}
intro_is_ambient = 0; intro_durs = []
nbk = 0

for d in tracks:
    secs = d["sections"]; dur = d["duration_s"]
    durations.append(dur); n_sections.append(len(secs))
    # section-type durations + transitions
    types = [sectype(s["label"]) for s in secs]
    for s, ty in zip(secs, types): sec_durs[ty].append(s["dur_s"])
    for i in range(len(types)-1):
        trans[(types[i],types[i+1])] = trans.get((types[i],types[i+1]),0)+1
    # element active fraction (time-weighted) + first-entry time
    for e in ELS:
        on_time = sum(s["dur_s"] for s in secs if s["elements"].get(e,0) > ACT)
        el_active_frac[e].append(on_time/dur)
        ent = next((s["start_s"] for s in secs if s["elements"].get(e,0) > ACT), None)
        entry_rank[e].append(ent if ent is not None else dur)
    # intro
    intro_is_ambient += 1 if types[0] in ("intro/ambient","breakdown") else 0
    intro_durs.append(secs[0]["dur_s"])
    # breakdowns
    bks = [s for s,ty in zip(secs,types) if ty=="breakdown"]
    breakdowns_per_hr.append(len(bks)/(dur/3600))
    for s in bks:
        breakdown_durs.append(s["dur_s"]); nbk+=1
        for e in ELS:
            if s["elements"].get(e,0) > ACT: breakdown_keep[e]+=1
    # energy arc resampled to 24 pts
    ts = np.array([(s["start_s"]+s["end_s"])/2 for s in secs]); en = np.array([s["energy"] for s in secs])
    energy_curves.append(np.interp(np.linspace(0,1,24), ts/dur, en))

def stat(x): return {"mean":round(float(np.mean(x)),1),"median":round(float(np.median(x)),1)} if len(x) else {}

grammar = {
  "dj": os.path.basename(os.path.dirname(os.path.abspath(a.dir))) or "dj",
  "n_tracks": N,
  "track_minutes": stat([d/60 for d in durations]),
  "sections_per_track": stat(n_sections),
  "section_durations_s": {t: stat(v) for t,v in sec_durs.items() if v},
  "element_active_fraction": {e: round(float(np.mean(v)),2) for e,v in el_active_frac.items()},
  "element_entry_order": sorted(ELS, key=lambda e: np.mean(entry_rank[e])),
  "element_mean_entry_s": {e: int(np.mean(entry_rank[e])) for e in ELS},
  "intro_ambient_fraction": round(intro_is_ambient/N,2),
  "intro_dur_s": stat(intro_durs),
  "breakdowns_per_hour": stat(breakdowns_per_hr),
  "breakdown_dur_s": stat(breakdown_durs),
  "breakdown_retains": {e: round(breakdown_keep[e]/max(1,nbk),2) for e in ELS},
  "energy_arc_24": [round(float(v),2) for v in np.mean(energy_curves,axis=0)],
  "section_transitions": {f"{k[0]}->{k[1]}": v for k,v in sorted(trans.items(), key=lambda x:-x[1])},
}

if a.out: json.dump(grammar, open(a.out,"w"), indent=2); print("grammar ->", a.out)

# --- readable summary ---
arc = grammar["energy_arc_24"]
arcbar = "".join(" ▁▂▃▄▅▆▇█"[min(8,int(v*8))] for v in arc)
lines = [f"# {grammar['dj']} — learned arrangement grammar ({N} tracks)\n",
  f"- track length: ~{grammar['track_minutes']['median']:.0f} min · {grammar['sections_per_track']['median']:.0f} sections/track",
  f"- **intro is ambient/no-kick {int(grammar['intro_ambient_fraction']*100)}% of the time** (median {grammar['intro_dur_s']['median']:.0f}s)",
  f"- **element entry order:** {' → '.join(grammar['element_entry_order'])}",
  "- **element presence (fraction of track active):**"]
for e in ELS: lines.append(f"    {e:10s} {grammar['element_active_fraction'][e]:.2f}  {'█'*int(grammar['element_active_fraction'][e]*30)}")
lines += [f"- **breakdowns:** ~{grammar['breakdowns_per_hour']['mean']:.1f}/hr, median {grammar['breakdown_dur_s']['median']:.0f}s; "
          f"during them, retains: " + ", ".join(f"{e} {grammar['breakdown_retains'][e]:.0%}" for e in ELS if grammar['breakdown_retains'][e]>0.3),
  f"- **section durations (median s):** " + ", ".join(f"{t} {v['median']:.0f}" for t,v in grammar['section_durations_s'].items()),
  f"- **typical energy arc (start→end):**\n```\n{arcbar}\n```",
  f"- **most common transitions:** " + ", ".join(list(grammar['section_transitions'].keys())[:6])]
md = "\n".join(lines)
print("\n"+md)
if a.md: open(a.md,"w").write(md); print("\nmd ->", a.md)
