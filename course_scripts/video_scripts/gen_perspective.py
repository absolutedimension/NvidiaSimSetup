#!/usr/bin/env python3
"""Generate audio + photoreal variant images + manifest for a perspective video. Runs on EC2.
Usage: python3 gen_perspective.py <school|college> <build_dir>"""
import os, sys, base64, requests, json, subprocess, asyncio, edge_tts

PERS, B = sys.argv[1], sys.argv[2]
os.makedirs(f"{B}/img2", exist_ok=True)
VOICE, RATE = "en-GB-SoniaNeural", "-2%"
KEY="sk-trigunai-master-key-2026"; URL="http://localhost:4000/v1/images/generations"
PHOTO=(" Photorealistic candid documentary photograph, real, natural warm lighting, shallow depth of field, "
       "cinematic colour grade, 16:9, high detail. Keep the lower third uncluttered for a caption.")

# (sid, narration, label, [shot prompts])  — school shots are FACE-FREE (Azure blocks photoreal minors)
SCHOOL=[
 ("s01","You've talked to a voice assistant — you ask a question, it answers. An A.I. agent is the next step up. It doesn't just answer you. It actually does the job.","Ask a school student",
  ["A hand holding a smartphone showing a glowing voice-assistant waveform, close up, warm light, no face",
   "A smart speaker glowing softly on a desk in a cosy room, bokeh, no people"]),
 ("s02","Think of a normal chatbot as a friend who tells you the recipe. An agent is the friend who walks into the kitchen and actually cooks the meal.","Talks vs. doing",
  ["A recipe open on a phone propped up in a kitchen, candid, no people",
   "Hands cooking at a stove with steam rising, warm cosy kitchen, shallow depth of field"]),
 ("s03","Every agent has four simple parts. A brain that decides what to do. Hands, the tools it can use. A loop, where it tries something and checks. And a finish line, so it knows when the job is done.","What it's made of",
  ["A hand ticking items off a printed checklist, close up, warm light",
   "A tidy workbench with tools neatly laid out, shallow depth of field",
   "Close up of a to-do list with several items crossed off, pen resting"]),
 ("s04","Say you tell it, plan my birthday party. It checks your calendar, makes a guest list, orders a cake online, and sends out the invites, one step after another, until the whole party is ready.","A real example",
  ["A calendar app open on a phone, a finger scrolling, close up",
   "A birthday cake on a table with soft warm party lights, bokeh, no people",
   "Colourful party invitations and decorations arranged on a table, no people"]),
 ("s05","Here's the secret. It works in a loop. Look, is the job done? If not, do the next small thing, then check again. Look, act, check. Over and over, on its own, until it's finished.","How it thinks",
  ["Close up of a checklist with most boxes ticked, a pen in hand",
   "Hands arranging sticky notes in a row on a wall, warm light",
   "A desk with a neat step-by-step plan written out, warm light, no face"]),
 ("s06","So remember the one big idea. A chatbot only talks. An agent acts, using tools, step by step, until the job is done. That's an agent.","Remember this",
  ["A pair of hands closing a laptop on a cosy desk, golden hour, no face",
   "A warm tidy study desk with a notebook and a cup of coffee, bokeh, no people"]),
]
COLLEGE=[
 ("s01","You've used ChatGPT. That's a single call. A prompt goes in, text comes out, and it's done. An agent wraps that same model in a loop, and gives it hands: tools it can actually call.","Ask a college student",
  ["A college student at a laptop with a chat interface on screen, campus, candid",
   "Close up of a terminal or code editor glowing on a laptop in a warm room"]),
 ("s02","One turn looks like this. You give a goal. The model reasons, then asks to call a tool, say, web search. The tool runs and returns a result. The model reads it, and decides the next move. It repeats until the goal is met.","One turn of the loop",
  ["Terminal output scrolling on a dark screen, close up",
   "A search query being typed into a browser, screen glow",
   "Code running line by line on a screen, shallow depth of field"]),
 ("s03","Here's the shift that matters. In a normal program, you write every step. With an agent, you give only the goal, and the model chooses the steps itself, at runtime. One step, or twelve, and a different path each time. The model is driving, not your code.","You give the goal",
  ["A developer leaning back and thinking, laptop open, warm office bokeh",
   "A branching flowchart or decision tree on a monitor, close up",
   "Hands resting on a keyboard, screen reflected, contemplative"]),
 ("s04","Take a real job. Triage my unread emails and flag the urgent ones. The agent reads the inbox, classifies each message, and drafts the replies. It chose that sequence, you only stated the goal.","A real agent",
  ["An email inbox open on a laptop screen, close up",
   "Someone reviewing emails, a hand on the trackpad, warm light",
   "A reply being typed on a laptop, screen glow, shallow depth of field"]),
 ("s05","In code, it's just a while loop. Ask the model. If it requests a tool, run the tool, feed the result back, and loop. When there are no more tool calls, it's done. That handful of lines is the entire heart of every agent.","It's just a loop",
  ["A code editor showing a loop, syntax highlighted, dark theme, close up",
   "Fingers typing code on a laptop, warm focused light",
   "Code on a dark screen with a blinking cursor, close up"]),
 ("s06","Because the model drives, it can loop forever, call the wrong tool, or run up a bill. So real agents add guardrails. A step limit, output checks, a cost cap, and a human checkpoint before anything risky. Autonomy is powerful; guardrails make it safe.","Guardrails",
  ["A monitoring dashboard with graphs on a screen, close up",
   "Someone reviewing and approving something on a screen, hand poised, warm light",
   "A usage and cost graph trending on a laptop display"]),
 ("s07","And the honest version. The model isn't thinking like you do. It's predicting the next best action, over and over, inside a loop. Powerful, useful, and not magic. Understand that, and you can build one for almost any task.","The honest version",
  ["A developer satisfied at a laptop, leaning back, warm golden light, candid",
   "A warm closing shot of hands building, code on a screen, shallow depth of field"]),
]
GRADUATE=[
 ("s01","If you've shipped code, here's the precise version. An agent is a policy, a function that maps observations to actions. The language model is that policy. It decides each move.","Ask a graduate",
  ["A software engineer at a desk with multiple monitors showing code, warm office, candid",
   "Close up of code and a function on a screen, syntax highlighted, dark theme",
   "An engineer thoughtfully studying a screen, warm bokeh office"]),
 ("s02","The tools define its action space, everything it can actually do beyond producing text. Call an A.P.I., query a database, run code, send a message.","The action space",
  ["A screen showing an A.P.I. request and a JSON response, close up",
   "A database query running in a terminal, green text on dark screen",
   "Multiple tool icons and a terminal on a developer's monitor, warm light"]),
 ("s03","Its memory has two layers. Short term, the context window, its working memory for this run. And long term, retrieval over past state, pulling back what matters, when it matters.","Two kinds of memory",
  ["A diagram of a vector database and retrieval on a screen, close up",
   "Documents and notes being pulled up on a laptop, warm light",
   "A memory and context diagram on a dark-themed screen"]),
 ("s04","For jobs that take many steps, it plans. Decompose the task, reason and act in turns, the ReAct pattern, then reflect and self correct when a step fails.","How it plans",
  ["A flow of steps and a plan drawn on a whiteboard, close up",
   "A task broken into numbered steps on a dark-themed screen",
   "An engineer sketching a plan in a notebook, warm light"]),
 ("s05","And here's the distinction that separates engineers from tutorial followers. In a workflow, you hard code the control flow, fixed steps. In an agent, the model decides the control flow at runtime. More flexible, more powerful, and less predictable.","Workflow vs. agent",
  ["Two software architecture diagrams side by side on a monitor, close up",
   "A fixed pipeline diagram next to a dynamic flow on a screen",
   "An engineer comparing two diagrams on a large monitor, warm office"]),
 ("s06","That non determinism is the tax you pay for autonomy. So production agents wrap the loop in guardrails. Validation, retries, cost caps, observability. So a probabilistic core behaves like a dependable system.","The reliability tax",
  ["A monitoring dashboard with logs and metrics on a screen, close up",
   "Server logs scrolling on a dark terminal",
   "An observability dashboard with graphs on a screen, warm room"]),
 ("s07","So, an L.L.M. policy, acting over a tool defined action space, with layered memory and a planning loop, bounded by guardrails. That's an agent, precisely. Now you can architect one.","Architect one",
  ["A clean system architecture diagram on a monitor with an engineer satisfied, warm light",
   "A tidy system diagram on a dark-themed screen, close up",
   "An engineer leaning back content at a laptop, golden hour, candid"]),
]
DATA = {"school":SCHOOL, "college":COLLEGE, "graduate":GRADUATE}[PERS]

def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())

async def gen_audio():
    for sid,narr,_,_ in DATA:
        await edge_tts.Communicate(narr, VOICE, rate=RATE).save(f"{B}/{sid}.mp3")
        print("audio",sid,flush=True)
asyncio.run(gen_audio())

def gen_img(prompt,out):
    r=requests.post(URL,headers={"Authorization":f"Bearer {KEY}"},json={"model":"gpt-image-1.5","prompt":prompt+PHOTO,"size":"1536x1024","n":1},timeout=300)
    if r.status_code!=200: print("  ERR",r.status_code,r.text[:110]); return False
    it=r.json()["data"][0]; d=base64.b64decode(it["b64_json"]) if it.get("b64_json") else requests.get(it["url"]).content
    open(out,"wb").write(d); return True

manifest={}
for sid,narr,label,shots in DATA:
    d=dur(f"{B}/{sid}.mp3"); N=min(max(1,min(3,round(d/5.0))), len(shots))
    imgs=[]
    for k in range(N):
        out=f"{B}/img2/{sid}_v{k+1}.png"; print(f">> {sid} v{k+1}",flush=True)
        if gen_img(shots[k],out): imgs.append(out)
    if not imgs:  # safety: ensure at least 1 image
        out=f"{B}/img2/{sid}_v1.png"
        if gen_img(shots[0],out): imgs.append(out)
    manifest[sid]={"dur":d,"N":len(imgs),"images":imgs,"audio":f"{B}/{sid}.mp3","label":label}
json.dump(manifest,open(f"{B}/manifest.json","w"),indent=2)
print("MANIFEST",{k:v["N"] for k,v in manifest.items()},flush=True)
