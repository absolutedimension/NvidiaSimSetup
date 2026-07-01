"""Stage 5 — calibrate the student simulator from REAL de-identified Acharya data.

Input:  calibration/real_aggregate.json  (produced on the VM by aggregate_profiles.mjs;
        contains only counts/distributions — no names, no transcripts).
Output: calibrated_priors.json  — priors the simulator loads if present (student_env
        falls back to literature priors when a field is missing or data is insufficient).

Honest by design: it reports DATA SUFFICIENCY per signal and refuses to emit a prior
it can't support (min-sample gates). A thin cohort yields few calibrated fields — that's
correct, not a bug. As the cohort grows, re-run and more fields fill in.

Run:  python3 calibrate.py
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(__file__)
AGG = os.path.join(HERE, "calibration", "real_aggregate.json")
OUT = os.path.join(HERE, "calibrated_priors.json")

MIN_STUDENTS_FOR_MISC = 5      # need a few students before trusting a prevalence
MIN_OBS_PER_CONCEPT = 4        # need several states before trusting a difficulty


def main():
    if not os.path.exists(AGG):
        print(f"no aggregate at {AGG} — run aggregate_profiles.mjs on the VM first.")
        sys.exit(1)
    agg = json.load(open(AGG))
    n = agg.get("n_students", 0)
    priors = {"source": "acharya_real_aggregate", "generated_from": agg.get("generated_utc"),
              "n_students": n, "fields": {}}
    report = []

    # 1) Misconception prevalence (real, course-mixed free-text) ----------------
    mf = agg.get("misconception_frequency", {})
    if n >= MIN_STUDENTS_FOR_MISC and mf:
        prevalence = {k: v / n for k, v in mf.items()}
        priors["fields"]["misconception_candidates"] = prevalence
        report.append(f"misconceptions: {len(mf)} REAL phrases captured -> emitted as "
                      f"candidates (prevalence over {n} students).")
    else:
        report.append(f"misconceptions: INSUFFICIENT (n={n} < {MIN_STUDENTS_FOR_MISC}) "
                      f"-> keep literature priors. ({len(mf)} real phrases logged so far.)")

    # 2) Per-concept difficulty — prefer the EVENT STREAM (real recall verdicts:
    #    difficulty = 1 - P(correct on recall)); fall back to snapshot state dist.
    diffs = {}
    rbc = agg.get("recall_by_concept", {})
    for concept, r in rbc.items():
        obs = r.get("correct", 0) + r.get("wrong", 0)
        if obs < MIN_OBS_PER_CONCEPT:
            continue
        diffs[concept] = round(1.0 - r["correct"] / obs, 3)
    src = "event-stream recall verdicts"
    if not diffs:  # fall back to profile-snapshot state distribution
        src = "profile-snapshot states"
        for concept, states in agg.get("concept_states", {}).items():
            obs = sum(states.values())
            if obs < MIN_OBS_PER_CONCEPT:
                continue
            diffs[concept] = round(1.0 - states.get("solid", 0) / obs, 3)
    if diffs:
        priors["fields"]["concept_difficulty"] = diffs
        report.append(f"concept difficulty: calibrated for {len(diffs)} concept(s) from {src}.")
    else:
        report.append(f"concept difficulty: INSUFFICIENT (no concept has >= "
                      f"{MIN_OBS_PER_CONCEPT} obs in events or snapshots) -> keep literature priors. "
                      f"[events seen: {agg.get('n_events', 0)}]")

    # 3) Retention from SRS Leitner boxes ---------------------------------------
    boxes = agg.get("srs_boxes", [])
    if len(boxes) >= 5:
        mean_box = sum(boxes) / len(boxes)
        # higher mean box => recalls survive => slower effective forgetting.
        priors["fields"]["srs_mean_box"] = round(mean_box, 3)
        report.append(f"retention: {len(boxes)} SRS boxes, mean box {mean_box:.2f} "
                      f"-> consolidation evidence captured.")
    else:
        report.append(f"retention: INSUFFICIENT ({len(boxes)} SRS boxes) -> keep "
                      f"literature forgetting rate.")

    # 4) Engagement (always reportable) -----------------------------------------
    priors["fields"]["engagement"] = {
        "streak_mean": agg.get("streak", {}).get("mean"),
        "streak_max": agg.get("streak", {}).get("max"),
        "active_days_mean": agg.get("active_days", {}).get("mean"),
    }

    json.dump(priors, open(OUT, "w"), indent=2)
    print("=== CALIBRATION REPORT (honest data-sufficiency) ===")
    for r in report:
        print(" •", r)
    print(f"\nstudents with data: {n} | with concept-states: {agg.get('n_with_concepts')} "
          f"| with misconceptions: {agg.get('n_with_misconceptions')}")
    print(f"wrote {OUT} — fields: {list(priors['fields'])}")
    print("\nVERDICT:", "ENOUGH to calibrate some fields." if priors["fields"].get("concept_difficulty")
          or priors["fields"].get("misconception_candidates")
          else "TOO THIN to calibrate the sim yet — flywheel is running; revisit as the cohort grows.")


if __name__ == "__main__":
    main()
