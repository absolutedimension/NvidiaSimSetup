# Course 6 — Build Your AI Music Factory (15 Days) · Landing-Page Handoff

> **Status:** Curriculum complete (2026-06-20). Sibling to Course 5 (AI Video Factory). Same rule:
> **we teach the factory, we do not sell music-as-a-service.** The standout hook — students build
> **their own AI singer** (a voice they own), not a Suno subscription.
> **Landing CTA = REGISTER / JOIN THE WAITLIST** (free-now funnel). Post-launch course; collecting
> interest now is free validation — recording it comes after the first paid cohort.

---

## 1. The offer (landing copy)

**Title:** Build Your AI Music Factory
**Tagline:** Turn a prompt or your lyrics into finished, mastered, **copyright-clean** music — songs
with vocals, beats, focus & meditation tracks — in your *own* GPU studio. And build **your own AI
singer**: a voice you own, consistent across every song. 15 days, monetization-safe, at scale.

**You build:** your own end-to-end AI music factory **+ your own AI singer** — and release your first
tracks from it.

**For:** musicians & producers · **faceless music-channel builders** (lofi / study / sleep / meditation) ·
content creators & podcasters who need music · wellness & meditation creators · game / app / ad makers ·
B2B sync & brand-music.

**You need:** a laptop + a modest cloud-GPU budget (~$1/hr) + a basic mic (only for the singer days).
**No music theory, no production background.** The AI writes the lyrics and the melodies; you direct.

**Outcome:** a working music factory you *own* + your own AI singer + your first released tracks —
across songs, beats, focus/meditation, in 50+ languages, all **safe to monetize** on YouTube / Spotify / ads.

**Why it's different:** every output is **copyright-clean** (built on MIT-licensed models trained on
licensed + royalty-free data — not a black box that can get you demonetized), and you build a **singer
you own**. Taught by someone who runs this exact pipeline to score a real channel and course library.

---

## 2. The 15-day curriculum

Project-based. Every day = a short lesson + a hands-on lab; the labs compound. By Day 15 you have a
running factory, your own AI singer, and released tracks. Three milestones marked ★.

| Day | Title | You learn | Hands-on lab |
|---|---|---|---|
| **1** | The AI Music Factory | Prompt/lyrics → finished mastered track; the model landscape (generation vs sung-melody); **why copyright-clean = monetization-safe**; the business models (faceless channels, beats for creators, meditation, sync/B2B) | Tour finished tracks across every style; pick your lane |
| **2** | Your GPU + the engine | Cheap cloud GPU; install the **copyright-clean engine** (ACE-Step class); model basics; cost control | Spin up a box; generate your first 40-second song |
| **3** | Prompting music: style & control | Prompt craft for genre / mood / instruments / BPM; style presets; **reference-style matching** (make it like THIS track — legally) | Generate the same idea in 3 styles |
| **4** | Songs with vocals & lyrics | AI-writing lyrics; lyric → full vocal song; **50+ languages** (EN / Hindi); song structure (verse / chorus) | A full vocal song from your own lyrics |
| **5** | Any length: extend & structure | Seamless crossfade extension; intros / outros; loop-ready beds; 2 min → 1 hour | A 30-minute continuous track |
| **6** | Focus / study / sleep + brainwave tones | **Isochronic & binaural** tones (beta / alpha / theta) — the science *and* the honest claims; **432Hz** tuning; the huge faceless-channel niche | A 1-hour focus track with an isochronic bed |
| **7** ★ | Meditation, raga & wellness | 432Hz Indian-classical, sitar / sarangi healing, ambient drones; pacing for relaxation | **★ Milestone: a complete meditation track** |
| **8** | Beats, lofi & instrumentals | Lofi chill, hip-hop beats, instrumental beds for creators; stems | A lofi beat / instrumental pack |
| **9** | Build your AI singer I — record the voice | The recording protocol (consent, vowels & sargam, **sung** Hindi + English, dynamics, ~25–30 min); mic & setup; why *sung* phonemes beat spoken ones (fixes accent) | Record your singer dataset (or use a provided one) |
| **10** ★ | Build your AI singer II — train & sing | Voice-conversion (RVC) training; converting AI vocals into **your singer's voice**; a consistent owned identity across songs | **★ Milestone: a song in your own AI singer's voice** |
| **11** | Precise melodies — singing synthesis | SVS (DiffSinger): render a melody **you** compose (MIDI) vs. dice-roll generation; when to use each | Sing a specific tune you wrote |
| **12** | Mastering & polish | Loudness (LUFS for streaming), EQ, stereo width, fades; final MP3 / WAV; the quality bar | Master a track to streaming spec |
| **13** | Automate the factory | One-command presets per style; batching; templates; a repeatable content pipeline | A one-command template for your channel's sound |
| **14** | Publish & monetize, copyright-clean | Distribution (DistroKid / YouTube / Spotify); **proving your tracks are clean**; faceless music channels; sync / licensing for B2B; the support trap to avoid | Prep a release + a B2B / sync offer |
| **15** ★★ | Ship & scale | A release calendar; building a catalog; your AI singer as a brand | **★★ Capstone: release your first 3 tracks + your AI singer · Demo Day** |

**What you walk away with:** a running AI music factory you own · **your own AI singer** · released
tracks across songs / beats / focus / meditation · a copyright-clean, monetization-safe workflow · and
a release calendar to build a catalog — plus (B2B track) a sync/brand-music offer.

---

## 3. Drop-in course card (add to `courses.ts`)

```ts
const AMBER = '#ffb454';   // suggested accent for the music course

// ── 6. Build Your AI Music Factory — register-interest / waitlist ─────────────
{
  id: 'ai-music-factory',
  badge: 'NEW · REGISTER INTEREST',
  status: 'waitlist',                 // CTA => "Join the waitlist"
  accent: AMBER,
  title: 'Build Your AI Music Factory',
  tagline:
    'Turn a prompt or your lyrics into finished, mastered, copyright-clean music — songs, beats, ' +
    'focus & meditation tracks — in your own GPU studio. And build your own AI singer: a voice you own.',
  fromEpisodes: 'The sound of the whole project — learn to produce monetization-safe music at scale.',
  level: 'Creator → Label of one',
  modulesCount: 15,
  hours: '~18 hours over 15 days',
  outcome:
    'Your own AI music factory + your own AI singer + your first released tracks — copyright-clean ' +
    'across songs, beats, focus & meditation, in 50+ languages.',
  forWho:
    'Musicians & producers, faceless music-channel builders (lofi/study/meditation), creators & ' +
    'podcasters, wellness creators, game/app/ad makers, and B2B sync & brand-music.',
  prerequisites:
    'A laptop + a modest cloud-GPU budget (~$1/hr) + a basic mic (for the singer days). No music theory.',
  registerKey: 'MUSIC',
  modules: [
    { n: 1,  title: 'The AI Music Factory',          brief: 'The model landscape, the styles, the business models.' },
    { n: 2,  title: 'Your GPU + the engine',          brief: 'Spin up a box; install the copyright-clean engine.' },
    { n: 3,  title: 'Prompting music',                brief: 'Style/mood/BPM control + reference-style matching.' },
    { n: 4,  title: 'Songs with vocals & lyrics',     brief: 'Lyric → full vocal song in 50+ languages.' },
    { n: 5,  title: 'Any length: extend & structure', brief: 'Seamless extension; loop-ready beds; 2 min → 1 hr.' },
    { n: 6,  title: 'Focus / study + brainwave tones',brief: 'Isochronic/binaural beats; 432Hz; the channel niche.' },
    { n: 7,  title: 'Meditation, raga & wellness',    brief: '432Hz classical, sitar healing, ambient drones.' },
    { n: 8,  title: 'Beats, lofi & instrumentals',    brief: 'Lofi, hip-hop beats, instrumental beds + stems.' },
    { n: 9,  title: 'Your AI singer I — record',      brief: 'The recording protocol for an owned voice dataset.' },
    { n: 10, title: 'Your AI singer II — train & sing',brief: 'RVC training → a song in your own singer\'s voice.' },
    { n: 11, title: 'Precise melodies — SVS',         brief: 'Render a melody you composed (DiffSinger).' },
    { n: 12, title: 'Mastering & polish',             brief: 'LUFS, EQ, stereo, fades — streaming-ready.' },
    { n: 13, title: 'Automate the factory',           brief: 'Presets, batching, one-command templates.' },
    { n: 14, title: 'Publish & monetize',             brief: 'Distribution, proving clean, sync/B2B offers.' },
    { n: 15, title: 'Ship & scale',                   brief: 'Release 3 tracks + your AI singer; a catalog plan.' },
  ],
},
```

## 4. Register wiring (for Deepak)
- Add `'MUSIC'` to the `registerKey` union + a `REGISTER_URL_MUSIC` (waitlist form / Substack fallback).

## 5. Update `COURSE_INDEXES.md`
Add a row:
`| 6 | **Build Your AI Music Factory** | (the sound craft) | **Register interest** | **Join the waitlist** | Creator → Label of one | 15 | ~18 |`
…and add a Course 6 section with the §1 + §2 content.

---

## CEO note (not for the page)
- **Workshop taught as a course** — approved move (mirror of Course 5). CTA = waitlist, not a price.
- **Honest on the tone claims:** isochronic/432Hz = "may support focus/relaxation," NEVER "heals" or
  a medical claim. Keep wellness copy to *clarity*, not cure (brand rule).
- **Copyright-clean is the real moat** — lead with monetization-safety; it's what separates this from
  "just use Suno" (which has murkier commercial terms).
- **B2B = teaching / sync-licensing**, not done-for-you scoring as a service (support trap).
- **Do not let it displace July-18.** Post-launch; collect register-interest now, build after first paid cohort.
