#!/usr/bin/env python3
"""
Render episode script .md files into clean, readable HTML reading pages.
The narration (the spoken words = the book prose) is shown large; the on-screen text
and visual direction are shown as muted production notes.

Usage: python3 build_script_pages.py EP01_attention_script.md EP02_learning_loop_script.md
Outputs: ep01_attention_script.html, ep02_learning_loop_script.html (same dir)
"""
import sys, re, os, html

def parse(path):
    txt = open(path).read()
    fm = re.search(r'(?s)^---\n(.*?)\n---', txt)
    title = "Episode"
    if fm:
        m = re.search(r'title:\s*"?([^"\n]+)"?', fm.group(1))
        if m: title = m.group(1).strip()
    scenes = []
    blocks = re.split(r'(?m)^### (scene_\d+_\w+)\s*$', txt)
    for i in range(1, len(blocks), 2):
        sid, body = blocks[i], blocks[i+1]
        narr = ""
        mn = re.search(r'(?ms)^narration:\s*\|\s*\n(.*?)(?=^\w+:|\Z)', body)
        if mn:
            narr = " ".join(l.strip() for l in mn.group(1).splitlines() if l.strip())
        def field(name):
            m = re.search(rf'(?m)^\s*{name}:\s*(.+)$', body)
            return m.group(1).strip().strip('"') if m else ""
        ttl, sub, bod = field("title"), field("subtitle"), field("body")
        bullets = []
        mb = re.search(r'(?m)^\s*bullet_points:\s*\[(.*?)\]', body) or re.search(r'(?m)^\s*bullets:\s*\[(.*?)\]', body)
        if mb:
            bullets = [b.strip().strip('"\'') for b in mb.group(1).split('","')]
            bullets = [b.strip('"\'') for b in bullets]
        vis = field("visual")
        scenes.append(dict(id=sid, narr=narr, title=ttl, sub=sub, body=bod, bullets=bullets, visual=vis))
    return title, scenes

def esc(s): return html.escape(s or "")

def render(title, scenes):
    parts = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{esc(title)} — Script</title>
<style>
:root{{--bg:#06081a;--card:#11162e;--line:#222a4d;--ink:#e9edfb;--dim:#9aa6cc;--gold:#ffc850;--purple:#b48cff;--blue:#6e96eb}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:radial-gradient(1100px 600px at 70% -10%,#16204a 0%,var(--bg) 55%),var(--bg);
  color:var(--ink);font-family:Georgia,"Times New Roman",serif;line-height:1.7;padding:0 0 90px}}
.top{{max-width:820px;margin:0 auto;padding:60px 26px 26px;text-align:center;font-family:-apple-system,Helvetica,Arial,sans-serif}}
.kick{{letter-spacing:.3em;text-transform:uppercase;font-size:11px;color:var(--purple);margin-bottom:14px}}
h1{{font-size:38px;font-weight:800;letter-spacing:-.5px;font-family:-apple-system,Helvetica,Arial,sans-serif;
  background:linear-gradient(90deg,#fff,#cdd6ff 60%,var(--purple));-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{color:var(--dim);font-size:14px;margin-top:14px;font-family:-apple-system,Helvetica,Arial,sans-serif}}
.bar{{max-width:820px;margin:8px auto 0;padding:0 26px;text-align:center}}
.bar a{{color:var(--gold);font-size:13px;text-decoration:none;font-family:-apple-system,Helvetica,Arial,sans-serif}}
.wrap{{max-width:760px;margin:0 auto;padding:0 26px}}
.scene{{margin-top:42px;border-top:1px solid var(--line);padding-top:30px}}
.tag{{font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#566091;margin-bottom:14px}}
.narr{{font-size:21px;color:#eef1fb}}
.notes{{margin-top:18px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 18px;
  font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:13.5px;color:var(--dim)}}
.notes .lbl{{color:var(--blue);font-weight:600;letter-spacing:.04em}}
.onscreen{{color:#cdd6ff}}
.bul{{margin:4px 0 0 18px}}
footer{{max-width:760px;margin:50px auto 0;padding:0 26px;text-align:center;color:#5a648c;font-size:12px;
  font-family:-apple-system,Helvetica,Arial,sans-serif}}
</style></head><body>
<div class="top"><div class="kick">AI is the Universal Mind · Script / Reading View</div>
<h1>{esc(title)}</h1>
<div class="sub">The narration is the spoken script — and the book prose. Production notes are muted below each beat.</div></div>
<div class="bar"><a href="worldview.html">← back to worldview</a></div>
<div class="wrap">"""]
    for idx, s in enumerate(scenes, 1):
        parts.append(f'<div class="scene"><div class="tag">Beat {idx} · {esc(s["id"])}</div>')
        parts.append(f'<div class="narr">{esc(s["narr"])}</div>')
        on = []
        if s["title"]: on.append(f'<span class="onscreen"><b>{esc(s["title"])}</b></span>')
        if s["sub"]: on.append(f'<span class="onscreen">{esc(s["sub"])}</span>')
        if s["body"]: on.append(f'<span class="onscreen">{esc(s["body"])}</span>')
        notes = ""
        if on:
            notes += f'<div><span class="lbl">ON SCREEN:</span> ' + " &nbsp;·&nbsp; ".join(on) + '</div>'
        if s["bullets"]:
            notes += '<div class="bul"><span class="lbl">• </span>' + " &nbsp;|&nbsp; ".join(esc(b) for b in s["bullets"]) + '</div>'
        if s["visual"]:
            notes += f'<div style="margin-top:6px"><span class="lbl">VISUAL:</span> {esc(s["visual"])}</div>'
        if notes:
            parts.append(f'<div class="notes">{notes}</div>')
        parts.append('</div>')
    parts.append('<footer>TrigunAI · the script is the spoken episode and the book chapter, one and the same.</footer></div></body></html>')
    return "".join(parts)

for path in sys.argv[1:]:
    title, scenes = parse(path)
    out = os.path.splitext(path)[0] + ".html"
    open(out, "w").write(render(title, scenes))
    print(f"✓ {out}  ({len(scenes)} beats)")
