#!/usr/bin/env python3
"""Regenerate index.json — the master coverage matrix — from every <board>_class<N>_<subject>.json
cell in this folder. Run after adding/updating cells:  python3 build_index.py
Schema of a cell: {board, class, subject, source:{name,url,verified_on}, confidence, status,
                   live_questions?, chapters:[{id,name,subtopics:[...]}]}
"""
import json, glob, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
cells = []
for fp in sorted(glob.glob(os.path.join(HERE, "*.json"))):
    if os.path.basename(fp) == "index.json":
        continue
    try:
        c = json.load(open(fp, encoding="utf-8"))
        cells.append((os.path.basename(fp), c))
    except Exception as e:
        print("skip", fp, e)

BOARDS = ["ICSE", "CBSE", "Bihar Board"]
CLASSES = [1, 2, 3, 4, 5]
SUBJECTS = ["Mathematics", "EVS", "English", "General Knowledge", "Hindi"]

matrix = {}          # board -> class -> subject -> status
for fn, c in cells:
    matrix.setdefault(c["board"], {}).setdefault(int(c["class"]), {})[c["subject"]] = {
        "file": fn, "status": c.get("status", "draft"),
        "confidence": c.get("confidence", "?"), "chapters": len(c.get("chapters", [])),
        "live_questions": c.get("live_questions", 0),
        "source": c.get("source", {}).get("name", ""),
    }

total_possible = len(BOARDS) * len(CLASSES) * len(SUBJECTS)
done = sum(1 for _, c in cells)
index = {
    "generated_on": "2026-08-02",
    "schema": "kids_quiz/curriculum/<board>_class<N>_<subject>.json",
    "matrix_definition": {"boards": BOARDS, "classes": CLASSES, "subjects": SUBJECTS,
                          "total_cells": total_possible},
    "coverage": {"cells_done": done, "cells_total": total_possible,
                 "percent": round(100 * done / total_possible)},
    "cells": matrix,
}
json.dump(index, open(os.path.join(HERE, "index.json"), "w"), indent=2, ensure_ascii=False)
print(f"index.json: {done}/{total_possible} cells ({index['coverage']['percent']}%)")
for b in matrix:
    for cl in sorted(matrix[b]):
        for su, info in matrix[b][cl].items():
            print(f"  {b} Class {cl} {su}: {info['status']} ({info['chapters']} ch, {info['live_questions']} Qs)")
