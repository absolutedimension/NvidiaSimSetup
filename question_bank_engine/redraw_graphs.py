#!/usr/bin/env python3
"""Clean-redraw pilot for graph_plot diagram questions.

VLM -> structured SPEC (not code) -> fixed matplotlib renderer -> VLM verify -> retry.
No LLM code execution: the model emits DATA describing the plot; a trusted renderer draws
it. Output is our own figure -> copyright-clean, watermark-free.

    python3 redraw_graphs.py [--limit 20] [--max-retries 2] [--out-dir /tmp/redraw]
"""
import argparse
import base64
import json
import os
import sqlite3
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qbank import config

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
VMODEL = os.environ.get("QBANK_VISION_MODEL", "gpt-4o")

SPEC_SYS = r"""You reproduce an exam-paper GRAPH as a structured spec so a renderer can redraw it
cleanly (no watermark). Read the figure and the question, then output JSON describing the plot.

Schema:
{
 "title": string|null,
 "xlabel": string, "ylabel": string,
 "xlim": [min,max]|null, "ylim": [min,max]|null,
 "show_axes_origin": bool,           // draw x=0/y=0 axes through origin (physics style)
 "series": [
   // choose the kind that fits; give REAL coordinates in data units
   {"kind":"polyline","points":[[x,y],...],"label":string|null,"style":"solid|dashed|dotted"},
   {"kind":"function","fn":"line|parabola|exp|log|sine|hyperbola|sqrt|circle",
      "params":{...},"domain":[a,b],"label":string|null,"style":"solid|dashed|dotted"},
   {"kind":"scatter","points":[[x,y],...],"label":string|null},
   {"kind":"segment","from":[x,y],"to":[x,y],"arrow":bool,"label":string|null}
 ],
 "annotations":[{"x":num,"y":num,"text":string}],
 "hlines":[num,...], "vlines":[num,...]
}
function params: line{m,c}; parabola{a,b,c}; exp{a,k}(a*e^(k x)); log{a,b}(a*ln(x)+b);
sine{A,w,phi,c}; hyperbola{k}(y=k/x); sqrt{a}(a*sqrt(x)); circle{cx,cy,r}.
Capture the SHAPE and key points/labels faithfully; approximate coordinates are fine.
Output ONLY the JSON object."""

VERIFY_SYS = """You are checking whether a REDRAWN graph faithfully reproduces an ORIGINAL exam
figure for the SAME question. You get the ORIGINAL first, then OUR redraw. Judge whether a
student answering the question would get the SAME answer from our redraw: same curve shapes,
same relationships, same key labels/points. Ignore watermark, colour, minor styling.
Return JSON {"faithful": true|false, "issues": [short strings], "score": 0-10}."""


def _b64(path):
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    return mime, base64.b64encode(open(path, "rb").read()).decode()


def _call(messages, model=VMODEL):
    body = json.dumps({"model": model, "messages": messages,
                       "response_format": {"type": "json_object"}, "temperature": 0.2}).encode()
    req = urllib.request.Request(PROXY, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return json.loads(r["choices"][0]["message"]["content"])


def extract_spec(stem, fig_path, critique=None):
    mime, b64 = _b64(fig_path)
    user = [{"type": "text", "text": "QUESTION: " + stem[:600]
             + ("\n\nYour previous spec had these problems, fix them: " + json.dumps(critique) if critique else "")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]
    return _call([{"role": "system", "content": SPEC_SYS}, {"role": "user", "content": user}])


def verify(stem, orig_path, our_path):
    om, ob = _b64(orig_path)
    nm, nb = _b64(our_path)
    user = [{"type": "text", "text": "QUESTION: " + stem[:400] + "\n\nORIGINAL figure:"},
            {"type": "image_url", "image_url": {"url": f"data:{om};base64,{ob}"}},
            {"type": "text", "text": "OUR redraw:"},
            {"type": "image_url", "image_url": {"url": f"data:{nm};base64,{nb}"}}]
    return _call([{"role": "system", "content": VERIFY_SYS}, {"role": "user", "content": user}])


def render(spec, out_path):
    fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=130)
    for s in spec.get("series", []):
        k = s.get("kind"); style = {"solid": "-", "dashed": "--", "dotted": ":"}.get(s.get("style", "solid"), "-")
        lab = s.get("label")
        if k == "polyline":
            p = np.array(s["points"], float); ax.plot(p[:, 0], p[:, 1], style, label=lab, lw=2)
        elif k == "scatter":
            p = np.array(s["points"], float); ax.scatter(p[:, 0], p[:, 1], label=lab, zorder=3)
        elif k == "segment":
            a, b = s["from"], s["to"]; ax.plot([a[0], b[0]], [a[1], b[1]], style, label=lab, lw=2)
            if s.get("arrow"):
                ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", lw=2))
        elif k == "function":
            fn = s.get("fn"); pr = s.get("params", {}); d = s.get("domain", spec.get("xlim") or [-10, 10])
            x = np.linspace(d[0], d[1], 400)
            with np.errstate(all="ignore"):
                if fn == "line": y = pr.get("m", 1) * x + pr.get("c", 0)
                elif fn == "parabola": y = pr.get("a", 1) * x**2 + pr.get("b", 0) * x + pr.get("c", 0)
                elif fn == "exp": y = pr.get("a", 1) * np.exp(pr.get("k", 1) * x)
                elif fn == "log": x = np.linspace(max(d[0], 1e-3), d[1], 400); y = pr.get("a", 1) * np.log(x) + pr.get("b", 0)
                elif fn == "sine": y = pr.get("A", 1) * np.sin(pr.get("w", 1) * x + pr.get("phi", 0)) + pr.get("c", 0)
                elif fn == "hyperbola": x = x[x != 0]; y = pr.get("k", 1) / x
                elif fn == "sqrt": x = np.linspace(max(d[0], 0), d[1], 400); y = pr.get("a", 1) * np.sqrt(x)
                elif fn == "circle":
                    th = np.linspace(0, 2 * np.pi, 400)
                    ax.plot(pr.get("cx", 0) + pr.get("r", 1) * np.cos(th),
                            pr.get("cy", 0) + pr.get("r", 1) * np.sin(th), style, label=lab, lw=2)
                    y = None
                else: y = None
            if y is not None:
                ax.plot(x, y, style, label=lab, lw=2)
    for h in spec.get("hlines", []) or []: ax.axhline(h, color="#888", lw=.8)
    for v in spec.get("vlines", []) or []: ax.axvline(v, color="#888", lw=.8)
    if spec.get("show_axes_origin"):
        ax.axhline(0, color="#333", lw=1); ax.axvline(0, color="#333", lw=1)
    for a in spec.get("annotations", []) or []:
        try: ax.annotate(a["text"], (a["x"], a["y"]), fontsize=8)
        except Exception: pass
    if spec.get("xlim"): ax.set_xlim(*spec["xlim"])
    if spec.get("ylim"): ax.set_ylim(*spec["ylim"])
    ax.set_xlabel(spec.get("xlabel") or ""); ax.set_ylabel(spec.get("ylabel") or "")
    if spec.get("title"): ax.set_title(spec["title"], fontsize=10)
    if any(s.get("label") for s in spec.get("series", [])): ax.legend(fontsize=7)
    ax.grid(True, alpha=.25)
    fig.tight_layout(); fig.savefig(out_path); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--out-dir", default="/tmp/redraw")
    ap.add_argument("--types-json", default="/tmp/diag_types.json")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    ids = [r["id"] for r in json.load(open(args.types_json)) if r["type"] == "graph_plot"][:args.limit]
    c = sqlite3.connect(config.DB_PATH); c.execute("PRAGMA busy_timeout=30000")
    report = []
    passed = 0
    for n, qid in enumerate(ids, 1):
        row = c.execute("SELECT stem, figure_refs FROM questions WHERE id=?", (qid,)).fetchone()
        if not row: continue
        stem, refs = row
        try:
            orig = os.path.join(config.FIG_DIR, json.loads(refs or "[]")[0])
        except Exception:
            continue
        if not os.path.exists(orig): continue
        our = os.path.join(args.out_dir, f"{qid}.png")
        critique, verdict, ok = None, None, False
        for attempt in range(args.max_retries + 1):
            try:
                spec = extract_spec(stem, orig, critique)
                render(spec, our)
                verdict = verify(stem, orig, our)
            except Exception as e:
                verdict = {"faithful": False, "issues": [f"error: {str(e)[:60]}"], "score": 0}
                break
            if verdict.get("faithful"):
                ok = True; break
            critique = verdict.get("issues")
        passed += ok
        report.append({"id": qid, "passed": ok, "score": verdict.get("score"),
                       "issues": verdict.get("issues"), "orig": orig, "our": our if os.path.exists(our) else None})
        print(f"  [{n}/{len(ids)}] {qid}  {'PASS' if ok else 'fail'}  score={verdict.get('score')}")

    json.dump(report, open(os.path.join(args.out_dir, "report.json"), "w"))
    print(f"\n[redraw] clean-pass yield: {passed}/{len(ids)} = {100*passed/max(1,len(ids)):.0f}%")


if __name__ == "__main__":
    main()
