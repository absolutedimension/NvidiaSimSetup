# 🎤 AI Singer — Voice Recording Guide

**For:** the person lending their voice · **Time needed:** ~30–40 minutes · **Result:** a custom AI singer "voice" that TrigunAI owns and can use to sing any song.

> Read this once fully, then record in order. Don't overthink it — a calm, clean, natural take is worth more than a "perfect" performance. We need your *natural voice*, not a polished studio vocal.

---

## ✅ Part 1 — Setup (5 min)

**Gear (any of these works):**
- A phone (modern phones are fine), a USB mic, or a laptop mic in a quiet room. A USB mic or good earphones-with-mic is best, but a phone in a quiet room is totally acceptable.

**Environment — this matters most:**
- 🔇 **Quiet room.** No fan, AC, TV, traffic, or echo. A small room with soft furnishings (bed, curtains, clothes) sounds better than a big empty/tiled room.
- 🎙️ **Mic ~15–20 cm (a hand-span) from your mouth.** Stay roughly the same distance the whole time.
- 🚫 **No effects.** Turn OFF any "reverb", "voice changer", noise-cancellation, or beautify filters. We want the raw voice.
- 🔈 Speak/sing at a **comfortable, consistent volume** — not whispering, not shouting.

**Recording settings (if your app lets you choose):**
- Format: **WAV** (preferred) or high-quality M4A/MP3. Sample rate **44.1 kHz or 48 kHz**. Mono is fine.
- Recommended free apps: **Voice Memos** (iPhone), **Samsung Voice Recorder / Easy Voice Recorder** (Android), **Audacity** (laptop).

**Quick test:** record 5 seconds saying *"testing, one two three"*, play it back. Can you hear it clearly with **no background hum or echo**? Good. If it's noisy/echoey, change rooms.

---

## ✍️ Part 2 — Consent (please read & record this line first)

Start your recording by saying this out loud (this protects everyone and confirms the voice is given freely):

> *"My name is __________. Today's date is __________. I give TrigunAI Innovations permission to use recordings of my voice to create and use a synthetic AI singing voice."*

---

## 🎵 Part 3 — What to record (the session, ~25–30 min)

Record these **in order**. You can do it all in one file, or one file per section (either is fine — see naming in Part 5). Leave a **2-second pause of silence** between items. If you mess up, just pause and redo that line — we'll clean it up.

### A. Spoken warm-up — neutral voice (~2 min)
Speak naturally, like you're reading the news. **Do this in BOTH Hindi and English** (Hindi is important — it's how we make the singer sound natively Hindi).

- **Hindi:** Read any calm paragraph — a news article, a story, or just describe your day for ~1 minute in Hindi.
- **English:** The same — read or speak naturally for ~1 minute in English.

### B. Sustained vowels — the core of the voice (~3 min)
This is the most important part for timbre. Hold each vowel **steady for ~4–5 seconds**, at a comfortable pitch. Do the set **three times: once low, once medium, once high** in your range.

Sing (hold each): **"aaaa" … "eeee" … "iiii" … "oooo" … "uuuu"**
Then the Indian vowels: **"आ … ई … ऊ … ए … ओ"**

### C. Scales — sargam (~4 min)
Sing the sargam slowly and clearly, going up and then down. Do it **2–3 times, starting at different comfortable pitches** (one lower, one higher). This teaches the AI your full range.

> **सा रे ग म प ध नी सां** (up)  …then…  **सां नी ध प म ग रे सा** (down)
> *(Sa Re Ga Ma Pa Dha Ni Saa → Saa Ni Dha Pa Ma Ga Re Sa)*

### D. Sung passages — Hindi (~6 min) ⭐ most important for accent
Sing these **slowly and clearly**, in a simple natural tune (any melody you like — it doesn't need to match a real song). Sing each line, pause, repeat it once. Put feeling into it but keep it gentle.

```
सुर में बहता ये मन मेरा
हर साँस में एक नया सवेरा
आवाज़ मेरी है खुली हवा
गाता रहूँ मैं सुबह से शाम
```
Then sing these single words on a held note (for clear pronunciation):
**प्रेम · विरह · सपना · चाँदनी · ख़ुशी · आँसू · उम्मीद · ज़िंदगी**

### E. Sung passages — English (~4 min)
Same idea — simple gentle tune, sing slowly and clearly:

```
Here I am, my voice is free
Singing soft and easily
Morning light and evening calm
Every note becomes a song
```

### F. Dynamics & emotion (~3 min)
Sing **any one** of the lines above (Hindi or English) **four ways**, so the AI learns your expressive range:
1. **Soft & gentle** (like a lullaby)
2. **Bright & happy**
3. **Sad & longing**
4. **Strong & full** (louder, confident)

---

## 📋 Part 4 — Do's & Don'ts

| ✅ Do | 🚫 Don't |
|---|---|
| Record in a quiet, soft room | Record near a fan/AC/window/traffic |
| Keep a steady distance from the mic | Move closer/farther while recording |
| Sing/speak slowly and clearly | Rush or mumble |
| Keep a consistent comfortable volume | Whisper one line, belt the next |
| Turn OFF all filters/effects | Use reverb, autotune, or "beautify" |
| Pause 2 sec & redo if you slip | Stop the whole session over one slip |
| Drink water, stay relaxed | Strain or push your voice |

**Total raw material we want: ~20–30 minutes of clean audio.** More is better, but quality > quantity. Even 15 clean minutes makes a great singer.

---

## 📦 Part 5 — Naming & sending the files

- If **one file**: name it `singer_<yourname>.wav`
- If **separate files**: `<yourname>_A_warmup.wav`, `<yourname>_B_vowels.wav`, `<yourname>_C_sargam.wav`, `<yourname>_D_hindi.wav`, `<yourname>_E_english.wav`, `<yourname>_F_emotion.wav`
- Send the **original files** (not screen-recordings or compressed re-shares). Google Drive, WeTransfer, or AirDrop preserves quality; avoid WhatsApp "audio" which compresses heavily — use WhatsApp **"Document"** if you must, or better, Drive/WeTransfer.

That's it — thank you! 🙏 Your voice becomes a singer that can perform in any language and style.

---

### (Internal note — for the TrigunAI side, not the friend)
This dataset supports two paths: (1) **best zero-shot reference** — pick the cleanest 15–30 s sung clip as the singer's `*_ref.wav` for seed-vc (immediate, fixes the Hindi accent if the sung-Hindi section is used); (2) **fine-tune** seed-vc on the full ~25 min for a more robust, higher-fidelity owned voice. Convert delivered files to 44.1 kHz mono WAV, trim silence, and stage under `/home/ubuntu/singers/`. A male recording → Ravi, female → Maya (or mint a new named singer). See `singerize.py` + `production-music-trigunai` skill.
</content>
