# 🔌 KIDS "ALIVE WORKSHEET" — the integration contract (Phase 0)

*Written 2026-08-02. The single seam between the worksheet-engine session and the avatar/UI session.
Freeze this and the two sessions build independently. Companions: `WORKSHEET_COMPONENT_HANDOFF.md`,
`../../../kids_quiz/WORKSHEET_GRAMMAR.md`.*

## The screen (composition)
One kids worksheet screen layers three things that already exist:
```
┌───────────────────────────────────────────────┐
│  [avatar]  ← corner: kid.glb reads + reacts    │   avatar/UI session owns this (iframe)
│                                                │
│      ┌──────────────────────────────┐          │
│      │  WORKSHEET ITEM (do it)       │          │   worksheet session — KidsWorksheet.render()
│      │  + concept animation (see it) │          │   kids-quiz-viz mounts in the workspace
│      └──────────────────────────────┘          │
└───────────────────────────────────────────────┘
```

## The ONE API — `KidsAvatar.speak`
The worksheet calls this for every instruction and every celebration. The avatar session owns the guts.
```js
KidsAvatar.speak(text, { mood, onEnd })
//  text  : string to voice (the item.voice or a feedback line)
//  mood  : 'talk' | 'celebrate' | 'think' | 'encourage' | 'idle'   (optional)
//  onEnd : callback fired when speech finishes                      (optional)
```

## Transport — postMessage (avatar runs in an <iframe>, so the sessions stay decoupled)
`KidsAvatar.speak` is a thin wrapper the worksheet page provides; under the hood:

**page → avatar iframe**
```json
{ "type":"kidsAvatar:speak", "id":"<uuid>", "text":"Trace the number 5!", "mood":"talk" }
{ "type":"kidsAvatar:mood",  "mood":"celebrate" }
```
**avatar iframe → page**
```json
{ "type":"kidsAvatar:ready" }              // emit ONCE on load — tells the page the avatar owns audio now
{ "type":"kidsAvatar:done", "id":"<uuid>" } // when the spoken line finishes → fires onEnd
```

## Graceful degradation (why this works TODAY)
- Until the avatar posts `kidsAvatar:ready`, the page plays `/kids/tts?text=…` audio **itself** (voice works now, no lip-sync).
- The moment the avatar session ships a receiver that posts `ready`, the page **hands audio off** to the avatar — lip-sync + mood, no worksheet-code change. Same `KidsAvatar.speak` call, upgraded output.

## What the AVATAR session implements (Phase 1)
1. Inside `avatar_widget.html`: `window.addEventListener('message', …)` for `kidsAvatar:speak`.
2. On load, `parent.postMessage({type:'kidsAvatar:ready'}, '*')`.
3. On `speak`: fetch `/kids/tts?text=…` (or your own TTS), play it, drive `kid.glb` mouth from a
   **dynamic** viseme timeline (the crux — your greeting visemes are pre-baked; this needs text→viseme
   at runtime: server-side amplitude extraction from the TTS mp3, or a phoneme estimator). Apply `mood`
   as a body/face state. Post `kidsAvatar:done` with the same `id` when finished.
4. Keep `kid.glb`, sizing, idle-bob as-is — only add the message receiver + dynamic mouth.

## What the WORKSHEET session provides (this session — DONE in the prototype)
- `alive_worksheet.html` — composes the avatar iframe + `KidsWorksheet.render` + a `#viz` mount for
  kids-quiz-viz, and defines the `KidsAvatar.speak` wrapper + the audio fallback.
- Calls `KidsAvatar.speak(item.voice)` on render and `KidsAvatar.speak(feedback,{mood:'celebrate'})` on `onDone`.

## Boundaries
- Avatar iframe URL = `/static/kids/avatar_widget.html` (avatar session's file — I don't edit it).
- Message `type` strings above are frozen. Don't rename `KidsAvatar` / the `kidsAvatar:*` types.
- Physical code collision point remains `main.py` (the assess-page inject) — coordinate before editing.

— worksheet agent
