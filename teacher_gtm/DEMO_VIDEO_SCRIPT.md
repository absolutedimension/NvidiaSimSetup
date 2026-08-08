# Acharya Demo Video — production script (v1)

> **Purpose:** the single ~3-min Hinglish demo video used across the 25-lead funnel
> (pre-demo warm-up · no-show fallback · post-demo recap · forward-to-decision-maker).
> **Pipeline:** `production-video-trigunai` (shader bg + slides + captions + music bed)
> **+ real screen recordings** (the product proof — see Asset List §A, Deepak records these
> on his phone BEFORE render day; a product demo with no real screens is a pamphlet).
> **Audience:** coaching-institute owners, Hindi-belt + metro. **Language:** Hinglish
> narration (Hindi sentence flow, English product words). **CTA:** reply "DEMO" on WhatsApp.
> **Brand:** Acharya dark-gold palette (`reference-acharya-brand`), Acharya avatar persona
> optional as corner presenter (talking-avatar-trigunai — same face/voice as Maya calls).

---

## Production settings

| Setting | Value |
|---|---|
| Mode | Mode C (premium) — motion graphics + screen-capture inserts + word-synced captions |
| Voice | Hindi male, warm-professional (the Maya/Acharya voice family — hi-IN Dhruv or equivalent) |
| Music | Soft focus bed, -22 dB under VO |
| Resolution / length | 1080p landscape 16:9 · target 2:45–3:15 · burned-in captions (teachers watch muted) |
| Also render | 9:16 vertical cut of Scenes 2–5 (60–90s) for WhatsApp status forwarding |

---

## Scenes

### Scene 1 — The 160 hours (0:00–0:25) · HOOK
**Narration:** "Aap apne students ko hafte mein sirf kuch ghante padhaate hain. Baaki **160
ghante** woh akele hote hain. Wahin doubts jama hote hain, practice chhoot jaati hai — aur
kamzor student chupchaap coaching chhod deta hai."
**On-screen:** dark-gold motion graphic — a week-grid of 168 cells; 8 light up (class hours),
160 stay dark; a student icon fades out of the dark zone. Keyword pops: "160 ghante akele".
**Visual direction:** slow, serious, no product yet. The problem must sting first.

### Scene 2 — Meet Acharya, under YOUR name (0:25–0:50)
**Narration:** "Miliye **Acharya** se — aapka apna AI tutor, **aapke naam se**, WhatsApp pe.
Koi app install nahi. Aapke students usi WhatsApp pe message karte hain jo unke paas pehle
se hai — aur Acharya khud ko batata hai: *'[Sharma Sir] ka tutor'*."
**On-screen:** ✂️ **SCREEN-CAP A** — real WhatsApp chat opening: student sends "Hi", Acharya
replies introducing itself under the teacher's brand name. Zoom on the branded intro line.
**Visual direction:** phone-frame mockup, the brand-name reply highlighted in gold.

### Scene 3 — The 9pm doubt, solved (0:50–1:35) · THE CORE PROOF
**Narration:** "Raat 9 baje ka doubt? Ab aapko disturb nahi karta. Student photo bhejta hai
ya type karta hai — Acharya **step-by-step** solve karta hai, aapke syllabus ke hisaab se,
Hindi ya English mein. Aur sirf jawab nahi deta — samjhaata hai, phir **practice ka sawaal**
deta hai, aur exam se pehle revision bhi karwata hai. Roz. Bina thake."
**On-screen:** ✂️ **SCREEN-CAP B** — real chat: a NEET/JEE physics doubt (e.g. projectile
motion) sent at "9:04 pm", Acharya's stepwise solution scrolling; then ✂️ **SCREEN-CAP C** —
daily practice question arriving next morning. Caption pops: "24×7 · aapke syllabus pe ·
Hindi/English".
**Visual direction:** let the real answer scroll for 8–10 seconds — THIS is the product;
don't rush it. Timestamp visible.

### Scene 4 — What YOU see: the weekly report (1:35–2:10) · THE THING THEY PAY FOR
**Narration:** "Aur aap? Aapko har hafte milti hai **report**: kaun sa student roz practice
kar raha hai, kaun **chupchaap peeche chhoot raha hai**, aur kis topic pe atka hai — test
result aane se pehle. Yehi cheez batch ko toot-ne se bachaati hai."
**On-screen:** ✂️ **SCREEN-CAP D** — the real weekly teacher report (WhatsApp/web view):
active-student list, stuck-topics list. Motion-graphic overlay circles the "quietly falling
behind" student row in gold.
**Visual direction:** shift the frame from student-phone to teacher-phone — make it visually
obvious this screen is the OWNER's view.

### Scene 5 — Price + the risk-free start (2:10–2:40)
**Narration:** "Poora system: **₹4,999 mahina, flat** — 50 students tak, koi per-student fees
nahi. Ek student ki fees se bhi kam. Aur shuruaat? **14 din bilkul FREE**, aapke 10 students
ke saath. Kaam kare toh rakhiye. Na kare toh band — koi charge nahi. Setup hum karte hain,
24 ghante ke andar; aapko sirf ek WhatsApp message forward karna hai."
**On-screen:** clean pricing card (dark-gold): "₹4,999/mo flat · 50 students · 14 din free ·
setup by us". A "❌ koi app nahi · ❌ per-student fee nahi · ❌ result ke jhoothe vaade nahi"
strike-line beat.
**Visual direction:** calm confidence; the three NOTs build trust — keep them.

### Scene 6 — CTA (2:40–2:55)
**Narration:** "Apne students ke liye Acharya ko kaam karta hua dekhna chahte hain — aapke
apne subject pe, live? Isi number pe **'DEMO'** reply kijiye, ya humein call kijiye.
20 minute — aur aapka apna AI tutor taiyaar."
**On-screen:** WhatsApp reply-box animation typing "DEMO"; Acharya logo + trigun mark;
contact card: "TrigunAI — DEMO". End on the brand triskelion spin (trigun_spin_1080.mp4).

---

## §A Asset list (record BEFORE render day — Deepak, ~45 min)

| ✂️ | What to capture (phone screen-rec, clean demo tenant, student name "Rahul") | Used in |
|---|---|---|
| A | Fresh chat: "Hi" → branded intro "[Sharma Sir] ka tutor" (use a neutral demo brand) | Scene 2 |
| B | Physics doubt (photo or text) → full stepwise solution, timestamp ~9 pm | Scene 3 |
| C | Next-morning daily-practice message | Scene 3 |
| D | Weekly teacher report — active list + stuck-topics view | Scene 4 |

Guardrails on the captures: real product only, no mocked answers; verify the solution is
CORRECT before recording (a wrong answer in the demo video is fatal); no real student names.

## §B Render plan

1. Deepak records A–D → drops into `teacher_gtm/demo_video_assets/`
2. Run `video-script-writer-trigunai` output (this file) through `production-video-trigunai`
   Mode C on the EC2 box (start box → render → stop box)
3. QC pass: every screen-cap readable at phone size? captions synced? price card correct?
4. Host: YouTube unlisted + direct MP4 on gurukul.trigunai.com (WhatsApp-friendly link)
5. Hand the link to the field rep + drop into the onboarding bot's
   post-demo template

*v1 · 2026-07-12 · Owner: Deepak · Consumed by: production-video-trigunai*
