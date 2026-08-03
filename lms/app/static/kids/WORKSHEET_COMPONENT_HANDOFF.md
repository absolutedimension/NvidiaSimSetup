# 🤝 Handoff — Kids Worksheet Component (for the UI/UX agent)

*Written 2026-08-02 by the agent building the worksheet engine. You're building the kids look/avatar;
this note tells you exactly what I added so we don't collide.*

## TL;DR
I added a **worksheet renderer** for the non-MCQ item types (trace, match, sort, order, fill, number-pad,
true/false, colour-by-number, and **open answers via keyboard + voice**). It's **decoupled**, in **new files
only**, and already **deployed live** (`lms-kids:v14`, kids app only — `lms`/Acharya untouched).

**Live demo:** https://kids-education.trigunai.com/static/kids/worksheet_demo.html

## Files I own (do not need to touch — but good to know)
| File | Role |
|---|---|
| `static/kids/worksheet.js` | The component. One global: `KidsWorksheet.render(mount, item, {onDone, voice})` |
| `static/kids/worksheet.css` | Styling — **every class is `.ws-*`** (namespaced, can't clash with your UI) |
| `static/kids/worksheet_demo.html` | Standalone test page (all 19 archetypes) |
| `../../../kids_quiz/WORKSHEET_GRAMMAR.md` | The spec: ~30 archetypes + the item JSON schema |

## Files YOU own (I did NOT touch)
`index.html`, `avatar_widget.html`, `characters/`, `kid.glb`, `greeting.*`, `kids_voice.js/css`,
`voice_quiz.html`. No overlap — I only added `worksheet.*`.

## The contract (how you'd drop a worksheet into your UI)
```js
KidsWorksheet.render(
  document.getElementById('mount'),      // any container you own
  { type:'match_following', instruction:'Match each animal to its home!',
    payload:{ pairs:[['🐄 Cow','Shed'],['🐦 Bird','Nest']] }, explain:'All matched!' },
  { voice:true, onDone:(r)=>{ /* r = {correct, item, answerGiven} */ } }
);
```
- It renders its own card (`.ws-card`) with instruction + 🔊 hear button + the right input widget + a Check/feedback footer.
- It calls `/kids/tts` for voice (same endpoint as `kids_voice.js`) and Web Speech API for spoken answers.
- Item JSON schema + every `type` → input-family mapping is in `WORKSHEET_GRAMMAR.md §2–§3`.

## The ONE shared-file hook (let's coordinate before either of us edits it)
To wire worksheets into the live student test, `main.py` (~line 683, where the kids assess page already
injects `kids_voice.css/js`) needs to ALSO inject:
```html
<link rel="stylesheet" href="/static/kids/worksheet.css">
<script src="/static/kids/worksheet.js" defer></script>
```
…plus a dispatch so non-`mcq` pool items route to `KidsWorksheet.render`. **`main.py` is our collision
point** — whoever edits it, ping the other first. (Also still needs worksheet-type items in the qbank;
today the pool is MCQ-only, so nothing worksheet renders in the live flow yet.)

## Boundaries / please don't
- Don't rename the `.ws-*` classes or the `KidsWorksheet` global.
- Style *around* the component (card sits in your container); if you want it to match your theme, override
  the `:root` `--ws-*` vars — don't fork the file.
- Deploys snapshot the whole `lms/` tree → commit your WIP to a safe point before a deploy so it doesn't
  ship half-finished.

Questions → leave a note here or ping Deepak. — worksheet agent
